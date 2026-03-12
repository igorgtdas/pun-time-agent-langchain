from langchain.tools import tool, ToolRuntime

from core.logger import log_event
from core.settings import load_config
from tools.context import Context

CONFIG = load_config()


@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    log_event(
        "tool_call",
        {"tool": "get_user_location", "input": {"user_id": user_id}},
        CONFIG,
    )
    output = "Florida" if user_id == "1" else "SF"
    
    log_event(
        "tool_result",
        {"tool": "get_user_location", "output": output},
        CONFIG,
    )
    return output
