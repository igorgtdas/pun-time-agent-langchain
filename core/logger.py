import json
import logging
import time

from core.settings import AppConfig

_logger = logging.getLogger(__name__)


def init_logging(config: AppConfig) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    if not config.enable_json_logs:
        _logger.setLevel(logging.WARNING)


def log_event(event: str, payload: dict, config: AppConfig) -> None:
    if not config.enable_json_logs:
        return
    _logger.info(
        json.dumps({"event": event, "ts": time.time(), **payload}, ensure_ascii=True)
    )
