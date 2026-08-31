"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/lib/types";
import { ChatBubble } from "./ChatBubble";
import { PendingIndicator } from "./PendingIndicator";

interface Props {
  messages: Message[];
  onRetry: (userMessage: Message) => void;
}

export function ChatThread({ messages, onRetry }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages or status changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Detect pending: last message is an assistant with status "pending"
  const lastMsg = messages[messages.length - 1];
  const showPending =
    lastMsg?.sender === "assistant" && lastMsg.status === "pending";

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
        {messages.map((msg) => {
          const isUser = msg.sender === "user";
          return (
            <ChatBubble
              key={msg.id}
              message={msg}
              onRetry={isUser ? () => onRetry(msg) : undefined}
            />
          );
        })}

        {showPending && <PendingIndicator />}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
