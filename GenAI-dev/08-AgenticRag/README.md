# 08 — RAG Agéntico

RAG que **decide** en vez de ejecutar un pipeline fijo. LangGraph + Azure OpenAI
(generación/grading/reescritura) + Chroma con embeddings HuggingFace locales.

## Flujo

```
retrieve → grade_documents ─┬─ relevantes    → generate → END
                            └─ no relevantes  → rewrite  → retrieve  (loop, máx 2)
```

- **grade_documents**: el LLM descarta chunks irrelevantes.
- **rewrite**: si nada sirve, reformula la query y reintenta (tope `MAX_REWRITES`).
- **generate**: responde solo con el contexto; si no hay, lo admite.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # rellena las claves Azure
```

## Uso

```bash
# 1) Indexar fuentes (edita urls.txt o pasa URLs por CLI)
python ingest.py
python ingest.py https://ejemplo.com/doc --reset

# 2) Preguntar
python agent.py "¿qué es un agente LLM?"
python agent.py                # REPL interactivo
```

## Archivos

| Archivo          | Rol                                              |
|------------------|--------------------------------------------------|
| `store.py`       | Embeddings HF + Chroma persistente (compartido)  |
| `ingest.py`      | URLs → chunks → vectorstore                       |
| `agent.py`       | Grafo agéntico + CLI/REPL                          |
| `urls.txt`       | Fuentes a indexar                                 |

Embeddings locales (`all-MiniLM-L6-v2`): sin coste API. Solo Azure se usa para el LLM.
