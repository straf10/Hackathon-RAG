# Project Specification — PageIndex RAG for 10-K Financial Documents

## 1. Project Overview

| Field | Detail |
|-------|--------|
| **Event** | Netcompany Hackathon Thessaloniki 2026 |
| **Challenge** | Challenge 2 — AI-Powered Knowledge Base |
| **Project Title** | PageIndex RAG for 10-K Financial Documents |
| **Team Location** | Thessaloniki, Greece |
| **Timeline** | March 6–20, 2026 |
| **Submission Due** | March 15, 2026 |
| **Pitch Date** | March 19, 2026 |

### 1.1 Problem Statement

Financial analysts spend hours manually searching through SEC 10-K filings — documents that routinely exceed 200 pages — to extract revenue figures, risk factors, segment breakdowns, and year-over-year comparisons. The information is buried across disparate sections, inconsistent formatting, and legal boilerplate.

### 1.2 Proposed Solution

A Retrieval-Augmented Generation (RAG) system that ingests 10-K annual reports from major public companies (NVIDIA, Alphabet/Google, Apple), indexes them at page-level granularity, and answers natural-language financial questions with **grounded, source-cited, explainable responses**.

The system goes beyond simple Q&A by providing:

- **Intelligent retrieval** — semantic search with metadata filtering by company and fiscal year.
- **Explainable responses** — every answer includes source citations (filename, page number, relevance score, text snippet).
- **Multi-step reasoning** — sub-question decomposition for comparative and analytical queries.
- **Feedback loop** — user feedback collection for continuous improvement signals.
- **Financial visualization** — automatic table and chart rendering for numerical data.

### 1.3 Target Data Corpus

| Company | Fiscal Year | Source | Format | File |
|---------|-------------|--------|--------|------|
| NVIDIA | 2024 | SEC EDGAR | PDF | `nvidia_2024.pdf` |
| NVIDIA | 2025 | SEC EDGAR | PDF | `nvidia_2025.pdf` |
| Alphabet (Google) | 2024 | SEC EDGAR | PDF | `google-2024.pdf` |
| Alphabet (Google) | 2025 | SEC EDGAR | PDF | `google_2025.pdf` |
| Apple | 2024 | SEC EDGAR | PDF | `apple_2024.pdf` |
| Apple | 2025 | SEC EDGAR | PDF | `apple_2025.pdf` |

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

| Service | Image / Build | Internal Port | Exposed Port | Purpose |
|---------|---------------|---------------|--------------|---------|
| `backend` | Build: `./backend` | 8000 | 8000 | FastAPI REST API + RAG engine |
| `frontend` | Build: `./frontend` | 8501 | 8501 | Streamlit chat UI |
| `chromadb` | `chromadb/chroma:latest` | 8000 | 8100 | Persistent vector storage |

All services communicate over an internal Docker network. The backend connects to ChromaDB via `CHROMA_HOST:CHROMA_PORT` environment variables. ChromaDB data persists in a named Docker volume (`chroma_data`).

### 3.2 Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Backend Framework | Python 3.12 + FastAPI | Async, high-performance, listed in challenge recommendations |
| RAG Framework | LlamaIndex | Purpose-built for document RAG; native PDF readers, chunking, SEC support |
| LLM | OpenAI `gpt-4o-mini` | Covered by hackathon API key; fast, cost-effective, strong reasoning |
| Embeddings | OpenAI `text-embedding-3-small` | Covered by hackathon API key; high-quality 1536-dim dense vectors |
| Vector Database | ChromaDB | Free, open-source, official Docker image, excellent Python SDK |
| PDF Parsing | PyMuPDF (`pymupdf`) | Free, fast, reliable extraction with page-level metadata |
| Frontend | Streamlit | Rapid prototyping; built-in chat, charts, tables, data display |
| Feedback Storage | SQLite | Zero-config, built into Python stdlib, no additional container needed |
| Containerization | Docker + Docker Compose | Mandatory per challenge rules |

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

| Requirement | Description | Status |
|-------------|-------------|--------|
| FR-ING-01 | Parse all PDFs recursively from the `data/` directory using PyMuPDFReader. | Done |
| FR-ING-02 | Split documents into chunks (1024 tokens, 200-token overlap) using `SentenceSplitter`. | Done |
| FR-ING-03 | Attach metadata to every chunk: `company`, `year`, `doc_type`, `source_file`. | Done |
| FR-ING-04 | Generate embeddings via OpenAI `text-embedding-3-small`. | Done |
| FR-ING-05 | Store embedded chunks in ChromaDB with full metadata. | Done |
| FR-ING-06 | Return ingestion status: documents processed count, chunks created count. | Done |
| FR-ING-07 | Skip corrupted PDFs gracefully without halting the pipeline. | Done |

### 4.2 RAG Query (`POST /query`)

| Requirement | Description | Status |
|-------------|-------------|--------|
| FR-QRY-01 | Accept a natural-language question string. | Done |
| FR-QRY-02 | Accept optional filters: list of companies, list of fiscal years. | Done |
| FR-QRY-03 | Perform semantic vector search against ChromaDB with metadata filtering. | Done |
| FR-QRY-04 | Use sub-question decomposition for comparative/multi-step queries. | Done |
| FR-QRY-05 | Synthesize a grounded answer using only retrieved context (no hallucination). | Done |
| FR-QRY-06 | Return structured response: answer text + list of source documents. | Done |
| FR-QRY-07 | Each source document includes: filename, page number, relevance score, text snippet. | Done |

### 4.3 User Feedback (`POST /feedback`)

| Requirement | Description | Status |
|-------------|-------------|--------|
| FR-FDB-01 | Accept feedback per query: `query_id`, `rating` (up/down), optional `comment`. | Done |
| FR-FDB-02 | Persist feedback to SQLite with timestamp. | **TODO** |
| FR-FDB-03 | Return confirmation with generated `feedback_id`. | Done |
| FR-FDB-04 | Provide aggregated stats endpoint: total queries, positive %, negative %. | **TODO** |

### 4.4 Frontend (Streamlit)

| Requirement | Description | Status |
|-------------|-------------|--------|
| FR-UI-01 | Chat interface with persistent message history via `st.session_state`. | Done |
| FR-UI-02 | Sidebar filters: multi-select for companies (NVIDIA, Google, Apple) and years (2024, 2025). | Done |
| FR-UI-03 | Source citation display: expandable section under each answer showing source documents. | Done |
| FR-UI-04 | Feedback buttons (thumbs up/down) on every assistant response. | Done |
| FR-UI-05 | Loading spinner during query processing. | Done |
| FR-UI-06 | (Bonus) Financial data visualization: tables or bar charts when the response contains numerical data. | Done |
| FR-UI-07 | (Bonus) Analytics dashboard: feedback statistics and recent feedback entries. | **TODO** |

---

## 5. Non-Functional Requirements

| ID | Category | Requirement | Status |
|----|----------|-------------|--------|
| NFR-01 | Deployment | Full system starts with `docker compose up --build`, no manual steps beyond `.env` creation. | Done |
| NFR-02 | Portability | Runs on any machine with Docker Desktop installed (Windows, macOS, Linux). | Done |
| NFR-03 | Resilience | Graceful degradation with MockLLM/MockEmbedding when no valid OpenAI key is configured. | Done |
| NFR-04 | Security | API keys never committed to version control; `.env` is in `.gitignore`. | Done |
| NFR-05 | Performance | Query response latency under 15 seconds for typical single-company questions. | Untested |
| NFR-06 | Data Integrity | ChromaDB data persisted via named Docker volume (`chroma_data`); survives container restarts. | Done |
| NFR-07 | Observability | Structured logging across all services for debugging and demo purposes. | Done |
| NFR-08 | CORS | Backend allows cross-origin requests from the Streamlit frontend container. | Done |

---

## 6. API Contract

### 6.1 Request/Response Schemas

**QueryRequest**

```json
{
  "question": "string (required)",
  "companies": ["string"] | null,
  "years": [integer] | null,
  "use_sub_questions": false
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

| Method | Path | Request Body | Response Body | Description |
|--------|------|-------------|---------------|-------------|
| GET | `/` | — | `{"message": "..."}` | Root health message |
| GET | `/health` | — | `{"status": "ok"}` | Health check |
| POST | `/query` | `QueryRequest` | `QueryResponse` | Execute RAG query with optional filters |
| POST | `/ingest` | — | `IngestResponse` | Trigger document ingestion pipeline |
| POST | `/feedback` | `FeedbackRequest` | `FeedbackResponse` | Submit user feedback on a response |

---

## 7. Deliverables

| # | Deliverable | Format | Due Date | Status |
|---|-------------|--------|----------|--------|
| D1 | Working Dockerized application | `docker-compose.yml` | March 15, 2026 | Done |
| D2 | Source code repository | Git (GitHub/GitLab) | March 15, 2026 | Done |
| D3 | README with setup instructions | `README.md` | March 15, 2026 | Done |
| D4 | Curated 10-K PDF dataset | `data/` directory | March 15, 2026 | Done |
| D5 | Live demo (3–4 example queries) | In-person pitch | March 19, 2026 | Pending |
| D6 | Pitch presentation | Slides + live demo | March 19, 2026 | Pending |

---

## 8. Scoring Criteria

| Criterion | Weight | What Judges Evaluate |
|-----------|--------|---------------------|
| **Innovation** | 25% | Novelty of approach; PageIndex granularity, sub-question decomposition, metadata-filtered RAG |
| **Technical Execution** | 25% | Code quality, architecture, Docker setup, end-to-end pipeline reliability |
| **Pitching** | 20% | Clarity of presentation, live demo quality, storytelling, problem-solution framing |
| **Potential Impact** | 15% | Real-world applicability for financial analysts, scalability to more filings/companies |
| **UX** | 15% | Chat interface usability, source citations, filtering, feedback mechanism, visual polish |

### 8.1 Pitch Strategy Alignment

| Scoring Area | Feature That Addresses It |
|--------------|--------------------------|
| Innovation (25%) | Page-level citation, sub-question decomposition, metadata-filtered RAG |
| Technical (25%) | Full Docker Compose stack, LlamaIndex pipeline, ChromaDB persistence |
| Pitching (20%) | Live comparative query demo ("Compare NVIDIA vs Google revenue 2024–2025") |
| Impact (15%) | Eliminates manual 10-K search; extensible to any SEC filing |
| UX (15%) | Streamlit chat UI, sidebar filters, expandable source citations, feedback buttons, auto-visualization |

---

## 9. Implementation Phases

### Phase 1: Docker + Skeleton — **Complete**

- [x] `docker-compose.yml` with 3 services (backend, frontend, chromadb)
- [x] `backend/Dockerfile` (python:3.12-slim, uvicorn CMD)
- [x] `frontend/Dockerfile` (python:3.12-slim, streamlit CMD)
- [x] `backend/requirements.txt` with all dependencies
- [x] `frontend/requirements.txt` (streamlit, requests)
- [x] `.gitignore`
- [x] Hello-world FastAPI backend (`/` and `/health` endpoints) → `backend/app/main.py`
- [x] Hello-world Streamlit frontend → `frontend/app.py`
- [x] Verified: `docker compose up --build` starts all services without errors

### Phase 2: Data Ingestion Pipeline — **Complete**

- [x] PDF loader service with PyMuPDFReader → `backend/app/services/pdf_parser.py`
- [x] Downloaded all 6 10-K PDFs from SEC EDGAR into `data/nvidia/`, `data/google/`, `data/apple/`
- [x] Environment settings via pydantic-settings → `backend/app/config.py`
- [x] Indexer service → `backend/app/services/indexer.py`
  - [x] Load PDFs via `pdf_parser.load_pdf_documents()`
  - [x] Chunking with `SentenceSplitter` (chunk_size=1024, overlap=200) — 625 docs → 796 chunks
  - [x] Metadata enrichment: company, year, doc_type, source_file
  - [x] Embedding generation via OpenAI `text-embedding-3-small` (MockEmbedding fallback)
  - [x] ChromaDB storage via HTTP client with retry logic

### Phase 3: RAG Engine + API — **Complete**

- [x] RAG engine → `backend/app/services/rag_engine.py`
  - [x] ChromaDB connection with HTTP client + EphemeralClient fallback
  - [x] Standard query engine: natural language → retrieve chunks → LLM synthesis
  - [x] Metadata filtering: company and year via FilterOperator.IN + FilterCondition.AND
  - [x] Sub-question decomposition via `SubQuestionQueryEngine`
  - [x] Structured response: answer + source_nodes (filename, page, score, snippet)
  - [x] MockLLM / MockEmbedding fallback when no valid API key
- [x] Pydantic schemas → `backend/app/models/schemas.py`
  - [x] QueryRequest, SourceDocument, QueryResponse, IngestResponse, FeedbackRequest, FeedbackResponse
- [x] API routers → `backend/app/routers/`
  - [x] `query.py`: POST `/query` with lazy RAGEngine initialization
  - [x] `ingest.py`: POST `/ingest` triggers indexer pipeline
  - [x] `feedback.py`: POST `/feedback` accepts and logs feedback
- [x] FastAPI main → `backend/app/main.py`
  - [x] Router registration, CORS middleware

### Phase 4: Streamlit UI — **Complete**

- [x] Chat interface with `st.session_state` for persistent history → `frontend/app.py`
- [x] `st.chat_message()` loop for message display
- [x] `st.chat_input()` → POST to `/query` → render response
- [x] Loading spinner during query processing
- [x] Sidebar filters: `st.multiselect` for companies and years
- [x] Sub-question decomposition toggle
- [x] Source citations: expandable section with filename, page, relevance score, snippet
- [x] Feedback buttons (thumbs up/down) on every assistant response → POST to `/feedback`
- [x] Financial data visualization: auto-detection of numerical tables → `st.table()` + `st.bar_chart()`
- [x] Backend health check button
- [x] Clear chat button

### Phase 5: Feedback Persistence — **In Progress**

- [ ] Create `backend/app/services/feedback.py`:
  - [ ] SQLite initialization: table `feedback` (id, query_id, query_text, response_text, rating, comment, timestamp)
  - [ ] `save_feedback()` → persist to database
  - [ ] `get_feedback_stats()` → aggregated stats (total, positive %, negative %)
  - [ ] `get_recent_feedback(limit)` → last N feedback entries
- [ ] Wire `routers/feedback.py` to use `services/feedback.py` instead of logging
- [ ] Add `GET /feedback/stats` endpoint
- [ ] Analytics dashboard in Streamlit sidebar

### Phase 6: Documentation + Submission — **In Progress**

- [x] README.md with setup instructions, architecture diagram, API docs, project structure
- [x] Combined specification document (this file)
- [ ] Pitch preparation:
  - [ ] 1-slide summary: problem → solution → impact
  - [ ] Live demo scenario (3–4 example queries showcasing reasoning)
  - [ ] Architecture slide

---

## 10. Project Structure

```
Hackathon-RAG/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entrypoint, CORS, router registration
│   │   ├── config.py               # Environment settings (pydantic-settings)
│   │   ├── routers/
│   │   │   ├── query.py            # POST /query — RAG queries with filters
│   │   │   ├── ingest.py           # POST /ingest — trigger ingestion pipeline
│   │   │   └── feedback.py         # POST /feedback — user feedback collection
│   │   ├── services/
│   │   │   ├── pdf_parser.py       # PyMuPDFReader PDF loading + token counting
│   │   │   ├── rag_engine.py       # LlamaIndex RAG pipeline + sub-question engine
│   │   │   ├── indexer.py          # Chunking + embedding + ChromaDB storage
│   │   │   └── feedback.py         # SQLite feedback persistence (Phase 5)
│   │   └── models/
│   │       └── schemas.py          # Pydantic request/response models
│   ├── requirements.txt
│   └── Dockerfile                  # python:3.12-slim
├── frontend/
│   ├── app.py                      # Streamlit chat UI with filters, citations, charts
│   ├── requirements.txt
│   └── Dockerfile                  # python:3.12-slim
├── data/
│   ├── nvidia/                     # NVIDIA 10-K FY2024, FY2025
│   │   ├── nvidia_2024.pdf
│   │   └── nvidia_2025.pdf
│   ├── google/                     # Alphabet 10-K FY2024, FY2025
│   │   ├── google-2024.pdf
│   │   └── google_2025.pdf
│   └── apple/                      # Apple 10-K FY2024, FY2025
│       ├── apple_2024.pdf
│       └── apple_2025.pdf
├── docker-compose.yml              # 3 services: backend, frontend, chromadb
├── .env                            # OPENAI_API_KEY (gitignored, create locally)
├── .gitignore
├── README.md
└── Project_Specification.md        # This file
```

---

## 11. Key Dates

| Date | Milestone |
|------|-----------|
| March 6, 2026 | Hackathon kick-off |
| March 6–8 | Phase 1–2: Docker skeleton + data ingestion pipeline |
| March 9–12 | Phase 3–4: RAG engine, API, Streamlit UI |
| March 13–14 | Phase 5–6: Feedback persistence, polish, documentation |
| **March 15, 2026** | **Submission deadline** |
| March 16–18 | Pitch preparation + demo rehearsal |
| **March 19, 2026** | **Pitch day** |
| March 20, 2026 | Results / awards |

---

## 12. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OpenAI API key quota exhausted | Medium | High | MockLLM/MockEmbedding fallback; use `gpt-4o-mini` (low cost) |
| Large PDF parsing failures | Low | Medium | Graceful skip per file; structured logging for debugging |
| ChromaDB container instability | Low | High | Named volume for persistence; EphemeralClient fallback in code |
| Query latency exceeds acceptable threshold | Medium | Medium | Limit chunk retrieval top-k; use smaller embedding model |
| Docker build fails on pitch day | Low | Critical | Pre-build and test images day before; push images to registry |
