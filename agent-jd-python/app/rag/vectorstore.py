import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from app.rag.embedding_api import EmbeddingProvider, HashEmbeddingProvider
from app.rag.bm25 import Bm25Index
from app.rag.schema import RagChunk, RagHit


class FaissStore:
    def __init__(self, name: str, root: Path, embedder: EmbeddingProvider | None = None):
        self.name = name
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / f"{name}.index"
        self.meta_path = self.root / f"{name}.meta.json"
        self.embedder = embedder or HashEmbeddingProvider()
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.embedder.dim))
        self.meta: dict[int, dict[str, Any]] = {}
        self._load()

    def add(self, chunks: list[RagChunk | dict[str, Any]]) -> list[int]:
        if not chunks:
            return []
        normalized = [self._normalize_chunk(chunk) for chunk in chunks]
        embeddings = self.embedder.embed([chunk["text"] for chunk in normalized])
        return self._add_normalized(normalized, embeddings)

    async def aadd(self, chunks: list[RagChunk | dict[str, Any]]) -> list[int]:
        if not chunks:
            return []
        normalized = [self._normalize_chunk(chunk) for chunk in chunks]
        embeddings = await self.embedder.aembed([chunk["text"] for chunk in normalized])
        return self._add_normalized(normalized, embeddings)

    def _add_normalized(self, normalized: list[dict[str, Any]], embeddings: np.ndarray) -> list[int]:
        self._remove_replaced_documents(normalized)
        start_id = max(self.meta.keys(), default=0) + 1
        ids = np.array([start_id + i for i in range(len(normalized))], dtype="int64")
        self.index.add_with_ids(embeddings, ids)
        for vector_id, chunk in zip(ids.tolist(), normalized):
            self.meta[vector_id] = chunk
        self.persist()
        return ids.tolist()

    def search(self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        if self.index.ntotal == 0:
            return []
        q = self.embedder.embed([query])
        return self._search_by_vector(q, top_k=top_k, filters=filters)

    async def asearch(self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        if self.index.ntotal == 0:
            return []
        q = await self.embedder.aembed([query])
        return self._search_by_vector(q, top_k=top_k, filters=filters)

    def lexical_search(self, query: str, top_k: int = 5, filters: dict[str, Any] | None = None) -> list[RagHit]:
        rows = [
            (vector_id, item)
            for vector_id, item in sorted(self.meta.items())
            if self._match_filters(item.get("metadata", {}), filters)
        ]
        if not rows:
            return []
        index = Bm25Index([item.get("text", "") for _, item in rows])
        results = []
        for row_index, score in index.search(query, top_k=top_k):
            vector_id, item = rows[row_index]
            results.append(
                RagHit(
                    kb=item.get("kb", self.name),
                    doc_id=item.get("doc_id", str(vector_id)),
                    chunk_id=item.get("chunk_id", str(vector_id)),
                    text=item.get("text", ""),
                    score=score,
                    metadata={**item.get("metadata", {}), "bm25_score": score},
                )
            )
        return results

    def _search_by_vector(self, q: np.ndarray, top_k: int, filters: dict[str, Any] | None = None) -> list[RagHit]:
        fetch_k = min(max(top_k * 4, top_k), self.index.ntotal)
        scores, ids = self.index.search(q, fetch_k)
        results = []
        for score, doc_id in zip(scores[0].tolist(), ids[0].tolist()):
            if doc_id == -1:
                continue
            item = dict(self.meta.get(doc_id, {}))
            if not self._match_filters(item.get("metadata", {}), filters):
                continue
            results.append(
                RagHit(
                    kb=item.get("kb", self.name),
                    doc_id=item.get("doc_id", str(doc_id)),
                    chunk_id=item.get("chunk_id", str(doc_id)),
                    text=item.get("text", ""),
                    score=float(score),
                    metadata=item.get("metadata", {}),
                )
            )
            if len(results) >= top_k:
                break
        return results

    def persist(self) -> None:
        serialized = faiss.serialize_index(self.index)
        self.index_path.write_bytes(serialized.tobytes())
        self.meta_path.write_text(json.dumps(self.meta, ensure_ascii=False), encoding="utf-8")

    def _load(self) -> None:
        if self.index_path.exists():
            raw = np.frombuffer(self.index_path.read_bytes(), dtype="uint8")
            self.index = faiss.deserialize_index(raw)
        if self.meta_path.exists():
            raw = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self.meta = {int(k): v for k, v in raw.items()}
        if self.index.d != self.embedder.dim:
            raise ValueError(
                f"FAISS index dimension mismatch for {self.name}: index={self.index.d}, embedder={self.embedder.dim}. "
                "Rebuild the index after changing EMBEDDING_MODEL."
            )

    def _remove_replaced_documents(self, normalized: list[dict[str, Any]]) -> None:
        document_keys = {(item.get("kb", self.name), item.get("doc_id", "")) for item in normalized}
        replaced_ids = [
            vector_id
            for vector_id, item in self.meta.items()
            if (item.get("kb", self.name), item.get("doc_id", "")) in document_keys
        ]
        if not replaced_ids:
            return
        self.index.remove_ids(np.asarray(replaced_ids, dtype="int64"))
        for vector_id in replaced_ids:
            self.meta.pop(vector_id, None)

    def _normalize_chunk(self, chunk: RagChunk | dict[str, Any]) -> dict[str, Any]:
        if isinstance(chunk, RagChunk):
            return {
                "kb": chunk.kb,
                "doc_id": chunk.doc_id,
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
        return {
            "kb": chunk.get("kb", self.name),
            "doc_id": chunk.get("doc_id", chunk.get("id", "")),
            "chunk_id": chunk.get("chunk_id", chunk.get("id", "")),
            "text": chunk["text"],
            "metadata": chunk.get("metadata", {}),
        }

    def _match_filters(self, metadata: dict[str, Any], filters: dict[str, Any] | None) -> bool:
        if not filters:
            return True
        return all(metadata.get(key) == value for key, value in filters.items())
