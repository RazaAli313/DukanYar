"""LLM service — thin wrapper around the OpenAI-compatible chat completions API.

Gemini Flash now (via its OpenAI-compatible endpoint), Qwen later.
Swapping providers is a config change only — no code change here.
"""

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings
from app.prompts import MODE_HINTS, SYSTEM_PROMPT, VOICE_LANGUAGE_HINT

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


async def stream_reply(
    turns: list[dict[str, str]],
    channel: str = "text",
    mode: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream an assistant reply token-by-token.

    *turns* is the conversation so far (prior turns + the new user message)
    as OpenAI-style {"role", "content"} dicts. The TEXT-4 system persona
    (app.prompts.SYSTEM_PROMPT) is prepended here as the first message.
    *channel* is where the latest user message came from ("text" | "voice");
    voice turns get an extra system nudge to answer in Roman-Urdu (VOICE-2).
    Yields incremental text deltas (not accumulated).
    """
    # TEXT-4: the system prompt always leads the message list.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if mode and mode in MODE_HINTS:
        messages.append({"role": "system", "content": MODE_HINTS[mode]})
    if channel == "voice":
        messages.append({"role": "system", "content": VOICE_LANGUAGE_HINT})
    messages.extend(turns)
    client = _get_client()
    # reasoning_effort is provider-specific (Gemini 3: "minimal", Groq:
    # "none") — configured via .env. An empty value omits the parameter
    # entirely so providers that don't support it stay happy.
    extra_kwargs: dict[str, str] = {}
    if settings.llm_reasoning_effort:
        extra_kwargs["reasoning_effort"] = settings.llm_reasoning_effort
    stream = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        stream=True,
        **extra_kwargs,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ── structured extraction for mode-scoped record flows (TEXT-5) ──────────────

import json as _json  # noqa: E402

_SALE_EXTRACT_SYSTEM = """\
You extract a sale from the shopkeeper's message. The shopkeeper picked "Sale"
mode, so you do NOT classify intent — assume they are describing a sale.

Reply with ONLY a JSON object, no prose:
{
  "action": "propose" | "clarify",
  "items": [{"name": "<item as said>", "quantity": <int>}],
  "stated_total": <number or null>,
  "payment": "cash" | "udhaar",
  "khata_number": <int or null>,
  "reply": "<one short Roman-Urdu sentence to the shopkeeper>"
}

Rules:
- "propose" when you have at least one item with a quantity AND a stated total.
  The reply should read the sale back and ask for confirmation, e.g.
  "Do coke, aik chips — total 480 rupay. Theek hai?"
- "clarify" when an item, a quantity, or the total is missing. The reply asks
  ONE short question, e.g. "Kitne coke?" or "Total kitna hua?"
- payment is "udhaar" only if a khata number or "udhaar"/"khaate" is mentioned;
  otherwise "cash".
- The stated total is authoritative — do not compute it from prices.
- Keep item names close to what was said ("coke", "chips", "doodh").
"""


async def extract_sale(turns: list[dict[str, str]]) -> dict:
    """One-shot structured parse of a sale from the recent turns."""
    client = _get_client()
    messages = [{"role": "system", "content": _SALE_EXTRACT_SYSTEM}, *turns]
    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        data = _json.loads(raw)
    except _json.JSONDecodeError:
        return {"action": "clarify", "reply": "Muaaf kijiye, samajh nahi aaya. Dobara boliye?"}
    data.setdefault("action", "clarify")
    data.setdefault("items", [])
    data.setdefault("reply", "Theek hai?")
    return data


_ROMAN_SYSTEM = (
    "Transliterate the user's message into Roman-Urdu (Latin letters) exactly as "
    "a Pakistani shopkeeper would type it. Keep English product words as-is "
    "(coke, chips, lays, doodh). Do NOT translate, answer, or add anything — "
    "output only the transliterated line."
)


async def to_roman_urdu(text: str) -> str:
    """Best-effort Urdu-script -> Roman-Urdu. Returns the original on any failure."""
    if not text or not any("؀" <= ch <= "ۿ" for ch in text):
        return text  # already Latin
    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": _ROMAN_SYSTEM},
                {"role": "user", "content": text},
            ],
            temperature=0,
        )
        out = (resp.choices[0].message.content or "").strip()
        return out or text
    except Exception:
        return text


_EXPENSE_EXTRACT_SYSTEM = """\
The shopkeeper picked "Kharcha" mode — they are recording money the shop spent.
Reply with ONLY a JSON object:
{
  "action": "propose" | "clarify",
  "amount": <number or null>,
  "note": "<short description of the expense, e.g. 'bijli ka bill'>",
  "reply": "<one short Roman-Urdu sentence>"
}
- "propose" when you have an amount AND some idea what it was for. The reply
  reads it back: "Bijli ka bill 3000 rupay — likh doon?"
- "clarify" when the amount or the purpose is missing: "Kitne ka bill tha?"
- Never invent an amount.
"""

_UDHAAR_EXTRACT_SYSTEM = """The shopkeeper picked "Udhaar" mode. They are either RECORDING credit given /
a repayment received, or ASKING about a customer's khata (balance, name).
Use the WHOLE conversation so far. Reply with ONLY this JSON object:
{
  "action": "propose" | "clarify" | "lookup",
  "kind": "udhaar" | "payment",
  "khata_number": <int, or null>,
  "customer_name": "<the person's name, or null>",
  "cnic": "<CNIC digits if stated ANYWHERE in the conversation, else null>",
  "amount": <number, or null>,
  "reply": "<one short Roman-Urdu sentence>"
}

RULES
- "lookup" = the shopkeeper is ASKING, not recording. Questions like "khata 1 ka
  record batao", "Akram ka kitna udhaar hai", "khata number 2 ka naam kya hai",
  "us ka balance batao". Fill khata_number / customer_name from what they said and
  set reply to a brief acknowledgement ("Dekh raha hoon..."). Do NOT ask for a
  CNIC or amount for a lookup.
- "propose" = they are RECORDING and you have an amount AND (a khata number OR a
  name). For a new name with no khata number, "propose" needs a CNIC present.
  reply asks for a yes: "Akram ko 400 udhaar, likh doon?"
- "clarify" = recording, but something needed is missing. New customer name known
  but no CNIC anywhere -> ask: "Akram ki CNIC batayein (13 digits)."
- kind = "payment" if they say jama / wapas / diye / repaid; else "udhaar".
- ALWAYS scan every earlier turn for a CNIC (dashes optional, e.g.
  42101-1234567-9) and carry the amount/name from earlier turns.
- Never invent an amount, name, or CNIC. For recording, the reply must ASK.

EXAMPLES
"khata number 1 ka record batao"
-> {"action":"lookup","khata_number":1,"customer_name":null,"cnic":null,
    "amount":null,"kind":"udhaar","reply":"Khata 1 dekh raha hoon."}
"Akram ne 400 udhaar liya" / assistant asks CNIC / "cnic 42101-1234567-9"
-> {"action":"propose","kind":"udhaar","khata_number":null,
    "customer_name":"Akram","cnic":"4210112345679","amount":400,
    "reply":"Akram ko 400 udhaar, naya khata banega, likh doon?"}
"""


async def _extract(system: str, turns: list[dict[str, str]]) -> dict:
    client = _get_client()
    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": system}, *turns],
        response_format={"type": "json_object"},
        temperature=0,
    )
    try:
        data = _json.loads(resp.choices[0].message.content or "{}")
    except _json.JSONDecodeError:
        return {"action": "clarify", "reply": "Samajh nahi aaya, dobara boliye?"}
    data.setdefault("action", "clarify")
    data.setdefault("reply", "Theek hai?")
    return data


async def extract_expense(turns: list[dict[str, str]]) -> dict:
    return await _extract(_EXPENSE_EXTRACT_SYSTEM, turns)


async def extract_udhaar(turns: list[dict[str, str]]) -> dict:
    return await _extract(_UDHAAR_EXTRACT_SYSTEM, turns)
