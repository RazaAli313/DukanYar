/**
 * Text-to-speech — VOICE-3.
 *
 * Sends the assistant's finished reply text to the backend, which synthesizes it
 * through the configured provider (edge-tts / Azure) and returns MP3 audio. The
 * reply is always shown as text regardless; audio is a bonus that degrades
 * gracefully.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SPEAK_TIMEOUT_MS = 20_000;

export async function synthesizeSpeech(text: string): Promise<Blob> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), SPEAK_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/voice/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(detail || `HTTP ${res.status}`);
    }

    const blob = await res.blob();
    if (blob.size === 0) throw new Error("Empty audio");
    return blob;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Speech synthesis timed out");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
