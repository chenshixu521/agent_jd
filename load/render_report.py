from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    summary_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])
    users = sys.argv[3]
    duration = sys.argv[4]
    fake_delay = sys.argv[5]
    rows = json.loads(summary_path.read_text(encoding="utf-8"))

    task = find(rows, "TASK", "match task end-to-end")
    http_rows = [row for row in rows if row.get("method") != "TASK"]
    request_count = integer(task, "num_requests")
    failure_count = integer(task, "num_failures")
    success_rate = 0.0 if request_count == 0 else 100 * (request_count - failure_count) / request_count
    http_request_count = sum(integer(row, "num_requests") for row in http_rows)
    http_failure_count = sum(integer(row, "num_failures") for row in http_rows)
    http_failure_rate = 0.0 if http_request_count == 0 else 100 * http_failure_count / http_request_count
    http_response_times = combine_response_times(http_rows)
    report = f"""# Agent JD Load Test Baseline

Generated: {datetime.now(timezone.utc).isoformat()}

## Scope

This is a deterministic infrastructure baseline using the Fake LLM. It measures Nginx, Java, MySQL, Redis Stream, Python Agent, task polling, and persistence. It does not represent real model throughput or production capacity.

## Configuration

- Concurrent users: {users}
- Duration: {duration}
- Fake LLM delay: {fake_delay} ms
- Scenario: submit a match-analysis task and poll until SUCCESS

## Results

| Metric | Result |
| --- | ---: |
| Completed task workflows | {request_count} |
| Task success rate | {success_rate:.2f}% |
| Task end-to-end P50 | {percentile(task, 0.50):.2f} ms |
| Task end-to-end P95 | {percentile(task, 0.95):.2f} ms |
| Task average | {average(task):.2f} ms |
| HTTP requests | {http_request_count} |
| HTTP request P95 | {response_time_percentile(http_response_times, http_request_count, 0.95):.2f} ms |
| HTTP failure rate | {http_failure_rate:.2f}% |

## Interpretation

The run fails when request failures reach 1% or task P95 reaches 5 seconds. Re-run on the target machine before quoting these numbers, and retain the Fake LLM limitation when describing the result.
"""
    report_path.write_text(report, encoding="utf-8")


def find(rows: list[dict], row_type: str, name: str) -> dict:
    for row in rows:
        if row.get("method", "") == row_type and row.get("name") == name:
            return row
    raise RuntimeError(f"Missing Locust stats row: type={row_type!r}, name={name!r}")


def number(row: dict, key: str) -> float:
    return float(row.get(key, 0) or 0)


def integer(row: dict, key: str) -> int:
    return int(number(row, key))


def average(row: dict) -> float:
    count = integer(row, "num_requests")
    return 0.0 if count == 0 else number(row, "total_response_time") / count


def percentile(row: dict, percent: float) -> float:
    return response_time_percentile(response_times(row), integer(row, "num_requests"), percent)


def response_times(row: dict) -> Counter[float]:
    return Counter({float(key): int(value) for key, value in row.get("response_times", {}).items()})


def combine_response_times(rows: list[dict]) -> Counter[float]:
    combined: Counter[float] = Counter()
    for row in rows:
        combined.update(response_times(row))
    return combined


def response_time_percentile(response_time_counts: Counter[float], request_count: int, percent: float) -> float:
    if request_count == 0:
        return 0.0
    threshold = int(request_count * percent)
    processed = 0
    for response_time in sorted(response_time_counts, reverse=True):
        processed += response_time_counts[response_time]
        if request_count - processed <= threshold:
            return float(response_time)
    return 0.0


if __name__ == "__main__":
    main()
