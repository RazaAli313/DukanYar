# SALE + CATLG MVP — Implementation Changelog

> Generated from the approved MVP plan. Covers SALE-1 through SALE-4 and CATLG-2.

---

## Database Migrations (run in order)

### 1. `supabase/migrations/20260902100000_current_shop_id.sql` (Phase 0A)

**Why:** The Phase-3 migration referenced `public.current_shop_id()` in 15 RLS policies but the function was never defined. Without this fix, any query against `products`, `customers`, `sales`, `stock_movements`, `ledger_entries`, or `expenses` fails.

**Adds:**
- `public.current_shop_id()` — SQL function that returns the `shop_id` for the currently authenticated user by looking up `profiles`.

---

### 2. `supabase/migrations/20260903000001_sale_seed_data.sql` (Phase 1A)

**Why:** SALE-1 requires a pre-seeded demo catalog so "2 coke" always resolves. No products existed in the database.

**Adds:**
- 1 demo shop: `Demo Dukan` (UUID: `00000000-0000-0000-0000-000000000001`)
- 16 products with realistic Pakistani retail pricing:

  | Product | Sale Price | Cost Price | Stock |
  |---------|-----------|------------|-------|
  | Coca-Cola 345ml | 80 | 60 | 48 |
  | Pepsi 345ml | 80 | 60 | 36 |
  | Lays Classic (family) | 150 | 110 | 30 |
  | Oreo Biscuit | 60 | 42 | 24 |
  | Nestle Water 1.5L | 100 | 70 | 60 |
  | Tapal Danedar 900g | 1400 | 1200 | 12 |
  | Olper Milk 1L | 280 | 245 | 24 |
  | Shan Biryani Masala | 90 | 65 | 18 |
  | National Ketchup 310g | 250 | 190 | 15 |
  | Dalda Oil 5L | 2800 | 2500 | 8 |
  | Surf Excel 1kg | 650 | 520 | 15 |
  | Lifebuoy Soap | 90 | 65 | 20 |
  | Jazz SIM | 100 | 80 | 10 |
  | Rooh Afza 800ml | 450 | 370 | 12 |
  | Parle-G Biscuit | 30 | 20 | 50 |
  | Sting Energy Drink | 150 | 110 | 24 |

- 37 product aliases (voice-resolution nicknames like "coke", "thanda", "chai", "doodh", "sabun", etc.)

**Idempotent:** Uses `ON CONFLICT DO NOTHING` — safe to re-run.

---

### 3. `supabase/migrations/20260903100000_sale_rpc.sql` (Phase 4A)

**Why:** The old `salesService.ts` did stock decrement in a loop of individual queries — not atomic. If one failed, earlier ones were already committed. SALE-4 requires atomicity.

**Adds:**
- `public.process_sale()` — PL/pgSQL function that in one transaction:
  1. Inserts the `sales` header row
  2. Inserts `sold_items` for each line item
  3. Inserts negative `stock_movements` for each item
  4. Decrements `products.stock` (non-blocking — allows negative)
  5. Inserts `ledger_entries` if payment type is udhaar/split
  6. Returns `{ sale_id, items, stock_flags }` where `stock_flags` lists any item that went negative

**Parameters:** `p_shop_id`, `p_items` (JSONB array), `p_total_amount`, `p_payment_type`, `p_customer_id`, `p_created_by`

---

### 4. `supabase/migrations/20260903200000_undo_sale_rpc.sql` (Phase 4C)

**Why:** SALE-4 requires the ability to undo a committed sale and restore stock.

**Adds:**
- `public.undo_sale()` — PL/pgSQL function that:
  1. Verifies the sale exists and belongs to the caller's shop
  2. For each sold item: inserts positive `stock_movements` and restores `products.stock`
  3. If the sale was udhaar: inserts a compensating `payment` ledger entry
  4. Returns `{ sale_id, undone, restored }` with per-item restoration details
  5. Does NOT delete the sale row — preserves audit trail; the `tool_calls` record is marked `undone` by the application layer

---

### 5. `supabase/migrations/20260904000000_stock_adjustment_rpc.sql` (Phase 5A)

**Why:** CATLG-2 requires atomic stock adjustments (restock, stock correction, price update).

**Adds:**
- `public.process_stock_adjustment()` — PL/pgSQL function supporting 3 adjustment types:
  - `restock_add` — `stock += value` with positive stock_movement
  - `restock_set` — `stock = value` with delta stock_movement
  - `price_update` — `sale_price = value`
- Returns `{ product_id, name, adjustment_type, old_stock, new_stock, old_price, new_price }`

---

## New Frontend Files

### 6. `frontend/src/lib/tools/registry.ts` (Phase 3A)

**Why:** TOOL-1 requires a tool registry so feature tools are additive files. The model needs schemas to call tools.

**Adds:**
- `ToolDefinition` interface — `name`, `description`, `parameters` (JSON Schema), `riskTier`, `handler`
- `ToolContext` interface — `supabase`, `shopId`, `userId`, `conversationId`, `messageId`
- `ToolResult` interface — `success`, `summary` (chat text), `data` (structured payload)
- `ToolRegistry` class — `register()`, `get()`, `all()`, `toModelSchemas()` (OpenAI-compatible function-calling format)
- Singleton `registry` export

---

### 7. `frontend/src/lib/tools/index.ts` (Phase 3A)

**Why:** Central tool list. Adding a new tool = create file + add import + register call.

**Registers:**
- `recordSaleDefinition` from `./record_sale`
- `undoSaleDefinition` from `./undo_sale`
- `adjustProductDefinition` from `./adjust_product`

---

### 8. `frontend/src/lib/tools/record_sale.ts` (Phase 4B)

**Why:** SALE-3 requires a `record_sale` tool the model can invoke.

**Tool schema (what the model fills):**
- `items[]` — `{ product_name, quantity }`
- `total_amount` — stated total (source of truth per SALE-3 primacy rule)
- `payment_type` — `cash` / `udhaar` / `split`
- `khata_number` (optional) — for udhaar customer lookup

**Handler logic:**
1. Resolves each `product_name` to a product ID via `resolveProduct()` from catalogService
2. Looks up customer by `khata_number` if udhaar
3. Calls `process_sale` RPC atomically
4. Builds chat-text summary with itemized list
5. Appends out-of-stock warnings if any item went negative (Phase 4D)
6. Returns `sale_id` in summary for undo reference

**Risk tier:** `commit_undo`

---

### 9. `frontend/src/lib/tools/undo_sale.ts` (Phase 4C)

**Why:** SALE-4 requires undoing a committed sale and restoring stock.

**Tool schema:**
- `sale_id` — UUID of the sale to undo

**Handler logic:**
1. Calls `undo_sale` RPC (restores stock, offsets ledger)
2. Finds the original `tool_calls` record and marks it `undone`
3. Returns per-item restoration summary as chat text

**Risk tier:** `commit_undo`

---

### 10. `frontend/src/lib/tools/adjust_product.ts` (Phase 5B)

**Why:** CATLG-2 — restock, correct stock count, or update price for existing products.

**Tool schema:**
- `product_name` — spoken name or alias
- `adjustment_type` — `restock_add` / `restock_set` / `price_update`
- `value` — numeric value

**Handler logic:**
1. Resolves product via catalogService (never creates new — that's CATLG-1, cut)
2. If ambiguous, returns candidate names and asks for clarification
3. Calls `process_stock_adjustment` RPC
4. Returns before/after summary as chat text (e.g., "Restocked Coke: +24 units (22 -> 46)")

**Risk tier:** `commit_undo`

---

### 11. `frontend/app/api/chat/route.ts` (Phase 3B)

**Why:** TOOL-2 requires an orchestration loop — message in, tool calls, reply out.

**API endpoint:** `POST /api/chat`

**Request body:** `{ message: string, conversationId: string }`

**Flow:**
1. Authenticates caller via Supabase auth
2. Resolves user's `shop_id` from profiles
3. Persists user message to `messages` table
4. Calls the LLM (OpenAI-compatible) with tool schemas from the registry
5. Orchestration loop (max 5 rounds):
   - If model returns text → persist as assistant message, return
   - If model returns tool calls → execute each via registry, log to `tool_calls` table, feed results back to model
6. On tool failure → reports error in reply text, never claims silent success
7. Returns `{ reply, tool_calls }`

**Required env vars (add to `.env.local`):**
- `LLM_BASE_URL` — OpenAI-compatible API base URL
- `LLM_API_KEY` — matching API key
- `LLM_MODEL` — model name (default: `gpt-4o-mini`)

---

## Modified Frontend Files

### 12. `frontend/src/lib/sales/catalogService.ts` (Phase 1B + 2A)

**Changes to `resolveProduct()`:**

| Before | After |
|--------|-------|
| Returned `ProductMatch \| null` | Returns `ResolveResult { match, candidates }` |
| Used `.limit(1)` + `.maybeSingle()` | Fetches all `ilike` matches |
| Direct name match OR alias match (two separate single-result queries) | Both queries run, results combined and deduplicated via `Set<string>` |
| No ambiguity handling | 1 match → `{ match }`, multiple → `{ candidates }`, zero → both empty |
| Alias lookup used exact `ilike('alias', term)` | Alias lookup uses `ilike('alias', '%term%')` for substring matching |

**Added:** `ResolveResult` interface

**Added:** `listProducts(supabase, shopId)` — returns all products for a shop sorted by name, so the chat assistant can answer "what's in stock?" queries.

---

### 13. `frontend/app/actions/sales.ts` (Phase 2A)

**Changes to `resolveProductAction()`:**

| Before | After |
|--------|-------|
| Imported `ProductMatch` | Imports `ResolveResult` |
| Return type: `data?: ProductMatch \| null` | Return type: `data?: ResolveResult` |

**No changes to `processSaleAction()`** — it was already wired correctly with stock alerts.

---

## File Map (visual)

```
supabase/migrations/
  20260901092045_fnd_phase1_schema.sql      (existing — foundation tables)
  20260902070905_sale_khata_exp_tool_...sql (existing — SALE/KHATA/EXP tables)
  20260902100000_current_shop_id.sql        NEW — Phase 0A
  20260903000001_sale_seed_data.sql         NEW — Phase 1A
  20260903100000_sale_rpc.sql               NEW — Phase 4A
  20260903200000_undo_sale_rpc.sql          NEW — Phase 4C
  20260904000000_stock_adjustment_rpc.sql   NEW — Phase 5A

frontend/src/lib/
  sales/
    catalogService.ts                       MODIFIED — Phase 1B + 2A
    salesService.ts                         MODIFIED — Audit fix (removed 'split')
  tools/
    registry.ts                             NEW — Phase 3A
    index.ts                                NEW — Phase 3A
    record_sale.ts                          NEW — Phase 4B
    undo_sale.ts                            NEW — Phase 4C
    adjust_product.ts                       NEW — Phase 5B

frontend/app/
  actions/
    sales.ts                                MODIFIED — Phase 2A
    auth.ts                                 (unchanged)
  api/
    chat/
      route.ts                              NEW — Phase 3B
```

---

## Critical Audit Fixes (Post-Implementation)

### Fix 1: LLM Model Provider — DashScope / Qwen

**File:** `frontend/app/api/chat/route.ts`

| Setting | Before | After |
|---------|--------|-------|
| `LLM_BASE_URL` fallback | _(none — threw if unset)_ | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` fallback | `gpt-4o-mini` | `qwen-plus` |
| Required env vars | `LLM_BASE_URL` + `LLM_API_KEY` | `LLM_API_KEY` only (base URL has sensible default) |

The orchestration loop uses the standard OpenAI-compatible `/chat/completions` endpoint, which DashScope supports natively — no code changes to the fetch logic needed.

### Fix 2: Trim Payment Type to `cash` | `udhaar` (SALE-3 Alignment)

Removed all `'split'` payment logic across 4 files:

| File | Change |
|------|--------|
| `frontend/src/lib/tools/record_sale.ts` | Schema `enum` trimmed to `['cash', 'udhaar']`; khata description updated |
| `frontend/src/lib/sales/salesService.ts` | `RecordSaleParams.payment_type` type narrowed to `'cash' \| 'udhaar'`; udhaar condition simplified from `udhaar \| split` to `udhaar` |
| `supabase/migrations/20260903100000_sale_rpc.sql` | Added `ALTER TABLE` to drop old CHECK constraint and add new `CHECK (payment_type IN ('cash', 'udhaar'))`; `process_sale()` ledger condition changed from `IN ('udhaar', 'split')` to `= 'udhaar'` |
| `supabase/migrations/20260903200000_undo_sale_rpc.sql` | `undo_sale()` ledger reversal condition changed from `IN ('udhaar', 'split')` to `= 'udhaar'` |

**Note:** The original migration (`20260902070905`) still contains `CHECK (payment_type IN ('cash', 'udhaar', 'split'))` — this is intentional. The sale_rpc migration (20260903100000) drops that constraint and replaces it with the trimmed version. Migrations run in timestamp order, so the fix applies correctly.
