"""
Puente A2A ↔ LangGraph.

AgentExecutor traduce un mensaje A2A entrante en:
  task submitted → working (progreso) → artifact (respuesta) → completed
Soporta no-streaming (message/send) y streaming (message/stream): el mismo
execute() emite eventos a la EventQueue; el SDK los entrega como SSE o
respuesta única según el método que use el cliente.
"""

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from agent import LangGraphAgent


class LangGraphAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = LangGraphAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()

        # Reutiliza la task si ya existe (multi-turno); si no, créala.
        task = context.current_task
        if task is None:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        async for item in self.agent.stream(query, task.context_id):
            if not item["done"]:
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(item["content"], task.context_id, task.id),
                )
            else:
                await updater.add_artifact(
                    [Part(root=TextPart(text=item["content"]))],
                    name="respuesta",
                )
                await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Este agente no soporta cancelación.
        raise ServerError(error=UnsupportedOperationError())
