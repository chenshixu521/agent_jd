from dataclasses import dataclass, field
from typing import Any


SUPPORTED_KBS = {
    "jd",
    "project_template",
    "skill_keyword",
    "interview_question",
    "greeting_template",
    "resume_corpus",
}


@dataclass(frozen=True)
class KnowledgeDoc:
    kb: str
    doc_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagChunk:
    kb: str
    doc_id: str
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagHit:
    kb: str
    doc_id: str
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
