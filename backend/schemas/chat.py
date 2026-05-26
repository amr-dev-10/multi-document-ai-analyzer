from datetime import datetime

from pydantic import BaseModel, Field


class Source(BaseModel):
    document_id: int
    document_name: str
    page: int | None = None
    chunk_id: int
    score: float
    text: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: int | None = None
    top_k: int = Field(default=5, ge=1, le=12)


class QueryResponse(BaseModel):
    session_id: int
    answer: str
    sources: list[Source]


class MessageOut(BaseModel):
    id: int
    role: str
    message: str
    sources: list[Source]
    created_at: datetime

