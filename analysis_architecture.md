# AI Document Analyzer — Architecture Analysis & Improvement Map

## Current State Summary

The project is a **local-first RAG (Retrieval-Augmented Generation)** system built with FastAPI + PostgreSQL. It is a solid MVP but several flows have production gaps that need improvement before scaling.

---

## Architecture Diagram

> **Legend:**  
> 🟢 = Solid / Production-Ready  
> 🟡 = Acceptable for MVP, needs upgrade path  
> 🔴 = Needs immediate improvement (marked `⚠️`)

```mermaid
flowchart TD
    subgraph CLIENT["🖥️ Frontend (Static HTML/JS/CSS)"]
        UI_AUTH["Auth Form\n(Login / Register)"]
        UI_UPLOAD["File Upload"]
        UI_CHAT["Chat / Q&A"]
        UI_DOCS["Document List\n(polling every 2.5s ⚠️ POLL-1)"]
    end

    subgraph FASTAPI["⚡ FastAPI Application (main.py)"]
        CORS["CORS Middleware\n(allow_origins=* ⚠️ SEC-1)"]
        AUTH_EP["POST /auth/register\nPOST /auth/login"]
        UPLOAD_EP["POST /upload\nGET /upload/status/:id"]
        DOCS_EP["GET /documents\nGET /documents/:id/download"]
        SEARCH_EP["GET /search?q="]
        CHAT_EP["POST /chat/query\nGET /chat/history/:id"]
        HEALTH["GET /health"]
    end

    subgraph AUTH_MODULE["🔐 Auth Module"]
        HASH["PBKDF2-SHA256\nPassword Hashing 🟢"]
        TOKEN["Custom HMAC JWT\n(no library ⚠️ SEC-2)"]
        DEP["Bearer Token\nDependency 🟢"]
    end

    subgraph PROCESSING["📄 Document Processing Pipeline"]
        BG_TASK["FastAPI BackgroundTask\n(blocks event loop ⚠️ PROC-1)"]
        EXTRACT["extractors.py\nPDF / DOCX / XLSX / CSV / Image"]
        IMAGE_OCR["Image OCR\n(pytesseract optional ⚠️ PROC-2)"]
        CHUNKER["chunker.py\nFixed-size word chunks\n(no semantic boundary ⚠️ RAG-1)"]
        EMBED["embeddings/local.py\nBlake2b hashing vector\n(not semantic ⚠️ RAG-2)"]
        PROC_SVC["document_processor.py"]
    end

    subgraph RAG_MODULE["🤖 RAG Module"]
        RETRIEVE["retriever.py\nLoads ALL chunks to RAM ⚠️ RAG-3"]
        QA["qa.py\nGroq LLM or extractive fallback"]
        GROQ["Groq API\n(llama-3.1-8b-instant)"]
    end

    subgraph STORAGE_LAYER["🗄️ Storage Layer"]
        PG[("PostgreSQL\nUsers / Documents / Chunks / Chat")]
        LOCAL_FS["Local Filesystem\ndata/uploads/{user_id}/"]
        EMBED_STORE["Chunks.embedding\nstored as JSON TEXT ⚠️ RAG-4"]
    end

    subgraph INFRA["🐳 Docker Compose Infrastructure"]
        REDIS["Redis 7\n(exists but unused in app ⚠️ INFRA-1)"]
        CHROMA["ChromaDB\n(exists but unused ⚠️ INFRA-1)"]
        MINIO["MinIO\n(exists but unused ⚠️ INFRA-1)"]
        CELERY_W["Celery Worker\n(wired but dead code ⚠️ INFRA-1)"]
    end

    subgraph TESTS["🧪 Testing"]
        TEST1["test_core.py\n(2 unit tests only ⚠️ TEST-1)"]
    end

    %% Client → API flows
    UI_AUTH -->|"POST register/login"| AUTH_EP
    UI_UPLOAD -->|"POST multipart/form-data"| UPLOAD_EP
    UI_CHAT -->|"POST JSON query"| CHAT_EP
    UI_DOCS -->|"GET poll"| DOCS_EP

    %% Auth flow
    AUTH_EP --> HASH
    AUTH_EP --> TOKEN
    UPLOAD_EP --> DEP
    DOCS_EP --> DEP
    SEARCH_EP --> DEP
    CHAT_EP --> DEP

    %% Upload + processing flow
    UPLOAD_EP -->|"save file"| LOCAL_FS
    UPLOAD_EP -->|"insert Document row status=queued"| PG
    UPLOAD_EP -->|"add_task()"| BG_TASK
    BG_TASK --> PROC_SVC
    PROC_SVC --> EXTRACT
    EXTRACT --> IMAGE_OCR
    EXTRACT --> CHUNKER
    CHUNKER --> EMBED
    EMBED -->|"json.dumps(vector) stored as TEXT"| EMBED_STORE
    PROC_SVC -->|"insert Chunks + update status"| PG

    %% RAG flow
    CHAT_EP --> QA
    SEARCH_EP --> RETRIEVE
    QA --> RETRIEVE
    RETRIEVE -->|"SELECT * FROM chunks WHERE user_id=?"| PG
    RETRIEVE -->|"cosine in Python loop"| EMBED
    QA --> GROQ
    QA -->|"fallback extractive"| CHAT_EP

    %% Storage
    PG --> EMBED_STORE
    LOCAL_FS -.->|"planned swap → MinIO"| MINIO
    EMBED_STORE -.->|"planned swap → ChromaDB"| CHROMA
    BG_TASK -.->|"planned swap → Celery"| CELERY_W
    CELERY_W -.-> REDIS

    %% Styling
    classDef warn fill:#ff6b6b,color:#fff,stroke:#cc0000,stroke-width:2px
    classDef ok fill:#51cf66,color:#fff,stroke:#2f9e44
    classDef neutral fill:#339af0,color:#fff,stroke:#1971c2
    classDef infra fill:#868e96,color:#fff,stroke:#495057

    class CORS,TOKEN,BG_TASK,IMAGE_OCR,CHUNKER,EMBED,RETRIEVE,EMBED_STORE,UI_DOCS warn
    class HASH,DEP,EXTRACT,QA ok
    class REDIS,CHROMA,MINIO,CELERY_W,TEST1 infra
```

---

## ⚠️ Improvement Areas (Prioritized)

### 🔴 CRITICAL — Security

| ID | Location | Issue | Fix |
|---|---|---|---|
| **SEC-1** | `main.py:18` | `allow_origins=["*"]` — open CORS in production | Restrict to known frontend origins via env var |
| **SEC-2** | `auth/security.py` | Hand-rolled JWT with `hmac` — missing `nbf`, no key rotation, no refresh token | Replace with `python-jose` or `PyJWT`, add refresh token flow |

---

### 🔴 HIGH — RAG Quality

| ID | Location | Issue | Fix |
|---|---|---|---|
| **RAG-1** | `rag/chunker.py` | Fixed-size word chunks with no sentence/paragraph boundary awareness — splits mid-sentence | Use sentence-aware splitter (e.g. `langchain_text_splitters.RecursiveCharacterTextSplitter`) |
| **RAG-2** | `embeddings/local.py` | Blake2b hash-bucketing is a **bag-of-words hash** — semantically unaware; `"bank" (finance)` = `"bank" (river)` | Swap to `sentence-transformers` (`all-MiniLM-L6-v2`) for real semantic search |
| **RAG-3** | `rag/retriever.py:13` | `SELECT * FROM chunks WHERE user_id=?` loads **all user chunks into RAM** then scores in Python — O(n) per query | Add `pgvector` extension + `vector` column type, use ANN SQL (`<=>`) or swap to ChromaDB (already in docker-compose) |
| **RAG-4** | `models/document.py:32` | Embeddings stored as `TEXT` JSON (no vector index) — unusable for SQL-native similarity | Use `pgvector` or move to ChromaDB |

---

### 🟡 MEDIUM — Processing & Workers

| ID | Location | Issue | Fix |
|---|---|---|---|
| **PROC-1** | `api/v1/upload.py:47` | `BackgroundTasks` runs in the **same process/thread pool** as the API — heavy PDF processing blocks other requests | Route task to Celery worker (already wired in `docker-compose.yml`) |
| **PROC-2** | `services/extractors.py:65` | Image OCR silently fails and returns placeholder text — user has no feedback | Check for `pytesseract` at startup; return clear error status on document |
| **INFRA-1** | `docker-compose.yml` | Redis, ChromaDB, MinIO, Celery worker are all **declared but never used** by the application code | Wire Celery for document processing; wire ChromaDB for vector storage; wire MinIO for file storage |

---

### 🟡 MEDIUM — Frontend

| ID | Location | Issue | Fix |
|---|---|---|---|
| **POLL-1** | `frontend/app.js:91` | `setInterval(loadDocuments, 2500)` — polls forever even when all documents are ready, wastes bandwidth | Stop polling once all docs hit `ready`/`failed`; or use WebSocket / Server-Sent Events |

---

### 🟡 MEDIUM — Testing

| ID | Location | Issue | Fix |
|---|---|---|---|
| **TEST-1** | `tests/test_core.py` | Only **2 unit tests**, no API integration tests, no auth tests, no upload/processing tests | Add pytest fixtures with `TestClient`, test all endpoints, mock Groq, test error states |

---

### 🟢 LOW — Observability (Missing Entirely)

| Area | What's Missing |
|---|---|
| **Logging** | No structured logging (`logging` / `structlog`) — only exception messages in `document.error` |
| **Metrics** | No Prometheus / OpenTelemetry hooks |
| **Tracing** | No request tracing IDs — hard to correlate upload → background task → chunk → query |

---

## Data Flow: Upload → Processing (Current vs. Ideal)

```mermaid
sequenceDiagram
    participant Browser
    participant FastAPI
    participant BackgroundTask as BackgroundTask ⚠️
    participant Celery as Celery Worker (unused ⚠️)
    participant Extractor
    participant Chunker
    participant Embedder as Embedder ⚠️ (hash-based)
    participant PostgreSQL

    Browser->>FastAPI: POST /upload (multipart)
    FastAPI->>PostgreSQL: INSERT document (status=queued)
    FastAPI->>BackgroundTask: add_task(process_document_task)
    Note over BackgroundTask: Runs in same process!<br/>Blocks API under load ⚠️

    BackgroundTask->>Extractor: extract_pages(path)
    Extractor->>Chunker: chunk_pages(pages)
    Note over Chunker: Fixed word-size, no sentence boundary ⚠️
    Chunker->>Embedder: embed_text(chunk)
    Note over Embedder: Blake2b hash vector, not semantic ⚠️
    Embedder->>PostgreSQL: INSERT chunk (embedding as JSON TEXT ⚠️)
    BackgroundTask->>PostgreSQL: UPDATE document status=ready

    Note over Celery: Already in docker-compose<br/>but never invoked ⚠️
```

---

## Data Flow: Query → Answer (Current vs. Ideal)

```mermaid
sequenceDiagram
    participant Browser
    participant FastAPI
    participant Retriever as Retriever ⚠️
    participant PostgreSQL
    participant Groq

    Browser->>FastAPI: POST /chat/query {question}
    FastAPI->>PostgreSQL: INSERT ChatMessage (user)
    FastAPI->>Retriever: retrieve(db, user_id, question)
    Retriever->>PostgreSQL: SELECT * chunks WHERE user_id=?
    Note over Retriever: ALL chunks loaded into RAM ⚠️<br/>cosine scored in Python loop ⚠️
    Retriever-->>FastAPI: top-k Sources
    FastAPI->>Groq: chat.completions (if key set)
    Groq-->>FastAPI: answer
    FastAPI->>PostgreSQL: INSERT ChatMessage (assistant)
    FastAPI-->>Browser: {answer, sources}
```

---

## Quick-Win Improvement Roadmap

```mermaid
gantt
    title Improvement Roadmap (suggested order)
    dateFormat  YYYY-MM-DD
    section Security
    Fix CORS origins (SEC-1)         :done, s1, 2026-05-19, 1d
    Replace hand-rolled JWT (SEC-2)  :s2, after s1, 2d
    section RAG Quality
    Swap hash embed → sentence-transformers (RAG-2) :r2, 2026-05-20, 3d
    Sentence-aware chunker (RAG-1)   :r1, after r2, 2d
    Add pgvector column + index (RAG-3, RAG-4) :r3, after r1, 2d
    section Workers
    Wire Celery for processing (PROC-1, INFRA-1) :w1, 2026-05-24, 3d
    section Testing
    Add API integration tests (TEST-1) :t1, 2026-05-26, 3d
    section Frontend
    Replace polling with SSE (POLL-1) :f1, 2026-05-27, 2d
    section Observability
    Add structlog + request IDs     :o1, 2026-05-28, 2d
```

