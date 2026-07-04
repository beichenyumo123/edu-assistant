"""
教育助手Agent
处理学习资料相关的问答、摘要、知识点提取等任务
"""
from typing import AsyncGenerator, Dict

from .llm import get_llm
from ..rag.retriever import retrieve_relevant_chunks, format_retrieved_context


EDU_SYSTEM_PROMPT = """你是 EduAssistant 教育助手，一位专业、耐心的AI学习导师。

回答规则：
- 优先基于提供的参考资料回答，回答时用【来源X】标注引用
- 如果参考资料不足，可以结合通用学习方法补充，但要明确说明
- 使用Markdown格式组织回答
- 对关键概念给出例子帮助理解
"""


async def edu_chat_stream(
    query: str,
    user_id: int,
    conversation_history: list = None,
) -> AsyncGenerator[Dict, None]:
    """教育助手流式对话。"""
    yield {"type": "thinking", "step": "正在检索知识库..."}
    docs = retrieve_relevant_chunks(query, user_id=user_id)
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
            "document_id": doc.metadata.get("document_id", "未知"),
            "document_name": doc.metadata.get("document_name", "未知文档"),
            "chunk_index": doc.metadata.get("chunk_index", "?"),
            "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
        }
        for doc in docs
    ]

    yield {"type": "done", "content": full_response, "sources": sources}
