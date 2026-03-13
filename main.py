from agents.router_agent import RouterAgent
from chat.chat import run_chat

if __name__ == "__main__":
    agent = RouterAgent()
    run_chat(agent)