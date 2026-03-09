from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import feedback, ingest, query, usage
from .utils.token_tracker import install as install_token_tracking
from .utils.token_tracker import persist as persist_usage


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_token_tracking()
    query.init_engine()
    yield
    persist_usage()


app = FastAPI(title="Financial RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(feedback.router)
app.include_router(usage.router)


@app.get("/")
async def root():
    return {"message": "Financial RAG Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
