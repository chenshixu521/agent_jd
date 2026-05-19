from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChatMessage:
    role: str
    content: str
    message_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ChatMessage":
        return ChatMessage(
            role=data["role"],
            content=data["content"],
            message_id=data.get("message_id") or data.get("messageId") or str(uuid4()),
            created_at=data.get("created_at") or data.get("createdAt") or now_iso(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionState:
    session_id: str
    user_id: str
    title: str = "新会话"
    status: str = "ACTIVE"
    summary: str = ""
    turn_count: int = 0
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SessionState":
        return SessionState(
            session_id=data["session_id"],
            user_id=str(data["user_id"]),
            title=data.get("title", "新会话"),
            status=data.get("status", "ACTIVE"),
            summary=data.get("summary", ""),
            turn_count=int(data.get("turn_count", 0)),
            created_at=data.get("created_at", now_iso()),
            updated_at=data.get("updated_at", now_iso()),
            metadata=data.get("metadata", {}),
        )
