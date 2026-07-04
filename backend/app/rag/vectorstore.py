"""
轻量知识库存储模块

Sprint1 的目标是先跑通“上传资料 -> 分块入库 -> 检索问答”的闭环。
这里使用本地 JSON 文件实现一个可离线运行的检索存储；后续若需要接入
ChromaDB，只需要保持 add_texts/similarity_search/delete 这几个方法兼容即可。
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..core.config import settings


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@dataclass
class RetrievedDocument:
    """检索返回的文档块，字段兼容 LangChain Document 的常用访问方式。"""

    page_content: str
    metadata: dict


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


def _score(query_tokens: list[str], content: str) -> float:
    if not query_tokens or not content:
        return 0.0
    content_tokens = _tokenize(content)
    if not content_tokens:
        return 0.0

    counts = {}
    for token in content_tokens:
        counts[token] = counts.get(token, 0) + 1

    matched = sum(counts.get(token, 0) for token in query_tokens)
    coverage = len({token for token in query_tokens if token in counts}) / max(1, len(set(query_tokens)))
    length_penalty = math.log(len(content_tokens) + 10, 10)
    return matched / length_penalty + coverage * 2


class LocalVectorStore:
    """按用户隔离的本地文本检索库。"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.base_dir = Path(settings.CHROMA_PERSIST_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.base_dir / f"user_{user_id}_docs.json"

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save(self, records: list[dict]) -> None:
        self.path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_texts(self, texts: Iterable[str], metadatas: Iterable[dict] | None = None) -> None:
        records = self._load()
        metadata_list = list(metadatas or [])
        for index, text in enumerate(texts):
            records.append(
                {
                    "page_content": text,
                    "metadata": metadata_list[index] if index < len(metadata_list) else {},
                }
            )
        self._save(records)

    def similarity_search(self, query: str, k: int = 4) -> list[RetrievedDocument]:
        records = self._load()
        query_tokens = _tokenize(query)
        ranked = []
        for record in records:
            score = _score(query_tokens, record.get("page_content", ""))
            if score > 0:
                ranked.append((score, record))

        if not ranked and records:
            ranked = [(0.1, record) for record in records[:k]]

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedDocument(
                page_content=record.get("page_content", ""),
                metadata=record.get("metadata", {}),
            )
            for _, record in ranked[:k]
        ]

    def delete(self, where: dict | None = None) -> None:
        if not where:
            self._save([])
            return
        records = self._load()

        def should_keep(record: dict) -> bool:
            metadata = record.get("metadata", {})
            return not all(str(metadata.get(key)) == str(value) for key, value in where.items())

        self._save([record for record in records if should_keep(record)])


def get_vectorstore(user_id: int) -> LocalVectorStore:
    """获取指定用户的本地知识库存储。"""
    return LocalVectorStore(user_id=user_id)


def delete_user_collection(user_id: int) -> None:
    """删除用户的所有知识库数据。"""
    path = Path(settings.CHROMA_PERSIST_DIR) / f"user_{user_id}_docs.json"
    if path.exists():
        path.unlink()
