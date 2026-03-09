# Financial RAG - Hackathon Thessaloniki 2026

Retrieval-Augmented Generation σύστημα για ανάλυση 10-K financial reports (NVIDIA, Google, Apple).

## Tech Stack

- **Backend:** FastAPI + LlamaIndex + OpenAI
- **Frontend:** Streamlit
- **Vector DB:** ChromaDB
- **Containerization:** Docker Compose

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) εγκατεστημένο και σε λειτουργία
- OpenAI API key

Επιβεβαίωση ότι το Docker τρέχει:

```bash
docker --version
docker compose version
```

## Setup (πρώτη φορά)

### 1. Clone the repo

```bash
git clone <repo-url>
cd Hackathon-RAG
```

### 2. Δημιουργία `.env`

Φτιάξε ένα αρχείο `.env` στον root φάκελο του project:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

> **Σημαντικό:** Το `.env` δεν γίνεται push στο Git. Κάθε μέλος το φτιάχνει τοπικά.

### 3. Εκκίνηση

```bash
docker compose up --build
```

Η πρώτη εκτέλεση θα πάρει μερικά λεπτά (κατεβάζει images, εγκαθιστά packages).

### 4. Επαλήθευση

| Service  | URL                    | Τι θα δεις                        |
|----------|------------------------|-----------------------------------|
| Backend  | http://localhost:8000  | `{"message": "Financial RAG..."}` |
| Frontend | http://localhost:8501  | Streamlit Chat UI                 |
| ChromaDB | http://localhost:8100  | ChromaDB API                      |

## Καθημερινή χρήση

```bash
git pull                          # παίρνεις τις τελευταίες αλλαγές
docker compose up --build         # χτίζει και τρέχει τα services
```

Για να σταματήσεις: **Ctrl+C** ή σε νέο terminal:

```bash
docker compose down
```

## API Endpoints

| Method | Endpoint    | Request Body | Response | Περιγραφή |
|--------|-------------|--------------|----------|-----------|
| GET    | `/`         | —            | `{"message": "..."}` | Health message |
| GET    | `/health`   | —            | `{"status": "ok"}` | Health check |
| POST   | `/query`    | `QueryRequest` | `QueryResponse` | RAG query με optional φίλτρα |
| POST   | `/ingest`   | —            | `IngestResponse` | Trigger PDF ingestion pipeline |
| POST   | `/feedback` | `FeedbackRequest` | `FeedbackResponse` | Submit user feedback |

### Παράδειγμα `/query`

```json
// Request
{
  "question": "What was NVIDIA's total revenue in 2024?",
  "companies": ["nvidia"],
  "years": [2024]
}

// Response
{
  "answer": "NVIDIA's total revenue for fiscal year 2024 was...",
  "sources": [
    {
      "filename": "nvidia_2024.pdf",
      "page": 45,
      "score": 0.8721,
      "text_snippet": "Total revenue for the fiscal year..."
    }
  ]
}
```

### Παράδειγμα `/feedback`

```json
// Request
{"query_id": "q-001", "rating": "up", "comment": "accurate answer"}

// Response
{"status": "ok", "feedback_id": "adcf3f7e-cd91-..."}
```

> **Σημείωση:** Χωρίς valid OpenAI API key (`sk-...`), το σύστημα χρησιμοποιεί MockLLM/MockEmbedding και επιστρέφει `"Empty Response"`. Αυτό είναι αναμενόμενο.

## Τοπικό Testing (χωρίς Docker)

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Σε δεύτερο terminal (PowerShell):

```powershell
# Health check
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json

# Query
Invoke-RestMethod -Uri http://127.0.0.1:8000/query -Method Post -ContentType 'application/json' -Body '{"question":"What is NVIDIA revenue?"}' | ConvertTo-Json

# Feedback
Invoke-RestMethod -Uri http://127.0.0.1:8000/feedback -Method Post -ContentType 'application/json' -Body '{"query_id":"q1","rating":"up"}' | ConvertTo-Json
```

## PDF Parsing — `backend/app/services/pdf_parser.py`

Η συνάρτηση `load_pdf_documents()` διαβάζει όλα τα PDF από τον φάκελο `data/` και τα μετατρέπει σε LlamaIndex `Document` objects.

**Τι κάνει:**

1. Σαρώνει αναδρομικά τον φάκελο `data/` για αρχεία `.pdf`
2. Χρησιμοποιεί τον `PyMuPDFReader` (μέσω `file_extractor`) αντί του default PDF reader
3. Επεξεργάζεται κάθε αρχείο ξεχωριστά — αν κάποιο PDF είναι corrupted, το παρακάμπτει χωρίς να σταματάει
4. Καταγράφει (logging) πόσα documents παρήχθησαν ανά αρχείο και το σύνολο στο τέλος

**Εκτέλεση μέσα στο Docker container** (απαιτεί `docker compose up --build`):

```bash
docker compose exec backend python -m app.services.pdf_parser
```

**Εκτέλεση τοπικά** (χωρίς Docker, από τον root φάκελο του project):

```bash
python -m backend.app.services.pdf_parser
```

**Χρήση ως module:**

```python
from backend.app.services.pdf_parser import load_pdf_documents

documents = load_pdf_documents()  # -> list[Document]
```

## Project Structure

```
Hackathon-RAG/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entrypoint + router registration + CORS
│   │   ├── config.py            # Settings (env vars, pydantic-settings)
│   │   ├── routers/
│   │   │   ├── query.py         # POST /query — RAG queries
│   │   │   ├── ingest.py        # POST /ingest — trigger indexing
│   │   │   └── feedback.py      # POST /feedback — user feedback
│   │   ├── services/
│   │   │   ├── pdf_parser.py    # PDF loading με PyMuPDFReader
│   │   │   ├── rag_engine.py    # LlamaIndex RAG pipeline (Mock fallback)
│   │   │   └── indexer.py       # Document chunking + embedding + ChromaDB
│   │   └── models/
│   │       └── schemas.py       # Pydantic request/response models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                   # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
├── data/                        # 10-K PDFs (committed στο repo)
│   ├── nvidia/
│   ├── google/
│   └── apple/
├── docker-compose.yml
├── .env                         # API keys (ΔΕΝ γίνεται commit)
└── README.md
```
