from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Document Analyzer"
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://analyzer:analyzer@localhost:5432/analyzer?sslmode=disable"
    storage_dir: str = "./data/uploads"
    vector_dim: int = 256
    secret_key: str = "change-me-in-development"
    access_token_expire_minutes: int = 1440
    max_upload_mb: int = 50
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
