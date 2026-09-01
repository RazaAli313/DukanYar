"use client";

/**
 * Voice bar mounted above the text input.
 *
 * Release flow (VOICE-1 capture -> VOICE-2 transcription):
 *   guard-passed clip -> POST /voice/transcribe -> confidence gate ->
 *   onSend(transcript, "voice") — the same path typed messages take, which is
 *   what makes voice and text interchangeable.
 * The audio blob is uploaded only to our own backend, which proxies to the STT
 * provider.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  usePushToTalk,
  type CapturedAudio,
} from "@/lib/voice/usePushToTalk";
import { transcribeAudio, STT_MIN_CONFIDENCE } from "@/lib/voice/stt";
import { PushToTalkButton } from "./PushToTalkButton";
import { RecordingIndicator } from "./RecordingIndicator";

interface Props {
  onSend: (text: string, channel?: "text" | "voice") => void | Promise<void>;
  /** True while an assistant reply is streaming — mirrors the send button. */
  disabled: boolean;
  /** Fired when the shopkeeper starts a new recording (stop any playing reply). */
  onCaptureStart?: () => void;
  /** Transient prompt from the parent, e.g. after a re-speak (VOICE-4). */
  notice?: string | null;
}

const HINT_MS = 2500;

export function VoiceBar({ onSend, disabled, onCaptureStart, notice }: Props) {
  const [hint, setHint] = useState<string | null>(null);
  const [transcribing, setTranscribing] = useState(false);
  const hintTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const disabledRef = useRef(disabled);
  useEffect(() => {
    disabledRef.current = disabled;
  }, [disabled]);

  const showHint = useCallback((msg: string) => {
    setHint(msg);
    if (hintTimerRef.current) clearTimeout(hintTimerRef.current);
    hintTimerRef.current = setTimeout(() => setHint(null), HINT_MS);
  }, []);

  const submitClip = useCallback(
    async (clip: CapturedAudio) => {
      // Re-check: a reply may have started streaming during the hold.
      if (disabledRef.current) return;
      setTranscribing(true);
      try {
        const { transcript, confidence } = await transcribeAudio(clip);
        if (!transcript.trim() || confidence < STT_MIN_CONFIDENCE) {
          showHint("Awaaz saaf samajh nahi aayi — dobara boliye");
          return;
        }
        await onSend(transcript, "voice");
      } catch {
        showHint("Transcription nahi ho saki — dobara koshish karein");
      } finally {
        setTranscribing(false);
      }
    },
    [onSend, showHint],
  );

  const { status, elapsedMs, error, start, stop, cancel } = usePushToTalk({
    onAutoSubmit: submitClip,
  });

  const handlePressStart = useCallback(() => {
    onCaptureStart?.();
    start();
  }, [onCaptureStart, start]);

  const handlePressEnd = useCallback(async () => {
    const clip = await stop();
    if (!clip) {
      // Only nag when the user actually meant to record (was holding).
      if (status === "recording") {
        showHint("Bohat mukhtasar — button ko dabaye rakhein aur bolein");
      }
      return;
    }
    await submitClip(clip);
  }, [stop, status, showHint, submitClip]);

  const showIndicator = status === "recording";
  const showDenied = status === "denied";
  const showError = status === "error";

  return (
    <div className="shrink-0 border-t border-slate-800/40 bg-[var(--surface)] px-4 py-3">
      <div className="mx-auto flex max-w-[420px] flex-col items-center gap-2">
        <PushToTalkButton
          status={status}
          disabled={disabled || transcribing}
          onPressStart={handlePressStart}
          onPressEnd={handlePressEnd}
          onPressCancel={cancel}
        />

        <div className="min-h-[1.25rem] text-center">
          {showIndicator ? (
            <RecordingIndicator elapsedMs={elapsedMs} />
          ) : transcribing ? (
            <span className="text-[0.8125rem] text-slate-400">
              Likh raha hoon…
            </span>
          ) : showDenied || showError ? (
            <span className="text-[0.8125rem] text-rose-300">{error}</span>
          ) : hint ? (
            <span className="text-[0.8125rem] text-amber-300">{hint}</span>
          ) : notice ? (
            <span className="text-[0.8125rem] text-emerald-300">{notice}</span>
          ) : (
            <span className="text-[0.8125rem] text-slate-500">
              Bolne ke liye mic dabaye rakhein
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
