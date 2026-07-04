"""
工具API - 摘要生成、知识点提取等独立工具
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..models.document import Document
from ..rag.loader import parse_file
from ..rag.retriever import format_retrieved_context
from ..agents.llm import get_llm
from ..core.config import settings
from .auth import get_current_user

import os

router = APIRouter(prefix="/api/tools", tags=["工具"])


@router.post("/summarize")
def summarize_document(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成文档摘要"""
    doc_id = body.get("document_id")
    length = body.get("length", "medium")

    doc = db.query(Document).filter(
        Document.id == doc_id, Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 读取文件文本
    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    text = parse_file(file_path, f".{doc.file_type}")

    # 截取前4000字做摘要
    text_preview = text[:4000]

    length_prompts = {
        "short": "请用2-3句话简要总结",
        "medium": "请用一段话总结核心内容，包含3-5个要点",
        "long": "请详细总结，包含主要论点和支撑细节",
    }

    prompt = f"""{length_prompts.get(length, length_prompts["medium"])}。

原文内容：
{text_preview}

请直接给出摘要，使用Markdown格式。"""

    llm = get_llm(temperature=0.3)
    result = llm.invoke(prompt)

    return {"summary": result.content, "document_id": doc_id}


@router.post("/extract-knowledge")
def extract_knowledge(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提取知识点"""
    doc_id = body.get("document_id")

    doc = db.query(Document).filter(
        Document.id == doc_id, Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    text = parse_file(file_path, f".{doc.file_type}")
    text_preview = text[:5000]

    prompt = f"""请从以下内容中提取关键知识点，每个知识点包含：
- 标题（简洁的知识点名称）
- 简要说明（1-2句话解释）

输出格式（JSON数组）：
[
  {{"title": "知识点名称", "description": "简要说明"}},
  ...
]

原文内容：
{text_preview}"""

    llm = get_llm(temperature=0.3)
    result = llm.invoke(prompt)

    # 尝试解析JSON
    import json
    try:
        # 提取JSON部分
        content = result.content
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            knowledge_points = json.loads(content[start:end])
        else:
            knowledge_points = [{"title": "解析失败", "description": content}]
    except Exception:
        knowledge_points = [{"title": "知识点", "description": result.content}]

    return {"knowledge_points": knowledge_points, "document_id": doc_id}
