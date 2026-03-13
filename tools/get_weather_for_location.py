import json
from urllib.parse import urlencode
from urllib.request import urlopen

from langchain.tools import tool, ToolRuntime

from core.logger import log_event
from core.settings import load_config
from tools.context import Context

CONFIG = load_config()
TOOL_NAME = "get_weather_for_location"


def _fetch_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _weather_code_to_text(code: int) -> str:
    mapping = {
        0: "Ceo limpo",
        1: "Predominantemente limpo",
        2: "Parcialmente nublado",
        3: "Encoberto",
        45: "Neblina",
        48: "Nevoeiro gelado",
        51: "Garoa leve",
        53: "Garoa moderada",
        55: "Garoa intensa",
        61: "Chuva fraca",
        63: "Chuva moderada",
        65: "Chuva forte",
        71: "Neve fraca",
        73: "Neve moderada",
        75: "Neve forte",
        80: "Pancadas de chuva fracas",
        81: "Pancadas de chuva moderadas",
        82: "Pancadas de chuva fortes",
        95: "Trovoadas",
        96: "Trovoadas com granizo leve",
        99: "Trovoadas com granizo forte",
    }
    return mapping.get(code, f"Codigo {code}")


def _error_output(message: str) -> str:
    return json.dumps({"success": False, "message": message}, ensure_ascii=False)


def _fail(runtime: ToolRuntime[Context] | None, message: str) -> str:
    if runtime is not None:
        runtime.context.tool_failures.setdefault(TOOL_NAME, message)
    output = _error_output(message)
    log_event(
        "tool_result",
        {"tool": TOOL_NAME, "output": output},
        CONFIG,
    )
    return output


@tool
def get_weather_for_location(city: str, runtime: ToolRuntime[Context]) -> str:
    """Get current weather for a given city using Open-Meteo."""
    previous_error = runtime.context.tool_failures.get(TOOL_NAME)
    if previous_error:
        output = _error_output(previous_error)
        log_event(
            "tool_blocked",
            {"tool": TOOL_NAME, "reason": previous_error},
            CONFIG,
        )
        return output
    log_event(
        "tool_call",
        {"tool": TOOL_NAME, "input": {"city": city}},
        CONFIG,
    )

    query = urlencode({"name": city, "count": 1, "language": "pt", "format": "json"})
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?{query}"
    try:
        geocode = _fetch_json(geocode_url)
    except Exception as exc:
        return _fail(runtime, f"Erro ao consultar geocoding: {exc}")
    if geocode.get("error"):
        return _fail(
            runtime,
            f"Erro no geocoding: {geocode.get('reason') or 'resposta invalida'}",
        )
    results = geocode.get("results") or []
    if not results:
        return _fail(runtime, f"Nao encontrei a localizacao: {city}.")

    location = results[0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    location_name = location.get("name") or city
    region = location.get("admin1")
    country = location.get("country")
    location_label = ", ".join(
        [part for part in [location_name, region, country] if part]
    )

    forecast_query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m,weather_code",
        }
    )
    forecast_url = f"https://api.open-meteo.com/v1/forecast?{forecast_query}"
    try:
        forecast = _fetch_json(forecast_url)
    except Exception as exc:
        return _fail(runtime, f"Erro ao consultar previsao: {exc}")
    if forecast.get("error"):
        return _fail(
            runtime,
            f"Erro na previsao: {forecast.get('reason') or 'resposta invalida'}",
        )
    current = forecast.get("current") or {}
    temperature = current.get("temperature_2m")
    wind_speed = current.get("wind_speed_10m")
    weather_code = current.get("weather_code")

    if temperature is None or wind_speed is None or weather_code is None:
        return _fail(runtime, f"Dados de clima indisponiveis para {location_label}.")

    description = _weather_code_to_text(int(weather_code))
    output = (
        f"Clima em {location_label}: {description}. "
        f"Temperatura {temperature}C e vento {wind_speed} km/h."
    )
    log_event(
        "tool_result",
        {"tool": TOOL_NAME, "output": output},
        CONFIG,
    )
    return output
