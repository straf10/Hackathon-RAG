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
    except FileNotFoundError:
        logger.warning("Ingestion failed: data directory not found")
        raise HTTPException(status_code=404, detail="Data directory not found.")
    except ValueError:
        logger.warning("Ingestion failed: no valid documents")
        raise HTTPException(status_code=400, detail="No valid PDF documents found.")
    except Exception:
        logger.exception("Ingestion failed")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred during ingestion.",
        )
    finally:
        persist_usage()

    return IngestResponse(
        status=result.get("status", "ok"),
        documents_processed=result.get("documents_loaded", 0),
        chunks_created=result.get("chunks_created", 0),
        existing_chunks=result.get("existing_chunks", 0),
    )
