import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException

from ..models.schemas import QueryRequest, QueryResponse, SourceDocument
from ..services.rag_engine import RAGEngine
from ..utils.token_tracker import get_usage, persist as persist_usage

logger = logging.getLogger(__name__)

router = APIRouter()

_engine: RAGEngine | None = None


def _safe_int(value) -> int:
    """Convert *value* to int, returning 0 for anything non-numeric."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def init_engine() -> None:
    global _engine
    _engine = RAGEngine()


def get_engine() -> RAGEngine:
    assert _engine is not None, "RAGEngine not initialized (startup failed?)"
    return _engine


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    usage = get_usage()
    if usage["budget_remaining_usd"] <= 0:
        raise HTTPException(
            status_code=429,
            detail="Token budget exhausted. No further queries allowed.",
        )

    query_id = str(uuid.uuid4())
    try:
        engine = get_engine()
        result = await asyncio.to_thread(
            engine.query,
            question=request.question,
            companies=request.companies,
            years=request.years,
            use_sub_questions=request.use_sub_questions,
        )
    except Exception:
        logger.exception("RAG query failed")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your query.",
        )
    finally:
        persist_usage()

    answer = result["answer"]
    if not answer or answer.strip().lower() in ("empty response", "none", ""):
        answer = (
            "I don't have enough information in the ingested 10-K documents "
            "to answer this question. Try rephrasing, adjusting the company/"
            "year filters, or asking something related to the financial "
            "filings (revenue, expenses, risk factors, etc.)."
        )

    sources = [
        SourceDocument(
            filename=s.get("filename", "unknown"),
            page=_safe_int(s.get("page_label", 0)),
            score=s.get("score") or 0.0,
            text_snippet=s.get("text_snippet", ""),
            source_type=s.get("source_type", "document"),
        )
        for s in result.get("source_nodes", [])
    ]

    return QueryResponse(answer=answer, sources=sources, query_id=query_id)
