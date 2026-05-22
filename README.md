# IA Generativa — Prácticas del Máster

Prácticas del módulo de **IA Generativa** del Máster en IA & Big Data (Tajamar / Microsoft).

El módulo se divide en dos itinerarios complementarios: uno centrado en **consumir servicios de IA en la nube** (Azure) y otro en **construir modelos desde cero** con Python.

---

## Estructura

```
GenAI-client/                         # Itinerario cloud — Azure AI
  01-Foundry_Exploration/              # Texto, JSON estructurado, guardrails, razonamiento, multimodal
  02-prompt_engineering-models_parameters/   # Técnicas de prompting y parámetros del modelo
  03-fine_tuning/                      # Fine-tuning de un modelo en Azure AI Foundry
  04-embeddings_y_vector_database/     # Azure AI Search: vector, hybrid y semantic search

GenAI-dev/                            # Itinerario dev — modelos desde cero (Keras / PyTorch)
  01-RNA/                              # Red neuronal densa — regresión de precios de vivienda
  02-CNN/                              # Red convolucional — clasificación de imágenes
  03-GANs/                             # Generative Adversarial Network
  04-autoencoders-gans/                # Autoencoders para detección de anomalías
```

Cada práctica incluye su enunciado en `PRACTICA.md` y el entregable en uno o varios notebooks `.ipynb`.

---

## Itinerario client — Azure AI

Uso de servicios gestionados de IA generativa en la nube, sin entrenar modelos propios desde cero.

### 01 — Foundry Exploration
Exploración de Azure AI Foundry en tres partes:
- Generación de texto, salida en **JSON estructurado** y **guardrails** de content safety
- **Razonamiento** y **function calling**
- Modelos **multimodales**

### 02 — Prompt Engineering y parámetros
Experimentación con técnicas de prompt engineering (mínimo 6) y con el efecto de los parámetros del modelo (`temperature`, `top_p`, penalties) sobre la respuesta. Aplicación de las técnicas a casos de uso reales.

### 03 — Fine-tuning
Fine-tuning de un modelo de lenguaje en Azure AI Foundry mediante el **Python SDK**: dataset propio en formato JSONL dividido en `training_set` / `validation_set`, despliegue del modelo y evaluación comparativa frente al modelo base. Incluye capturas del despliegue y de las métricas de entrenamiento.

### 04 — Embeddings y Vector Database
Pipeline de indexación con el wizard *Import data* de **Azure AI Search** (vectorización integrada sobre documentos en Blob Storage) y ejecución de los cuatro modos de búsqueda: **vector, hybrid, semantic y semantic hybrid search**.

---

## Itinerario dev — modelos desde cero

Construcción, entrenamiento y evaluación de redes neuronales con Python (Keras / PyTorch).

### 01 — RNA (Red Neuronal Artificial)
Red neuronal densa con Keras para **predecir el precio de viviendas** (regresión sobre dataset tabular de Kaggle). Incluye preprocesado, escalado de features, modelo serializado (`.keras` + `scaler.pkl`) y una app de inferencia.

### 02 — CNN (Red Neuronal Convolucional)
Red convolucional para **clasificación de imágenes** (reconocimiento de dibujos del dataset QuickDraw). Incluye una app con frontend web para dibujar y clasificar en tiempo real.

### 03 — GANs
Implementación de una **Generative Adversarial Network**: red generadora y discriminadora entrenadas de forma adversarial para sintetizar muestras nuevas.

### 04 — Autoencoders para detección de anomalías
**Autoencoders** con PyTorch aplicados a detección de anomalías, incluyendo una variante *denoising*. La idea: el autoencoder aprende a reconstruir lo normal, y el error de reconstrucción alto señala anomalías.

---

## Cómo ejecutar

**Itinerario client:** requiere una cuenta de Azure con los recursos correspondientes (Azure AI Foundry, Azure OpenAI, Azure AI Search). Cada notebook documenta sus credenciales y deployments necesarios.

**Itinerario dev:** notebooks ejecutables en local o en Google Colab.

```bash
pip install tensorflow keras torch scikit-learn pandas numpy matplotlib
```

Las apps de los itinerarios `01-RNA` y `02-CNN` se lanzan con:

```bash
python app.py
```
