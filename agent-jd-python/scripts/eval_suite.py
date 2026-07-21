import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.eval_agent import run_agent_evaluation
from scripts.eval_rag import evaluate_configurations


METRICS = ("recall_at_3", "recall_at_5", "mrr", "ndcg_at_5")


async def run_evaluation_suite(
    corpus: Path,
    rag_dataset: Path,
    agent_dataset: Path,
    include_bge: bool,
    bge_model: str,
) -> dict[str, Any]:
    retrieval = evaluate_configurations(
        provider="hash",
        model="hash-baseline",
        corpus=corpus,
        dataset=rag_dataset,
        modes=["vector", "hybrid"],
    )
    if include_bge:
        retrieval.extend(
            evaluate_configurations(
                provider="sentence_transformers",
                model=bge_model,
                corpus=corpus,
                dataset=rag_dataset,
                modes=["vector", "hybrid"],
            )
        )

    structured_match = await run_agent_evaluation(agent_dataset, provider="fake")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "datasets": {
            "retrieval_corpus": {"path": str(corpus), "documents": _jsonl_size(corpus)},
            "retrieval_queries": {"path": str(rag_dataset), "queries": _jsonl_size(rag_dataset)},
            "structured_match": {"path": str(agent_dataset), "cases": _jsonl_size(agent_dataset)},
        },
        "retrieval": [_without_details(item) for item in retrieval],
        "retrieval_comparisons": _retrieval_comparisons(retrieval),
        "structured_match": _without_details(structured_match),
        "limitations": [
            "The held-out datasets are small, manually constructed, and separate from the runtime seed corpus.",
            "Hash embedding is a deterministic regression baseline, not a semantic model quality result.",
            "BGE saturates this small benchmark, so its scores do not establish a hybrid or reranker uplift.",
            "Structured matching uses a Fake LLM and measures schema, skill labels, and skill evidence only.",
            "Free-text summaries and suggestions are not covered by the faithfulness metric.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    datasets = report["datasets"]
    retrieval_rows = [
        "| Provider / Model | Mode | Recall@3 | Recall@5 | MRR | nDCG@5 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["retrieval"]:
        retrieval_rows.append(
            f"| {item['provider']} / {item['model']} | {item['mode']} | "
            f"{item['recall_at_3']:.4f} | {item['recall_at_5']:.4f} | "
            f"{item['mrr']:.4f} | {item['ndcg_at_5']:.4f} |"
        )

    comparison_rows = [
        "| Provider / Model | Recall@3 | Recall@5 | MRR | nDCG@5 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["retrieval_comparisons"]:
        delta = item["hybrid_minus_vector"]
        comparison_rows.append(
            f"| {item['provider']} / {item['model']} | "
            f"{delta['recall_at_3']:+.4f} | {delta['recall_at_5']:+.4f} | "
            f"{delta['mrr']:+.4f} | {delta['ndcg_at_5']:+.4f} |"
        )

    match = report["structured_match"]
    limitation_lines = "\n".join(f"- {item}" for item in report["limitations"])
    return (
        "# Evaluation Report\n\n"
        f"Generated at: `{report['generated_at']}`\n\n"
        "## Datasets\n\n"
        f"- Held-out retrieval corpus: {datasets['retrieval_corpus']['documents']} documents\n"
        f"- Manually labeled retrieval set: {datasets['retrieval_queries']['queries']} queries\n"
        f"- Structured match set: {datasets['structured_match']['cases']} resume/JD pairs\n\n"
        "The held-out retrieval corpus is not imported into the running application and is separate from `seed/`.\n\n"
        "## Retrieval\n\n"
        + "\n".join(retrieval_rows)
        + "\n\n## Hybrid Minus Vector-Only\n\n"
        + "\n".join(comparison_rows)
        + "\n\n## Structured Match\n\n"
        f"Provider / model: `{match['provider']} / {match['model']}`\n\n"
        "| Metric | Result |\n"
        "| --- | ---: |\n"
        f"| Structured output success rate | {match['structured_output_success_rate']:.4f} |\n"
        f"| Skill label exact match rate | {match['skill_label_exact_match_rate']:.4f} |\n"
        f"| Grounded skill claim rate | {match['grounded_skill_claim_rate']:.4f} |\n"
        f"| Evidence coverage rate | {match['evidence_coverage_rate']:.4f} |\n\n"
        "## Limitations\n\n"
        f"{limitation_lines}\n"
    )


def write_reports(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evaluation.json"
    markdown_path = output_dir / "evaluation.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _retrieval_comparisons(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for item in results:
        grouped.setdefault((item["provider"], item["model"]), {})[item["mode"]] = item

    comparisons = []
    for (provider, model), modes in grouped.items():
        if "vector" not in modes or "hybrid" not in modes:
            continue
        comparisons.append(
            {
                "provider": provider,
                "model": model,
                "hybrid_minus_vector": {
                    metric: round(modes["hybrid"][metric] - modes["vector"][metric], 4) for metric in METRICS
                },
            }
        )
    return comparisons


def _without_details(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key != "details"}


def _jsonl_size(path: Path) -> int:
    with path.open("r", encoding="utf-8") as source:
        return sum(1 for line in source if line.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="eval/heldout_knowledge.jsonl")
    parser.add_argument("--rag-dataset", default="eval/heldout_rag_dataset.jsonl")
    parser.add_argument("--agent-dataset", default="eval/agent_match_dataset.jsonl")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--include-bge", action="store_true")
    parser.add_argument("--bge-model", default="BAAI/bge-small-zh-v1.5")
    args = parser.parse_args()

    report = asyncio.run(
        run_evaluation_suite(
            corpus=Path(args.corpus),
            rag_dataset=Path(args.rag_dataset),
            agent_dataset=Path(args.agent_dataset),
            include_bge=args.include_bge,
            bge_model=args.bge_model,
        )
    )
    json_path, markdown_path = write_reports(report, Path(args.output_dir))
    print(f"Wrote {json_path} and {markdown_path}")


if __name__ == "__main__":
    main()
