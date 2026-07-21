import hashlib
import json
from typing import Any
from uuid import uuid4

from app.core.tracing import get_user_id
from app.infra.redis_client import get_redis
from app.memory.context_window import ContextWindowPolicy
from app.memory.schema import ChatMessage, SessionState, now_iso


class RedisSessionStore:
    def __init__(self, ttl_seconds: int = 7 * 24 * 3600, message_limit: int = 200, context_policy: ContextWindowPolicy | None = None):
        self.ttl_seconds = ttl_seconds
        self.message_limit = message_limit
        self.context_policy = context_policy or ContextWindowPolicy()

    async def create_session(
        self,
        user_id: str | None = None,
        title: str = "新会话",
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> SessionState:
        user = user_id or get_user_id() or "anonymous"
        state = SessionState(
            session_id=session_id or str(uuid4()),
            user_id=str(user),
            title=title,
            metadata=metadata or {},
        )
        await self.save_session(state)
        return state

    async def save_session(self, state: SessionState) -> None:
        client = await get_redis()
        if client is None:
            return
        key = self._session_key(state.session_id)
        await client.setex(key, self.ttl_seconds, json.dumps(state.to_dict(), ensure_ascii=False))
        await client.zadd(self._user_sessions_key(state.user_id), {state.session_id: self._score(state.updated_at)})
        await client.expire(self._user_sessions_key(state.user_id), self.ttl_seconds)

    async def get_session(self, session_id: str) -> SessionState | None:
        client = await get_redis()
        if client is None:
            return None
        raw = await client.get(self._session_key(session_id))
        return SessionState.from_dict(json.loads(raw)) if raw else None

    async def touch_session(self, session_id: str) -> None:
        state = await self.get_session(session_id)
        if state is None:
            return
        state.updated_at = now_iso()
        await self.save_session(state)

    async def append_message(self, session_id: str, message: ChatMessage) -> None:
        client = await get_redis()
        if client is None:
            return
        key = self._messages_key(session_id)
        await client.rpush(key, json.dumps(message.to_dict(), ensure_ascii=False))
        await client.ltrim(key, -self.message_limit, -1)
        await client.expire(key, self.ttl_seconds)
        state = await self.get_session(session_id)
        if state is not None:
            state.turn_count += 1 if message.role == "user" else 0
            state.updated_at = now_iso()
            await self.save_session(state)

    async def list_messages(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        client = await get_redis()
        if client is None:
            return []
        rows = await client.lrange(self._messages_key(session_id), -limit, -1)
        return [ChatMessage.from_dict(json.loads(row)) for row in rows]

    async def build_context(self, session_id: str, incoming_message: str | None = None) -> list[ChatMessage]:
        messages = await self.list_messages(session_id, limit=self.message_limit)
        if incoming_message:
            messages.append(ChatMessage(role="user", content=incoming_message))
        return self.context_policy.trim(messages)

    async def set_task_status(self, task_id: str, status: str, progress: int, payload: dict[str, Any] | None = None) -> None:
        client = await get_redis()
        if client is None:
            return
        data = {"task_id": task_id, "status": status, "progress": progress, "updated_at": now_iso(), **(payload or {})}
        await client.setex(self._agent_task_key(task_id), 24 * 3600, json.dumps(data, ensure_ascii=False))

    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        client = await get_redis()
        if client is None:
            return None
        raw = await client.get(self._agent_task_key(task_id))
        return json.loads(raw) if raw else None

    async def get_prompt_cache(self, cache_key: str) -> dict[str, Any] | None:
        client = await get_redis()
        if client is None:
            return None
        raw = await client.get(self._prompt_cache_key(cache_key))
        return json.loads(raw) if raw else None

    async def set_prompt_cache(self, cache_key: str, value: dict[str, Any], ttl_seconds: int = 3600) -> None:
        client = await get_redis()
        if client is None:
            return
        await client.setex(self._prompt_cache_key(cache_key), ttl_seconds, json.dumps(value, ensure_ascii=False))

    def make_prompt_cache_key(self, capability: str, prompt_version: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{capability}:{prompt_version}:{digest}"

    def _session_key(self, session_id: str) -> str:
        return f"session:state:{session_id}"

    def _messages_key(self, session_id: str) -> str:
        return f"session:messages:{session_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        return f"session:user:{user_id}"

    def _agent_task_key(self, task_id: str) -> str:
        return f"agent:task:{task_id}"

    def _prompt_cache_key(self, cache_key: str) -> str:
        return f"prompt:ctx:{cache_key}"

    def _score(self, iso_time: str) -> float:
        return float(sum(ord(char) for char in iso_time))


_session_store: RedisSessionStore | None = None


def get_session_store() -> RedisSessionStore:
    global _session_store
    if _session_store is None:
        _session_store = RedisSessionStore()
    return _session_store
