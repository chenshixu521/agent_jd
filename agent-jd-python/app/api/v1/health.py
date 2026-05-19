from fastapi import APIRouter

from app.core.tracing import get_trace_id

router = APIRouter()


@router.get("/health")
async def health():
    return {"code": 0, "msg": "ok", "data": {"status": "UP"}, "traceId": get_trace_id()}
