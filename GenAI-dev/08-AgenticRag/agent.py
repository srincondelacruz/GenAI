"""
RAG Agéntico — LangGraph + Azure OpenAI + Chroma (embeddings HuggingFace).

Flujo:
    retrieve → grade_documents → ┬─ (relevantes)    → generate → END
                                 └─ (no relevantes)  → rewrite → retrieve  (loop, máx N)

Qué lo hace "agéntico" (no un RAG lineal):
  - grade_documents : el LLM juzga si los chunks recuperados sirven para la pregunta.
  - rewrite         : si no sirven, el LLM reformula la query y se reintenta.
  - decisión        : el grafo decide solo entre responder o re-buscar, con tope de
                      reescrituras (MAX_REWRITES) para evitar bucles infinitos.

Uso:
    python agent.py "¿tu pregunta?"
    python agent.py                 # modo REPL interactivo
"""

import os
import sys
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from store import get_vectorstore

load_dotenv()

MAX_REWRITES = 2   # reescrituras antes de rendirse y responder con lo que haya
TOP_K        = 4   # chunks por recuperación

# ── LLM (Azure OpenAI) ────────────────────────────────────────────────────────

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    temperature=0,
)

retriever = get_vectorstore().as_retriever(search_kwargs={"k": TOP_K})


# ── Estado ────────────────────────────────────────────────────────────────────

class RagState(TypedDict):
    question:  str            # pregunta actual (puede reescribirse)
    original:  str            # pregunta original del usuario (no cambia)
    documents: list[Document] # chunks recuperados
    generation: str           # respuesta final
    rewrites:  int            # nº de reescrituras hechas


# ── Nodos ─────────────────────────────────────────────────────────────────────

def retrieve_node(state: RagState) -> dict:
    """Recupera chunks de Chroma para la pregunta actual."""
    docs = retriever.invoke(state["question"])
    print(f"[retrieve] '{state['question']}' → {len(docs)} chunks")
    return {"documents": docs}


def grade_documents_node(state: RagState) -> dict:
    """El LLM filtra: deja solo los chunks relevantes a la pregunta."""
    question = state["question"]
    kept: list[Document] = []

    for d in state["documents"]:
        prompt = (
            "Eres un evaluador de relevancia. ¿El siguiente fragmento contiene "
            "información útil para responder la pregunta?\n"
            "Responde ÚNICAMENTE 'si' o 'no'.\n\n"
            f"Pregunta: {question}\n\n"
            f"Fragmento: {d.page_content[:1500]}"
        )
        verdict = llm.invoke([HumanMessage(content=prompt)]).content.strip().lower()
        if verdict.startswith("s"):
            kept.append(d)

    print(f"[grade] {len(kept)}/{len(state['documents'])} chunks relevantes")
    return {"documents": kept}


def rewrite_node(state: RagState) -> dict:
    """Reformula la query para mejorar la recuperación."""
    prompt = (
        "Reformula la siguiente pregunta para que una búsqueda semántica recupere "
        "mejores resultados. Mantén la intención original. Responde solo con la nueva "
        "pregunta, sin explicaciones.\n\n"
        f"Pregunta original: {state['original']}\n"
        f"Última pregunta:   {state['question']}"
    )
    new_q = llm.invoke([HumanMessage(content=prompt)]).content.strip()
    n = state["rewrites"] + 1
    print(f"[rewrite #{n}] → {new_q}")
    return {"question": new_q, "rewrites": n}


def generate_node(state: RagState) -> dict:
    """Genera la respuesta final a partir de los chunks relevantes."""
    docs = state["documents"]
    if docs:
        context = "\n\n---\n\n".join(d.page_content for d in docs)
        sys_msg = (
            "Eres un asistente que responde apoyándote en el contexto dado. "
            "Sintetiza e infiere a partir de los fragmentos para construir la mejor "
            "respuesta posible, aunque no haya una definición literal. Solo di que "
            "falta información si el contexto es claramente ajeno al tema. "
            "Responde conciso y en el idioma de la pregunta."
        )
        user = f"Contexto:\n{context}\n\nPregunta: {state['original']}"
    else:
        sys_msg = "Eres un asistente honesto."
        user = (
            f"No se encontró contexto relevante para: {state['original']}\n"
            "Indica que no hay información suficiente en la base de conocimiento."
        )

    answer = llm.invoke(
        [SystemMessage(content=sys_msg), HumanMessage(content=user)]
    ).content.strip()
    print("[generate] respuesta lista")
    return {"generation": answer}


# ── Router ────────────────────────────────────────────────────────────────────

def decide(state: RagState) -> Literal["generate", "rewrite"]:
    """Si hay chunks relevantes → responder. Si no y quedan intentos → reescribir."""
    if state["documents"]:
        return "generate"
    if state["rewrites"] < MAX_REWRITES:
        return "rewrite"
    return "generate"   # sin contexto, pero agotados los reintentos → responder honesto


# ── Grafo ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(RagState)

    g.add_node("retrieve", retrieve_node)
    g.add_node("grade",    grade_documents_node)
    g.add_node("rewrite",  rewrite_node)
    g.add_node("generate", generate_node)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", decide, {"generate": "generate", "rewrite": "rewrite"})
    g.add_edge("rewrite", "retrieve")
    g.add_edge("generate", END)

    return g.compile()


app = build_graph()


def ask(question: str) -> str:
    result = app.invoke({
        "question":  question,
        "original":  question,
        "documents": [],
        "generation": "",
        "rewrites":  0,
    })
    return result["generation"]


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("\n" + ask(" ".join(sys.argv[1:])))
    else:
        print("RAG Agéntico — escribe tu pregunta (Ctrl-C para salir)\n")
        try:
            while True:
                q = input("> ").strip()
                if q:
                    print("\n" + ask(q) + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\nbye")
