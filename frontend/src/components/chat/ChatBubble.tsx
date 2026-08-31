import { isRtl } from "@/lib/rtl";
import type { Message } from "@/lib/types";

interface Props {
  message: Message;
  onRetry?: () => void;
}

export function ChatBubble({ message, onRetry }: Props) {
  const isUser = message.sender === "user";
  const rtl = isRtl(message.text);

  return (
    <div
      className={`flex flex-col gap-0.5 animate-[fadeSlideIn_0.25s_ease-out_forwards] ${
        isUser ? "items-end" : "items-start"
      }`}
    >
      <div
        className={`max-w-[75%] md:max-w-[65%] rounded-2xl px-4 py-2.5 leading-relaxed whitespace-pre-wrap break-words ${
          isUser
            ? "bg-emerald-700 text-emerald-50 rounded-br-md"
            : "bg-[var(--surface)] text-slate-200 rounded-bl-md border border-slate-800/50"
        }`}
        {...(rtl ? { dir: "rtl", lang: "ur" } : {})}
      >
        <p className="text-[0.9375rem] leading-[1.55]">{message.text}</p>
      </div>

      {/* Timestamp — small, muted, below the bubble */}
      <span className="px-1 text-[0.6875rem] leading-none text-slate-600">
        {message.createdAt.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>

      {message.status === "error" && onRetry && (
        <button
          onClick={onRetry}
          className="mt-0.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-rose-300 transition-colors hover:bg-slate-700"
        >
          Dubara bhejein
        </button>
      )}
    </div>
  );
}
