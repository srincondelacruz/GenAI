# Práctica: Prompt Engineering y Parametrización de Modelos

Esta práctica tiene como objetivo experimentar de forma práctica con técnicas de prompt engineering y parámetros de modelos de IA generativa. Se divide en **2 partes independientes**, cada una entregable como un notebook `.ipynb` separado.

**🎯 Objetivo general:** Comprender mediante experimentación cómo diferentes técnicas de prompting y configuraciones de parámetros afectan las respuestas de modelos IAG, desarrollando criterio para aplicarlas en casos reales.

---

## 1) Exploración de Técnicas de Prompt Engineering

**Objetivo:** Experimentar con técnicas de prompt engineering, entendiendo su propósito y efectividad en distintos contextos.

### 1.1 - Selección y Prueba de Técnicas
Debes **seleccionar al menos 6 técnicas** de las documentadas en `TEORIA.md` (las que te resulten más interesantes o útiles). Si quieres probar más de 6, adelante.

Para cada técnica seleccionada:
- **Explica** qué es la técnica **con tus propias palabras** (no copies la definición de la teoría)
- **Diseña un ejemplo práctico** usando Azure AI Foundry u OpenAI API
- **Ejecuta el prompt** y muestra la respuesta del modelo
- **Analiza el resultado**: ¿funcionó como esperabas? ¿qué ventajas observaste? ¿en qué casos usarías esta técnica?

**Documentación:** Consulta el archivo `TEORIA.md` de este mismo directorio para entender cada técnica.

### 1.2 - Aplicación de Técnicas en Casos Reales
Después de probar las técnicas individualmente, **elige 2 casos de uso reales** (por ejemplo: generación de documentación técnica, análisis de sentimiento, extracción de datos estructurados, etc.) y aplica las técnicas más apropiadas para cada caso. Justifica por qué elegiste esas técnicas.

### Entregable (Parte 1):
Notebook `.ipynb` que incluya:
- **Sección de configuración** (imports, credenciales/API keys, conexión al modelo)
- **Una sección por cada técnica probada** con:
  - Explicación de la técnica (con tus palabras)
  - Código del prompt
  - Salida del modelo
  - Análisis crítico del resultado
- **Sección de casos de uso reales** con aplicación práctica
- **Conclusiones personales**: ¿Qué técnicas te parecieron más útiles? ¿Cuáles usarías en proyectos futuros? (opcional)

---

## 2) Experimentación con Parámetros del Modelo

**Objetivo:** Entender cómo los parámetros del modelo (temperature, top_p, penalties) modifican el comportamiento de las respuestas generadas.

### 2.1 - Experimentación con temperature
Prueba el **mismo prompt** con diferentes valores de `temperature`:
- `temperature = 0.0`
- `temperature = 0.5`
- `temperature = 1.0`
- `temperature = 1.5` (si la API lo permite)

Analiza cómo cambian las respuestas. Usa un caso práctico (ejemplo: generar un eslogan, escribir código, responder una pregunta técnica).

### 2.2 - Experimentación con top_p
Prueba el **mismo prompt** con diferentes valores de `top_p`:
- `top_p = 0.1`
- `top_p = 0.5`
- `top_p = 0.9`
- `top_p = 1.0`

Mantén `temperature = 1.0` para ver el efecto puro de top_p. Compara con los resultados de temperature.

### 2.3 - Experimentación con Penalties
Prueba prompts que **tiendan a repetir contenido** (por ejemplo: describir un producto, generar múltiples ideas similares) con:
- `presence_penalty = 0.0` vs `presence_penalty = 0.6`
- `frequency_penalty = 0.0` vs `frequency_penalty = 0.8`
- Combinación de ambos penalties

Analiza qué tipo de repeticiones evita cada uno.

### 2.4 - Preguntas Teóricas (Responder con tus propias palabras)
Incluye una sección en el notebook respondiendo estas preguntas basándote en tu experiencia práctica y lo aprendido:

1. **¿Cuál es la diferencia entre top_p y temperature?**
2. **¿Por qué no se recomienda ajustar top_p y temperature al mismo tiempo?**
3. **¿Cuál es la diferencia entre presence_penalty y frequency_penalty?**

### Entregable (Parte 2):
Notebook `.ipynb` que incluya:
- **Sección de configuración** (imports, credenciales, modelo)
- **Una sección por parámetro experimentado** con:
  - Código mostrando diferentes configuraciones
  - Salidas del modelo para cada configuración
  - Análisis comparativo: ¿cómo afecta cada valor?
- **Sección de preguntas teóricas** con tus respuestas reflexivas (no copiadas)
- **Conclusiones**: ¿Qué configuración usarías para cada tipo de tarea? (código, creatividad, extracción de datos, etc.)

---

## ⭐ Extras

Funcionalidades adicionales que suman puntos:

- **Técnicas adicionales no documentadas:** Investiga y prueba técnicas de prompt engineering que NO aparezcan en `TEORIA.md` pero que uses habitualmente o descubras en tu investigación (cita las fuentes consultadas).

- **Documentación tipo tutorial:** Estructura el notebook como un mini-tutorial que otro estudiante podría seguir para aprender sobre el tema.

---

## Formato y criterios de entrega

- **Formato:** Dos notebooks `.ipynb` separados (uno por cada parte), autocontenidos y ejecutables.
- Requisitos mínimos que debe incluir cada notebook:
	- **Sección de configuración** clara (imports, credenciales, modelo a usar)
	- **Código reproducible y documentado** con comentarios explicativos
	- **Salidas visibles** de todas las ejecuciones (no limpies los outputs del notebook)
	- **Análisis y reflexiones propias** escritas con tus palabras, no copiadas de la teoría
	- **Markdown bien estructurado** con títulos, subtítulos y secciones claras que faciliten la lectura
