"""
Embedding 模型工厂

统一使用本地 sentence-transformers 模型，避免上传向量化和查询检索
使用不同 embedding 模型导致向量空间不一致。
"""
from __future__ import annotations

import os
from functools import lru_cache

from ..core.config import settings


@lru_cache(maxsize=1)
def get_embeddings():
    """
    获取本地 embedding 函数单例。

    上传文件向量化、用户问题向量匹配都复用这个实例，保证模型只在
    当前后端进程中加载一次。
    """
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "Local embedding requires langchain-huggingface and sentence-transformers. "
            "Run: pip install langchain-huggingface sentence-transformers"
        ) from exc

    try:
        return HuggingFaceEmbeddings(
            model_name=settings.LOCAL_EMBEDDING_MODEL,
            model_kwargs={"local_files_only": True},
            encode_kwargs={"normalize_embeddings": True},
        )
    except Exception as exc:
        raise RuntimeError(
            f"Local embedding model is not available in cache: {settings.LOCAL_EMBEDDING_MODEL}. "
            "Please download it once before starting the backend."
        ) from exc


def preload_embeddings() -> None:
    """启动时预加载 embedding 模型，后续请求复用缓存实例。"""
    get_embeddings()
