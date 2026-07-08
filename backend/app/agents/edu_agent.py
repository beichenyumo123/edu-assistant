"""
企业入职培训 Agent
处理公司制度、流程规范、岗位培训资料相关的问答任务
"""
from typing import AsyncGenerator, Dict

from .llm import get_llm
from ..core.config import settings
from ..rag.evaluation import evaluate_rag_answer
from ..rag.retriever import retrieve_relevant_chunks, format_retrieved_context


EDU_SYSTEM_PROMPT = """你是 OnboardAgent 企业新员工入职培训助手，一位专业、谨慎、耐心的企业知识助理。

回答规则：
- 优先基于公司已上传的员工手册、规章制度、流程规范、信息安全和岗位培训资料回答
- 涉及考勤、报销、权限、合规、安全等关键要求时，必须用【来源X】标注引用
- 优先采信员工手册、正式制度、流程规范和安全合规文档；普通培训材料可作为辅助
- 如果参考资料不足或与问题无关，要明确说明“当前知识库没有足够依据”，不要强行编造制度
- 可以补充通用入职建议，但必须和公司资料依据区分开
- 涉及合同、薪酬、法律或纪律处分等高风险事项时，提醒新员工以 HR、法务或直属负责人确认为准
- 使用 Markdown 格式组织回答
"""


async def edu_chat_stream(
    query: str,
    user_id: int,
    conversation_history: list = None,
    selected_document_ids: list[int] | None = None,
    memory_context: str | None = None,
) -> AsyncGenerator[Dict, None]:
    """入职培训助手流式对话。"""
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
        yield {"type": "thinking", "step": "未找到匹配的培训资料，将给出通用入职建议"}

    history_text = ""
    if conversation_history:
        recent = conversation_history[-6:]
        history_text = "\n".join(f"{msg.get('role')}: {msg.get('content')}" for msg in recent)

    prompt = f"""{EDU_SYSTEM_PROMPT}

历史对话：
{history_text or "（无）"}

用户记忆：
{memory_context or "（暂无稳定偏好）"}

参考资料：
{context}

用户问题：{query}

请基于以上参考资料回答用户问题。如果参考资料充分，用【来源X】标注出处。"""

    yield {"type": "thinking", "step": "正在生成回答..."}

    full_response = ""
    try:
        llm = get_llm(temperature=0.7)
        async for chunk in llm.astream(prompt):
            content = chunk.content
            if content:
                full_response += content
                yield {"type": "token", "content": content}
    except Exception as exc:
        full_response = (
            "抱歉，生成回答时出错了。企业知识库检索已经完成，但调用大模型生成答案失败。\n\n"
            f"错误类型：{type(exc).__name__}\n\n"
            "请检查 DeepSeek API Key、模型名、base_url 或当前网络/代理配置后重试。"
        )
        yield {"type": "thinking", "step": "回答生成失败，已返回错误提示"}
        yield {"type": "token", "content": full_response}

    sources = [
        {
            "source_no": index,
            "document_id": doc.metadata.get("document_id", "未知"),
            "document_name": doc.metadata.get("document_name", "未知文档"),
            "chunk_index": doc.metadata.get("chunk_index", "?"),
            "evidence_id": doc.metadata.get("evidence_id"),
            "source_type": doc.metadata.get("source_type", "enterprise_upload"),
            "trust_level": doc.metadata.get("trust_level", "medium"),
            "retrieval_rank": doc.metadata.get("retrieval_rank"),
            "retrieval_score": doc.metadata.get("retrieval_score"),
            "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
        }
        for index, doc in enumerate(docs, 1)
    ]

    evaluation = evaluate_rag_answer(
        query=query,
        answer=full_response,
        docs=docs,
        selected_document_ids=selected_document_ids,
        top_k=settings.RETRIEVAL_TOP_K,
    )

    yield {
        "type": "done",
        "content": full_response,
        "sources": sources,
        "evaluation": evaluation,
    }
