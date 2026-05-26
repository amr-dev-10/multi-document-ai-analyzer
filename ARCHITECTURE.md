# Architecture

This project implements the uploaded HLD as a local-first MVP with production-ready boundaries.

## Modules

```text
backend/
  api/v1/          HTTP routes for auth, upload, documents, search, chat
  auth/            password hashing and bearer token handling
  core/            configuration
  db/              SQLAlchemy session and metadata
  models/          user, document, chunk, chat tables
  schemas/         request/response contracts
  services/        document processing and extraction
  rag/             chunking, retrieval, answer orchestration
  embeddings/      local deterministic embedding implementation
  storage/         local upload storage
  workers/         Celery entrypoint for queue-based processing
frontend/          local static UI served by FastAPI
```

## Local Runtime Flow

1. User registers or logs in.
2. User uploads one or more files.
3. FastAPI saves original files under `data/uploads/{user_id}`.
4. A background task extracts text, chunks content, creates local embeddings, and stores chunks in PostgreSQL.
5. User asks a question.
6. Retriever embeds the question, runs cosine similarity against owned chunks, and returns top citations.
7. If `GROQ_API_KEY` is set, Groq generates an answer from retrieved context. Otherwise, the API returns an extractive answer from the top cited chunks.

## Production Upgrade Points

| Current Local Component | Production Swap |
|---|---|
| PostgreSQL via local Docker | Managed PostgreSQL |
| FastAPI BackgroundTasks | Celery workers |
| Local file storage | MinIO or S3 |
| Local hashing embeddings | OpenAI `text-embedding-3-large` |
| PostgreSQL chunk vectors | ChromaDB collection |
| Static frontend | Next.js + Tailwind CSS |
| Simple HMAC bearer token | JWT library with refresh tokens |

The `docker-compose.yml` already includes Redis, Postgres, Chroma, and MinIO so these swaps can be made incrementally.
