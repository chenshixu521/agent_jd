from app.core.settings import settings
from app.llm.factory import get_llm
from app.llm.fake_provider import FakeLLMProvider


async def test_fake_provider_returns_valid_match_json(monkeypatch):
    monkeypatch.setattr(settings, "fake_llm_delay_ms", 0)

    result = await FakeLLMProvider().json_mode([])

    assert result["total_score"] == 82
    assert result["suggestions"]


async def test_fake_provider_detects_prior_chat_context(monkeypatch):
    monkeypatch.setattr(settings, "fake_llm_delay_ms", 0)
    messages = [
        {"role": "system", "content": "你是 AI 求职 Agent"},
        {"role": "user", "content": "历史对话：E2E_FIRST\n用户问题：E2E_SECOND"},
    ]

    result = await FakeLLMProvider().chat(messages)

    assert "FAKE_E2E_CONTEXT_OK" in result


def test_factory_allows_fake_provider_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "openai_api_key", None)

    assert isinstance(get_llm(), FakeLLMProvider)
