from langchain.tools import tool

from core.logger import log_event
from core.settings import load_config

CONFIG = load_config()


@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    log_event(
        "tool_call",
        {"tool": "get_weather_for_location", "input": {"city": city}},
        CONFIG,
    )
    output = f"It's always sunny in {city}!"
    log_event(
        "tool_result",
        {"tool": "get_weather_for_location", "output": output},
        CONFIG,
    )
    return output
