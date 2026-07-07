# Project Structure

OnboardAgent keeps source code, runtime data, and generated artifacts separate.

```text
edu-assistant/
├── backend/
│   ├── app/                  # FastAPI application source
│   ├── scripts/              # maintenance, seed, and evaluation scripts
│   ├── data/                 # local runtime data, ignored by git
│   │   ├── uploads/          # uploaded company training documents
│   │   └── chroma_db/        # ChromaDB vector index
│   └── edu_assistant.db      # local SQLite database, ignored by git
├── frontend/                 # Vue application source
├── artifacts/                # generated outputs, ignored by git
│   ├── evaluations/          # batch evaluation reports
│   └── presentations/        # generated slide decks and render images
└── docs/                     # project documentation
```

Notes:

- `backend/data/` is runtime state. It is recreated by app startup or scripts.
- `artifacts/` is for generated reports and presentation files, not product source.
- Avoid placing user uploads or generated slides at the repository root.
