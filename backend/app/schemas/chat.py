"""
对话相关 Pydantic Schema
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """发送消息请求"""
    conversation_id: int | None = Field(None, description="对话ID（为空则创建新对话）")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")
    agent_type: str = Field(default="edu", description="兼容旧客户端字段；当前统一使用入职培训助手")
    selected_document_ids: list[int] | None = Field(
        None,
        description="入职培训资料检索范围；为空表示全知识库，空数组表示不检索任何资料",
    )


class ChatResponse(BaseModel):
    """对话响应"""
    conversation_id: int
    message: dict  # {role, content, sources, agent_steps, evaluation}
    agent_steps: list = Field(default_factory=list, description="Agent执行步骤")
    evaluation: dict | None = Field(default=None, description="RAG在线评价指标")


class ConversationCreate(BaseModel):
    """创建对话"""
    agent_type: str = Field(default="edu", description="兼容旧字段；当前统一为 edu")
    title: str = Field(default="新对话", max_length=200)


class ConversationUpdate(BaseModel):
    """更新对话"""
    title: str | None = Field(None, max_length=200)


class SummaryRequest(BaseModel):
    """摘要生成请求"""
    document_id: int = Field(..., description="文档ID")
    length: str = Field(default="medium", description="摘要长度：short | medium | long")


class KnowledgeExtractRequest(BaseModel):
    """培训知识卡片提取请求"""
    document_id: int = Field(..., description="文档ID")
