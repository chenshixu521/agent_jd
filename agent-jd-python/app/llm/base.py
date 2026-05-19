from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    async def json_mode(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError
