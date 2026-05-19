from fastapi import Header, Request

from app.core.tracing import set_trace_id, set_user_id


async def bind_context(request: Request, x_trace_id: str | None = Header(default=None), x_user_id: str | None = Header(default=None)) -> None:
    trace_id = set_trace_id(x_trace_id)
    set_user_id(x_user_id)
    request.state.trace_id = trace_id
    request.state.user_id = x_user_id
