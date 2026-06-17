"""
Ingesta: URLs → documentos → chunks → embeddings → Chroma.

Uso:
    python ingest.py                # lee urls.txt
    python ingest.py https://a https://b   # URLs por CLI
    python ingest.py --reset        # borra la colección antes de indexar
"""

import sys
import os

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from store import get_vectorstore, PERSIST_DIR

CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 150


def load_urls(args: list[str]) -> list[str]:
    """URLs desde CLI; si no hay, desde urls.txt (una por línea, # = comentario)."""
    cli = [a for a in args if a.startswith("http")]
    if cli:
        return cli

    path = os.path.join(os.path.dirname(__file__), "urls.txt")
    if not os.path.exists(path):
        sys.exit("No hay URLs: pásalas por CLI o crea urls.txt")

    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def main():
    args  = sys.argv[1:]
    reset = "--reset" in args

    urls = load_urls(args)
    print(f"[ingest] {len(urls)} URLs a indexar")

    # 1) Cargar páginas web
    docs = []
    for url in urls:
        try:
            loaded = WebBaseLoader(url).load()
            docs.extend(loaded)
            print(f"[load] OK  {url}  ({len(loaded)} doc)")
        except Exception as e:
            print(f"[load] ERR {url} → {e}")

    if not docs:
        sys.exit("No se cargó ningún documento.")

    # 2) Trocear
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    print(f"[split] {len(chunks)} chunks")

    # 3) Vectorstore
    vs = get_vectorstore()
    if reset:
        # vacía la colección sin borrar el directorio
        try:
            vs.delete_collection()
            vs = get_vectorstore()
            print("[reset] colección vaciada")
        except Exception as e:
            print(f"[reset] aviso: {e}")

    # 4) Indexar (embeddings HuggingFace locales)
    vs.add_documents(chunks)
    print(f"[done] indexados {len(chunks)} chunks en {PERSIST_DIR}")


if __name__ == "__main__":
    main()
