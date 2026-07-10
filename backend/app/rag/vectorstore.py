"""
ChromaDB 语义向量存储模块

按用户隔离 Collection，提供 add_texts / similarity_search / delete 方法。
接口与旧 LocalVectorStore 完全兼容，调用方无需改动。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma

from ..core.config import settings
from .embeddings import get_embeddings


@dataclass
class RetrievedDocument:
    """检索返回的文档块，字段兼容 LangChain Document 的常用访问方式。"""

    page_content: str
    metadata: dict


class ChromaVectorStore:
    """按用户隔离的 ChromaDB 语义向量存储。"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.collection_name = f"user_{user_id}"
        self.persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_fn = get_embeddings()
        self._store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self._embedding_fn,
            persist_directory=str(self.persist_dir),
        )

    def add_texts(self, texts: Iterable[str], metadatas: Iterable[dict] | None = None) -> None:
        """添加文本块到向量库，使用确定性 ID 确保幂等。"""
        texts_list = list(texts)
        metadata_list = list(metadatas) if metadatas else []
        if not texts_list:
            return

        ids = [
            f"{self.collection_name}_{metadata_list[i].get('document_id', 'unknown')}_{metadata_list[i].get('chunk_index', i)}"
            if i < len(metadata_list)
            else f"{self.collection_name}_{i}"
            for i in range(len(texts_list))
        ]
        self._store.add_texts(texts=texts_list, metadatas=metadata_list, ids=ids)

    def similarity_search(
        self, query: str, k: int = 4, where: dict | None = None
    ) -> list[RetrievedDocument]:
        """语义检索，返回最相关的 k 个文档块。"""
        lc_docs = self._store.similarity_search(query, k=k, filter=where)
        return [
            RetrievedDocument(page_content=doc.page_content, metadata=doc.metadata or {})
            for doc in lc_docs
        ]

    def similarity_search_with_score(
        self, query: str, k: int = 4, where: dict | None = None
    ) -> list[tuple[RetrievedDocument, float]]:
        """语义检索，返回带余弦距离的 (文档块, 分数) 列表。

        分数为余弦距离（0 = 完全相同，2 = 完全相反），越小越相关。
        """
        lc_results = self._store.similarity_search_with_score(query, k=k, filter=where)
        return [
            (RetrievedDocument(page_content=doc.page_content, metadata=doc.metadata or {}), score)
            for doc, score in lc_results
        ]

    def delete(self, where: dict | None = None) -> None:
        """按条件删除文档块。where=None 时清空该用户全部数据。"""
        if where is None:
            # 清空集合：取所有 ID 后删除
            results = self._store.get()
            if results and results.get("ids"):
                self._store.delete(ids=results["ids"])
        else:
            results = self._store.get(where=where)
            if results and results.get("ids"):
                self._store.delete(ids=results["ids"])


def get_vectorstore(user_id: int) -> ChromaVectorStore:
    """获取指定用户的 ChromaDB 向量存储。"""
    return ChromaVectorStore(user_id=user_id)


class SharedVectorStore:
    """全局共享的 ChromaDB 向量存储，用于系统默认文档。

    所有用户共享同一个 shared 集合，部署时预向量化一次即可。
    API 表面与 ChromaVectorStore 一致。
    """

    COLLECTION_NAME = "shared"

    def __init__(self):
        self.persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_fn = get_embeddings()
        self._store = Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            persist_directory=str(self.persist_dir),
        )

    def add_texts(self, texts: Iterable[str], metadatas: Iterable[dict] | None = None) -> None:
        """添加文本块到共享向量库，使用确定性 ID 确保幂等（可重复运行 seed 脚本）。"""
        texts_list = list(texts)
        metadata_list = list(metadatas) if metadatas else []
        if not texts_list:
            return

        ids = [
            f"shared_{metadata_list[i].get('document_id', 'unknown')}_{metadata_list[i].get('chunk_index', i)}"
            if i < len(metadata_list)
            else f"shared_{i}"
            for i in range(len(texts_list))
        ]
        self._store.add_texts(texts=texts_list, metadatas=metadata_list, ids=ids)

    def similarity_search(
        self, query: str, k: int = 4, where: dict | None = None
    ) -> list[RetrievedDocument]:
        lc_docs = self._store.similarity_search(query, k=k, filter=where)
        return [
            RetrievedDocument(page_content=doc.page_content, metadata=doc.metadata or {})
            for doc in lc_docs
        ]

    def similarity_search_with_score(
        self, query: str, k: int = 4, where: dict | None = None
    ) -> list[tuple[RetrievedDocument, float]]:
        lc_results = self._store.similarity_search_with_score(query, k=k, filter=where)
        return [
            (RetrievedDocument(page_content=doc.page_content, metadata=doc.metadata or {}), score)
            for doc, score in lc_results
        ]

    def delete(self, where: dict | None = None) -> None:
        if where is None:
            results = self._store.get()
            if results and results.get("ids"):
                self._store.delete(ids=results["ids"])
        else:
            results = self._store.get(where=where)
            if results and results.get("ids"):
                self._store.delete(ids=results["ids"])

    def count(self) -> int:
        """返回共享集合中的向量块数量。"""
        results = self._store.get()
        return len(results["ids"]) if results and results.get("ids") else 0


_shared_store: SharedVectorStore | None = None


def get_shared_vectorstore() -> SharedVectorStore:
    """获取共享向量存储单例（所有用户共享的系统默认文档）。"""
    global _shared_store
    if _shared_store is None:
        _shared_store = SharedVectorStore()
    return _shared_store


def delete_user_collection(user_id: int) -> None:
    """删除用户的所有向量数据（直接移除整个 ChromaDB Collection）。"""
    import chromadb
    from chromadb.errors import NotFoundError

    persist_dir = str(Path(settings.CHROMA_PERSIST_DIR))
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection(f"user_{user_id}")
    except (ValueError, NotFoundError):
        pass  # Collection 不存在时无需处理
