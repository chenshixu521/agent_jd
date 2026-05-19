from contextvars import ContextVar
from uuid import uuid4

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def set_trace_id(trace_id: str | None) -> str:
    value = trace_id or str(uuid4())
    trace_id_var.set(value)
    return value


def get_trace_id() -> str:
    value = trace_id_var.get()
    if not value:
        value = str(uuid4())
        trace_id_var.set(value)
    return value


def set_user_id(user_id: str | None) -> None:
    user_id_var.set(user_id or "")


def get_user_id() -> str:
    return user_id_var.get()
