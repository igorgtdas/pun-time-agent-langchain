import os
import uuid
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from agents.router_agent import RouterAgent
from core.observability import to_jsonable

load_dotenv()


def _new_thread_id() -> str:
    return f"user_{uuid.uuid4().hex[:8]}"


def _require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY não configurada.",
        )
    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida.",
        )


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    thread_id: str | None = None
    include_reasoning: bool = True
    include_route: bool = True


class ChatResponse(BaseModel):
    thread_id: str
    response: Any
    route: str | None = None
    reasoning: str | None = None


app = FastAPI(title="Langchain Time/Weather Agent API")
_router_agent = RouterAgent()


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, _: None = Depends(_require_api_key)) -> ChatResponse:
    thread_id = payload.thread_id or _new_thread_id()
    result = _router_agent.route_and_run(
        question=payload.question,
        thread_id=thread_id,
        include_reasoning=payload.include_reasoning,
        include_route=payload.include_route,
    )
    response = to_jsonable(result.get("response"))
    route = result.get("route")
    reasoning = result.get("reasoning")
    return ChatResponse(
        thread_id=thread_id,
        response=response,
        route=str(route) if route is not None else None,
        reasoning=reasoning,
    )
