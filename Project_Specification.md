# Project Specification — Lexio: PageIndex RAG for Financial Documents

> **Challenge 2: AI-Powered Knowledge Base System** — Netcompany Hackathon Thessaloniki 2026

---

## 1. Project Overview

| Field              | Detail                                     |
| ------------------ | ------------------------------------------ |
| **Event**          | Netcompany Hackathon Thessaloniki 2026     |
| **Challenge**      | Challenge 2 — AI-Powered Knowledge Base    |
| **Project Title**  | Lexio — PageIndex RAG for Financial Documents |
| **Team Location**  | Thessaloniki, Greece                       |
| **Timeline**       | March 6–20, 2026                           |
| **Submission Due** | March 15, 2026                             |
| **Pitch Date**     | March 19, 2026                             |

**Domain:** Financial document analysis (SEC filings, annual reports, 10-K filings).

---

## 2. Ideation

*Design and implement an intelligent Knowledge Base solution powered by GenAI. The goal is to go beyond a simple Q&A bot — build a system that understands, organizes, and retrieves knowledge intelligently.*

Lexio addresses each challenge requirement as follows:

| Challenge Requirement | Lexio Implementation |
| --------------------- | --------------------- |
| **Ingest and structure knowledge** from documents, APIs, or provided data sources | Recursive PDF ingestion from `data/` directory; PyMuPDF parses financial documents page-by-page; structured chunks with metadata (company, year, doc_type, source_file). |
| **Natural language querying** with relevant, explainable responses | Natural-language questions via chat UI; metadata filtering by company and fiscal year; structured responses with source citations (filename, page number, relevance score, text snippet). |
| **Learn from user interactions**, refining relevance or summaries over time | Token usage tracking and budget enforcement; corpus fingerprint enables smart re-ingestion when documents change; design supports future feedback loops (extensible). |
| **Semantic search or RAG** for grounded answers | LlamaIndex RAG pipeline with OpenAI embeddings; ChromaDB vector store for semantic retrieval; retrieval-augmented generation ensures answers cite source pages. |
| **GenAI as reasoning and retrieval engine** — connect, interpret, synthesize knowledge meaningfully | Sub-question decomposition for comparative queries (e.g. *"Compare NVIDIA vs Google revenue 2024–2025"*); LLM synthesizes retrieved context into coherent answers; PageIndex granularity ties every chunk to its source page. |

---

## 3. Expected Outcomes

| Outcome | Challenge Expectation | Lexio Delivery |
| ------- | --------------------- | -------------- |
| **Working Prototype** | A functioning system that allows users to add, search, and query information using natural language. | Full Dockerized stack: `docker compose up --build` starts backend (FastAPI), frontend (Streamlit), and ChromaDB. Users ingest PDFs, filter by company/year, and query in natural language with instant answers. |
| **Knowledge Artifacts** | Demonstrate structured output — knowledge graphs, entity relationships, embeddings, or summarized content snippets. | Dense embeddings (OpenAI `text-embedding-3-small`) in ChromaDB; page-level metadata on every chunk; source citations with filename, page, score, snippet; optional auto-visualization of numerical data (tables, bar charts). |
| **Live Demo** | Present the solution end-to-end — from ingestion and indexing to natural language answers and reasoning results. | End-to-end flow: ingest → index → query with citations. Comparative queries showcase sub-question decomposition. Live demo plan: 3–4 example queries (simple + multi-step) during pitch. |
| **Approach & Rationale** | Explain architecture, how GenAI is used (indexing, semantic search, summarization), and why design choices matter (scalability, modularity, novelty). | See [README — Architecture](README.md#architecture). Key rationale: PageIndex citation (exact page references), LlamaIndex for modular RAG, Docker for portability, metadata filtering for precision. |

---

## 4. Tech Stack

### 4.1 Core Technologies

| Layer | Technology | Role |
| ----- | ---------- | ---- |
| **Runtime Environment** | Dockerized application on Linux base image | All services run in containers; `python:3.12-slim` (official) for backend/frontend; `chromadb/chroma:1.5.2` for vector DB. |
| **Backend** | Python (FastAPI) | Async REST API; `/query`, `/ingest`, `/health`, `/usage`; CORS, validation, budget enforcement. |
| **Frontend** | Streamlit | Chat interface for querying and visualization; sidebar filters, source citations, token analytics, auto-charts for numerical data. |
| **Database / Search Layer** | ChromaDB | Vector database for embeddings; metadata index for company, year, doc_type, source_file; persistent storage via Docker volume. |
| **AI / LLM Frameworks** | OpenAI API, LlamaIndex | `gpt-4.1` for answer synthesis; `text-embedding-3-small` for dense embeddings; LlamaIndex for retrieval, chunking, sub-question decomposition. |

### 4.2 Supporting Tools

| Tool | Usage |
| ---- | ----- |
| **Containerization** | Docker / Docker Compose for multi-service setup (backend, frontend, chromadb). |
| **Embedding / RAG Pipelines** | Dense embeddings (OpenAI); metadata-filtered semantic retrieval; BM25/TF-IDF alternatives not used (dense embeddings sufficient for this scope). |
| **Documentation** | Clear README with setup, architecture (Mermaid diagram), API reference; optional architectural diagram. |
