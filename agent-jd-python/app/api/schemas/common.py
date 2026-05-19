from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    task_id: str | None = Field(default=None, alias="taskId")
    stream: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class AgentErrorPayload(BaseModel):
    type: str
    message: str
    retryable: bool = False


class AgentResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    success: bool = True
    taskId: str | None = None
    data: Any = None
    error: AgentErrorPayload | None = None
    traceId: str | None = None
