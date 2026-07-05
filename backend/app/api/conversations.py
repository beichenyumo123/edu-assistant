"""
对话管理API - 列表、详情、删除
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..models.conversation import Conversation
from ..models.message import Message
from .auth import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["对话管理"])


@router.get("")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有对话"""
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return {"conversations": [c.to_dict() for c in convs]}


@router.get("/{conv_id}")
def get_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取对话详情（含所有消息）"""
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    # 解析sources JSON
    import json
    msg_list = []
    for m in messages:
        d = m.to_dict()
        if m.sources and m.role == "assistant":
            try:
                d["sources"] = json.loads(m.sources)
            except Exception:
                d["sources"] = []
        else:
            d["sources"] = []
        if m.agent_steps and m.role == "assistant":
            try:
                d["agent_steps"] = json.loads(m.agent_steps)
            except Exception:
                d["agent_steps"] = []
        else:
            d["agent_steps"] = []
        if m.evaluation and m.role == "assistant":
            try:
                d["evaluation"] = json.loads(m.evaluation)
            except Exception:
                d["evaluation"] = None
        else:
            d["evaluation"] = None
        msg_list.append(d)

    return {"conversation": conv.to_dict(), "messages": msg_list}


@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除对话及其所有消息"""
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.delete(conv)
    db.commit()
    return {"success": True, "message": "对话已删除"}
