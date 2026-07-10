"""
工具API - 制度速览、培训知识卡片提取等独立工具
"""
import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
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
        ("入职流程", ["入职", "试用期", "转正", "报道", "导师", "onboarding", "probation"]),
        ("人事制度", ["考勤", "请假", "休假", "加班", "薪酬", "绩效", "attendance", "leave"]),
        ("财务报销", ["报销", "发票", "差旅", "预算", "付款", "reimbursement", "travel"]),
        ("信息安全", ["信息安全", "保密", "账号", "权限", "数据", "security", "privacy"]),
        ("合规要求", ["合规", "廉洁", "利益冲突", "行为准则", "compliance", "ethics"]),
        ("岗位培训", ["培训", "岗位", "产品", "业务", "客户", "training", "product"]),
    ]
    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return category
    return "核心培训知识"


def _parse_knowledge_json(content: str) -> list:
    """从 LLM 输出中提取 JSON 数组。"""
    start = content.find("[")
    end = content.rfind("]") + 1
    if start >= 0 and end > start:
        return json.loads(content[start:end])
    raise ValueError("未找到 JSON 数组")


def _normalize_knowledge_point(raw, index: int) -> dict:
    """把新旧格式的培训知识卡片统一成前端导出可用结构。"""
    if not isinstance(raw, dict):
        raw = {"title": f"培训知识{index}", "description": str(raw)}

    title = _compact_text(raw.get("title") or f"培训知识{index}", 60)
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


def _resolve_document_path(doc: Document) -> str:
    """兼容历史数据：优先使用入库文件名，缺失时尝试原始文件名。"""
    candidates = [
        os.path.join(settings.UPLOAD_DIR, doc.filename),
        os.path.join(settings.UPLOAD_DIR, doc.original_name),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    raise HTTPException(
        status_code=404,
        detail="资料文件不存在，请重新上传该资料后再生成制度速览或培训知识卡片。",
    )


def _safe_llm_invoke(prompt: str, temperature: float = 0.3) -> str | None:
    """调用 LLM，失败时返回 None，交给本地规则兜底。"""
    try:
        llm = get_llm(temperature=temperature)
        result = llm.invoke(prompt)
        return str(getattr(result, "content", result) or "").strip()
    except Exception as exc:
        print(f"⚠️ 工具 LLM 调用失败，已使用本地规则兜底: {exc}")
        return None


def _fallback_summary(text: str, length: str = "medium") -> str:
    """在远程 LLM 不可用时，用原文句段生成一个可用摘要。"""
    units = _split_excerpt_units(text)
    if not units:
        return "### 制度速览\n\n当前资料未解析出可用于速览的文本内容。"

    limit = {"short": 3, "medium": 5, "long": 8}.get(length, 5)
    selected = units[:limit]
    lead = _compact_text(" ".join(selected[:2]), 360)
    bullets = "\n".join(f"- {_compact_text(unit, 180)}" for unit in selected)
    return f"### 制度速览\n\n{lead}\n\n### 新人需要关注\n\n{bullets}"


def _fallback_knowledge_points(text: str, max_points: int = 8) -> list[dict]:
    """在远程 LLM 不可用时，从原文句段中抽取基础培训知识卡片。"""
    units = _split_excerpt_units(text)
    points = []
    seen = set()
    for unit in units:
        excerpt = _compact_text(unit, 220)
        key = _dedup_key(excerpt)
        if not key or key in seen:
            continue
        seen.add(key)
        title = _compact_text(re.sub(r"[：:。！？!?；;].*$", "", excerpt), 36)
        if len(title) < 6:
            title = f"培训要点{len(points) + 1}"
        points.append({
            "category": "核心培训知识",
            "title": title,
            "description": excerpt,
            "key_points": [excerpt],
            "examples": [],
            "source_excerpt": excerpt,
            "relevant_chunks": [{"text": excerpt, "chunk_index": None}],
        })
        if len(points) >= max_points:
            break
    return points or [{
        "category": "核心培训知识",
        "title": "资料内容",
        "description": "当前资料未解析出足够结构化的培训知识卡片。",
        "key_points": [],
        "examples": [],
        "source_excerpt": "",
        "relevant_chunks": [],
    }]


@router.post("/summarize")
def summarize_document(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成制度/培训资料速览"""
    doc_id = body.get("document_id")
    length = body.get("length", "medium")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        or_(Document.user_id == current_user.id, Document.is_shared == True),  # noqa: E712
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 共享文档从 seeds 目录读取，用户文档从 uploads 读取
    if doc.is_shared:
        file_path = str(
            Path(__file__).resolve().parents[3] / "deploy" / "seeds" / doc.original_name
        )
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="共享文档种子文件缺失")
    else:
        file_path = _resolve_document_path(doc)
    text = parse_file(file_path, f".{doc.file_type}")

    # 截取前4000字做摘要
    text_preview = text[:4000]

    length_prompts = {
        "short": "请用2-3句话概括这份企业培训资料",
        "medium": "请生成制度速览，包含适用对象、核心要求和3-5个新人注意事项",
        "long": "请详细整理这份企业培训资料，包含适用对象、关键规则、操作步骤和注意事项",
    }

    prompt = f"""{length_prompts.get(length, length_prompts["medium"])}。

原文内容：
{text_preview}

请直接给出制度速览，使用 Markdown 格式。"""

    content = _safe_llm_invoke(prompt, temperature=0.3)
    if not content:
        content = _fallback_summary(text, length)

    return {"summary": content, "document_id": doc_id}


@router.post("/extract-knowledge")
def extract_knowledge(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提取培训知识卡片并召回相关原文片段"""
    doc_id = body.get("document_id")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        or_(Document.user_id == current_user.id, Document.is_shared == True),  # noqa: E712
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.is_shared:
        file_path = str(
            Path(__file__).resolve().parents[3] / "deploy" / "seeds" / doc.original_name
        )
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="共享文档种子文件缺失")
    else:
        file_path = _resolve_document_path(doc)
    text = parse_file(file_path, f".{doc.file_type}")
    text_preview = text[:12000]

    prompt = f"""请把以下企业培训资料整理成结构清晰、可直接导出为新人培训笔记的知识卡片。

要求：
- 按新人入职理解顺序组织，优先合并同类制度、流程和注意事项，不要拆成零散碎片。
- 数量控制在 6-10 个知识卡片；资料本身很短时可以更少。
- category 是模块名，例如入职流程、人事制度、财务报销、信息安全、合规要求、岗位培训。
- description 用 1 句话说明这条规则或流程对新员工的意义。
- key_points 写 2-4 条新人必须知道的要求、步骤或限制。
- examples 写原文中可直接引用的制度条款、口径、时间节点或操作模板；没有就返回空数组。
- source_excerpt 必须从原文摘取，控制在 180 字以内，不要编造。

输出格式（JSON数组）：
[
  {{
    "category": "模块名称",
    "title": "培训知识名称",
    "description": "一句话说明",
    "key_points": ["要点1", "要点2"],
    "examples": ["例句或模板"],
    "source_excerpt": "原文短摘录"
  }}
]

只输出 JSON 数组，不要输出 Markdown 或额外解释。

原文内容：
{text_preview}"""

    content = _safe_llm_invoke(prompt, temperature=0.3)

    # 尝试解析 JSON，并兼容旧格式
    if content:
        try:
            raw_points = _parse_knowledge_json(content)
        except Exception:
            raw_points = [{"title": "培训知识", "description": content}]

        knowledge_points = [
            _normalize_knowledge_point(point, index)
            for index, point in enumerate(raw_points, 1)
        ]
    else:
        knowledge_points = _fallback_knowledge_points(text_preview)

    # 为每张知识卡片检索相关原文片段
    from ..rag.vectorstore import get_vectorstore, get_shared_vectorstore

    try:
        vectorstore = (
            get_shared_vectorstore()
            if doc.is_shared
            else get_vectorstore(user_id=current_user.id)
        )
    except Exception as exc:
        print(f"⚠️ 培训知识卡片向量库加载失败，已退回原文片段兜底: {exc}")
        vectorstore = None
    doc_id_str = str(doc_id)

    DISTANCE_THRESHOLD = 1.0   # 余弦距离阈值：<1.0 表示有一定相关性
    global_seen = set()        # 跨知识卡片全局去重

    for point in knowledge_points:
        query = " ".join([
            point.get("title", ""),
            point.get("description", ""),
            " ".join(point.get("key_points", [])),
            " ".join(point.get("examples", [])),
        ])
        try:
            scored = vectorstore.similarity_search_with_score(query, k=6) if vectorstore else []
        except Exception as exc:
            print(f"⚠️ 培训知识卡片相关片段检索失败，已跳过向量召回: {exc}")
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
