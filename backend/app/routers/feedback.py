import logging
import uuid

from fastapi import APIRouter

from ..models.schemas import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(request: FeedbackRequest):
    feedback_id = str(uuid.uuid4())

    # TODO: replace with persistent storage via services/feedback.py (Phase 5)
    logger.info(
        "Feedback received: id=%s query=%s rating=%s comment=%r",
        feedback_id,
        request.query_id,
        request.rating,
        request.comment,
    )

    return FeedbackResponse(status="ok", feedback_id=feedback_id)
