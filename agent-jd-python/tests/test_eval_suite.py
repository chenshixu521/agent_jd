from scripts.eval_suite import _retrieval_comparisons, render_markdown


def test_retrieval_comparisons_calculates_hybrid_delta():
    vector = {
        "provider": "hash",
        "model": "hash-baseline",
        "mode": "vector",
        "recall_at_3": 0.5,
        "recall_at_5": 0.6,
        "mrr": 0.4,
        "ndcg_at_5": 0.45,
    }
    hybrid = {
        **vector,
        "mode": "hybrid",
        "recall_at_3": 0.8,
        "recall_at_5": 0.9,
        "mrr": 0.7,
        "ndcg_at_5": 0.75,
    }

    comparison = _retrieval_comparisons([vector, hybrid])[0]

    assert comparison["hybrid_minus_vector"] == {
        "recall_at_3": 0.3,
        "recall_at_5": 0.3,
        "mrr": 0.3,
        "ndcg_at_5": 0.3,
    }


def test_render_markdown_includes_retrieval_and_match_metrics():
    report = {
        "generated_at": "2026-07-21T12:00:00+00:00",
        "datasets": {
            "retrieval_corpus": {"documents": 10},
            "retrieval_queries": {"queries": 20},
            "structured_match": {"cases": 20},
        },
        "retrieval": [
            {
                "provider": "hash",
                "model": "hash-baseline",
                "mode": "hybrid",
                "recall_at_3": 0.85,
                "recall_at_5": 0.95,
                "mrr": 0.7058,
                "ndcg_at_5": 0.7671,
            }
        ],
        "retrieval_comparisons": [],
        "structured_match": {
            "provider": "fake",
            "model": "deterministic",
            "structured_output_success_rate": 1.0,
            "skill_label_exact_match_rate": 1.0,
            "grounded_skill_claim_rate": 1.0,
            "evidence_coverage_rate": 1.0,
        },
        "limitations": ["Small held-out set."],
    }

    markdown = render_markdown(report)

    assert "| hash / hash-baseline | hybrid | 0.8500 | 0.9500 | 0.7058 | 0.7671 |" in markdown
    assert "| Structured output success rate | 1.0000 |" in markdown
    assert "Small held-out set." in markdown
