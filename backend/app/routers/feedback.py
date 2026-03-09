import logging
import uuid

from fastapi import APIRouter, HTTPException, Query

from ..models.schemas import (
    FeedbackRecord,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackStatsResponse,
)
from ..services.feedback import get_feedback_stats, get_recent_feedback, save_feedback

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(request: FeedbackRequest):
    feedback_id = str(uuid.uuid4())
    try:
        save_feedback(
            feedback_id=feedback_id,
            query_id=request.query_id,
            rating=request.rating,
            comment=request.comment,
        )
    except Exception:
        logger.exception("Failed to persist feedback %s", feedback_id)
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    return FeedbackResponse(status="ok", feedback_id=feedback_id)


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def feedback_stats():
    try:
        stats = get_feedback_stats()
    except Exception:
        logger.exception("Failed to retrieve feedback stats")
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")
    return FeedbackStatsResponse(**stats)


@router.get("/feedback/recent", response_model=list[FeedbackRecord])
async def recent_feedback(limit: int = Query(default=20, ge=1, le=100)):
    try:
        rows = get_recent_feedback(limit=limit)
    except Exception:
        logger.exception("Failed to retrieve recent feedback")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")
    return [FeedbackRecord(**r) for r in rows]
