# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

OnboardAgent is a RAG-based enterprise onboarding assistant focused on answering new-employee questions over uploaded company handbooks, policies, workflows, security rules, and role-training materials. It is in early skeleton phase (single initial commit, ~46 source files, no tests or linting configured).

## Commands

### One-click start

```bash
# macOS / Linux
./start.sh

# Windows（双击 start.bat 或命令行运行）
start.bat

# 跨平台（任何装了 Python 的系统）
python start.py
```

Starts both backend (:8000) and frontend (:5173) concurrently. Auto-creates venv, installs dependencies, and copies `.env.example` if needed. Ctrl+C stops both.

`start.py` also supports partial start:

```bash
python start.py backend   # 仅后端
python start.py frontend  # 仅前端
```

### Backend (FastAPI + SQLAlchemy + SQLite)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # edit with API keys
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs auto-served at `http://localhost:8000/docs` (Swagger UI).

Seed demo data: `cd backend && python scripts/seed_demo_knowledge.py`

### Frontend (Vue 3 + Vite + Naive UI + Pinia)

```bash
cd frontend
npm install
npm run dev          # Vite dev server on :5173, proxies /api → :8000, /ws → ws://:8000
npm run build        # production build → dist/
```

### No tests or linting configured

There are no test frameworks, linters, or formatters set up for either frontend or backend.

## Architecture

### LLM gateway (`backend/app/agents/llm.py`)

`get_llm()` is the single factory for all LLM access. It reads `LLM_PROVIDER` from `.env` and returns one of:
- **ChatOpenAIGateway** wrapping `langchain_openai.ChatOpenAI` — used when a real API key is configured for DeepSeek or SiliconFlow (both speak OpenAI-compatible API).
- **LocalDemoLLM** — offline fallback that returns deterministic, rule-based responses for summaries, knowledge extraction, and Q&A. Activated automatically when no valid API key is present. This ensures the full upload → RAG → chat flow works without internet.

All agents and tools call `get_llm()` — never instantiate an LLM directly.

### RAG pipeline (upload → retrieve → answer)

1. **Upload** (`api/files.py`): file is saved to `backend/data/uploads/`, then immediately parsed and chunked.
2. **Parse** (`rag/loader.py`): `parse_file()` handles PDF (PyPDF2), Word (python-docx), TXT, Markdown. `split_text()` chunks by character count with overlap.
3. **Store** (`rag/vectorstore.py`): `ChromaVectorStore` stores local BGE embeddings in ChromaDB under `backend/data/chroma_db/`, isolated by user collection.
4. **Retrieve** (`rag/retriever.py`): `retrieve_relevant_chunks()` queries the vector store and `format_retrieved_context()` builds the prompt context block.
5. **Generate** (`agents/edu_agent.py`): `edu_chat_stream()` is an async generator that retrieves context, builds a prompt with the last 3 conversation rounds (6 messages), and streams LLM output token-by-token.

### Onboarding agent

- **edu_agent** (`agents/edu_agent.py`): onboarding agent that uses RAG — retrieves from uploaded company training documents before answering.

The onboarding agent exposes an `async generator` streaming interface and is invoked from `api/chat.py`.

### WebSocket streaming protocol

Chat uses WebSocket at `/ws/chat/{user_id}` with JSON messages. The `ChatWebSocket` class (`frontend/src/utils/websocket.js`) handles connection, auto-reconnect (up to 5 attempts, exponential backoff), and dispatching by message type:

| `data.type` | Purpose |
|-------------|---------|
| `thinking` | Agent reasoning/planning visualization |
| `token` | Streaming response token (appended to message) |
| `done` | Response complete |
| `error` | Error occurred |
| `meta` | Metadata (conversation ID, etc.) |

The frontend falls back to HTTP POST `/api/chat/ask` if WebSocket fails.

### Auth flow

JWT-based: `backend/app/core/security.py` uses bcrypt + python-jose. The frontend axios instance (`utils/api.js`) attaches the token via interceptor and redirects to `/login` on 401. The Pinia `auth` store manages login/register/logout state. All protected API endpoints use the `get_current_user` dependency (pattern: copy from `api/auth.py`).

### Key design decisions (do not change without reason)

- **User data isolation**: vector store files are per-user (`user_{user_id}_docs.json`).
- **Upload auto-vectorization**: file upload triggers immediate text extraction + chunking + storage — no separate "process" step.
- **Conversation window**: last 3 rounds (6 messages) included in LLM context (`conversation_history[-6:]`).
- **CORS**: only `localhost:5173` and `localhost:3000` allowed.
- **Config**: all settings via `pydantic-settings` from `.env` — see `backend/app/core/config.py`.

### Database

SQLite via SQLAlchemy 2.0. Tables are auto-created on startup via `base.metadata.create_all()` in `core/database.py`. Four models: User, Conversation, Message, Document. Database file: `backend/edu_assistant.db`.
