"""Voice router — VOICE-2 speech-to-text, VOICE-3 text-to-speech.

POST /voice/transcribe   multipart: file=<audio clip>   ->  { transcript, confidence }
POST /voice/speak        { text }                       ->  audio/mpeg bytes

Nothing here is persisted (no DB yet).
"""

import logging

from fastapi import APIRouter, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from app.config import settings
from app.services import stt, voice as tts

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB — a push-to-talk clip is far smaller
_MAX_TTS_CHARS = 8000


class TranscribeResponse(BaseModel):
    transcript: str
    confidence: float


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1)
    voice: str | None = None


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


@router.post(
    "/speak",
    responses={200: {"content": {"audio/mpeg": {}}}},
)
async def speak(body: SpeakRequest):
    provider = settings.tts_provider.lower()
    if provider not in ("edge", "azure"):
        raise HTTPException(502, f"TTS not configured: unknown provider '{provider}'")
    if provider == "azure" and not (
        settings.azure_speech_key and settings.azure_speech_region
    ):
        raise HTTPException(502, "TTS not configured: Azure key/region missing")

    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Empty text")
    if len(text) > _MAX_TTS_CHARS:
        raise HTTPException(413, "Text too long for synthesis")

    try:
        audio = await tts.synthesize(text, voice=body.voice)
    except tts.TTSError as exc:
        logger.warning("TTS failed: %s", exc)
        raise HTTPException(502, f"Speech synthesis failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — surface as 502, never a 500 stacktrace
        logger.exception("Unexpected TTS error")
        raise HTTPException(502, f"Speech synthesis error: {exc}") from exc

    return Response(content=audio, media_type="audio/mpeg")
