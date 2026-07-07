# OnboardAgent - 企业新员工入职培训助手

基于 RAG 的企业新员工入职培训知识助手，面向大型公司员工手册、规章制度、流程规范、信息安全和岗位培训资料，提供可追溯来源的问答、制度速览和培训知识卡片。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Naive UI + Pinia |
| 后端 | FastAPI + LangChain + SQLAlchemy |
| AI | DeepSeek / 本地 BGE 向量模型 |
| 向量库 | ChromaDB + SentenceTransformers |
| 数据库 | SQLite |
| 通信 | REST API + WebSocket |

## 快速启动
Mac/Linux一键启动脚本：
```bash
./start.sh
```
Windows启动脚本：
```bash
./start.bat
```
### 1. 后端

```bash
cd backend
pip install -r requirements.txt

# 配置API Key
cp .env.example .env
# 编辑 .env 填入 DeepSeek API Key (免费注册: https://platform.deepseek.com)

# 启动
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API文档: http://localhost:8000/docs

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:5173

## 项目结构

```
edu-assistant/
├── backend/
│   ├── app/
│   │   ├── api/        # API路由
│   │   ├── core/       # 配置/数据库/安全
│   │   ├── models/     # SQLAlchemy模型
│   │   ├── schemas/    # Pydantic Schema
│   │   ├── agents/     # 入职培训 Agent
│   │   └── rag/        # RAG检索模块
│   ├── data/           # 本地运行数据（uploads/chroma_db，已忽略）
│   ├── scripts/        # 数据重建、批量评测等脚本
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/      # 页面组件
│       ├── stores/     # Pinia状态管理
│       └── utils/      # 工具类
└── artifacts/          # 生成物与评测报告（已忽略）
```
