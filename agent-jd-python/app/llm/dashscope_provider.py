from typing import Any

import httpx

from app.core.settings import settings
from app.llm.base import LLMProvider


class DashScopeProvider(LLMProvider):
    def __init__(self) -> None:
        self.api_key = settings.dashscope_api_key
        self.model = settings.dashscope_model

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": kwargs.get("model", self.model), "messages": messages, "temperature": kwargs.get("temperature", 0.3)},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def json_mode(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        import json
        text = await self.chat(messages, **kwargs)
        return json.loads(text)
