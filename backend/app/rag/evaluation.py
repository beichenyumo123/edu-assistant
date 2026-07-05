"""
RAG 在线评价指标。

这些指标不依赖人工标注集，适合在每次问答后做即时质量复盘。
严格的 recall@k / hitrate 仍需要离线题库与标准证据集；这里提供的是可落库、
可展示的启发式指标，用来观察检索质量、引用正确率和幻觉风险。
"""
from __future__ import annotations

import re
from statistics import mean
from typing import Any

from ..core.config import settings
from .vectorstore import RetrievedDocument


_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9_]+")
_SOURCE_RE = re.compile(r"(?:【|\[|\(|（)?来源\s*(\d+)(?:】|\]|\)|）)?")
_EVIDENCE_RE = re.compile(r"doc\d+_chunk\d+")
_MARKDOWN_PREFIX_RE = re.compile(r"^[#>\-\*\d\.\s、]+")


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _round(value: float | None) -> float | None:
    return round(value, 4) if isinstance(value, (int, float)) else None


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text or "")}


def _overlap_ratio(left: str, right: str) -> float:
    left_tokens = _tokenize(left)
    if not left_tokens:
        return 0.0
    right_tokens = _tokenize(right)
    if not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def _score_to_relevance(score: Any) -> float | None:
    """把 Chroma 距离粗略映射为 0-1 相关性，分数越高越相关。"""
    if not isinstance(score, (int, float)):
        return None
    # 当前向量已归一化，Chroma 距离通常在 0-2 间；保守裁剪避免异常值污染展示。
    return _clamp(1 - (float(score) / 2))


def _trust_score(level: str | None) -> float:
    return {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.4,
    }.get((level or "").lower(), 0.55)


def _split_claims(answer: str) -> list[str]:
    text = re.sub(r"```.*?```", " ", answer or "", flags=re.S)
    raw_units = re.split(r"[。！？!?；;\n]+", text)
    claims = []
    for unit in raw_units:
        cleaned = _MARKDOWN_PREFIX_RE.sub("", unit).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if len(cleaned) < 8:
            continue
        if cleaned.endswith(("吗", "呢", "?")):
            continue
        claims.append(cleaned)
    return claims


def _extract_source_refs(text: str) -> list[int]:
    refs = []
    for match in _SOURCE_RE.finditer(text or ""):
        try:
            refs.append(int(match.group(1)))
        except (TypeError, ValueError):
            continue
    return refs


def _extract_evidence_refs(text: str) -> list[str]:
    return _EVIDENCE_RE.findall(text or "")


def _risk_level(risk: float) -> str:
    if risk < 0.25:
        return "low"
    if risk < 0.55:
        return "medium"
    return "high"


def evaluate_rag_answer(
    query: str,
    answer: str,
    docs: list[RetrievedDocument],
    selected_document_ids: list[int] | None = None,
    top_k: int | None = None,
) -> dict:
    """生成一次 RAG 问答的在线评价指标。"""
    top_k = top_k or settings.RETRIEVAL_TOP_K
    retrieved_count = len(docs)
    context_text = "\n".join(doc.page_content for doc in docs)
    source_numbers = set(range(1, retrieved_count + 1))
    evidence_ids = {
        str(doc.metadata.get("evidence_id"))
        for doc in docs
        if doc.metadata and doc.metadata.get("evidence_id")
    }

    relevance_values = [
        value
        for value in (
            _score_to_relevance((doc.metadata or {}).get("retrieval_score")) for doc in docs
        )
        if value is not None
    ]
    trust_values = [_trust_score((doc.metadata or {}).get("trust_level")) for doc in docs]
    unique_docs = {
        str((doc.metadata or {}).get("document_id"))
        for doc in docs
        if (doc.metadata or {}).get("document_id")
    }

    retrieval_quality_parts = []
    if relevance_values:
        retrieval_quality_parts.append(mean(relevance_values))
    if retrieved_count:
        retrieval_quality_parts.append(_overlap_ratio(query, context_text))
        retrieval_quality_parts.append(mean(trust_values))
        retrieval_quality_parts.append(min(1.0, len(unique_docs) / max(1, retrieved_count)))
    retrieval_quality = mean(retrieval_quality_parts) if retrieval_quality_parts else 0.0

    claims = _split_claims(answer)
    source_refs = _extract_source_refs(answer)
    evidence_refs = _extract_evidence_refs(answer)
    valid_source_refs = [ref for ref in source_refs if ref in source_numbers]
    invalid_source_refs = [ref for ref in source_refs if ref not in source_numbers]
    valid_evidence_refs = [ref for ref in evidence_refs if ref in evidence_ids]
    invalid_evidence_refs = [ref for ref in evidence_refs if ref not in evidence_ids]

    supported_claims = [
        claim
        for claim in claims
        if any(ref in source_numbers for ref in _extract_source_refs(claim))
        or any(ref in evidence_ids for ref in _extract_evidence_refs(claim))
    ]
    total_refs = len(source_refs) + len(evidence_refs)
    valid_refs = len(valid_source_refs) + len(valid_evidence_refs)
    citation_coverage = len(supported_claims) / len(claims) if claims else 1.0
    citation_validity = valid_refs / total_refs if total_refs else (1.0 if not docs else 0.0)
    referenced_sources = {ref for ref in valid_source_refs}
    source_utilization = len(referenced_sources) / retrieved_count if retrieved_count else 0.0
    context_overlap = _overlap_ratio(answer, context_text) if docs else 0.0
    abstention_detected = any(
        phrase in (answer or "")
        for phrase in ("没有足够依据", "未找到", "知识库", "无法基于资料", "参考资料不足")
    )

    if docs:
        groundedness = (
            citation_coverage * 0.35
            + citation_validity * 0.25
            + context_overlap * 0.25
            + source_utilization * 0.15
        )
    else:
        groundedness = 0.75 if abstention_detected else 0.15

    hallucination_risk = 1 - _clamp(groundedness)
    if abstention_detected and not docs:
        hallucination_risk = min(hallucination_risk, 0.25)

    overall_score = (
        retrieval_quality * 0.45
        + _clamp(groundedness) * 0.45
        + citation_validity * 0.10
    )

    notes = [
        "online_heuristic: 当前为在线启发式指标，严格 recall@k/hitrate 需要离线标注题集。",
    ]
    if not docs:
        notes.append("no_retrieval_context: 本次未检索到可用证据。")
    if invalid_source_refs or invalid_evidence_refs:
        notes.append("invalid_citation: 回答中出现了未命中的来源编号或 evidence_id。")
    if docs and citation_coverage < 0.5:
        notes.append("low_citation_coverage: 多数关键结论缺少来源绑定。")

    return {
        "mode": "online_heuristic",
        "overall_score": _round(_clamp(overall_score)),
        "risk_level": _risk_level(hallucination_risk),
        "retrieval_quality": _round(_clamp(retrieval_quality)),
        "groundedness": _round(_clamp(groundedness)),
        "citation_coverage": _round(_clamp(citation_coverage)),
        "citation_validity": _round(_clamp(citation_validity)),
        "hallucination_risk": _round(_clamp(hallucination_risk)),
        "retrieval": {
            "top_k": top_k,
            "selected_document_count": len(selected_document_ids) if selected_document_ids is not None else None,
            "retrieved_chunks": retrieved_count,
            "retrieval_hit": bool(retrieved_count and retrieval_quality >= 0.25),
            "best_relevance": _round(max(relevance_values) if relevance_values else None),
            "mean_relevance": _round(mean(relevance_values) if relevance_values else None),
            "query_coverage": _round(_overlap_ratio(query, context_text)),
            "document_diversity": _round(len(unique_docs) / retrieved_count if retrieved_count else 0.0),
            "source_trust": _round(mean(trust_values) if trust_values else 0.0),
        },
        "generation": {
            "claim_count": len(claims),
            "supported_claim_count": len(supported_claims),
            "unsupported_claim_count": max(0, len(claims) - len(supported_claims)),
            "valid_citation_count": valid_refs,
            "invalid_citation_count": len(invalid_source_refs) + len(invalid_evidence_refs),
            "source_utilization": _round(source_utilization),
            "context_overlap": _round(context_overlap),
            "abstention_detected": abstention_detected,
        },
        "notes": notes,
    }
