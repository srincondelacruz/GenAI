"""
Host MCP + Azure OpenAI.

Flujo:
  1. Lanza server.py como subproceso MCP (stdio) y abre una ClientSession.
  2. list_tools() → traduce los tools MCP al formato de function-calling de OpenAI.
  3. El LLM (Azure OpenAI) decide qué tool llamar; el host ejecuta la llamada
     vía session.call_tool() y le devuelve el resultado al modelo (bucle ReAct).
  4. Cuando el modelo deja de pedir tools, imprime la respuesta final.

Uso:
    python host.py "¿qué hora es en Tokyo y cuánto es 23*7+4?"
    python host.py                # REPL interactivo
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import AsyncAzureOpenAI

load_dotenv()

SYSTEM = (
    "Eres un asistente útil y conciso. Dispones de herramientas vía MCP. "
    "Úsalas cuando aporten datos exactos (cálculos, hora, notas). "
    "Responde en el idioma de la pregunta."
)

# Lanza el servidor MCP con el MISMO intérprete del venv.
SERVER = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(os.path.dirname(__file__), "server.py")],
)


def to_openai_tools(mcp_tools) -> list[dict]:
    """Traduce tools MCP → esquema function-calling de OpenAI."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema,
            },
        }
        for t in mcp_tools
    ]


def tool_result_text(result) -> str:
    """Concatena el texto de un CallToolResult."""
    parts = [c.text for c in result.content if getattr(c, "type", None) == "text"]
    return "\n".join(parts) if parts else "(sin contenido)"


async def chat(session: ClientSession, llm: AsyncAzureOpenAI, deployment: str, question: str) -> str:
    tools = to_openai_tools((await session.list_tools()).tools)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]

    while True:
        resp = await llm.chat.completions.create(
            model=deployment, messages=messages, tools=tools, temperature=0
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        # Registra la decisión del modelo (asistente con tool_calls)
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        # Ejecuta cada tool vía MCP y devuelve el resultado al modelo
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            print(f"  [tool] {tc.function.name}({args})")
            result = await session.call_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result_text(result),
            })


async def main():
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    llm = AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    )

    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print(f"[mcp] conectado. tools: {[t.name for t in tools]}\n")

            cli = " ".join(sys.argv[1:]).strip()
            if cli:
                print(await chat(session, llm, deployment, cli))
                return

            print("Host MCP — escribe tu pregunta (Ctrl-C para salir)\n")
            try:
                while True:
                    q = input("> ").strip()
                    if q:
                        print("\n" + await chat(session, llm, deployment, q) + "\n")
            except (KeyboardInterrupt, EOFError):
                print("\nbye")


if __name__ == "__main__":
    asyncio.run(main())
