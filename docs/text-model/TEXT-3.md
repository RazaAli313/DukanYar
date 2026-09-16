### TEXT-3 — Conversation persistence & history

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-3 |
| Ticket Name | Conversation persistence & history |
| Status | BE Done \| FE pending (TEXT-5) |
| Priority | P2 — Normal |
| Dependencies | TEXT-2 (conversation endpoint), FND-2 (conversations/messages tables), AUTH-3 (shop scoping) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — conversation history, multi-tenant |

**Description:** As a shopkeeper, I want my conversation saved and reloaded, so that I
can see earlier messages after closing and reopening the app, and so the assistant
can use recent context within a conversation.

**Acceptance Criteria:**
```gherkin
Feature: Text pillar — conversation persistence

  Scenario: Messages are persisted
    Given the shopkeeper sends a message and receives a reply
    Then both the user message and the assistant reply are stored against their conversation

  Scenario: History reloads on return
    Given the shopkeeper has an existing conversation
    When they reopen the app
    Then the previous messages are shown in order

  Scenario: History is scoped to the shop
    Given two shops each have conversations
    When a shopkeeper loads their history
    Then only their own shop's messages are returned, never another shop's

  Scenario: Recent context is available to the model
    Given a conversation has prior messages
    When a new message is sent
    Then the backend includes recent prior turns as context in the model call
```

---

## Implementation notes (BE, 2026-09-02)

**Design decision — one thread per shop.** There is exactly one `conversations`
row per shop, lazily created on the first message and never closed. No session or
thread concept, nothing archived: a shopkeeper thinks *"meri dukaan ki baat-cheet"*,
not *"conversation #5"*. The `{conversation_id}` in the POST path is therefore
accepted but ignored — the shop's thread is resolved server-side, so a client
cannot address another shop's thread or invent one.

**Storage and context are separate.** Every message is stored forever (INSERT
only, no pruning) — rows are ~1KB and the audit trail is what makes *"did I really
record that expense?"* answerable. What is capped is how much history each model
call replays: `LLM_MAX_CONTEXT_TURNS` (default 8), applied at read time. Token
cost and latency come from the prompt, not the table. Note this is a behaviour
change: the frontend previously sent up to 20 turns from memory, and that field
(`recent_turns`) is now accepted-but-ignored.

**Voice collapses to text.** The transcript lands in `messages.message` with
`channel='voice'` and `transcription_confidence`; audio is never stored (VOICE-2
deferred this persistence here).

**Ordering inside the POST handler** is load-bearing:
1. pre-flight the LLM client *before any write*, so a config failure cannot leave
   an orphan user message that a retry would duplicate;
2. read the context window *before* persisting the new message, so the current
   text is not both replayed as history and appended as the live turn;
3. persist the assistant reply only after the stream closes, and only if it
   produced text. Client disconnect (`asyncio.CancelledError` — a `BaseException`,
   so it needs its own handler) persists the partial as `failed` under
   `asyncio.shield`.

Failed / half-streamed replies are never replayed as context.

**Auth.** `Authorization: Bearer <supabase access token>` is required. The token
is verified with Supabase and `shop_id` / `role_name` come from `public.profiles`
— *not* from JWT claims. `public.current_shop_id()` reads
`app_metadata.shop_id`, which nothing currently populates, but that only affects
RLS-bound clients; this backend uses the service_role key and scopes every query
itself.

**Endpoints**
| method | path | notes |
| :-- | :-- | :-- |
| POST | `/conversations/{conversation_id}/messages` | path id ignored; SSE `meta` → `delta`… → `done` \| `error` |
| GET | `/conversations/history?limit=30` | oldest-first; `{conversation_id, messages: [{id, role, content, channel, status, transcription_confidence, created_at}]}` |

**Not applied:** `supabase/migrations/20260902190000_text3_conversation_shop_unique.sql`
adds `UNIQUE(conversations.shop_id)`. It needs an ack from the migrations owner
first — see the consequence note in the file (deleting the creating auth user
would cascade away the shop's entire history).

**AC status:** "messages persisted", "scoped to the shop", and "recent context
reaches the model" are met and tested. **"History reloads on return" is met on the
backend only** — the endpoint exists; rendering it is TEXT-5.
