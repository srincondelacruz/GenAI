"""
Cliente A2A.

1) Descubre el Agent Card del servidor (/.well-known/agent.json).
2) Crea el A2AClient a partir del card.
3) Envía un mensaje en dos modos:
     - message/send    (no-streaming): una sola respuesta.
     - message/stream  (SSE):          eventos incrementales (working → artifact → completed).

Uso:
    python client.py "¿cuánto es 23 * 7 + 4?"
    python client.py --no-stream "hola"
"""

import sys
import uuid
from collections.abc import Iterable

import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendStreamingMessageRequest,
    TextPart,
)

BASE_URL = "http://127.0.0.1:9999"


def make_message(text: str) -> Message:
    return Message(
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
        message_id=uuid.uuid4().hex,
    )


def texts_from(parts: Iterable) -> str:
    """Extrae el texto de una lista de Part."""
    out = []
    for p in parts or []:
        root = getattr(p, "root", p)
        if getattr(root, "kind", None) == "text" or hasattr(root, "text"):
            out.append(getattr(root, "text", ""))
    return " ".join(t for t in out if t)


async def run(text: str, stream: bool) -> None:
    async with httpx.AsyncClient(timeout=60) as httpx_client:
        # 1) Descubrimiento del Agent Card
        resolver = A2ACardResolver(httpx_client, base_url=BASE_URL)
        card = await resolver.get_agent_card()
        print(f"[card] {card.name} — streaming={card.capabilities.streaming}")

        # 2) Cliente A2A
        client = A2AClient(httpx_client, agent_card=card)
        msg = make_message(text)

        if not stream:
            # 3a) message/send — respuesta única
            req = SendMessageRequest(id=uuid.uuid4().hex, params=MessageSendParams(message=msg))
            resp = await client.send_message(req)
            result = resp.root.result  # Task | Message
            artifacts = getattr(result, "artifacts", None) or []
            answer = " ".join(texts_from(a.parts) for a in artifacts) or texts_from(
                getattr(result, "parts", None)
            )
            print(f"\n[send] respuesta:\n{answer or result}")
            return

        # 3b) message/stream — eventos SSE incrementales
        req = SendStreamingMessageRequest(
            id=uuid.uuid4().hex, params=MessageSendParams(message=msg)
        )
        print("\n[stream] eventos:")
        async for chunk in client.send_message_streaming(req):
            event = chunk.root.result
            kind = getattr(event, "kind", type(event).__name__)
            if kind == "status-update":
                state = event.status.state
                note = texts_from(getattr(event.status.message, "parts", None)) if event.status.message else ""
                print(f"  · status={state} {note}")
            elif kind == "artifact-update":
                print(f"  ✓ artifact: {texts_from(event.artifact.parts)}")
            elif kind == "task":
                print(f"  · task creada id={event.id} estado={event.status.state}")
            else:
                print(f"  · {kind}")


if __name__ == "__main__":
    import asyncio

    args = sys.argv[1:]
    stream = "--no-stream" not in args
    text = " ".join(a for a in args if not a.startswith("--")) or "¿Cuánto es 23 * 7 + 4?"
    asyncio.run(run(text, stream))
