"""
Email Agent — LangGraph + Azure OpenAI + Gmail IMAP/SMTP
Flujo: fetch → classify → router → draft → human_review → send | summarize | archive → END

Human-in-the-Loop: antes de enviar cualquier respuesta urgente el agente se detiene,
muestra el borrador y espera aprobación explícita del operador.
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
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

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
    approved: bool              # HITL: True si el operador aprobó el borrador
    human_feedback: str         # HITL: texto alternativo si el operador editó el borrador
    analysis: str               # PARALELO: análisis de puntos clave extraído junto con el borrador


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

    # Devuelve solo los campos que modifica (regla en nodos paralelos)
    return {"draft_reply": draft, "approved": False, "human_feedback": ""}


def urgent_dispatch_node(state: AgentState) -> AgentState:
    """Nodo puente que activa el fan-out paralelo draft + analyze para emails urgentes."""
    return state


def analyze_node(state: AgentState) -> AgentState:
    """
    PARALELO con draft_node: analiza el email urgente y extrae puntos clave,
    acción requerida e indicadores de urgencia para ayudar al revisor humano.
    """
    email_data = state["current_email"]

    prompt = f"""Analiza el siguiente email urgente y responde en formato estructurado:

1. PUNTOS CLAVE (máximo 3 bullets)
2. ACCIÓN REQUERIDA (una frase)
3. INDICADORES DE URGENCIA (¿por qué es urgente?)

Asunto: {email_data['subject']}
De: {email_data['from']}
Contenido: {email_data['body'][:800]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    analysis = response.content.strip()

    print(f"[analyze] Análisis completado para '{email_data['subject']}'")

    # Devuelve solo los campos que modifica (regla en nodos paralelos)
    return {"analysis": analysis}


def human_review_node(state: AgentState) -> AgentState:
    """
    HITL: pausa el grafo y muestra el borrador al operador.
    El operador puede responder:
      - 'approve'        → enviar el borrador tal cual
      - 'reject'         → descartar el borrador, no enviar nada
      - 'edit: <texto>'  → reemplazar el borrador con el texto indicado y enviar
    """
    email_data = state["current_email"]
    decision: str = interrupt({
        "action":    "review_draft",
        "subject":   email_data["subject"],
        "from":      email_data["from"],
        "draft":     state["draft_reply"],
        "analysis":  state.get("analysis", ""),
        "instructions": "Responde 'approve', 'reject' o 'edit: <nuevo texto>'",
    })

    decision = decision.strip()
    if decision.lower().startswith("edit:"):
        new_draft = decision[5:].strip()
        return {**state, "approved": True, "draft_reply": new_draft, "human_feedback": new_draft}
    elif decision.lower() == "approve":
        return {**state, "approved": True, "human_feedback": ""}
    else:
        return {**state, "approved": False, "human_feedback": ""}


def send_node(state: AgentState) -> AgentState:
    """
    Envía el borrador aprobado al remitente del email original via SMTP de Gmail.
    Solo se ejecuta si el operador aprobó (approved=True).
    """
    email_data = state["current_email"]
    draft = state["draft_reply"]
    recipient = email_data["from"]
    subject = f"Re: {email_data['subject']}"

    msg = MIMEText(draft, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [recipient], msg.as_string())

    print(f"[send] Respuesta enviada a '{recipient}' (asunto: {subject})")

    return {
        **state,
        "processed": state["processed"] + [{
            "subject":        email_data["subject"],
            "from":           email_data["from"],
            "classification": "urgent",
            "action":         "respuesta enviada",
            "draft":          draft,
        }],
    }


def skip_send_node(state: AgentState) -> AgentState:
    """Registra el email urgente como descartado cuando el operador rechazó el borrador."""
    email_data = state["current_email"]
    print(f"[skip_send] Borrador rechazado para '{email_data['subject']}'")
    return {
        **state,
        "processed": state["processed"] + [{
            "subject":        email_data["subject"],
            "from":           email_data["from"],
            "classification": "urgent",
            "action":         "borrador rechazado",
        }],
    }


def review_router(state: AgentState) -> str:
    """Dirige a send si el operador aprobó, o a skip_send si rechazó."""
    return "send" if state.get("approved") else "skip_send"


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
    """Si quedan emails en la cola vuelve a classify; si no, pasa al resumen final."""
    return "classify" if state["emails"] else "send_summary"


def send_summary_node(state: AgentState) -> AgentState:
    """
    Nodo final: envía un email de resumen consolidado con todos los emails
    informativos procesados. Si no hay ninguno, no envía nada.
    """
    info_emails = [e for e in state["processed"] if e.get("summary")]

    if not info_emails:
        print("[send_summary] Sin emails informativos, no se envía resumen.")
        return state

    lines = ["Resumen de emails informativos recibidos:\n"]
    for i, e in enumerate(info_emails, 1):
        lines.append(f"{i}. [{e['from']}]")
        lines.append(f"   Asunto: {e['subject']}")
        lines.append(f"   Resumen: {e['summary']}\n")

    body = "\n".join(lines)
    subject = f"📋 Resumen de bandeja de entrada — {len(info_emails)} emails informativos"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = GMAIL_ADDRESS

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [GMAIL_ADDRESS], msg.as_string())

    print(f"[send_summary] Resumen enviado a {GMAIL_ADDRESS} ({len(info_emails)} emails)")
    return state


# ── Construcción del grafo ────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    graph.add_node("fetch",            fetch_node)
    graph.add_node("classify",         classify_node)
    graph.add_node("urgent_dispatch",  urgent_dispatch_node)
    graph.add_node("draft",            draft_node)
    graph.add_node("analyze",          analyze_node)
    graph.add_node("human_review",     human_review_node)
    graph.add_node("send",             send_node)
    graph.add_node("skip_send",        skip_send_node)
    graph.add_node("summarize",        summarize_node)
    graph.add_node("archive",          archive_node)
    graph.add_node("send_summary",     send_summary_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "classify")

    graph.add_conditional_edges(
        "classify",
        router,
        {"urgent": "urgent_dispatch", "info": "summarize", "spam": "archive"}
    )

    # Fan-out paralelo: urgent_dispatch lanza draft y analyze simultáneamente
    graph.add_edge("urgent_dispatch", "draft")
    graph.add_edge("urgent_dispatch", "analyze")

    # Fan-in: human_review espera a que draft y analyze terminen antes de ejecutarse
    graph.add_edge("draft",   "human_review")
    graph.add_edge("analyze", "human_review")

    graph.add_conditional_edges(
        "human_review",
        review_router,
        {"send": "send", "skip_send": "skip_send"}
    )

    for node in ("send", "skip_send", "summarize", "archive"):
        graph.add_conditional_edges(
            node,
            should_continue,
            {"classify": "classify", "send_summary": "send_summary"}
        )

    graph.add_edge("send_summary", END)

    return graph.compile(checkpointer=checkpointer)


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
        if e.get("summary"):
            print(f"  ↳ {e['summary']}")
        if e.get("draft"):
            print(f"  ↳ borrador: {e['draft'][:80]}…")
    print(sep)
    print(f"Total: {len(processed)}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    checkpointer = MemorySaver()
    app = build_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "email-session-1"}}

    initial_state = {
        "emails":         [],
        "current_email":  {},
        "classification": "",
        "draft_reply":    "",
        "summary":        "",
        "processed":      [],
        "approved":       False,
        "human_feedback": "",
        "analysis":       "",
    }

    result = app.invoke(initial_state, config)

    # Loop de HITL: el grafo puede interrumpirse varias veces (una por cada email urgente)
    while True:
        snapshot = app.get_state(config)
        if not snapshot.next:
            break  # el grafo terminó

        # Extraer los datos del interrupt
        interrupt_data = snapshot.tasks[0].interrupts[0].value
        print("\n" + "=" * 60)
        print("REVISIÓN HUMANA REQUERIDA")
        print("=" * 60)
        print(f"De:     {interrupt_data['from']}")
        print(f"Asunto: {interrupt_data['subject']}")
        if interrupt_data.get("analysis"):
            print(f"\n--- ANÁLISIS ---\n{interrupt_data['analysis']}")
        print(f"\n--- BORRADOR ---\n{interrupt_data['draft']}\n")
        print(interrupt_data["instructions"])
        print("-" * 60)

        decision = input("Tu decisión: ").strip()
        if not decision:
            decision = "reject"

        result = app.invoke(Command(resume=decision), config)

    print_summary(result["processed"])
