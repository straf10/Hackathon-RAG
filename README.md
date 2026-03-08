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

## Project Structure

```
Hackathon-RAG/
├── backend/
│   ├── app/
│   │   └── main.py              # FastAPI entrypoint
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                   # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
├── data/                        # 10-K PDFs (τοποθετούνται τοπικά)
├── docker-compose.yml
├── .env                         # API keys (ΔΕΝ γίνεται commit)
└── README.md
```
