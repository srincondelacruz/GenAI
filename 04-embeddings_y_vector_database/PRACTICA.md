# PRACTICA: Embeddings y Vector Database (Azure AI Search)

> Formato: MD. Entrega en la carpeta del tema. Esta práctica tiene dos partes: documentación del wizard (Import data) y ejecución de búsquedas.

---

## Resumen

Objetivo: Crear y documentar un pipeline de indexación por medio del wizard "Import data" del portal de Azure (vectorización integrada). Posteriormente realizar búsquedas contra el índice creado: Vector Search, Hybrid Search, Semantic Search y Semantic Hybrid Search. Incluir capturas, explicaciones y resultados.

---

## Requisitos previos

- Cuenta Azure con recurso Azure AI Search (Basic o superior recomendado).
- Contenedor en Azure Blob Storage con documentos (PDF/DOCX/HTML).
- Recurso Azure OpenAI con deployment de embeddings.

---

## PARTE 1 — Creación del índice mediante el wizard (Import data)

Esta parte es documental: seguir el wizard en el portal para crear el índice. Entregar en este archivo las capturas y explicaciones.

Pasos (portal):
1. En el recurso de **Azure AI Search** seleccionar **Import data**.
2. Elegir escenario: **RAG** (no agentic retrieval).
3. Conectar a **Azure Blob Storage** (seleccionar contenedor con documentos). Autenticación por Managed Identity o clave.
4. En vectorización elegir proveedor (Azure OpenAI / Foundry) y deployment de embeddings.
5. Revisar la inferencia del esquema y ajustar campos si hace falta.
6. Finalizar: el wizard crea Data Source, Index, Skillset (si se activó enrichment), Indexer y Knowledge Store opcional.

### Capturas y explicaciones que hay que adjuntar

- **ÍNDICE (Index schema)**: capturar la definición del índice creado.
- **SEMANTIC CONFIGURATION**: captura del objeto semántico creado. Explicar qué es y cómo está configurado.
- **VECTOR PROFILE**: captura de la sección `Algorithm` y `Vectorizer` del índice. Explicar cada una de ellas y cómo están configuradas
- **SKILLSET**: captura del skillset generado por el wizard. Explicar qué es y los pasos que contiene
---

## PARTE 2 — Búsquedas prácticas (ejecución en Python)

Entregar un script o notebook (.ipynb recomendado) con ejecuciones de los siguientes tipos de búsqueda y ejemplos de resultados (top-5):

1. Vector Search
2. Hybrid Search (vector + keyword)
3. Semantic Search (query_type=semantic)
4. Semantic Hybrid Search (semantic + vector)

[Referencia para semantic ranking](https://github.com/Azure-Samples/azure-search-python-samples/blob/main/Quickstart-Semantic-Ranking/semantic-ranking-quickstart.ipynb)
[Referencia para vector search](https://github.com/Azure-Samples/azure-search-python-samples/blob/main/Quickstart-Vector-Search/vector-search-quickstart.ipynb)


## ⭐ Extra (elige al menos UNA opción y documenta)

A. Añadir una **custom skill** (OCR o endpoint propio) al skillset: documentar su implementación y efecto en indexing. Referencia: https://learn.microsoft.com/en-us/azure/search/cognitive-search-defining-skillset

B. Añadir un **scoring profile** al índice y explicar cómo afecta al ranking. Referencia: https://learn.microsoft.com/es-es/azure/search/index-add-scoring-profiles?tabs=python

C. Implementar **multimodal search** (texto + imágenes) si los documentos contienen imágenes. Referencia: https://learn.microsoft.com/en-us/azure/search/multimodal-search-overview

---

## Entregables (qué debe contener la entrega)

1. Un archivo en formato .docx, .ipynb o .md documentando la Parte 1
2. `practica_vector_search.ipynb` o `practica_vector_search.py` con la Parte 2 ejecutada y resultados incluidos.
4. (Opcional) Documentación y explicación de la implementación del extra elegido

---
