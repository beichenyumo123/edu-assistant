"""
Embedding 模型工厂

优先使用 SiliconFlow 的云端 embedding API；未配置 API Key 时自动降级到
本地 sentence-transformers 模型，保证离线环境也能跑通语义检索流程。
"""
from __future__ import annotations

from ..core.config import settings


def _is_real_key(value: str) -> bool:
    """判断是否为真实 API Key（排除占位符和示例值）。"""
    return bool(value and value.strip() and not value.lower().startswith(("your_", "sk-xxx", "change-")))


def get_embeddings():
    """
    获取 embedding 函数实例。

    - 配置 SiliconFlow API Key 时：使用 OpenAIEmbeddings（兼容 SiliconFlow API）
    - 未配置时：使用本地 HuggingFaceEmbeddings（sentence-transformers）
    """
    provider = (settings.EMBEDDING_PROVIDER or "").lower()
    has_silicon_key = _is_real_key(settings.SILICONFLOW_API_KEY)
    use_api = provider == "siliconflow" and has_silicon_key

    if use_api:
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise RuntimeError(
                "SiliconFlow embedding is configured but langchain-openai is not installed. "
                "Run: pip install langchain-openai"
            ) from exc

        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_BASE_URL,
        )

    # 本地离线回退
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "No embedding API key configured and langchain-huggingface is not installed. "
            "Run: pip install langchain-huggingface sentence-transformers"
        ) from exc

    return HuggingFaceEmbeddings(model_name=settings.LOCAL_EMBEDDING_MODEL)
