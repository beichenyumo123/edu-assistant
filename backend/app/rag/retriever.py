"""
检索器 - 封装 ChromaDB 查询逻辑
"""
from typing import List
from .vectorstore import RetrievedDocument, get_vectorstore
from ..core.config import settings


SOURCE_TYPE_LABELS = {
    "textbook": "教材",
    "courseware": "课件",
    "exercise": "习题",
    "teacher_note": "教师笔记",
    "web": "网页资料",
    "student_upload": "学生上传资料",
}

TRUST_LEVEL_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}


def _enrich_doc(doc: RetrievedDocument, score, rank: int) -> RetrievedDocument:
    metadata = dict(doc.metadata or {})

    document_id = str(metadata.get("document_id", "unknown"))
    chunk_index = metadata.get("chunk_index", "?")

    metadata.setdefault("document_name", metadata.get("source", "未知文档"))
    metadata.setdefault("source_type", "student_upload")
    metadata.setdefault("trust_level", "medium")
    metadata["evidence_id"] = f"doc{document_id}_chunk{chunk_index}"
    metadata["retrieval_rank"] = rank

    if score is not None:
        metadata["retrieval_score"] = float(score)
        metadata["retrieval_score_type"] = "chroma_distance_lower_is_better"

    return RetrievedDocument(page_content=doc.page_content, metadata=metadata)


def retrieve_relevant_chunks(
    query: str,
    user_id: int,
    top_k: int = None,
    document_ids: list[int] | None = None,
) -> List[RetrievedDocument]:
    """从用户知识库检索相关文档块，并补充证据元数据。"""
    k = top_k or settings.RETRIEVAL_TOP_K
    if document_ids is not None and not document_ids:
        return []

    where = None
    if document_ids:
        normalized_ids = [str(doc_id) for doc_id in document_ids]
        where = (
            {"document_id": normalized_ids[0]}
            if len(normalized_ids) == 1
            else {"document_id": {"$in": normalized_ids}}
        )

    vectorstore = get_vectorstore(user_id=user_id)

    try:
        scored_docs = vectorstore.similarity_search_with_score(query, k=k, where=where)
        return [
            _enrich_doc(doc, score, rank)
            for rank, (doc, score) in enumerate(scored_docs, 1)
        ]
    except Exception as exc:
        try:
            docs = vectorstore.similarity_search(query, k=k, where=where)
            return [_enrich_doc(doc, None, rank) for rank, doc in enumerate(docs, 1)]
        except Exception as fallback_exc:
            print(f"⚠️ 知识库检索失败，已跳过本次 RAG 检索: {fallback_exc or exc}")
            return []


def format_retrieved_context(docs: List[RetrievedDocument]) -> str:
    """将检索到的文档块格式化为 LLM 可用的证据上下文。"""
    if not docs:
        return "（未找到相关知识库内容）"

    context_parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        doc_name = meta.get("document_name", "未知文档")
        chunk_idx = meta.get("chunk_index", "?")
        evidence_id = meta.get("evidence_id", f"source_{i}")
        source_type = SOURCE_TYPE_LABELS.get(meta.get("source_type"), meta.get("source_type", "未知"))
        trust_level = TRUST_LEVEL_LABELS.get(meta.get("trust_level"), meta.get("trust_level", "未知"))
        score = meta.get("retrieval_score")
        score_text = f"{score:.4f}，越小越相关" if isinstance(score, (int, float)) else "未知"

        context_parts.append(
            f"[来源{i} | {evidence_id}]\n"
            f"文档：{doc_name}\n"
            f"资料类型：{source_type}\n"
            f"可信等级：{trust_level}\n"
            f"chunk：{chunk_idx}\n"
            f"检索距离：{score_text}\n"
            f"正文：{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)
