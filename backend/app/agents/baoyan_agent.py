"""
保研助手Agent
处理院校查询、推免时间线、条件匹配等保研场景
"""
from typing import AsyncGenerator, Dict

from .llm import get_llm


BAOYAN_SYSTEM_PROMPT = """你是 EduAssistant 保研助手，一位熟悉保研流程的学习规划顾问。

回答规则：
- 给出结构化、可操作的建议
- 提醒用户以目标院校官网最新通知为准
- 使用Markdown格式组织回答
"""


async def baoyan_chat_stream(
    query: str,
    user_id: int = None,
    conversation_history: list = None,
) -> AsyncGenerator[Dict, None]:
    """保研助手流式对话。"""
    yield {"type": "thinking", "step": "正在分析保研相关问题..."}

    history_text = ""
    if conversation_history:
        recent = conversation_history[-6:]
        history_text = "\n".join(f"{msg.get('role')}: {msg.get('content')}" for msg in recent)

    prompt = f"""{BAOYAN_SYSTEM_PROMPT}

历史对话：
{history_text or "（无）"}

用户问题：{query}

请从准备材料、时间节点、信息核验和下一步行动四个角度给出建议。"""

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
            "抱歉，生成回答时出错了。当前调用大模型生成答案失败。\n\n"
            f"错误类型：{type(exc).__name__}\n\n"
            "请检查 DeepSeek API Key、模型名、base_url 或当前网络/代理配置后重试。"
        )
        yield {"type": "thinking", "step": "回答生成失败，已返回错误提示"}
        yield {"type": "token", "content": full_response}

    yield {"type": "done", "content": full_response, "sources": []}
