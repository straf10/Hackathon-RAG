from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import feedback, ingest, query

app = FastAPI(title="Financial RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(feedback.router)


@app.get("/")
async def root():
    return {"message": "Financial RAG Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
