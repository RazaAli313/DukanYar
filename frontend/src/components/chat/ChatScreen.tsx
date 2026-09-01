"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type { Channel, Message } from "@/lib/types";
import { sendMessage, MAX_RECENT_TURNS } from "@/lib/chatApi";
import { useReplySpeech } from "@/lib/voice/useReplySpeech";
import { ChatThread } from "./ChatThread";
import { ChatInput } from "./ChatInput";
import { VoiceBar } from "@/components/voice/VoiceBar";

function generateId(): string {
  return crypto.randomUUID();
}

/** Map frontend Message to the Turn shape expected by the backend. */
function toTurns(messages: Message[]): { role: "user" | "assistant"; content: string }[] {
  return messages
    .filter((m) => m.status === "complete" || m.status === "streaming")
    .slice(-MAX_RECENT_TURNS)
    .map((m) => ({
      role: m.sender === "user" ? ("user" as const) : ("assistant" as const),
      content: m.text,
    }));
}

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  // One conversation ID per tab session — stable across messages.
  const [conversationId] = useState(() => generateId());
  const speech = useReplySpeech();
  // Speak assistant replies aloud (any channel). On by default — voice-first.
  const [speakReplies, setSpeakReplies] = useState(true);
  const speakRepliesRef = useRef(speakReplies);
  useEffect(() => {
    speakRepliesRef.current = speakReplies;
  }, [speakReplies]);

  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);
  const noticeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flashVoiceNotice = useCallback((msg: string) => {
    setVoiceNotice(msg);
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => setVoiceNotice(null), 4000);
  }, []);

  const handleSend = useCallback(
    async (text: string, channel: Channel = "text") => {
      let replyText = "";
      speech.stop(); // a new message supersedes any playing reply
      setVoiceNotice(null);
      // ── FIX B: build recent_turns BEFORE appending the new user message,
      // so the current message is not sent twice (once in recent_turns, once as text).
      const recentTurns = toTurns(messages);

      const userMsg: Message = {
        id: generateId(),
        sender: "user",
        text,
        status: "complete",
        createdAt: new Date(),
        channel,
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
        await sendMessage(
          conversationId,
          text,
          recentTurns,
          {
            onDelta: (delta) => {
              replyText += delta;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === pendingMsg.id
                    ? {
                        ...m,
                        text: m.text + delta,
                        // Flip to "streaming" on first delta
                        status: m.status === "pending" ? "streaming" : m.status,
                      }
                    : m,
                ),
              );
            },
            onComplete: () => {
              const speakThis =
                speakRepliesRef.current && replyText.trim().length > 0;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === pendingMsg.id
                    ? {
                        ...m,
                        status: "complete" as const,
                        spoken: speakThis || undefined,
                      }
                    : m,
                ),
              );
              if (speakThis) void speech.speak(pendingMsg.id, replyText);
            },
          },
          channel,
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingMsg.id
              ? {
                  ...m,
                  text:
                    m.text || "Kuch masla ho gaya. Dubara koshish karein.",
                  status: "error" as const,
                }
              : m,
          ),
        );
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [messages, conversationId],
  );

  // ── FIX C: retry must NOT call handleSend (which appends a new user bubble).
  // It removes the failed assistant message, appends a fresh placeholder,
  // and re-streams against the existing user message.
  const handleRetry = useCallback(
    async (userMessage: Message) => {
      let replyText = "";
      // FIX: use message ID to find the failed assistant bubble — createdAt
      // timestamps can be equal (same JS tick), breaking > comparison.
      const userIdx = messages.findIndex((m) => m.id === userMessage.id);
      const failedAssistantId = messages.find(
        (m, i) =>
          i > userIdx &&
          m.sender === "assistant" &&
          m.status === "error",
      )?.id;

      // Remove the failed assistant bubble by ID.
      setMessages((prev) =>
        prev.filter((m) => m.id !== failedAssistantId),
      );

      // Build recent_turns from messages BEFORE this user message (exclusive).
      const contextMessages = messages.slice(0, userIdx);
      const recentTurns = toTurns(contextMessages);

      const pendingMsg: Message = {
        id: generateId(),
        sender: "assistant",
        text: "",
        status: "pending",
        createdAt: new Date(),
      };

      // Append the fresh placeholder
      setMessages((prev) => [...prev, pendingMsg]);

      try {
        await sendMessage(
          conversationId,
          userMessage.text,
          recentTurns,
          {
            onDelta: (delta) => {
              replyText += delta;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === pendingMsg.id
                    ? {
                        ...m,
                        text: m.text + delta,
                        status: m.status === "pending" ? "streaming" : m.status,
                      }
                    : m,
                ),
              );
            },
            onComplete: () => {
              const speakThis =
                speakRepliesRef.current && replyText.trim().length > 0;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === pendingMsg.id
                    ? {
                        ...m,
                        status: "complete" as const,
                        spoken: speakThis || undefined,
                      }
                    : m,
                ),
              );
              if (speakThis) void speech.speak(pendingMsg.id, replyText);
            },
          },
          userMessage.channel ?? "text",
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingMsg.id
              ? {
                  ...m,
                  text: "Kuch masla ho gaya. Dubara koshish karein.",
                  status: "error" as const,
                }
              : m,
          ),
        );
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [messages, conversationId],
  );

  // ── VOICE-4: re-speak a mis-transcribed voice turn.
  // Drops that turn + everything after it, then invites a fresh recording.
  // Shopkeepers don't type Urdu, so correction is by voice, not by editing text.
  const handleRedoVoice = useCallback(
    (userMessage: Message) => {
      speech.stop();
      setMessages((prev) => {
        const idx = prev.findIndex((m) => m.id === userMessage.id);
        return idx === -1 ? prev : prev.slice(0, idx);
      });
      flashVoiceNotice("Phir boliye — mic dabaye rakhein");
    },
    [speech, flashVoiceNotice],
  );

  const isPending =
    messages.length > 0 &&
    (messages[messages.length - 1].status === "pending" ||
      messages[messages.length - 1].status === "streaming");

  return (
    <div className="flex h-dvh bg-[var(--background)]">
      {/* ── Centered app column (720px) ───────────────────────── */}
      <div className="mx-auto flex h-full w-full max-w-[720px] flex-col">
        {/* ── Header ────────────────────────────────────────── */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-800/40 bg-[var(--surface)] px-4">
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

          <button
            onClick={() => {
              setSpeakReplies((on) => {
                if (on) speech.stop();
                return !on;
              });
            }}
            aria-pressed={speakReplies}
            aria-label={
              speakReplies ? "Awaaz band karein" : "Awaaz chaalu karein"
            }
            className={`flex h-8 w-8 items-center justify-center rounded-full text-base transition-colors ${
              speakReplies
                ? "bg-emerald-500/15 text-emerald-300"
                : "bg-slate-800 text-slate-500"
            }`}
          >
            {speakReplies ? "🔊" : "🔇"}
          </button>
        </header>

        {/* ── Thread (scrollable) ───────────────────────────── */}
        <ChatThread
          messages={messages}
          onRetry={handleRetry}
          onRedoVoice={handleRedoVoice}
          speech={{
            activeId: speech.activeId,
            status: speech.status,
            onPlay: (m) => void speech.speak(m.id, m.text),
            onStop: speech.stop,
          }}
        />

        {/* ── Voice bar (push-to-talk) ──────────────────────── */}
        <VoiceBar
          onSend={handleSend}
          disabled={isPending}
          onCaptureStart={speech.stop}
          notice={voiceNotice}
        />

        {/* ── Input (pinned bottom) ─────────────────────────── */}
        <ChatInput onSend={handleSend} disabled={isPending} />
      </div>
    </div>
  );
}
