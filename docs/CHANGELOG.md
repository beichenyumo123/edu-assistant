# 版本更新说明

---

## 2026-07-04 — 启动脚本跨平台改造

### 变更

- **`start.py`** (新增) — 跨平台 Python 启动脚本，替代纯 bash 的 `start.sh`
  - 自动检测 Windows/macOS/Linux，适配不同平台的 venv 路径和命令
  - 支持 `python start.py [all|backend|frontend]` 选择性启动
  - 优雅关闭：`terminate()` → `wait(5s)` → `kill()` 渐进式清理子进程
- **`start.sh`** (重写) — 精简为 3 行薄封装，`exec python start.py "$@"` 委托给 Python
- **`start.bat`** (新增) — Windows 批处理入口，检测 Python 后调用 `python start.py`
- **`CLAUDE.md`** — 更新启动命令，补充 Windows 和跨平台用法

### 兼容性

| 平台 | 启动方式 |
|------|---------|
| macOS / Linux | `./start.sh` 或 `python start.py` |
| Windows | 双击 `start.bat` 或 `python start.py` |

---

## 2026-07-04 — 完成 T33：Agent 思考面板持久化

### 变更

- **`backend/app/models/message.py`**
  - `messages` 表新增 `agent_steps` 字段，用 JSON 保存 assistant 消息对应的 Agent 思考步骤
- **`backend/app/core/database.py`**
  - 启动时为已有 SQLite 数据库自动补充 `messages.agent_steps` 列，避免旧库缺列
- **`backend/app/api/chat.py`**
  - HTTP 与 WebSocket 两条聊天链路都收集 Agent 思考步骤
  - 每个步骤增加 `tool_name` 和 `elapsed_ms`，完成后随 assistant 消息一起保存
  - WebSocket `done` 消息返回完整 `agent_steps`
- **`backend/app/api/conversations.py`**
  - 历史对话详情接口解析并返回 `agent_steps`
- **`frontend/src/views/ChatView.vue`**
  - 思考过程从临时独立气泡改为 assistant 消息内的可折叠面板
  - 消息完成后仍保留思考过程，切换历史对话后也能恢复
  - 面板内展示步骤、工具名称和累计耗时
- **`docs/sprint1-progress.md`**
  - T33/T34 更新为完成，剩余事项仅保留端到端联调验证

---

## 2026-07-04 — 重构知识点导出的笔记结构

### 问题

上一版虽然解决了部分原文摘录重复问题，但导出的 Markdown 仍然是扁平知识点列表，且会把检索到的长 chunk 原样贴到知识点下面，导致文件阅读体验像碎片拼贴，缺少清晰层级。

### 修复

- **`backend/app/api/tools.py`**
  - 知识点提取 Prompt 改为面向“可导出的复习笔记”生成，新增 `category`、`key_points`、`examples`、`source_excerpt` 等结构化字段
  - 兼容旧 JSON 格式，缺失 `category` 时按标题和描述自动归类
  - 检索原文时不再直接返回整段 chunk，而是从 chunk 中抽取 1-2 个最相关短句，最长约 280 字
  - 保留跨知识点去重，减少重复摘录
- **`backend/app/agents/llm.py`**
  - 离线 `LocalDemoLLM` 的知识点输出同步升级为新结构，保证无 API Key 时导出格式一致
- **`frontend/src/views/ChatView.vue`**
  - `downloadKnowledgeMarkdown()` 改为“文档概览 → 模块分组 → 知识点 → 复习要点/可套用表达/原文依据”的层级结构
  - 导出时对列表和摘录做清洗、截断、去重，避免长段原文破坏笔记结构

### 效果

导出的 .md 从“知识点碎片 + 大段原文”改为“分模块复习笔记”。每个知识点保留精简出处，但不会再把整块检索文本全部贴进文件。

---

## 2026-07-04 — 修复知识点导出的原文摘录质量问题

### 问题

导出的 .md 中每个知识点下面贴的原文摘录几乎一模一样，且包含大量与知识点无关的内容，不可用。根因是 4 个叠加问题：

1. **PDF 排版断行未合并** — PyPDF2 提取的文本保留了 PDF 的视觉换行，导致一句英文模板被拆成 3 行，分块时句子被截断、不同内容被硬拼在一起
2. **chunk 粒度过粗** — 不相关的整页内容混在一个 chunk 里
3. **无相似度阈值** — 检索召回的不相关 chunk 也照单全收
4. **无跨知识点去重** — 同一个大杂烩 chunk 出现在所有知识点下

### 修复

- **`backend/app/rag/loader.py`**
  - 新增 `_merge_pdf_lines()` — 将 PDF 排版断行合并为自然段落：检测行尾是否为句末标点，非句末则与下一行合并（加空格），空行作为段落边界
  - `split_text()` 改进 — 用 `text.strip()` + `re.sub(r'\n{3,}', '\n\n', ...)` 替代逐行 strip 重建，保留 `\n\n` 段落间距；切分阈值从 chunk_size*0.45 降到 0.35，段落边界更易被选为切分点
- **`backend/app/rag/vectorstore.py`**
  - 新增 `similarity_search_with_score()` — 返回 `list[tuple[RetrievedDocument, float]]`，分数为余弦距离（0=完全相同，2=完全相反）
- **`backend/app/api/tools.py`**
  - `extract_knowledge` 检索逻辑重写：`similarity_search` → `similarity_search_with_score`，k=3 → k=5
  - 新增距离阈值过滤（`DISTANCE_THRESHOLD = 1.0`，余弦距离 >=1.0 的结果丢弃）
  - 新增跨知识点全局去重（`global_seen` set，用文本前 120 字符做 dedup key）

### 注意

已上传的旧文档的 ChromaDB 向量是用旧分块逻辑生成的。要使修复生效，需**重新上传文件**以触发新的解析+分块+向量化流程。

---

## 2026-07-04 — 增强知识点导出：附带文档原文摘录

### 变更

- **`backend/app/api/tools.py`** — `extract_knowledge` 接口增强
  - LLM 提取知识点后，用每个知识点的标题+描述去 ChromaDB 做语义检索（k=3）
  - 召回结果仅保留属于当前文档的原文片段，按文本去重
  - 响应中每个知识点新增 `relevant_chunks` 字段（含 `text` 和 `chunk_index`）
- **`frontend/src/views/ChatView.vue`** — `downloadKnowledgeMarkdown()` 升级
  - 导出的 .md 中每个知识点下方以引用块（`>`）形式附带原文摘录
  - 多行原文自动换行缩进，保持 Markdown 格式兼容

### 效果

导出的 .md 从"知识点目录"变为"结构化复习笔记"——每个知识点不仅有 LLM 的简短解释，还附带文档原文，翻阅时可直接对照出处。

---

## 2026-07-04 — Sprint1 T24：知识点 Markdown 导出

### 新增

- **`frontend/src/views/ChatView.vue`** — 知识点 Markdown 导出功能
  - 新增 `downloadKnowledgeMarkdown()` 函数，将提取的知识点生成为格式化的 .md 文件
  - 导出内容包括：文档名称标题、导出时间戳、知识点数量统计、各知识点标题与描述
  - 使用 `Blob` + `URL.createObjectURL()` 触发浏览器下载，无需后端接口
  - 知识点结果卡片 footer 新增"导出 Markdown"按钮（带 DownloadOutline 图标）
  - 摘要卡片与知识点卡片的 footer 统一为 `<n-space>` 横向布局

### 进度

- PBI_06（知识点提取）3 项 Task 全部完成：T22 ✅ T23 ✅ T24 ✅

---

## 2026-07-04 — 修复流式输出时无法向上滚动

### 变更

- **`frontend/src/views/ChatView.vue`** — `scrollToBottom()` 增加智能滚动逻辑
  - 新增 `isNearBottom()` 判断用户是否在底部（阈值 50px）
  - 流式 token 推送时仅在用户位于底部时才自动滚动
  - 用户主动发送消息、加载历史记录时强制滚动到底部
  - 用户向上滚动阅读历史消息时不会被新 token 拉回底部

---

## 2026-07-04 — Sprint1 T7：语义向量检索

### 变更概要

将 `LocalVectorStore`（JSON + 关键词 TF 打分）替换为 **ChromaDB + embedding 模型**，实现真正的语义向量检索。

### 新增

- **`backend/app/rag/embeddings.py`** — embedding 模型工厂函数 `get_embeddings()`
  - 优先使用 SiliconFlow 云端 API（`BAAI/bge-m3`，1024 维）
  - 无 API Key 时自动回退本地 `shibing624/text2vec-base-chinese`（768 维）
- **ChromaDB 持久化存储**于 `backend/chroma_db/`，按 `user_{id}` 隔离 Collection

### 变更

- **`backend/app/rag/vectorstore.py`** — `ChromaVectorStore` 替换 `LocalVectorStore`
  - 保留 `RetrievedDocument`、`get_vectorstore()`、`delete_user_collection()` 接口不变
  - `add_texts` 使用确定性 ID 实现幂等（重跑 seed 不会重复）
- **`backend/app/core/config.py`** — 新增 `EMBEDDING_PROVIDER`、`EMBEDDING_MODEL`、`LOCAL_EMBEDDING_MODEL`
- **`backend/.env.example`** — 新增 embedding 配置项
- **`backend/scripts/seed_demo_knowledge.py`** — 移除重复 `split_text()`，改用 `get_vectorstore().add_texts()`
- **`backend/requirements.txt`** — 新增 `chromadb`、`langchain-chroma`、`langchain-huggingface`、`sentence-transformers`；langchain 系列升级至 1.x

### 未改动（零影响）

- `api/files.py`、`api/chat.py`、`agents/edu_agent.py`、`rag/retriever.py`、`rag/loader.py`

### 验证结果

- 语义检索测试通过："编程语言" → Python 文档（top-1），"保研材料" → 保研指南（top-1）
- Delete by document_id 精确删除，delete all 清空全部
- 种子数据写入 4 份演示文档至 ChromaDB
- 端到端 RAG 问答返回带来源标注的回答

---

## 2026-07-04 — 修复 bcrypt 兼容性

### 变更

- **移除 `passlib` 依赖**，直接使用 `bcrypt` 进行密码哈希/验证（`backend/app/core/security.py`）
- **`backend/requirements.txt`** — 移除 `passlib[bcrypt]==1.7.4`，bcrypt 改为 `>=4.0.1`

### 原因

`passlib` 与 bcrypt 4.1+ 不兼容（`__about__` 属性移除 + 72 字节密码限制），注册时抛 500 错误。

---

## 2026-07-04 — 完善 .gitignore、新增启动脚本

### 新增

- **`start.sh`** — 一键启动脚本（自动创建 venv、安装依赖、启动前后端）
- **`CLAUDE.md`** — 项目架构文档

### 变更

- **`.gitignore`** — 新增 `.DS_Store`、`.vite/`、`.pytest_cache/`、`.cursor/`、日志等规则
