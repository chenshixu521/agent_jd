from typing import Any

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    user_id: str | None = Field(default=None, alias="userId")
    title: str = "新会话"
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class MessageAppendRequest(BaseModel):
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
