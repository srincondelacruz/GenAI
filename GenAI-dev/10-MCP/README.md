# 10 — MCP (Model Context Protocol)

Servidor MCP que expone herramientas + host que conecta un LLM (**Azure OpenAI**)
a ese servidor. El modelo decide qué tool llamar; el host las ejecuta vía MCP y
le devuelve el resultado (bucle ReAct). Transporte **stdio** (el de Claude Desktop).

## Arquitectura

```
┌──────────── host.py (Azure OpenAI) ─────────────┐
│ list_tools → esquema function-calling           │
│ LLM elige tool → call_tool(MCP) → resultado     │
│ repite hasta respuesta final                     │
└───────────────────┬─────────────────────────────┘
                    │ stdio (JSON-RPC por stdin/stdout)
┌───────────────────▼─────────────────────────────┐
│ server.py (FastMCP)                              │
│   tools: calculator · current_time · add_note ·  │
│          list_notes                              │
└──────────────────────────────────────────────────┘
```

## Tools

| Tool           | Qué hace                                   |
|----------------|--------------------------------------------|
| `calculator`   | Evalúa expresión aritmética segura          |
| `current_time` | Hora actual por zona IANA (def. Madrid)     |
| `add_note`     | Guarda nota en memoria                      |
| `list_notes`   | Lista notas de la sesión                    |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # rellena las claves Azure
```

## Uso

```bash
# El host lanza el server solo (stdio); no hay que arrancarlo aparte.
python host.py "¿qué hora es en Tokyo y cuánto es 23*7+4?"
python host.py                # REPL interactivo
```

Inspeccionar el server con la herramienta oficial:

```bash
npx @modelcontextprotocol/inspector python server.py
```

SDK: `mcp` (FastMCP server + ClientSession/stdio_client en el host).
