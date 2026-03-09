import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import IngestResponse
from ..services.indexer import run_ingestion

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest():
    try:
        result = run_ingestion()
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return IngestResponse(
        status=result.get("status", "ok"),
        documents_processed=result.get("documents_loaded", 0),
        chunks_created=result.get("chunks_created", 0),
    )
