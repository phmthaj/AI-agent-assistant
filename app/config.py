import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    short_term_memory_ttl_seconds: int
    short_term_memory_max_messages: int
    openai_api_base: str
    openai_api_key: str
    openai_model: str
    llm_max_tokens: int
    agent_max_steps: int
    sql_echo: bool


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_agent",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        short_term_memory_ttl_seconds=_get_int(
            "SHORT_TERM_MEMORY_TTL_SECONDS",
            3600,
        ),
        short_term_memory_max_messages=_get_int(
            "SHORT_TERM_MEMORY_MAX_MESSAGES",
            12,
        ),
        openai_api_base=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:8000/v1"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "dummy"),
        openai_model=os.getenv("OPENAI_MODEL", "Qwen/Qwen3-4B"),
        llm_max_tokens=_get_int("LLM_MAX_TOKENS", 2048),
        agent_max_steps=_get_int("AGENT_MAX_STEPS", 6),
        sql_echo=_get_bool("SQL_ECHO", False),
    )
