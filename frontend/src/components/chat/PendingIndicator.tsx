/**
 * Animated typing indicator shown while awaiting an assistant reply.
 * Three staggered bouncing dots inside an assistant-style bubble.
 */
export function PendingIndicator() {
  return (
    <div className="flex animate-[fadeSlideIn_0.2s_ease-out_forwards] justify-start">
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-slate-800/60 bg-[var(--surface)] px-4 py-3.5">
        <span className="h-2 w-2 rounded-full bg-slate-400 animate-[typingBounce_1.4s_ease-in-out_infinite]" />
        <span className="h-2 w-2 rounded-full bg-slate-400 animate-[typingBounce_1.4s_ease-in-out_infinite_0.2s]" />
        <span className="h-2 w-2 rounded-full bg-slate-400 animate-[typingBounce_1.4s_ease-in-out_infinite_0.4s]" />
      </div>
    </div>
  );
}
