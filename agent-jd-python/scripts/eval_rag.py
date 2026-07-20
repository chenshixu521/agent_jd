import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.rag.embedding_api import HashEmbeddingProvider, SentenceTransformerEmbeddingProvider
from app.rag.evaluation import RetrievalCase, evaluate_retrieval
from app.rag.service import RagService
from scripts.import_knowledge import load_jsonl


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["hash", "sentence_transformers"], default="hash")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--seed", default="seed/knowledge.jsonl")
    parser.add_argument("--dataset", default="eval/rag_dataset.jsonl")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    embedder = (
        HashEmbeddingProvider()
        if args.provider == "hash"
        else SentenceTransformerEmbeddingProvider(model=args.model)
    )
    with TemporaryDirectory(prefix="agent-jd-rag-eval-") as temp_dir:
        service = RagService(root=Path(temp_dir), embedder=embedder)
        service.add_documents(load_jsonl(Path(args.seed)))
        result = evaluate_retrieval(service, load_cases(Path(args.dataset)))

    summary = {key: value for key, value in result.items() if key != "details"}
    summary["provider"] = args.provider
    summary["model"] = args.model if args.provider == "sentence_transformers" else "hash-baseline"
    if args.details:
        summary["details"] = result["details"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
