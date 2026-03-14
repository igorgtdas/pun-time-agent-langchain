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

Rules:
If a user asks you for the weather, make sure you know the location. In case user dont pass any location, ask for it and don't answer the question.
If a tool returns JSON with success=false, do not call any tool again and reply with the error message.
"""  # Prompt base do agente.


@dataclass
class ResponseFormat:
    """Response schema for the agent."""  # Schema da resposta estruturada.

    agent_response: str  # Resposta principal do agente.
    agent_name: str | None = None  # Nome do agente que respondeu.


class WeatherAgent:
    def __init__(self, use_memory: bool = False, window_size: int = 3):
        # use_memory ativa/desativa historico; window_size limita mensagens consideradas.
        self._use_memory = use_memory
        self._window_size = window_size
        self._history: dict[str, list[dict[str, str]]] = {}
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
            tools=[get_weather_for_location],
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
            {
                "messages": self._build_messages(thread_id, question),
            },
            config=config,
            context=Context(user_id=thread_id),  # Contexto inicial.
        )
        structured = response["structured_response"]
        self._record_history(thread_id, question, structured)
        log_event(
            "agent_response",
            {"thread_id": thread_id, "response": to_jsonable(structured)},
            CONFIG,
        )
        return structured  # Retorna resposta estruturada.

    def _build_messages(self, thread_id: str, question: str) -> list[dict[str, str]]:
        user_message = {"role": "user", "content": question}
        if not self._use_memory or self._window_size <= 0:
            return [user_message]
        history = self._history.get(thread_id, [])
        max_messages = self._window_size * 2
        return history[-max_messages:] + [user_message]

    def _record_history(self, thread_id: str, question: str, structured) -> None:
        if not self._use_memory or self._window_size <= 0:
            return
        assistant_text = getattr(structured, "agent_response", str(structured))
        new_entries = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant_text},
        ]
        history = self._history.get(thread_id, [])
        max_messages = self._window_size * 2
        self._history[thread_id] = (history + new_entries)[-max_messages:]
