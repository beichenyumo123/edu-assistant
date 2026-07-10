"""
检索器 - 封装 ChromaDB 查询逻辑

同时查询用户个人集合 (user_{id}) 和共享集合 (shared)，
合并结果按相似度排序。
"""
import os
from typing import List

from sqlalchemy import or_

from ..core.database import SessionLocal
from ..models.document import Document
from .vectorstore import RetrievedDocument, get_vectorstore, get_shared_vectorstore
from ..core.config import settings


SOURCE_TYPE_LABELS = {
    "employee_handbook": "员工手册",
    "policy": "公司制度",
    "workflow": "流程规范",
    "security": "信息安全规范",
    "compliance": "合规资料",
    "training": "岗位培训资料",
    "product_doc": "产品/业务资料",
    "textbook": "培训教材",
    "courseware": "培训课件",
    "teacher_note": "培训讲义",
    "web": "网页资料",
    "student_upload": "历史上传资料",
    "enterprise_upload": "企业上传资料",
}

TRUST_LEVEL_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}


def _document_file_exists(doc: Document) -> bool:
    """检查资料原文件是否仍存在，避免历史残留向量参与检索。"""
    candidates = [
        os.path.join(settings.UPLOAD_DIR, doc.filename),
        os.path.join(settings.UPLOAD_DIR, doc.original_name),
    ]
    return any(path and os.path.exists(path) for path in candidates)


def _active_document_ids(user_id: int, requested_ids: list[int] | None) -> list[int]:
    """返回当前用户可参与检索的 ready 资料 ID（含共享文档）。"""
    db = SessionLocal()
    try:
        query = db.query(Document).filter(
            or_(
                Document.user_id == user_id,
                Document.is_shared == True,  # noqa: E712
            ),
            Document.status == "ready",
        )
        if requested_ids is not None:
            query = query.filter(Document.id.in_(requested_ids))

        docs = query.all()
        # 共享文档无物理文件，跳过文件存在性检查
        return [
            int(doc.id)
            for doc in docs
            if doc.is_shared or _document_file_exists(doc)
        ]
    finally:
        db.close()


def _enrich_doc(doc: RetrievedDocument, score, rank: int) -> RetrievedDocument:
    metadata = dict(doc.metadata or {})

    document_id = str(metadata.get("document_id", "unknown"))
    chunk_index = metadata.get("chunk_index", "?")

    metadata.setdefault("document_name", metadata.get("source", "未知文档"))
    metadata.setdefault("source_type", "enterprise_upload")
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
    """从企业知识库检索相关文档块（个人集合 + 共享集合），并补充证据元数据。"""
    k = top_k or settings.RETRIEVAL_TOP_K
    if document_ids is not None and not document_ids:
        return []

    active_ids = _active_document_ids(user_id, document_ids)
    if not active_ids:
        return []

    normalized_ids = [str(doc_id) for doc_id in active_ids]
    where = (
        {"document_id": normalized_ids[0]}
        if len(normalized_ids) == 1
        else {"document_id": {"$in": normalized_ids}}
    )

    personal_store = get_vectorstore(user_id=user_id)
    shared_store = get_shared_vectorstore()

    def _query_store(store, k_override=None):
        """查询单个向量存储，失败时降级为无分数检索。"""
        kk = k_override or k
        try:
            return store.similarity_search_with_score(query, k=kk, where=where)
        except Exception:
            try:
                docs = store.similarity_search(query, k=kk, where=where)
                return [(doc, None) for doc in docs]
            except Exception:
                return []

    # 分别查询两个集合
    personal_results = _query_store(personal_store)
    shared_results = _query_store(shared_store)

    # 合并、按分数排序（chroma 距离越小越相关，None 排最后）
    all_results = personal_results + shared_results
    all_results.sort(key=lambda x: x[1] if x[1] is not None else float("inf"))
    all_results = all_results[:k]

    # 去重：同名文档保留分数更优的
    seen_doc_names = set()
    deduped = []
    for doc, score in all_results:
        doc_name = (doc.metadata or {}).get("document_name", "")
        if doc_name and doc_name in seen_doc_names:
            continue
        if doc_name:
            seen_doc_names.add(doc_name)
        deduped.append((doc, score))

    return [
        _enrich_doc(doc, score, rank)
        for rank, (doc, score) in enumerate(deduped, 1)
    ]


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
