# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

OnboardAgent is a RAG-based enterprise onboarding assistant that answers new-employee questions over uploaded company handbooks, policies, workflows, security rules, and role-training materials. It uses local BGE embeddings (BAAI/bge-small-zh-v1.5) with ChromaDB for vector search, and supports DeepSeek or SiliconFlow as the LLM backend with an offline demo fallback.

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

Requires Python 3.11+ (see `.python-version`). `start.py` auto-creates a venv, pip-installs backend dependencies, npm-installs frontend dependencies, copies `.env.example` → `.env` if missing, then starts backend (:8000) and frontend (:5173) concurrently. Ctrl+C stops both.

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

The embedding model (`BAAI/bge-small-zh-v1.5`) must be downloaded once before first run — the app runs in offline mode (`HF_HUB_OFFLINE=1`, `local_files_only=True`). The first `pip install` of `sentence-transformers` typically caches it; if missing, run once with internet to let HuggingFace cache the model.

Seed demo data: `cd backend && python scripts/seed_demo_knowledge.py`

### Utility scripts

```bash
# Rebuild all ChromaDB vectors after changing the embedding model
cd backend && python scripts/rebuild_vectorstore.py [--user-id <id>]

# Batch-evaluate RAG quality across 48 default questions (outputs to artifacts/evaluations/)
cd backend && python scripts/batch_eval_rag.py [--questions <path>]
```

### Frontend (Vue 3 + Vite + Naive UI + Pinia)

```bash
cd frontend
npm install
npm run dev          # Vite dev server on :5173, proxies /api → :8000, /ws → ws://:8000
npm run build        # production build → dist/
```

The frontend is plain JavaScript (no TypeScript). Two routes only: `/login` and `/` (ChatView, protected by auth guard). The frontend has no separate `components/` directory — views compose Naive UI components directly.

### No tests or linting configured

There are no test frameworks, linters, or formatters set up for either frontend or backend.

## Architecture

### LLM gateway (`backend/app/agents/llm.py`)

`get_llm()` is the single factory for all LLM access. It reads `LLM_PROVIDER` from `.env` and returns one of:
- **ChatOpenAIGateway** wrapping `langchain_openai.ChatOpenAI` — used when a real API key is configured for DeepSeek or SiliconFlow (both speak OpenAI-compatible API). Provider is selected by `LLM_PROVIDER` (`deepseek` | `siliconflow` | `zhipu`), gated on whether the corresponding API key passes `_is_real_key()`.
- **LocalDemoLLM** — offline fallback that returns deterministic, rule-based responses for summaries, knowledge extraction, and Q&A. Activated automatically when no valid API key is present. This ensures the full upload → RAG → chat flow works without internet.

All agents and tools call `get_llm()` — never instantiate an LLM directly.

### Embedding model (`backend/app/rag/embeddings.py`)

`get_embeddings()` is an `@lru_cache` singleton returning a `HuggingFaceEmbeddings` instance for `BAAI/bge-small-zh-v1.5`. It runs in strict offline mode (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `local_files_only=True`) — the model must be cached locally before first use. Embeddings are normalized. `preload_embeddings()` is called at startup so the model is warm before any request arrives.

### RAG pipeline (upload → parse → store → retrieve → generate → evaluate)

1. **Upload** (`api/files.py`): file is saved to `backend/data/uploads/`, then immediately parsed and chunked.
2. **Parse** (`rag/loader.py`): `parse_file()` handles PDF (PyPDF2 with pdfplumber fallback), Word (python-docx), TXT, Markdown. PDF parsing includes `_merge_pdf_lines()` to reconstruct paragraphs from individual text lines. `split_text()` chunks by character count with overlap, preferring paragraph/sentence boundaries.
3. **Store** (`rag/vectorstore.py`): `ChromaVectorStore` stores embeddings in ChromaDB under `backend/data/chroma_db/`, with per-user collections named `user_{user_id}`. Chunks get deterministic IDs (`user_{user_id}_{document_id}_{chunk_index}`) so re-vectorizing the same file is idempotent.
4. **Retrieve** (`rag/retriever.py`): `retrieve_relevant_chunks()` queries with per-user filtering and optional document-ID scoping. Each retrieved chunk is enriched with `evidence_id` (e.g., `doc42_chunk3`), `retrieval_rank`, `retrieval_score`, and Chinese-labeled `source_type` / `trust_level`. `format_retrieved_context()` builds the LLM prompt context block with citation markers (`[来源N | docX_chunkY]`).
5. **Generate** (`agents/edu_agent.py`): `edu_chat_stream()` is an async generator that retrieves context, builds a prompt with the last 3 conversation rounds (6 messages), and streams LLM output token-by-token.
6. **Evaluate** (`rag/evaluation.py`): `evaluate_rag_answer()` computes online heuristic metrics after each answer — retrieval quality (mean relevance, query coverage, document diversity, source trust), groundedness (citation coverage/validity, context overlap, source utilization), and hallucination risk. Results are stored in the `evaluation` JSON column on the assistant `Message` and surfaced in the frontend.

### Evidence metadata on retrieved chunks

Every chunk returned by the retriever carries enriched metadata:

| Field | Source | Example |
|-------|--------|---------|
| `evidence_id` | Computed from doc ID + chunk index | `doc42_chunk3` |
| `retrieval_rank` | 1-based position in results | `1` |
| `retrieval_score` | Chroma cosine distance (lower = better) | `0.3421` |
| `source_type` | Document category label (Chinese) | `公司制度` |
| `trust_level` | Confidence tier | `high` / `medium` / `low` |

The LLM is instructed to cite `[来源N]` markers in its answers, and the evaluation module checks whether those citations reference valid source numbers.

### AI Memory system (`backend/app/services/user_memory.py`, `api/memory.py`)

Rule-based heuristic memory that tracks user behavior across conversations without storing raw chat content:

- **Tracking**: infers topics (入职流程, 考勤休假, 报销差旅, 信息安全, 人事制度, 岗位培训), answer style preferences (结构化/简洁/详细/步骤化/表格化), and communication tone (专业清晰/直接高效/耐心详细/结构清晰) from the user's question text via keyword rules.
- **Document usage**: records which documents the user most frequently queries against.
- **Prompt injection**: `build_memory_context()` generates a summary block (department, role, frequent topics, style/tone preferences,常用资料) that is injected into the LLM system prompt.
- **API**: `GET/PATCH/DELETE /api/memory/me` — users can view their memory profile, update preferences (style, tone, enable/disable), or clear all memory.
- **Storage**: `UserMemory` model — one row per user with JSON columns for counters. Memory is updated after every chat turn via `record_memory_interaction()`.

### Default document auto-seeding (`backend/app/services/default_documents.py`)

`ensure_default_onboarding_document()` is called during user registration to seed a default onboarding PDF (欣旺达-劳动人事管理全流程手册.pdf) for new users. It searches the uploads directory, existing user documents, and the Desktop for the file. The function is idempotent — users who already have the document are skipped. Failures do not block registration.

### Tools API (`api/tools.py`)

Two LLM-powered document analysis endpoints:
- `POST /api/tools/summarize` — generates a Chinese document summary (制度速览) with length options (short/medium/long).
- `POST /api/tools/extract-knowledge` — extracts structured knowledge cards (category, title, description, key_points, examples) from a document.

Both work with the LocalDemoLLM fallback.

### Database migration

`init_db()` in `core/database.py` calls `_ensure_sqlite_column()` to add `agent_steps`, `evaluation`, and `memory_enabled` columns to the `messages` table if they don't exist — this is a lightweight migration for SQLite-only schemas that predate these columns.

### WebSocket streaming protocol

Chat uses WebSocket at `/ws/chat/{user_id}` with JSON messages. The `ChatWebSocket` class (`frontend/src/utils/websocket.js`) handles connection, auto-reconnect (up to 5 attempts, exponential backoff), and dispatching by message type:

| `data.type` | Purpose |
|-------------|---------|
| `thinking` | Agent reasoning/planning visualization |
| `token` | Streaming response token (appended to message) |
| `done` | Response complete — carries `sources` (cited chunks) and `evaluation` (quality metrics) |
| `error` | Error occurred |
| `meta` | Metadata (conversation ID, etc.) |

The frontend falls back to HTTP POST `/api/chat/ask` if WebSocket fails.

### Auth flow

JWT-based: `backend/app/core/security.py` uses bcrypt + python-jose. The frontend axios instance (`utils/api.js`) attaches the token via interceptor and redirects to `/login` on 401. The Pinia `auth` store manages login/register/logout state. All protected API endpoints use the `get_current_user` dependency (pattern: copy from `api/auth.py`).

### Key design decisions (do not change without reason)

- **User data isolation**: ChromaDB collections are per-user (`user_{user_id}`). Document queries are scoped to the authenticated user.
- **Upload auto-vectorization**: file upload triggers immediate text extraction + chunking + storage — no separate "process" step.
- **Conversation window**: last 3 rounds (6 messages) included in LLM context (`conversation_history[-6:]`).
- **CORS**: only `localhost:5173` and `localhost:3000` allowed.
- **Config**: all settings via `pydantic-settings` from `.env` — see `backend/app/core/config.py`. Key tunables: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=200`, `RETRIEVAL_TOP_K=4`, `MAX_UPLOAD_SIZE_MB=20`, `ALLOWED_EXTENSIONS={.pdf,.docx,.txt,.md}`.
- **Offline embeddings**: embedding model runs with `local_files_only=True` — no network calls during inference. The model must be pre-cached.
- **Deterministic chunk IDs**: ChromaDB document IDs embed user, document, and chunk index — re-uploading the same file overwrites rather than duplicates vectors.
- **Document existence check**: retriever verifies that the original uploaded file still exists on disk before including its vectors in search results, preventing stale vectors from deleted files from polluting results.

### Database

SQLite via SQLAlchemy 2.0. Tables are auto-created on startup via `Base.metadata.create_all()` in `core/database.py`, plus lightweight column migrations. Five models: User, Conversation, Message, Document, UserMemory. Database file: `backend/edu_assistant.db`.

### Frontend state management

Two Pinia stores: `auth.js` (login/register/logout/token — fully used) and `chat.js` (conversations/messages — exists but `ChatView.vue` manages most chat state inline with `ref()`; the store is an incomplete abstraction). `ChatView.vue` is a ~1100-line monolithic component handling: conversation sidebar, message list with streaming, file management drawer, AI memory settings drawer, profile editing, and RAG evaluation display.
