from dataclasses import dataclass

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from core.logger import init_logging, log_event
from core.observability import get_langsmith_callbacks, to_jsonable
from core.settings import load_config
from tools.context import Context
from tools.tool_current_date_time import tool_current_date_time

load_dotenv()

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
Papel:
Voce e um agente de horario.

Missao:
Responder perguntas sobre horas com trocadilhos em portugues.

Tools:
- tool_current_date_time: use para obter a data e hora atuais.

Regras:
- Sempre que o usuario pedir a hora, use a tool para buscar a hora atual.
- Sempre inclua a hora atual na resposta.
- A resposta deve conter um trocadilho leve e amigavel.
"""


@dataclass
class ResponseFormat:
    """Response schema for the agent."""

    agent_response: str
    current_time: str


class TimePunAgent:
    def __init__(self):
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
            tools=[tool_current_date_time],
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
            {"messages": [{"role": "user", "content": question}]},
            config=config,
            context=Context(user_id=thread_id),
        )
        structured = response["structured_response"]
        log_event(
            "agent_response",
            {"thread_id": thread_id, "response": to_jsonable(structured)},
            CONFIG,
        )
        return structured
