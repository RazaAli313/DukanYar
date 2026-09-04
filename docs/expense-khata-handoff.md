# Expense + Khata module — handoff / progress

**Owner:** Usman (Muhammad Usman Tariq)
**Branch:** `feat/expense-khata-module` → PR against `develop` (Raza reviews & merges)
**Scope:** EXP epic (`docs/expense/`, EXP-1..3) + KHATA epic (`docs/khata/`, KHATA-1..4).
Read each ticket's `.md` + `user-stories.md` + `index.md` before starting it.

This is a **separate note from `docs/HANDOFF.md`**, which belongs to the TEXT/VOICE module.

---

## Project context (short)

DukanYar = voice-first, multimodal Urdu AI assistant for small Pakistani retail
shopkeepers. Alibaba Cloud AI Hackathon 2026 (one week).

- **Stack:** Next.js (frontend, Vercel later) + FastAPI (backend, `uv`, Render later) + Supabase (hosted Postgres + Auth + RLS).
- EXP and KHATA are **Phase 3** feature epics — they normally sit on top of the
  **TOOL epic (Phase 2)** which is *not built yet*.

---

## Migration convention (IMPORTANT — read before adding SQL)

- Migrations live in `supabase/migrations/`, `<timestamp>_<name>.sql`, **one file per epic, additive**. Never edit another epic's migration.
- **The two FND migration timestamps are inverted:**
  `20260901000001_fix_fnd_phase1_schema.sql` sorts *before*
  `20260901092045_fnd_phase1_schema.sql` even though the "fix" must run *after* the base.
  → A clean `supabase db reset` will run them in the wrong order and fail.
- **Apply migrations to the hosted Supabase project directly** — via the dashboard
  **SQL Editor** (paste + Run), or `supabase db push` (only sends migrations not yet
  recorded on the remote, so the FND inversion doesn't bite). Do **not** rely on `db reset`.
- Access: Supabase project is owned by Sheheryar; Usman has **Developer** role
  (SQL Editor access). DB password / connection string not held by Usman.

---

## EXP-1 — Expenses schema (DONE by Sheheryar, NOT in repo — 2026-09-02)

Sheheryar built the expense schema **directly in the hosted Supabase dashboard**.
There is **no migration file for it in `supabase/migrations/`** — this is drift and
must be fixed (ask Sheheryar to commit his SQL).

### Actual schema in the hosted DB

`public.expense_categories`
- `id` uuid PK `gen_random_uuid()`
- `name` text
- **Seeded with ONE row only:** `Uncategorized` (`bd09cba8-b474-4742-9f28-78be666ca984`)

`public.expenses`
- `id` uuid PK `gen_random_uuid()`
- `shop_id` uuid NOT NULL → `shops(id)` ON DELETE CASCADE
- `category_id` uuid **NULL** → `expense_categories(id)` (NULL = uncategorized)
- `amount` numeric NOT NULL, `CHECK (amount > 0)`
- `note` text NULL
- `expense_date` date NOT NULL DEFAULT `CURRENT_DATE`
- `created_by` uuid NULL → `profiles(id)` ON DELETE SET NULL
- `created_at` timestamptz NOT NULL `now()`

RLS policies (depend on a `public.current_shop_id()` helper Sheheryar added):
- `expense_categories` SELECT — `auth.role() = 'authenticated'`
- `expenses` INSERT — WITH CHECK `shop_id = current_shop_id()`
- `expenses` SELECT — `is_admin() OR shop_id = current_shop_id()`
- `expenses` DELETE — `shop_id = current_shop_id()`
- **no UPDATE policy** (EXP-3 only lists + deletes — acceptable)

### Gaps / follow-ups

1. **Drift:** Sheheryar's full phase-3 SQL is now committed as
   `supabase/migrations/20260902070905_sale_khata_exp_tool_admin_rpt.sql` (he ran it
   in the dashboard first). Still open: confirm `public.current_shop_id()` lives in a
   committed migration — it is referenced by every RLS policy but wasn't in the FND files.
2. **Categories seeded** — `20260902171955_seed_expense_categories.sql` adds
   `Utilities, Rent, Supplies, Salaries, Transport, Maintenance, Other` (applied to the
   hosted DB). `Uncategorized` was already there.

## EXP-2 / EXP-3 data layer — DONE (routing-independent, 2026-09-02)

`backend/app/services/expenses.py` — no HTTP/tool/UI, just rows:

- `resolve_category(name)` — exact name match → Roman-Urdu/English keyword map
  (`bijli/gas/paani → Utilities`, `kiraya → Rent`, `tankhwah → Salaries`, ...) →
  `Uncategorized` fallback.
- `create_expense(*, shop_id, amount, category=None, note=None, expense_date=None,
  created_by=None)` — rejects non-positive / non-numeric amount (`ExpenseError`),
  resolves category, inserts, returns the row with the category **name**.
- `get_expense`, `list_expenses(*, shop_id, limit=20)` (most-recent-first),
  `delete_expense(*, shop_id, expense_id)` (the EXP-2 undo **and** EXP-3 delete —
  same op, shop-scoped so another shop can't touch it).

Backend uses the service_role key → RLS bypassed → **every function takes `shop_id`
and scopes the query itself**.

Tests: `backend/tests/test_expenses.py` — 16 cases against the real Supabase project
(throwaway shop per test, CASCADE cleanup). `uv run pytest`.

**Still out of scope** (waiting on the block-vs-free-form decision): HTTP endpoint,
voice/text → fields parsing, frontend, `tool_calls` rows, orchestration, EXP-2 AC3
(missing-amount clarification — that's orchestration-layer).

### Note — column name

The real column is **`expense_date`** (not `spent_on` as an earlier draft plan had it).
RLS uses `current_shop_id()`.

### AC status

- AC1 (table w/ amount, optional category, note, date; shop-scoped) — met.
- AC2 (missing category → uncategorized, not rejected) — met via nullable `category_id`.
  "sensible default categories exist" — only partly (one row).
- AC3 (positive amount) — met by `CHECK (amount > 0)`.

---

## Blockers for later tickets (not EXP-1)

- **B1 — Dual Next.js app dir.** `frontend/app/` (auth) shadows `frontend/src/app/`
  (chat/voice, `@/*`→`src/*`). Chat UI currently dead. Consolidate before any UI ticket.
- **B2 — No backend Supabase client.** `backend/app/db.py` still `NotImplementedError`;
  `supabase` not in `pyproject.toml`. Needed for TEXT-3 + expense/khata persistence
  from FastAPI (service-role client) — or route DB via Next.js server actions.
- **B3 — `backend/app/auth.py` returns a hard-coded fake user.** Real `shop_id` needed
  for shop-scoping — verify Supabase JWT in FastAPI, or have Next.js pass a trusted `shop_id`.
- **B4 — EXP-2/EXP-3 & KHATA-2/3/4 depend on the TOOL epic (Phase 2)**, which doesn't
  exist. "Log by voice" needs tool-registry + orchestration + confirm/undo.

---

## KHATA-1..4 data layer — DONE (routing-independent, 2026-09-02)

`backend/app/services/khata.py` — customers + ledger, no HTTP/tool/UI.

- `normalize_cnic(cnic)` — strips formatting, must be 13 digits (`KhataError` otherwise).
- `register_customer(*, shop_id, name, cnic, created_by=None)` — DB trigger assigns the
  per-shop running `khata_number`; blank name / bad CNIC → `KhataError`; CNIC already in
  this shop → `DuplicateCustomerError` (carries the existing row). One retry on a
  `khata_number` race.
- `find_customer(*, shop_id, khata_number=None, cnic=None)` — khata# first, else CNIC
  fallback, else `KhataError`. Shop-scoped. `None` if absent.
- `customer_balance(*, shop_id, customer_id)` — `Σ udhaar − Σ payment` over
  `ledger_entries`. Read-only. Partial repayment falls out naturally; overpay → negative.
- `list_customers(*, shop_id, limit=50)` — customers + balance, newest khata# first.
- `log_udhaar(*, shop_id, customer_id, amount, sale_id=None, created_by=None)` and
  `record_payment(*, shop_id, customer_id, amount, created_by=None)` — insert a
  `udhaar` / `payment` ledger row, return `{"entry": ..., "balance": <new>}`. Both
  reject non-positive amounts **and** verify the customer belongs to `shop_id` before
  inserting (`_assert_customer_in_shop`).
- `reverse_ledger_entry(*, shop_id, entry_id)` — the KHATA-2 undo; shop-scoped delete.

**KHATA-3 approval gate is NOT here** — `record_payment` is the post-approval action;
`pending_approval` → approve/reject lives in TOOL-3 / orchestration.

Cash vs credit (confirmed against SALE epic): a **cash sale records no customer** and
never calls this module. Only a khata#-present (credit) sale creates a `ledger_entries`
`udhaar` row, linked via `sale_id`. `log_udhaar` also works standalone (no `sale_id`).

Tests: `backend/tests/test_khata.py` — 21 cases against the real project. `uv run pytest`
(58 total with the expense suite).

## NEXT

- Resolve **B1** (frontend dual-dir), then the block-vs-free-form decision, then wire
  the EXP + KHATA data layers to endpoints + UI.
- **TEXT-3** (needs B2 ✅ done) — message persistence; prerequisite for `tool_calls`
  and the free-form orchestration path.
- Minimal TOOL layer (or block endpoints) for EXP-2 / KHATA-2/3 / SALE-3.
- **Ask Sheheryar:** confirm `public.current_shop_id()` is in a committed migration.
