# agent.py — núcleo del agente LangChain
# Conecta Azure OpenAI con la herramienta de búsqueda SerpAPI.
# Mantiene memoria conversacional separada por chat_id.

from langchain_openai import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os

# Diccionario global que guarda una instancia de memoria por cada chat de Telegram.
# Esto replica el nodo "Simple Memory" de n8n, manteniendo el historial de conversación.
_memory_store: dict = {}


def _get_memory(chat_id: str) -> ConversationBufferMemory:
    """Devuelve la memoria conversacional del chat, creándola si no existe."""
    if chat_id not in _memory_store:
        _memory_store[chat_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return _memory_store[chat_id]


async def run_agent(message: str, chat_id: str) -> dict:
    """
    Ejecuta el agente con el mensaje del usuario.
    Devuelve la respuesta y si se usó SerpAPI durante la ejecución.
    """
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        temperature=0,
    )

    # Usamos un dict mutable como flag porque las closures de Python
    # no permiten reasignar variables del ámbito externo con '='
    used = {"serpapi": False}

    search = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))

    def tracked_search(query: str) -> str:
        """Wrapper de SerpAPI que activa el flag al ser invocado por el agente."""
        used["serpapi"] = True
        return search.run(query)

    tools = [
        Tool(
            name="search",
            func=tracked_search,
            description="Útil para buscar noticias actuales e información reciente en internet.",
        )
    ]

    # El prompt incluye instrucciones estrictas de formato para que el email
    # quede bien estructurado sin necesidad de postprocesado complejo
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un asistente útil que puede buscar información en internet. Responde siempre en español.
Cuando presentes noticias, usa EXACTAMENTE este formato para cada noticia:

1. **[Título de la noticia](url)**
*Fuente: nombre_fuente*
*Fecha: fecha*
Resumen breve de 2-3 frases explicando de qué trata.

No uses ### ni ningún otro encabezado Markdown."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=_get_memory(chat_id),
        verbose=True,
        return_intermediate_steps=True,
    )

    result = await executor.ainvoke({"input": message})

    # El output puede quedar vacío cuando la respuesta contiene bloques de código.
    # En ese caso recuperamos el contenido del último paso intermedio del agente.
    output = result.get("output", "").strip()
    if not output and result.get("intermediate_steps"):
        last_step = result["intermediate_steps"][-1]
        output = str(last_step[-1]) if last_step else ""

    return {
        "output": output,
        "used_serpapi": used["serpapi"],
    }
