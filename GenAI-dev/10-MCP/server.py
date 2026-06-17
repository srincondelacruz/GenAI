"""
Servidor MCP (Model Context Protocol) — transporte stdio.

Expone 3 herramientas de utilidad vía FastMCP. El host (host.py) lo lanza como
subproceso y se comunica por stdin/stdout — el mismo mecanismo que usa Claude
Desktop. Los esquemas JSON de cada tool se generan solos desde los type hints.

Probar suelto:  python server.py        (queda esperando JSON-RPC por stdin)
Inspeccionar:   npx @modelcontextprotocol/inspector python server.py
"""

import ast
import operator as op
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="utilidades-demo",
    instructions="Servidor MCP con calculadora, hora actual y notas en memoria.",
)

# ── Calculadora (evaluador aritmético seguro) ─────────────────────────────────

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


@mcp.tool()
def calculator(expression: str) -> str:
    """Evalúa una expresión aritmética (+ - * / ** % y paréntesis). Ej: '23 * 7 + 4'."""
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error al evaluar '{expression}': {e}"


# ── Hora actual ───────────────────────────────────────────────────────────────

@mcp.tool()
def current_time(timezone: str = "Europe/Madrid") -> str:
    """Devuelve la fecha y hora actual en la zona horaria dada (IANA, ej: 'Europe/Madrid')."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except Exception:
        return f"Zona horaria desconocida: '{timezone}'"
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


# ── Notas en memoria ──────────────────────────────────────────────────────────

_NOTES: list[str] = []


@mcp.tool()
def add_note(text: str) -> str:
    """Guarda una nota en memoria. Devuelve el índice asignado."""
    _NOTES.append(text)
    return f"Nota #{len(_NOTES)} guardada."


@mcp.tool()
def list_notes() -> str:
    """Lista todas las notas guardadas en esta sesión."""
    if not _NOTES:
        return "No hay notas."
    return "\n".join(f"{i}. {n}" for i, n in enumerate(_NOTES, 1))


if __name__ == "__main__":
    mcp.run(transport="stdio")
