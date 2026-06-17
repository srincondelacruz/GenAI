# 10-MCP / client-ts — Cliente MCP genérico (TypeScript)

Cliente MCP que se conecta a **cualquier servidor MCP público** vía
**Streamable HTTP** (con fallback a SSE). Incluye un host que integra
**Azure OpenAI** para orquestar llamadas a tools (bucle ReAct).

## Arquitectura

```
┌──────────── host.ts (Azure OpenAI) ──────────────┐
│ listTools → esquema function-calling              │
│ LLM elige tool → callTool(MCP) → resultado       │
│ repite hasta respuesta final                      │
└───────────────────┬──────────────────────────────┘
                    │  Streamable HTTP / SSE
┌───────────────────▼──────────────────────────────┐
│ client.ts (McpClientWrapper)                      │
│   StreamableHTTPClientTransport                   │
│   fallback: SSEClientTransport                    │
│       ↓                                           │
│   Cualquier servidor MCP público                  │
│   (local, Azure Function, cloud, etc.)            │
└──────────────────────────────────────────────────┘
```

## Setup

```bash
npm install
cp .env.example .env    # rellena las claves Azure y la URL del servidor
npm run build
```

## Uso

```bash
# Modo CLI (una pregunta)
node dist/index.js "¿qué hora es en Tokyo y cuánto es 23*7+4?"

# REPL interactivo
node dist/index.js

# Atajo con npm
npm run dev -- "¿cuánto es 100/3?"
```

## Conectar a diferentes servidores

Cambia `MCP_SERVER_URL` en `.env`:

```bash
# Servidor local (Parte 2 — Azure Function local)
MCP_SERVER_URL=http://localhost:7071/api/mcp

# Servidor desplegado en Azure
MCP_SERVER_URL=https://func-xxxxxx.azurewebsites.net/api/mcp

# Cualquier servidor MCP público con Streamable HTTP o SSE
MCP_SERVER_URL=https://otro-servidor.ejemplo.com/mcp
```

## Módulo reutilizable

`client.ts` se puede usar de forma independiente sin el host/LLM:

```typescript
import { McpClientWrapper } from "./client.js";

const client = await McpClientWrapper.connect("http://localhost:7071/api/mcp");
const tools = await client.listTools();
const result = await client.callTool("calculator", { expression: "2+2" });
await client.close();
```

## Estructura

```
client-ts/
├── .env.example
├── package.json
├── tsconfig.json
└── src/
    ├── index.ts      # Entry point (carga .env y lanza host)
    ├── client.ts     # Módulo cliente MCP reutilizable
    └── host.ts       # Orquestador con Azure OpenAI + bucle ReAct
```

SDK: `@modelcontextprotocol/sdk` (Client + StreamableHTTPClientTransport + SSEClientTransport).
