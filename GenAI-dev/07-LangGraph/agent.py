"""
Email Agent — LangGraph + Azure OpenAI + Gmail IMAP/SMTP
Flujo: fetch → classify → router → draft | summarize | archive → END
"""

import os
import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

load_dotenv()

# ── LLM (Azure OpenAI) ────────────────────────────────────────────────────────

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=0,
)

GMAIL_ADDRESS  = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# ── Estado del agente ─────────────────────────────────────────────────────────

class AgentState(TypedDict):
    emails: list[dict]          # emails pendientes de procesar
    current_email: dict         # email que se está procesando ahora
    classification: str         # "urgent" | "info" | "spam"
    draft_reply: str            # borrador de respuesta (solo urgent)
    summary: str                # resumen de una línea (solo info)
    processed: list[dict]       # log de todos los emails procesados


# ── Gmail helpers (IMAP) ──────────────────────────────────────────────────────

def get_imap_connection() -> imaplib.IMAP4_SSL:
    """Abre una conexión IMAP autenticada con Gmail."""
    conn = imaplib.IMAP4_SSL("imap.gmail.com")
    conn.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
    return conn


def decode_header_value(value: str) -> str:
    """Decodifica headers de email que pueden estar en base64 o quoted-printable."""
    from email.header import decode_header
    parts = decode_header(value or "")
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="ignore"))
        else:
            result.append(part)
    return "".join(result)


def extract_body(msg: email.message.Message) -> str:
    """Extrae el texto plano del cuerpo del email."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                return payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
    return ""


# ── Nodos ─────────────────────────────────────────────────────────────────────

def fetch_node(state: AgentState) -> AgentState:
    """
    Conecta a Gmail via IMAP y lee los últimos 10 emails no leídos de la bandeja
    de entrada. Extrae subject, remitente, uid y primeros 2000 caracteres del body.
    """
    conn = get_imap_connection()
    conn.select("INBOX")

    _, uids = conn.search(None, "UNSEEN")
    uid_list = uids[0].split()[-10:]   # últimos 10 no leídos

    emails = []
    for uid in uid_list:
        _, data = conn.fetch(uid, "(RFC822)")
        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        emails.append({
            "uid":     uid.decode(),
            "subject": decode_header_value(msg.get("Subject", "(sin asunto)")),
            "from":    decode_header_value(msg.get("From", "")),
            "body":    extract_body(msg)[:2000],
        })

    conn.logout()
    print(f"[fetch] {len(emails)} emails no leídos encontrados")
    return {**state, "emails": emails, "processed": []}


def classify_node(state: AgentState) -> AgentState:
    """
    Extrae el primer email de la cola y lo clasifica con el LLM en:
    'urgent' (requiere respuesta), 'info' (informativo) o 'spam'.
    Elimina el email de la lista para que el bucle avance.
    """
    emails = state["emails"]
    current = emails[0]

    prompt = f"""Clasifica el siguiente email en exactamente una de estas categorías:
- urgent: requiere respuesta o acción inmediata
- info: informativo, no requiere acción
- spam: correo no deseado, publicidad o phishing

Responde ÚNICAMENTE con una de estas tres palabras: urgent, info, spam

Asunto: {current['subject']}
De: {current['from']}
Contenido: {current['body'][:500]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    classification = response.content.strip().lower()

    if classification not in ("urgent", "info", "spam"):
        classification = "info"

    print(f"[classify] '{current['subject']}' → {classification}")
    return {
        **state,
        "current_email":  current,
        "emails":         emails[1:],
        "classification": classification,
        "draft_reply":    "",
        "summary":        "",
    }


def draft_node(state: AgentState) -> AgentState:
    """
    Para emails urgentes: redacta una respuesta profesional con el LLM y la guarda
    en el estado. No envía el email — solo genera el borrador para revisión humana.
    """
    email_data = state["current_email"]

    prompt = f"""Redacta una respuesta profesional y concisa al siguiente email.
La respuesta debe ser breve (máximo 3 párrafos) y en el mismo idioma que el email original.

Asunto: {email_data['subject']}
De: {email_data['from']}
Contenido: {email_data['body']}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    draft = response.content.strip()

    print(f"[draft] Borrador generado para '{email_data['subject']}'")

    return {
        **state,
        "draft_reply": draft,
        "processed": state["processed"] + [{
            "subject":        email_data["subject"],
            "from":           email_data["from"],
            "classification": "urgent",
            "action":         "borrador generado",
            "draft":          draft,
        }],
    }


def summarize_node(state: AgentState) -> AgentState:
    """
    Para emails informativos: genera un resumen de una sola frase con el LLM.
    Permite tener un log rápido de lo recibido sin leer cada email completo.
    """
    email_data = state["current_email"]

    prompt = f"""Resume en UNA sola frase (máximo 15 palabras) el contenido del siguiente email.
Responde solo con la frase, sin puntuación final ni comillas.

Asunto: {email_data['subject']}
Contenido: {email_data['body'][:300]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    summary = response.content.strip().rstrip(".")

    print(f"[summarize] '{email_data['subject']}' → {summary}")

    return {
        **state,
        "summary": summary,
        "processed": state["processed"] + [{
            "subject":        email_data["subject"],
            "from":           email_data["from"],
            "classification": "info",
            "action":         "resumido",
            "summary":        summary,
        }],
    }


def archive_node(state: AgentState) -> AgentState:
    """
    Para emails spam: mueve el email a la carpeta [Gmail]/Spam via IMAP.
    Copia el mensaje a Spam y lo elimina de INBOX marcándolo como borrado.
    """
    email_data = state["current_email"]
    uid = email_data["uid"]

    conn = get_imap_connection()
    conn.select("INBOX")

    # Copia a Spam y borra de INBOX
    conn.uid("COPY", uid, "[Gmail]/Spam")
    conn.uid("STORE", uid, "+FLAGS", "\\Deleted")
    conn.expunge()
    conn.logout()

    print(f"[archive] '{email_data['subject']}' movido a spam")

    return {
        **state,
        "processed": state["processed"] + [{
            "subject":        email_data["subject"],
            "from":           email_data["from"],
            "classification": "spam",
            "action":         "archivado como spam",
        }],
    }


# ── Router y condición de parada ──────────────────────────────────────────────

def router(state: AgentState) -> str:
    """Devuelve el nodo siguiente según la clasificación del email actual."""
    return state["classification"]


def should_continue(state: AgentState) -> str:
    """Si quedan emails en la cola vuelve a classify; si no, termina."""
    return "classify" if state["emails"] else "end"


# ── Construcción del grafo ────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("fetch",     fetch_node)
    graph.add_node("classify",  classify_node)
    graph.add_node("draft",     draft_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("archive",   archive_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "classify")

    graph.add_conditional_edges(
        "classify",
        router,
        {"urgent": "draft", "info": "summarize", "spam": "archive"}
    )

    for node in ("draft", "summarize", "archive"):
        graph.add_conditional_edges(
            node,
            should_continue,
            {"classify": "classify", "end": END}
        )

    return graph.compile()


# ── Tabla resumen final ───────────────────────────────────────────────────────

def print_summary(processed: list[dict]):
    if not processed:
        print("\nNo se procesaron emails.")
        return

    w = [48, 12, 30]
    sep = "-" * (sum(w) + 4)
    print(f"\n{'=' * (sum(w) + 4)}")
    print("RESUMEN DE EMAILS PROCESADOS")
    print(f"{'=' * (sum(w) + 4)}")
    print(f"{'ASUNTO':<{w[0]}}  {'CLASIF.':<{w[1]}}  {'ACCIÓN':<{w[2]}}")
    print(sep)
    for e in processed:
        print(f"{e['subject'][:w[0]]:<{w[0]}}  {e['classification']:<{w[1]}}  {e['action'][:w[2]]:<{w[2]}}")
    print(sep)
    print(f"Total: {len(processed)}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_graph()

    final_state = app.invoke({
        "emails":         [],
        "current_email":  {},
        "classification": "",
        "draft_reply":    "",
        "summary":        "",
        "processed":      [],
    })

    print_summary(final_state["processed"])
