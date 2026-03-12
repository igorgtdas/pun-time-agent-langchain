from datetime import datetime

from langchain.tools import tool

from core.logger import log_event
from core.settings import load_config

CONFIG = load_config()


@tool
def tool_current_date_time() -> str:
    """Return the current date and time."""
    log_event(
        "tool_call",
        {"tool": "tool_current_date_time", "input": {}},
        CONFIG,
    )
    output = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_event(
        "tool_result",
        {"tool": "tool_current_date_time", "output": output},
        CONFIG,
    )
    return output
