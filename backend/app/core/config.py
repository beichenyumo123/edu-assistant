"""
应用配置模块
集中管理所有配置项，支持环境变量覆盖
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础
    APP_NAME: str = "EduAssistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库 (SQLite)
    DATABASE_URL: str = "sqlite:///./edu_assistant.db"

    # JWT认证
    SECRET_KEY: str = "your-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # LLM配置 (默认使用DeepSeek，免费额度)
    LLM_PROVIDER: str = "deepseek"  # deepseek | siliconflow | zhipu
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "Qwen/Qwen3.5-397B"

    # 嵌入模型配置（语义搜索）
    EMBEDDING_PROVIDER: str = "siliconflow"          # siliconflow | local
    EMBEDDING_MODEL: str = "BAAI/bge-m3"             # SiliconFlow 上的 embedding 模型
    LOCAL_EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"  # 离线回退模型

    # ChromaDB向量库
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_TOP_K: int = 4

    # 文件上传
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".md"}

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保上传目录和向量库目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
