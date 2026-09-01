"""Voice router — VOICE-2 speech-to-text.

POST /voice/transcribe   multipart: file=<audio clip>   ->  { transcript, confidence }

The transcript is NOT persisted (no DB yet). The frontend submits it to the
shared POST /conversations/{id}/messages endpoint tagged `channel="voice"`.
"""

import logging

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.services import stt

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB — a push-to-talk clip is far smaller


class TranscribeResponse(BaseModel):
    transcript: str
    confidence: float


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile):
    provider = settings.stt_provider.lower()
    if provider == "speechmatics" and not settings.speechmatics_api_key:
        raise HTTPException(502, "STT not configured: SPEECHMATICS_API_KEY missing")
    if provider == "groq" and not settings.effective_groq_stt_key:
        raise HTTPException(502, "STT not configured: no Groq key available")

    audio = await file.read()
    if not audio:
        raise HTTPException(422, "Empty audio upload")
    if len(audio) > _MAX_BYTES:
        raise HTTPException(413, "Audio clip too large")

    try:
        result = await stt.transcribe(
            audio,
            file.content_type or "application/octet-stream",
            filename=file.filename or "clip.webm",
        )
    except stt.STTError as exc:
        logger.warning("STT failed: %s", exc)
        raise HTTPException(502, f"Transcription failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — surface as 502, never a 500 stacktrace
        logger.exception("Unexpected STT error")
        raise HTTPException(502, f"Transcription error: {exc}") from exc

    return TranscribeResponse(transcript=result.text, confidence=result.confidence)
