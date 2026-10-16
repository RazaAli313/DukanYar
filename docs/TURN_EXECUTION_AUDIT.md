# Execution Audit Report — Current Turn

> **Scope:** All changes made during this implementation session.
> **Executed against:** Approved SALE + CATLG MVP Plan + post-plan audit directives.

---

## Files Created

| # | Path | Lines | Summary |
|---|------|-------|---------|
| 1 | `supabase/migrations/20260902100000_current_shop_id.sql` | 19 | Defines the missing `public.current_shop_id()` SQL function that 15 RLS policies in the Phase-3 migration depend on. |
| 2 | `supabase/migrations/20260903000001_sale_seed_data.sql` | 141 | Seeds a demo shop with 16 Pakistani retail products and 37 voice-resolution aliases, all idempotent via `ON CONFLICT DO NOTHING`. |
| 3 | `supabase/migrations/20260903100000_sale_rpc.sql` | 118 | Adds the atomic `process_sale()` RPC (sale + items + stock decrement + ledger in one transaction) and trims the `payment_type` CHECK constraint to `cash`/`udhaar` only. |
| 4 | `supabase/migrations/20260903200000_undo_sale_rpc.sql` | 74 | Adds the `undo_sale()` RPC that restores stock via positive movements and offsets udhaar ledger entries while preserving the sale row for audit. |
| 5 | `supabase/migrations/20260904000000_stock_adjustment_rpc.sql` | 87 | Adds the `process_stock_adjustment()` RPC supporting `restock_add`, `restock_set`, and `price_update` for CATLG-2. |
| 6 | `frontend/src/lib/tools/registry.ts` | 89 | Implements the tool registry with `ToolDefinition`, `ToolContext`, `ToolResult` types and a `ToolRegistry` class that converts tools to OpenAI-compatible function schemas. |
| 7 | `frontend/src/lib/tools/index.ts` | 16 | Central tool list that imports and registers `record_sale`, `undo_sale`, and `adjust_product` definitions. |
| 8 | `frontend/src/lib/tools/record_sale.ts` | 194 | The `record_sale` tool — resolves product names, calls `process_sale` RPC, and returns itemized chat summaries with out-of-stock warnings. |
| 9 | `frontend/src/lib/tools/undo_sale.ts` | 101 | The `undo_sale` tool — calls `undo_sale` RPC, marks the original `tool_calls` record as `'undone'`, and returns restoration summary. |
| 10 | `frontend/src/lib/tools/adjust_product.ts` | 127 | The `adjust_product` tool — resolves existing products (never creates new), calls `process_stock_adjustment` RPC, returns before/after chat text. |
| 11 | `frontend/app/api/chat/route.ts` | 292 | The `POST /api/chat` orchestration loop — authenticates caller, calls DashScope/Qwen with tool schemas, executes tool calls via registry (max 5 rounds), persists messages and tool_calls. |
| 12 | `docs/SALE_CATLG_IMPLEMENTATION.md` | 297 | Implementation changelog documenting every migration, tool, and modification with before/after tables. |
| 13 | `docs/EXECUTION_AUDIT_REPORT.md` | 169 | Full plan-adherence audit with deviation check, cut-item confirmation, and TypeScript compilation status. |

---

## Files Modified

| # | Path | Summary of Changes |
|---|------|-------------------|
| 1 | `frontend/src/lib/sales/catalogService.ts` | Rewrote `resolveProduct()` to return `ResolveResult { match, candidates }` instead of `ProductMatch \| null`; removed `.limit(1)` to fetch all `ilike` hits; deduplicates via `Set<string>`; added `listProducts(supabase, shopId)`. |
| 2 | `frontend/app/actions/sales.ts` | Updated `resolveProductAction()` return type from `ProductMatch \| null` to `ResolveResult` to match the rewritten catalog service. |
| 3 | `frontend/src/lib/sales/salesService.ts` | Narrowed `payment_type` from `'cash' \| 'udhaar' \| 'split'` to `'cash' \| 'udhaar'`; simplified udhaar ledger condition to `payment_type === 'udhaar'`. |
| 4 | `docs/SALE_CATLG_IMPLEMENTATION.md` | Appended "Critical Audit Fixes" section documenting DashScope defaults and split-payment removal across all files. |

---

## Files Deleted or Renamed

**None.** No files were deleted or renamed during this session.

---

## Summary of Logic and Config Changes

### Environment Variables

| Variable | Before | After | File |
|----------|--------|-------|------|
| `LLM_BASE_URL` default | _(unset — threw error)_ | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | `frontend/app/api/chat/route.ts` |
| `LLM_MODEL` default | `gpt-4o-mini` | `qwen-plus` | `frontend/app/api/chat/route.ts` |
| `LLM_API_KEY` | Required | Required (unchanged) | `frontend/app/api/chat/route.ts` |

### Dependencies

No new npm packages or Python packages were added. All tool logic uses existing `@supabase/supabase-js` and `@supabase/ssr` clients.

### Database Migrations

| Migration | What It Adds |
|-----------|-------------|
| `20260902100000_current_shop_id.sql` | `current_shop_id()` helper function (fixes broken RLS policies) |
| `20260903000001_sale_seed_data.sql` | 1 shop + 16 products + 37 aliases for demo |
| `20260903100000_sale_rpc.sql` | `process_sale()` atomic RPC + `payment_type` CHECK constraint narrowed to `cash`/`udhaar` |
| `20260903200000_undo_sale_rpc.sql` | `undo_sale()` atomic undo RPC |
| `20260904000000_stock_adjustment_rpc.sql` | `process_stock_adjustment()` RPC for CATLG-2 |

### Core App Logic

| Change | Impact |
|--------|--------|
| Product resolution now returns candidates instead of single match | Enables text-based ambiguity handling — when multiple products match, the orchestrator asks the shopkeeper to clarify |
| Payment type restricted to `cash` / `udhaar` only | `'split'` removed from TypeScript types, tool schemas, and all 3 PL/pgSQL functions; DB CHECK constraint updated via migration |
| Tool registry + orchestration loop added | Entire tool-calling pipeline now exists: model receives tool schemas, calls tools, results feed back into conversation — all within Next.js |
| Sale recording moved from loop-of-queries to atomic RPC | Stock decrements, sold_items inserts, and stock_movements now happen in a single database transaction — no partial commits on failure |
| Out-of-stock flags embedded in chat reply text | When any product's stock goes negative after a sale, the warning is appended directly to the model's reply string |
| LLM defaults pointed to Alibaba Cloud DashScope | Supports hackathon requirement; uses standard OpenAI-compatible endpoint so no fetch logic changes needed |

---

## Plan Adherence

| Category | Verdict |
|----------|---------|
| Unplanned deviations | **0** |
| Directed overrides (stakeholder-requested) | **2** — DashScope defaults, split removal |
| Cut items accidentally built | **0** — no CATLG-1, CATLG-3, pg_trgm, or UI cards |
| New TypeScript errors introduced | **0** |
