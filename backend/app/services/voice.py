"""Text-to-speech service — VOICE-3.

One `synthesize()` interface with the provider chosen by config (`TTS_PROVIDER`),
so the Urdu voice source can be swapped without touching capture (VOICE-1) or STT
(VOICE-2):

- **edge** (default) — `edge-tts`, free, no key. Real `ur-PK` neural voices via
  Edge's online endpoint (unofficial — the adapter is why we can swap out).
- **azure** — the same `ur-PK` voices via Azure Speech's REST endpoint (needs a
  key). Fallback when edge-tts quality / reliability is not enough.
- **elevenlabs** — ElevenLabs REST endpoint (needs a key + voice ID). Uses
  `ELEVENLABS_VOICE_ID`, not `TTS_VOICE`.
- **upliftai** — UpliftAI Orator voices, Urdu-first (needs a key). Uses
  `UPLIFTAI_VOICE_ID`. Expects Urdu-script input, so pair with
  `TTS_TRANSLITERATE=true` for Roman-Urdu replies.

Voice-turn replies are Roman-Urdu (VOICE-2). If `TTS_TRANSLITERATE` is on, a Groq
call converts them to Urdu script first for cleaner pronunciation; that step is
best-effort and falls back to the original text on any error.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT_S = 20.0
_AZURE_OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"


class TTSError(Exception):
    """Speech synthesis failed — provider error or misconfiguration."""


async def synthesize(text: str, *, voice: str | None = None) -> bytes:
    """Return MP3 audio bytes for *text* using the configured provider."""
    clean = (text or "").strip()
    if not clean:
        raise TTSError("Empty text")

    if settings.tts_transliterate:
        clean = await _to_urdu_script(clean)

    voice = voice or settings.tts_voice
    provider = settings.tts_provider.lower()
    if provider == "edge":
        return await _synthesize_edge(clean, voice)
    if provider == "azure":
        return await _synthesize_azure(clean, voice)
    if provider == "elevenlabs":
        return await _synthesize_elevenlabs(clean)
    if provider == "upliftai":
        return await _synthesize_upliftai(clean)
    raise TTSError(f"Unknown TTS provider: {provider}")


# ── Roman-Urdu → Urdu script (optional) ──────────────────────────────────────

_TRANSLITERATE_SYSTEM = (
    "Convert the following Roman-Urdu text into natural Urdu (Arabic) script. "
    "Keep English words and product names in Latin letters. "
    "Output only the converted text, nothing else."
)


async def _to_urdu_script(text: str) -> str:
    """Best-effort transliteration via the LLM. Returns the original on failure."""
    try:
        from app.services import llm

        client = llm._get_client()  # noqa: SLF001 — reuse the configured client
        extra: dict[str, str] = {}
        if settings.llm_reasoning_effort:
            extra["reasoning_effort"] = settings.llm_reasoning_effort
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": _TRANSLITERATE_SYSTEM},
                {"role": "user", "content": text},
            ],
            stream=False,
            **extra,
        )
        out = (resp.choices[0].message.content or "").strip()
        return out or text
    except Exception as exc:  # noqa: BLE001 — transliteration is optional
        logger.warning("Transliteration failed, using original text: %s", exc)
        return text


# ── edge-tts ────────────────────────────────────────────────────────────────

async def _synthesize_edge(text: str, voice: str) -> bytes:
    try:
        import edge_tts
    except ImportError as exc:  # pragma: no cover
        raise TTSError("edge-tts is not installed (uv add edge-tts)") from exc

    try:
        communicate = edge_tts.Communicate(text, voice, rate=settings.tts_rate)
        chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.extend(chunk["data"])
    except Exception as exc:  # noqa: BLE001
        raise TTSError(f"edge-tts failed: {exc}") from exc

    if not chunks:
        raise TTSError("edge-tts returned no audio")
    return bytes(chunks)


# ── Azure Speech REST ───────────────────────────────────────────────────────

def _ssml(text: str, voice: str) -> str:
    safe = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    # Azure ignores <voice> and falls back to the region default (Hindi in
    # centralindia) unless the synthesis namespace is declared.
    parts = voice.split("-")
    lang = "-".join(parts[:2]) if len(parts) >= 2 else "ur-PK"
    return (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{lang}">'
        f'<voice name="{voice}">{safe}</voice>'
        "</speak>"
    )


async def _synthesize_azure(text: str, voice: str) -> bytes:
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise TTSError("AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set")

    url = (
        f"https://{settings.azure_speech_region}.tts.speech.microsoft.com"
        "/cognitiveservices/v1"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": _AZURE_OUTPUT_FORMAT,
        "User-Agent": "dukanyar",
    }
    logger.info("Azure TTS: voice=%s region=%s chars=%d", voice, settings.azure_speech_region, len(text))
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
        resp = await client.post(url, headers=headers, content=_ssml(text, voice))
    if resp.status_code >= 400:
        raise TTSError(f"Azure TTS failed: {resp.status_code} {resp.text[:200]}")
    if not resp.content:
        raise TTSError("Azure TTS returned no audio")
    return resp.content


# ── ElevenLabs REST ───────────────────────────────────────────────────────────────

async def _synthesize_elevenlabs(text: str) -> bytes:
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise TTSError("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID not set")

    url = (
        "https://api.elevenlabs.io/v1/text-to-speech/"
        f"{settings.elevenlabs_voice_id}?output_format=mp3_44100_128"
    )
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
    }
    payload = {"text": text, "model_id": settings.elevenlabs_model_id}
    logger.info(
        "ElevenLabs TTS: voice=%s model=%s chars=%d",
        settings.elevenlabs_voice_id, settings.elevenlabs_model_id, len(text),
    )
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise TTSError(
            f"ElevenLabs TTS failed: {resp.status_code} {resp.text[:200]}"
        )
    if not resp.content:
        raise TTSError("ElevenLabs TTS returned no audio")
    return resp.content


# ── UpliftAI REST ─────────────────────────────────────────────────────────────────

async def _synthesize_upliftai(text: str) -> bytes:
    if not settings.upliftai_api_key:
        raise TTSError("UPLIFTAI_API_KEY not set")

    url = "https://api.upliftai.org/v1/synthesis/text-to-speech"
    headers = {
        "Authorization": f"Bearer {settings.upliftai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "voiceId": settings.upliftai_voice_id,
        "text": text,
        "outputFormat": settings.upliftai_output_format,
    }
    logger.info(
        "UpliftAI TTS: voice=%s format=%s chars=%d",
        settings.upliftai_voice_id, settings.upliftai_output_format, len(text),
    )
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
        resp = await client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise TTSError(
            f"UpliftAI TTS failed: {resp.status_code} {resp.text[:200]}"
        )
    if not resp.content:
        raise TTSError("UpliftAI TTS returned no audio")
    return resp.content
