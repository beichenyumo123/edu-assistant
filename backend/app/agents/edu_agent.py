"""
教育助手Agent
处理学习资料相关的问答、摘要、知识点提取等任务
"""
from typing import AsyncGenerator, Dict

from .llm import get_llm
from ..rag.retriever import retrieve_relevant_chunks, format_retrieved_context


EDU_SYSTEM_PROMPT = """你是 EduAssistant 教育助手，一位专业、耐心的 AI 学习导师。

回答规则：
- 优先基于提供的参考资料回答，关键结论必须用【来源X】标注引用
- 优先采信教材、课件、教师笔记等高可信资料
- 学生上传资料和网页资料可以作为辅助，但不能单独支撑强结论
- 如果参考资料不足或与问题无关，要明确说明“当前知识库没有足够依据”，不要强行编造
- 可以补充通用学习建议，但必须和资料依据区分开
- 使用 Markdown 格式组织回答
"""


async def edu_chat_stream(
    query: str,
    user_id: int,
    conversation_history: list = None,
    selected_document_ids: list[int] | None = None,
) -> AsyncGenerator[Dict, None]:
    """教育助手流式对话。"""
    if selected_document_ids is not None:
        selected_count = len(selected_document_ids)
        yield {"type": "thinking", "step": f"正在检索已勾选的 {selected_count} 份资料..."}
    else:
        yield {"type": "thinking", "step": "正在检索知识库..."}

    docs = retrieve_relevant_chunks(
        query,
        user_id=user_id,
        document_ids=selected_document_ids,
    )
    context = format_retrieved_context(docs)

    if docs:
        yield {"type": "thinking", "step": f"找到 {len(docs)} 个相关文档片段"}
    else:
        yield {"type": "thinking", "step": "未找到匹配的知识库内容，将给出通用学习建议"}

    history_text = ""
    if conversation_history:
        recent = conversation_history[-6:]
        history_text = "\n".join(f"{msg.get('role')}: {msg.get('content')}" for msg in recent)

    prompt = f"""{EDU_SYSTEM_PROMPT}

历史对话：
{history_text or "（无）"}

参考资料：
{context}

用户问题：{query}

请基于以上参考资料回答用户问题。如果参考资料充分，用【来源X】标注出处。"""

    yield {"type": "thinking", "step": "正在生成回答..."}

    llm = get_llm(temperature=0.7)
    full_response = ""
    async for chunk in llm.astream(prompt):
        content = chunk.content
        if content:
            full_response += content
            yield {"type": "token", "content": content}

    sources = [
        {
            "source_no": index,
            "document_id": doc.metadata.get("document_id", "未知"),
            "document_name": doc.metadata.get("document_name", "未知文档"),
            "chunk_index": doc.metadata.get("chunk_index", "?"),
            "evidence_id": doc.metadata.get("evidence_id"),
            "source_type": doc.metadata.get("source_type", "student_upload"),
            "trust_level": doc.metadata.get("trust_level", "medium"),
            "retrieval_rank": doc.metadata.get("retrieval_rank"),
            "retrieval_score": doc.metadata.get("retrieval_score"),
            "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
        }
        for index, doc in enumerate(docs, 1)
    ]

    yield {"type": "done", "content": full_response, "sources": sources}
