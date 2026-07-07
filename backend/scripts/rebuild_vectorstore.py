#!/usr/bin/env python3
"""
Rebuild ChromaDB vectors from uploaded ready documents.

Use this after changing the local embedding model, because Chroma collections
keep their original vector dimensionality.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.user import User
from app.rag.loader import parse_file, split_text
from app.rag.vectorstore import delete_user_collection, get_vectorstore


def rebuild_user_documents(user_id: int | None = None) -> None:
    db = SessionLocal()
    try:
        query = db.query(Document).filter(Document.status == "ready")
        if user_id is not None:
            query = query.filter(Document.user_id == user_id)

        docs = query.order_by(Document.user_id.asc(), Document.id.asc()).all()
        if not docs:
            user_query = db.query(User.id)
            if user_id is not None:
                user_query = user_query.filter(User.id == user_id)
            user_ids = [row[0] for row in user_query.all()]
            for current_user_id in user_ids:
                delete_user_collection(current_user_id)
                print(f"Deleted stale collection for user {current_user_id}.")
            print("No ready documents found. Please upload documents again to rebuild vectors.")
            return

        user_ids = sorted({doc.user_id for doc in docs})
        for current_user_id in user_ids:
            print(f"Rebuilding collection for user {current_user_id}...")
            delete_user_collection(current_user_id)
            vectorstore = get_vectorstore(user_id=current_user_id)

            user_docs = [doc for doc in docs if doc.user_id == current_user_id]
            for doc in user_docs:
                file_path = Path(settings.UPLOAD_DIR) / doc.filename
                if not file_path.exists():
                    doc.status = "error"
                    doc.error_message = f"Uploaded file not found: {file_path}"
                    print(f"  ! {doc.original_name}: missing file")
                    continue

                try:
                    text = parse_file(str(file_path), f".{doc.file_type}")
                    chunks = split_text(text)
                    if not chunks:
                        raise ValueError("No text chunks generated")

                    vectorstore.add_texts(
                        texts=chunks,
                        metadatas=[
                            {
                                "document_id": str(doc.id),
                                "document_name": doc.original_name,
                                "chunk_index": i,
                                "file_type": doc.file_type,
                                "source_type": "enterprise_upload",
                                "trust_level": "medium",
                            }
                            for i in range(len(chunks))
                        ],
                    )

                    doc.chunk_count = len(chunks)
                    doc.status = "ready"
                    doc.error_message = None
                    print(f"  ✓ {doc.original_name}: {len(chunks)} chunks")
                except Exception as exc:
                    doc.status = "error"
                    doc.error_message = str(exc)
                    print(f"  ! {doc.original_name}: {exc}")

        db.commit()
        print("Vectorstore rebuild complete.")
    finally:
        db.close()


def main() -> None:
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rebuild_user_documents(user_id=user_id)


if __name__ == "__main__":
    main()
