"""
AI 记忆服务

第一版采用可解释的启发式统计：记录常问主题、回答风格偏好、
沟通语气和常用资料，不保存完整回答内容。
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from ..models.document import Document
from ..models.user import User
from ..models.user_memory import UserMemory


MAX_TRACKED_ITEMS = 8
ANSWER_STYLE_OPTIONS = ("结构化", "简洁", "详细", "步骤化", "表格化")
COMMUNICATION_TONE_OPTIONS = ("专业清晰", "直接高效", "耐心详细", "结构清晰")

TOPIC_RULES = [
    ("入职流程", ("入职", "第一周", "新人", "报道", "劳动合同", "员工登记", "承诺书", "培训清单")),
    ("考勤休假", ("考勤", "打卡", "迟到", "早退", "请假", "年假", "调休", "病假", "事假")),
    ("报销差旅", ("报销", "差旅", "出差", "发票", "费用", "借款", "交通", "住宿")),
    ("信息安全", ("信息安全", "数据", "外发", "保密", "权限", "账号", "密码", "安全")),
    ("人事制度", ("试用期", "转正", "绩效", "合同", "薪酬", "离职", "纪律", "处分")),
    ("岗位培训", ("岗位", "产品", "业务", "职责", "流程", "学习", "培训", "技能")),
]

STYLE_RULES = [
    ("表格化", ("表格", "对比", "列成表")),
    ("步骤化", ("步骤", "流程", "清单", "怎么处理", "如何", "怎么办", "待办")),
    ("简洁", ("简洁", "简要", "简单", "一句话", "概括")),
    ("详细", ("详细", "展开", "具体", "完整", "解释")),
]

TONE_RULES = [
    ("直接高效", ("直接", "简洁", "快速", "重点")),
    ("耐心详细", ("详细", "解释", "讲解", "展开")),
    ("结构清晰", ("步骤", "清单", "表格", "分点")),
]


def _loads_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback
    return data if isinstance(data, type(fallback)) else fallback


def _dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _infer_by_rules(text: str, rules: list[tuple[str, tuple[str, ...]]], fallback: str) -> list[str]:
    lowered = text.lower()
    matched = []
    for label, keywords in rules:
        if any(keyword.lower() in lowered for keyword in keywords):
            matched.append(label)
    return matched or [fallback]


def _bump_counts(counts: dict[str, int], labels: list[str]) -> dict[str, int]:
    next_counts = dict(counts)
    for label in labels:
        next_counts[label] = int(next_counts.get(label, 0)) + 1
    return dict(
        sorted(next_counts.items(), key=lambda item: item[1], reverse=True)[:MAX_TRACKED_ITEMS]
    )


def _top_items(counts: dict[str, int], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {"name": name, "count": int(count)}
        for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]


def _get_or_create_memory(db: Session, user_id: int) -> UserMemory:
    memory = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    if memory:
        return memory
    memory = UserMemory(user_id=user_id)
    db.add(memory)
    return memory


def _document_choices(
    db: Session,
    user_id: int,
    selected_document_ids: list[int] | None,
    sources: list[dict] | None,
) -> list[dict[str, Any]]:
    doc_ids = []
    if selected_document_ids is not None:
        doc_ids.extend(selected_document_ids)
    elif sources:
        for source in sources:
            try:
                doc_ids.append(int(source.get("document_id")))
            except (TypeError, ValueError):
                continue

    unique_doc_ids = []
    for doc_id in doc_ids:
        if doc_id > 0 and doc_id not in unique_doc_ids:
            unique_doc_ids.append(doc_id)

    if not unique_doc_ids:
        return []

    docs = (
        db.query(Document)
        .filter(Document.user_id == user_id, Document.id.in_(unique_doc_ids))
        .all()
    )
    by_id = {doc.id: doc for doc in docs}
    return [
        {"id": doc_id, "name": by_id[doc_id].original_name}
        for doc_id in unique_doc_ids
        if doc_id in by_id
    ]


def record_memory_interaction(
    db: Session,
    user: User,
    query: str,
    selected_document_ids: list[int] | None,
    sources: list[dict] | None,
) -> UserMemory:
    """在一次问答结束后更新用户记忆。调用方负责 commit。"""
    memory = _get_or_create_memory(db, user.id)
    if memory.memory_enabled is False:
        return memory

    topic_counts = _loads_json(memory.topic_counts, {})
    style_counts = _loads_json(memory.style_counts, {})
    tone_counts = _loads_json(memory.tone_counts, {})
    document_usage = _loads_json(memory.document_usage, {})

    topics = _infer_by_rules(query, TOPIC_RULES, "通用入职答疑")
    styles = _infer_by_rules(query, STYLE_RULES, "结构化")
    tones = _infer_by_rules(query, TONE_RULES, "专业清晰")
    documents = _document_choices(db, user.id, selected_document_ids, sources)

    memory.question_count = int(memory.question_count or 0) + 1
    memory.topic_counts = _dumps_json(_bump_counts(topic_counts, topics))
    memory.style_counts = _dumps_json(_bump_counts(style_counts, styles))
    memory.tone_counts = _dumps_json(_bump_counts(tone_counts, tones))
    memory.preferred_answer_style = styles[0] if styles[0] != "结构化" else (memory.preferred_answer_style or "结构化")
    memory.communication_tone = tones[0] if tones[0] != "专业清晰" else (memory.communication_tone or "专业清晰")
    memory.last_question = query[:500]

    if selected_document_ids is not None:
        memory.last_selected_document_ids = _dumps_json(selected_document_ids)

    if documents:
        document_usage = _bump_counts(document_usage, [item["name"] for item in documents])
        memory.document_usage = _dumps_json(document_usage)
        memory.last_used_documents = _dumps_json(documents[:MAX_TRACKED_ITEMS])

    db.add(memory)
    return memory


def get_memory_summary(db: Session, user: User) -> dict[str, Any]:
    memory = db.query(UserMemory).filter(UserMemory.user_id == user.id).first()
    if not memory:
        return {
            "user_id": user.id,
            "memory_enabled": True,
            "department": user.grade,
            "role": user.major,
            "question_count": 0,
            "preferred_answer_style": "结构化",
            "communication_tone": "专业清晰",
            "top_topics": [],
            "document_preferences": [],
            "last_used_documents": [],
            "last_question": None,
            "updated_at": None,
        }

    return {
        "user_id": user.id,
        "memory_enabled": memory.memory_enabled is not False,
        "department": user.grade,
        "role": user.major,
        "question_count": int(memory.question_count or 0),
        "preferred_answer_style": memory.preferred_answer_style or "结构化",
        "communication_tone": memory.communication_tone or "专业清晰",
        "top_topics": _top_items(_loads_json(memory.topic_counts, {})),
        "document_preferences": _top_items(_loads_json(memory.document_usage, {})),
        "last_used_documents": _loads_json(memory.last_used_documents, []),
        "last_question": memory.last_question,
        "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
    }


def clear_user_memory(db: Session, user: User) -> None:
    memory = db.query(UserMemory).filter(UserMemory.user_id == user.id).first()
    if memory:
        db.delete(memory)


def update_memory_settings(
    db: Session,
    user: User,
    memory_enabled: bool | None = None,
    preferred_answer_style: str | None = None,
    communication_tone: str | None = None,
) -> UserMemory:
    """更新用户可控的记忆设置。调用方负责 commit。"""
    memory = _get_or_create_memory(db, user.id)

    if memory_enabled is not None:
        memory.memory_enabled = bool(memory_enabled)
    if preferred_answer_style:
        if preferred_answer_style not in ANSWER_STYLE_OPTIONS:
            raise ValueError("不支持的回答风格")
        memory.preferred_answer_style = preferred_answer_style
    if communication_tone:
        if communication_tone not in COMMUNICATION_TONE_OPTIONS:
            raise ValueError("不支持的沟通语气")
        memory.communication_tone = communication_tone

    db.add(memory)
    return memory


def build_memory_context(db: Session, user: User) -> str:
    """生成可注入 Agent Prompt 的用户记忆摘要。"""
    summary = get_memory_summary(db, user)
    if not summary.get("memory_enabled", True):
        return ""

    topics = "、".join(item["name"] for item in summary["top_topics"][:3]) or "暂无"
    docs = "、".join(item["name"] for item in summary["document_preferences"][:3]) or "暂无"

    parts = [
        f"部门：{summary.get('department') or '未知'}",
        f"岗位：{summary.get('role') or '未知'}",
        f"常问主题：{topics}",
        f"偏好回答风格：{summary.get('preferred_answer_style') or '结构化'}",
        f"沟通语气偏好：{summary.get('communication_tone') or '专业清晰'}",
        f"常用资料：{docs}",
    ]
    return "\n".join(parts)
