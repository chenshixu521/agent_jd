import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from app.rag.embedding_api import HashEmbeddingProvider, SentenceTransformerEmbeddingProvider
from app.rag.evaluation import RetrievalCase, evaluate_retrieval
from app.rag.schema import RagHit
from app.rag.service import RagService
from scripts.import_knowledge import load_jsonl


class VectorOnlySearchService:
    def __init__(self, service: RagService):
        self.service = service

    def search_multi(self, query: str, kbs: list[str], top_k: int = 5) -> list[RagHit]:
        hits: list[RagHit] = []
        per_kb = max(top_k * 2, 6)
        for kb in kbs:
            hits.extend(self.service.search(query, kb=kb, top_k=per_kb))
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]


def load_cases(path: Path) -> list[RetrievalCase]:
    cases = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            item = json.loads(line)
            cases.append(
                RetrievalCase(
                    query=item["query"],
                    kbs=item["kbs"],
                    relevant_doc_ids=set(item["relevant_doc_ids"]),
                )
            )
    return cases


def evaluate_configurations(
    provider: str,
    model: str,
    corpus: Path,
    dataset: Path,
    modes: list[str],
) -> list[dict[str, Any]]:
    embedder = HashEmbeddingProvider() if provider == "hash" else SentenceTransformerEmbeddingProvider(model=model)
    with TemporaryDirectory(prefix="agent-jd-rag-eval-") as temp_dir:
        service = RagService(root=Path(temp_dir), embedder=embedder)
        service.add_documents(load_jsonl(corpus))
        cases = load_cases(dataset)
        results = []
        for mode in modes:
            search_service = service if mode == "hybrid" else VectorOnlySearchService(service)
            result = evaluate_retrieval(search_service, cases)
            result.update(
                {
                    "provider": provider,
                    "model": model if provider == "sentence_transformers" else "hash-baseline",
                    "mode": mode,
                }
            )
            results.append(result)
        return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["hash", "sentence_transformers"], default="hash")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--seed", default="seed/knowledge.jsonl")
    parser.add_argument("--dataset", default="eval/rag_dataset.jsonl")
    parser.add_argument("--mode", choices=["vector", "hybrid"], default="hybrid")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    result = evaluate_configurations(
        provider=args.provider,
        model=args.model,
        corpus=Path(args.seed),
        dataset=Path(args.dataset),
        modes=[args.mode],
    )[0]
    if not args.details:
        result = {key: value for key, value in result.items() if key != "details"}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
