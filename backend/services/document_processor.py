import json
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.embeddings.local import embed_text
from backend.models.document import Chunk, Document
from backend.rag.chunker import chunk_pages
from backend.services.extractors import extract_pages


def process_document(db: Session, document_id: int) -> None:
    print("PROCESS")
    document = db.get(Document, document_id)
    if not document:
        return
    document.status = "processing"
    document.error = None
    db.commit()
    try:
        pages = extract_pages(document.storage_path, document.file_name, document.content_type)
        chunks = chunk_pages(pages)
        db.execute(delete(Chunk).where(Chunk.document_id == document.id))
        for item in chunks:
            db.add(
                Chunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    page_number=item.page,
                    chunk_index=item.index,
                    chunk_text=item.text,
                    embedding=json.dumps(embed_text(item.text)),
                    meta_json=json.dumps({"source": document.file_name, "page": item.page}),
                )
            )
        document.status = "ready" if chunks else "empty"
        document.processed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        document.status = "failed"
        document.error = str(exc)
        db.commit()

