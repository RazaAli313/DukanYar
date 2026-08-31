"use client";

import { useState, useCallback } from "react";
import type { Message } from "@/lib/types";
import { sendMessage } from "@/lib/chatApi";
import { ChatThread } from "./ChatThread";
import { ChatInput } from "./ChatInput";

function generateId(): string {
  return crypto.randomUUID();
}

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: Message = {
      id: generateId(),
      sender: "user",
      text,
      status: "complete",
      createdAt: new Date(),
    };

    const pendingMsg: Message = {
      id: generateId(),
      sender: "assistant",
      text: "",
      status: "pending",
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, pendingMsg]);

    try {
      const replyText = await sendMessage(text);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingMsg.id
            ? { ...m, text: replyText, status: "complete" as const }
            : m
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === pendingMsg.id
            ? {
                ...m,
                text: "Kuch masla ho gaya. Dubara koshish karein.",
                status: "error" as const,
              }
            : m
        )
      );
    }
  }, []);

  // TEXT-1 minimal retry: re-send the last user message
  const handleRetry = useCallback(
    (userMessage: Message) => {
      // Remove the failed assistant message and re-send
      setMessages((prev) =>
        prev.filter(
          (m) =>
            !(m.sender === "assistant" && m.status === "error" && m.createdAt > userMessage.createdAt)
        )
      );
      handleSend(userMessage.text);
    },
    [handleSend]
  );

  const isPending =
    messages.length > 0 &&
    messages[messages.length - 1].status === "pending";

  return (
    <div className="flex h-dvh bg-[var(--background)]">
      {/* ── Centered app column (720px) ───────────────────────── */}
      <div className="mx-auto flex h-full w-full max-w-[720px] flex-col">
        {/* ── Header ────────────────────────────────────────── */}
        <header className="flex h-14 shrink-0 items-center border-b border-slate-800/40 bg-[var(--surface)] px-4">
          <div className="flex items-center gap-3">
            <h1 className="text-[1.0625rem] font-semibold tracking-tight text-slate-100">
              DukanYar
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-800/70 px-2.5 py-0.5 text-[0.6875rem] font-medium text-slate-400">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inset-0 animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </span>
              AI
            </span>
          </div>
        </header>

        {/* ── Thread (scrollable) ───────────────────────────── */}
        <ChatThread messages={messages} onRetry={handleRetry} />

        {/* ── Input (pinned bottom) ─────────────────────────── */}
        <ChatInput onSend={handleSend} disabled={isPending} />
      </div>
    </div>
  );
}
