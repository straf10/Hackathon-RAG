from fastapi import APIRouter

from ..utils.token_tracker import get_usage

router = APIRouter()


@router.get("/usage")
async def usage():
    return get_usage()
