# Agent JD Load Test Baseline

Generated: 2026-07-21T11:16:59.912621+00:00

## Scope

This is a deterministic infrastructure baseline using the Fake LLM. It measures Nginx, Java, MySQL, Redis Stream, Python Agent, task polling, and persistence. It does not represent real model throughput or production capacity.

## Configuration

- Concurrent users: 5
- Duration: 30s
- Fake LLM delay: 100 ms
- Scenario: submit a match-analysis task and poll until SUCCESS

## Results

| Metric | Result |
| --- | ---: |
| Completed task workflows | 130 |
| Task success rate | 100.00% |
| Task end-to-end P50 | 1100.00 ms |
| Task end-to-end P95 | 1200.00 ms |
| Task average | 1038.56 ms |
| HTTP requests | 1537 |
| HTTP request P95 | 15.00 ms |
| HTTP failure rate | 0.00% |

## Interpretation

The run fails when request failures reach 1% or task P95 reaches 5 seconds. Re-run on the target machine before quoting these numbers, and retain the Fake LLM limitation when describing the result.
