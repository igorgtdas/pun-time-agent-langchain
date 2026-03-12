from dataclasses import dataclass
import os


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


def _is_truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class AppConfig:
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_timeout: int
    llm_max_tokens: int
    llm_top_p: float
    llm_frequency_penalty: float
    llm_presence_penalty: float
    enable_langsmith: bool
    enable_json_logs: bool


def load_config() -> AppConfig:
    return AppConfig(
        llm_provider=_get_env("LLM_PROVIDER", "openai"),
        llm_model=_get_env("LLM_MODEL", "gpt-4.1-mini"),
        llm_temperature=float(_get_env("LLM_TEMPERATURE", "0")),
        llm_timeout=int(_get_env("LLM_TIMEOUT", "10")),
        llm_max_tokens=int(_get_env("LLM_MAX_TOKENS", "1000")),
        llm_top_p=float(_get_env("LLM_TOP_P", "1")),
        llm_frequency_penalty=float(_get_env("LLM_FREQUENCY_PENALTY", "0")),
        llm_presence_penalty=float(_get_env("LLM_PRESENCE_PENALTY", "0")),
        enable_langsmith=_is_truthy(_get_env("LANGSMITH_TRACING", "")) or _is_truthy(
            _get_env("LANGCHAIN_TRACING_V2", "")
        ),
        enable_json_logs=_is_truthy(_get_env("JSON_LOGS", "true")),
    )
