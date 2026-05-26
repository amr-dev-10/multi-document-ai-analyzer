import re
import uuid
from pathlib import Path

from backend.core.config import settings


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "upload.bin"


def save_upload(user_id: int, filename: str, content: bytes) -> Path:
    user_dir = settings.storage_path / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{uuid.uuid4().hex}_{safe_filename(filename)}"
    path.write_bytes(content)
    return path

