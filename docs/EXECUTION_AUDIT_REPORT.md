# SALE + CATLG MVP — Execution Audit Report

> **Date:** September 2, 2026
> **Executed against:** Approved MVP Implementation Plan (SALE_and_CATLG_Implementation)
> **Scope:** SALE-1, SALE-2, SALE-3, SALE-4, CATLG-2

---

## 1. Plan Adherence — Deviation Check

| Plan Requirement | Status | Deviation? |
|-----------------|--------|------------|
| No dedicated sales/catalog UI — all output via chat text | Followed | **No** |
| No separate Python/FastAPI backend | Followed | **No** — all logic lives in Next.js server actions / API routes |
| Phase 0A: `current_shop_id()` migration | Followed | **No** |
| Phase 1A: ~16 products + aliases seed data | Followed | **No** — exactly 16 products, 37 aliases |
| Phase 1B: `listProducts()` in catalogService | Followed | **No** |
| Phase 2A: Fix `resolveProduct()` — return `ResolveResult` with `match`/`candidates` | Followed | **No** |
| Phase 2A: Remove `.limit(1)` — fetch all matches | Followed | **No** |
| Phase 2A: Skip `pg_trgm` — use `ilike` only | Followed | **No** |
| Phase 2B: Text-based ambiguity handling | Followed | **No** |
| Phase 3A: Minimal tool registry (`registry.ts` + `index.ts`) | Followed | **No** |
| Phase 3B: Orchestration loop as Next.js API route | Followed | **No** |
| Phase 4A: Atomic `process_sale` RPC | Followed | **No** |
| Phase 4B: `record_sale` tool with product resolution | Followed | **No** |
| Phase 4C: `undo_sale` RPC + tool | Followed | **No** |
| Phase 4D: Out-of-stock flags in chat reply text | Followed | **No** — embedded in `record_sale` summary |
| Phase 5A: `process_stock_adjustment` RPC | Followed | **No** |
| Phase 5B: `adjust_product` tool (stretch) | Followed | **No** |
| CATLG-1 (add product by voice) — cut | Followed | **No** — not implemented |
| CATLG-3 (proactive low-stock alerts) — cut | Followed | **No** — not implemented |
| `pg_trgm` extension — cut | Followed | **No** — not added |
| UI card components — cut | Followed | **No** — no `.tsx` components created |
| Stated total primacy (SALE-3) | Followed | **No** — `total_amount` passed through as-is to RPC |
| Non-blocking negative inventory (SALE-4) | Followed | **No** — stock can go negative, flagged in `stock_flags` |
| Relative imports in frontend | Followed | **No** — all imports use `../../` paths |

**Post-plan audit fixes applied (per stakeholder instruction):**

| Fix | Description | Deviation from original plan? |
|-----|-------------|-------------------------------|
| LLM provider switch | Changed default model from `gpt-4o-mini` to `qwen-plus`, base URL to DashScope | **Directed override** — stakeholder explicitly requested Alibaba Cloud DashScope for hackathon |
| Payment type trim | Removed `'split'` from all schemas, RPCs, tools, and services | **Directed override** — stakeholder explicitly requested cash/udhaar only per SALE-3 |

**Verdict: Zero unplanned deviations. Two directed overrides applied per stakeholder instruction.**

---

## 2. Files Created (11 new files)

### Database Migrations (5 files)

| # | File | Phase | Lines | What It Adds |
|---|------|-------|-------|-------------|
| 1 | `supabase/migrations/20260902100000_current_shop_id.sql` | 0A | 19 | `public.current_shop_id()` — SQL function returning `profiles.shop_id` for `auth.uid()`. Required by 15 RLS policies in the Phase-3 migration that referenced it but never defined it. |
| 2 | `supabase/migrations/20260903000001_sale_seed_data.sql` | 1A | 141 | Demo shop `Demo Dukan` (UUID `00000000-...-0001`), 16 Pakistani retail products (Coca-Cola, Pepsi, Lays, Tapal, Olper, Shan, Dalda, etc.) with `sale_price`/`cost_price`/`stock`, and 37 voice-resolution aliases (coke, thanda, chai, doodh, sabun, etc.). All idempotent with `ON CONFLICT DO NOTHING`. |
| 3 | `supabase/migrations/20260903100000_sale_rpc.sql` | 4A | 118 | `public.process_sale()` — atomic PL/pgSQL function: inserts `sales` header, `sold_items` per line, negative `stock_movements`, decrements `products.stock` (non-blocking, allows negative), inserts `ledger_entries` for udhaar. Returns `{ sale_id, items, stock_flags }`. Also drops and re-adds the `payment_type` CHECK constraint to trim to `cash`/`udhaar` only. |
| 4 | `supabase/migrations/20260903200000_undo_sale_rpc.sql` | 4C | 74 | `public.undo_sale()` — restores product stock via positive `stock_movements`, adds compensating `payment` ledger entry if udhaar, preserves sale row for audit trail. Returns `{ sale_id, undone, restored }`. |
| 5 | `supabase/migrations/20260904000000_stock_adjustment_rpc.sql` | 5A | 87 | `public.process_stock_adjustment()` — supports `restock_add` (stock += value), `restock_set` (stock = value), and `price_update` (sale_price = value). Returns before/after state. |

### Frontend Tool System (5 files)

| # | File | Phase | Lines | What It Adds |
|---|------|-------|-------|-------------|
| 6 | `frontend/src/lib/tools/registry.ts` | 3A | 89 | `ToolDefinition`, `ToolContext`, `ToolResult` interfaces. `ToolRegistry` class with `register()`, `get()`, `all()`, `toModelSchemas()` (converts to OpenAI-compatible function-calling format). Singleton `registry` export. |
| 7 | `frontend/src/lib/tools/index.ts` | 3A | 16 | Central tool list — imports and registers `recordSaleDefinition`, `undoSaleDefinition`, `adjustProductDefinition`. Adding a new tool = one import + one `register()` call. |
| 8 | `frontend/src/lib/tools/record_sale.ts` | 4B | 194 | `record_sale` tool. Resolves each `product_name` via `catalogService.resolveProduct()`, looks up customer by `khata_number` for udhaar, calls `process_sale` RPC, builds itemized chat summary with out-of-stock warnings appended. Risk tier: `commit_undo`. |
| 9 | `frontend/src/lib/tools/undo_sale.ts` | 4C | 101 | `undo_sale` tool. Calls `undo_sale` RPC, finds and marks the original `tool_calls` record as `'undone'`, returns per-item restoration summary as chat text. Risk tier: `commit_undo`. |
| 10 | `frontend/src/lib/tools/adjust_product.ts` | 5B | 127 | `adjust_product` tool. Resolves existing product (never creates new — CATLG-1 is cut), calls `process_stock_adjustment` RPC, returns before/after summary. Handles ambiguous matches by returning candidate names. Risk tier: `commit_undo`. |

### Frontend API Route (1 file)

| # | File | Phase | Lines | What It Adds |
|---|------|-------|-------|-------------|
| 11 | `frontend/app/api/chat/route.ts` | 3B | 292 | `POST /api/chat` — full orchestration loop. Authenticates caller, resolves `shop_id`, persists user message, calls DashScope Qwen (or configured LLM) with tool schemas, loops up to 5 rounds executing tool calls via registry, persists assistant reply, logs all tool calls to `tool_calls` table, reports failures in reply text. Defaults: `qwen-plus` model, DashScope international endpoint. |

---

## 3. Files Modified (3 files)

| # | File | Phase | What Changed |
|---|------|-------|-------------|
| 1 | `frontend/src/lib/sales/catalogService.ts` | 1B + 2A | **`resolveProduct()`** completely rewritten: return type changed from `Promise<ProductMatch \| null>` to `Promise<ResolveResult>`. Removed `.limit(1)` — now fetches all `ilike` matches for both direct name and alias lookups. Deduplicates via `Set<string>`. Returns `{ match }` for single hit, `{ candidates }` for ambiguity, both empty for no match. Alias search changed from exact `ilike('alias', term)` to substring `ilike('alias', '%term%')`. Added `ResolveResult` interface. Added `listProducts(supabase, shopId)` returning all products sorted by name. |
| 2 | `frontend/app/actions/sales.ts` | 2A | **`resolveProductAction()`** updated: import changed from `ProductMatch` to `ResolveResult`, return type changed from `data?: ProductMatch \| null` to `data?: ResolveResult`. `processSaleAction()` unchanged. |
| 3 | `frontend/src/lib/sales/salesService.ts` | Audit fix | `RecordSaleParams.payment_type` narrowed from `'cash' \| 'udhaar' \| 'split'` to `'cash' \| 'udhaar'`. Udhaar ledger condition simplified from `(payment_type === 'udhaar' \|\| payment_type === 'split')` to `payment_type === 'udhaar'`. |

---

## 4. What Was NOT Built (Per Plan — Cut Items)

| Cut Item | Reason (from plan) | Confirmed not built? |
|----------|-------------------|---------------------|
| Separate Python/FastAPI backend (`db.py`, `auth.py`, `pyproject.toml`) | Duplicates existing Next.js Supabase wiring | **Yes — not touched** |
| Catalog list page (`/app/catalog/page.tsx`) | No dedicated UI per project scope | **Yes — not created** |
| `ProductMatchCard.tsx` | Chat text only | **Yes — not created** |
| `SaleConfirmationCard.tsx` | Chat text only | **Yes — not created** |
| `AdjustConfirmationCard.tsx` | Chat text only | **Yes — not created** |
| `AddProductCard.tsx` | CATLG-1 cut | **Yes — not created** |
| `LowStockAlerts.tsx` | CATLG-3 cut | **Yes — not created** |
| `pg_trgm` trigram extension | Overkill for 16-product demo | **Yes — not added** |
| CATLG-1 — Add product by voice | Roadmap; seed data covers demo | **Yes — not implemented** |
| CATLG-3 — Proactive low-stock alerts | P3 roadmap, "build last" | **Yes — not implemented** |
| Backend catalog REST endpoints | Frontend queries Supabase directly | **Yes — not created** |

---

## 5. TypeScript Compilation Status

```
$ tsc --noEmit

Found 4 errors in 3 files.
```

All 4 errors are **pre-existing** and unrelated to SALE/CATLG work:

| File | Error | Cause |
|------|-------|-------|
| `app/(auth)/login/page.tsx` | `'signIn'` not exported from `auth.ts` | Pre-existing — auth actions file only exports `signUpAction` |
| `app/(auth)/signup/page.tsx` | `'signUp'` not exported from `auth.ts` | Pre-existing — same |
| `app/app/page.tsx` | `'getUserProfile'` not exported | Pre-existing — same |
| `app/app/page.tsx` | `'signOut'` not exported | Pre-existing — same |

**Zero errors in any SALE/CATLG file.**

---

## 6. Environment Variables

The chat orchestration route (`/api/chat`) requires these in `.env.local`:

| Variable | Required? | Default |
|----------|-----------|---------|
| `LLM_API_KEY` | **Yes** | _(none — throws if unset)_ |
| `LLM_BASE_URL` | No | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | No | `qwen-plus` |

---

## 7. Migration Execution Order

Migrations must be pushed in timestamp order:

```
1. 20260902100000_current_shop_id.sql      — fix missing RLS helper
2. 20260903000001_sale_seed_data.sql       — seed demo catalog
3. 20260903100000_sale_rpc.sql             — atomic sale + CHECK constraint fix
4. 20260903200000_undo_sale_rpc.sql        — atomic undo
5. 20260904000000_stock_adjustment_rpc.sql — CATLG-2 adjustments
```

---

## 8. Total Output

| Metric | Count |
|--------|-------|
| New files created | 11 |
| Files modified | 3 |
| Database migrations | 5 |
| TypeScript tool definitions | 3 (`record_sale`, `undo_sale`, `adjust_product`) |
| Database RPC functions | 3 (`process_sale`, `undo_sale`, `process_stock_adjustment`) |
| Database helper functions | 1 (`current_shop_id`) |
| Seed products | 16 |
| Seed aliases | 37 |
| Lines of new code | ~1,260 |
| Pre-existing TS errors (not ours) | 4 |
| New TS errors introduced | 0 |
| Unplanned deviations from plan | 0 |
