# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

EduAssistant is a RAG + dual-agent intelligent learning assistant covering academic tutoring (`edu_agent`) and graduate school recommendation (`baoyan_agent`). Sprint1 all 34 tasks complete, awaiting end-to-end validation.

**Stack**: FastAPI + SQLAlchemy 2.0 + SQLite + ChromaDB | Vue 3 + Vite + Naive UI + Pinia

## Commands

### One-click start (cross-platform)

```bash
# macOS / Linux
./start.sh

# Windows（双击或命令行）
start.bat

# 所有平台
python start.py              # 启动前后端
python start.py backend       # 仅后端
python start.py frontend      # 仅前端
```

All three enforce **Python 3.11** (project requirement). Auto-creates venv, installs deps, copies `.env.example`. Ctrl+C graceful shutdown.

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit API keys
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs` (Swagger).

Seed demo data (idempotent, clears old records before reseeding):

```bash
cd backend && python scripts/seed_demo_knowledge.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Vite dev server on :5173, proxies /api → :8000, /ws → ws://:8000
npm run build      # production build → dist/
```

### No tests or linting configured yet

## Architecture

### LLM gateway (`backend/app/agents/llm.py`)

`get_llm()` is the single factory. Reads `LLM_PROVIDER` from `.env`, returns:
- **ChatOpenAIGateway** wrapping `langchain_openai.ChatOpenAI` — for DeepSeek / SiliconFlow (both OpenAI-compatible)
- **LocalDemoLLM** — offline fallback: deterministic responses for summaries, knowledge extraction, Q&A. Activated when no valid API key. Ensures full upload → RAG → chat flow works without internet.

`tools.py` wraps calls via `_safe_llm_invoke()` — returns `None` on failure, then falls back to local rule-based extraction (`_fallback_knowledge_points` / `_fallback_summary`). Never crash on LLM unavailability.

### Embedding model (`backend/app/rag/embeddings.py`)

`get_embeddings()` — single factory, `@lru_cache(maxsize=1)`. **Local-only** by default: `BAAI/bge-small-zh-v1.5` via `langchain_huggingface.HuggingFaceEmbeddings`, with `local_files_only=True`. Model is shared across upload vectorization and query retrieval (same vector space).

### RAG pipeline

1. **Upload** (`api/files.py`): file saved → parsed → chunked → vectorized in one pass
2. **Parse** (`rag/loader.py`): `parse_file()` dispatches by extension. `_parse_pdf()` uses PyPDF2 then `_merge_pdf_lines()` to merge artificial line breaks back into natural paragraphs (detects sentence-ending punctuation). `split_text()` chunks by character count, preferring paragraph boundaries (`\n\n`) as cut points.
3. **Store** (`rag/vectorstore.py`): `ChromaVectorStore` wraps `langchain_chroma.Chroma`. Collections named `user_{user_id}` for isolation. `add_texts()` uses deterministic IDs for idempotent inserts. `similarity_search()` and `similarity_search_with_score()` (returns cosine distance) both support `where` filtering.
4. **Retrieve** (`rag/retriever.py`): `retrieve_relevant_chunks()` + `format_retrieved_context()` build the prompt context block.
5. **Generate** (`agents/edu_agent.py`): `edu_chat_stream()` async generator — retrieves context, builds prompt from last 3 rounds (6 messages), streams LLM output.

### Dual-agent system

- **edu_agent** (`agents/edu_agent.py`): tutoring with RAG — retrieves from user docs before answering
- **baoyan_agent** (`agents/baoyan_agent.py`): grad school advising — general LLM conversation, no RAG

Both expose async generator streaming. Invoked from `api/chat.py` (HTTP + WebSocket).

### Tools API (`backend/app/api/tools.py`)

`POST /api/tools/summarize` — document summary (short/medium/long). Falls back to local extraction if LLM unavailable.

`POST /api/tools/extract-knowledge` — structured knowledge extraction:
- Sends 12K chars to LLM with a detailed prompt asking for `{category, title, description, key_points, examples, source_excerpt}` JSON
- Falls back to `_fallback_knowledge_points()` (rule-based from sentence splitting) if LLM fails
- After extraction: searches ChromaDB per-point with `similarity_search_with_score`, filters by distance < 1.0 and document_id, deduplicates globally, extracts focused excerpts from chunks via `_focused_excerpt()` (keyword-overlap scoring on sentence units)
- `_normalize_knowledge_point()` ensures backward compatibility with older JSON formats

### WebSocket streaming protocol

Chat at `/ws/chat/{user_id}` with JSON messages:

| `data.type` | Purpose |
|-------------|---------|
| `thinking` | Agent reasoning step (tool_name + elapsed_ms) |
| `token` | Streaming response token |
| `done` | Response complete (includes sources + agent_steps) |
| `error` | Error occurred |
| `meta` | Conversation ID, initial metadata |

Frontend `ChatWebSocket` class (auto-reconnect: 5 attempts, exponential backoff). HTTP POST `/api/chat/ask` as fallback.

### Auth flow

JWT: `bcrypt` (direct, no passlib) + `python-jose`. Frontend axios interceptor attaches token and redirects to `/login` on 401. Pinia `auth` store manages login/register/logout.

### Database

SQLite via SQLAlchemy 2.0, auto-created on startup. Four models:

| Model | Notable columns |
|-------|----------------|
| User | username, hashed_password |
| Conversation | user_id, title, agent_type |
| Message | conversation_id, role, content, sources (JSON), **agent_steps** (JSON), **evaluation** (JSON) |
| Document | user_id, filename, original_name, file_type, chunk_count, status |

### Key design decisions (do not change without reason)

- **Python 3.11 required** — enforced by `start.sh` / `start.bat`
- **Local embedding model** — `BAAI/bge-small-zh-v1.5`, shared instance for upload + query, no API key needed
- **User data isolation**: per-user ChromaDB collections (`user_{user_id}`), per-user document records
- **Upload auto-vectorization**: no separate "process" step — file upload triggers immediate text extraction + chunking + vector store
- **Conversation window**: last 3 rounds (6 messages) in LLM context (`conversation_history[-6:]`)
- **Agent steps persistence**: thinking steps saved as JSON in `messages.agent_steps`, rendered as collapsible panel inside assistant message bubbles — survives page refresh and history reload
- **Smart scroll**: during streaming, only auto-scroll when user is within 50px of bottom; user scrolls up → no auto-scroll
- **LLM fallback everywhere**: `tools.py`, `edu_agent.py` all degrade gracefully when LLM is unavailable
- **CORS**: `localhost:5173` and `localhost:3000`
- **Config**: all settings via `pydantic-settings` from `.env` — see `backend/app/core/config.py`

### Frontend structure

Single-page app in `frontend/src/`:
- `views/ChatView.vue` — main chat view (sidebar + message area + knowledge drawer + input). Contains all scroll logic, WebSocket wiring, file upload, summary/knowledge extraction UI, and markdown export
- `views/LoginView.vue` — login/register forms
- `stores/auth.js` — Pinia auth store
- `stores/chat.js` — Pinia chat store (messages, thinking state)
- `utils/api.js` — axios instance with JWT interceptor
- `utils/websocket.js` — `ChatWebSocket` class
- `utils/markdown.js` — markdown-it renderer with highlight.js
