Here is the project architecture in one view:

```mermaid
flowchart TD
    U["User Browser"] --> UI["Frontend Static UI<br/>frontend/index.html<br/>app.js, styles.css"]

    UI --> AUTH["Auth APIs<br/>POST /api/v1/auth/register<br/>POST /api/v1/auth/login"]
    UI --> UPLOAD["Upload APIs<br/>POST /api/v1/upload<br/>GET /api/v1/upload/status/{id}"]
    UI --> DOCS["Document APIs<br/>GET /api/v1/documents<br/>GET /api/v1/documents/{id}/download"]
    UI --> CHAT["Chat APIs<br/>POST /api/v1/chat/query<br/>GET /api/v1/chat/history/{session_id}"]
    UI --> SEARCH["Search API<br/>GET /api/v1/search?q=..."]

    AUTH --> AUTH_SERVICE["Auth Logic<br/>password hashing<br/>bearer token creation<br/>current user dependency"]
    AUTH_SERVICE --> DB["PostgreSQL<br/>users<br/>documents<br/>chunks<br/>chat_sessions<br/>messages"]

    UPLOAD --> STORAGE["Local File Storage<br/>data/uploads/{user_id}"]
    UPLOAD --> DOC_ROW["Create Document Row<br/>status = queued"]
    DOC_ROW --> DB
    UPLOAD --> BG["FastAPI Background Task"]

    BG --> PROCESSOR["Document Processor<br/>backend/services/document_processor.py"]
    PROCESSOR --> EXTRACT["Extractors<br/>PDF: PyMuPDF<br/>DOCX: python-docx<br/>Excel/CSV: pandas<br/>TXT: text read<br/>Image: OCR fallback"]
    EXTRACT --> CHUNKER["Chunker<br/>backend/rag/chunker.py<br/>splits text by words<br/>keeps page metadata"]
    CHUNKER --> EMBED["Local Embeddings<br/>backend/embeddings/local.py<br/>deterministic vector hashing"]
    EMBED --> CHUNKS["Store Chunks<br/>chunk_text<br/>embedding<br/>page number<br/>metadata"]
    CHUNKS --> DB
    PROCESSOR --> READY["Document status = ready/failed"]
    READY --> DB

    SEARCH --> RETRIEVER["Retriever<br/>backend/rag/retriever.py"]
    CHAT --> QA["Q&A Service<br/>backend/rag/qa.py"]

    QA --> RETRIEVER
    RETRIEVER --> QUERY_EMBED["Embed User Question"]
    QUERY_EMBED --> VECTOR_SEARCH["Cosine Similarity Search<br/>against user's chunks"]
    VECTOR_SEARCH --> DB
    DB --> SOURCES["Top Matching Sources<br/>document<br/>page<br/>chunk<br/>score<br/>text"]

    SOURCES --> QA
    QA --> GROQ_CHECK{"GROQ_API_KEY set?"}
    GROQ_CHECK -->|Yes| GROQ["Groq SDK<br/>GROQ_MODEL<br/>Generates answer from context"]
    GROQ_CHECK -->|No| EXTRACTIVE["Local Extractive Answer<br/>returns top snippets"]

    GROQ --> ANSWER["Answer + Citations"]
    EXTRACTIVE --> ANSWER
    ANSWER --> SAVE_CHAT["Save user + assistant messages"]
    SAVE_CHAT --> DB
    ANSWER --> UI
```

**Module Map**

```mermaid
flowchart LR
    MAIN["backend/main.py<br/>FastAPI app<br/>static frontend<br/>health route"] --> ROUTER["backend/api/v1/router.py"]

    ROUTER --> AUTH_API["auth.py"]
    ROUTER --> UPLOAD_API["upload.py"]
    ROUTER --> DOC_API["documents.py"]
    ROUTER --> SEARCH_API["search.py"]
    ROUTER --> CHAT_API["chat.py"]

    AUTH_API --> AUTH_MOD["backend/auth<br/>security.py<br/>dependencies.py"]
    UPLOAD_API --> STORAGE_MOD["backend/storage/local.py"]
    UPLOAD_API --> PROCESS_MOD["backend/services/document_processor.py"]
    PROCESS_MOD --> EXTRACT_MOD["backend/services/extractors.py"]
    PROCESS_MOD --> CHUNK_MOD["backend/rag/chunker.py"]
    PROCESS_MOD --> EMBED_MOD["backend/embeddings/local.py"]

    SEARCH_API --> RETRIEVER_MOD["backend/rag/retriever.py"]
    CHAT_API --> QA_MOD["backend/rag/qa.py"]
    QA_MOD --> GROQ_MOD["groq Python SDK"]

    AUTH_MOD --> MODELS["backend/models<br/>User<br/>Document<br/>Chunk<br/>ChatSession<br/>ChatMessage"]
    PROCESS_MOD --> MODELS
    RETRIEVER_MOD --> MODELS
    CHAT_API --> MODELS

    MODELS --> DB_SESSION["backend/db/session.py"]
    DB_SESSION --> POSTGRES["WSL PostgreSQL"]
```

**Request Flow**

1. **Register/Login**
   `frontend/app.js` calls `/api/v1/auth/register` or `/api/v1/auth/login`.
   Backend stores user in PostgreSQL and returns a bearer token.

2. **Upload Document**
   Browser sends files to `/api/v1/upload`.
   Backend saves original files in `data/uploads/{user_id}` and creates `documents` rows with `queued` status.

3. **Process Document**
   Background task extracts text, chunks it, creates embeddings, and stores chunks in PostgreSQL.

4. **Ask Question**
   Browser calls `/api/v1/chat/query`.
   Backend embeds the question, retrieves matching chunks, sends context to Groq if `GROQ_API_KEY` exists, and returns answer with citations.

5. **Fallback Mode**
   If no Groq key is configured, the app still works by returning extractive answers from the most relevant chunks.