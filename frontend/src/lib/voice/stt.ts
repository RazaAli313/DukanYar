/**
 * Speech-to-text — VOICE-1 STUB.
 *
 * VOICE-2 replaces the body of `transcribeAudio()` with a real Speechmatics call
 * (Groq whisper-large-v3 is the documented fallback). Capture (VOICE-1) and the
 * UI do not change when that swap happens — only this function.
 *
 * The stub returns a realistic Urdu sentence (not a bracketed placeholder) so the
 * end-to-end speak -> reply loop looks real in the demo.
 */

import type { CapturedAudio } from "./usePushToTalk";

const SAMPLE_TRANSCRIPTS = [
  "دو کوک اور ایک پیکٹ بسکٹ چاہیے",
  "آج کتنی سیل ہوئی",
  "چینی کا ایک کلو کتنے کا ہے",
  "علی بھائی کا کتنا ادھار باقی ہے",
];

/** Simulated STT latency (ms). */
const STUB_DELAY_MS = 600;

export async function transcribeAudio(audio: CapturedAudio): Promise<string> {
  // Stub: ignores the audio, just proves the wiring. VOICE-2 sends `audio.blob`
  // to Speechmatics here and returns the real transcript.
  void audio;
  await new Promise((resolve) => setTimeout(resolve, STUB_DELAY_MS));
  const idx = Math.floor(Math.random() * SAMPLE_TRANSCRIPTS.length);
  return SAMPLE_TRANSCRIPTS[idx];
}
