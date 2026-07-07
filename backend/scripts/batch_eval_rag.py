"""
Batch evaluate OnboardAgent RAG answers with the existing online metrics.

This script reuses the real edu_agent pipeline, then aggregates the evaluation
dict returned by backend/app/rag/evaluation.py. It is intended for product demos
and midterm reports, not as a strict gold-label benchmark.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.edu_agent import edu_chat_stream  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.user import User  # noqa: E402


DEFAULT_QUESTIONS = [
    {"id": "rag_01", "question": "OnboardAgent 为什么比普通聊天 AI 更适合新员工入职培训？"},
    {"id": "rag_02", "question": "系统如何把员工手册和制度文件转化为可检索的企业知识库？"},
    {"id": "rag_03", "question": "RAG 在企业制度问答中如何降低大模型幻觉？"},
    {"id": "rag_04", "question": "来源引用和证据追溯对制度问答有什么价值？"},
    {"id": "rag_05", "question": "新员工勾选培训资料后，系统如何只检索对应资料？"},
    {"id": "rag_06", "question": "为什么企业制度文档需要先切块再向量化？"},
    {"id": "rag_07", "question": "向量模型在公司制度检索中承担什么作用？"},
    {"id": "rag_08", "question": "在线评价指标如何观察一次制度问答是否可信？"},
    {"id": "rag_09", "question": "引用正确率低说明企业问答可能存在什么问题？"},
    {"id": "rag_10", "question": "如果知识库没有足够依据，入职培训助手应该如何回答？"},
    {"id": "onboard_01", "question": "新员工入职第一周需要完成哪些事项？"},
    {"id": "onboard_02", "question": "入职后遇到账号或设备问题应该找谁？"},
    {"id": "onboard_03", "question": "试用期通常持续多久？"},
    {"id": "onboard_04", "question": "试用期转正评估主要看哪些方面？"},
    {"id": "onboard_05", "question": "新人必修培训包括哪些内容？"},
    {"id": "onboard_06", "question": "未按时完成必修培训可能有什么影响？"},
    {"id": "onboard_07", "question": "劳动合同和薪酬福利问题应该向谁确认？"},
    {"id": "onboard_08", "question": "直属导师在新人入职过程中主要提供什么帮助？"},
    {"id": "attendance_01", "question": "公司标准工作时间是什么？"},
    {"id": "attendance_02", "question": "哪些岗位可以采用弹性工作制？"},
    {"id": "attendance_03", "question": "员工应该如何完成上下班打卡？"},
    {"id": "attendance_04", "question": "因出差或系统故障无法打卡时应该怎么处理？"},
    {"id": "attendance_05", "question": "请假需要提前多久提交申请？"},
    {"id": "attendance_06", "question": "病假是否需要补充证明？"},
    {"id": "attendance_07", "question": "未经审批擅自缺勤可能如何处理？"},
    {"id": "attendance_08", "question": "加班为什么需要提前审批？"},
    {"id": "expense_01", "question": "员工出差前为什么要提交差旅申请？"},
    {"id": "expense_02", "question": "差旅申请中需要写明哪些信息？"},
    {"id": "expense_03", "question": "超出差旅标准的费用应该如何处理？"},
    {"id": "expense_04", "question": "哪些非公务费用不得报销？"},
    {"id": "expense_05", "question": "报销时发票需要满足哪些要求？"},
    {"id": "expense_06", "question": "电子发票为什么要避免重复提交？"},
    {"id": "expense_07", "question": "费用发生后多久内应该提交报销申请？"},
    {"id": "expense_08", "question": "逾期报销是否一定可以受理？"},
    {"id": "security_01", "question": "员工账号为什么不能共享给他人使用？"},
    {"id": "security_02", "question": "系统权限应该按照什么原则申请？"},
    {"id": "security_03", "question": "离岗、转岗或项目结束后权限应该如何处理？"},
    {"id": "security_04", "question": "哪些信息属于敏感信息？"},
    {"id": "security_05", "question": "客户数据和源代码能否上传到个人网盘？"},
    {"id": "security_06", "question": "公司设备应采取哪些安全措施？"},
    {"id": "security_07", "question": "发现设备丢失或账号异常登录时应该怎么办？"},
    {"id": "security_08", "question": "员工在合规行为方面有哪些禁止事项？"},
    {"id": "workflow_01", "question": "新人如何快速了解与自己岗位相关的制度和流程？"},
    {"id": "workflow_02", "question": "回答涉及薪酬、合同或处分时为什么要提醒以 HR 或法务确认为准？"},
    {"id": "workflow_03", "question": "制度速览功能适合帮助新员工解决什么问题？"},
    {"id": "workflow_04", "question": "培训知识卡片如何帮助新人建立入职知识框架？"},
    {"id": "workflow_05", "question": "如果多个资料都提到同一流程，回答中应该如何标注来源？"},
    {"id": "workflow_06", "question": "企业培训资料更新后为什么需要重建或更新向量索引？"},
    {"id": "workflow_07", "question": "请总结从上传公司制度资料到生成可信回答的完整闭环。"},
    {"id": "workflow_08", "question": "新员工如何判断某个回答是否真正基于公司资料？"},
]


METRIC_KEYS = [
    "overall_score",
    "retrieval_quality",
    "groundedness",
    "citation_coverage",
    "citation_validity",
    "hallucination_risk",
]


def load_questions(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return DEFAULT_QUESTIONS
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, list):
        return [
            item if isinstance(item, dict) else {"id": f"q_{index}", "question": str(item)}
            for index, item in enumerate(data, 1)
        ]
    if isinstance(data, dict) and isinstance(data.get("questions"), list):
        return data["questions"]
    raise ValueError("questions file must be a JSON list or {'questions': [...]}")


def get_user_id(username: str | None, explicit_user_id: int | None) -> int:
    if explicit_user_id:
        return explicit_user_id

    db = SessionLocal()
    try:
        query = db.query(User)
        user = query.filter(User.username == username).first() if username else query.first()
        if not user:
            raise RuntimeError("No user found. Please register or pass --user-id.")
        return int(user.id)
    finally:
        db.close()


def ready_documents(user_id: int) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        docs = (
            db.query(Document)
            .filter(Document.user_id == user_id, Document.status == "ready")
            .order_by(Document.id.asc())
            .all()
        )
        return [
            {
                "id": doc.id,
                "name": doc.original_name,
                "file_type": doc.file_type,
                "chunk_count": doc.chunk_count,
            }
            for doc in docs
        ]
    finally:
        db.close()


async def run_one(question: dict[str, Any], user_id: int) -> dict[str, Any]:
    selected_document_ids = question.get("selected_document_ids")
    answer_parts = []
    done_chunk = {}
    async for chunk in edu_chat_stream(
        question["question"],
        user_id=user_id,
        conversation_history=[],
        selected_document_ids=selected_document_ids,
    ):
        if chunk["type"] == "token":
            answer_parts.append(chunk.get("content", ""))
        elif chunk["type"] == "done":
            done_chunk = chunk

    answer = done_chunk.get("content") or "".join(answer_parts)
    return {
        "id": question.get("id"),
        "question": question["question"],
        "selected_document_ids": selected_document_ids,
        "answer_preview": answer[:220],
        "sources": done_chunk.get("sources", []),
        "evaluation": done_chunk.get("evaluation") or {},
    }


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.mean(values), 4)


def pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{round(value * 100)}%"


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "question_count": len(results),
        "metrics": {},
        "retrieval_hit_rate": None,
        "avg_retrieved_chunks": None,
        "avg_supported_claim_ratio": None,
    }

    for key in METRIC_KEYS:
        values = [
            result["evaluation"].get(key)
            for result in results
            if isinstance(result.get("evaluation", {}).get(key), (int, float))
        ]
        summary["metrics"][key] = average(values)

    retrieval_hits = [
        result["evaluation"].get("retrieval", {}).get("retrieval_hit")
        for result in results
        if "retrieval" in result.get("evaluation", {})
    ]
    if retrieval_hits:
        summary["retrieval_hit_rate"] = round(
            sum(1 for item in retrieval_hits if item) / len(retrieval_hits),
            4,
        )

    retrieved_chunks = [
        result["evaluation"].get("retrieval", {}).get("retrieved_chunks")
        for result in results
        if isinstance(result.get("evaluation", {}).get("retrieval", {}).get("retrieved_chunks"), int)
    ]
    summary["avg_retrieved_chunks"] = average(retrieved_chunks)

    ratios = []
    for result in results:
        generation = result.get("evaluation", {}).get("generation", {})
        claim_count = generation.get("claim_count")
        supported = generation.get("supported_claim_count")
        if isinstance(claim_count, int) and claim_count > 0 and isinstance(supported, int):
            ratios.append(supported / claim_count)
    summary["avg_supported_claim_ratio"] = average(ratios)
    return summary


def write_markdown_report(
    output_path: Path,
    user_id: int,
    documents: list[dict[str, Any]],
    summary: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    metrics = summary["metrics"]
    lines = [
        "# OnboardAgent RAG 批量评测报告",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 用户 ID：{user_id}",
        f"- 问题数量：{summary['question_count']}",
        f"- 资料数量：{len(documents)}",
        "",
        "## 平均指标",
        "",
        "| 指标 | 平均值 |",
        "| --- | ---: |",
        f"| 总分 | {pct(metrics.get('overall_score'))} |",
        f"| 检索质量 | {pct(metrics.get('retrieval_quality'))} |",
        f"| 证据支撑 | {pct(metrics.get('groundedness'))} |",
        f"| 引用覆盖 | {pct(metrics.get('citation_coverage'))} |",
        f"| 引用正确 | {pct(metrics.get('citation_validity'))} |",
        f"| 幻觉风险 | {pct(metrics.get('hallucination_risk'))} |",
        f"| 检索命中率 | {pct(summary.get('retrieval_hit_rate'))} |",
        f"| 平均检索块数 | {summary.get('avg_retrieved_chunks') or '-'} |",
        "",
        "> 说明：这是在线启发式批量评测，复用产品当前的 RAG 评价逻辑；不是基于人工标注 gold set 的严格准确率。",
        "",
        "## 评测资料",
        "",
    ]
    for doc in documents:
        lines.append(f"- #{doc['id']} {doc['name']} ({doc['file_type']}, {doc['chunk_count']} chunks)")

    lines.extend(["", "## 单题结果", ""])
    for result in results:
        evaluation = result.get("evaluation", {})
        retrieval = evaluation.get("retrieval", {})
        generation = evaluation.get("generation", {})
        lines.extend(
            [
                f"### {result.get('id')}: {result.get('question')}",
                "",
                f"- 总分：{pct(evaluation.get('overall_score'))}",
                f"- 检索质量：{pct(evaluation.get('retrieval_quality'))}",
                f"- 证据支撑：{pct(evaluation.get('groundedness'))}",
                f"- 引用覆盖：{pct(evaluation.get('citation_coverage'))}",
                f"- 引用正确：{pct(evaluation.get('citation_validity'))}",
                f"- 幻觉风险：{pct(evaluation.get('hallucination_risk'))}",
                f"- 检索块：{retrieval.get('retrieved_chunks', 0)}",
                f"- 关键结论：{generation.get('supported_claim_count', 0)}/{generation.get('claim_count', 0)}",
                "",
            ]
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Batch evaluate OnboardAgent RAG metrics.")
    parser.add_argument("--questions", help="Optional JSON questions file.")
    parser.add_argument("--user-id", type=int, help="User ID to evaluate.")
    parser.add_argument("--username", help="Username to evaluate. Defaults to the first user.")
    parser.add_argument("--out", default="../artifacts/evaluations/rag_batch_eval.json", help="JSON output path.")
    parser.add_argument("--markdown", default="../artifacts/evaluations/rag_batch_eval.md", help="Markdown report path.")
    args = parser.parse_args()

    questions = load_questions(args.questions)
    user_id = get_user_id(args.username, args.user_id)
    documents = ready_documents(user_id)
    if not documents:
        raise RuntimeError("No ready documents found for this user.")

    results = []
    for index, question in enumerate(questions, 1):
        print(f"[{index}/{len(questions)}] {question['question']}")
        results.append(await run_one(question, user_id))

    summary = aggregate(results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "online_heuristic_batch",
        "user_id": user_id,
        "documents": documents,
        "summary": summary,
        "results": results,
    }

    out_path = ROOT / args.out
    md_path = ROOT / args.markdown
    out_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(md_path, user_id, documents, summary, results)

    print("\n=== Summary ===")
    for key, value in summary["metrics"].items():
        print(f"{key}: {pct(value)}")
    print(f"retrieval_hit_rate: {pct(summary['retrieval_hit_rate'])}")
    print(f"avg_retrieved_chunks: {summary['avg_retrieved_chunks']}")
    print(f"\nJSON: {out_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
