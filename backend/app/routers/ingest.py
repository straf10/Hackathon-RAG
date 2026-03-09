import asyncio
import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import IngestRequest, IngestResponse
from ..services.indexer import run_ingestion
from ..utils.token_tracker import persist as persist_usage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest | None = None):
    force = request.force if request else False
    try:
        result = await asyncio.to_thread(run_ingestion, force)
    except FileNotFoundError as exc:
        logger.warning("Ingestion failed: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("Ingestion failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        persist_usage()

    return IngestResponse(
        status=result.get("status", "ok"),
        documents_processed=result.get("documents_loaded", 0),
        chunks_created=result.get("chunks_created", 0),
        existing_chunks=result.get("existing_chunks", 0),
    )
