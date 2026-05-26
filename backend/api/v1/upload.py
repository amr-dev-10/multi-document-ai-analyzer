from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.core.config import settings
from backend.db.session import SessionLocal, get_db
from backend.models.document import Document
from backend.models.user import User
from backend.schemas.document import DocumentOut, UploadResponse
from backend.services.document_processor import process_document
from backend.storage.local import save_upload
from backend.workers.celery_app import process_document_job

router = APIRouter()

@router.post("", response_model=UploadResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UploadResponse:
    print("START READ")

    created: list[Document] = []
    for file in files:
        content = await file.read()
        print("READ COMPLETE")
        if len(content) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"{file.filename} is too large")
        path = save_upload(user.id, file.filename or "upload.bin", content)
        print("FILE SAVED")
        document = Document(
            user_id=user.id,
            file_name=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            storage_path=str(path),
            status="queued",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        process_document_job.delay(document.id)
        print("TASK QUEUED")
        created.append(document)
    return UploadResponse(documents=[DocumentOut.model_validate(doc) for doc in created])


@router.get("/status/{document_id}", response_model=DocumentOut)
def upload_status(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentOut:
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(document)

