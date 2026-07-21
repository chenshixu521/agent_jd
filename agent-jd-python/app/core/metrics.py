from prometheus_client import Counter, Histogram

from app.core.settings import settings

_CAPABILITIES = {"resume", "jd", "keyword", "project", "match", "greeting", "chat"}
_ACTIONS = {"optimize", "advice", "parse", "analyze", "extract", "rewrite", "generate", "message", "talk"}

AGENT_REQUESTS = Counter(
    "agent_jd_agent_requests",
    "Agent requests handled by capability, action, and outcome",
    ("capability", "action", "outcome"),
)
AGENT_REQUEST_DURATION = Histogram(
    "agent_jd_agent_request_duration_seconds",
    "Agent request duration in seconds",
    ("capability", "action", "outcome"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 180),
)
LLM_REQUESTS = Counter(
    "agent_jd_llm_requests",
    "LLM requests by provider, model, mode, and outcome",
    ("provider", "model", "mode", "outcome"),
)
LLM_REQUEST_DURATION = Histogram(
    "agent_jd_llm_request_duration_seconds",
    "LLM request duration in seconds",
    ("provider", "model", "mode", "outcome"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 180),
)
LLM_TOKENS = Counter(
    "agent_jd_llm_tokens",
    "Tokens reported by the model provider",
    ("provider", "model", "token_type"),
)
LLM_COST_USD = Counter(
    "agent_jd_llm_cost_usd",
    "Estimated LLM cost in USD using configured per-million-token prices",
    ("provider", "model"),
)


def record_agent_request(capability: str, action: str, outcome: str, duration_seconds: float) -> None:
    labels = {
        "capability": _bounded(capability, _CAPABILITIES),
        "action": _bounded(action, _ACTIONS),
        "outcome": outcome,
    }
    AGENT_REQUESTS.labels(**labels).inc()
    AGENT_REQUEST_DURATION.labels(**labels).observe(max(0.0, duration_seconds))


def record_llm_call(
    provider: str,
    model: str,
    mode: str,
    outcome: str,
    duration_seconds: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    labels = {"provider": provider, "model": model, "mode": mode, "outcome": outcome}
    LLM_REQUESTS.labels(**labels).inc()
    LLM_REQUEST_DURATION.labels(**labels).observe(max(0.0, duration_seconds))

    prompt_tokens = max(0, prompt_tokens)
    completion_tokens = max(0, completion_tokens)
    if prompt_tokens:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)
    total_tokens = prompt_tokens + completion_tokens
    if total_tokens:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="total").inc(total_tokens)

    input_price = max(0.0, settings.llm_input_cost_per_million_usd)
    output_price = max(0.0, settings.llm_output_cost_per_million_usd)
    estimated_cost = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000
    if estimated_cost:
        LLM_COST_USD.labels(provider=provider, model=model).inc(estimated_cost)


def _bounded(value: str, allowed: set[str]) -> str:
    return value if value in allowed else "other"
