from typing import Any
from time import perf_counter
import json

import httpx

from app.core.settings import settings
from app.core.metrics import record_llm_call
from app.llm.base import LLMProvider


class DashScopeProvider(LLMProvider):
    def __init__(self) -> None:
        self.api_key = settings.dashscope_api_key
        self.model = settings.dashscope_model

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        return await self._completion(messages, "chat", kwargs)

    async def json_mode(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        return await self._completion(messages, "json", kwargs)

    async def _completion(self, messages: list[dict[str, str]], mode: str, kwargs: dict[str, Any]) -> Any:
        model = kwargs.get("model", self.model)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }
        if kwargs.get("max_tokens") is not None:
            payload["max_tokens"] = kwargs.get("max_tokens")
        started = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content) if mode == "json" else content
        except Exception:
            record_llm_call("dashscope", model, mode, "failed", perf_counter() - started)
            raise

        usage = data.get("usage", {})
        record_llm_call(
            "dashscope",
            model,
            mode,
            "success",
            perf_counter() - started,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )
        return result
