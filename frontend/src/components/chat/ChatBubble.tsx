import { isRtl } from "@/lib/rtl";
import type { Message } from "@/lib/types";
import type { SpeechStatus } from "@/lib/voice/useReplySpeech";
import { ReplaySpeechButton } from "@/components/voice/ReplaySpeechButton";

interface Props {
  message: Message;
  onRetry?: () => void;
  speechStatus?: SpeechStatus;
  onSpeechPlay?: () => void;
  onSpeechStop?: () => void;
  /** When set, this is the latest voice turn — offer a re-speak (VOICE-4). */
  onRedoVoice?: () => void;
}

export function ChatBubble({
  message,
  onRetry,
  speechStatus,
  onSpeechPlay,
  onSpeechStop,
  onRedoVoice,
}: Props) {
  const isUser = message.sender === "user";
  const isVoice = message.channel === "voice";
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

      {/* Timestamp — small, muted, below the bubble. Voice turns get a 🎤 tag. */}
      <span className="px-1 text-[0.6875rem] leading-none text-slate-600">
        {isUser && isVoice && <span className="mr-1">🎤</span>}
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

      {speechStatus && onSpeechPlay && onSpeechStop && (
        <ReplaySpeechButton
          status={speechStatus}
          onPlay={onSpeechPlay}
          onStop={onSpeechStop}
        />
      )}

      {onRedoVoice && (
        <button
          onClick={onRedoVoice}
          className="mt-0.5 inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700"
        >
          <span aria-hidden>↺</span> Ghalat? Phir bolein
        </button>
      )}
    </div>
  );
}
