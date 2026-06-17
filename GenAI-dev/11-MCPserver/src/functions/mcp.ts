/**
 * Azure Function — Endpoint MCP (Streamable HTTP).
 *
 * Expone el servidor MCP en /api/mcp usando WebStandardStreamableHTTPServerTransport.
 * Modo stateless (sessionIdGenerator: undefined) — ideal para serverless.
 *
 * Soporta:
 *   POST /api/mcp   → mensajes JSON-RPC del cliente
 *   GET  /api/mcp   → SSE stream (para notificaciones server→client)
 *   DELETE /api/mcp  → cierre de sesión
 */

import {
  app,
  HttpRequest,
  HttpResponseInit,
  InvocationContext,
} from "@azure/functions";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { registerTools } from "../tools/index.js";

// ── Habilitar HTTP streaming (requerido para SSE en Azure Functions) ───────
app.setup({ enableHttpStream: true });

/**
 * Crea una instancia fresca del servidor MCP con todas las tools registradas.
 */
function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "mcp-azure-demo",
    version: "1.0.0",
  });
  registerTools(server);
  return server;
}

/**
 * Handler principal — procesa requests MCP (POST, GET, DELETE).
 *
 * Usa WebStandardStreamableHTTPServerTransport que trabaja con la API
 * Web estándar (Request/Response), perfecta para Azure Functions v4.
 */
async function mcpHandler(
  request: HttpRequest,
  _context: InvocationContext
): Promise<HttpResponseInit> {
  try {
    // Crear servidor y transport por cada request (stateless)
    const server = createMcpServer();
    const transport = new WebStandardStreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // stateless — sin gestión de sesiones
      enableJsonResponse: true,      // preferir JSON sobre SSE cuando sea posible
    });

    await server.connect(transport);

    // Construir un Request web estándar a partir del HttpRequest de Azure
    const stdRequest = toWebStandardRequest(request);

    // Dejar que el transport maneje el request y devuelva un Response estándar
    const response = await transport.handleRequest(stdRequest);

    // Convertir la Response web estándar al formato de Azure Functions
    return fromWebStandardResponse(response);
  } catch (error) {
    return {
      status: 500,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        error: `Error interno MCP: ${error instanceof Error ? error.message : String(error)}`,
      }),
    };
  }
}

/**
 * Convierte HttpRequest de Azure Functions → Request web estándar.
 */
function toWebStandardRequest(req: HttpRequest): Request {
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    headers.set(key, value);
  });

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  // Solo incluir body en métodos que lo soportan
  if (req.method !== "GET" && req.method !== "HEAD" && req.method !== "DELETE") {
    init.body = req.body as any;
    // @ts-expect-error — duplex es necesario para streams pero no está en los tipos
    init.duplex = "half";
  }

  return new Request(req.url, init);
}

/**
 * Convierte Response web estándar → HttpResponseInit de Azure Functions.
 */
function fromWebStandardResponse(response: Response): HttpResponseInit {
  const headers: Record<string, string> = {};
  response.headers.forEach((value, key) => {
    headers[key] = value;
  });

  const contentType = headers["content-type"] || "";

  // Si es SSE, devolver el body como ReadableStream
  if (contentType.includes("text/event-stream")) {
    return {
      status: response.status,
      headers,
      body: response.body as any,
    };
  }

  // Para JSON u otro contenido, devolver el body directamente
  return {
    status: response.status,
    headers,
    body: response.body as any,
  };
}

// ── Registrar Azure Function ──────────────────────────────────────────────
app.http("mcp", {
  methods: ["GET", "POST", "DELETE"],
  authLevel: "anonymous",
  route: "mcp",
  handler: mcpHandler,
});
