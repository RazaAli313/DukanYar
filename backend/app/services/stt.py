"""Speech-to-text service — VOICE-2.

One `transcribe()` interface with two providers so the choice is a config switch
(`STT_PROVIDER`):

- **speechmatics** (default) — batch REST API (create job → poll → fetch transcript).
  Strong on accented / noisy speech and Urdu-English code-switching.
- **groq** — `whisper-large-v3` on the same key as the LLM. Fallback / A-B option.

Both output **Urdu script** (there is no Roman-Urdu STT mode). The transcript is
returned to the caller, not persisted (no DB yet).
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_POLL_INTERVAL_S = 1.0
_POLL_TIMEOUT_S = 25.0
_HTTP_TIMEOUT_S = 30.0


class STTError(Exception):
    """Transcription failed — provider error, timeout, or misconfiguration."""


@dataclass
class Transcript:
    text: str
    confidence: float  # 0.0–1.0; mean word confidence (0.0 when no words)


async def transcribe(
    audio: bytes,
    content_type: str,
    filename: str = "clip.webm",
) -> Transcript:
    """Transcribe an audio clip using the configured provider."""
    provider = settings.stt_provider.lower()
    if provider == "groq":
        return await _transcribe_groq(audio, content_type, filename)
    return await _transcribe_speechmatics(audio, content_type, filename)


# ── Speechmatics batch ───────────────────────────────────────────────────────

async def _transcribe_speechmatics(
    audio: bytes, content_type: str, filename: str
) -> Transcript:
    if not settings.speechmatics_api_key:
        raise STTError("SPEECHMATICS_API_KEY is not set")

    vocab = [{"content": w} for w in settings.stt_extra_vocab_list]
    transcription_config: dict = {
        "language": settings.stt_language,
        "operating_point": settings.speechmatics_operating_point,
    }
    if vocab:
        transcription_config["additional_vocab"] = vocab

    config = {"type": "transcription", "transcription_config": transcription_config}
    headers = {"Authorization": f"Bearer {settings.speechmatics_api_key}"}
    base = settings.speechmatics_url.rstrip("/")

    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
        # 1 — create the job
        resp = await client.post(
            f"{base}/jobs",
            headers=headers,
            files={
                "data_file": (
                    filename,
                    audio,
                    content_type or "application/octet-stream",
                )
            },
            data={"config": json.dumps(config)},
        )
        if resp.status_code >= 400:
            raise STTError(
                f"Speechmatics job create failed: {resp.status_code} {resp.text[:300]}"
            )
        job_id = resp.json().get("id")
        if not job_id:
            raise STTError("Speechmatics did not return a job id")

        # 2 — poll until done
        deadline = time.monotonic() + _POLL_TIMEOUT_S
        while True:
            await asyncio.sleep(_POLL_INTERVAL_S)
            resp = await client.get(f"{base}/jobs/{job_id}", headers=headers)
            resp.raise_for_status()
            status = resp.json().get("job", {}).get("status")
            if status == "done":
                break
            if status in ("rejected", "deleted", "expired"):
                raise STTError(f"Speechmatics job {status}")
            if time.monotonic() > deadline:
                raise STTError("Speechmatics transcription timed out")

        # 3 — fetch the transcript
        resp = await client.get(
            f"{base}/jobs/{job_id}/transcript",
            headers=headers,
            params={"format": "json-v2"},
        )
        resp.raise_for_status()
        return _parse_speechmatics(resp.json())


def _parse_speechmatics(payload: dict) -> Transcript:
    parts: list[str] = []
    confidences: list[float] = []

    for result in payload.get("results", []):
        alt = (result.get("alternatives") or [{}])[0]
        content = alt.get("content", "")
        if not content:
            continue
        if result.get("type") == "punctuation" and parts:
            parts[-1] = parts[-1] + content
        else:
            parts.append(content)
            conf = alt.get("confidence")
            if conf is not None:
                confidences.append(float(conf))

    text = " ".join(parts).strip()
    confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return Transcript(text=text, confidence=confidence)


# ── Groq whisper-large-v3 ────────────────────────────────────────────────────

async def _transcribe_groq(
    audio: bytes, content_type: str, filename: str
) -> Transcript:
    key = settings.effective_groq_stt_key
    if not key:
        raise STTError("No Groq STT key (GROQ_STT_API_KEY / LLM_API_KEY)")

    base = settings.groq_stt_base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_S) as client:
        resp = await client.post(
            f"{base}/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files={
                "file": (filename, audio, content_type or "application/octet-stream")
            },
            data={
                "model": settings.groq_stt_model,
                "language": settings.stt_language,
                "response_format": "verbose_json",
            },
        )
    if resp.status_code >= 400:
        raise STTError(f"Groq transcription failed: {resp.status_code} {resp.text[:300]}")
    return _parse_groq(resp.json())


def _parse_groq(payload: dict) -> Transcript:
    text = (payload.get("text") or "").strip()

    # whisper has no per-word confidence — approximate from segment log-probs.
    probs: list[float] = []
    for seg in payload.get("segments") or []:
        logprob = seg.get("avg_logprob")
        if logprob is not None:
            probs.append(math.exp(logprob))

    if probs:
        confidence = max(0.0, min(1.0, sum(probs) / len(probs)))
    else:
        confidence = 0.9 if text else 0.0

    return Transcript(text=text, confidence=confidence)
