from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocIn(BaseModel):
    kb: str
    doc_id: str = Field(alias="docId")
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class RagIndexRequest(BaseModel):
    docs: list[KnowledgeDocIn]
    chunk_size: int = Field(default=500, alias="chunkSize")
    overlap: int = 50

    model_config = {"populate_by_name": True}


class RagSearchRequest(BaseModel):
    query: str
    kbs: list[str]
    top_k: int = Field(default=5, alias="topK")
    filters: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}
