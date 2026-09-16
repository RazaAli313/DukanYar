"use client";

/**
 * VOICE-3 — small control under a spoken assistant reply.
 * Play / replay the reply audio, stop it, or retry after a failure.
 * The reply text is always visible regardless of this button's state.
 */

import type { SpeechStatus } from "@/lib/voice/useReplySpeech";

interface Props {
  status: SpeechStatus;
  onPlay: () => void;
  onStop: () => void;
}

export function ReplaySpeechButton({ status, onPlay, onStop }: Props) {
  const base =
    "mt-0.5 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors";

  if (status === "loading") {
    return (
      <span
        className={`${base} border-slate-700 bg-slate-800 text-slate-400`}
      >
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-600 border-t-slate-300" />
        Awaaz tayyar…
      </span>
    );
  }

  if (status === "playing") {
    return (
      <button
        onClick={onStop}
        className={`${base} border-emerald-700 bg-emerald-950/50 text-emerald-300 hover:bg-emerald-900/50`}
      >
        <span aria-hidden>⏹</span> Rokiye
      </button>
    );
  }

  const label =
    status === "error"
      ? "Awaaz nahi chali — dobara"
      : status === "blocked"
        ? "Suniye"
        : "Dobara suniye";

  return (
    <button
      onClick={onPlay}
      className={`${base} border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700`}
    >
      <span aria-hidden>🔊</span> {label}
    </button>
  );
}
