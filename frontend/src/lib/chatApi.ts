/**
 * Chat API layer — TEXT-2 real implementation.
 *
 * Calls POST /conversations/{id}/messages and streams the reply via SSE.
 * The component layer wires onDelta/onComplete callbacks for progressive rendering.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Client-side timeout for the entire streaming request (ms). */
const STREAM_TIMEOUT_MS = 30_000;

/** Maximum prior turns sent to the LLM as context. */
export const MAX_RECENT_TURNS = 20;

interface Turn {
  role: "user" | "assistant";
  content: string;
}

interface StreamCallbacks {
  /** Called for each incremental text delta. */
  onDelta: (delta: string) => void;
  /** Called once when the stream finishes successfully. */
  onComplete: () => void;
}

/**
 * Send a user message to the backend and stream the assistant reply.
 *
 * @throws {Error} on HTTP errors, network failures, or mid-stream error events.
 */
export async function sendMessage(
  conversationId: string,
  text: string,
  recentTurns: Turn[],
  callbacks: StreamCallbacks,
): Promise<void> {
  // Abort the request if no response arrives within the timeout.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

  try {
    const res = await fetch(
      `${API_BASE}/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, recent_turns: recentTurns }),
        signal: controller.signal,
      },
    );

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(detail || `HTTP ${res.status}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("Response body is not readable");

    const decoder = new TextDecoder();
    let buffer = "";

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Reset the timeout on every chunk — the stream is alive.
      clearTimeout(timer);

      buffer += decoder.decode(value, { stream: true });

      // Split on double-newline; the last segment is potentially incomplete —
      // keep it in the buffer for the next read.
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const raw of parts) {
        const event = parseSseEvent(raw);
        if (!event) continue;

        switch (event.type) {
          case "delta":
            callbacks.onDelta((event.data as { text: string }).text);
            break;
          case "error":
            throw new Error((event.data as { detail: string }).detail);
          case "done":
            callbacks.onComplete();
            return;
        }
      }
    }

    // Stream ended without a `done` event — treat as an error.
    throw new Error("Stream ended unexpectedly");
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ── SSE parser ────────────────────────────────────────────────────────────────

interface SseEvent {
  type: string;
  data: unknown;
}

function parseSseEvent(raw: string): SseEvent | null {
  let eventType = "message";
  let dataStr = "";

  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataStr += line.slice(5).trim();
    }
    // Ignore id / retry / comment lines
  }

  if (!dataStr) return null;

  try {
    return { type: eventType, data: JSON.parse(dataStr) };
  } catch {
    return null;
  }
}
