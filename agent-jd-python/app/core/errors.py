from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.tracing import get_trace_id


class ErrorCode:
    OK = 0
    PARAM_INVALID = 40001
    AUTH_INVALID = 40102
    NOT_FOUND = 40401
    AGENT_FAILED = 50001
    SYSTEM_ERROR = 50000


class AgentError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ApiResponse(BaseModel):
    code: int
    msg: str
    data: object | None = None
    traceId: str | None = None


async def agent_error_handler(_: Request, exc: AgentError) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "code": exc.code,
            "msg": exc.message,
            "success": False,
            "data": None,
            "error": {"type": exc.__class__.__name__, "message": exc.message, "retryable": exc.code >= 50000},
            "traceId": get_trace_id(),
        },
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "code": ErrorCode.SYSTEM_ERROR,
            "msg": str(exc),
            "success": False,
            "data": None,
            "error": {"type": exc.__class__.__name__, "message": str(exc), "retryable": True},
            "traceId": get_trace_id(),
        },
    )
