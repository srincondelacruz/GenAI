"""
Agente LangGraph (ReAct) sobre Azure OpenAI + 1 herramienta (calculadora).

Expone stream(query, context_id): async generator que emite progreso
(llamadas a herramienta) y al final la respuesta. El AgentExecutor A2A lo
traduce a eventos del protocolo (working → artifact → completed).
"""

import ast
import operator as op
import os
from collections.abc import AsyncIterable
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

load_dotenv()

SYSTEM_PROMPT = (
    "Eres un asistente útil y conciso. Responde en el idioma de la pregunta. "
    "Para cálculos aritméticos usa SIEMPRE la herramienta 'calculator'."
)

# ── Herramienta de ejemplo (evaluador aritmético seguro) ──────────────────────

_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("expresión no permitida")


@tool
def calculator(expression: str) -> str:
    """Evalúa una expresión aritmética, p.ej. '2 + 2 * 3'. Solo + - * / ** % y paréntesis."""
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error al evaluar '{expression}': {e}"


# ── Agente ────────────────────────────────────────────────────────────────────

class LangGraphAgent:
    """Agente ReAct con memoria por thread_id (= context_id de A2A)."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            temperature=0,
        )
        self.graph = create_react_agent(
            llm,
            tools=[calculator],
            checkpointer=MemorySaver(),
            prompt=SYSTEM_PROMPT,
        )

    async def stream(self, query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
        config = {"configurable": {"thread_id": context_id}}
        inputs = {"messages": [("user", query)]}

        # Progreso: cada paso del grafo (stream_mode='values' = estado completo)
        async for event in self.graph.astream(inputs, config, stream_mode="values"):
            msg = event["messages"][-1]
            if isinstance(msg, AIMessage) and msg.tool_calls:
                name = msg.tool_calls[0]["name"]
                yield {"done": False, "content": f"Usando herramienta «{name}»…"}
            elif isinstance(msg, ToolMessage):
                yield {"done": False, "content": "Procesando resultado…"}

        # Respuesta final (último AIMessage del estado)
        final = self.graph.get_state(config).values["messages"][-1]
        yield {"done": True, "content": final.content}
