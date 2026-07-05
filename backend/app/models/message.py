"""
消息模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text, default=None)  # JSON格式：引用的文档来源
    agent_steps = Column(Text, default=None)  # JSON格式：Agent思考步骤
    evaluation = Column(Text, default=None)  # JSON格式：RAG评价指标
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    conversation = relationship("Conversation", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "agent_steps": self.agent_steps,
            "evaluation": self.evaluation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
