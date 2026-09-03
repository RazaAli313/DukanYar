"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Mic, Send, Loader2, Volume2 } from "lucide-react";
import {
  sendMessage,
  loadHistory,
  type ActionCard,
  type Mode,
} from "@/lib/chatApi";
import { api } from "@/lib/api";
import { usePushToTalk } from "@/lib/voice/usePushToTalk";
import { transcribeAudio, STT_MIN_CONFIDENCE } from "@/lib/voice/stt";
import { useReplySpeech } from "@/lib/voice/useReplySpeech";
import { MODES } from "./modes";
import { ConfirmationCard } from "./ConfirmationCard";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Msg {
  id: string;
  role: "user" | "assistant";
  text: string;
  status: "streaming" | "complete" | "error";
  channel?: "text" | "voice";
}

const uid = () => crypto.randomUUID();

export function ConversationScreen({ mode }: { mode: Mode }) {
  const cfg = MODES[mode];
  const router = useRouter();
  const speech = useReplySpeech();

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [card, setCard] = useState<ActionCard | null>(null);
  const [busy, setBusy] = useState(false);
  const [locked, setLocked] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // The thread is one per shop and persists — reload it so a refresh doesn't
  // wipe the conversation.
  useEffect(() => {
    loadHistory(25)
      .then(({ messages: hist }) => {
        setMessages(
          hist.map((h) => ({
            id: h.id,
            role: h.sender,
            text: h.text,
            status: h.status === "error" ? "error" : "complete",
            channel: h.channel,
          })),
        );
      })
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, []);

  // The raw proposed card (carries the private _fields the confirm call needs).
  const proposalRef = useRef<Record<string, unknown> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, card]);

  const runTurn = useCallback(
    async (text: string, channel: "text" | "voice", confidence?: number) => {
      if (busy || locked) return;
      speech.stop();
      setNotice(null);
      setCard(null);

      const userMsg: Msg = { id: uid(), role: "user", text, status: "complete", channel };
      const pending: Msg = { id: uid(), role: "assistant", text: "", status: "streaming" };
      setMessages((m) => [...m, userMsg, pending]);
      setBusy(true);

      let acc = "";
      try {
        await sendMessage(
          mode,
          text,
          {
            onMeta: ({ userText }) => {
              // Voice transcripts come back romanised — show what was stored.
              if (userText && userText !== text) {
                setMessages((m) =>
                  m.map((x) => (x.id === userMsg.id ? { ...x, text: userText } : x)),
                );
              }
            },
            onDelta: (d) => {
              acc += d;
              setMessages((m) =>
                m.map((x) => (x.id === pending.id ? { ...x, text: acc } : x)),
              );
            },
            onAction: (c) => {
              setCard(c);
              proposalRef.current = c as unknown as Record<string, unknown>;
            },
            onComplete: () => {
              setMessages((m) =>
                m.map((x) =>
                  x.id === pending.id ? { ...x, status: "complete" } : x,
                ),
              );
              if (channel === "voice" && acc.trim()) {
                void speech.speak(pending.id, acc);
              }
            },
          },
          channel,
          confidence,
        );
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Kuch masla ho gaya.";
        setMessages((m) =>
          m.map((x) =>
            x.id === pending.id
              ? { ...x, text: x.text || msg, status: "error" }
              : x,
          ),
        );
      } finally {
        setBusy(false);
      }
    },
    [busy, locked, mode, speech],
  );

  // ── voice ──────────────────────────────────────────────────────────────────
  const ptt = usePushToTalk({
    onAutoSubmit: (clip) => void handleClip(clip),
  });

  const handleClip = useCallback(
    async (clip: Awaited<ReturnType<typeof ptt.stop>>) => {
      if (!clip) return;
      setBusy(true);
      try {
        const { transcript, confidence } = await transcribeAudio(clip);
        if (!transcript.trim() || confidence < STT_MIN_CONFIDENCE) {
          setNotice("Awaaz saaf nahi aayi. Dobara boliye ya likh dein.");
          setBusy(false);
          return;
        }
        setBusy(false);
        await runTurn(transcript, "voice", confidence);
      } catch {
        setNotice("Awaaz process nahi ho saki. Likh kar bhejein.");
        setBusy(false);
      }
    },
    [runTurn],
  );

  const onMicUp = useCallback(async () => {
    const clip = await ptt.stop();
    void handleClip(clip);
  }, [ptt, handleClip]);

  // ── confirm the proposed action (sale / kharcha / udhaar) ──────────────────
  const confirmAction = useCallback(async () => {
    const p = proposalRef.current as Record<string, unknown> | null;
    if (!p) return;
    setBusy(true);
    try {
      let res;
      if (p.kind === "sale") {
        res = await api.confirmSale({
          items: (p._items as { name: string; quantity: number }[]) ?? [],
          stated_total: (p._stated_total as number) ?? 0,
          payment: (p.payment as "cash" | "udhaar") ?? "cash",
          khata_number: (p.khata_number as number | null) ?? null,
        });
      } else if (p.kind === "kharcha") {
        res = await api.confirmExpense({
          amount: (p._amount as number) ?? 0,
          desc: (p._desc as string) ?? null,
        });
      } else {
        res = await api.confirmUdhaar({
          amount: (p._amount as number) ?? 0,
          kind: (p._kind as "udhaar" | "payment") ?? "udhaar",
          khata_number: (p._khata_number as number | null) ?? null,
          customer_name: (p._customer_name as string | null) ?? null,
          cnic: (p._cnic as string | null) ?? null,
          new_customer: (p._new as boolean) ?? false,
        });
      }
      setCard(res.card as ActionCard);
      setLocked(true);
      const line = `${res.card.title} record ho gaya${
        res.card.note ? `. ${res.card.note}` : `, ${res.card.total}.`
      }`;
      setMessages((m) => [
        ...m,
        { id: uid(), role: "assistant", text: line, status: "complete" },
      ]);
      void speech.speak(uid(), line);
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Save nahi hua.");
    } finally {
      setBusy(false);
    }
  }, [speech]);

  const recording = ptt.status === "recording";
  const canSend = input.trim() && !busy && !locked;

  return (
    <div className="flex h-[calc(100dvh-8.5rem)] flex-col">
      {/* header */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => router.push("/app")}
          aria-label="Wapas"
        >
          <ArrowLeft className="size-4" />
        </Button>
        <div>
          <h1 className="font-serif text-lg font-semibold leading-tight">
            {cfg.title}
          </h1>
          <p className="text-xs text-muted-foreground">{cfg.hint}</p>
        </div>
      </div>

      {/* thread */}
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {loaded && messages.length === 0 && (
          <div className="mx-auto mt-10 max-w-xs text-center">
            <cfg.icon className="mx-auto size-8 text-muted-foreground" strokeWidth={1.5} />
            <p className="mt-3 text-sm text-muted-foreground">{cfg.placeholder}</p>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={cn(
              "flex animate-[fadeSlideIn_0.2s_ease-out_forwards]",
              m.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-3.5 py-2 text-[0.9375rem] leading-relaxed whitespace-pre-wrap",
                m.role === "user"
                  ? "rounded-br-sm bg-primary text-primary-foreground"
                  : m.status === "error"
                    ? "rounded-bl-sm bg-destructive/10 text-destructive"
                    : "rounded-bl-sm bg-card border border-border",
              )}
            >
              {m.text || (m.status === "streaming" ? "…" : "")}
              {m.role === "assistant" && m.channel === "voice" && m.text && (
                <button
                  onClick={() => speech.speak(m.id, m.text)}
                  className="ml-2 inline-flex align-middle text-muted-foreground"
                  aria-label="Dobara sunein"
                >
                  <Volume2 className="size-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}

        {card && (
          <div className="animate-[fadeSlideIn_0.2s_ease-out_forwards]">
            <ConfirmationCard
              card={card}
              busy={busy}
              onConfirm={confirmAction}
              onCancel={() => {
                setCard(null);
                proposalRef.current = null;
              }}
            />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* notice */}
      {notice && (
        <p className="border-t border-border bg-caution/40 px-4 py-2 text-center text-xs text-caution-foreground">
          {notice}
        </p>
      )}

      {/* input */}
      {locked ? (
        <div className="border-t border-border p-4">
          <Button className="w-full" onClick={() => router.push("/app")}>
            Ho gaya — wapas Ghar
          </Button>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSend) return;
            const t = input.trim();
            setInput("");
            void runTurn(t, "text");
          }}
          className="flex items-center gap-2 border-t border-border p-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={cfg.placeholder}
            disabled={busy || recording}
            className="flex-1 rounded-full border border-input bg-card px-4 py-2.5 text-[0.9375rem] outline-none placeholder:text-muted-foreground/70 focus:border-ring focus:ring-2 focus:ring-ring/30 disabled:opacity-50"
          />
          <button
            type="button"
            onMouseDown={ptt.start}
            onMouseUp={onMicUp}
            onMouseLeave={() => recording && onMicUp()}
            onTouchStart={(e) => {
              e.preventDefault();
              ptt.start();
            }}
            onTouchEnd={(e) => {
              e.preventDefault();
              void onMicUp();
            }}
            disabled={busy || !!input.trim()}
            aria-label="Bol kar likhein"
            className={cn(
              "flex size-11 shrink-0 items-center justify-center rounded-full transition-all active:scale-95 disabled:opacity-30",
              recording
                ? "animate-pulse bg-destructive text-white"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
            )}
          >
            <Mic className="size-5" />
          </button>
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Bhejein"
            className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all active:scale-95 disabled:opacity-30"
          >
            {busy ? <Loader2 className="size-5 animate-spin" /> : <Send className="size-5" />}
          </button>
        </form>
      )}
    </div>
  );
}
