from fastapi import FastAPI

app = FastAPI(title="Financial RAG API")


@app.get("/")
async def root():
    return {"message": "Financial RAG Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
