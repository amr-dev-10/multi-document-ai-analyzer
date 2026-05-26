from groq import Groq
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.rag.retriever import retrieve
from backend.schemas.chat import Source


def answer_question(db: Session, user_id: int, question: str, top_k: int = 5) -> tuple[str, list[Source]]:
    sources = retrieve(db, user_id, question, top_k=top_k)
    if not sources:
        return "I could not find relevant content in your uploaded documents yet. Upload a document and wait until it is marked ready.", []
    if settings.groq_api_key:
        try:
            return _groq_answer(question, sources), sources
        except Exception:
            pass
    return _extractive_answer(question, sources), sources


def _groq_answer(question: str, sources: list[Source]) -> str:
    client = Groq(api_key=settings.groq_api_key)
    context = "\n\n".join(
        f"[{idx}] {source.document_name}, page {source.page or 'n/a'}, chunk {source.chunk_id}\n{source.text}"
        for idx, source in enumerate(sources, start=1)
    )
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {
                "role": "system",
                "content": "Answer only from the provided document context. Include concise citation markers like [1] when useful.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return response.choices[0].message.content or ""


def _extractive_answer(question: str, sources: list[Source]) -> str:
    lines = ["Based on the most relevant document sections:"]
    for idx, source in enumerate(sources[:3], start=1):
        snippet = source.text[:500].strip()
        if len(source.text) > 500:
            snippet += "..."
        page = f", page {source.page}" if source.page else ""
        lines.append(f"[{idx}] {snippet} ({source.document_name}{page})")
    return "\n\n".join(lines)
