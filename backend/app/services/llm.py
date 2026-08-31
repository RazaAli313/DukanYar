"""LLM service — thin wrapper around the OpenAI-compatible chat completions API.

Gemini Flash now (via its OpenAI-compatible endpoint), Qwen later.
Swapping providers is a config change only — no code change here.
"""

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings
from app.prompts import SYSTEM_PROMPT

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


async def stream_reply(turns: list[dict[str, str]]) -> AsyncGenerator[str, None]:
    """Stream an assistant reply token-by-token.

    *turns* is the conversation so far (prior turns + the new user message)
    as OpenAI-style {"role", "content"} dicts. The TEXT-4 system persona
    (app.prompts.SYSTEM_PROMPT) is prepended here as the first message.
    Yields incremental text deltas (not accumulated).
    """
    # TEXT-4: the system prompt always leads the message list.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *turns]
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
