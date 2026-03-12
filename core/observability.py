from __future__ import annotations

from dataclasses import asdict, is_dataclass
import logging

from core.settings import AppConfig

try:
    from langchain.callbacks.tracers import LangChainTracer
except Exception:  # Compatibilidade com versões sem este módulo.
    LangChainTracer = None

_logger = logging.getLogger(__name__)


def get_langsmith_callbacks(config: AppConfig):
    if not config.enable_langsmith:
        return None
    try:
        if LangChainTracer is None:
            raise RuntimeError("LangChainTracer indisponível na versão atual.")
        return [LangChainTracer()]
    except Exception as exc:
        _logger.warning("LangSmith tracing indisponivel: %s", exc)
        return None


def to_jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    return value
