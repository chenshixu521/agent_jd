# Evaluation datasets

- `rag_dataset.jsonl` uses the runtime seed corpus and remains a development regression set.
- `heldout_knowledge.jsonl` and `heldout_rag_dataset.jsonl` form a separate, manually labeled retrieval benchmark. They are not imported into the running application.
- `agent_match_dataset.jsonl` contains independent resume/JD pairs with expected matched and missing skills for structured-output evaluation.

The held-out data is small and manually constructed. It supports reproducible local comparison, not claims about production traffic or general model quality. The structured grounding metric covers matched/missing skill claims and their evidence only; it does not score the factual correctness of free-text summaries or suggestions.

Run the reproducible suite from `agent-jd-python/`:

```bash
# Hash vector/hybrid comparison + deterministic structured-match evaluation
python -m scripts.eval_suite

# Also run the local Chinese embedding model
python -m scripts.eval_suite --include-bge
```

The suite writes compact, reviewable results to `reports/evaluation.json` and `reports/evaluation.md`. Use `scripts.eval_rag --details` or `scripts.eval_agent --details` to inspect per-case results.
