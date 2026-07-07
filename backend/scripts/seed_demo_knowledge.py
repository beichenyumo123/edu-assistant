"""
为当前注册用户生成 OnboardAgent 企业入职培训演示知识库。

用法：
    python scripts/seed_demo_knowledge.py

脚本会读取 users 表中的第一个用户，为其创建几份企业培训演示资料、documents 记录，
并写入 ChromaDB 向量库。
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

DB_PATH = BASE_DIR / "edu_assistant.db"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
KNOWLEDGE_DIR = DATA_DIR / "chroma_db"


DEMO_DOCS = [
    {
        "filename": "demo_employee_handbook.md",
        "original_name": "演示资料-员工手册与入职流程.md",
        "file_type": "md",
        "source_type": "employee_handbook",
        "trust_level": "high",
        "content": """# 员工手册与入职流程

本资料用于帮助新员工了解入职后的基本安排、试用期要求和常用内部支持渠道。所有具体执行以公司正式通知和 HR 解释为准。

## 入职第一周

新员工应在入职第一周完成账号开通、工牌领取、设备验收、企业邮箱登录、办公软件安装和新人必修课程学习。直属导师会协助熟悉团队成员、工作流程和近期任务。

## 试用期管理

试用期通常为三个月。试用期内员工需完成岗位学习计划，并在每月与直属负责人进行一次反馈沟通。转正评估重点包括工作态度、岗位技能、协作表现和制度遵守情况。

## 培训要求

新人必修培训包括公司文化、信息安全、合规行为准则、财务报销流程和岗位基础知识。未按时完成必修培训可能影响试用期评估。

## 内部支持

遇到账号、设备、工位、系统权限或培训平台问题，可先联系直属导师；涉及劳动合同、社保公积金、薪酬福利等事项，应联系 HR 服务窗口。
""",
    },
    {
        "filename": "demo_attendance_leave_policy.md",
        "original_name": "演示资料-考勤与休假制度.md",
        "file_type": "md",
        "source_type": "policy",
        "trust_level": "high",
        "content": """# 考勤与休假制度

本制度说明员工日常考勤、请假、加班和异常考勤处理要求。各地办公室可能存在差异，具体以所在地 HR 通知为准。

## 工作时间

公司标准工作时间为周一至周五 9:00 至 18:00，中午休息 1 小时。部分岗位可根据业务安排采用弹性工作制，但须经直属负责人确认。

## 打卡要求

员工应在指定考勤系统完成上下班打卡。因外出拜访、出差、系统故障等原因无法打卡的，应在 3 个工作日内提交异常考勤说明。

## 请假流程

请假应至少提前 1 个工作日通过系统提交申请。病假需按公司规定补充医疗证明。未经审批擅自缺勤，可能按旷工处理。

## 加班管理

加班需基于业务需要并提前获得直属负责人审批。未经审批的延时停留不默认计入加班。加班补偿方式以公司制度和所在地法规要求为准。
""",
    },
    {
        "filename": "demo_reimbursement_travel_policy.md",
        "original_name": "演示资料-差旅与报销流程.md",
        "file_type": "md",
        "source_type": "workflow",
        "trust_level": "high",
        "content": """# 差旅与报销流程

本资料用于说明员工差旅申请、费用标准、发票要求和报销审批流程，帮助新员工避免常见报销问题。

## 差旅申请

员工因公出差前，应在系统中提交差旅申请，写明出差目的、城市、时间、预算和项目归属。未提前审批的差旅费用，可能无法报销。

## 交通住宿

交通和住宿应符合公司差旅标准。超出标准的费用需提前说明原因并获得负责人审批。个人旅游、探亲或非公务产生的费用不得报销。

## 发票要求

报销需提供真实、合规、完整的发票和消费凭证。发票抬头、税号、金额和日期应与实际业务一致。电子发票应避免重复提交。

## 报销时限

员工应在费用发生后 30 天内提交报销申请。逾期提交需说明原因，是否受理由财务部门根据制度判断。
""",
    },
    {
        "filename": "demo_security_compliance.md",
        "original_name": "演示资料-信息安全与合规行为准则.md",
        "file_type": "md",
        "source_type": "security",
        "trust_level": "high",
        "content": """# 信息安全与合规行为准则

信息安全和合规是所有员工必须遵守的基本要求。新员工应在入职阶段完成相关培训，并在日常工作中持续遵守。

## 账号与权限

员工账号仅限本人使用，不得出借、共享或转交他人。系统权限应按岗位需要申请，离岗、转岗或项目结束后应及时回收不再需要的权限。

## 数据保密

客户数据、商业计划、源代码、合同价格、员工个人信息等均属于敏感信息。未经授权不得复制、外发、上传到个人网盘或输入到未经批准的第三方工具。

## 设备安全

公司设备应设置强密码并开启自动锁屏。发现设备丢失、账号异常登录或疑似钓鱼邮件，应立即联系信息安全团队。

## 合规行为

员工不得利用岗位便利收受不当利益，不得泄露公司商业秘密，不得伪造报销凭证或隐瞒利益冲突。发现违规风险应及时向合规渠道报告。
""",
    },
]


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"数据库不存在：{DB_PATH}")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    user = cur.execute("select id, username from users order by id limit 1").fetchone()
    if not user:
        raise SystemExit("当前没有用户，请先在网页注册一个账号。")

    user_id, username = user

    from app.rag.loader import split_text
    from app.rag.vectorstore import get_vectorstore

    vectorstore = get_vectorstore(user_id=user_id)

    # 清除旧文档记录和向量数据，确保幂等重跑
    cur.execute(
        "select id from documents where user_id = ?",
        (user_id,),
    )
    old_ids = [row[0] for row in cur.fetchall()]
    for old_id in old_ids:
        cur.execute("delete from documents where id = ?", (old_id,))
    vectorstore.delete()
    if old_ids:
        print(f"已清除 {len(old_ids)} 条旧文档记录，重新生成...")

    created = 0
    for item in DEMO_DOCS:

        file_path = UPLOAD_DIR / item["filename"]
        file_path.write_text(item["content"], encoding="utf-8")
        chunks = split_text(item["content"])
        cur.execute(
            """
            insert into documents
                (user_id, filename, original_name, file_type, file_size, chunk_count, status, error_message)
            values (?, ?, ?, ?, ?, ?, 'ready', null)
            """,
            (
                user_id,
                item["filename"],
                item["original_name"],
                item["file_type"],
                file_path.stat().st_size,
                len(chunks),
            ),
        )
        document_id = cur.lastrowid
        vectorstore.add_texts(
            texts=chunks,
            metadatas=[
                {
                    "document_id": str(document_id),
                    "document_name": item["original_name"],
                    "chunk_index": i,
                    "file_type": item["file_type"],
                    "source_type": item["source_type"],
                    "trust_level": item["trust_level"],
                }
                for i in range(len(chunks))
            ],
        )
        created += 1

    con.commit()
    con.close()

    print(f"已为用户 {username}(id={user_id}) 创建 {created} 份演示资料。")
    print(f"知识库索引：{KNOWLEDGE_DIR}（ChromaDB）")


if __name__ == "__main__":
    main()
