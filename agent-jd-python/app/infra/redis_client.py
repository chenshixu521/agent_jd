import json
from typing import Any

import redis.asyncio as redis
from loguru import logger

from app.core.settings import settings

_client: redis.Redis | None = None


async def get_redis() -> redis.Redis | None:
    global _client
    if _client is not None:
        return _client
    try:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        await _client.ping()
        return _client
    except Exception as exc:
        logger.warning(f"Redis unavailable: {exc}")
        _client = None
        return None


async def set_context(task_id: str, payload: dict[str, Any], ttl: int = 86400) -> None:
    client = await get_redis()
    if client is None:
        return
    await client.setex(f"agent:context:{task_id}", ttl, json.dumps(payload, ensure_ascii=False))


async def get_context(task_id: str) -> dict[str, Any] | None:
    client = await get_redis()
    if client is None:
        return None
    raw = await client.get(f"agent:context:{task_id}")
    return json.loads(raw) if raw else None


async def append_event(task_id: str, event: dict[str, Any], ttl: int = 86400) -> None:
    client = await get_redis()
    if client is None:
        return
    key = f"agent:event:{task_id}"
    await client.rpush(key, json.dumps(event, ensure_ascii=False))
    await client.expire(key, ttl)


async def set_task_status(task_id: str, status: str, progress: int, extra: dict[str, Any] | None = None, ttl: int = 86400) -> None:
    client = await get_redis()
    if client is None:
        return
    key = f"agent:task:{task_id}"
    payload = {"task_id": task_id, "status": status, "progress": progress, **(extra or {})}
    await client.setex(key, ttl, json.dumps(payload, ensure_ascii=False))
