/**
 * Cliente MCP reutilizable — conecta a cualquier servidor MCP público.
 *
 * Soporta transporte Streamable HTTP (recomendado) con fallback a SSE
 * para servidores legacy.
 *
 * Uso:
 *   const client = await McpClientWrapper.connect("http://localhost:7071/api/mcp");
 *   const tools = await client.listTools();
 *   const result = await client.callTool("calculator", { expression: "2+2" });
 *   await client.close();
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";

export interface McpToolInfo {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export class McpClientWrapper {
  private client: Client;
  private serverUrl: string;

  private constructor(client: Client, serverUrl: string) {
    this.client = client;
    this.serverUrl = serverUrl;
  }

  /**
   * Conecta a un servidor MCP remoto.
   * Intenta Streamable HTTP primero; si falla, cae a SSE.
   */
  static async connect(serverUrl: string): Promise<McpClientWrapper> {
    const client = new Client({
      name: "mcp-client-ts",
      version: "1.0.0",
    });

    const url = new URL(serverUrl);

    // Intentar Streamable HTTP (transporte moderno)
    try {
      const transport = new StreamableHTTPClientTransport(url);
      await client.connect(transport);
      console.log(`[mcp] conectado vía Streamable HTTP → ${serverUrl}`);
      return new McpClientWrapper(client, serverUrl);
    } catch (err) {
      console.log(
        `[mcp] Streamable HTTP falló, intentando SSE... (${err instanceof Error ? err.message : String(err)})`
      );
    }

    // Fallback a SSE (servidores legacy)
    try {
      const transport = new SSEClientTransport(url);
      await client.connect(transport);
      console.log(`[mcp] conectado vía SSE → ${serverUrl}`);
      return new McpClientWrapper(client, serverUrl);
    } catch (err) {
      throw new Error(
        `No se pudo conectar al servidor MCP en ${serverUrl}: ${err instanceof Error ? err.message : String(err)}`
      );
    }
  }

  /**
   * Lista todas las tools disponibles en el servidor.
   */
  async listTools(): Promise<McpToolInfo[]> {
    const result = await this.client.listTools();
    return result.tools.map((t: Tool) => ({
      name: t.name,
      description: t.description || "",
      inputSchema: t.inputSchema as Record<string, unknown>,
    }));
  }

  /**
   * Ejecuta una tool por nombre con los argumentos dados.
   */
  async callTool(
    name: string,
    args: Record<string, unknown> = {}
  ): Promise<string> {
    const result = await this.client.callTool({
      name,
      arguments: args,
    });

    // Extraer texto de los contenidos
    const content = "content" in result ? result.content : [];
    const parts = (content as Array<{ type: string; text?: string }>)
      .filter((c) => c.type === "text" && c.text)
      .map((c) => c.text as string);

    return parts.join("\n") || "(sin contenido)";
  }

  /**
   * Lista los resources del servidor (si los hay).
   */
  async listResources(): Promise<
    Array<{ uri: string; name: string; description?: string }>
  > {
    try {
      const result = await this.client.listResources();
      return result.resources.map((r) => ({
        uri: r.uri,
        name: r.name,
        description: r.description,
      }));
    } catch {
      return []; // El servidor puede no soportar resources
    }
  }

  /**
   * Cierra la conexión al servidor.
   */
  async close(): Promise<void> {
    await this.client.close();
    console.log(`[mcp] desconectado de ${this.serverUrl}`);
  }
}
