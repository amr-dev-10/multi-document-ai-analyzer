import os

from celery import Celery

from backend.core.config import settings
from backend.db.session import SessionLocal
from backend.services.document_processor import process_document

celery_app = Celery("ai_document_analyzer", broker=settings.celery_broker_url, backend=settings.celery_result_backend)


@celery_app.task(name="process_document")
def process_document_job(document_id: int) -> None:
    print(f"CELERY TASK START {document_id}")
    db = SessionLocal()
    try:
        process_document(db, document_id)
    except Exception as e:
        print("TASK ERROR", e)
    finally:
        db.close()

