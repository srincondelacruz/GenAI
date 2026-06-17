/**
 * Herramientas MCP — portadas del server.py original.
 *
 * Cada función registra una tool en el McpServer.
 * Esquemas generados con Zod → el SDK los expone como JSON Schema.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

// ── Estado en memoria (notas) ────────────────────────────────────────────────
const notes: string[] = [];

/**
 * Registra todas las tools en el servidor MCP proporcionado.
 */
export function registerTools(server: McpServer): void {
  // ── Calculadora (evaluador aritmético seguro) ────────────────────────────
  server.tool(
    "calculator",
    "Evalúa una expresión aritmética (+ - * / ** % y paréntesis). Ej: '23 * 7 + 4'.",
    { expression: z.string().describe("Expresión aritmética a evaluar") },
    async ({ expression }) => {
      try {
        // Validar que solo contenga caracteres aritméticos seguros
        if (!/^[\d\s+\-*/%().]+$/.test(expression)) {
          return {
            content: [
              {
                type: "text" as const,
                text: `Error: la expresión '${expression}' contiene caracteres no permitidos. Solo se permiten números y operadores (+, -, *, /, %, **, paréntesis).`,
              },
            ],
          };
        }

        // Evaluación segura usando Function con scope restringido
        const sanitized = expression.replace(/\*\*/g, "**");
        const result = new Function(`"use strict"; return (${sanitized})`)();

        return {
          content: [{ type: "text" as const, text: String(result) }],
        };
      } catch (e) {
        return {
          content: [
            {
              type: "text" as const,
              text: `Error al evaluar '${expression}': ${e instanceof Error ? e.message : String(e)}`,
            },
          ],
        };
      }
    }
  );

  // ── Hora actual ──────────────────────────────────────────────────────────
  server.tool(
    "current_time",
    "Devuelve la fecha y hora actual en la zona horaria dada (IANA, ej: 'Europe/Madrid').",
    {
      timezone: z
        .string()
        .default("Europe/Madrid")
        .describe("Zona horaria IANA (ej: 'Europe/Madrid', 'Asia/Tokyo')"),
    },
    async ({ timezone }) => {
      try {
        const now = new Date();
        const formatted = now.toLocaleString("es-ES", {
          timeZone: timezone,
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          timeZoneName: "short",
        });
        return {
          content: [{ type: "text" as const, text: formatted }],
        };
      } catch {
        return {
          content: [
            {
              type: "text" as const,
              text: `Zona horaria desconocida: '${timezone}'`,
            },
          ],
        };
      }
    }
  );

  // ── Notas en memoria ────────────────────────────────────────────────────
  server.tool(
    "add_note",
    "Guarda una nota en memoria. Devuelve el índice asignado.",
    { text: z.string().describe("Texto de la nota a guardar") },
    async ({ text }) => {
      notes.push(text);
      return {
        content: [
          { type: "text" as const, text: `Nota #${notes.length} guardada.` },
        ],
      };
    }
  );

  server.tool(
    "list_notes",
    "Lista todas las notas guardadas en esta sesión.",
    {},
    async () => {
      if (notes.length === 0) {
        return {
          content: [{ type: "text" as const, text: "No hay notas." }],
        };
      }
      const list = notes.map((n, i) => `${i + 1}. ${n}`).join("\n");
      return {
        content: [{ type: "text" as const, text: list }],
      };
    }
  );
}
