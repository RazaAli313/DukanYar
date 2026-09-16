"use client";

/**
 * VOICE-1 — push-to-talk capture state machine.
 *
 * Owns getUserMedia permission, MediaRecorder start/stop, elapsed time, a safety
 * cap on runaway holds, and the accidental-tap guards. The assembled audio Blob
 * is returned from `stop()` and never leaves the browser in this ticket.
 */

import { useCallback, useEffect, useRef, useState } from "react";

// ── Tunables ─────────────────────────────────────────────────────────────────
const MIN_RECORD_MS = 450; // shorter than this = accidental tap, discard
const MIN_BLOB_BYTES = 2048; // near-empty clip, discard
const MAX_RECORD_MS = 60_000; // safety cap — auto-stop a forgotten hold
const ELAPSED_TICK_MS = 100;

export type PushToTalkStatus =
  | "idle"
  | "requesting"
  | "recording"
  | "denied"
  | "error";

export interface CapturedAudio {
  blob: Blob;
  durationMs: number;
  mimeType: string;
}

interface Options {
  /** Called when the safety cap fires and produces a usable clip. */
  onAutoSubmit?: (clip: CapturedAudio) => void;
}

export interface UsePushToTalk {
  status: PushToTalkStatus;
  elapsedMs: number;
  /** Human-readable Roman-Urdu message when status is "denied" or "error". */
  error: string | null;
  /** Begin capture. No-op unless idle. */
  start: () => void;
  /** End capture. Resolves the clip, or null when it fails a guard / wasn't recording. */
  stop: () => Promise<CapturedAudio | null>;
  /** Abort capture and discard (system gesture / unmount). */
  cancel: () => void;
}

function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported) {
    for (const type of candidates) {
      if (MediaRecorder.isTypeSupported(type)) return type;
    }
  }
  return "";
}

export function usePushToTalk(options: Options = {}): UsePushToTalk {
  const { onAutoSubmit } = options;

  const [status, setStatus] = useState<PushToTalkStatus>("idle");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef(0);
  // Set the instant the user releases — lets us abort a capture whose
  // getUserMedia promise is still pending.
  const releasedRef = useRef(false);
  const maxTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const onAutoSubmitRef = useRef(onAutoSubmit);
  useEffect(() => {
    onAutoSubmitRef.current = onAutoSubmit;
  }, [onAutoSubmit]);

  const teardownStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const clearTimers = useCallback(() => {
    if (maxTimerRef.current) clearTimeout(maxTimerRef.current);
    if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    maxTimerRef.current = null;
    elapsedTimerRef.current = null;
  }, []);

  const finalize = useCallback((): CapturedAudio | null => {
    const mimeType = recorderRef.current?.mimeType || "audio/webm";
    const durationMs = performance.now() - startedAtRef.current;
    const blob = new Blob(chunksRef.current, { type: mimeType });
    chunksRef.current = [];
    recorderRef.current = null;

    if (durationMs < MIN_RECORD_MS || blob.size < MIN_BLOB_BYTES) return null;
    return { blob, durationMs, mimeType };
  }, []);

  /** Shared stop routine. `auto` marks the safety-cap path. */
  const doStop = useCallback(
    (auto: boolean): Promise<CapturedAudio | null> => {
      releasedRef.current = true;
      clearTimers();
      setElapsedMs(0);

      const rec = recorderRef.current;
      if (!rec || rec.state === "inactive") {
        teardownStream();
        setStatus((s) =>
          s === "recording" || s === "requesting" ? "idle" : s,
        );
        return Promise.resolve(null);
      }

      return new Promise<CapturedAudio | null>((resolve) => {
        rec.onstop = () => {
          teardownStream();
          const result = finalize();
          setStatus("idle");
          if (auto && result) onAutoSubmitRef.current?.(result);
          resolve(result);
        };
        try {
          rec.stop();
        } catch {
          teardownStream();
          setStatus("idle");
          resolve(null);
        }
      });
    },
    [clearTimers, teardownStream, finalize],
  );

  const stop = useCallback(() => doStop(false), [doStop]);

  const cancel = useCallback(() => {
    releasedRef.current = true;
    clearTimers();
    const rec = recorderRef.current;
    if (rec && rec.state !== "inactive") {
      rec.onstop = null;
      try {
        rec.stop();
      } catch {
        /* already stopped */
      }
    }
    recorderRef.current = null;
    chunksRef.current = [];
    teardownStream();
    setStatus("idle");
    setElapsedMs(0);
  }, [clearTimers, teardownStream]);

  const start = useCallback(() => {
    // Allow a retry from "denied"/"error" (user may have just fixed permissions).
    if (status === "requesting" || status === "recording") return;

    if (
      typeof navigator === "undefined" ||
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setStatus("error");
      setError("Is browser mein voice support nahi hai. Text likh kar bhejein.");
      return;
    }

    releasedRef.current = false;
    setError(null);
    setStatus("requesting");

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        // User let go (or cancelled) while the prompt was open — drop it.
        if (releasedRef.current) {
          stream.getTracks().forEach((t) => t.stop());
          setStatus("idle");
          return;
        }

        streamRef.current = stream;
        chunksRef.current = [];

        const mimeType = pickMimeType();
        const rec = mimeType
          ? new MediaRecorder(stream, { mimeType })
          : new MediaRecorder(stream);
        recorderRef.current = rec;

        rec.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };

        startedAtRef.current = performance.now();
        rec.start();
        setStatus("recording");
        setElapsedMs(0);

        elapsedTimerRef.current = setInterval(() => {
          setElapsedMs(performance.now() - startedAtRef.current);
        }, ELAPSED_TICK_MS);

        maxTimerRef.current = setTimeout(() => {
          void doStop(true);
        }, MAX_RECORD_MS);
      })
      .catch((err: unknown) => {
        teardownStream();
        const name = err instanceof DOMException ? err.name : "";
        if (name === "NotAllowedError" || name === "PermissionDeniedError") {
          setStatus("denied");
          setError(
            "Voice istemal karne ke liye microphone ki ijazat chahiye. Browser ke site settings mein microphone allow kar ke dobara koshish karein.",
          );
        } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
          setStatus("error");
          setError("Koi microphone nahi mila.");
        } else {
          setStatus("error");
          setError("Microphone shuru nahi ho saka. Dobara koshish karein.");
        }
      });
  }, [status, doStop, teardownStream]);

  // Unmount cleanup — never leave the mic open.
  useEffect(() => {
    return () => {
      releasedRef.current = true;
      if (maxTimerRef.current) clearTimeout(maxTimerRef.current);
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
      const rec = recorderRef.current;
      if (rec && rec.state !== "inactive") {
        rec.onstop = null;
        try {
          rec.stop();
        } catch {
          /* noop */
        }
      }
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return { status, elapsedMs, error, start, stop, cancel };
}
