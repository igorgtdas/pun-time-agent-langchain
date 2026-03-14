from agents.router_agent import RouterAgent
from chat.chat import run_chat

if __name__ == "__main__":
    # Memoria opcional por agente:
    # use_memory=True ativa historico; window_size define o limite de mensagens.
    agent = RouterAgent(use_memory=True, window_size=3)
    run_chat(agent)