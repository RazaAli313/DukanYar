### TEXT-5 — Dashboard + mode-based conversation screen

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-5 |
| Ticket Name | Dashboard + mode-based conversation screen |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | TEXT-3 (BE persistence, done), AUTH `app_metadata.shop_id` fix, frontend app-tree reconciliation, RPT views (in phase-3 migration) |
| Estimate | BE: small (mode field + prompt/tool routing) \| FE: TBD |
| Source References | TEXT-3 review (2026-09-02) — "history reloads on return" is a UI scenario left unmet by the backend-only TEXT-3. Design discussion (2026-09-03) — shopkeeper picks the intent from the dashboard instead of the LLM classifying it. |

**Description:** As a shopkeeper, I want to open the app to a summary of my day and
tap what I want to record (Sale / Udhaar / Kharcha / Poocho), then handle it by
voice on one consistent screen — so the assistant never has to guess what I meant,
and my earlier messages are still there when I come back.

**Design decision — shopkeeper picks the mode, the LLM does not classify intent.**
Intent classification with a small model on accented Urdu is unreliable, and this
is a money-handling app — logging a sale as an expense loses trust instantly. A tap
is a 100%-accurate, zero-latency, zero-cost intent signal. The LLM's job shrinks to
the part it is good at: pulling structured fields out of messy speech, and running
the confirmation dialogue. This also simplifies the TOOL epic — tool calls are
scoped by mode, there is no router.

---

## Screen 1 — Dashboard (`/app`)

Not a product catalog. "What is my business doing today" + "what do I want to
record".

```
┌───────────────────────────────────────┐
│  Assalam o alaikum, <shop name>        │
│                                       │
│  Aaj                                   │
│    Sale       ₨ 12,400                 │  ← daily_sales_profit_view (total_sales)
│    Profit     ₨  3,100                 │  ← daily_sales_profit_view (total_profit)
│    Udhaar baqaya  ₨ 8,500              │  ← outstanding_udhaar_view (Σ balance)
│    ⚠ 3 cheezein kam stock              │  ← low_stock_view (count)
│                                       │
│   ┌─────────┐   ┌─────────┐            │
│   │  Sale   │   │ Udhaar  │            │
│   ├─────────┤   ├─────────┤            │
│   │ Kharcha │   │ Poocho  │            │
│   └─────────┘   └─────────┘            │
└───────────────────────────────────────┘
```

- Today's numbers come straight from the RPT views already created in
  `20260902070905_sale_khata_exp_tool_admin_rpt.sql` — a read per view, scoped by
  `shop_id`.
- The four cards route to `/record/<mode>`.
- Products / inventory live in a separate nav section, not on the dashboard.

## Screen 2 — Conversation screen (`/record/[mode]`)

One shared component, `ConversationScreen`, configured by `mode` ∈
`sale | udhaar | kharcha | ask`.

**Shared across every mode (build once, reuse):**
- push-to-talk voice bar + text input
- message thread / transcript display
- streaming reply render (SSE `delta`)
- TTS playback of the reply

**Per-mode configuration (`modes.ts`):**

| | sale | udhaar | kharcha | ask |
| :-- | :-- | :-- | :-- | :-- |
| Heading | Naya Sale | Udhaar | Kharcha | Poocho |
| Tool given to the LLM | `record_sale` | `log_udhaar` | `record_expense` | none |
| System prompt | slot-fill a sale | slot-fill a ledger entry | slot-fill an expense | Q&A only, no writes |
| Confirmation card | line items + total | customer + amount | category + amount | none |
| After execute | disable inputs, speak summary | same | same | never — stays open, multi-turn |

```
src/components/conversation/
  ConversationScreen.tsx      # shared shell
  modes.ts                    # { sale: {title, tool, prompt, Confirm, accent}, ... }
  confirmations/
    SaleConfirmation.tsx      # the one genuinely per-mode piece
    UdhaarConfirmation.tsx
    KharchaConfirmation.tsx
```

`ChatScreen` / `ChatThread` / `ChatInput` / `VoiceBar` are refactored into
`ConversationScreen` + retained sub-components.

## The record flow (sale / udhaar / kharcha)

1. Shopkeeper is on `/record/sale`, says *"do coke aik chips chaar so"*.
2. STT → text → LLM call **with the `record_sale` tool** → structured args
   `{ items: [{coke, 2}, {chips, 1}], total: 400 }`.
3. **Confirmation card renders on screen** (visual) *and* the assistant speaks it:
   *"Do coke, aik chips, total ₨400 — theek hai?"*
4. **Mic + text stay active** — shopkeeper can say "haan" or correct it
   ("nahi, teen coke"). A correction loops back to step 2 with the amended args.
5. On "haan" → execute: `sales` insert → `sold_items` → stock decrement →
   `ledger_entries` (if the payment type is udhaar/split) → RPT views update
   themselves.
6. **Only now** disable mic + text.
7. Assistant speaks the outcome: *"Sale record ho gayi. Aaj ki sale ab ₨12,800,
   profit ₨3,300."* Any stock warning (negative inventory, SALE-4) is spoken here.
8. A "Naya Sale" button re-enables inputs, or the screen returns to the dashboard.

Inputs disable **after** the operation succeeds, never before the confirmation.
The confirmation is always card **and** voice, so the shopkeeper can eyeball
"coke 2, chips 1" even if the audio was unclear.

`ask` mode skips steps 2-7 entirely: no tool, no confirmation, no disable — it is
a normal multi-turn Q&A ("aaj kitni sale hui", "kaun kitna udhaar") that only
reads.

## Backend impact (small)

- `MessageRequest` gains `mode: "sale" | "udhaar" | "kharcha" | "ask"`.
- The router picks the system prompt and the tool list from `mode` — no intent
  classification, no routing model.
- Tool execution + the confirmation gate belong to the TOOL epic; TEXT-5 only
  wires `mode` through and renders the confirmation card.

---

## Integration work (pre-existing blockers, unchanged)

| Task | Notes |
| :-- | :-- |
| Reconcile the two `app/` trees | Delete `src/app/`; keep `src/components` + `src/lib`. Next.js serves only the root `app/`, so the chat UI under `src/app/` has never rendered. |
| Merge `globals.css` | `src/app/globals.css` is Tailwind **v4** (`@import`, `@theme`, theme tokens, keyframes) — the components need it. Root `app/globals.css` uses **v3** directives though v4 is installed. |
| Fonts | Components expect Geist (`--font-geist-sans`); root layout loads Inter. |
| Attach the token | `supabase.auth.getSession()` → `Authorization: Bearer <access_token>` on every backend call. |
| Load history on mount | `GET /conversations/history` → map `{role, content}` → the frontend `Message` shape (`sender`, `text`). |
| Drop the client-generated conversation id | The server resolves the shop's thread; read it from the SSE `meta` event. |
| Stop sending `recent_turns` | The backend ignores it; context comes from the DB. |
| Fix `middleware.ts` | Selects `profiles.role`; the column is `role_name`, so admin/shopkeeper redirects never fire. |

**Blocked on:** `public.current_shop_id()` reads `app_metadata.shop_id`, which
nothing populates. The TEXT-3 backend does not depend on it (service_role + manual
scoping), but the dashboard's RPT-view reads and any other RLS-bound frontend query
do. Owned by the AUTH epic.

**Acceptance Criteria:**
```gherkin
Feature: Dashboard + mode-based conversation screen

  Scenario: Dashboard shows today at a glance
    Given a signed-in shopkeeper
    When they open the app
    Then they see today's sales, profit, outstanding udhaar and low-stock count
    And four actions: Sale, Udhaar, Kharcha, Poocho

  Scenario: Picking a mode opens the shared conversation screen
    Given the shopkeeper taps "Sale"
    When the conversation screen opens
    Then the heading reads "Naya Sale"
    And the same voice bar, text input and transcript are used as every other mode

  Scenario: The assistant never guesses the intent
    Given the shopkeeper is in "Kharcha" mode
    When they speak
    Then the backend uses the expense prompt and the expense tool only
    And no intent-classification step runs

  Scenario: Confirmation before any write
    Given the shopkeeper has described a sale
    Then the parsed items and total are shown on a card and spoken aloud
    And the mic stays active for a yes / no / correction
    And nothing is written until the shopkeeper agrees

  Scenario: Inputs lock after a successful operation
    Given the shopkeeper confirms the sale
    When the sale, stock and ledger updates succeed
    Then the mic and text input are disabled
    And the outcome and updated day total are spoken

  Scenario: Ask mode is read-only and stays open
    Given the shopkeeper is in "Poocho" mode
    When they ask about today's sales
    Then they get an answer with no confirmation card
    And the inputs are never disabled

  Scenario: History reloads on return
    Given the shopkeeper has an existing conversation
    When they reopen or refresh the app
    Then the previous messages are shown in order

  Scenario: Requests are authenticated
    Given the shopkeeper sends a message
    Then the request carries their Supabase access token
    And the reply is persisted against their shop's thread

  Scenario: Auth pages keep working
    Given the globals.css and layout are reconciled
    When the login and signup pages are opened
    Then their styling is unbroken
```
