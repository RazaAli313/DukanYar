/**
 * Speech-to-text — VOICE-2.
 *
 * Uploads the captured clip to the backend, which proxies to Speechmatics (or
 * Groq whisper-large-v3, per STT_PROVIDER) and returns the transcript plus a
 * mean word-confidence. The audio never goes to a third party from the browser.
 *
 * Output is Urdu script (there is no Roman-Urdu STT mode) — the chat UI already
 * RTL-renders it and the LLM persona reads it fine.
 */

import type { CapturedAudio } from "./usePushToTalk";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Below this mean word confidence, prompt the shopkeeper to try again. */
export const STT_MIN_CONFIDENCE = 0.5;

/** Batch transcription can take a few seconds — cap the wait. */
const TRANSCRIBE_TIMEOUT_MS = 40_000;

export interface Transcription {
  transcript: string;
  confidence: number;
}

export async function transcribeAudio(
  audio: CapturedAudio,
): Promise<Transcription> {
  const ext = audio.mimeType.includes("mp4") ? "mp4" : "webm";
  const form = new FormData();
  form.append("file", audio.blob, `clip.${ext}`);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TRANSCRIBE_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/voice/transcribe`, {
      method: "POST",
      body: form,
      signal: controller.signal,
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(detail || `HTTP ${res.status}`);
    }

    const data = (await res.json()) as Partial<Transcription>;
    return {
      transcript: data.transcript ?? "",
      confidence: typeof data.confidence === "number" ? data.confidence : 0,
    };
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Transcription timed out");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
