# DukanYar — Project-Wide ERD

**FigJam link:** [DukanYar Project-Wide ERD](https://www.figma.com/board/w7Dyt8IonzheO7ly4HbC18/DukanYar-Project-Wide-ERD?node-id=0-1&t=7DddBYAutMPcDs1o-1)

## Description

This diagram consolidates the entities established across every epic's per-ticket ERDs
(ADMIN, AUTH, CATLG, EXP, FND, KHATA, RPT, SALE, TEXT, TOOL, VOICE) into a single
canonical schema, with duplicate/placeholder tables from individual tickets reconciled
into shared entities.

### Core identity & tenancy (FND-2, AUTH-1/2/3)

- **SHOP**, **ROLE**, **USER**, **SESSION** — every user belongs to one shop and one role;
  sessions back authentication.

### Conversation (FND-2, TEXT-2/3, VOICE-2)

- **CONVERSATION** → **MESSAGE** — shared by text and voice; `channel` distinguishes the
  two, `status` tracks streaming/retry, `transcriptionConfidence` is populated for voice
  messages only.

### Tool-calling & orchestration (TOOL-1/2/3/4)

- **TOOL_DEFINITION** → **TOOL_CALL** → **ACTION_CONFIRMATION** / **CONFIRMATION_CARD** —
  the generic backbone behind every voice/text-triggered action (sales, udhaar, expenses,
  catalog edits). Feature-specific "parse request" tables from individual tickets
  (e.g. `EXPENSE_LOG_REQUEST`, `REPAYMENT_REQUEST`) collapse into this pattern.

### Sales & inventory (SALE-1/2/3/4)

- **PRODUCT**, **PRODUCT_ALIAS**, **ITEM_RESOLUTION**, **LOW_STOCK_ALERT**
- **SALE** → **SALE_LINE** → **PRODUCT**, with **STOCK_MOVEMENT** recording each atomic
  decrement (or undo) and its out-of-stock flag.

### Udhaar / credit ledger (KHATA-1/2/3/4)

- **CUSTOMER** (khata number + CNIC fallback) → **LEDGER_ENTRY** (`udhaar` or `payment`),
  optionally linked back to the originating **SALE**.

### Expenses (EXP-1/2/3)

- **EXPENSE_CATEGORY** → **EXPENSE**, shop-scoped.

### Admin oversight (ADMIN-1/2/3)

- **AUDIT_LOG** (user + optionally shop-scoped action trail), standalone **SERVICE_HEALTH**
  snapshot. Voice/transcription monitoring reads `MESSAGE` filtered to the voice channel
  rather than a separate table.

### Reporting (RPT-1/2/3/4)

- **DAILY_SALES_PROFIT_VIEW**, **OUTSTANDING_UDHAAR_VIEW**, **LOW_STOCK_VIEW** — owned,
  shop-scoped read views aggregating `SALE`, `LEDGER_ENTRY`, and `PRODUCT` respectively.

---

_Generated from the epic/ticket ERDs — see each pillar's `docs/<pillar>/` folder for the
per-ticket diagrams and source tickets this was reconciled from._
