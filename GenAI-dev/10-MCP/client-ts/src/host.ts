/**
 * Host MCP + Azure OpenAI — equivalente TypeScript de host.py.
 *
 * Flujo:
 *   1. Conecta al servidor MCP remoto vía client.ts (Streamable HTTP / SSE).
 *   2. listTools() → traduce los tools MCP al formato function-calling de OpenAI.
 *   3. El LLM (Azure OpenAI) decide qué tool llamar; el host ejecuta la llamada
 *      vía callTool() y devuelve el resultado al modelo (bucle ReAct).
 *   4. Cuando el modelo deja de pedir tools, imprime la respuesta final.
 *
 * Uso:
 *   node dist/index.js "¿qué hora es en Tokyo y cuánto es 23*7+4?"
 *   node dist/index.js                # REPL interactivo
 */

import { AzureOpenAI } from "openai";
import type {
  ChatCompletionMessageParam,
  ChatCompletionTool,
} from "openai/resources/index.js";
import { McpClientWrapper, McpToolInfo } from "./client.js";
import { createInterface } from "readline";

const SYSTEM_PROMPT =
  "Eres un asistente útil y conciso. Dispones de herramientas vía MCP. " +
  "Úsalas cuando aporten datos exactos (cálculos, hora, notas). " +
  "Responde en el idioma de la pregunta.";

/**
 * Traduce tools MCP → esquema function-calling de OpenAI.
 */
function toOpenAITools(mcpTools: McpToolInfo[]): ChatCompletionTool[] {
  return mcpTools.map((t) => ({
    type: "function" as const,
    function: {
      name: t.name,
      description: t.description,
      parameters: t.inputSchema,
    },
  }));
}

/**
 * Bucle ReAct: LLM elige tool → callTool(MCP) → resultado → LLM.
 * Repite hasta que el modelo devuelve una respuesta sin tool_calls.
 */
export async function chat(
  mcpClient: McpClientWrapper,
  llm: AzureOpenAI,
  deployment: string,
  question: string,
  tools: ChatCompletionTool[]
): Promise<string> {
  const messages: ChatCompletionMessageParam[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: question },
  ];

  while (true) {
    const resp = await llm.chat.completions.create({
      model: deployment,
      messages,
      tools,
      temperature: 0,
    });

    const msg = resp.choices[0].message;

    // Sin tool_calls → respuesta final
    if (!msg.tool_calls || msg.tool_calls.length === 0) {
      return msg.content || "";
    }

    // Registrar la decisión del modelo
    messages.push({
      role: "assistant",
      content: msg.content,
      tool_calls: msg.tool_calls.map((tc) => ({
        id: tc.id,
        type: "function" as const,
        function: {
          name: tc.function.name,
          arguments: tc.function.arguments,
        },
      })),
    });

    // Ejecutar cada tool vía MCP
    for (const tc of msg.tool_calls) {
      const args = JSON.parse(tc.function.arguments || "{}");
      console.log(`  [tool] ${tc.function.name}(${JSON.stringify(args)})`);

      const result = await mcpClient.callTool(tc.function.name, args);
      messages.push({
        role: "tool",
        tool_call_id: tc.id,
        content: result,
      });
    }
  }
}

/**
 * Punto de entrada principal.
 */
export async function main(): Promise<void> {
  const serverUrl = process.env.MCP_SERVER_URL;
  if (!serverUrl) {
    console.error("Error: MCP_SERVER_URL no está definida en .env");
    process.exit(1);
  }

  const deployment = process.env.AZURE_OPENAI_DEPLOYMENT;
  if (!deployment) {
    console.error("Error: AZURE_OPENAI_DEPLOYMENT no está definida en .env");
    process.exit(1);
  }

  // Conectar al servidor MCP
  const mcpClient = await McpClientWrapper.connect(serverUrl);

  try {
    // Listar tools disponibles
    const mcpTools = await mcpClient.listTools();
    console.log(
      `[mcp] tools: [${mcpTools.map((t) => t.name).join(", ")}]\n`
    );

    const openaiTools = toOpenAITools(mcpTools);

    // Crear cliente Azure OpenAI
    const llm = new AzureOpenAI({
      apiKey: process.env.AZURE_OPENAI_API_KEY,
      endpoint: process.env.AZURE_OPENAI_ENDPOINT,
      apiVersion:
        process.env.AZURE_OPENAI_API_VERSION || "2025-01-01-preview",
    });

    // Modo CLI (argumento) o REPL interactivo
    const cliQuestion = process.argv.slice(2).join(" ").trim();

    if (cliQuestion) {
      const answer = await chat(
        mcpClient,
        llm,
        deployment,
        cliQuestion,
        openaiTools
      );
      console.log(answer);
    } else {
      console.log("Host MCP — escribe tu pregunta (Ctrl-C para salir)\n");

      const rl = createInterface({
        input: process.stdin,
        output: process.stdout,
      });

      const askQuestion = (): void => {
        rl.question("> ", async (q: string) => {
          const trimmed = q.trim();
          if (trimmed) {
            try {
              const answer = await chat(
                mcpClient,
                llm,
                deployment,
                trimmed,
                openaiTools
              );
              console.log("\n" + answer + "\n");
            } catch (err) {
              console.error(
                `Error: ${err instanceof Error ? err.message : String(err)}\n`
              );
            }
          }
          askQuestion();
        });
      };

      rl.on("close", () => {
        console.log("\nbye");
      });

      askQuestion();

      // Esperar a que el REPL cierre antes de desconectar
      await new Promise<void>((resolve) => {
        rl.on("close", resolve);
      });
    }
  } finally {
    await mcpClient.close();
  }
}
