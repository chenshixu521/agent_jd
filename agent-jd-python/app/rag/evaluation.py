from dataclasses import dataclass
from math import log2
from typing import Any, Protocol

from app.rag.schema import RagHit


class SearchService(Protocol):
    def search_multi(self, query: str, kbs: list[str], top_k: int = 5) -> list[RagHit]: ...


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    kbs: list[str]
    relevant_doc_ids: set[str]


def evaluate_retrieval(service: SearchService, cases: list[RetrievalCase]) -> dict[str, Any]:
    if not cases:
        return {
            "queries": 0,
            "recall_at_3": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "ndcg_at_5": 0.0,
            "details": [],
        }

    recall_at_3 = 0.0
    recall_at_5 = 0.0
    reciprocal_rank = 0.0
    ndcg_at_5 = 0.0
    details = []
    for case in cases:
        hits = service.search_multi(case.query, kbs=case.kbs, top_k=5)
        retrieved = _unique_doc_ids(hits)
        recall3 = _recall(retrieved[:3], case.relevant_doc_ids)
        recall5 = _recall(retrieved[:5], case.relevant_doc_ids)
        rr = _reciprocal_rank(retrieved, case.relevant_doc_ids)
        ndcg5 = _ndcg(retrieved, case.relevant_doc_ids, 5)
        recall_at_3 += recall3
        recall_at_5 += recall5
        reciprocal_rank += rr
        ndcg_at_5 += ndcg5
        details.append(
            {
                "query": case.query,
                "expected": sorted(case.relevant_doc_ids),
                "retrieved": retrieved,
                "recall_at_3": round(recall3, 4),
                "recall_at_5": round(recall5, 4),
                "reciprocal_rank": round(rr, 4),
                "ndcg_at_5": round(ndcg5, 4),
            }
        )

    size = len(cases)
    return {
        "queries": size,
        "recall_at_3": round(recall_at_3 / size, 4),
        "recall_at_5": round(recall_at_5 / size, 4),
        "mrr": round(reciprocal_rank / size, 4),
        "ndcg_at_5": round(ndcg_at_5 / size, 4),
        "details": details,
    }


def _unique_doc_ids(hits: list[RagHit]) -> list[str]:
    result = []
    seen = set()
    for hit in hits:
        if hit.doc_id in seen:
            continue
        seen.add(hit.doc_id)
        result.append(hit.doc_id)
    return result


def _recall(retrieved: list[str], relevant: set[str]) -> float:
    return len(set(retrieved) & relevant) / len(relevant) if relevant else 0.0


def _reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def _ndcg(retrieved: list[str], relevant: set[str], top_k: int) -> float:
    if not relevant:
        return 0.0
    dcg = sum(1.0 / log2(rank + 1) for rank, doc_id in enumerate(retrieved[:top_k], start=1) if doc_id in relevant)
    ideal_hits = min(len(relevant), top_k)
    ideal_dcg = sum(1.0 / log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / ideal_dcg if ideal_dcg else 0.0
