from app.rag.evaluation import RetrievalCase, evaluate_retrieval
from app.rag.schema import RagHit


class StubSearchService:
    def search_multi(self, query: str, kbs: list[str], top_k: int = 5) -> list[RagHit]:
        return [
            RagHit(kb="jd", doc_id="irrelevant", chunk_id="1", text="", score=1.0),
            RagHit(kb="jd", doc_id="expected", chunk_id="2", text="", score=0.9),
        ]


def test_evaluate_retrieval_calculates_recall_and_mrr():
    result = evaluate_retrieval(
        StubSearchService(),
        [RetrievalCase(query="query", kbs=["jd"], relevant_doc_ids={"expected"})],
    )

    assert result["recall_at_3"] == 1.0
    assert result["recall_at_5"] == 1.0
    assert result["mrr"] == 0.5
