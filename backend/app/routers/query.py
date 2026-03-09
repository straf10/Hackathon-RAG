import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import QueryRequest, QueryResponse, SourceDocument
from ..services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter()

_engine: RAGEngine | None = None


def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        engine = get_engine()
        result = engine.query(
            question=request.question,
            companies=request.companies,
            years=request.years,
            use_sub_questions=False,
        )
    except Exception as exc:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    sources = [
        SourceDocument(
            filename=s.get("filename", "unknown"),
            page=int(s.get("page_label", 0) or 0),
            score=s.get("score") or 0.0,
            text_snippet=s.get("text_snippet", ""),
        )
        for s in result.get("source_nodes", [])
    ]

    return QueryResponse(answer=result["answer"], sources=sources)
