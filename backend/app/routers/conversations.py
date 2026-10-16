"""Conversation transport for the unified LLM tool orchestration loop.

POST /conversations/{conversation_id}/messages  send a message, stream the reply
POST /conversations/actions/{id}/confirm        execute an approval-gated tool
POST /conversations/actions/{id}/reject         reject an approval-gated tool
DELETE /conversations/actions/{id}              undo a committed tool
GET  /conversations/history                     reload the thread

Auth: ``Authorization: Bearer <supabase access token>``; the shop is resolved
from the profile, never the body. The conversation is the shop's single thread;
the path id is ignored.

Dashboard modes are prompt hints only. The model always sees the complete tool
registry and decides which tool or sequence of tools matches the request.
"""

import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from openai import APIError, APITimeoutError
from pydantic import BaseModel, Field

from app.auth import CurrentUserDep
from app.config import settings
from app.services import conversations as convo
from app.services import llm
from app.services import tool_calls as tool_call_store
from app.tools.registry import get_registry

logger = logging.getLogger(__name__)

router = APIRouter()

Mode = Literal["sale", "udhaar", "kharcha", "ask", "maal"]


class Turn(BaseModel):
    role: str
    content: str


class MessageRequest(BaseModel):
    text: str
    channel: Literal["text", "voice"] = "text"
    mode: Mode = "ask"
    transcription_confidence: float | None = None
    #: Deprecated — context comes from the DB now. Accepted so old clients don't 422.
    recent_turns: list[Turn] = Field(default_factory=list, deprecated=True)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── send a message ───────────────────────────────────────────────────────────

@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, body: MessageRequest, user: CurrentUserDep):
    try:
        llm._get_client()  # noqa: SLF001 — pre-flight before any write
    except Exception as exc:
        logger.exception("LLM client init failed")
        raise HTTPException(status_code=502, detail=f"LLM config error: {exc}") from exc

    conversation = convo.get_or_create_conversation(shop_id=user.shop_id, user_id=user.user_id)
    conv_id = conversation["id"]
    prior = convo.recent_turns(conversation_id=conv_id, max_turns=settings.llm_max_context_turns)

    # Voice transcripts arrive in Urdu script; store and reason over Roman-Urdu
    # so the whole thread reads the way the shopkeeper types.
    user_text = body.text
    if body.channel == "voice":
        user_text = await llm.to_roman_urdu(body.text)

    user_message = convo.add_message(
        conversation_id=conv_id,
        sender=convo.SENDER_USER,
        content=user_text,
        channel=body.channel,
        transcription_confidence=(
            body.transcription_confidence if body.channel == "voice" else None
        ),
    )
    turns = prior + [{"role": "user", "content": user_text}]

    # Execution context passed to every tool handler.
    tool_ctx = {"shop_id": user.shop_id, "user_id": user.user_id}

    async def _run_tools(tool_calls: list, ctx: dict) -> list[dict]:
        """Execute tool calls returned by the model and collect results."""
        registry = get_registry()
        results: list[dict] = []
        for tc in tool_calls:
            fn = tc.function
            tool_def = registry.get(fn.name)
            if tool_def is None:
                results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": json.dumps({"ok": False, "error": f"Unknown tool: {fn.name}"}),
                })
                continue
            try:
                params = json.loads(fn.arguments or "{}")
            except json.JSONDecodeError:
                params = {}
            audit = tool_call_store.create(
                message_id=user_message["id"],
                tool_name=fn.name,
                params=params,
                status=(
                    "pending_approval"
                    if tool_def.risk_tier == "approval_required"
                    else "pending"
                ),
            )
            if tool_def.risk_tier == "approval_required":
                results.append(
                    {
                        "tool_call_id": tc.id,
                        "role": "tool",
                        "content": json.dumps(
                            {"ok": True, "pending_approval": True}
                        ),
                        "audit_id": audit["id"],
                        "tool_name": fn.name,
                        "params": params,
                        "pending_approval": True,
                    }
                )
                continue
            try:
                result = await tool_def.handler(params, ctx)
            except Exception as exc:
                logger.exception("Tool handler %s raised", fn.name)
                result = {"ok": False, "error": str(exc)}
            tool_call_store.resolve(
                tool_call_id=audit["id"],
                status="committed" if result.get("ok") else "failed",
                response=result,
            )
            results.append({
                "tool_call_id": tc.id,
                "role": "tool",
                "content": json.dumps(result),
                "audit_id": audit["id"],
                "tool_name": fn.name,
                "params": params,
            })
        return results

    async def event_stream():
        def persist(text: str, status: str) -> None:
            if not text.strip():
                return
            try:
                convo.add_message(
                    conversation_id=conv_id,
                    sender=convo.SENDER_ASSISTANT,
                    content=text,
                    channel=body.channel,
                    status=status,
                )
            except Exception:
                logger.exception("failed to persist assistant reply")

        yield _sse("meta", {"conversation_id": conv_id, "user_text": user_text})

        try:
            in_scope = await llm.is_shop_request(turns)
        except (APIError, APITimeoutError) as exc:
            yield _sse("error", {"detail": f"LLM error: {exc}"})
            return
        except Exception as exc:
            logger.exception("Unexpected scope-classification error")
            yield _sse("error", {"detail": f"Internal error: {exc}"})
            return

        if not in_scope:
            reply = (
                "Main sirf aapki dukaan, maal, sale, khata aur kharchay mein "
                "madad kar sakta hoon."
            )
            for word in reply.split(" "):
                yield _sse("delta", {"text": word + " "})
            persist(reply, convo.STATUS_COMPLETE)
            yield _sse("done", {"conversation_id": conv_id})
            return

        # ── every mode uses one LLM-directed tool loop (TOOL-2) ─────────────
        # The dashboard mode is only a prompt hint. It never hard-routes the
        # request or limits the tool schemas the model may select.
        registry = get_registry()
        tool_schemas = registry.schemas()
        orchestration_turns = list(turns)
        for _round in range(5):
            try:
                msg = await llm.tool_call_reply(
                    orchestration_turns,
                    tool_schemas,
                    channel=body.channel,
                    mode=body.mode,
                )
            except (APIError, APITimeoutError) as exc:
                yield _sse("error", {"detail": f"LLM error: {exc}"})
                return
            except Exception as exc:
                logger.exception("Unexpected orchestration error")
                yield _sse("error", {"detail": f"Internal error: {exc}"})
                return

            if not msg.tool_calls:
                reply = (msg.content or "").strip()
                for word in reply.split(" ") if reply else []:
                    yield _sse("delta", {"text": word + " "})
                persist(reply, convo.STATUS_COMPLETE)
                yield _sse("done", {"conversation_id": conv_id})
                return

            yield _sse("delta", {"text": ""})
            tool_results = await _run_tools(msg.tool_calls, tool_ctx)

            pending_approval = False
            for tr in tool_results:
                try:
                    payload = json.loads(tr["content"])
                    is_pending = bool(tr.get("pending_approval"))
                    pending_approval = pending_approval or is_pending
                    definition = registry.get(tr["tool_name"])
                    card = (
                        definition.presenter(
                            params=tr["params"],
                            result=payload,
                            tool_call_id=tr["audit_id"],
                            status=(
                                "proposed"
                                if is_pending
                                else ("recorded" if payload.get("ok") else "failed")
                            ),
                        )
                        if definition and definition.presenter
                        else None
                    )
                    if card:
                        yield _sse("action", card)
                    yield _sse(
                        "tool_result",
                        {
                            "tool_call_id": tr["tool_call_id"],
                            "result": payload,
                        },
                    )
                except Exception:
                    logger.exception("Failed to emit tool result")

            if pending_approval:
                reply = "Details check karke tasdeeq karein."
                for word in reply.split(" "):
                    yield _sse("delta", {"text": word + " "})
                persist(reply, convo.STATUS_COMPLETE)
                yield _sse("done", {"conversation_id": conv_id})
                return

            orchestration_turns.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            orchestration_turns.extend(
                {
                    "tool_call_id": tr["tool_call_id"],
                    "role": "tool",
                    "content": tr["content"],
                }
                for tr in tool_results
            )

        detail = "Ek message mein bohat zyada actions aaye. Dobara chhota karke boliye."
        yield _sse("error", {"detail": detail})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/actions/{tool_call_id}/confirm")
async def confirm_tool_action(tool_call_id: str, user: CurrentUserDep) -> dict[str, Any]:
    call = tool_call_store.get_for_shop(
        tool_call_id=tool_call_id, shop_id=user.shop_id
    )
    if call is None:
        raise HTTPException(404, "Ye pending action nahi mila.")
    if call["status"] != "pending_approval":
        raise HTTPException(409, "Ye action pending approval mein nahi hai.")

    tool_def = get_registry().get(call["tool_name"])
    if tool_def is None:
        raise HTTPException(422, "Is action ka tool available nahi hai.")
    if not tool_call_store.claim_approval(tool_call_id=tool_call_id):
        raise HTTPException(409, "Ye action pehle hi process ho raha hai.")

    try:
        result = await tool_def.handler(
            call["params"], {"shop_id": user.shop_id, "user_id": user.user_id}
        )
    except Exception as exc:
        logger.exception("Approved tool handler %s raised", call["tool_name"])
        result = {"ok": False, "error": str(exc), "reply": str(exc)}

    status = "committed" if result.get("ok") else "failed"
    tool_call_store.resolve(
        tool_call_id=tool_call_id, status=status, response=result
    )
    card = (
        tool_def.presenter(
            params=call["params"],
            result=result,
            tool_call_id=tool_call_id,
            status="recorded" if result.get("ok") else "failed",
        )
        if tool_def.presenter
        else None
    )
    reply = result.get("reply") or (
        "Action complete ho gaya." if result.get("ok") else "Action complete nahi hua."
    )
    convo.add_message(
        conversation_id=call["conversation_id"],
        sender=convo.SENDER_ASSISTANT,
        content=reply,
    )
    return {"ok": bool(result.get("ok")), "reply": reply, "card": card, "result": result}


@router.post("/actions/{tool_call_id}/reject")
def reject_tool_action(tool_call_id: str, user: CurrentUserDep) -> dict[str, Any]:
    call = tool_call_store.get_for_shop(
        tool_call_id=tool_call_id, shop_id=user.shop_id
    )
    if call is None:
        raise HTTPException(404, "Ye pending action nahi mila.")
    if call["status"] != "pending_approval":
        raise HTTPException(409, "Ye action pending approval mein nahi hai.")

    tool_call_store.set_status(tool_call_id=tool_call_id, status="rejected")
    reply = "Theek hai, action cancel kar diya."
    convo.add_message(
        conversation_id=call["conversation_id"],
        sender=convo.SENDER_ASSISTANT,
        content=reply,
    )
    return {
        "ok": True,
        "tool_call_id": tool_call_id,
        "status": "rejected",
        "reply": reply,
    }


@router.delete("/actions/{tool_call_id}")
def undo_tool_action(tool_call_id: str, user: CurrentUserDep) -> dict[str, Any]:
    call = tool_call_store.get_for_shop(
        tool_call_id=tool_call_id, shop_id=user.shop_id
    )
    if call is None:
        raise HTTPException(404, "Ye action nahi mila.")
    if call["status"] != "committed":
        raise HTTPException(409, "Sirf committed action undo ho sakta hai.")

    tool_def = get_registry().get(call["tool_name"])
    if tool_def is None or tool_def.undo is None:
        raise HTTPException(422, "Is action ke liye undo available nahi hai.")

    result = call.get("response") or {}
    undone = tool_def.undo(
        result=result,
        ctx={"shop_id": user.shop_id, "user_id": user.user_id},
    )

    if not undone:
        raise HTTPException(409, "Action undo nahi hua ya pehle hi undo ho chuka hai.")

    tool_call_store.set_status(tool_call_id=tool_call_id, status="undone")
    reply = "Action wapas ho gaya."
    convo.add_message(
        conversation_id=call["conversation_id"],
        sender=convo.SENDER_ASSISTANT,
        content=reply,
    )
    return {"ok": True, "tool_call_id": tool_call_id, "reply": reply}


# ── history ──────────────────────────────────────────────────────────────────

@router.get("/history")
def get_history(
    user: CurrentUserDep,
    limit: int = Query(convo.DEFAULT_HISTORY_LIMIT, ge=1, le=convo.MAX_HISTORY_LIMIT),
):
    conversation = convo.find_conversation(shop_id=user.shop_id)
    if conversation is None:
        return {"conversation_id": None, "messages": [], "action": None}

    action = None
    registry = get_registry()
    for call in tool_call_store.recent_for_conversation(
        conversation_id=conversation["id"]
    ):
        tool_def = registry.get(call["tool_name"])
        if tool_def and tool_def.presenter:
            action = tool_def.presenter(
                params=call.get("params") or {},
                result=call.get("response") or {},
                tool_call_id=call["id"],
                status=(
                    "proposed"
                    if call["status"] == "pending_approval"
                    else "recorded"
                ),
            )
            if action:
                break
    return {
        "conversation_id": conversation["id"],
        "messages": convo.list_messages(
            shop_id=user.shop_id, conversation_id=conversation["id"], limit=limit
        ),
        "action": action,
    }
