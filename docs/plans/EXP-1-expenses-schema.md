# Plan — EXP-1: Expenses schema & categories

**Branch:** `feat/expense-khata-module`
**Ticket:** `docs/expense/EXP-1.md` (P2) · epic `docs/expense/index.md` · stories `docs/expense/user-stories.md`
**Scope of this ticket:** database only — one additive migration. No API, no UI.
**Status:** approved with changes (2026-09-02).

---

## 1. What EXP-1 asks for (acceptance criteria)

1. After the migration runs, an `expenses` table exists with **amount, optional category, note, date**, and each expense **belongs to exactly one shop**.
2. Logging an expense **without a category** stores it as **uncategorized** (not rejected).
3. An expense **must have a positive amount**.

That is the whole ticket. Everything else (voice logging, list UI) is EXP-2 / EXP-3.

---

## 2. Context found in the repo

- **Migrations live in `supabase/migrations/`** (Supabase CLI, `config.toml` present). Convention from the two existing files: `public.` schema prefix, `uuid` PK `default gen_random_uuid()`, `timestamptz ... default now()`, RLS enabled + policies keyed on `auth.uid()` via `public.profiles`. Rule (HANDOFF.md): **one migration file per epic, additive, timestamped; never edit another epic's migration.**
- **The two FND migration timestamps are inverted** — `20260901000001_fix_fnd_phase1_schema.sql` sorts *before* `20260901092045_fnd_phase1_schema.sql` despite being the later "fix". This is why a clean `supabase db reset` is not reliable here; the hosted DB was built by applying them in intended order by hand.
- FND schema already has `shops`, `roles`, `profiles`, `conversations`, `messages`. `profiles.shop_id` is the shop-scoping anchor; `public.is_admin()` helper exists.
- **`roles`** is the precedent for a small seed/lookup table (`name TEXT PRIMARY KEY`, seeded with `INSERT`).

### Blockers that do NOT affect EXP-1 but block EXP-2/EXP-3, KHATA-2+, TEXT-3 and the UI work:

- **B1 — Dual Next.js app dir.** Auth work landed in `frontend/app/` + `frontend/utils/` + `frontend/providers/` + `frontend/middleware.ts`; the chat/voice work is in `frontend/src/app/` + `frontend/src/**` with `@/* → ./src/*`. Next.js uses root `app/` when both exist, so **the chat UI (`src/app/page.tsx`) is currently shadowed / dead.** Must consolidate to one layout (recommend: move auth into `src/`) before any UI ticket.
- **B2 — No backend Supabase client.** `backend/app/db.py` still raises `NotImplementedError`; `supabase` is not in `pyproject.toml`. Sheheryar's auth work was Next.js-only. TEXT-3 and all expense/khata **persistence from FastAPI** need either (a) a service-role Supabase client in `db.py`, or (b) DB access moved to Next.js server actions. Decision needed.
- **B3 — `backend/app/auth.py` returns a hard-coded fake user.** Shop-scoping ACs need a real `shop_id`. Options: verify the Supabase JWT in FastAPI, or have the Next.js layer pass a trusted `shop_id`.
- **B4 — EXP-2/EXP-3 & KHATA-2/3/4 depend on the TOOL epic (Phase 2), which does not exist.** "Log expense by voice" needs a tool-registry + orchestration + confirm/undo loop (TOOL-1/2/3). Realistic options for today in §5.

---

## 3. Migration (approved, essentially verbatim)

**File:** `supabase/migrations/20260902135234_exp_schema.sql` (timestamp regenerated at write time; ensure it sorts *after* the FND files)

```sql
-- EXP-1 — Expense tracking schema
-- Epic: docs/expense/ · additive, owns only expense_* tables.

-- Canonical default expense categories (lookup table, mirrors public.roles).
-- 'uncategorized' is the fallback when a shopkeeper names no category.
create table public.expense_categories (
    name text primary key
);

insert into public.expense_categories (name) values
    ('uncategorized'),
    ('utilities'),      -- bijli, gas, paani, phone
    ('rent'),
    ('supplies'),       -- shop consumables, packaging
    ('salaries'),
    ('transport'),
    ('maintenance'),
    ('other')
on conflict (name) do nothing;

create table public.expenses (
    id          uuid primary key default gen_random_uuid(),
    shop_id     uuid not null references public.shops(id) on delete cascade,
    amount      numeric(12,2) not null check (amount > 0),
    category    text not null default 'uncategorized'
                    references public.expense_categories(name) on delete set default,
    note        text,
    spent_on    date not null default current_date,
    created_at  timestamptz not null default now()
);

create index expenses_shop_spent_on_idx
    on public.expenses (shop_id, spent_on desc);

-- RLS — mirror the conversations/messages policy shape.
alter table public.expense_categories enable row level security;
alter table public.expenses           enable row level security;

create policy "Anyone authenticated can read expense categories"
    on public.expense_categories for select to authenticated using (true);

create policy "Shopkeepers or Admins can access their shop expenses"
    on public.expenses for all
    using (
        shop_id in (select shop_id from public.profiles where id = auth.uid())
        or public.is_admin()
    )
    with check (
        shop_id in (select shop_id from public.profiles where id = auth.uid())
        or public.is_admin()
    );
```

### Locked decisions

| Choice | Decision | Rationale |
| --- | --- | --- |
| `category` model | **seed lookup table** (`expense_categories`), FK from `expenses.category` | ERD-canonical; 8 categories map cleanly to EXP-2's "bijli → utilities" inference |
| default categories | `uncategorized, utilities, rent, supplies, salaries, transport, maintenance, other` | confirmed |
| `amount` | **`numeric(12,2)` rupees** | matches repo's numeric usage; avoids paisa-math churn in a hackathon |
| `category NOT NULL DEFAULT 'uncategorized'` | keep | AC2 — never reject |
| `spent_on date DEFAULT current_date` | keep | AC1; day-grained |
| separate `created_at timestamptz` | keep | audit + "most recent first" tiebreak in EXP-3 |
| `on delete set default` on category FK | keep | deleting a category must not delete expenses |
| RLS `with check` + `using` | keep | block inserting rows for another shop |

---

## 4. Steps for EXP-1

1. Write `supabase/migrations/20260902135234_exp_schema.sql` as above (regenerate the timestamp so it sorts after both FND files).
2. **Apply to the hosted Supabase project via the SQL editor** (not `supabase db reset` — the FND timestamp inversion makes a clean reset unreliable). Need the project SQL-editor access or a connection string — see Q3.
3. Verify **against the hosted DB** after applying:
   - `insert into expenses (shop_id, amount) values ('<real shop_id>', 500);` → row has `category = 'uncategorized'`, `spent_on = today`.
   - `insert ... (amount) values (0)` and `(-10)` → both rejected by the CHECK.
   - as a normal (non-admin) user context, insert with a foreign `shop_id` → rejected by RLS.
   - confirm the FND tables/policies are untouched.
4. Commit: `feat(exp): expenses schema & default categories (EXP-1)` — plain message, no trailer.
5. **Write a new handoff note** `docs/expense-khata-handoff.md` (do **not** edit `docs/HANDOFF.md`, which is the text/voice module's) recording: migration filename + what it adds, the hosted-apply requirement, and the FND timestamp-inversion gotcha.
6. Update `docs/expense/index.md` — EXP-1 status → Done.
7. **Message Sheheryar:** new epic migration added under `supabase/migrations/`; must be applied to the hosted project (SQL editor), not via reset; and flag the existing FND timestamp inversion so future migrations are ordered/applied deliberately.
8. No PR yet unless you want a draft — see Q4.

**Definition of done:** migration applied to the hosted DB; the three ACs demonstrably hold; FND schema unaffected; handoff note + `index.md` updated; Sheheryar notified.

---

## 5. Today's sequencing (after EXP-1)

Given the TOOL-epic dependency, a realistic order that still demos:

- **A. EXP-1** (this plan) — schema. ~30 min, no blockers.
- **B. KHATA-1** — `customers` table (khata# unique per shop, CNIC, name) + **typed registration**. Depends only on FND-2/AUTH-3, buildable today; needs B1/B2/B3 decisions if it touches FastAPI or the frontend.
- **C. Resolve B1** (consolidate frontend dirs) — unblocks the UI refresh + all list screens.
- **D. TEXT-3** — needs B2 (backend Supabase client). First real use of `db.py`.
- **E. EXP-3 / KHATA-4 read-only list & lookup** — direct REST endpoints, no TOOL loop.
- **F. EXP-2 / KHATA-2/3** — need a minimal TOOL-1/2/3. Biggest chunk; may slip past today.
- **G. Voice provider spike** (ElevenLabs vs UpliftAI) — independent, run any time.

**This is more than one day.** Suggested firm goal for today: **EXP-1 + KHATA-1 + B1**; rest as stretch.

---

## 6. Voice spike — the two options

**Option 1 — throwaway comparison scripts (recommended first).** Standalone scripts under `spike/`, not wired into the app. One fixed Roman-Urdu/Urdu clip + one reply-text string through each provider's STT and TTS. Capture per provider: latency (cold/warm), transcript accuracy vs a hand transcript, TTS naturalness, Urdu/Roman-Urdu handling, free-tier limits, price. Output a comparison table. ~1–2 h, zero risk.

**Option 2 — wire behind the existing adapters.** `stt.py` / `voice.py` already switch on `STT_PROVIDER` / `TTS_PROVIDER`. Add `elevenlabs` / `upliftai` branches, A/B in the real flow. More realistic, ~half a day, touches shipped code.

**Recommendation:** Option 1 today to pick a winner, then a small follow-up to wire only the winner.

---

## 7. Open questions (your call — not answerable from the repo)

4. **PR cadence** — one PR per ticket to `develop`, or one bundled `feat/expense-khata-module` PR at the end? (Only documented constraint: PRs target `develop`.)
5. **Today's committed scope** — agree to EXP-1 + KHATA-1 + frontend-dir consolidation as the firm goal?
6. **Voice spike** — Option 1 as its own task? Confirm providers/endpoints (ElevenLabs Scribe STT + TTS; UpliftAI which endpoints?) and whether you have API keys for both.
