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

## PDF Parsing — `backend/app/services/pdf_parser.py`

Η συνάρτηση `load_pdf_documents()` διαβάζει όλα τα PDF από τον φάκελο `data/` και τα μετατρέπει σε LlamaIndex `Document` objects.

**Τι κάνει:**

1. Σαρώνει αναδρομικά τον φάκελο `data/` για αρχεία `.pdf`
2. Χρησιμοποιεί τον `PyMuPDFReader` (μέσω `file_extractor`) αντί του default PDF reader
3. Επεξεργάζεται κάθε αρχείο ξεχωριστά — αν κάποιο PDF είναι corrupted, το παρακάμπτει χωρίς να σταματάει
4. Καταγράφει (logging) πόσα documents παρήχθησαν ανά αρχείο και το σύνολο στο τέλος

**Εκτέλεση standalone:**

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
│   │   ├── main.py              # FastAPI entrypoint
│   │   └── services/
│   │       └── pdf_parser.py    # PDF parsing με PyMuPDFReader
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                   # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
├── data/                        # 10-K PDFs (committed στο repo)
├── docker-compose.yml
├── .env                         # API keys (ΔΕΝ γίνεται commit)
└── README.md
```
