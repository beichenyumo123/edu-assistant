"""
对话API - HTTP问答 + WebSocket流式对话
"""
import json
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..models.conversation import Conversation
from ..models.message import Message
from ..schemas.chat import ChatRequest
from ..agents.edu_agent import edu_chat_stream
from .auth import get_current_user

router = APIRouter(tags=["对话"])


def _infer_tool_name(step: str) -> str:
    """根据思考步骤文案补充前端展示用的工具名称。"""
    if any(keyword in step for keyword in ("检索", "文档片段", "知识库", "匹配")):
        return "企业知识检索"
    if any(keyword in step for keyword in ("生成", "回答")):
        return "回答生成"
    if "分析" in step:
        return "问题分析"
    return "Agent"


def _build_agent_step(step: str, started_at: float) -> dict:
    """构造可持久化的 Agent 思考步骤。"""
    return {
        "text": step,
        "tool_name": _infer_tool_name(step),
        "elapsed_ms": max(0, int((time.perf_counter() - started_at) * 1000)),
    }


def _get_history(conv_id: int, db: Session) -> list:
    """获取对话历史（用于上下文）"""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def _normalize_selected_document_ids(value) -> list[int] | None:
    """规范化前端传来的培训资料勾选范围。None 表示全库，[] 表示不检索。"""
    if value is None:
        return None
    if not isinstance(value, list):
        return None

    normalized = []
    for item in value:
        try:
            doc_id = int(item)
        except (TypeError, ValueError):
            continue
        if doc_id > 0 and doc_id not in normalized:
            normalized.append(doc_id)
    return normalized


@router.post("/api/chat/ask")
def chat_ask(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """HTTP同步问答（非流式，用于快速调试）"""
    # 获取或创建对话
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        conv = Conversation(
            user_id=current_user.id,
            agent_type="edu",
            title=req.message[:30] if len(req.message) > 30 else req.message,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 保存用户消息
    user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
    conv.updated_at = datetime.utcnow()
    db.add(user_msg)
    db.commit()

    # 获取历史上下文
    history = _get_history(conv.id, db)
    selected_document_ids = _normalize_selected_document_ids(req.selected_document_ids)

    # 收集Agent流式输出
    full_response = ""
    sources = []
    agent_steps = []
    evaluation = None

    import asyncio
    started_at = time.perf_counter()

    async def _collect():
        nonlocal full_response, sources, agent_steps, evaluation
        stream = edu_chat_stream(
            req.message,
            current_user.id,
            history[:-1],
            selected_document_ids=selected_document_ids,
        )

        async for chunk in stream:
            if chunk["type"] == "thinking":
                agent_steps.append(_build_agent_step(chunk["step"], started_at))
            elif chunk["type"] == "token":
                full_response += chunk["content"]
            elif chunk["type"] == "done":
                sources = chunk.get("sources", [])
                evaluation = chunk.get("evaluation")
                agent_steps.append(_build_agent_step("回答生成完成", started_at))

    asyncio.run(_collect())

    # 保存AI回复
    ai_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=full_response,
        sources=json.dumps(sources, ensure_ascii=False),
        agent_steps=json.dumps(agent_steps, ensure_ascii=False),
        evaluation=json.dumps(evaluation, ensure_ascii=False) if evaluation else None,
    )
    conv.updated_at = datetime.utcnow()
    db.add(ai_msg)
    db.commit()

    return {
        "conversation_id": conv.id,
        "message": {
            "role": "assistant",
            "content": full_response,
            "sources": sources,
            "agent_steps": agent_steps,
            "evaluation": evaluation,
        },
        "agent_steps": agent_steps,
        "evaluation": evaluation,
    }


@router.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: int):
    """
    WebSocket流式对话
    消息格式（客户端→服务端）：
      {"conversation_id": 1, "message": "...", "selected_document_ids": [1, 2]}

    消息格式（服务端→客户端）：
      {"type": "thinking", "step": "..."}
      {"type": "token", "content": "..."}
      {"type": "done", "sources": [...]}
    """
    await websocket.accept()

    # 创建独立的数据库Session
    db = next(get_db())

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            req_data = json.loads(data)

            user_msg_text = req_data.get("message", "")
            conversation_id = req_data.get("conversation_id")
            selected_document_ids = _normalize_selected_document_ids(
                req_data.get("selected_document_ids")
            )

            # 验证用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                await websocket.send_json({"type": "error", "message": "用户不存在"})
                continue

            # 获取或创建对话
            if conversation_id:
                conv = db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                ).first()
                if not conv:
                    await websocket.send_json({"type": "error", "message": "对话不存在"})
                    continue
            else:
                conv = Conversation(
                    user_id=user_id,
                    agent_type="edu",
                    title=user_msg_text[:30] if len(user_msg_text) > 30 else user_msg_text,
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)

            # 保存用户消息
            user_msg = Message(conversation_id=conv.id, role="user", content=user_msg_text)
            conv.updated_at = datetime.utcnow()
            db.add(user_msg)
            db.commit()

            # 先发送conversation_id
            await websocket.send_json({"type": "meta", "conversation_id": conv.id})

            # 获取历史
            history = _get_history(conv.id, db)

            # 流式推送Agent回复
            full_response = ""
            sources = []
            agent_steps = []
            evaluation = None
            started_at = time.perf_counter()

            stream = edu_chat_stream(
                user_msg_text,
                user_id,
                history[:-1],
                selected_document_ids=selected_document_ids,
            )

            async for chunk in stream:
                if chunk["type"] == "thinking":
                    step = _build_agent_step(chunk["step"], started_at)
                    agent_steps.append(step)
                    await websocket.send_json({"type": "thinking", "step": step["text"], **step})
                elif chunk["type"] == "token":
                    full_response += chunk["content"]
                    await websocket.send_json({"type": "token", "content": chunk["content"]})
                elif chunk["type"] == "done":
                    full_response = chunk.get("content", full_response)
                    sources = chunk.get("sources", [])
                    evaluation = chunk.get("evaluation")
                    agent_steps.append(_build_agent_step("回答生成完成", started_at))

            # 发送完成信号
            await websocket.send_json({
                "type": "done",
                "sources": sources,
                "agent_steps": agent_steps,
                "evaluation": evaluation,
            })

            # 保存AI消息
            ai_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_response,
                sources=json.dumps(sources, ensure_ascii=False),
                agent_steps=json.dumps(agent_steps, ensure_ascii=False),
                evaluation=json.dumps(evaluation, ensure_ascii=False) if evaluation else None,
            )
            conv.updated_at = datetime.utcnow()
            db.add(ai_msg)
            db.commit()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        db.close()
