# Project Requirements — PageIndex RAG for 10-K Financial Documents

## 1. Project Overview

| Field              | Detail                                                                 |
|--------------------|------------------------------------------------------------------------|
| **Event**          | Netcompany Hackathon Thessaloniki 2026                                 |
| **Challenge**      | Challenge 2 — AI-Powered Knowledge Base                               |
| **Project Title**  | PageIndex RAG for 10-K Financial Documents                             |
| **Team Location**  | Thessaloniki, Greece                                                   |
| **Timeline**       | March 6–20, 2026                                                       |
| **Submission Due** | March 15, 2026                                                         |
| **Pitch Date**     | March 19, 2026                                                         |

### 1.1 Problem Statement

Financial analysts spend hours manually searching through SEC 10-K filings—documents that routinely exceed 200 pages—to extract revenue figures, risk factors, segment breakdowns, and year-over-year comparisons. The information is buried across disparate sections, inconsistent formatting, and legal boilerplate.

### 1.2 Proposed Solution

A Retrieval-Augmented Generation (RAG) system that ingests 10-K annual reports from major public companies (NVIDIA, Alphabet/Google, Apple), indexes them at page-level granularity, and answers natural-language financial questions with **grounded, source-cited, explainable responses**.

The system goes beyond simple Q&A by providing:

- **Intelligent retrieval** — semantic search with metadata filtering by company and fiscal year.
- **Explainable responses** — every answer includes source citations (filename, page number, relevance score, text snippet).
- **Multi-step reasoning** — sub-question decomposition for comparative and analytical queries.
- **Feedback loop** — user feedback collection for continuous improvement signals.

### 1.3 Target Data Corpus

| Company           | Fiscal Year | Source         | Format |
|-------------------|-------------|----------------|--------|
| NVIDIA            | 2024        | SEC EDGAR      | PDF    |
| NVIDIA            | 2025        | SEC EDGAR      | PDF    |
| Alphabet (Google) | 2024        | SEC EDGAR      | PDF    |
| Alphabet (Google) | 2025        | SEC EDGAR      | PDF    |
| Apple             | 2024        | SEC EDGAR      | PDF    |
| Apple             | 2025        | SEC EDGAR      | PDF    |

All documents are publicly available on SEC EDGAR and constitute curated, legally public data.

---

## 2. Technical Constraints (Netcompany-Mandated)

### 2.1 Containerization

- The entire application **must** be Dockerized.
- All services **must** run inside a Linux-based container environment.
- A single `docker compose up --build` command must bring the full system online.

### 2.2 Docker Images

- **Only official Docker Hub images** are permitted (per challenge rules, page 4).
- Base images used:
  - `python:3.12-slim` (official Python image) — backend and frontend containers.
  - `chromadb/chroma:latest` (official ChromaDB image) — vector database container.

### 2.3 External API Keys

- OpenAI API keys are provided by the hackathon organizers.
- Keys are stored in a `.env` file at the project root and are **never** committed to version control.
- The system must degrade gracefully (MockLLM / MockEmbedding fallback) when no valid API key is present.

### 2.4 No Paid Infrastructure

- All tools, frameworks, and databases must be free or open-source, with the sole exception of the organizer-provided OpenAI API credits.

---

## 3. Technical Architecture

### 3.1 Services (Docker Compose)

| Service      | Image / Build          | Internal Port | Exposed Port | Purpose                          |
|--------------|------------------------|---------------|--------------|----------------------------------|
| `backend`    | Build: `./backend`     | 8000          | 8000         | FastAPI REST API + RAG engine    |
| `frontend`   | Build: `./frontend`    | 8501          | 8501         | Streamlit chat UI                |
| `chromadb`   | `chromadb/chroma:latest` | 8000        | 8100         | Persistent vector storage        |

All services communicate over an internal Docker network. The backend connects to ChromaDB via `CHROMA_HOST:CHROMA_PORT` environment variables.

### 3.2 Tech Stack

| Layer              | Technology                          | Justification                                                        |
|--------------------|-------------------------------------|----------------------------------------------------------------------|
| Backend Framework  | Python 3.12 + FastAPI               | Async, high-performance, listed in challenge recommendations         |
| RAG Framework      | LlamaIndex                          | Purpose-built for document RAG; native PDF readers, chunking, SEC support |
| LLM                | OpenAI `gpt-4o-mini`                | Covered by hackathon API key; fast, cost-effective, strong reasoning  |
| Embeddings         | OpenAI `text-embedding-3-small`     | Covered by hackathon API key; high-quality dense vectors             |
| Vector Database    | ChromaDB                            | Free, open-source, official Docker image, excellent Python SDK       |
| PDF Parsing        | PyMuPDF (`pymupdf`)                 | Free, fast, reliable extraction with page-level metadata             |
| Frontend           | Streamlit                           | Rapid prototyping; built-in chat, charts, tables, data display       |
| Feedback Storage   | SQLite                              | Zero-config, built into Python stdlib, no additional container needed |
| Containerization   | Docker + Docker Compose             | Mandatory per challenge rules                                        |

### 3.3 Data Pipeline

```
10-K PDFs (data/)
    │
    ▼
PyMuPDFReader ── per-page Document extraction
    │
    ▼
SentenceSplitter ── chunk_size=1024, overlap=200
    │
    ▼
Metadata Enrichment ── company, year, doc_type, source_file
    │
    ▼
OpenAI text-embedding-3-small ── dense vector generation
    │
    ▼
ChromaDB ── persistent vector storage with metadata index
```

### 3.4 Query Pipeline

```
User Question + optional filters (company, year)
    │
    ▼
Metadata Filter Construction ── FilterOperator.IN + FilterCondition.AND
    │
    ▼
Semantic Retrieval ── top-k chunks from ChromaDB
    │
    ▼
Sub-Question Decomposition ── SubQuestionQueryEngine for multi-step reasoning
    │
    ▼
LLM Synthesis (gpt-4o-mini) ── grounded answer from retrieved context
    │
    ▼
Structured Response ── answer + source_nodes (filename, page, score, snippet)
```

---

## 4. Functional Requirements

### 4.1 Document Ingestion (`POST /ingest`)

| Requirement | Description |
|-------------|-------------|
| FR-ING-01   | Parse all PDFs recursively from the `data/` directory using PyMuPDFReader. |
| FR-ING-02   | Split documents into chunks (1024 tokens, 200-token overlap) using `SentenceSplitter`. |
| FR-ING-03   | Attach metadata to every chunk: `company`, `year`, `doc_type`, `source_file`. |
| FR-ING-04   | Generate embeddings via OpenAI `text-embedding-3-small`. |
| FR-ING-05   | Store embedded chunks in ChromaDB with full metadata. |
| FR-ING-06   | Return ingestion status: documents processed count, chunks created count. |
| FR-ING-07   | Skip corrupted PDFs gracefully without halting the pipeline. |

### 4.2 RAG Query (`POST /query`)

| Requirement | Description |
|-------------|-------------|
| FR-QRY-01   | Accept a natural-language question string. |
| FR-QRY-02   | Accept optional filters: list of companies, list of fiscal years. |
| FR-QRY-03   | Perform semantic vector search against ChromaDB with metadata filtering. |
| FR-QRY-04   | Use sub-question decomposition for comparative/multi-step queries. |
| FR-QRY-05   | Synthesize a grounded answer using only retrieved context (no hallucination). |
| FR-QRY-06   | Return structured response: answer text + list of source documents. |
| FR-QRY-07   | Each source document includes: filename, page number, relevance score, text snippet. |

### 4.3 User Feedback (`POST /feedback`)

| Requirement | Description |
|-------------|-------------|
| FR-FDB-01   | Accept feedback per query: `query_id`, `rating` (up/down), optional `comment`. |
| FR-FDB-02   | Persist feedback to SQLite with timestamp. |
| FR-FDB-03   | Return confirmation with generated `feedback_id`. |
| FR-FDB-04   | Provide aggregated stats endpoint: total queries, positive %, negative %. |

### 4.4 Frontend (Streamlit)

| Requirement | Description |
|-------------|-------------|
| FR-UI-01    | Chat interface with persistent message history via `st.session_state`. |
| FR-UI-02    | Sidebar filters: multi-select for companies (NVIDIA, Google, Apple) and years (2024, 2025). |
| FR-UI-03    | Source citation display: expandable section under each answer showing source documents. |
| FR-UI-04    | Feedback buttons (thumbs up/down) on every assistant response. |
| FR-UI-05    | Loading spinner during query processing. |
| FR-UI-06    | (Bonus) Financial data visualization: tables or bar charts when the response contains numerical data. |
| FR-UI-07    | (Bonus) Analytics dashboard: feedback statistics and recent feedback entries. |

---

## 5. Non-Functional Requirements

| ID        | Category       | Requirement                                                                                  |
|-----------|----------------|----------------------------------------------------------------------------------------------|
| NFR-01    | Deployment     | Full system starts with `docker compose up --build`, no manual steps beyond `.env` creation. |
| NFR-02    | Portability    | Runs on any machine with Docker Desktop installed (Windows, macOS, Linux).                   |
| NFR-03    | Resilience     | Graceful degradation with MockLLM/MockEmbedding when no valid OpenAI key is configured.      |
| NFR-04    | Security       | API keys never committed to version control; `.env` is in `.gitignore`.                      |
| NFR-05    | Performance    | Query response latency under 15 seconds for typical single-company questions.                |
| NFR-06    | Data Integrity | ChromaDB data persisted via named Docker volume (`chroma_data`); survives container restarts. |
| NFR-07    | Observability  | Structured logging across all services for debugging and demo purposes.                      |
| NFR-08    | CORS           | Backend allows cross-origin requests from the Streamlit frontend container.                  |

---

## 6. API Contract

### 6.1 Request/Response Schemas

**QueryRequest**
```json
{
  "question": "string (required)",
  "companies": ["string"] | null,
  "years": [integer] | null
}
```

**QueryResponse**
```json
{
  "answer": "string",
  "sources": [
    {
      "filename": "string",
      "page": integer,
      "score": float,
      "text_snippet": "string"
    }
  ]
}
```

**IngestResponse**
```json
{
  "status": "string",
  "documents_processed": integer,
  "chunks_created": integer
}
```

**FeedbackRequest**
```json
{
  "query_id": "string (required)",
  "rating": "up" | "down",
  "comment": "string" | null
}
```

**FeedbackResponse**
```json
{
  "status": "string",
  "feedback_id": "string (uuid)"
}
```

### 6.2 Endpoints

| Method | Path        | Request Body      | Response Body      | Description                            |
|--------|-------------|-------------------|--------------------|----------------------------------------|
| GET    | `/`         | —                 | `{"message": "..."}` | Root health message                  |
| GET    | `/health`   | —                 | `{"status": "ok"}`  | Health check                          |
| POST   | `/query`    | `QueryRequest`    | `QueryResponse`    | Execute RAG query with optional filters |
| POST   | `/ingest`   | —                 | `IngestResponse`   | Trigger document ingestion pipeline    |
| POST   | `/feedback` | `FeedbackRequest` | `FeedbackResponse` | Submit user feedback on a response     |

---

## 7. Deliverables

| #  | Deliverable                      | Format                | Due Date       |
|----|----------------------------------|-----------------------|----------------|
| D1 | Working Dockerized application   | `docker-compose.yml`  | March 15, 2026 |
| D2 | Source code repository           | Git (GitHub/GitLab)   | March 15, 2026 |
| D3 | README with setup instructions   | `README.md`           | March 15, 2026 |
| D4 | Curated 10-K PDF dataset         | `data/` directory     | March 15, 2026 |
| D5 | Live demo (3–4 example queries)  | In-person pitch       | March 19, 2026 |
| D6 | Pitch presentation               | Slides + live demo    | March 19, 2026 |

---

## 8. Scoring Criteria

| Criterion            | Weight | What Judges Evaluate                                                                 |
|----------------------|--------|--------------------------------------------------------------------------------------|
| **Innovation**       | 25%    | Novelty of approach; PageIndex granularity, sub-question decomposition, metadata-filtered RAG. |
| **Technical Execution** | 25% | Code quality, architecture, Docker setup, end-to-end pipeline reliability.           |
| **Pitching**         | 20%    | Clarity of presentation, live demo quality, storytelling, problem-solution framing.   |
| **Potential Impact** | 15%    | Real-world applicability for financial analysts, scalability to more filings/companies. |
| **UX**               | 15%    | Chat interface usability, source citations, filtering, feedback mechanism, visual polish. |

### 8.1 Pitch Strategy Alignment

| Scoring Area         | Feature That Addresses It                                                |
|----------------------|--------------------------------------------------------------------------|
| Innovation (25%)     | Page-level citation, sub-question decomposition, metadata-filtered RAG   |
| Technical (25%)      | Full Docker Compose stack, LlamaIndex pipeline, ChromaDB persistence     |
| Pitching (20%)       | Live comparative query demo ("Compare NVIDIA vs Google revenue 2024–2025") |
| Impact (15%)         | Eliminates manual 10-K search; extensible to any SEC filing              |
| UX (15%)             | Streamlit chat UI, sidebar filters, expandable source citations, feedback |

---

## 9. Project Structure

```
Hackathon-RAG/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entrypoint + CORS + router registration
│   │   ├── config.py               # Environment settings (pydantic-settings)
│   │   ├── routers/
│   │   │   ├── query.py            # POST /query
│   │   │   ├── ingest.py           # POST /ingest
│   │   │   └── feedback.py         # POST /feedback
│   │   ├── services/
│   │   │   ├── pdf_parser.py       # PyMuPDFReader PDF loading
│   │   │   ├── rag_engine.py       # LlamaIndex RAG pipeline + MockLLM fallback
│   │   │   ├── indexer.py          # Chunking + embedding + ChromaDB storage
│   │   │   └── feedback.py         # SQLite feedback persistence
│   │   └── models/
│   │       └── schemas.py          # Pydantic request/response models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                      # Streamlit chat UI
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── nvidia/                     # NVIDIA 10-K 2024, 2025
│   ├── google/                     # Alphabet 10-K 2024, 2025
│   └── apple/                      # Apple 10-K 2024, 2025
├── docker-compose.yml
├── .env                            # OPENAI_API_KEY (gitignored)
├── .gitignore
├── README.md
├── Plan.md
└── Project_Requirements.md
```

---

## 10. Key Dates

| Date             | Milestone                                      |
|------------------|-------------------------------------------------|
| March 6, 2026    | Hackathon kick-off                              |
| March 6–8        | Phase 1: Docker skeleton + data ingestion pipeline |
| March 9–12       | Phase 2–3: RAG engine, API, Streamlit UI        |
| March 13–14      | Phase 4–5: Feedback loop, polish, documentation |
| March 15, 2026   | **Submission deadline**                         |
| March 16–18      | Pitch preparation + demo rehearsal              |
| March 19, 2026   | **Pitch day**                                   |
| March 20, 2026   | Results / awards                                |

---

## 11. Risks and Mitigations

| Risk                                      | Likelihood | Impact | Mitigation                                                        |
|-------------------------------------------|------------|--------|-------------------------------------------------------------------|
| OpenAI API key quota exhausted            | Medium     | High   | MockLLM/MockEmbedding fallback; use `gpt-4o-mini` (low cost)     |
| Large PDF parsing failures                | Low        | Medium | Graceful skip per file; structured logging for debugging          |
| ChromaDB container instability            | Low        | High   | Named volume for persistence; EphemeralClient fallback in code    |
| Query latency exceeds acceptable threshold| Medium     | Medium | Limit chunk retrieval top-k; use smaller embedding model          |
| Docker build fails on pitch day           | Low        | Critical | Pre-build and test images day before; push images to registry    |
