from dataclasses import dataclass  # Define classes de dados de forma simples.

from dotenv import load_dotenv  # Carrega variáveis do arquivo .env.
from langchain.agents import create_agent  # Monta o agente com modelo, prompt e tools.
from langchain.agents.structured_output import ToolStrategy  # Força saída estruturada.
from langchain.chat_models import init_chat_model  # Inicializa o modelo de chat (LLM).
from langgraph.checkpoint.memory import InMemorySaver  # Armazena estado em memória.

from core.logger import init_logging, log_event
from core.observability import get_langsmith_callbacks, to_jsonable
from core.settings import load_config

from tools.context import Context  # Schema do contexto usado pelas tools.
from tools.get_user_location import get_user_location  # Tool: descobre a localização do usuário.
from tools.get_weather_for_location import get_weather_for_location


load_dotenv()  # Torna variáveis do .env disponíveis no ambiente.

CONFIG = load_config()
init_logging(CONFIG)

LLM_MODEL = CONFIG.llm_model
LLM_PROVIDER = CONFIG.llm_provider
TEMPERATURE = CONFIG.llm_temperature
TIMEOUT = CONFIG.llm_timeout
MAX_TOKENS = CONFIG.llm_max_tokens
TOP_P = CONFIG.llm_top_p
FREQUENCY_PENALTY = CONFIG.llm_frequency_penalty
PRESENCE_PENALTY = CONFIG.llm_presence_penalty

SYSTEM_PROMPT = """
Role: 
You are a weather agent.

Mission:
Your mission is to help the user with their weather questions.


Tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

Rules:
If a user asks you for the weather, make sure you know the location. In case user dont pass any location, ask for it and don't answer the question.
If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""  # Prompt base do agente.


@dataclass
class ResponseFormat:
    """Response schema for the agent."""  # Schema da resposta estruturada.

    agent_response: str  # Resposta principal do agente.
    weather_conditions: str | None = None  # Campo opcional com condições do tempo.


class WeatherAgent:
    def __init__(self):
        self._model = init_chat_model(  # Inicializa o LLM com configs do .env.
            LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=TEMPERATURE,
            timeout=TIMEOUT,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
            frequency_penalty=FREQUENCY_PENALTY,
            presence_penalty=PRESENCE_PENALTY,
        )
        self._checkpointer = InMemorySaver()  # Guarda estado do agente em memória.
        self._agent = create_agent(  # Cria o agente com prompt e tools.
            model=self._model,
            system_prompt=SYSTEM_PROMPT,
            tools=[get_user_location, get_weather_for_location],
            context_schema=Context,  # Schema de contexto para tools.
            response_format=ToolStrategy(ResponseFormat),  # Saída estruturada.
            checkpointer=self._checkpointer,
        )

    def run(self, question: str, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}  # Identifica a sessão.
        callbacks = get_langsmith_callbacks(CONFIG)
        if callbacks:
            config["callbacks"] = callbacks  # Habilita tracing no invoke.
        log_event(
            "user_message",
            {"thread_id": thread_id, "content": question},
            CONFIG,
        )
        response = self._agent.invoke(  # Executa o agente com a pergunta.
            {"messages": [{"role": "user", "content": question}]},
            config=config,
            context=Context(user_id=thread_id),  # Contexto inicial.
        )
        structured = response["structured_response"]
        log_event(
            "agent_response",
            {"thread_id": thread_id, "response": to_jsonable(structured)},
            CONFIG,
        )
        return structured  # Retorna resposta estruturada.
