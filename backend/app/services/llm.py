"""LLM service — thin wrapper around the OpenAI-compatible chat completions API.

Gemini Flash now (via its OpenAI-compatible endpoint), Qwen later.
Swapping providers is a config change only — no code change here.
"""

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings

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

    *turns* is a full OpenAI-style message list (system + history + user).
    Yields incremental text deltas (not accumulated).
    """
    client = _get_client()
    stream = await client.chat.completions.create(
        model=settings.llm_model,
        messages=turns,
        stream=True,
        # Minimize Gemini thinking for faster time-to-first-token.
        # "none" is rejected by Gemini 3 models; "minimal" is the lowest allowed.
        reasoning_effort="minimal",
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
