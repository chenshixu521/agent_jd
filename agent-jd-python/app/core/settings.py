from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "agent-jd-python"
    app_env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    internal_token: str = "<shared-internal-token>"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 180.0
    dashscope_api_key: str | None = None
    dashscope_model: str = "qwen-plus"
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimension: int = 512
    faiss_dir: Path = Path("./data/faiss_index")
    prompt_dir: Path = Path("./app/prompts/templates")
    rag_rrf_k: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
