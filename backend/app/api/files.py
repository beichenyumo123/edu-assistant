"""
文件管理API - 上传、列表、删除
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..models.document import Document
from ..rag.loader import parse_file, split_text
from ..rag.vectorstore import get_vectorstore
from .auth import get_current_user

router = APIRouter(prefix="/api/files", tags=["文件管理"])


def validate_file(filename: str) -> str:
    """验证文件类型，返回扩展名"""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。支持: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    return ext

def infer_source_profile(filename: str, file_type: str) -> dict:
    """根据文件名粗略推断资料类型和可信等级。"""
    name = (filename or "").lower()

    rules = [
        ("employee_handbook", "high", ["员工手册", "新人手册", "入职手册", "handbook", "onboarding"]),
        ("policy", "high", ["制度", "规章", "政策", "办法", "规范", "policy", "policies"]),
        ("workflow", "high", ["流程", "报销", "审批", "请假", "差旅", "采购", "workflow", "process", "sop"]),
        ("security", "high", ["信息安全", "数据安全", "保密", "权限", "账号", "security", "privacy"]),
        ("compliance", "high", ["合规", "廉洁", "反舞弊", "行为准则", "compliance", "ethics"]),
        ("training", "medium", ["培训", "课程", "课件", "讲义", "training", "courseware", "slides", "ppt"]),
        ("product_doc", "medium", ["产品", "业务", "客户", "方案", "product", "business"]),
        ("web", "low", ["网页", "博客", "web", "blog"]),
    ]

    for source_type, trust_level, keywords in rules:
        if any(keyword in name for keyword in keywords):
            return {"source_type": source_type, "trust_level": trust_level}

    return {"source_type": "enterprise_upload", "trust_level": "medium"}


def _document_file_exists(doc: Document) -> bool:
    """兼容历史数据：入库文件名或原始文件名任一存在即可读取。"""
    candidates = [
        os.path.join(settings.UPLOAD_DIR, doc.filename),
        os.path.join(settings.UPLOAD_DIR, doc.original_name),
    ]
    return any(path and os.path.exists(path) for path in candidates)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传企业培训资料并自动向量化"""
    # 验证文件类型
    ext = validate_file(file.filename)

    # 检查文件大小
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大: {file_size_mb:.1f}MB。限制: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # 保存文件
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, unique_name)
    with open(save_path, "wb") as f:
        f.write(content)

    # 创建数据库记录
    doc = Document(
        user_id=current_user.id,
        filename=unique_name,
        original_name=file.filename,
        file_type=ext.lstrip("."),
        file_size=len(content),
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 异步向量化（这里同步处理，生产环境建议用Celery等任务队列）
    try:
        # 解析文件文本
        text = parse_file(save_path, ext)
        if not text or len(text.strip()) < 10:
            raise ValueError("文件内容为空或过短")

        # 文本分块
        chunks = split_text(text)
        source_profile = infer_source_profile(doc.original_name, doc.file_type)

        # 存入ChromaDB（用user_id隔离）
        vectorstore = get_vectorstore(user_id=current_user.id)
        vectorstore.add_texts(
            texts=chunks,
            metadatas=[
                {
                    "document_id": str(doc.id),
                    "document_name": doc.original_name,
                    "chunk_index": i,
                    "file_type": doc.file_type,
                    "source_type": source_profile["source_type"],
                    "trust_level": source_profile["trust_level"],
                }
                for i in range(len(chunks))
            ],
        )

        # 更新文档状态
        doc.status = "ready"
        doc.chunk_count = len(chunks)
    except Exception as e:
        doc.status = "error"
        doc.error_message = str(e)

    db.commit()
    db.refresh(doc)

    return {"success": doc.status == "ready", "file": doc.to_dict()}


@router.get("")
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的文件列表（含共享文档）"""
    docs = (
        db.query(Document)
        .filter(
            or_(
                Document.user_id == current_user.id,
                Document.is_shared == True,  # noqa: E712
            )
        )
        .order_by(Document.created_at.desc())
        .all()
    )
    files = []
    for doc in docs:
        item = doc.to_dict()
        # 共享文档的种子文件在 deploy/seeds/，不检查 uploads 目录
        if doc.status == "ready" and not doc.is_shared and not _document_file_exists(doc):
            item["status"] = "error"
            item["error_message"] = "资料文件缺失，请重新上传"
        files.append(item)
    return {"files": files}


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除文件及对应的向量数据（系统默认文档不可删除）"""
    doc = db.query(Document).filter(Document.id == file_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    if doc.is_default:
        raise HTTPException(status_code=403, detail="系统默认文档不可删除")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此文件")

    # 删除ChromaDB中的向量数据
    try:
        vectorstore = get_vectorstore(user_id=current_user.id)
        # 删除该文档所有分块
        vectorstore.delete(where={"document_id": str(doc.id)})
    except Exception:
        pass  # 向量删除失败不影响文件记录删除

    # 删除物理文件
    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(doc)
    db.commit()
    return {"success": True, "message": "文件已删除"}
