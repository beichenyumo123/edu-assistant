"""
文档模型 - 记录用户上传的企业培训资料
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # 'pdf'|'docx'|'txt'|'md'
    file_size = Column(Integer, default=0)           # 字节
    chunk_count = Column(Integer, default=0)         # 向量化后的分块数
    status = Column(String(20), default="processing")  # 'processing'|'ready'|'error'
    error_message = Column(String(500), default=None)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
