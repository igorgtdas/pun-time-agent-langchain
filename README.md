# langchain-time_weather_agent_cx

Agente de hora/clima com roteamento e fallback out_of_scope.

## Requisitos
- Python 3.11+
- Dependencias: langchain, langgraph, langchain-openai, langsmith, python-dotenv

## Variaveis de ambiente
Exemplo de `.env`:
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0
LLM_TIMEOUT=10
LLM_MAX_TOKENS=1000
LLM_TOP_P=1
LLM_FREQUENCY_PENALTY=0
LLM_PRESENCE_PENALTY=0

JSON_LOGS=true
LANGSMITH_TRACING=false
```

## Execucao local
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Docker
Build:
```
docker build -t langchain-time-weather-agent .
```

Run:
```
docker run --env-file .env -it langchain-time-weather-agent
```
