from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from agents.out_of_scope_agent import OutOfScopeAgent
from agents.time_pun_agent import TimePunAgent
from agents.weather_agent import WeatherAgent
# Para adicionar/remover agentes: ajuste os imports acima conforme novos agentes.
from core.logger import init_logging, log_event
from core.observability import get_langsmith_callbacks, to_jsonable
from core.settings import load_config
from tools.context import Context

load_dotenv()

CONFIG = load_config()
init_logging(CONFIG)

LLM_MODEL = CONFIG.llm_model
LLM_PROVIDER = CONFIG.llm_provider
TEMPERATURE = 0
TIMEOUT = CONFIG.llm_timeout
MAX_TOKENS = CONFIG.llm_max_tokens
TOP_P = CONFIG.llm_top_p
FREQUENCY_PENALTY = CONFIG.llm_frequency_penalty
PRESENCE_PENALTY = CONFIG.llm_presence_penalty

SYSTEM_PROMPT = """
Papel:
Voce e um agente roteador (supervisor).

Missao:
Selecionar o melhor agente para responder a pergunta do usuario.

Agentes disponiveis:
- TIME_PUN: perguntas sobre horas/horario, com trocadilhos.
- WEATHER: perguntas sobre clima/tempo e condicoes meteorologicas.
- OUT_OF_SCOPE: perguntas simples fora do escopo (hora/clima).
# Para adicionar/remover agentes: atualize esta lista e o enum AgentRoute.

Regras:
- Responda APENAS com o ENUM do agente correto e um reasoning curto.
- Se a intencao for ambigua, escolha o mais provavel.
- O reasoning deve ter no maximo 1 frase.
- Se alguma tool retornar JSON com success=false, nao chame nenhuma tool novamente e responda com a mensagem de erro.
"""


class AgentRoute(str, Enum):
    """Agent identifiers for routing."""

    TIME_PUN = "TIME_PUN"
    WEATHER = "WEATHER"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    # Para adicionar/remover agentes: inclua/remova o identificador aqui.


@dataclass
class ResponseFormat:
    """Response schema for the router."""

    agent: AgentRoute
    reasoning: str


ROUTE_TO_AGENT = {
    AgentRoute.TIME_PUN: TimePunAgent,
    AgentRoute.WEATHER: WeatherAgent,
    AgentRoute.OUT_OF_SCOPE: OutOfScopeAgent,
    # Para adicionar/remover agentes: atualize este mapa para ligar enum -> classe.
}


class RouterAgent:
    def __init__(self, use_memory: bool = False, window_size: int = 3):
        # use_memory ativa/desativa historico; window_size limita mensagens consideradas.
        self._use_memory = use_memory
        self._window_size = window_size
        self._history: dict[str, list[dict[str, str]]] = {}
        self._agent_instances = {route: cls() for route, cls in ROUTE_TO_AGENT.items()}
        self._model = init_chat_model(
            LLM_MODEL,
            model_provider=LLM_PROVIDER,
            temperature=TEMPERATURE,
            timeout=TIMEOUT,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
            frequency_penalty=FREQUENCY_PENALTY,
            presence_penalty=PRESENCE_PENALTY,
        )
        self._checkpointer = InMemorySaver()
        self._agent = create_agent(
            model=self._model,
            system_prompt=SYSTEM_PROMPT,
            tools=[],
            context_schema=Context,
            response_format=ToolStrategy(ResponseFormat),
            checkpointer=self._checkpointer,
        )

    def run(self, question: str, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        callbacks = get_langsmith_callbacks(CONFIG)
        if callbacks:
            config["callbacks"] = callbacks
        log_event(
            "user_message",
            {"thread_id": thread_id, "content": question},
            CONFIG,
        )
        response = self._agent.invoke(
            {"messages": self._build_messages(thread_id, question)},
            config=config,
            context=Context(user_id=thread_id),
        )
        structured = response["structured_response"]
        self._record_history(thread_id, question, structured)
        log_event(
            "agent_response",
            {"thread_id": thread_id, "response": to_jsonable(structured)},
            CONFIG,
        )
        return structured

    def route_and_run(
        self,
        question: str,
        thread_id: str,
        include_reasoning: bool = True,
        include_route: bool = True,
    ):
        route_response = self.run(question, thread_id)
        agent_class = ROUTE_TO_AGENT.get(route_response.agent)
        if not agent_class:
            raise ValueError(f"Rota nao mapeada: {route_response.agent}")
        agent_instance = self._agent_instances[route_response.agent]
        routed_question = question
        if include_reasoning and route_response.reasoning:
            routed_question = (
                f"{question}\n\n"
                "Contexto do roteador (reasoning): "
                f"{route_response.reasoning}"
            )
        agent_response = agent_instance.run(routed_question, thread_id)

        payload = {"response": agent_response}
        if include_route:
            payload["route"] = route_response.agent
        if include_reasoning:
            payload["reasoning"] = route_response.reasoning
        return payload

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
        assistant_text = str(structured)
        new_entries = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant_text},
        ]
        history = self._history.get(thread_id, [])
        max_messages = self._window_size * 2
        self._history[thread_id] = (history + new_entries)[-max_messages:]
