"""
文件相关 Pydantic Schema
"""
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """文件信息"""
    id: int
    original_name: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    is_shared: bool = False
    is_default: bool = False
    created_at: str


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    file: FileInfo | None = None
    message: str = ""
