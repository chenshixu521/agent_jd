from prometheus_client import REGISTRY
import pytest

from app.core.metrics import record_agent_request, record_llm_call
from app.core.settings import settings
from app.main import metrics


def sample(name: str, labels: dict[str, str]) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_records_agent_and_llm_metrics_with_estimated_cost(monkeypatch):
    agent_labels = {"capability": "match", "action": "analyze", "outcome": "success"}
    llm_labels = {"provider": "test-provider", "model": "test-model", "mode": "json", "outcome": "success"}
    cost_labels = {"provider": "test-provider", "model": "test-model"}
    before_agent = sample("agent_jd_agent_requests_total", agent_labels)
    before_llm = sample("agent_jd_llm_requests_total", llm_labels)
    before_cost = sample("agent_jd_llm_cost_usd_total", cost_labels)
    monkeypatch.setattr(settings, "llm_input_cost_per_million_usd", 1.0)
    monkeypatch.setattr(settings, "llm_output_cost_per_million_usd", 2.0)

    record_agent_request("match", "analyze", "success", 0.25)
    record_llm_call(
        "test-provider",
        "test-model",
        "json",
        "success",
        0.2,
        prompt_tokens=100,
        completion_tokens=50,
    )

    assert sample("agent_jd_agent_requests_total", agent_labels) - before_agent == 1
    assert sample("agent_jd_llm_requests_total", llm_labels) - before_llm == 1
    assert sample("agent_jd_llm_cost_usd_total", cost_labels) - before_cost == pytest.approx(0.0002)


def test_negative_prices_do_not_break_metrics_or_decrease_cost(monkeypatch):
    labels = {"provider": "test-provider", "model": "negative-price", "mode": "chat", "outcome": "success"}
    cost_labels = {"provider": "test-provider", "model": "negative-price"}
    before_requests = sample("agent_jd_llm_requests_total", labels)
    before_cost = sample("agent_jd_llm_cost_usd_total", cost_labels)
    monkeypatch.setattr(settings, "llm_input_cost_per_million_usd", -1.0)
    monkeypatch.setattr(settings, "llm_output_cost_per_million_usd", -2.0)

    record_llm_call(
        "test-provider",
        "negative-price",
        "chat",
        "success",
        0.1,
        prompt_tokens=100,
        completion_tokens=50,
    )

    assert sample("agent_jd_llm_requests_total", labels) - before_requests == 1
    assert sample("agent_jd_llm_cost_usd_total", cost_labels) - before_cost == 0


async def test_metrics_endpoint_exposes_prometheus_payload():
    response = await metrics()

    assert response.status_code == 200
    assert b"agent_jd_agent_requests_total" in response.body
