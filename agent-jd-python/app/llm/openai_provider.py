from typing import Any
from time import perf_counter
import json

from openai import AsyncOpenAI

from app.core.settings import settings
from app.core.metrics import record_llm_call
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
        model = kwargs.get("model", self.model)
        request: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }
        if kwargs.get("max_tokens") is not None:
            request["max_tokens"] = kwargs.get("max_tokens")
        started = perf_counter()
        try:
            response = await self.client.chat.completions.create(**request)
            content = response.choices[0].message.content or ""
        except Exception:
            record_llm_call("openai", model, "chat", "failed", perf_counter() - started)
            raise
        self._record_success(response, model, "chat", started)
        return content

    async def json_mode(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        model = kwargs.get("model", self.model)
        request: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "response_format": {"type": "json_object"},
        }
        if kwargs.get("max_tokens") is not None:
            request["max_tokens"] = kwargs.get("max_tokens")
        started = perf_counter()
        try:
            response = await self.client.chat.completions.create(**request)
            content = json.loads(response.choices[0].message.content or "{}")
        except Exception:
            record_llm_call("openai", model, "json", "failed", perf_counter() - started)
            raise
        self._record_success(response, model, "json", started)
        return content

    def _record_success(self, response: Any, model: str, mode: str, started: float) -> None:
        usage = response.usage
        record_llm_call(
            "openai",
            model,
            mode,
            "success",
            perf_counter() - started,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )
