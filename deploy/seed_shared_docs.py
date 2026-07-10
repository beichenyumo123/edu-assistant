#!/usr/bin/env python3
"""
部署时预向量化默认企业培训资料到共享 ChromaDB 集合。

用法：
    cd backend && ../venv/bin/python ../deploy/seed_shared_docs.py

该脚本幂等 — 重复运行不会产生重复向量。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 确保 backend 目录在 sys.path 中，以支持 from app.xxx import xxx
BACKEND_DIR = (Path(__file__).resolve().parents[1] / "backend").resolve()
sys.path.insert(0, str(BACKEND_DIR))

# 切换到 backend 目录（SQLite 数据库路径 sqlite:///./edu_assistant.db 相对于 CWD）
os.chdir(str(BACKEND_DIR))

# 从 .env 加载配置
from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, init_db  # noqa: E402
from app.rag.loader import parse_file, split_text  # noqa: E402
from app.rag.vectorstore import get_shared_vectorstore  # noqa: E402
from app.rag.embeddings import preload_embeddings  # noqa: E402
from app.models.document import Document  # noqa: E402

# 配置
SEED_PDF_NAME = "欣旺达-劳动人事管理全流程手册.pdf"
SEED_PDF_PATH = BACKEND_DIR.parent / "deploy" / "seeds" / SEED_PDF_NAME
DEFAULT_SOURCE_PROFILE = {"source_type": "workflow", "trust_level": "high"}
SEED_DOCUMENT_ID = 999999  # 固定共享文档 ID（用于幂等检测 + 确定性向量 ID）


def already_seeded(db) -> bool:
    """检查共享知识库是否已初始化。"""
    existing = (
        db.query(Document)
        .filter(
            Document.is_shared == True,  # noqa: E712
            Document.is_default == True,
            Document.original_name == SEED_PDF_NAME,
        )
        .first()
    )
    return existing is not None


def seed() -> int:
    """预向量化默认手册。返回写入的 chunk 数量。"""
    if not SEED_PDF_PATH.exists():
        print(f"❌ 种子文件不存在: {SEED_PDF_PATH}")
        sys.exit(1)

    print(f"📄 种子文件: {SEED_PDF_PATH} ({SEED_PDF_PATH.stat().st_size / 1024 / 1024:.1f} MB)")

    # 初始化 DB（确保表存在）
    init_db()
    db = SessionLocal()

    try:
        # 幂等检查
        if already_seeded(db):
            print("✅ 共享知识库已初始化，跳过")
            return 0

        # 预加载向量模型
        print("⏳ 加载向量模型...")
        preload_embeddings()

        # 解析 PDF
        print("📖 解析 PDF...")
        text = parse_file(str(SEED_PDF_PATH), ".pdf")
        if not text or len(text.strip()) < 100:
            print(f"❌ PDF 解析内容过短 ({len(text)} 字符)")
            sys.exit(1)
        print(f"   解析完成: {len(text)} 字符")

        # 切块
        chunks = split_text(text)
        print(f"   切块完成: {len(chunks)} 个块")

        # 创建共享文档记录（user_id=0 表示系统所有）
        doc = Document(
            user_id=0,
            filename=f"seed_{SEED_PDF_NAME}",
            original_name=SEED_PDF_NAME,
            file_type="pdf",
            file_size=SEED_PDF_PATH.stat().st_size,
            chunk_count=len(chunks),
            status="ready",
            is_shared=True,
            is_default=True,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"   DB 记录: doc_id={doc.id}")

        # 向量化写入共享集合
        print("🔢 向量化写入共享集合...")
        store = get_shared_vectorstore()
        store.add_texts(
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

        count = store.count()
        print(f"✅ 共享知识库初始化完成: {count} 个向量块")
        return len(chunks)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
