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

A Retrieval-Augmented Generation (RAG) system that ingests 10-K annual reports from major public companies (NVIDIA, Alphabet/Google, Apple), indexes them at page-level granularity, and answers natural-language financial questions with grounded, source-cited, explainable responses. See [README — Key Features](README.md#key-features) for the full feature list.

### 1.3 Target Data Corpus

Six 10-K PDFs from SEC EDGAR (NVIDIA, Alphabet, Apple; FY 2024 and 2025). See [README — Data Corpus](README.md#data-corpus) for the file listing.

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
  - `chromadb/chroma:1.5.2` (official ChromaDB image) — vector database container (pinned for reproducibility).

### 2.3 External API Keys

- OpenAI API keys are provided by the hackathon organizers.
- Keys are stored in a `.env` file at the project root and are **never** committed to version control.
- The system must degrade gracefully (MockLLM / MockEmbedding fallback) when no valid API key is present.

### 2.4 No Paid Infrastructure

- All tools, frameworks, and databases must be free or open-source, with the sole exception of the organizer-provided OpenAI API credits.

---

## 3. Technical Architecture

For the architecture diagram, see [README — Architecture](README.md#architecture).

### 3.1 Services (Docker Compose)

| Service | Image / Build | Internal Port | Exposed Port | Purpose |
|---------|---------------|---------------|--------------|---------|
| `backend` | Build: `./backend` | 8000 | 8000 | FastAPI REST API + RAG engine |
| `frontend` | Build: `./frontend` | 8501 | 8501 | Streamlit chat UI |
| `chromadb` | `chromadb/chroma:1.5.2` | 8000 | 8100 | Persistent vector storage |

All services communicate over an internal Docker network. The backend connects to ChromaDB via `CHROMA_HOST:CHROMA_PORT` environment variables. ChromaDB data persists in a named Docker volume (`chroma_data`).

### 3.2 Tech Stack, Pipelines

See [README — Tech Stack](README.md#tech-stack) for the technology table. See [README — How It Works](README.md#how-it-works) for the ingestion and query pipeline diagrams.

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
| FR-FDB-02 | Persist feedback to SQLite with timestamp. | Done |
| FR-FDB-03 | Return confirmation with generated `feedback_id`. | Done |
| FR-FDB-04 | Provide aggregated stats endpoint: total queries, positive %, negative %. | Done |

### 4.4 Frontend (Streamlit)

| Requirement | Description | Status |
|-------------|-------------|--------|
| FR-UI-01 | Chat interface with persistent message history via `st.session_state`. | Done |
| FR-UI-02 | Sidebar filters: multi-select for companies (NVIDIA, Google, Apple) and years (2024, 2025). | Done |
| FR-UI-03 | Source citation display: expandable section under each answer showing source documents. | Done |
| FR-UI-04 | Feedback buttons (thumbs up/down) on every assistant response. | Done |
| FR-UI-05 | Loading spinner during query processing. | Done |
| FR-UI-06 | (Bonus) Financial data visualization: tables or bar charts when the response contains numerical data. | Done |
| FR-UI-07 | (Bonus) Analytics dashboard: feedback statistics and recent feedback entries. | Done |

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
| NFR-08 | CORS | Backend allows cross-origin requests only from known origins (localhost:8501, 127.0.0.1:8501, frontend:8501). | Done |
| NFR-09 | Input Validation | Query requests validated: question 1–2000 chars, companies/years max 10 items. | Done |
| NFR-10 | Budget Enforcement | Token budget ($10) enforced; HTTP 429 when exhausted. | Done |
| NFR-11 | Concurrency | Ingestion guarded by lock; feedback DB and token tracker use thread-safe singletons. | Done |

---

## 6. API Contract

### 6.1 Request/Response Schemas

**QueryRequest**

```json
{
  "question": "string (required, 1–2000 chars)",
  "companies": ["string"] | null,
  "years": [integer] | null,
  "use_sub_questions": false
}
```

- `question`: required, min 1 char, max 2000 chars.
- `companies`, `years`: optional, max 10 items each.

**QueryResponse**

```json
{
  "answer": "string",
  "sources": [
    {
      "filename": "string",
      "page": integer,
      "score": float,
      "text_snippet": "string",
      "source_type": "document" | "sub_question"
    }
  ],
  "query_id": "string (uuid)"
}
```

- `query_id`: server-generated UUID; use when submitting feedback via `POST /feedback`.

**IngestResponse**

```json
{
  "status": "string",
  "documents_processed": integer,
  "chunks_created": integer,
  "existing_chunks": integer
}
```

- `status`: `ok` (completed), `skipped` (already populated), or `already_running` (concurrent request rejected).

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
| GET | `/usage` | — | Token usage + budget | API token counts and estimated cost |
| POST | `/query` | `QueryRequest` | `QueryResponse` | Execute RAG query (429 if budget exhausted; 422 if validation fails) |
| POST | `/ingest` | `{"force": bool}` (optional) | `IngestResponse` | Trigger ingestion (returns `already_running` if concurrent) |
| POST | `/feedback` | `FeedbackRequest` | `FeedbackResponse` | Submit user feedback (use `query_id` from `/query` response) |
| GET | `/feedback/stats` | — | `FeedbackStatsResponse` | Aggregated feedback statistics |
| GET | `/feedback/recent` | `?limit=N` (1–100) | `FeedbackRecord[]` | Recent feedback entries |
| POST | `/shutdown` | — | `{"status": "ok"}` | Persist data before stopping containers |

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
  - [x] ChromaDB storage via HTTP client with retry logic; concurrency lock prevents duplicate ingestion

### Phase 3: RAG Engine + API — **Complete**

- [x] RAG engine → `backend/app/services/rag_engine.py`
  - [x] ChromaDB connection with HTTP client + retry logic (5 attempts); raises `ConnectionError` on failure (no silent ephemeral fallback)
  - [x] Standard query engine: natural language → retrieve chunks → LLM synthesis
  - [x] Metadata filtering: company and year via FilterOperator.IN + FilterCondition.AND
  - [x] Sub-question decomposition via `SubQuestionQueryEngine`
  - [x] Structured response: answer + source_nodes (filename, page, score, snippet)
  - [x] MockLLM / MockEmbedding fallback when no valid API key
- [x] Pydantic schemas → `backend/app/models/schemas.py`
  - [x] QueryRequest (question 1–2000 chars, companies/years max 10), SourceDocument, QueryResponse (includes `query_id`), IngestResponse, FeedbackRequest, FeedbackResponse
- [x] API routers → `backend/app/routers/`
  - [x] `query.py`: POST `/query` with lazy RAGEngine init, `asyncio.to_thread` for blocking RAG, budget enforcement, server-side `query_id`
  - [x] `ingest.py`: POST `/ingest` triggers indexer pipeline (concurrency lock; returns `already_running` if concurrent)
  - [x] `feedback.py`: POST `/feedback` accepts and logs feedback (sync def for threadpool execution)
- [x] FastAPI main → `backend/app/main.py`
  - [x] Router registration, CORS restricted to localhost:8501, 127.0.0.1:8501, frontend:8501

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

### Phase 5: Feedback Persistence — **Complete**

- [x] Create `backend/app/services/feedback.py`:
  - [x] SQLite initialization: table `feedback` (feedback_id, query_id, rating, comment, created_at)
  - [x] Thread-safe singleton connection with double-checked locking; WAL journal mode
  - [x] `save_feedback()` → persist to database
  - [x] `get_feedback_stats()` → aggregated stats (total, positive %, negative %)
  - [x] `get_recent_feedback(limit)` → last N feedback entries
- [x] Wire `routers/feedback.py` to use `services/feedback.py` instead of logging
- [x] Add `GET /feedback/stats` endpoint
- [x] Analytics dashboard in Streamlit sidebar → `frontend/pages/Analytics.py`

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
│   │   │   ├── query.py            # POST /query — RAG queries, budget enforcement, asyncio.to_thread
│   │   │   ├── ingest.py           # POST /ingest — trigger ingestion pipeline (concurrency lock)
│   │   │   └── feedback.py         # POST /feedback — user feedback collection
│   │   ├── services/
│   │   │   ├── pdf_parser.py       # PyMuPDFReader PDF loading + token counting
│   │   │   ├── rag_engine.py       # LlamaIndex RAG pipeline; ChromaDB retry+fail (no ephemeral)
│   │   │   ├── indexer.py          # Chunking + embedding + ChromaDB (concurrency lock)
│   │   │   └── feedback.py         # SQLite feedback persistence (Phase 5)
│   │   └── models/
│   │       └── schemas.py          # Pydantic request/response models
│   ├── tests/
│   │   ├── test_health.py          # Smoke tests: /, /health, /usage, /shutdown
│   │   ├── test_schemas.py         # Pydantic model validation (all 9 schemas)
│   │   ├── test_query_router.py    # /query endpoint: guards, errors, success
│   │   ├── test_ingest_router.py   # /ingest endpoint + metadata extraction
│   │   ├── test_feedback_router.py # /feedback, /feedback/stats, /feedback/recent
│   │   ├── test_rag_engine.py      # Filter building + response formatting
│   │   ├── test_edge_cases.py      # Null inputs, type mismatches, malformed data
│   │   ├── test_e2e_integration.py # Real PDF loading, full API flow, contract compliance
│   │   └── test_performance.py     # 15s latency enforcement (NFR-05)
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
| OpenAI API key quota exhausted | Medium | High | MockLLM/MockEmbedding fallback; budget-conscious query batching |
| Large PDF parsing failures | Low | Medium | Graceful skip per file; structured logging for debugging |
| ChromaDB container instability | Low | High | Named volume for persistence; retry logic (5 attempts) with explicit `ConnectionError` on failure; backend fails fast rather than silently using empty ephemeral store |
| Query latency exceeds acceptable threshold | Medium | Medium | Limit chunk retrieval top-k; use smaller embedding model |
| Docker build fails on pitch day | Low | Critical | Pre-build and test images day before; push images to registry |

---

## 13. Testing

### 13.1 Overview

The backend includes **242 automated tests** across 9 test files, all runnable locally without Docker, ChromaDB, or an OpenAI API key. External dependencies are mocked. The test framework is **pytest** (already in `backend/requirements.txt`).

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

### 13.2 Test Files

| File | Tests | Category | Description |
|------|-------|----------|-------------|
| `test_health.py` | 14 | Smoke | Verifies `GET /`, `GET /health`, `GET /usage`, `POST /shutdown`, and 404 on unknown routes. Confirms response status codes, JSON structure, content types, and that `/shutdown` triggers persist. |
| `test_schemas.py` | 43 | Schema Validation | Exercises all 9 Pydantic models (`QueryRequest`, `SourceDocument`, `QueryResponse`, `IngestRequest`, `IngestResponse`, `FeedbackRequest`, `FeedbackResponse`, `FeedbackStatsResponse`, `FeedbackRecord`). Tests field defaults, `min_length`/`max_length` boundaries, `max_length` on list fields, required field rejection, type mismatch rejection, null handling, and JSON round-trip serialization. |
| `test_query_router.py` | 53 | Query Endpoint | Tests `POST /query` through the full router stack. Covers: no-API-key guard (friendly message, engine not called), budget exhaustion (zero and negative remaining), mock-output safety net (repeated "text" tokens replaced), OpenAI error classification (auth, rate-limit, unknown), successful query (answer + sources), empty-answer replacement, and `use_sub_questions` passthrough (default `True`, explicit `False`). |
| `test_ingest_router.py` | 19 | Ingestion | Tests `POST /ingest` for success, skipped (already populated), already-running (concurrent lock), and error paths (`FileNotFoundError` → 404, `ValueError` → 400, `RuntimeError` → 500). Also tests `_extract_metadata` against all corpus filename patterns and `enrich_metadata` on fake document objects. |
| `test_feedback_router.py` | 17 | Feedback | Tests `POST /feedback` (success, comment forwarding, rating forwarding), validation errors (missing `query_id`, missing `rating`, invalid rating, numeric rating, empty body, null body), persistence failure (→ 500), `GET /feedback/stats` (success, zero stats, DB error), and `GET /feedback/recent` (success, empty, multiple records, limit boundaries 0/101 → 422, DB error). |
| `test_rag_engine.py` | 18 | RAG Internals | Tests `RAGEngine._build_filters` (no filters → `None`, empty lists → `None`, companies-only, years-only, both with AND condition, case lowering, `None` ignored) and `_format_response` (empty response, single doc, sub-question detection, text truncation at 500 chars, `None` score preserved, score rounding to 4 decimals, `file_name` fallback, `unknown` filename, `page` key fallback, missing `source_nodes` attribute). |
| `test_edge_cases.py` | 44 | Edge Cases | Tests `_safe_int` with 11 type variants (int, string, float, `None`, empty string, non-numeric, list, dict, bool, negative). Tests 12 malformed JSON payloads to `/query` (empty, null, string, array, invalid JSON, null/empty/long question, wrong-type companies/years, over-max lists). Tests filter passthrough, UUID format on `query_id`, mock-output edge cases, source nodes with missing fields, Unicode questions, special characters, float-to-int year coercion, and extra-field ignoring. |
| `test_e2e_integration.py` | 25 | E2E Integration | Loads **real 10-K PDFs** from `data/` using `load_pdf_documents`, then runs `enrich_metadata` and `SentenceSplitter` on them. Verifies document count, text content, metadata fields (company, year, doc_type, source_file), and chunk inheritance. Simulates the full user journey: `POST /ingest` → `POST /query` → `POST /feedback`, validating every response field against the API contract (§6.1). Tests all 7 endpoint response shapes and parametrizes metadata extraction over all 6 corpus filenames. Auto-skips PDF tests if `data/` is absent. |
| `test_performance.py` | 9 | Performance (NFR-05) | Enforces the 15-second query latency requirement with hard `assert elapsed < 15.0` assertions. Tests 4 query variants (simple, filtered, 50-source, max-length question). Injects `time.sleep(2)` and `time.sleep(5)` into the mock engine to verify the system stays within budget even with realistic engine delays. Tests `/health`, `/`, and `/usage` for sub-1-second response. |

### 13.3 What the Tests Validate (by Spec Requirement)

| Spec Requirement | Covered By |
|-----------------|------------|
| FR-QRY-01: Accept natural-language question | `test_schemas.py::TestQueryRequest`, `test_edge_cases.py::TestQueryMalformedInput` |
| FR-QRY-02: Optional company/year filters | `test_schemas.py::TestQueryRequest`, `test_edge_cases.py::TestQueryFilterPassthrough` |
| FR-QRY-04: Sub-question decomposition | `test_query_router.py::TestQuerySuccess` (passthrough True/False) |
| FR-QRY-06: Structured response | `test_e2e_integration.py::TestResponseContractCompliance`, `test_e2e_integration.py::TestFullApiFlow` |
| FR-QRY-07: Source documents with metadata | `test_rag_engine.py::TestFormatResponse`, `test_edge_cases.py::TestSourceNodeEdgeCases` |
| FR-ING-03: Chunk metadata (company, year, doc_type) | `test_ingest_router.py::TestExtractMetadata`, `test_e2e_integration.py::TestRealMetadataEnrichment` |
| FR-ING-06: Ingestion status | `test_ingest_router.py::TestIngestSuccess`, `TestIngestSkipped`, `TestIngestAlreadyRunning` |
| FR-ING-07: Skip corrupted PDFs | `test_ingest_router.py::TestIngestErrors` |
| FR-FDB-01/02/03: Feedback persistence | `test_feedback_router.py::TestFeedbackPost`, `TestFeedbackValidation` |
| FR-FDB-04: Aggregated stats | `test_feedback_router.py::TestFeedbackStats` |
| NFR-03: MockLLM/MockEmbedding fallback | `test_query_router.py::TestQueryNoApiKey`, `TestQueryMockOutputSafetyNet` |
| NFR-05: Query latency < 15s | `test_performance.py::TestQueryLatency`, `TestSimulatedLatency` |
| NFR-08: CORS configuration | `test_health.py` (app boots with CORS middleware) |
| NFR-09: Input validation | `test_schemas.py`, `test_edge_cases.py::TestQueryMalformedInput` |
| NFR-10: Budget enforcement | `test_query_router.py::TestQueryBudgetExhausted` |

### 13.4 Audit Findings

Issues discovered during the test audit process:

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| 1 | No E2E flow test — the `/ingest` → `/query` → `/feedback` chain was never tested as a sequence | High | Added `TestFullApiFlow` in `test_e2e_integration.py` |
| 2 | No real PDF tests — `load_pdf_documents` + `enrich_metadata` + `SentenceSplitter` were untested on actual files | High | Added `TestRealPdfLoading`, `TestRealMetadataEnrichment`, `TestRealChunking` |
| 3 | NFR-05 (15s latency) completely untested | Medium | Added `TestQueryLatency` + `TestSimulatedLatency` with hard assertions |
| 4 | No response contract validation — tests checked individual fields but never the exact set of keys | Medium | Added `TestResponseContractCompliance` |
| 5 | Original `test_schemas.py` only tested `use_sub_questions` default — 8 of 9 schemas had zero coverage | Medium | Rewrote `test_schemas.py` with 43 tests covering all models |
| 6 | No validation boundary tests for `min_length=1`, `max_length=2000`, `max_length=10` | Medium | Added in `test_schemas.py` and `test_edge_cases.py` |
| 7 | No tests for malformed request bodies (null, array, invalid JSON) | Medium | Added `TestQueryMalformedInput` in `test_edge_cases.py` |
| 8 | No tests for filter passthrough to engine | Low | Added `TestQueryFilterPassthrough` |
| 9 | `query_id` UUID format never validated | Low | Added `TestQueryIdPresence` |
| 10 | Corpus coverage gap — `google-2024.pdf` (hyphen) vs `google_2025.pdf` (underscore) not parametrized | Low | Added `TestCorpusMetadataExtraction` over all 6 files |

### 13.5 Running Tests

```bash
# All tests
cd backend
python -m pytest tests/ -v --tb=short

# Specific category
python -m pytest tests/test_performance.py -v --tb=short

# E2E + performance only
python -m pytest tests/test_e2e_integration.py tests/test_performance.py -v --tb=short

# Skip real-PDF tests (if data/ folder is absent)
python -m pytest tests/ -v -k "not RealPdf and not RealMetadata and not RealChunking"
```
