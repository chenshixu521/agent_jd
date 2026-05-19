from pathlib import Path
from typing import Any

from loguru import logger

from app.core.settings import settings
from app.rag.embedding_api import EmbeddingProvider, get_embedding_provider
from app.rag.prompt_enhancer import PromptEnhancer
from app.rag.schema import KnowledgeDoc, RagHit, SUPPORTED_KBS
from app.rag.splitter import split_documents
from app.rag.vectorstore import FaissStore


class RagService:
    def __init__(self, root: Path | None = None, embedder: EmbeddingProvider | None = None):
        self.root = root or settings.faiss_dir
        self.embedder = embedder or get_embedding_provider()
        self.prompt_enhancer = PromptEnhancer()
        self._stores: dict[str, FaissStore] = {}

    def store(self, kb: str) -> FaissStore:
        self._validate_kb(kb)
        if kb not in self._stores:
            self._stores[kb] = FaissStore(kb, self.root, self.embedder)
        return self._stores[kb]

    def add_documents(self, docs: list[KnowledgeDoc], chunk_size: int = 500, overlap: int = 50) -> dict[str, int]:
        grouped: dict[str, list[KnowledgeDoc]] = {}
        for doc in docs:
            self._validate_kb(doc.kb)
            grouped.setdefault(doc.kb, []).append(doc)
        result: dict[str, int] = {}
        for kb, kb_docs in grouped.items():
            chunks = split_documents(kb_docs, chunk_size=chunk_size, overlap=overlap)
            ids = self.store(kb).add(chunks)
            result[kb] = len(ids)
            logger.info(f"RAG indexed kb={kb} docs={len(kb_docs)} chunks={len(ids)}")
        return result

    async def aadd_documents(self, docs: list[KnowledgeDoc], chunk_size: int = 500, overlap: int = 50) -> dict[str, int]:
        grouped: dict[str, list[KnowledgeDoc]] = {}
        for doc in docs:
            self._validate_kb(doc.kb)
            grouped.setdefault(doc.kb, []).append(doc)
        result: dict[str, int] = {}
        for kb, kb_docs in grouped.items():
            chunks = split_documents(kb_docs, chunk_size=chunk_size, overlap=overlap)
            ids = await self.store(kb).aadd(chunks)
            result[kb] = len(ids)
            logger.info(f"RAG indexed async kb={kb} docs={len(kb_docs)} chunks={len(ids)}")
        return result

    def search(self, query: str, kb: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        self._validate_kb(kb)
        return self.store(kb).search(query, top_k=top_k, filters=filters)

    async def asearch(self, query: str, kb: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        self._validate_kb(kb)
        return await self.store(kb).asearch(query, top_k=top_k, filters=filters)

    def search_multi(self, query: str, kbs: list[str], top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        hits: list[RagHit] = []
        per_kb = max(top_k, 3)
        for kb in kbs:
            hits.extend(self.search(query, kb=kb, top_k=per_kb, filters=filters))
        hits.sort(key=lambda item: item.score, reverse=True)
        return self._dedup(hits)[:top_k]

    async def asearch_multi(self, query: str, kbs: list[str], top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        hits: list[RagHit] = []
        per_kb = max(top_k, 3)
        for kb in kbs:
            hits.extend(await self.asearch(query, kb=kb, top_k=per_kb, filters=filters))
        hits.sort(key=lambda item: item.score, reverse=True)
        return self._dedup(hits)[:top_k]

    def recall_for_job(self, query: str, top_k: int = 5) -> list[RagHit]:
        return self.search_multi(query, ["jd", "skill_keyword", "interview_question"], top_k=top_k)

    def recall_for_project(self, query: str, top_k: int = 5) -> list[RagHit]:
        return self.search_multi(query, ["project_template", "skill_keyword", "interview_question"], top_k=top_k)

    def recall_for_greeting(self, query: str, top_k: int = 5) -> list[RagHit]:
        return self.search_multi(query, ["greeting_template", "jd"], top_k=top_k)

    def build_prompt_context(self, query: str, kbs: list[str], top_k: int = 5) -> str:
        hits = self.search_multi(query, kbs=kbs, top_k=top_k)
        return self.prompt_enhancer.build_context(query, hits)

    async def abuild_prompt_context(self, query: str, kbs: list[str], top_k: int = 5) -> str:
        hits = await self.asearch_multi(query, kbs=kbs, top_k=top_k)
        return self.prompt_enhancer.build_context(query, hits)

    def enhance_messages(self, messages: list[dict[str, str]], query: str, kbs: list[str], top_k: int = 5) -> list[dict[str, str]]:
        hits = self.search_multi(query, kbs=kbs, top_k=top_k)
        return self.prompt_enhancer.enhance_messages(messages, query, hits)

    def _validate_kb(self, kb: str) -> None:
        if kb not in SUPPORTED_KBS:
            raise ValueError(f"Unsupported knowledge base: {kb}")

    def _dedup(self, hits: list[RagHit]) -> list[RagHit]:
        seen = set()
        result: list[RagHit] = []
        for hit in hits:
            key = (hit.kb, hit.doc_id, hit.text[:80])
            if key in seen:
                continue
            seen.add(key)
            result.append(hit)
        return result


_default_service: RagService | None = None


def get_rag_service() -> RagService:
    global _default_service
    if _default_service is None:
        _default_service = RagService()
    return _default_service
