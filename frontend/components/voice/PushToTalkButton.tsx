"use client";

/**
 * Big press-and-hold mic button (VOICE-1).
 *
 * Pointer-driven with pointer capture, so releasing outside the button still
 * counts as release-to-send. Long-press context menu / text selection are
 * suppressed for mobile.
 */

import type { PointerEvent } from "react";
import type { PushToTalkStatus } from "@/lib/voice/usePushToTalk";

interface Props {
  status: PushToTalkStatus;
  disabled: boolean;
  onPressStart: () => void;
  onPressEnd: () => void;
  onPressCancel: () => void;
}

function MicIcon({ muted }: { muted?: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className="relative z-10 h-8 w-8 fill-current"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
      <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      {muted && (
        <path
          d="M3 3l18 18"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

export function PushToTalkButton({
  status,
  disabled,
  onPressStart,
  onPressEnd,
  onPressCancel,
}: Props) {
  const recording = status === "recording";
  const requesting = status === "requesting";
  const blocked = status === "denied" || status === "error";
  const isDisabled = disabled || requesting;

  function handlePointerDown(e: PointerEvent<HTMLButtonElement>) {
    if (isDisabled) return;
    // Keep receiving pointerup even if the finger slides off the button.
    e.currentTarget.setPointerCapture?.(e.pointerId);
    onPressStart();
  }

  function handlePointerUp() {
    if (isDisabled) return;
    onPressEnd();
  }

  const base =
    "relative flex h-16 w-16 items-center justify-center rounded-full shadow-lg transition active:scale-95 disabled:cursor-not-allowed";
  const tone = recording
    ? "bg-rose-500 text-white shadow-rose-500/30"
    : blocked
      ? "bg-slate-700 text-slate-400 shadow-black/20"
      : "bg-emerald-500 text-slate-950 shadow-emerald-500/30 hover:bg-emerald-400";
  const dimmed = isDisabled && !recording ? "opacity-40" : "";

  return (
    <button
      type="button"
      aria-label="Bol kar bhejein — dabaye rakhein"
      aria-pressed={recording}
      disabled={isDisabled}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={onPressCancel}
      onContextMenu={(e) => e.preventDefault()}
      style={{
        touchAction: "none",
        WebkitUserSelect: "none",
        userSelect: "none",
        WebkitTouchCallout: "none",
      }}
      className={`${base} ${tone} ${dimmed}`}
    >
      {recording && (
        <span className="absolute inset-0 animate-ping rounded-full bg-rose-400 opacity-75" />
      )}
      {requesting ? (
        <span className="relative z-10 h-6 w-6 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />
      ) : (
        <MicIcon muted={blocked} />
      )}
    </button>
  );
}
