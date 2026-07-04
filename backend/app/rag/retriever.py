"""
检索器 - 封装ChromaDB查询逻辑
"""
from typing import List
from .vectorstore import RetrievedDocument, get_vectorstore
from ..core.config import settings


def retrieve_relevant_chunks(
    query: str,
    user_id: int,
    top_k: int = None,
) -> List[RetrievedDocument]:
    """
    从用户的知识库中检索与查询最相关的文档块

    Args:
        query: 用户查询文本
        user_id: 用户ID（用于隔离知识库）
        top_k: 返回的块数，默认使用配置值

    Returns:
        相关文档块列表
    """
    k = top_k or settings.RETRIEVAL_TOP_K
    vectorstore = get_vectorstore(user_id=user_id)

    # 相似度检索
    docs = vectorstore.similarity_search(query, k=k)
    return docs


def format_retrieved_context(docs: List[RetrievedDocument]) -> str:
    """
    将检索到的文档块格式化为LLM可用的上下文字符串
    """
    if not docs:
        return "（未找到相关知识库内容）"

    context_parts = []
    for i, doc in enumerate(docs, 1):
        doc_id = doc.metadata.get("document_id", "未知")
        doc_name = doc.metadata.get("document_name", "未知文档")
        chunk_idx = doc.metadata.get("chunk_index", "?")
        context_parts.append(f"[来源{i}] {doc_name}（文档ID:{doc_id} 块:{chunk_idx}）\n{doc.page_content}")

    return "\n\n---\n\n".join(context_parts)
