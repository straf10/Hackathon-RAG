from fastapi import APIRouter

from ..utils.token_tracker import get_usage, persist

router = APIRouter()


@router.get("/usage")
async def usage():
    return get_usage()


@router.post("/shutdown")
async def shutdown():
    """Persist all data so nothing is lost on container stop."""
    persist()
    return {"status": "ok", "message": "Data saved. Safe to stop containers."}
