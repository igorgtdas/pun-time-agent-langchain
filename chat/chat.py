import uuid
from typing import Any


def _new_thread_id() -> str:
    return f"user_{uuid.uuid4().hex[:8]}"


def run_chat(agent: Any) -> None:
    thread_id = _new_thread_id()

    print("Chat iniciado. Use /clean para reiniciar e /exit para sair.")
    while True:
        question = input("Você: ").strip()
        if not question:
            continue
        if question == "/exit":
            print("Sessão encerrada.")
            break
        if question == "/clean":
            thread_id = _new_thread_id()
            print(f"Histórico limpo. Novo thread_id: {thread_id}")
            continue

        payload = agent.route_and_run(
            question=question,
            thread_id=thread_id,
            include_reasoning=True,
            include_route=True,
        )
        response = payload.get("response")
        route = payload.get("route")
        reasoning = payload.get("reasoning")
        final_text = getattr(response, "agent_response", str(response))
        print(f"Agente (final): {final_text}")
        print(f"Route: {route}")
        print(f"Reasoning: {reasoning}")


if __name__ == "__main__":
    raise SystemExit(
        "Execute via main.py para garantir o RouterAgent como entrypoint."
    )
