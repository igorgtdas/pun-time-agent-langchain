import uuid

from agents.out_of_scope_agent import OutOfScopeAgent
from agents.time_pun_agent import TimePunAgent
from agents.weather_agent import WeatherAgent
from agents.router_agent import RouterAgent


def _new_thread_id() -> str:
    return f"user_{uuid.uuid4().hex[:8]}"


def _select_agent():
    agents = {
        "1": ("Agente de horas com trocadilhos", TimePunAgent),
        "2": ("Agente de clima", WeatherAgent),
        "3": ("Agente de roteamento", RouterAgent),
        "4": ("Agente fora de escopo", OutOfScopeAgent),
    }
    while True:
        print("Selecione o agente:")
        for key, (label, _) in agents.items():
            print(f"{key}) {label}")
        choice = input("Opção: ").strip()
        if choice in agents:
            _, agent_cls = agents[choice]
            return agent_cls()
        print("Opção inválida. Tente novamente.")


def run_chat() -> None:
    agent = _select_agent()
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

        if isinstance(agent, RouterAgent):
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
        else:
            response = agent.run(question=question, thread_id=thread_id)
            print(f"Agente: {response}")


if __name__ == "__main__":
    run_chat()
