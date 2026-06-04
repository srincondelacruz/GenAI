# Telegram News Agent

Bot de Telegram con IA que busca noticias en internet y, con confirmación del usuario, envía un informe formateado por email.

Replica en Python el workflow de n8n: **Telegram Trigger → AI Agent (Azure OpenAI + SerpAPI) → Human-in-the-loop → Gmail**.

---

## Flujo

```
Usuario escribe en Telegram
        ↓
   Agente LangChain
   (Azure OpenAI + SerpAPI)
        ↓
  ¿Usó SerpAPI?
    ├─ NO → Responde en Telegram
    └─ SÍ → Envía respuesta + botones [✅ Sí] [❌ No]
                  ↓
        Usuario pulsa botón
          ├─ ✅ Sí → Envía informe HTML por Gmail
          └─ ❌ No → Cancela
```

---

## Requisitos

- Python 3.10+
- Cuenta de Azure con un despliegue de Azure OpenAI
- API Key de SerpAPI
- Bot de Telegram (creado con @BotFather)
- Cuenta de Gmail con App Password

---

## Instalación

### 1. Clona el repositorio y entra en la carpeta

```bash
git clone <url-del-repo>
cd 06-n8n-agent
```

### 2. Crea y activa el entorno virtual

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 4. Configura las variables de entorno

Copia el fichero de ejemplo y rellénalo:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
TELEGRAM_BOT_TOKEN=        # Token del bot de Telegram
AZURE_OPENAI_API_KEY=      # API Key de Azure OpenAI
AZURE_OPENAI_ENDPOINT=     # https://tu-recurso.cognitiveservices.azure.com
AZURE_OPENAI_DEPLOYMENT=   # Nombre del despliegue, ej: gpt-4o-mini
AZURE_OPENAI_API_VERSION=  # ej: 2025-01-01-preview
SERPAPI_API_KEY=            # API Key de SerpAPI
GMAIL_ADDRESS=              # tu@gmail.com
GMAIL_APP_PASSWORD=         # App Password de Google (16 caracteres)
```

### 5. Arranca el bot

```bash
python main.py
```

---

## Cómo obtener cada credencial

### Telegram Bot Token
1. Abre Telegram y busca **@BotFather**
2. Escribe `/newbot` y sigue las instrucciones
3. Copia el token que te da

### Azure OpenAI
1. Ve a [portal.azure.com](https://portal.azure.com)
2. Crea un recurso **Azure OpenAI**
3. En **Deployments**, despliega un modelo (ej: `gpt-4o-mini`)
4. En **Keys and Endpoint** copia la key y el endpoint

### SerpAPI
1. Regístrate en [serpapi.com](https://serpapi.com)
2. Ve a tu dashboard y copia la API Key

### Gmail App Password
1. Ve a [myaccount.google.com](https://myaccount.google.com)
2. Activa la **verificación en dos pasos** si no la tienes
3. Busca **Contraseñas de aplicaciones**
4. Crea una nueva para "Correo" → te da un código de 16 caracteres
5. Pónlo en `GMAIL_APP_PASSWORD`

---

## Estructura del proyecto

```
06-n8n-agent/
├── main.py           # Bot de Telegram y lógica human-in-the-loop
├── agent.py          # Agente LangChain con Azure OpenAI y SerpAPI
├── email_sender.py   # Conversión Markdown→HTML y envío por Gmail
├── requirements.txt  # Dependencias
├── .env.example      # Plantilla de variables de entorno
└── README.md
```

### `main.py`
Punto de entrada. Gestiona dos tipos de eventos de Telegram:
- **Mensajes de texto** → los pasa al agente y muestra la respuesta
- **Callbacks de botones** → gestiona la confirmación de envío de email

### `agent.py`
Núcleo del agente. Usa LangChain con:
- **AzureChatOpenAI** como modelo de lenguaje
- **SerpAPIWrapper** como herramienta de búsqueda web
- **ConversationBufferMemory** para mantener el historial por chat
- Un wrapper sobre SerpAPI que detecta si fue invocado durante la ejecución

### `email_sender.py`
Convierte la respuesta del agente (Markdown) a HTML y la envía por Gmail via SMTP SSL. La función `_md_to_html` procesa negritas, enlaces, fechas y elimina las imágenes de thumbnail.

---

## Uso

Una vez arrancado el bot, escríbele en Telegram:

```
dame las noticias de hoy
```

El bot responderá con las noticias y mostrará dos botones:

- **✅ Sí, enviar informe al correo** → envía un email HTML con el resumen
- **❌ No** → cancela sin enviar nada

Para preguntas que no requieren búsqueda web:

```
¿Qué es la inteligencia artificial?
```

El bot responderá directamente sin mostrar los botones de email.

---

## Dependencias principales

| Paquete | Versión | Para qué |
|---|---|---|
| python-telegram-bot | 21.9 | Bot de Telegram |
| langchain | 0.2.16 | Framework del agente |
| langchain-openai | 0.1.23 | Integración Azure OpenAI |
| langchain-community | 0.2.16 | SerpAPI wrapper |
| google-search-results | 2.4.2 | Cliente SerpAPI |
| python-dotenv | 1.0.0 | Variables de entorno |
