from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.document import Document
from backend.models.user import User
from backend.schemas.document import DocumentOut

router = APIRouter()


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[DocumentOut]:
    docs = db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())).all()
    return [DocumentOut.model_validate(doc) for doc in docs]


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> FileResponse:
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(document.storage_path, filename=document.file_name, media_type=document.content_type)

