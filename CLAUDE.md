# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DukanYar is a voice-first AI assistant for small retail shopkeepers in Pakistan. Shopkeepers speak Urdu (or Roman-Urdu) to log sales, record expenses, manage credit (udhaar/khata), and query their shop data. The UI is a mobile-first chat interface.

## Dev commands

### Backend (FastAPI, Python 3.13, uv)

```bash
cd backend
uv sync                              # install / sync deps
cp .env.example .env                 # fill values before first run
uv run fastapi dev app/main.py       # http://localhost:8000 (hot reload)
uv run pytest                        # all tests (requires SUPABASE_URL/KEY in .env)
uv run pytest tests/test_khata.py    # single test file
uv run pytest -k test_name           # single test by name
```

Tests hit a **real Supabase project** — no mocks. Tests skip automatically when `SUPABASE_URL`/`SUPABASE_KEY` are unset.

### Frontend (Next.js 16, React 19, TypeScript, Tailwind 4)

```bash
cd frontend
npm install
cp .env.example .env.local           # fill NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
npm run dev                          # http://localhost:3000
npm run build                        # production build check
npm run lint                         # ESLint
```

### Supabase migrations

```bash
supabase db push                     # apply pending migrations to remote
supabase migration new <name>        # create a new migration file
```

Migrations live in `supabase/migrations/`. All schema changes must go through migration files — never edit the DB schema directly.

## Branching

Feature branches use Conventional Branch naming (`feat/`, `fix/`, `docs/`, `chore/`) and are merged into `develop`. `main` is the production branch; `stage` is the staging branch. PRs go **against `develop`**, not `main`.

## Architecture

### Backend layers (`backend/app/`)

```
main.py          FastAPI app, CORS, router mounting
config.py        Pydantic Settings — all config from .env, no hard-coded values
auth.py          JWT validation via Supabase — extracts user_id + shop_id
db.py            Singleton Supabase service client (service-role key)
prompts.py       System prompts, MODE_HINTS, VOICE_LANGUAGE_HINT
routers/         Thin HTTP layer — validates, calls service, returns response
services/        Business logic
  llm.py         OpenAI-compatible streaming chat + structured JSON extraction
  stt.py         Speech-to-text: Speechmatics (primary) or Groq Whisper (fallback)
  voice.py       TTS pipeline: edge-tts (primary) or Azure Speech; optional Urdu transliteration
  conversations.py  Conversation/message persistence, context window management
  sale.py        Sale recording flow
  expenses.py    Expense recording flow
  khata.py       Credit ledger (udhaar / wapsi) flow
  catalog.py     Product catalog reads
  dashboard.py   Summary / dashboard data
  ledger.py      Ledger query helpers
```

**LLM**: `services/llm.py` wraps any OpenAI-compatible endpoint. The current provider (Gemini Flash, Groq, Qwen) is a config-only swap — set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` in `.env`. Provider-specific params like `reasoning_effort` are also config-driven.

**STT**: `services/stt.py` — `STT_PROVIDER=speechmatics` (default) or `groq`. Both output Urdu script; Roman-Urdu transliteration for TTS is done by an LLM call in `services/llm.to_roman_urdu()`.

**Context window**: Controlled by `LLM_MAX_CONTEXT_TURNS` (default 8). The full conversation is stored in Supabase; only the last N turns are sent to the LLM. This keeps latency flat as conversations grow.

### Conversation modes

Shopkeepers pick a mode before speaking/typing. Each mode selects a different extraction/flow on the backend:

| Mode | Urdu label | Backend behaviour |
|---|---|---|
| `sale` | Naya Sale | Structured JSON extraction → confirmation card → `record_sale` |
| `udhaar` | Udhaar | Structured JSON extraction → khata lookup or udhaar/payment record |
| `kharcha` | Kharcha | Structured JSON extraction → expense record |
| `ask` | Poocho | Conversational chat, no structured extraction |

`sale` is the only mode with a UI confirmation card before committing. The LLM extractor (`extract_sale`, `extract_expense`, `extract_udhaar` in `services/llm.py`) returns `{"action": "propose" | "clarify" | "lookup", ...}`.

### Frontend structure (`frontend/`)

```
app/
  (auth)/login, signup        Public pages
  (shop)/                     Protected shop shell (BottomNav, TenantProvider)
    app/                      Main chat/voice screen
    maal/                     Product catalog
    khata/                    Credit ledger
    hisaab/                   Expense summary
  admin/                      Admin-only dashboard
  actions/                    Next.js Server Actions (auth, sales, admin)
middleware.ts                 Route guard: unauthenticated → /login; admin → /admin; shopkeeper → /app

components/
  chat/          ChatScreen, ChatThread, ChatBubble, ChatInput, PendingIndicator
  voice/         PushToTalkButton, VoiceBar, RecordingIndicator, ReplaySpeechButton
  conversation/  ConversationScreen, ConfirmationCard, modes.ts
  dashboard/     DashboardView
  maal/          MaalView
  khata/         KhataView
  hisaab/        HisaabView
  ui/            shadcn/ui primitives (do not hand-edit)

lib/
  api.ts         Axios client for backend FastAPI calls
  chatApi.ts     Chat/voice API hooks and types (Mode type exported from here)
  types.ts       Shared TypeScript types
  tools/         Tool definitions (ToolDefinition, ToolResult, ToolContext interfaces)
    registry.ts  Interface contracts for the tool system
    record_sale.ts, adjust_product.ts, undo_sale.ts
  sales/         Supabase catalog and sales service helpers
  voice/         stt.ts, tts.ts, usePushToTalk.ts, useReplySpeech.ts hooks
  rtl.ts         RTL/Urdu text utilities

utils/supabase/
  client.ts      Browser Supabase client
  server.ts      Server-component Supabase client
  admin.ts       Service-role client (Server Actions only)

providers/
  TenantProvider.tsx  Provides shopId to the shop shell
```

### Auth and multi-tenancy

- Supabase Auth handles login/signup. Sessions are managed via `@supabase/ssr`.
- `profiles` table: one row per user, `role_name` is `shopkeeper` or `admin`. A DB trigger (`handle_new_user`) creates the profile on signup.
- All shop data is scoped by `shop_id`. The backend extracts `shop_id` from the user's JWT via `app/auth.py` + the `profiles` table.
- Middleware (`frontend/middleware.ts`) enforces role-based redirects: admins → `/admin`, shopkeepers → `/app`.

### Database

Supabase (Postgres + RLS). Key tables:
- `shops`, `profiles` — tenancy
- `conversations`, `messages` — chat history
- `products` — catalog
- `sales`, `sale_items` — sales records
- `customers`, `ledger_entries` — khata (credit) system
- `expenses`, `expense_categories` — expense tracking
- `tool_calls` — audit log of every tool invocation

Key RPCs: `record_sale`, `undo_sale`, `stock_adjustment`.

### Tool system (frontend-side)

`lib/tools/` defines tool contracts (`ToolDefinition`, `ToolResult`, `ToolContext`). Each tool implements a `handler(params, ctx)` async function. The risk tier (`commit_undo` vs `approval_required`) controls whether the UI shows a confirmation card before execution.

### Docs

`docs/` contains per-epic ticket files (AUTH-*, CATLG-*, EXP-*, SALE-*). These are the source of truth for feature specs and ERDs. Check the relevant ticket file before implementing anything in that domain.
