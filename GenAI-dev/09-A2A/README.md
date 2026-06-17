# 09 — Comunicación cliente-servidor con protocolo A2A

Implementa el **protocolo A2A** (Agent2Agent): un cliente descubre un agente
remoto por su *Agent Card* y le envía mensajes vía JSON-RPC sobre HTTP, con
soporte de **streaming SSE**. El agente del servidor es un grafo **LangGraph**
(ReAct) sobre Azure OpenAI con una herramienta de calculadora.

## Arquitectura

```
            ┌─────────── cliente (client.py) ───────────┐
            │ 1. GET /.well-known/agent.json  → AgentCard│
            │ 2. message/send   (JSON-RPC)    → respuesta│
            │ 3. message/stream (SSE)         → eventos  │
            └───────────────────┬───────────────────────┘
                                │ HTTP
            ┌───────────────────▼───────────────────────┐
            │ servidor A2A (server.py)                   │
            │   A2AStarletteApplication + DefaultHandler │
            │   └─ LangGraphAgentExecutor (executor.py)  │
            │        └─ LangGraphAgent (agent.py)        │
            │             ReAct + Azure OpenAI + tool    │
            └────────────────────────────────────────────┘
```

Eventos del protocolo que emite el servidor por cada mensaje:
`task` → `status-update (working)` … → `artifact-update (respuesta)` → `status-update (completed)`.

## Archivos

| Archivo             | Rol                                                      |
|---------------------|----------------------------------------------------------|
| `agent.py`          | Agente LangGraph (LLM + herramienta) con `stream()`      |
| `agent_executor.py` | Puente A2A: traduce a eventos task/status/artifact       |
| `server.py`         | Publica Agent Card + endpoint JSON-RPC (uvicorn)         |
| `client.py`         | Descubre el card y envía mensajes (send / stream)        |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # rellena las claves Azure
```

## Uso

```bash
# Terminal 1 — servidor
python server.py

# Terminal 2 — cliente
python client.py "¿cuánto es 23 * 7 + 4?"          # streaming (defecto)
python client.py --no-stream "explícame qué es A2A"  # respuesta única

# Ver el Agent Card directamente
curl http://127.0.0.1:9999/.well-known/agent.json
```

SDK: `a2a-sdk==0.2.16` (API estable `A2AStarletteApplication` / `A2AClient`).
