import asyncio
from abc import ABC, abstractmethod
from typing import Any

import httpx
import numpy as np
from openai import AsyncOpenAI

from app.core.settings import settings
from app.rag.embedder import HashEmbedder


class EmbeddingProvider(ABC):
    dim: int

    @abstractmethod
    async def aembed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dim: int = 384):
        self.dim = dim
        self._embedder = HashEmbedder(dim)

    async def aembed(self, texts: list[str]) -> np.ndarray:
        return self.embed(texts)

    def embed(self, texts: list[str]) -> np.ndarray:
        return self._embedder.embed(texts)


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str | None = None):
        from sentence_transformers import SentenceTransformer

        self.model_name = model or settings.embedding_model
        self._model = SentenceTransformer(self.model_name)
        dimension = self._model.get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError(f"无法识别 Embedding 模型维度: {self.model_name}")
        self.dim = int(dimension)

    async def aembed(self, texts: list[str]) -> np.ndarray:
        return await asyncio.to_thread(self.embed, texts)

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype="float32")


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str | None = None, dim: int | None = None):
        self.model = model or settings.embedding_model
        self.dim = dim or settings.embedding_dimension
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    async def aembed(self, texts: list[str]) -> np.ndarray:
        response = await self.client.embeddings.create(model=self.model, input=texts)
        vectors = [item.embedding for item in response.data]
        return _normalize(np.array(vectors, dtype="float32"))

    def embed(self, texts: list[str]) -> np.ndarray:
        raise RuntimeError("OpenAIEmbeddingProvider only supports async embedding")


class DashScopeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str | None = None, dim: int | None = None):
        self.model = model or settings.embedding_model
        self.dim = dim or settings.embedding_dimension
        self.api_key = settings.dashscope_api_key

    async def aembed(self, texts: list[str]) -> np.ndarray:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "input": {"texts": texts}},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            vectors = [item["embedding"] for item in data["output"]["embeddings"]]
            return _normalize(np.array(vectors, dtype="float32"))

    def embed(self, texts: list[str]) -> np.ndarray:
        raise RuntimeError("DashScopeEmbeddingProvider only supports async embedding")


def get_embedding_provider() -> EmbeddingProvider:
    provider = getattr(settings, "embedding_provider", "hash")
    if provider == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider()
    if provider == "openai" and settings.openai_api_key:
        return OpenAIEmbeddingProvider()
    if provider == "dashscope" and settings.dashscope_api_key:
        return DashScopeEmbeddingProvider()
    if provider == "hash":
        return HashEmbeddingProvider()
    raise RuntimeError(f"Unsupported or incorrectly configured EMBEDDING_PROVIDER: {provider}")


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype("float32")
