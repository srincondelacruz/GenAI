"""
Test de ejecución del Email Agent con HITL y paralelización.
Responde automáticamente 'reject' a todos los borradores (no envía emails).
"""
import time
from agent import build_graph, print_summary
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

checkpointer = MemorySaver()
app = build_graph(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "test-parallel-1"}}

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

print("Iniciando agente...")
t0 = time.time()
result = app.invoke(initial_state, config)
print(f"Primera ejecución: {time.time()-t0:.1f}s")

interrupt_count = 0
while True:
    snapshot = app.get_state(config)
    if not snapshot.next:
        break

    interrupt_count += 1
    interrupt_data = snapshot.tasks[0].interrupts[0].value

    print(f"\n{'='*65}")
    print(f"  REVISIÓN HUMANA #{interrupt_count}")
    print(f"{'='*65}")
    print(f"  De:     {interrupt_data['from']}")
    print(f"  Asunto: {interrupt_data['subject']}")

    if interrupt_data.get("analysis"):
        print(f"\n--- ANÁLISIS (paralelo) ---\n{interrupt_data['analysis']}")

    print(f"\n--- BORRADOR (paralelo) ---\n{interrupt_data['draft']}")
    print(f"\n{'-'*65}")

    decision = "reject"   # seguro para test — no envía
    print(f"  [AUTO-TEST] Decisión automática: '{decision}'")

    t1 = time.time()
    result = app.invoke(Command(resume=decision), config)
    print(f"  Reanudado en {time.time()-t1:.1f}s")

print(f"\nTotal de interrupciones HITL: {interrupt_count}")
print(f"Tiempo total: {time.time()-t0:.1f}s")
print_summary(result["processed"])
