import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.embeddings.local import cosine, embed_text
from backend.models.document import Chunk, Document
from backend.schemas.chat import Source


def retrieve(db: Session, user_id: int, question: str, top_k: int = 5) -> list[Source]:
    query_embedding = embed_text(question)
    chunks = db.scalars(select(Chunk).where(Chunk.user_id == user_id)).all()
    scored = []
    doc_cache: dict[int, Document] = {}
    for chunk in chunks:
        score = cosine(query_embedding, json.loads(chunk.embedding))
        if score <= 0:
            continue
        if chunk.document_id not in doc_cache:
            doc_cache[chunk.document_id] = db.get(Document, chunk.document_id)
        doc = doc_cache[chunk.document_id]
        if not doc:
            continue
        scored.append(
            Source(
                document_id=doc.id,
                document_name=doc.file_name,
                page=chunk.page_number,
                chunk_id=chunk.id,
                score=round(float(score), 4),
                text=chunk.chunk_text,
            )
        )
    return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]

