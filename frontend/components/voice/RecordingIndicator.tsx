"use client";

/**
 * Shown for the entire push-to-talk capture (VOICE-1 AC #3).
 * Pulsing dot + status text + ticking elapsed seconds.
 */

interface Props {
  elapsedMs: number;
}

function formatElapsed(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function RecordingIndicator({ elapsedMs }: Props) {
  return (
    <div
      aria-live="polite"
      className="flex items-center justify-center gap-2 text-[0.8125rem] text-slate-300"
    >
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inset-0 animate-ping rounded-full bg-rose-500 opacity-75" />
        <span className="relative h-2.5 w-2.5 rounded-full bg-rose-500" />
      </span>
      <span>Sun raha hoon…</span>
      <span className="tabular-nums text-slate-500">
        {formatElapsed(elapsedMs)}
      </span>
    </div>
  );
}
