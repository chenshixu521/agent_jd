# Evaluation Report

Generated at: `2026-07-21T12:02:37+00:00`

## Datasets

- Held-out retrieval corpus: 10 documents
- Manually labeled retrieval set: 20 queries
- Structured match set: 20 resume/JD pairs

The held-out retrieval corpus is not imported into the running application and is separate from `seed/`.

## Retrieval

| Provider / Model | Mode | Recall@3 | Recall@5 | MRR | nDCG@5 |
| --- | --- | ---: | ---: | ---: | ---: |
| hash / hash-baseline | vector | 0.5500 | 0.6500 | 0.4867 | 0.5228 |
| hash / hash-baseline | hybrid | 0.8500 | 0.9500 | 0.7058 | 0.7671 |
| sentence_transformers / BAAI/bge-small-zh-v1.5 | vector | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| sentence_transformers / BAAI/bge-small-zh-v1.5 | hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Hybrid Minus Vector-Only

| Provider / Model | Recall@3 | Recall@5 | MRR | nDCG@5 |
| --- | ---: | ---: | ---: | ---: |
| hash / hash-baseline | +0.3000 | +0.3000 | +0.2191 | +0.2443 |
| sentence_transformers / BAAI/bge-small-zh-v1.5 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |

## Structured Match

Provider / model: `fake / deterministic`

| Metric | Result |
| --- | ---: |
| Structured output success rate | 1.0000 |
| Skill label exact match rate | 1.0000 |
| Grounded skill claim rate | 1.0000 |
| Evidence coverage rate | 1.0000 |

## Limitations

- The held-out datasets are small, manually constructed, and separate from the runtime seed corpus.
- Hash embedding is a deterministic regression baseline, not a semantic model quality result.
- BGE saturates this small benchmark, so its scores do not establish a hybrid or reranker uplift.
- Structured matching uses a Fake LLM and measures schema, skill labels, and skill evidence only.
- Free-text summaries and suggestions are not covered by the faithfulness metric.
