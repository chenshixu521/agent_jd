from app.core.settings import settings
from app.llm.base import LLMProvider
from app.llm.dashscope_provider import DashScopeProvider
from app.llm.openai_provider import OpenAIProvider


def get_llm() -> LLMProvider:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAIProvider()
    if settings.llm_provider == "dashscope" and settings.dashscope_api_key:
        return DashScopeProvider()
    raise RuntimeError("LLM_PROVIDER must be openai or dashscope, and the matching API key must be configured")
