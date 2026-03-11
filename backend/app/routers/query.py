import asyncio
import logging
import re
import uuid

from fastapi import APIRouter, HTTPException

from ..models.schemas import QueryRequest, QueryResponse, SourceDocument
from ..services.rag_engine import RAGEngine
from ..utils.models import has_valid_openai_key
from ..utils.token_tracker import get_usage, persist as persist_usage

logger = logging.getLogger(__name__)

router = APIRouter()

_engine: RAGEngine | None = None

_MOCK_LLM_RE = re.compile(r"^(\s*text\b[\s,]*){3,}$", re.IGNORECASE)

_NO_API_KEY_MSG = (
    "No valid OpenAI API key is configured. The system cannot generate "
    "meaningful answers without a connection to the language model.\n\n"
    "Please set a valid `OPENAI_API_KEY` in the `.env` file or as an "
    "environment variable and restart the backend."
)

_BUDGET_EXHAUSTED_MSG = (
    "The API token budget has been exhausted — no further queries can be "
    "processed.\n\nTo continue, increase the budget in the backend "
    "configuration or reset the usage counters and restart the system."
)

_AUTH_FAILED_MSG = (
    "The OpenAI API rejected the provided API key (authentication error). "
    "Please verify that `OPENAI_API_KEY` is correct and active, then "
    "restart the backend."
)

_RATE_LIMIT_MSG = (
    "The OpenAI API rate limit or billing quota has been exceeded. "
    "Please wait a few minutes and try again, or check your OpenAI account "
    "billing settings."
)


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


def _is_mock_output(text: str) -> bool:
    """Return True when *text* looks like MockLLM filler (repeated 'text' tokens)."""
    return bool(_MOCK_LLM_RE.match(text.strip()))


def _classify_openai_error(exc: Exception) -> str | None:
    """Inspect the exception chain for OpenAI-specific errors and return a
    user-friendly message, or *None* if the error is unrecognised."""
    exc_str = f"{type(exc).__name__}: {exc}".lower()
    if any(kw in exc_str for kw in ("authenticationerror", "invalid api key", "401")):
        return _AUTH_FAILED_MSG
    if any(kw in exc_str for kw in ("ratelimiterror", "rate_limit", "429", "quota", "billing")):
        return _RATE_LIMIT_MSG
    return None


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    query_id = str(uuid.uuid4())

    if not has_valid_openai_key():
        return QueryResponse(answer=_NO_API_KEY_MSG, sources=[], query_id=query_id)

    usage = get_usage()
    if usage["budget_remaining_usd"] <= 0:
        return QueryResponse(answer=_BUDGET_EXHAUSTED_MSG, sources=[], query_id=query_id)

    try:
        engine = get_engine()
        result = await asyncio.to_thread(
            engine.query,
            question=request.question,
            companies=request.companies,
            years=request.years,
            use_sub_questions=request.use_sub_questions,
        )
    except Exception as exc:
        friendly = _classify_openai_error(exc)
        if friendly:
            logger.warning("OpenAI API error: %s", exc)
            return QueryResponse(answer=friendly, sources=[], query_id=query_id)
        logger.exception("RAG query failed")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your query.",
        )
    finally:
        persist_usage()

    answer = result["answer"]

    if _is_mock_output(answer):
        answer = _NO_API_KEY_MSG

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
