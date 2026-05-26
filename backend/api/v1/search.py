from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.rag.retriever import retrieve
from backend.schemas.chat import Source

router = APIRouter()


@router.get("", response_model=list[Source])
def search(
    q: str = Query(min_length=1),
    top_k: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Source]:
    return retrieve(db, user.id, q, top_k=top_k)

