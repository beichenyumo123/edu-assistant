"""
默认企业培训资料初始化服务

已废弃（2026-07）：默认文档不再在注册时 per-user 初始化，改为
部署时通过 deploy/seed_shared_docs.py 预向量化到共享 ChromaDB 集合。
此模块保留供参考，auth.py 中已移除对其的调用。
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.document import Document
from ..models.user import User
from ..rag.loader import parse_file, split_text
from ..rag.vectorstore import get_vectorstore


DEFAULT_ONBOARDING_ORIGINAL_NAME = "欣旺达-劳动人事管理全流程手册.pdf"
DEFAULT_ONBOARDING_KEYWORDS = ("劳动人事管理全流程手册", "欣旺达")
DEFAULT_SOURCE_PROFILE = {"source_type": "workflow", "trust_level": "high"}


def _has_default_document(db: Session, user_id: int) -> bool:
    return (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.original_name == DEFAULT_ONBOARDING_ORIGINAL_NAME,
        )
        .first()
        is not None
    )


def _existing_upload_path(doc: Document) -> Path | None:
    candidates = [
        Path(settings.UPLOAD_DIR) / doc.filename,
        Path(settings.UPLOAD_DIR) / doc.original_name,
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def _find_default_source_path(db: Session) -> Path | None:
    """查找默认手册源文件。

    查找顺序：
    1. 已上传的同名资料
    2. uploads 目录中的关键词匹配 PDF
    3. 项目 deploy/seeds/ 目录（部署时固化）
    4. 桌面兜底（本地开发）
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    backend_dir = Path(__file__).resolve().parents[2]

    docs = (
        db.query(Document)
        .filter(Document.original_name == DEFAULT_ONBOARDING_ORIGINAL_NAME)
        .order_by(Document.id.asc())
        .all()
    )
    for doc in docs:
        path = _existing_upload_path(doc)
        if path:
            return path

    for path in upload_dir.glob("*.pdf"):
        if any(keyword in path.name for keyword in DEFAULT_ONBOARDING_KEYWORDS):
            return path

    # 部署种子文件（deploy/seeds/）
    seed_path = backend_dir.parent / "deploy" / "seeds" / DEFAULT_ONBOARDING_ORIGINAL_NAME
    if seed_path.exists() and seed_path.is_file():
        return seed_path

    desktop_copy = Path.home() / "Desktop" / DEFAULT_ONBOARDING_ORIGINAL_NAME
    if desktop_copy.exists() and desktop_copy.is_file():
        return desktop_copy

    return None


def ensure_default_onboarding_document(db: Session, user: User) -> Document | None:
    """为新用户初始化默认入职培训资料。

    该函数保持幂等：用户已拥有默认资料时不重复创建。初始化失败不应阻断注册。
    """
    if _has_default_document(db, user.id):
        return (
            db.query(Document)
            .filter(
                Document.user_id == user.id,
                Document.original_name == DEFAULT_ONBOARDING_ORIGINAL_NAME,
            )
            .first()
        )

    source_path = _find_default_source_path(db)
    if not source_path:
        return None

    ext = source_path.suffix.lower() or ".pdf"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = Path(settings.UPLOAD_DIR) / unique_name
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    shutil.copyfile(source_path, save_path)

    doc = Document(
        user_id=user.id,
        filename=unique_name,
        original_name=DEFAULT_ONBOARDING_ORIGINAL_NAME,
        file_type="pdf",
        file_size=save_path.stat().st_size,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        text = parse_file(str(save_path), ext)
        if not text or len(text.strip()) < 10:
            raise ValueError("默认资料内容为空或过短")

        chunks = split_text(text)
        vectorstore = get_vectorstore(user_id=user.id)
        vectorstore.add_texts(
            texts=chunks,
            metadatas=[
                {
                    "document_id": str(doc.id),
                    "document_name": doc.original_name,
                    "chunk_index": i,
                    "file_type": doc.file_type,
                    "source_type": DEFAULT_SOURCE_PROFILE["source_type"],
                    "trust_level": DEFAULT_SOURCE_PROFILE["trust_level"],
                }
                for i in range(len(chunks))
            ],
        )

        doc.status = "ready"
        doc.chunk_count = len(chunks)
        doc.error_message = None
    except Exception as exc:
        doc.status = "error"
        doc.error_message = str(exc)

    db.commit()
    db.refresh(doc)
    return doc
