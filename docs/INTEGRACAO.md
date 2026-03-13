# Integracao e Docker

## Por que usar Docker
- Reprodutibilidade: mesma versao de Python e dependencias em qualquer ambiente.
- Isolamento: evita conflitos com outras bibliotecas do sistema.
- Portabilidade: facilita deploy em servidores, cloud ou pipelines de CI.
- Consistencia: o mesmo comando funciona igual em desenvolvimento e producao.

## Visao geral de integracao
Este projeto funciona em dois modos:
- CLI: usado localmente via `python main.py`.
- API (FastAPI): exposta por HTTP para integracoes como n8n e Telegram.

Para integrar com outras plataformas, o modo API e o mais indicado.

## Integracao com n8n (passo a passo)
1) Configure o `.env` com as variaveis do LLM e a chave da API:
```
API_KEY=uma-chave-forte
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0
```

2) Suba a API:
- Local:
```
uvicorn api.app:app --host 0.0.0.0 --port 8000
```
- Docker:
```
docker run --env-file .env -p 8000:8000 langchain-time-weather-agent \
  uvicorn api.app:app --host 0.0.0.0 --port 8000
```

3) No n8n, crie um workflow:
- (Opcional) Node **Webhook** para receber uma pergunta externa.
- Node **HTTP Request** para chamar a API:
  - Method: `POST`
  - URL: `http://SEU_HOST:8000/chat`
  - Headers:
    - `Content-Type: application/json`
    - `X-API-Key: uma-chave-forte`
  - Body (JSON):
```
{
  "question": "Que horas sao agora?",
  "thread_id": "user_1234"
}
```

4) Use a resposta do node HTTP Request:
- Campo `response` contem a resposta principal do agente.
- Campo `route` indica o agente selecionado pelo roteador.

Exemplo de resposta:
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

## Integracao com Telegram (resumo)
- O bot recebe a mensagem do usuario (webhook ou polling).
- O servidor do bot envia a pergunta para `POST /chat` com `X-API-Key`.
- A resposta do agente volta para o usuario no Telegram.

## Dicas e troubleshooting
- Use `thread_id` para manter contexto de conversa.
- Erro `401` indica API key invalida.
- Erro `500` indica `API_KEY` nao configurada no ambiente.
