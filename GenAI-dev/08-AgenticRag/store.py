"""
Capa de almacenamiento vectorial — HuggingFace embeddings + Chroma persistente.

Embeddings LOCALES (sentence-transformers): sin coste API, sin deployment extra.
Chroma persiste en disco (PERSIST_DIR); ingest.py lo llena, agent.py lo consulta.
"""

import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Modelo de embeddings local MULTILINGÜE: permite query en español sobre corpus
# en inglés (cross-lingual). 384 dims, sin prefijos especiales.
EMBED_MODEL  = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
PERSIST_DIR  = os.getenv("CHROMA_DIR", os.path.join(os.path.dirname(__file__), "chroma_db"))
COLLECTION   = "agentic_rag"

_embeddings = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Singleton: cargar el modelo de embeddings una sola vez (es caro)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    """Abre (o crea) la colección Chroma persistente."""
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIR,
    )
