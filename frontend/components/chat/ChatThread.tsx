"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/lib/types";
import type { SpeechStatus } from "@/lib/voice/useReplySpeech";
import { ChatBubble } from "./ChatBubble";
import { PendingIndicator } from "./PendingIndicator";

export interface SpeechControls {
  activeId: string | null;
  status: SpeechStatus;
  onPlay: (message: Message) => void;
  onStop: () => void;
}

interface Props {
  messages: Message[];
  onRetry: (userMessage: Message) => void;
  speech?: SpeechControls;
  /** Re-speak the latest voice turn (VOICE-4) — discards it and everything after. */
  onRedoVoice?: (userMessage: Message) => void;
}

export function ChatThread({ messages, onRetry, speech, onRedoVoice }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages or status changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Detect pending: last message is an assistant with status "pending"
  const lastMsg = messages[messages.length - 1];
  const showPending =
    lastMsg?.sender === "assistant" && lastMsg.status === "pending";

  // The most recent voice turn gets a re-speak affordance (VOICE-4), as long as
  // the exchange isn't mid-flight. It stays available even if later text turns
  // followed — re-speaking discards that voice turn and everything after it.
  const busy =
    lastMsg?.status === "pending" || lastMsg?.status === "streaming";
  let latestVoiceUserId: string | null = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].sender === "user" && messages[i].channel === "voice") {
      latestVoiceUserId = messages[i].id;
      break;
    }
  }

  // ── Empty state ────────────────────────────────────────────
  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center px-6">
        <div className="max-w-sm text-center space-y-3">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-3xl">
            🏪
          </div>
          <p className="text-lg font-semibold text-slate-100">
            Assalam-o-alaikum!
          </p>
          <p className="text-sm leading-relaxed text-slate-400">
            Main aapki dukaan ka AI assistant hoon. Koi bhi sawaal poochein —
            main madad ke liye tayyar hoon.
          </p>
        </div>
      </div>
    );
  }

  // ── Message list ───────────────────────────────────────────
  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      <div className="flex flex-col gap-3">
        {messages.map((msg, idx) => {
          const isUser = msg.sender === "user";

          // For user bubbles: retry re-sends this user message.
          let retryHandler: (() => void) | undefined;
          if (isUser) {
            retryHandler = () => onRetry(msg);
          } else if (msg.status === "error") {
            // For assistant error bubbles: find the most recent user message
            // before this one and retry that.
            for (let i = idx - 1; i >= 0; i--) {
              if (messages[i].sender === "user") {
                const userMsg = messages[i];
                retryHandler = () => onRetry(userMsg);
                break;
              }
            }
          }

          // For spoken assistant replies: a play / replay control (VOICE-3).
          let speechStatus: SpeechStatus | undefined;
          let onSpeechPlay: (() => void) | undefined;
          let onSpeechStop: (() => void) | undefined;
          if (
            speech &&
            !isUser &&
            msg.spoken &&
            msg.status === "complete"
          ) {
            speechStatus =
              speech.activeId === msg.id ? speech.status : "idle";
            onSpeechPlay = () => speech.onPlay(msg);
            onSpeechStop = speech.onStop;
          }

          const redoHandler =
            !busy && onRedoVoice && msg.id === latestVoiceUserId
              ? () => onRedoVoice(msg)
              : undefined;

          return (
            <ChatBubble
              key={msg.id}
              message={msg}
              onRetry={retryHandler}
              speechStatus={speechStatus}
              onSpeechPlay={onSpeechPlay}
              onSpeechStop={onSpeechStop}
              onRedoVoice={redoHandler}
            />
          );
        })}

        {showPending && <PendingIndicator />}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
