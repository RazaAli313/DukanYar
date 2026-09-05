/**
 * Chat API — talks to the FastAPI backend's conversation endpoint.
 *
 * Every call carries the shopkeeper's Supabase access token; the backend
 * resolves their shop from it (see backend/app/auth.py). The conversation is
 * the shop's single thread — its id is discovered from the SSE `meta` event,
 * never sent by the client.
 */

import { createClient } from "@/utils/supabase/client";
import type { Channel, Message, Sender } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Abort a stream that goes quiet for this long. */
const STREAM_TIMEOUT_MS = 45_000;

/** Which record flow the shopkeeper picked on the dashboard. */
export type Mode = "sale" | "udhaar" | "kharcha" | "ask";

/** Structured result of a tool the assistant ran (TOOL-4 / SALE-3). */
export interface ActionCard {
  kind: "sale" | "udhaar" | "kharcha";
  status: "proposed" | "recorded" | "failed";
  title: string;
  lines: { label: string; value: string; muted?: boolean; flag?: boolean }[];
  total?: string;
  note?: string;
}

interface StreamHandlers {
  /** Delivered before the first delta: the shop's conversation id, and the
   *  message as it was stored (voice transcripts are romanised server-side). */
  onMeta?: (meta: { conversationId: string; userText?: string }) => void;
  onDelta: (delta: string) => void;
  /** A tool proposed or executed an action. */
  onAction?: (action: ActionCard) => void;
  onComplete: () => void;
}

async function authHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) throw new Error("Aap login nahi hain. Dobara login karein.");
  return { Authorization: `Bearer ${session.access_token}` };
}

// ── send a message, stream the reply ─────────────────────────────────────────

export async function sendMessage(
  mode: Mode,
  text: string,
  handlers: StreamHandlers,
  channel: Channel = "text",
  transcriptionConfidence?: number,
): Promise<void> {
  const controller = new AbortController();
  let timer = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/conversations/active/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(await authHeader()),
      },
      body: JSON.stringify({
        text,
        channel,
        mode,
        transcription_confidence: transcriptionConfidence ?? null,
      }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(humanError(res.status, detail));
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("Reply stream nahi mila");

    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;

      clearTimeout(timer);
      timer = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const raw of parts) {
        const evt = parseSse(raw);
        if (!evt) continue;

        switch (evt.type) {
          case "meta": {
            const m = evt.data as { conversation_id: string; user_text?: string };
            handlers.onMeta?.({ conversationId: m.conversation_id, userText: m.user_text });
            break;
          }
          case "delta":
            handlers.onDelta((evt.data as { text: string }).text);
            break;
          case "action":
            handlers.onAction?.(evt.data as ActionCard);
            break;
          case "error":
            throw new Error((evt.data as { detail: string }).detail);
          case "done":
            handlers.onComplete();
            return;
        }
      }
    }
    throw new Error("Reply adhoori reh gayi. Dobara koshish karein.");
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Bahut der ho gayi. Dobara koshish karein.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ── load the shop's thread ───────────────────────────────────────────────────

interface HistoryRow {
  id: string;
  role: Sender;
  content: string;
  channel: Channel | null;
  status: string | null;
  transcription_confidence: number | null;
  created_at: string;
}

export async function loadHistory(
  limit = 30,
): Promise<{ conversationId: string | null; messages: Message[] }> {
  const res = await fetch(`${API_BASE}/conversations/history?limit=${limit}`, {
    headers: await authHeader(),
  });
  if (!res.ok) {
    throw new Error(humanError(res.status, await res.text().catch(() => "")));
  }
  const body = (await res.json()) as {
    conversation_id: string | null;
    messages: HistoryRow[];
  };
  return {
    conversationId: body.conversation_id,
    messages: body.messages.map((r) => ({
      id: r.id,
      sender: r.role,
      text: r.content,
      status: r.status === "failed" ? "error" : "complete",
      createdAt: new Date(r.created_at),
      channel: r.channel ?? undefined,
    })),
  };
}

// ── helpers ──────────────────────────────────────────────────────────────────

interface SseEvent {
  type: string;
  data: unknown;
}

function parseSse(raw: string): SseEvent | null {
  let type = "message";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) type = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return null;
  try {
    return { type, data: JSON.parse(data) };
  } catch {
    return null;
  }
}

function humanError(status: number, detail: string): string {
  if (status === 401) return "Session khatam ho gaya. Dobara login karein.";
  if (status === 403) return "Is dukaan ka access nahi.";
  if (status === 502) return "AI abhi jawab nahi de pa raha. Thodi der baad koshish karein.";
  return detail || `Error ${status}`;
}
