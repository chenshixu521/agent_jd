from fastapi import Header

from app.core.errors import AgentError, ErrorCode
from app.core.settings import settings


async def verify_internal_token(authorization: str | None = Header(default=None)) -> None:
    if not settings.internal_token:
        return
    expected = f"Bearer {settings.internal_token}"
    if authorization != expected:
        raise AgentError(ErrorCode.AUTH_INVALID, "内部服务令牌无效")
