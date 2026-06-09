"""
Email Agent — LangGraph + Azure OpenAI + Gmail IMAP/SMTP
Flujo: fetch → [MAP via Send] → N × email_pipeline (sub-grafo) → [REDUCE] → send_summary

Map-Reduce : fetch despacha cada email como sub-grafo paralelo independiente.
             Cada sub-grafo tiene su propio estado aislado; solo 'processed' sube
             al grafo padre mediante el reducer Annotated[list, operator.add].
HITL       : dentro del sub-grafo, human_review_node pausa la rama urgente.
Paralelismo: para emails urgentes, draft y analyze corren en paralelo en el sub-grafo.
"""

import operator
import os
import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command, Send

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


# ── Estados ───────────────────────────────────────────────────────────────────

class EmailState(TypedDict):
    """Estado privado de cada sub-grafo (un email)."""
    current_email:  dict
    classification: str
    draft_reply:    str
    summary:        str
    approved:       bool
    human_feedback: str
    analysis:       str
    processed:      list[dict]   # local; el reducer lo integra en AgentState


class AgentState(TypedDict):
    """Estado del grafo principal."""
    emails:    list[dict]
    processed: Annotated[list[dict], operator.add]   # REDUCE: acumula todas las ramas


# ── Gmail helpers ─────────────────────────────────────────────────────────────

def get_imap_connection() -> imaplib.IMAP4_SSL:
    conn = imaplib.IMAP4_SSL("imap.gmail.com")
    conn.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
    return conn


def decode_header_value(value: str) -> str:
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


# ── Nodo de fetch (grafo principal) ──────────────────────────────────────────

def fetch_node(state: AgentState) -> dict:
    conn = get_imap_connection()
    conn.select("INBOX")

    _, uids = conn.search(None, "UNSEEN")
    uid_list = uids[0].split()[-10:]

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
    return {"emails": emails}


# ── Nodos del sub-grafo (procesan UN email) ───────────────────────────────────

def classify_node(state: EmailState) -> dict:
    """MAP: clasifica el email asignado a esta rama."""
    current = state["current_email"]
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
    return {"classification": classification, "draft_reply": "", "summary": "", "analysis": ""}


def urgent_dispatch_node(state: EmailState) -> dict:
    """Nodo puente para el fan-out paralelo draft + analyze dentro del sub-grafo."""
    return {}


def draft_node(state: EmailState) -> dict:
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
    return {"draft_reply": draft, "approved": False, "human_feedback": ""}


def analyze_node(state: EmailState) -> dict:
    """PARALELO con draft: extrae puntos clave del email urgente."""
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
    return {"analysis": analysis}


def human_review_node(state: EmailState) -> dict:
    """HITL: pausa el sub-grafo y espera decisión del operador."""
    email_data = state["current_email"]
    decision: str = interrupt({
        "action":       "review_draft",
        "subject":      email_data["subject"],
        "from":         email_data["from"],
        "draft":        state["draft_reply"],
        "analysis":     state.get("analysis", ""),
        "instructions": "Responde 'approve', 'reject' o 'edit: <nuevo texto>'",
    })
    decision = decision.strip()
    if decision.lower().startswith("edit:"):
        new_draft = decision[5:].strip()
        return {"approved": True, "draft_reply": new_draft, "human_feedback": new_draft}
    elif decision.lower() == "approve":
        return {"approved": True, "human_feedback": ""}
    else:
        return {"approved": False, "human_feedback": ""}


def send_node(state: EmailState) -> dict:
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

    print(f"[send] Respuesta enviada a '{recipient}'")
    return {"processed": [{
        "subject":        email_data["subject"],
        "from":           email_data["from"],
        "classification": "urgent",
        "action":         "respuesta enviada",
        "draft":          draft,
    }]}


def skip_send_node(state: EmailState) -> dict:
    email_data = state["current_email"]
    print(f"[skip_send] Borrador rechazado para '{email_data['subject']}'")
    return {"processed": [{
        "subject":        email_data["subject"],
        "from":           email_data["from"],
        "classification": "urgent",
        "action":         "borrador rechazado",
    }]}


def summarize_node(state: EmailState) -> dict:
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
        "summary": summary,
        "processed": [{
            "subject":        email_data["subject"],
            "from":           email_data["from"],
            "classification": "info",
            "action":         "resumido",
            "summary":        summary,
        }],
    }


def archive_node(state: EmailState) -> dict:
    email_data = state["current_email"]
    uid = email_data["uid"]

    conn = get_imap_connection()
    conn.select("INBOX")
    conn.uid("COPY", uid, "[Gmail]/Spam")
    conn.uid("STORE", uid, "+FLAGS", "\\Deleted")
    conn.expunge()
    conn.logout()

    print(f"[archive] '{email_data['subject']}' movido a spam")
    return {"processed": [{
        "subject":        email_data["subject"],
        "from":           email_data["from"],
        "classification": "spam",
        "action":         "archivado como spam",
    }]}


# ── Routers del sub-grafo ─────────────────────────────────────────────────────

def router(state: EmailState) -> str:
    return state["classification"]


def review_router(state: EmailState) -> str:
    return "send" if state.get("approved") else "skip_send"


# ── Nodo reduce (grafo principal) ─────────────────────────────────────────────

def send_summary_node(state: AgentState) -> dict:
    """REDUCE: recibe todos los processed de las ramas y envía el resumen por email."""
    info_emails = [e for e in state["processed"] if e.get("summary")]

    if not info_emails:
        print("[send_summary] Sin emails informativos, no se envía resumen.")
        return {}

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
    return {}


# ── Sub-grafo: pipeline de un email ──────────────────────────────────────────

def build_email_subgraph():
    """Construye el sub-grafo que procesa UN email con HITL y paralelismo interno."""
    g = StateGraph(EmailState)

    g.add_node("classify",        classify_node)
    g.add_node("urgent_dispatch", urgent_dispatch_node)
    g.add_node("draft",           draft_node)
    g.add_node("analyze",         analyze_node)
    g.add_node("human_review",    human_review_node)
    g.add_node("send",            send_node)
    g.add_node("skip_send",       skip_send_node)
    g.add_node("summarize",       summarize_node)
    g.add_node("archive",         archive_node)

    g.set_entry_point("classify")
    g.add_conditional_edges("classify", router,
                            {"urgent": "urgent_dispatch", "info": "summarize", "spam": "archive"})

    # Fan-out paralelo dentro del sub-grafo (urgentes)
    g.add_edge("urgent_dispatch", "draft")
    g.add_edge("urgent_dispatch", "analyze")
    g.add_edge("draft",   "human_review")
    g.add_edge("analyze", "human_review")
    g.add_conditional_edges("human_review", review_router, {"send": "send", "skip_send": "skip_send"})

    for node in ("send", "skip_send", "summarize", "archive"):
        g.add_edge(node, END)

    return g.compile()


email_pipeline = build_email_subgraph()


# ── MAP: despacha emails al sub-grafo ─────────────────────────────────────────

def dispatch_emails(state: AgentState) -> list[Send]:
    """MAP: crea una rama paralela por cada email detectado."""
    return [
        Send("email_pipeline", {
            "current_email":  e,
            "classification": "",
            "draft_reply":    "",
            "summary":        "",
            "approved":       False,
            "human_feedback": "",
            "analysis":       "",
            "processed":      [],
        })
        for e in state["emails"]
    ]


# ── Grafo principal ───────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    graph.add_node("fetch",          fetch_node)
    graph.add_node("email_pipeline", email_pipeline)
    graph.add_node("send_summary",   send_summary_node)

    graph.set_entry_point("fetch")

    # fetch → MAP (N ramas paralelas, una por email)
    graph.add_conditional_edges("fetch", dispatch_emails, ["email_pipeline"])

    # REDUCE: cuando todas las ramas terminan, LangGraph ejecuta send_summary
    graph.add_edge("email_pipeline", "send_summary")
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

    result = app.invoke({"emails": [], "processed": []}, config)

    # HITL loop: una interrupción por cada email urgente pendiente de revisión
    while True:
        snapshot = app.get_state(config)
        if not snapshot.next:
            break

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

        decision = input("Tu decisión: ").strip() or "reject"
        result = app.invoke(Command(resume=decision), config)

    print_summary(result["processed"])
