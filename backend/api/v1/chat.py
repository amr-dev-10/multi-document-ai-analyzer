import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.chat import ChatMessage, ChatSession
from backend.models.user import User
from backend.rag.qa import answer_question
from backend.schemas.chat import MessageOut, QueryRequest, QueryResponse, Source

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> QueryResponse:
    session = db.get(ChatSession, payload.session_id) if payload.session_id else None
    if session and session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if not session:
        session = ChatSession(user_id=user.id, title=payload.question[:80])
        db.add(session)
        db.commit()
        db.refresh(session)

    db.add(ChatMessage(session_id=session.id, user_id=user.id, role="user", message=payload.question))
    answer, sources = answer_question(db, user.id, payload.question, top_k=payload.top_k)
    db.add(
        ChatMessage(
            session_id=session.id,
            user_id=user.id,
            role="assistant",
            message=answer,
            sources_json=json.dumps([source.model_dump() for source in sources]),
        )
    )
    db.commit()
    return QueryResponse(session_id=session.id, answer=answer, sources=sources)


@router.get("/history/{session_id}", response_model=list[MessageOut])
def history(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[MessageOut]:
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = db.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)).all()
    output = []
    for message in messages:
        sources = [Source(**item) for item in json.loads(message.sources_json or "[]")]
        output.append(MessageOut(id=message.id, role=message.role, message=message.message, sources=sources, created_at=message.created_at))
    return output

