from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    file_name: str
    content_type: str
    status: str
    error: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    documents: list[DocumentOut]

