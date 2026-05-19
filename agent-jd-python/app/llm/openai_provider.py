from typing import Any

from openai import AsyncOpenAI

from app.core.settings import settings
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
        )
        self.model = settings.openai_model

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        request: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }
        if kwargs.get("max_tokens") is not None:
            request["max_tokens"] = kwargs.get("max_tokens")
        response = await self.client.chat.completions.create(**request)
        return response.choices[0].message.content or ""

    async def json_mode(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "response_format": {"type": "json_object"},
        }
        if kwargs.get("max_tokens") is not None:
            request["max_tokens"] = kwargs.get("max_tokens")
        response = await self.client.chat.completions.create(**request)
        import json
        return json.loads(response.choices[0].message.content or "{}")
