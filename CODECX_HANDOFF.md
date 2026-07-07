# Codex 开发交接文档

> 本文档供 Codex（或任何AI编程助手）阅读，以理解项目当前状态和后续开发任务。

---

## 1. 项目概览

- **项目名**：OnboardAgent — 基于RAG的企业新员工入职培训助手
- **方向**：AI大模型
- **团队**：智学先锋，5人，10天周期（7/2-7/11），Scrum开发
- **当前状态**：项目骨架已完成（46个文件），Sprint1待开始

## 2. 已完成的代码

### 后端（FastAPI + LangChain + ChromaDB + SQLite）

```
backend/app/
├── main.py              ← FastAPI入口，已注册5个路由模块
├── core/
│   ├── config.py        ← 集中配置（Settings类，pydantic-settings）
│   ├── database.py      ← SQLAlchemy引擎 + Session + Base + init_db()
│   └── security.py      ← JWT(bcrypt+python-jose) + 密码哈希
├── models/
│   ├── user.py          ← User表（username/email/password/grade/major）
│   ├── conversation.py  ← Conversation表（user_id/agent_type/title）
│   ├── message.py       ← Message表（conv_id/role/content/sources JSON）
│   └── document.py      ← Document表（上传文件元数据+向量化状态）
├── schemas/
│   ├── auth.py          ← RegisterRequest / LoginRequest / TokenResponse
│   ├── chat.py          ← ChatRequest / SummaryRequest / KnowledgeExtractRequest
│   └── file.py          ← FileUploadResponse
├── api/
│   ├── auth.py          ← POST /api/auth/register, /api/auth/login, GET /api/auth/me
│   ├── files.py         ← POST/GET/DELETE /api/files（上传自动向量化到ChromaDB）
│   ├── chat.py          ← POST /api/chat/ask + WebSocket /ws/chat/{user_id}
│   ├── conversations.py ← GET/DELETE /api/conversations（对话CRUD）
│   └── tools.py         ← POST /api/tools/summarize, /api/tools/extract-knowledge
├── agents/
│   ├── llm.py           ← get_llm() 工厂函数，支持DeepSeek/硅基流动切换
│   ├── edu_agent.py     ← edu_chat_stream() 异步生成器，企业培训资料RAG检索→Prompt→流式输出
└── rag/
    ├── loader.py        ← parse_file() 多格式解析（PDF/Word/TXT/MD）+ split_text()
    ├── vectorstore.py   ← get_vectorstore(user_id) ChromaDB按用户隔离
    └── retriever.py     ← retrieve_relevant_chunks() + format_retrieved_context()
```

### 前端（Vue3 + Vite + NaiveUI + Pinia）

```
frontend/src/
├── main.js              ← createApp + Pinia + Router
├── App.vue              ← 路由容器
├── router/index.js      ← /login + /（含token路由守卫）
├── stores/
│   ├── auth.js          ← login/register/logout/fetchUser
│   └── chat.js          ← conversations/messages/thinking状态
├── utils/
│   ├── api.js           ← axios实例（baseURL/token拦截器/401跳转）
│   ├── websocket.js     ← ChatWebSocket类（connect/send/on/自动重连）
│   └── markdown.js      ← MarkdownIt + highlight.js 渲染器
└── views/
    ├── LoginView.vue    ← 登录/注册双Tab页面（完整UI+逻辑）
    └── ChatView.vue     ← 完整对话界面（侧边栏+消息区+预设卡片+Agent思考可视化+文件上传抽屉）
```

## 3. 关键设计决策（不要改）

1. **每个用户独立的ChromaDB Collection**（`user_{user_id}_docs`），实现数据隔离
2. **WebSocket用于流式对话**，路径`/ws/chat/{user_id}`，JSON消息协议
3. **LLM配置通过.env文件**，`get_llm()`从config读取，支持deepseek/siliconflow切换
4. **文件上传后自动向量化**（files.py的upload_file），状态字段标识进度
5. **对话历史取最近3轮**（edu_agent.py的`conversation_history[-6:]`）

## 4. 缺失待补（Sprint1需要开发的部分）

以下功能代码骨架已写好但可能需要完善：

| 事项 | 优先级 | 说明 |
|------|--------|------|
| tools.py的导入路径 | 🔴 | 当前import从`..`导入，确保uvicorn能正确解析 |
| pydantic-settings包 | 🔴 | config.py用了`pydantic_settings`，需确认在requirements.txt |
| langchain-chroma包 | 🔴 | vectorstore.py用了`langchain_chroma`，需确认依赖 |
| 前端npm包版本锁定 | 🟡 | package.json用了`^`，首次install可能版本差异 |
| 错误处理完善 | 🟡 | 部分except用了pass，生产中应加日志 |
| 对话标题自动截取 | 🟢 | chat.py已实现（前端30字截取），后端WS也可加 |

## 5. 开发批次规划

### Batch 1：让现有代码能跑（第1优先级）

**目标**：`pip install`成功 + `npm install`成功 + 后端启动 + 前端启动 + 注册登录流程走通

**提示词**：
```
我正在进行一个FastAPI+Vue3的项目OnboardAgent。请帮我：

1. 检查 backend/requirements.txt，确认所有包名正确且版本兼容
2. 检查 backend/app/ 下所有Python文件的import路径是否正确
3. 给出完整的启动步骤（包括虚拟环境创建）
4. 如果有缺失的依赖或错误的import，直接给出修复后的文件内容
```

### Batch 2：Sprint1核心——RAG问答链路（第2优先级）

**目标**：用户上传PDF → 自动向量化 → RAG问答 → 流式返回结果

**提示词**：
```
项目OnboardAgent的后端代码在 backend/app/ 下。

请阅读以下文件：
- backend/app/api/chat.py（WebSocket对话）
- backend/app/agents/edu_agent.py（RAG检索+LLM生成）
- backend/app/rag/loader.py（文档解析）
- backend/app/rag/vectorstore.py（ChromaDB）
- backend/app/rag/retriever.py（检索器）

现在需要完善以下功能：
1. [具体描述要完善的功能]
2. [具体描述要修复的bug]

请给出修改后的完整文件内容。
```

### Batch 3：前端联调（第3优先级）

**目标**：前端ChatView能通过WebSocket对话、文件上传抽屉能工作

**提示词**：
```
项目OnboardAgent的前端代码在 frontend/src/ 下。

当前ChatView.vue使用WebSocket进行流式对话，但可能需要调试以下问题：
1. [具体问题描述]

请阅读 frontend/src/views/ChatView.vue 和 frontend/src/utils/websocket.js，
给出修复方案。
```

### Batch 4：Sprint2——企业培训工具增强

**目标**：围绕企业入职培训问答增强制度速览、知识卡片和质量观测能力

**提示词**：
```
项目OnboardAgent已有入职培训Agent（edu_agent.py），现在需要添加更多企业培训工具能力。

当前的教育Agent参考：backend/app/agents/edu_agent.py

请实现：
1. [具体功能描述]
2. [具体功能描述]
```

## 6. 给Codex的通用提示词模板

### 模板A：理解项目（每个新会话先跑这个）

```
请按顺序阅读以下文件，然后给我一个项目结构总结：

1. G:\生产实习\edu-assistant\README.md
2. G:\生产实习\智学先锋-OnboardAgent项目设计报告.md
3. G:\生产实习\edu-assistant\backend\app\main.py
4. G:\生产实习\edu-assistant\backend\app\core\config.py
5. G:\生产实习\edu-assistant\backend\app\models\__init__.py

阅读完后回答：
- 这个项目做什么？
- 技术栈是什么？
- 当前代码完成度大概多少？
- 还缺什么才能跑起来？
```

### 模板B：开发新功能

```
我要在OnboardAgent项目中添加[功能描述]。

相关现有代码：
- backend/app/agents/edu_agent.py（参考Agent的实现模式）
- backend/app/api/chat.py（参考API路由的写法）
- backend/app/schemas/chat.py（参考Schema定义）

要求：
1. 遵循现有代码风格（命名/注释/结构）
2. 复用现有的 get_llm() 和 get_db()
3. 新API要加JWT认证（参考auth.py的get_current_user依赖注入）
4. 只输出需要修改/新增的文件，不要重写整个项目
```

### 模板C：修Bug

```
OnboardAgent项目运行时报错：

[粘贴完整报错信息]

相关文件：[文件路径]

请分析原因并给出修复方案。只修改必要的代码。
```

## 7. Codex的局限性（需要注意）

| Codex擅长 | Codex不擅长 |
|-----------|-------------|
| 单文件修改/新增 | 一次性重构整个项目 |
| 按明确指令写代码 | 主动发现设计问题 |
| 阅读已有代码后模仿风格 | 记忆跨会话的上下文 |
| 短文件（<500行） | 超长文件（>1000行） |

**建议**：
- 每次只让Codex处理1-2个文件
- 先让它"读"相关文件，再让它"写"
- 具体指令 > 模糊指令（"在XX函数后加一个YY功能" > "完善这个系统"）
- 每个新会话开头都粘贴"模板A"让它重建上下文

## 8. 当前计划的合理性评估

**结论：计划合理，可以分批完成。**

- Sprint1（Day1-4）：现有骨架已完成约60%，剩余工作主要是调试+联调，4天充裕
- Sprint2（Day5-10）：功能增量开发，每个功能相对独立，可并行
- 最大风险：LLM API配置（DeepSeek免费注册5分钟搞定）
- 次大风险：ChromaDB + SentenceTransformers首次下载模型（需要网络，约500MB）

**给Codex的分批策略**：
每个功能 = 1个Codex会话 = 1个明确的输入→输出任务
不要试图在一个会话里搞定所有东西。
