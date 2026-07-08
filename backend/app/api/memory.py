"""
AI 记忆 API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..services.user_memory import clear_user_memory, get_memory_summary, update_memory_settings
from .auth import get_current_user

router = APIRouter(tags=["AI记忆"])


class MemoryUpdateRequest(BaseModel):
    """更新 AI 记忆偏好请求。"""

    memory_enabled: bool | None = Field(None, description="是否开启 AI 记忆")
    preferred_answer_style: str | None = Field(
        None,
        description="回答风格：结构化 | 简洁 | 详细 | 步骤化 | 表格化",
    )
    communication_tone: str | None = Field(
        None,
        description="沟通语气：专业清晰 | 直接高效 | 耐心详细 | 结构清晰",
    )


@router.get("/api/memory/me")
def get_my_memory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的 AI 记忆画像。"""
    return {"memory": get_memory_summary(db, current_user)}


@router.patch("/api/memory/me")
def update_my_memory(
    req: MemoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户的 AI 记忆偏好。"""
    try:
        update_memory_settings(
            db,
            current_user,
            memory_enabled=req.memory_enabled,
            preferred_answer_style=req.preferred_answer_style,
            communication_tone=req.communication_tone,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()
    return {"memory": get_memory_summary(db, current_user)}


@router.delete("/api/memory/me")
def clear_my_memory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清空当前用户的 AI 记忆。"""
    clear_user_memory(db, current_user)
    db.commit()
    return {
        "message": "AI记忆已清空",
        "memory": get_memory_summary(db, current_user),
    }
