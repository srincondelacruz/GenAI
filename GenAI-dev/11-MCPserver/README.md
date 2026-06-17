# 11 — MCP Server (Azure Functions)

Servidor MCP remoto desplegado como **Azure Function** con transporte
**Streamable HTTP**. Expone herramientas de utilidad accesibles por cualquier
cliente MCP compatible.

---

## 📡 Endpoint

| Entorno | URL |
|---------|-----|
| **Local** | `http://localhost:7071/api/mcp` |
| **Azure** | `https://<function-app-name>.azurewebsites.net/api/mcp` |

**Transporte:** Streamable HTTP (JSON-RPC sobre HTTP)  
**Métodos soportados:** `POST`, `GET`, `DELETE`  
**Autenticación:** Anónima (configurable vía Azure EasyAuth)

---

## 🔧 Tools disponibles

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `calculator` | Evalúa una expresión aritmética segura (`+`, `-`, `*`, `/`, `**`, `%`, paréntesis) | `expression` (string) — Ej: `"23 * 7 + 4"` |
| `current_time` | Devuelve la fecha y hora actual en la zona horaria indicada | `timezone` (string, default: `"Europe/Madrid"`) — Zona IANA, ej: `"Asia/Tokyo"` |
| `add_note` | Guarda una nota en memoria (volátil, se pierde al reiniciar) | `text` (string) — Texto de la nota |
| `list_notes` | Lista todas las notas guardadas en la sesión actual | _(sin parámetros)_ |

---

## 🔌 Cómo conectarse (para consumidores)

### Opción 1 — Desde Claude Desktop / VS Code / Cursor

Añade esta configuración en tu archivo de cliente MCP (`mcp.json`, `claude_desktop_config.json`, etc.):

```json
{
  "mcpServers": {
    "mcp-azure-demo": {
      "url": "http://localhost:7071/api/mcp"
    }
  }
}
```

> Para producción, cambia la URL por la de Azure:
> `https://<function-app-name>.azurewebsites.net/api/mcp`

### Opción 2 — Desde MCP Inspector (pruebas rápidas)

```bash
npx @modelcontextprotocol/inspector http://localhost:7071/api/mcp
```

Esto abre una interfaz web donde puedes ver las tools, ejecutarlas y ver los resultados.

### Opción 3 — Desde código TypeScript/JavaScript

```bash
npm install @modelcontextprotocol/sdk zod
```

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

// 1. Conectar
const client = new Client({ name: "mi-app", version: "1.0.0" });
const transport = new StreamableHTTPClientTransport(
  new URL("http://localhost:7071/api/mcp")
);
await client.connect(transport);

// 2. Listar tools
const { tools } = await client.listTools();
console.log(tools.map(t => t.name));
// → ["calculator", "current_time", "add_note", "list_notes"]

// 3. Ejecutar una tool
const result = await client.callTool({
  name: "calculator",
  arguments: { expression: "23 * 7 + 4" },
});
console.log(result.content);
// → [{ type: "text", text: "165" }]

// 4. Cerrar conexión
await client.close();
```

### Opción 4 — Desde código Python

```bash
pip install mcp httpx
```

```python
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def main():
    async with streamablehttp_client("http://localhost:7071/api/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            # Listar tools
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

            # Ejecutar una tool
            result = await session.call_tool("calculator", {"expression": "23*7+4"})
            print(result.content[0].text)  # → "165"

asyncio.run(main())
```

### Opción 5 — Con curl (HTTP directo)

```bash
# Inicializar sesión
curl -X POST http://localhost:7071/api/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": { "name": "curl-test", "version": "1.0.0" }
    }
  }'

# Listar tools
curl -X POST http://localhost:7071/api/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Ejecutar calculator
curl -X POST http://localhost:7071/api/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "calculator",
      "arguments": { "expression": "23 * 7 + 4" }
    }
  }'
```

---

## 🏗️ Arquitectura

```
                    Cualquier cliente MCP
                    (Claude, VS Code, SDK, curl...)
                            │
                            │  HTTP POST/GET/DELETE
                            ▼
┌────────────────────────────────────────────────────────┐
│  Azure Function  /api/mcp                              │
│                                                        │
│  WebStandardStreamableHTTPServerTransport (stateless)  │
│       │                                                │
│  McpServer                                             │
│    tools: calculator · current_time · add_note ·       │
│           list_notes                                   │
└────────────────────────────────────────────────────────┘
```

**Stateless:** cada request crea una instancia nueva del servidor.
Las notas en memoria se pierden entre requests (pensado como demo).

---

## 🚀 Setup para desarrollo

### Requisitos previos

- [Node.js](https://nodejs.org/) >= 18
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) >= 4.0.7030
- [Docker](https://www.docker.com/) — para Azurite (emulador de Azure Storage)

### Instalación y ejecución local

```bash
# Instalar dependencias
npm install

# Compilar TypeScript
npm run build

# Arrancar servidor local (requiere Azurite corriendo)
npm start
# → Servidor disponible en http://localhost:7071/api/mcp
```

> **Nota:** Si no tienes Docker/Azurite, puedes configurar una Storage Account
> real en `local.settings.json` → `AzureWebJobsStorage`.

### Compilar en modo watch (desarrollo)

```bash
npm run watch   # en una terminal
func start      # en otra terminal
```

---

## ☁️ Despliegue a Azure

### Con Azure Developer CLI (recomendado)

```bash
# Login
azd auth login

# Desplegar (crea todos los recursos + despliega código)
azd up
# → Te pedirá nombre de entorno y región
# → Output: AZURE_FUNCTION_URL = https://func-xxxxx.azurewebsites.net

# Tu endpoint MCP estará en:
# https://func-xxxxx.azurewebsites.net/api/mcp
```

### Con Azure Functions Core Tools (alternativa)

```bash
# Crear Function App en Azure primero (vía Portal o az cli)
az functionapp create --name mi-mcp-server --resource-group mi-rg \
  --consumption-plan-location westeurope --runtime node --runtime-version 20 \
  --storage-account mistorageaccount

# Desplegar
func azure functionapp publish mi-mcp-server
```

---

## 📁 Estructura del proyecto

```
11-MCPserver/
├── azure.yaml               # Definición azd (despliegue)
├── host.json                 # Config Azure Functions runtime
├── local.settings.json       # Variables de entorno locales
├── package.json              # Dependencias y scripts
├── tsconfig.json             # Config TypeScript
├── .funcignore               # Archivos excluidos del deploy
├── src/
│   ├── functions/
│   │   └── mcp.ts            # Handler Azure Function (Streamable HTTP)
│   └── tools/
│       └── index.ts          # Herramientas MCP
└── infra/                    # Infraestructura Bicep para azd
    ├── main.bicep
    ├── main.parameters.json
    ├── abbreviations.json
    └── core/
        ├── storage.bicep
        └── host/
            ├── appserviceplan.bicep
            └── functions.bicep
```

---

## 🛡️ Seguridad (producción)

Para proteger el endpoint en producción:

1. **Azure EasyAuth** — Habilitar autenticación integrada en la Function App
2. **API Key** — Cambiar `authLevel` de `anonymous` a `function` en `mcp.ts`
3. **API Management** — Poner Azure APIM delante para rate limiting, OAuth, etc.

Más info: [Azure Functions MCP auth](https://learn.microsoft.com/azure/azure-functions/functions-mcp-tutorial)

---

## 📚 Referencias

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Azure Functions MCP extension](https://learn.microsoft.com/azure/azure-functions/functions-bindings-mcp)
- [Azure Samples: remote-mcp-functions-typescript](https://github.com/Azure-Samples/remote-mcp-functions-typescript)
