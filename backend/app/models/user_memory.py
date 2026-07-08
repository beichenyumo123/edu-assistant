"""
用户 AI 记忆模型
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..core.database import Base


class UserMemory(Base):
    """记录用户在入职培训助手中的稳定使用偏好。"""

    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    memory_enabled = Column(Boolean, default=True)
    question_count = Column(Integer, default=0)
    topic_counts = Column(Text, default="{}")
    style_counts = Column(Text, default="{}")
    tone_counts = Column(Text, default="{}")
    document_usage = Column(Text, default="{}")
    last_used_documents = Column(Text, default="[]")
    last_selected_document_ids = Column(Text, default="[]")
    preferred_answer_style = Column(String(50), default="结构化")
    communication_tone = Column(String(50), default="专业清晰")
    last_question = Column(Text, default=None)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
