"""
Servidor A2A: publica el Agent Card + expone el endpoint JSON-RPC.

- Agent Card en  http://HOST:PORT/.well-known/agent.json   (descubrimiento)
- JSON-RPC en    http://HOST:PORT/                          (message/send, message/stream)

Arrancar:  python server.py     (defecto 127.0.0.1:9999)
"""

import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent import LangGraphAgent
from agent_executor import LangGraphAgentExecutor

HOST = os.getenv("A2A_HOST", "127.0.0.1")
PORT = int(os.getenv("A2A_PORT", "9999"))


def build_agent_card() -> AgentCard:
    skill = AgentSkill(
        id="asistente_general",
        name="Asistente general con calculadora",
        description="Responde preguntas y resuelve operaciones aritméticas vía herramienta.",
        tags=["chat", "matemáticas", "langgraph"],
        examples=["¿Cuánto es 23 * 7 + 4?", "Explícame qué es el protocolo A2A"],
    )
    return AgentCard(
        name="LangGraph A2A Agent",
        description="Agente LangGraph (Azure OpenAI) expuesto mediante el protocolo A2A.",
        url=f"http://{HOST}:{PORT}/",
        version="1.0.0",
        default_input_modes=LangGraphAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=LangGraphAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )


def build_app():
    handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(
        agent_card=build_agent_card(),
        http_handler=handler,
    ).build()


if __name__ == "__main__":
    print(f"[server] A2A en http://{HOST}:{PORT}  (card: /.well-known/agent.json)")
    uvicorn.run(build_app(), host=HOST, port=PORT)
