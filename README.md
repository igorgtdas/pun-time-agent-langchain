# langchain-time_weather_agent_cx

Agente de hora/clima com roteamento e fallback out_of_scope.

## Requisitos
- Python 3.11+
- Dependencias: langchain, langgraph, langchain-openai, langsmith, python-dotenv,
  fastapi, uvicorn

## Variaveis de ambiente
Exemplo de `.env`:
```
JSON_LOGS=true
LANGSMITH_TRACING=false
API_KEY=uma-chave-forte
```

## Execucao local (CLI)
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Sobre FastAPI (conceito)
FastAPI e um framework web moderno para Python focado em performance, tipagem e
documentacao automatica. Ele gera uma API HTTP padronizada, o que facilita
integracao com plataformas como n8n e Telegram, que ja falam HTTP por natureza.

Referencias:
- https://fastapi.tiangolo.com/
- https://fastapi.tiangolo.com/learn/

## Execucao API (FastAPI)
```
python -m pip install -r requirements.txt
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### Como usar a API
Endpoint principal:
- `POST /chat`

Headers:
- `Content-Type: application/json`
- `X-API-Key: <sua-chave>`

Body (JSON):
```
{
  "question": "Que horas sao?",
  "thread_id": "user_1234",
  "include_reasoning": true,
  "include_route": true
}
```

Resposta (exemplo):
```
{
  "thread_id": "user_1234",
  "response": {
    "agent_response": "Agora sao 14:20, e o tempo voa!",
    "current_time": "2026-03-12T14:20:00"
  },
  "route": "TIME_PUN",
  "reasoning": "Pergunta sobre horario."
}
```

## Como testar (local)
Exemplo de chamada via `curl`:
```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: uma-chave-forte" \
  -d "{\"question\":\"Que horas sao?\"}"
```

Se preferir, voce pode testar via Swagger:
- `http://localhost:8000/docs`

## Docker
Build:
```
docker build -t langchain-time-weather-agent .
```

Run:
```
docker run --env-file .env -it langchain-time-weather-agent
```

Run (API):
```
docker run --env-file .env -p 8000:8000 langchain-time-weather-agent \
  uvicorn api.app:app --host 0.0.0.0 --port 8000
```

## Integracao com n8n (passo a passo)
1) Suba a API localmente ou via Docker.
2) No n8n, crie um workflow com os nodes:
   - (Opcional) **Webhook** para receber a pergunta.
   - **HTTP Request** para chamar a API.
3) Configure o node **HTTP Request**:
   - Method: `POST`
   - URL: `http://SEU_HOST:8000/chat`
   - Headers:
     - `Content-Type: application/json`
     - `X-API-Key: uma-chave-forte`
   - Body (JSON):
```
{
  "question": "Qual o clima hoje em Sao Paulo?",
  "thread_id": "n8n_001"
}
```
4) Use a resposta do HTTP Request para continuar o fluxo:
   - `response.agent_response` contem a resposta principal.
   - `route` indica o agente selecionado.

## Integracao com outras plataformas (ex.: Telegram)
O Telegram (e outras plataformas) costuma usar webhooks ou polling. Em ambos os
casos, o fluxo e o mesmo:
1) Receber a mensagem do usuario.
2) Enviar a pergunta para `POST /chat` com o header `X-API-Key`.
3) Retornar a resposta do agente ao usuario.
