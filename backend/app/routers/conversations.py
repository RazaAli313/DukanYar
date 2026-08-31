"""Conversations router — TEXT-2 model integration & streaming reply.

POST /conversations/{conversation_id}/messages

The backend is stateless in this ticket (no DB). The frontend sends recent
turns in the request body; this router forwards them to the LLM and streams
the reply back as Server-Sent Events.
"""

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import APIError, APITimeoutError
from pydantic import BaseModel, Field

from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / response models ────────────────────────────────────────────────

class Turn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class MessageRequest(BaseModel):
    text: str
    channel: str = "text"
    recent_turns: list[Turn] = Field(default_factory=list)


# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse_event(event: str, data: dict) -> str:
    """Format a single named SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, body: MessageRequest):
    """Stream an LLM reply via SSE.

    Pre-stream errors → HTTP 502 JSON.
    Mid-stream errors → named `error` event, then stream closes.
    """

    # Build the full message list for the LLM
    messages: list[dict[str, str]] = [
        {"role": t.role, "content": t.content} for t in body.recent_turns
    ]
    messages.append({"role": "user", "content": body.text})

    async def event_stream():
        try:
            async for delta in llm.stream_reply(messages):
                yield _sse_event("delta", {"text": delta})
            yield _sse_event("done", {})
        except (APIError, APITimeoutError) as exc:
            logger.warning("LLM error mid-stream: %s", exc)
            yield _sse_event("error", {"detail": f"LLM error: {exc}"})
        except Exception as exc:
            logger.exception("Unexpected error mid-stream")
            yield _sse_event("error", {"detail": f"Internal error: {exc}"})

    # Pre-flight validation: try to create the client before streaming starts.
    # This catches missing/bad config early so we can return a proper HTTP error
    # instead of a half-written stream.
    try:
        llm._get_client()  # noqa: SLF001 — intentional pre-flight check
    except Exception as exc:
        logger.exception("LLM client init failed")
        raise HTTPException(status_code=502, detail=f"LLM config error: {exc}") from exc

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering if present
        },
    )
