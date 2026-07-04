"""
为当前注册用户生成 EduAssistant Sprint1 演示知识库。

用法：
    python scripts/seed_demo_knowledge.py

脚本会读取 users 表中的第一个用户，为其创建几份演示资料、documents 记录，
并写入本地检索库 chroma_db/user_<id>_docs.json。
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "edu_assistant.db"
UPLOAD_DIR = BASE_DIR / "uploads"
KNOWLEDGE_DIR = BASE_DIR / "chroma_db"


DEMO_DOCS = [
    {
        "filename": "demo_python_review.md",
        "original_name": "演示资料-Python基础复习.md",
        "file_type": "md",
        "content": """# Python基础复习

Python是一门强调可读性和开发效率的高级编程语言，适合用于Web后端、数据分析、自动化脚本和人工智能应用开发。

## 变量与数据类型

Python常见数据类型包括整数、浮点数、字符串、布尔值、列表、元组、字典和集合。变量不需要提前声明类型，解释器会根据赋值自动推断。列表适合保存有序可变数据，字典适合保存键值对。

## 函数

函数用于封装可复用逻辑。定义函数时使用def关键字，可以设置参数、默认值和返回值。良好的函数应该职责单一、命名清晰，并尽量避免修改外部状态。

## 模块与包

模块是一个Python文件，包是包含多个模块的目录。通过import可以复用已有代码。项目开发中通常会把数据库、路由、模型、工具函数拆分到不同模块中，便于维护。

## 异常处理

异常处理使用try/except/finally结构。对于文件解析、网络请求、数据库操作等容易失败的逻辑，应捕获异常并给出清晰提示。

## 学习建议

学习Python时应重点掌握基本语法、函数、面向对象、文件读写、虚拟环境和常用第三方库。做项目时要多关注代码结构和可维护性。
""",
    },
    {
        "filename": "demo_data_structure.md",
        "original_name": "演示资料-数据结构与算法.md",
        "file_type": "md",
        "content": """# 数据结构与算法复习

数据结构用于组织和管理数据，算法用于解决问题。优秀的程序通常需要选择合适的数据结构，并设计复杂度可接受的算法。

## 数组与链表

数组支持通过下标快速访问，时间复杂度为O(1)，但插入和删除可能需要移动元素。链表插入和删除灵活，但随机访问效率较低。

## 栈与队列

栈遵循后进先出原则，常用于括号匹配、函数调用和撤销操作。队列遵循先进先出原则，常用于任务调度、广度优先搜索和消息缓冲。

## 哈希表

哈希表通过哈希函数把键映射到存储位置，平均情况下查找、插入和删除时间复杂度接近O(1)。Python中的dict就是哈希表的典型实现。

## 排序算法

常见排序算法包括冒泡排序、选择排序、插入排序、归并排序和快速排序。归并排序稳定，时间复杂度为O(n log n)；快速排序平均效率高，但最坏情况可能退化。

## 复杂度分析

时间复杂度描述算法运行时间随输入规模增长的趋势，空间复杂度描述额外内存占用。项目开发中应避免明显的O(n²)低效逻辑影响用户体验。
""",
    },
    {
        "filename": "demo_scrum_rag.md",
        "original_name": "演示资料-Scrum与RAG项目说明.md",
        "file_type": "md",
        "content": """# Scrum与RAG项目说明

EduAssistant项目采用Scrum敏捷开发模式推进，Sprint1目标是完成最小可用产品：用户注册登录、资料上传、RAG智能问答、课文摘要、知识点提取和ChatUI。

## Scrum角色

Master负责团队协调、进度管理、日报、风险追踪和会议组织。PO负责产品需求、用户故事、优先级排序和验收标准。PM负责技术架构、核心代码、代码Review、测试和部署。Dev成员分别承担前端和后端开发任务。

## Sprint1范围

Sprint1只关注核心闭环：注册登录后，用户上传学习资料，系统解析文本并分块入库，用户提问时系统检索相关片段，再生成有来源的回答。摘要生成和知识点提取作为P1功能帮助用户快速理解资料。

## RAG流程

RAG是检索增强生成。第一步是把文档切分为多个文本块并存入知识库；第二步是根据用户问题检索相关文本块；第三步是把检索结果和问题一起交给大模型生成回答。RAG的优点是回答有资料依据，可以减少幻觉。

## 风险控制

AI项目常见风险包括API额度不足、外部模型不可用、文件解析失败、前后端联调时间不足和演示环境不稳定。EduAssistant当前提供本地演示模式，在没有真实API Key时也能跑通流程。
""",
    },
    {
        "filename": "demo_baoyan_guide.md",
        "original_name": "演示资料-保研准备指南.md",
        "file_type": "md",
        "content": """# 保研准备指南

保研通常包括信息收集、材料准备、夏令营报名、预推免申请、面试考核和系统确认等阶段。不同学校和学院政策存在差异，最终应以官方通知为准。

## 基础材料

常见材料包括个人简历、成绩单、排名证明、英语成绩、获奖证书、科研或项目经历、个人陈述、专家推荐信和身份证明。材料应提前整理成PDF版本，命名清晰。

## 时间节点

夏令营通常集中在5月至7月，预推免通常集中在8月至9月，正式推免系统一般在9月下旬开放。学生应建立时间线，避免错过目标院校报名截止日期。

## 面试准备

面试通常考察专业基础、科研潜力、项目经历、英语表达和综合素质。准备时应熟悉自己的项目，能清楚说明问题背景、技术路线、个人贡献和最终成果。

## 院校匹配

选择院校时要综合考虑成绩排名、科研经历、竞赛成果、英语水平、目标专业方向和导师研究方向。建议设置冲刺、匹配和保底三个层次。
""",
    },
]


def split_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


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
    vector_path = KNOWLEDGE_DIR / f"user_{user_id}_docs.json"
    vector_records = []
    if vector_path.exists():
        vector_records = json.loads(vector_path.read_text(encoding="utf-8") or "[]")

    created = 0
    for item in DEMO_DOCS:
        exists = cur.execute(
            "select id from documents where user_id = ? and original_name = ?",
            (user_id, item["original_name"]),
        ).fetchone()
        if exists:
            continue

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
        for index, chunk in enumerate(chunks):
            vector_records.append(
                {
                    "page_content": chunk,
                    "metadata": {
                        "document_id": str(document_id),
                        "document_name": item["original_name"],
                        "chunk_index": index,
                        "file_type": item["file_type"],
                    },
                }
            )
        created += 1

    con.commit()
    con.close()
    vector_path.write_text(json.dumps(vector_records, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已为用户 {username}(id={user_id}) 创建 {created} 份演示资料。")
    print(f"知识库索引：{vector_path}")


if __name__ == "__main__":
    main()
