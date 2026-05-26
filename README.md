# AI Multi-Document Analyzer

Runnable local MVP for the uploaded HLD. It supports:

- User registration/login with JWT-style bearer tokens
- Multi-file upload
- Background document processing
- PDF, DOCX, TXT, CSV, XLSX/XLS, PNG/JPG extraction with graceful optional dependencies
- Local semantic search using deterministic embeddings
- Chat-style Q&A with citations
- PostgreSQL persistence for local development
- Optional Groq answer generation when `GROQ_API_KEY` is set
- Docker Compose scaffolding for API, Redis, Postgres, Chroma, MinIO, and worker expansion

## Quick Start

Start PostgreSQL first. If you use PostgreSQL inside WSL Ubuntu, follow [WSL_POSTGRES_SETUP.md](WSL_POSTGRES_SETUP.md).

The included Compose file can also provide a ready local database if Docker is installed:

```powershell
docker compose up -d postgres
```

This creates:

- Database: `analyzer`
- User: `analyzer`
- Password: `analyzer`
- Port: `5432`

Then start the app:

```powershell
cd ai-document-analyzer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_dev.py
```

Open `http://127.0.0.1:8000`.

Uploaded files are stored in `./data`; application records are stored in PostgreSQL.

If Windows says `python` was not found, install Python 3.12+ from `https://www.python.org/downloads/` and check "Add python.exe to PATH" during installation.

## Optional Groq

The app works locally without an API key by returning extractive answers from retrieved chunks. To enable generated answers:

```powershell
$env:GROQ_API_KEY="your-groq-key"
```

or put it in `.env`.

The Groq integration uses the official `groq` Python module and defaults to `llama-3.1-8b-instant`. Change `GROQ_MODEL` in `.env` to another model available in your Groq account.

## API

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/upload`
- `GET /api/v1/upload/status/{document_id}`
- `GET /api/v1/documents`
- `POST /api/v1/chat/query`
- `GET /api/v1/chat/history/{session_id}`
- `GET /api/v1/search?q=...`
- `GET /api/v1/documents/{document_id}/download`

## Architecture

```text
frontend/static UI
        |
FastAPI API routers
        |
services: auth, upload, processing, RAG, chat
        |
parsers -> chunker -> embeddings -> vector repository
        |
PostgreSQL DB + local file storage
```

The package structure mirrors the HLD so local implementations can later be swapped for Celery, ChromaDB, MinIO, and managed embedding services.
