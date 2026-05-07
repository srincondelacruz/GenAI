# Fine-Tuning de Modelos en Azure AI Foundry

En esta práctica aplicarás los conocimientos sobre fine-tuning de modelos de lenguaje en Azure AI Foundry. Entrenarás un modelo personalizado utilizando tu propio dataset y evaluarás su rendimiento comparándolo con el modelo base.

Podrás elegir entre dos modalidades de implementación:
- **Modalidad Portal**: Realizar el fine-tuning desde Azure AI Foundry Studio (requiere video del proceso)
- **Modalidad Python SDK**: Implementar el fine-tuning programáticamente usando código Python

La práctica se divide en una única parte integral y el entregable final será un **Jupyter Notebook** que documente todo el proceso y demuestre el funcionamiento del modelo fine-tuned.

---

## Parte 1) Entrenamiento y Evaluación de Modelo Fine-Tuned
**Objetivo:** Entrenar un modelo de lenguaje personalizado mediante fine-tuning, desplegarlo y evaluar su rendimiento mediante pruebas comparativas y análisis de métricas.

### 1.1 - Preparación del Dataset de Fine-Tuning

Crea o selecciona un dataset personalizado que defina el comportamiento deseado para tu modelo fine-tuned.

**Requisitos del dataset:**
- Formato **JSONL** (JSON Lines) compatible con Chat Completions API
- Mínimo **50-100 ejemplos** de conversaciones (recomendado: 100-300 para mejores resultados)
- Estructura conversacional con roles: `system`, `user`, `assistant`
- División en dos archivos:
  - `training_set.jsonl` (80% de los datos)
  - `validation_set.jsonl` (20% de los datos)

**Ejemplos de casos de uso:**
- Chatbot de soporte técnico especializado en un tema específico
- Asistente que responde con un tono/estilo particular (formal, casual, sarcástico, etc.)
- Generador de contenido en formato específico (JSON, XML, markdown estructurado)
- Asistente de código especializado en un lenguaje o framework
- Sistema de respuestas basado en documentación interna

**Documentación:**
- [Preparación de datos para fine-tuning](https://learn.microsoft.com/es-es/azure/ai-services/openai/how-to/fine-tuning?pivots=programming-language-python#prepare-your-training-and-validation-data)
- [Formato de archivo JSONL para Chat Completions](https://learn.microsoft.com/es-es/azure/ai-services/openai/how-to/fine-tuning?pivots=programming-language-python#example-file-format)

---

### 1.2 - Entrenamiento del Modelo (elegir una modalidad)

Realiza el fine-tuning de un modelo de Azure OpenAI usando el dataset preparado. **Elige UNA de las dos modalidades:**

#### 🖥️ Opción A - Modalidad Portal (Azure AI Foundry Studio)

Si eliges esta modalidad:
- Accede a [Azure AI Foundry](https://ai.azure.com/)
- Navega a la sección **Fine-tuning** y crea un nuevo trabajo
- Configura:
  - **Modelo base**: GPT-4o-mini, GPT-4o, u otro disponible
  - **Training type**: Standard, Global o Developer (justifica tu elección)
  - **Hiperparámetros**: Puedes usar valores automáticos o ajustarlos manualmente
  - **Suffix**: Nombre descriptivo para tu modelo (ej: "soporte-azure-v1")
- Sube los archivos `training_set.jsonl` y `validation_set.jsonl`
- Monitorea el progreso del entrenamiento

**📹 Requisito adicional para esta modalidad:**
- Graba un **video** mostrando la configuración del trabajo de fine-tuning
- Sube el video a SharePoint y proporciona el enlace en el notebook

**Documentación:**
- [Fine-tuning desde Azure AI Foundry Studio](https://learn.microsoft.com/es-es/azure/foundry/openai/how-to/fine-tuning?tabs=turbo%2Cpython-secure&pivots=programming-language-studio)

#### 💻 Opción B - Modalidad Python SDK

Si eliges esta modalidad, implementa el proceso completo usando código:

```python
from openai import AzureOpenAI
import os

# 1. Configurar cliente
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# 2. Subir archivos de entrenamiento
# 3. Crear trabajo de fine-tuning
# 4. Monitorear estado y métricas
```

**Requisitos de implementación:**
- Código para subir archivos de training y validation
- Creación del trabajo de fine-tuning con configuración personalizada
- Función para monitorear el estado del job (`queued`, `running`, `succeeded`)
- Captura y visualización de métricas de entrenamiento
- Manejo de errores y validaciones

**Documentación:**
- [Fine-tuning con Python SDK](https://learn.microsoft.com/es-es/azure/ai-services/openai/how-to/fine-tuning?pivots=programming-language-python)
- [Azure OpenAI Python SDK Reference](https://learn.microsoft.com/es-es/python/api/overview/azure/ai-openai-readme?view=azure-python-preview)

---

### 1.3 - Despliegue del Modelo Fine-Tuned

Una vez completado el entrenamiento con éxito (`succeeded`), despliega tu modelo fine-tuned:

**Configuración del deployment:**
- **Deployment name**: Nombre descriptivo (ej: "chatbot-soporte-v1")
- **Tokens per minute (TPM)**: Configura según tus necesidades (puede ser el mínimo para pruebas)

**Opciones de despliegue:**
- Desde el portal: Sección Fine-tuning → Selecciona tu modelo → Deploy
- Con Python SDK: Usa el SDK de Azure AI para crear el deployment programáticamente

Guarda la información del endpoint y deployment name para las pruebas.

**Documentación:**
- [Desplegar modelos fine-tuned](https://learn.microsoft.com/es-es/azure/ai-services/openai/how-to/fine-tuning?pivots=programming-language-python#deploy-a-fine-tuned-model)

---

### 1.4 - Pruebas y Evaluación del Modelo

Crea pruebas exhaustivas de tu modelo fine-tuned y compara su rendimiento con el modelo base.

**Pruebas a realizar:**

1. **Casos de uso del dataset**: Prueba ejemplos similares a los del entrenamiento
2. **Casos fuera del dataset**: Evalúa generalización con casos nuevos
3. **Casos edge**: Prueba situaciones límite o inusuales
4. **Comparación directa**: Misma pregunta al modelo base y al fine-tuned

**Análisis de métricas:**

Analiza las siguientes métricas del entrenamiento (disponibles en el portal o via API):

- **`training_loss`**: Pérdida en los datos de entrenamiento
  - Debe **disminuir** a lo largo de las épocas
  - Si no disminuye: problemas con datos o hiperparámetros
  
- **`validation_loss`**: Pérdida en los datos de validación
  - Debe **disminuir** de manera similar al training_loss
  - Si aumenta mientras training_loss baja: **overfitting**


**Documentación:**
- [Uso de modelos fine-tuned](https://learn.microsoft.com/es-es/azure/ai-services/openai/how-to/fine-tuning?pivots=programming-language-python#use-a-fine-tuned-model)
- [Interpretación de métricas de fine-tuning](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/fine-tuning?tabs=oai-sdk&pivots=programming-language-studio#metrics)

---

### Entregable:

**Archivo requerido:** Un Jupyter Notebook (`.ipynb`) que incluya:

#### Sección 1: Introducción y Contexto
- **Descripción del caso de uso**: ¿Qué problema resuelve tu modelo fine-tuned?
- **Dataset elegido**: Descripción del tipo de datos y objetivo

#### Sección 2: Proceso de Fine-Tuning
- **Si elegiste Modalidad Portal**: 
  - 📹 **Enlace al video** mostrando el proceso completo
  
- **Si elegiste Modalidad Python SDK**:
  - Código completo del proceso de fine-tuning
  - Outputs mostrando el progreso del entrenamiento
  - Manejo de estados y errores

Debes incluir una pequeña descripción de las configuraciones elegidas

#### Sección 3: Análisis de Métricas
- **Valores** de training_loss y validation_loss por época
- **Interpretación**: ¿El modelo aprendió correctamente? ¿Hay overfitting?
- **Conclusiones** sobre el proceso de entrenamiento

#### Sección 4: Pruebas Comparativas
- Pruebas comparando modelo base vs fine-tuned
- Casos del dataset y casos nuevos
- **Análisis cualitativo**: ¿En qué aspectos mejoró el modelo?

#### Sección 5: Conclusiones (opcional)
- Resumen de resultados obtenidos
- Problemas encontrados y cómo se resolvieron
- Lecciones aprendidas
- Posibles mejoras futuras

---

## ⭐ Extras (Opcional - Suma puntos adicionales)

### Extra 1: Stored Completions para Fine-Tuning con Datos de Producción

Implementa **Stored Completions** para capturar automáticamente interacciones reales de un modelo en producción y usarlas para re-entrenar el modelo de forma continua.

**¿Qué son Stored Completions?**
Azure OpenAI permite almacenar automáticamente las peticiones (prompts) y respuestas (completions) de tu modelo en un Azure Blob Storage. Estos datos pueden usarse para:
- Crear datasets de fine-tuning basados en datos reales de producción
- Mejorar iterativamente el modelo con casos de uso reales
- Auditar y analizar el comportamiento del modelo

Sigue esta **documentación** para guiarte en el proceso:

- [Stored Completions en Azure OpenAI](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/stored-completions?tabs=python-secure)


**Entregable del extra:**
- Notebook (.ipynb) adicional mostrando:
  - Configuración de stored completions (código y/o screenshots)
  - Proceso de extracción y filtrado de datos
  - Análisis de los datos capturados
  - Resultados del re-entrenamiento con datos de producción
  - Comparación antes/después

---

## Formato y criterios de entrega

### Formato de entrega

- **Archivo principal**: Jupyter Notebook (`.ipynb`) autocontenido
- **Archivos adicionales permitidos**:
  - `training_set.jsonl` y `validation_set.jsonl` (tu dataset)
  - Screenshots o imágenes ilustrativas (si son relevantes)
  - **Si elegiste Modalidad Portal**: Enlace al video dentro del notebook (visible en markdown cell)


## Recursos adicionales

### Documentación oficial recomendada

- [Guía completa de Fine-Tuning en Azure OpenAI](https://learn.microsoft.com/es-es/azure/ai-services/openai/how-to/fine-tuning)
- [Consideraciones para Fine-Tuning](https://learn.microsoft.com/es-es/azure/foundry/concepts/fine-tuning-considerations)
- [Pricing de Fine-Tuning](https://azure.microsoft.com/en-us/pricing/details/azure-openai/)
- [Best practices para Fine-Tuning](https://platform.openai.com/docs/guides/fine-tuning)

### Ejemplos

- [Ejemplos de Fine Tuning](https://github.com/openai/openai-cookbook/blob/main/examples/How_to_finetune_chat_models.ipynb)

