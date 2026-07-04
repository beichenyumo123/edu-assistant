"""
工具API - 摘要生成、知识点提取等独立工具
"""
import json
import os
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..models.document import Document
from ..rag.loader import parse_file
from ..agents.llm import get_llm
from ..core.config import settings
from .auth import get_current_user

router = APIRouter(prefix="/api/tools", tags=["工具"])


def _compact_text(text: str, max_chars: int | None = None) -> str:
    """压缩空白，得到适合导出和展示的一行文本。"""
    compacted = re.sub(r"\s+", " ", str(text or "")).strip()
    if max_chars and len(compacted) > max_chars:
        return compacted[: max_chars - 1].rstrip() + "…"
    return compacted


def _as_text_list(value) -> list[str]:
    """兼容 LLM 返回的字符串、数组或空值。"""
    if isinstance(value, list):
        items = value
    elif isinstance(value, str) and value.strip():
        items = re.split(r"\n+|[；;]", value)
    else:
        items = []
    return [_compact_text(item, 180) for item in items if _compact_text(item)]


def _infer_category(title: str, description: str) -> str:
    """当模型没有给 category 时，用轻量规则补一个模块名。"""
    text = f"{title} {description}".lower()
    rules = [
        ("文章结构", ["开头", "引出", "论证", "原因", "后果", "转折", "对比", "观点", "建议", "结尾", "hook", "analysis", "contrast"]),
        ("句式升级", ["倒装", "虚拟", "强调句", "句式", "从句", "非谓语", "not only", "only by", "so important"]),
        ("词汇表达", ["同义词", "替换", "词汇", "vocabulary", "important", "many", "good", "bad", "think"]),
        ("逻辑衔接", ["连接词", "逻辑", "therefore", "moreover", "nevertheless", "hence"]),
    ]
    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return category
    return "核心知识点"


def _parse_knowledge_json(content: str) -> list:
    """从 LLM 输出中提取 JSON 数组。"""
    start = content.find("[")
    end = content.rfind("]") + 1
    if start >= 0 and end > start:
        return json.loads(content[start:end])
    raise ValueError("未找到 JSON 数组")


def _normalize_knowledge_point(raw, index: int) -> dict:
    """把新旧格式的知识点统一成前端导出可用结构。"""
    if not isinstance(raw, dict):
        raw = {"title": f"知识点{index}", "description": str(raw)}

    title = _compact_text(raw.get("title") or f"知识点{index}", 60)
    description = _compact_text(raw.get("description") or raw.get("summary") or "", 260)
    category = _compact_text(raw.get("category") or raw.get("module") or "", 40)
    if not category:
        category = _infer_category(title, description)

    return {
        "category": category,
        "title": title,
        "description": description,
        "key_points": _as_text_list(raw.get("key_points") or raw.get("points")),
        "examples": _as_text_list(raw.get("examples") or raw.get("templates")),
        "source_excerpt": _compact_text(raw.get("source_excerpt") or raw.get("excerpt") or "", 280),
        "relevant_chunks": [],
    }


def _tokens(text: str) -> set[str]:
    """提取中英文关键词，用于从 chunk 中挑选最相关句子。"""
    lowered = (text or "").lower()
    english = re.findall(r"[a-z][a-z-]{1,}", lowered)
    cjk = re.findall(r"[\u4e00-\u9fff]", lowered)
    stopwords = {
        "的", "了", "和", "与", "是", "在", "用", "为", "及", "或", "个", "中",
        "this", "that", "with", "from", "into", "about", "must", "should", "could",
        "would", "there", "their",
    }
    return {token for token in english + cjk if token not in stopwords}


def _split_excerpt_units(text: str) -> list[str]:
    """把原文块切成较短句段，避免整块导出。"""
    units = []
    for line in str(text or "").splitlines():
        line = _compact_text(line)
        if not line:
            continue
        pieces = re.split(r"(?<=[。！？!?；;])\s*|(?<=\.)\s+(?=[A-Z\"'(])", line)
        for piece in pieces:
            piece = _compact_text(piece, 240)
            if piece:
                units.append(piece)
    if not units:
        fallback = _compact_text(text, 240)
        return [fallback] if fallback else []
    return units


def _focused_excerpt(source_text: str, query: str, max_chars: int = 280) -> str:
    """从较长原文中抽出与 query 最相关的 1-2 个短句段。"""
    units = _split_excerpt_units(source_text)
    if not units:
        return ""

    query_tokens = _tokens(query)
    if not query_tokens:
        return _compact_text(units[0], max_chars)

    scores = []
    for index, unit in enumerate(units):
        unit_tokens = _tokens(unit)
        overlap = query_tokens & unit_tokens
        score = len(overlap) * 2
        if _compact_text(query, 40).lower() in unit.lower():
            score += 4
        score -= len(unit) / 500
        scores.append((score, index))

    best_score, best_index = max(scores, key=lambda item: item[0])
    if best_score <= 0:
        return _compact_text(units[0], max_chars)

    selected = [best_index]
    for neighbor in (best_index - 1, best_index + 1):
        if 0 <= neighbor < len(units):
            neighbor_tokens = _tokens(units[neighbor])
            if query_tokens & neighbor_tokens:
                selected.append(neighbor)

    excerpt = " ".join(units[index] for index in sorted(set(selected)))
    return _compact_text(excerpt, max_chars)


def _dedup_key(text: str) -> str:
    return re.sub(r"\W+", "", text.lower())[:100]


@router.post("/summarize")
def summarize_document(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成文档摘要"""
    doc_id = body.get("document_id")
    length = body.get("length", "medium")

    doc = db.query(Document).filter(
        Document.id == doc_id, Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 读取文件文本
    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    text = parse_file(file_path, f".{doc.file_type}")

    # 截取前4000字做摘要
    text_preview = text[:4000]

    length_prompts = {
        "short": "请用2-3句话简要总结",
        "medium": "请用一段话总结核心内容，包含3-5个要点",
        "long": "请详细总结，包含主要论点和支撑细节",
    }

    prompt = f"""{length_prompts.get(length, length_prompts["medium"])}。

原文内容：
{text_preview}

请直接给出摘要，使用Markdown格式。"""

    llm = get_llm(temperature=0.3)
    result = llm.invoke(prompt)

    return {"summary": result.content, "document_id": doc_id}


@router.post("/extract-knowledge")
def extract_knowledge(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提取知识点并召回相关原文片段"""
    doc_id = body.get("document_id")

    doc = db.query(Document).filter(
        Document.id == doc_id, Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    text = parse_file(file_path, f".{doc.file_type}")
    text_preview = text[:12000]

    prompt = f"""请把以下资料整理成结构清晰、可直接导出为复习笔记的知识点。

要求：
- 按原文学习顺序组织，优先合并同类内容，不要拆成零散碎片。
- 数量控制在 6-10 个知识点；资料本身很短时可以更少。
- category 是模块名，用来给导出的 Markdown 分组。
- description 用 1 句话说明这个知识点的作用或核心含义。
- key_points 写 2-4 条可复习的要点。
- examples 写原文中可直接背诵或套用的例句、模板、术语；没有就返回空数组。
- source_excerpt 必须从原文摘取，控制在 180 字以内，不要编造。

输出格式（JSON数组）：
[
  {{
    "category": "模块名称",
    "title": "知识点名称",
    "description": "一句话说明",
    "key_points": ["要点1", "要点2"],
    "examples": ["例句或模板"],
    "source_excerpt": "原文短摘录"
  }}
]

只输出 JSON 数组，不要输出 Markdown 或额外解释。

原文内容：
{text_preview}"""

    llm = get_llm(temperature=0.3)
    result = llm.invoke(prompt)

    # 尝试解析 JSON，并兼容旧格式
    try:
        raw_points = _parse_knowledge_json(result.content)
    except Exception:
        raw_points = [{"title": "知识点", "description": result.content}]

    knowledge_points = [
        _normalize_knowledge_point(point, index)
        for index, point in enumerate(raw_points, 1)
    ]

    # 为每个知识点检索相关原文片段
    from ..rag.vectorstore import get_vectorstore

    vectorstore = get_vectorstore(user_id=current_user.id)
    doc_id_str = str(doc_id)

    DISTANCE_THRESHOLD = 1.0   # 余弦距离阈值：<1.0 表示有一定相关性
    global_seen = set()        # 跨知识点全局去重

    for point in knowledge_points:
        query = " ".join([
            point.get("title", ""),
            point.get("description", ""),
            " ".join(point.get("key_points", [])),
            " ".join(point.get("examples", [])),
        ])
        try:
            scored = vectorstore.similarity_search_with_score(query, k=6)
        except Exception:
            scored = []

        relevant = []

        if point.get("source_excerpt"):
            excerpt = point["source_excerpt"]
            key = _dedup_key(excerpt)
            if key and key not in global_seen:
                global_seen.add(key)
                relevant.append({"text": excerpt, "chunk_index": None})

        # 按分数过滤 + 仅保留当前文档 + 从长 chunk 中抽取最相关短句
        for doc, score in scored:
            if len(relevant) >= 2:
                break
            if score >= DISTANCE_THRESHOLD:
                continue
            if str(doc.metadata.get("document_id", "")) != doc_id_str:
                continue
            excerpt = _focused_excerpt(doc.page_content, query)
            if not excerpt:
                continue
            dedup_key = _dedup_key(excerpt)
            if not dedup_key or dedup_key in global_seen:
                continue
            global_seen.add(dedup_key)
            relevant.append({
                "text": excerpt,
                "chunk_index": doc.metadata.get("chunk_index", 0),
            })

        if not relevant:
            fallback_excerpt = _focused_excerpt(text_preview, query)
            if fallback_excerpt:
                key = _dedup_key(fallback_excerpt)
                if key and key not in global_seen:
                    global_seen.add(key)
                    relevant.append({"text": fallback_excerpt, "chunk_index": None})

        if relevant and not point.get("source_excerpt"):
            point["source_excerpt"] = relevant[0]["text"]
        point["relevant_chunks"] = relevant

    return {"knowledge_points": knowledge_points, "document_id": doc_id}
