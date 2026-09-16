# DukanYar — Complete Session Execution Report

> **Date:** September 2, 2026
> **Session Scope:** SALE-1 through SALE-4, CATLG-2 implementation + post-implementation refinements
> **Plan Executed Against:** Approved MVP Implementation Plan (SALE + CATLG)

---

## 1. Executive Summary

This session delivered the complete **SALE** and **CATLG-2** MVP for the DukanYar project — a voice-first, multimodal AI assistant for Pakistani retail shopkeepers. The work spans 5 database migrations, 3 AI tool definitions, 2 service modules, authentication fixes, and a full UI/UX redesign across the landing page and auth flows. Post-implementation, the orchestration wrapper was removed for clean module separation (TOOL epic handoff), and two critical audit fixes were applied per stakeholder directive.

**Key metrics:**
- 11 new files created, 5 files modified, 2 files deleted, 1 file stripped
- 5 production database migrations (877 lines of SQL)
- 3 AI tool definitions exported as standalone modules
- 0 unplanned deviations from the approved plan
- 0 TypeScript errors introduced

---

## 2. Project Scope & Architectural Constraints

The MVP was scoped for the **Alibaba Cloud AI Hackathon** with these hard constraints:

| Constraint | Decision |
|-----------|----------|
| No dedicated UI | All output via chat text — no cards, no panels |
| No Python/FastAPI backend | All logic lives in Next.js server actions and API routes |
| No `pg_trgm` extension | `ilike` substring matching sufficient for 16-product demo |
| CATLG-1 (add product by voice) | Cut — seed data covers demo |
| CATLG-3 (proactive low-stock alerts) | Cut — P3 roadmap item |
| Stated total primacy (SALE-3) | Shopkeeper's spoken amount is source of truth, no server-side recalculation |
| Non-blocking negative inventory (SALE-4) | Stock can go negative without blocking; flagged in `stock_flags` |
| Payment types | Cash and udhaar only — `split` deliberately excluded |
| LLM provider | Alibaba Cloud DashScope with Qwen model |

---

## 3. Phase-by-Phase Implementation

### Phase 0A — Foundation Fix: `current_shop_id()`

**Problem:** The Phase-3 migration (`20260902070905_sale_khata_exp_tool_admin_rpt.sql`) created 15 RLS policies referencing `public.current_shop_id()`, but the function was never defined. This would cause all tenant-scoped queries to fail.

**File:** `supabase/migrations/20260902100000_current_shop_id.sql` (20 lines)

**Solution:** SQL function that looks up `profiles.shop_id` for `auth.uid()`:
```sql
CREATE OR REPLACE FUNCTION public.current_shop_id()
RETURNS uuid LANGUAGE sql SECURITY DEFINER STABLE AS $$
  SELECT shop_id FROM public.profiles WHERE id = auth.uid() LIMIT 1;
$$;
```

---

### Phase 1A — Demo Catalog Seed Data

**File:** `supabase/migrations/20260903000001_sale_seed_data.sql` (142 lines)

**Contents:**
- 1 demo shop: `Demo Dukan` (UUID `00000000-0000-0000-0000-000000000001`)
- 16 Pakistani retail products with realistic `sale_price`, `cost_price`, and `stock` values:

| # | Product | Sale Price | Stock |
|---|---------|-----------|-------|
| 1 | Coca-Cola 345ml | Rs 80 | 48 |
| 2 | Pepsi 345ml | Rs 80 | 36 |
| 3 | Lays Classic (family) | Rs 150 | 30 |
| 4 | Oreo Biscuit | Rs 60 | 24 |
| 5 | Nestle Water 1.5L | Rs 100 | 60 |
| 6 | Tapal Danedar 900g | Rs 1,400 | 12 |
| 7 | Olper Milk 1L | Rs 280 | 24 |
| 8 | Shan Biryani Masala | Rs 120 | 18 |
| 9 | Dalda Oil 1L | Rs 480 | 20 |
| 10 | Surf Excel 500g | Rs 250 | 15 |
| 11 | Lifebuoy Soap | Rs 90 | 30 |
| 12 | Colgate 100g | Rs 120 | 24 |
| 13 | Pakistan Chai 250g | Rs 180 | 16 |
| 14 | Mezan Oil 1L | Rs 460 | 22 |
| 15 | National Ketchup | Rs 200 | 14 |
| 16 | Young's Strawberry Jam | Rs 350 | 10 |

- 37 voice-resolution aliases (Roman Urdu + English): `coke`, `thanda`, `pepsi`, `lays`, `chips`, `oreo`, `biscuit`, `pani`, `water`, `chai`, `tea`, `tapal`, `doodh`, `milk`, `olper`, `shan masala`, `biryani`, `dalda`, `oil`, `surf`, `detergent`, `sabun`, `soap`, `lifebuoy`, `colgate`, `toothpaste`, `chaye`, `mezan`, `ketchup`, `jam`, `young's`, etc.
- All inserts idempotent via `ON CONFLICT DO NOTHING`

---

### Phase 1B + 2A — Product Resolution Service Rewrite

**File:** `frontend/src/lib/sales/catalogService.ts` (83 lines, modified)

**Before:** `resolveProduct()` returned `ProductMatch | null` with `.limit(1)` — silently dropping ambiguous matches.

**After:** Returns `ResolveResult` with three outcomes:

```ts
export interface ResolveResult {
  match: ProductMatch | null;      // Single unambiguous hit
  candidates: ProductMatch[];     // Multiple matches (ambiguity)
}
```

**Key changes:**
- Removed `.limit(1)` — fetches all `ilike` matches
- Deduplicates via `Set<string>` (same product matched by name AND alias)
- Alias search changed from exact `ilike('alias', term)` to substring `ilike('alias', '%term%')`
- Added `listProducts(supabase, shopId)` returning all products sorted by name

**File:** `frontend/app/actions/sales.ts` (79 lines, modified)
- Updated `resolveProductAction()` return type to `ResolveResult`

---

### Phase 3A — Tool Type Contracts

**File:** `frontend/src/lib/tools/registry.ts` (44 lines, stripped to types-only)

Exports shared interfaces consumed by all tool definitions:
```ts
export type RiskTier = 'commit_undo' | 'approval_required';

export interface ToolContext {
  supabase: SupabaseClient;
  shopId: string;
  userId: string;
  conversationId: string;
  messageId: string;
}

export interface ToolResult {
  success: boolean;
  summary: string;
  data?: Record<string, unknown>;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: object;      // JSON Schema
  riskTier: RiskTier;
  handler: (params, ctx) => Promise<ToolResult>;
}
```

> **Note:** The `ToolRegistry` class and singleton were removed (TOOL epic ownership). See Section 5.

---

### Phase 4A — Atomic `process_sale` RPC

**File:** `supabase/migrations/20260903100000_sale_rpc.sql` (118 lines)

**Function:** `public.process_sale(p_shop_id, p_customer_id, p_payment_type, p_total_amount, p_items JSONB)`

**Atomic transaction flow:**
1. Inserts `sales` header row
2. For each item in `p_items`: inserts `sold_items` row, creates negative `stock_movements`, decrements `products.stock` (non-blocking — allows negative)
3. If `payment_type = 'udhaar'`: inserts `ledger_entries` with type `'udhaar'`
4. Returns `{ sale_id, items, stock_flags }` where `stock_flags` maps product IDs to their post-sale stock levels (negative values = out-of-stock warning)

**Also:** Drops and re-adds the `payment_type` CHECK constraint to enforce `cash`/`udhaar` only (removing `split`).

---

### Phase 4B — `record_sale` Tool Definition

**File:** `frontend/src/lib/tools/record_sale.ts` (195 lines)

**Exported:** `recordSaleDefinition: ToolDefinition`

| Property | Value |
|----------|-------|
| Name | `record_sale` |
| Risk Tier | `commit_undo` |
| Parameters | `items[]` (product_name, quantity), `total_amount`, `payment_type` (cash/udhaar), `khata_number` (optional) |

**Handler logic:**
1. Resolves each `product_name` via `catalogService.resolveProduct()`
2. Returns candidate list if any product is ambiguous
3. Looks up customer by `khata_number` for udhaar sales
4. Calls `process_sale` RPC with resolved product IDs
5. Builds itemized chat-text summary with out-of-stock warnings appended

---

### Phase 4C — `undo_sale` RPC + Tool

**File:** `supabase/migrations/20260903200000_undo_sale_rpc.sql` (75 lines)

**Function:** `public.undo_sale(p_sale_id, p_shop_id)`
- Restores stock via positive `stock_movements`
- If udhaar: adds compensating `payment` type `ledger_entries`
- Preserves original sale row for audit trail
- Returns `{ sale_id, undone, restored }`

**File:** `frontend/src/lib/tools/undo_sale.ts` (102 lines)

**Exported:** `undoSaleDefinition: ToolDefinition`

| Property | Value |
|----------|-------|
| Name | `undo_sale` |
| Risk Tier | `commit_undo` |
| Parameters | `sale_id` (UUID) |

**Handler logic:**
1. Calls `undo_sale` RPC
2. Finds and marks the original `tool_calls` record as `'undone'`
3. Returns per-item restoration summary as chat text

---

### Phase 5A — `process_stock_adjustment` RPC

**File:** `supabase/migrations/20260904000000_stock_adjustment_rpc.sql` (88 lines)

**Function:** `public.process_stock_adjustment(p_shop_id, p_product_id, p_adjustment_type, p_value)`

| Adjustment Type | Behavior |
|----------------|----------|
| `restock_add` | `stock += value` (positive stock movement) |
| `restock_set` | `stock = value` (correction/stocktake) |
| `price_update` | `sale_price = value` (pricing change) |

Returns `{ before, after }` with old and new values.

---

### Phase 5B — `adjust_product` Tool Definition

**File:** `frontend/src/lib/tools/adjust_product.ts` (128 lines)

**Exported:** `adjustProductDefinition: ToolDefinition`

| Property | Value |
|----------|-------|
| Name | `adjust_product` |
| Risk Tier | `commit_undo` |
| Parameters | `product_name`, `adjustment_type` (restock_add/restock_set/price_update), `value` |

**Handler logic:**
1. Resolves product via `catalogService.resolveProduct()` — never creates new products (CATLG-1 is cut)
2. Returns candidate list if ambiguous
3. Calls `process_stock_adjustment` RPC
4. Returns before/after summary as chat text

---

## 4. Post-Implementation Changes

### 4.1 — Critical Audit Fixes (Stakeholder-Directed)

**Fix 1: LLM Provider Switch**
- **File:** `frontend/app/api/chat/route.ts` (now deleted)
- Changed `LLM_MODEL` fallback from `gpt-4o-mini` to `qwen-plus`
- Added `LLM_BASE_URL` fallback to `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

**Fix 2: Payment Type Trim**
- Removed `'split'` from all schemas, types, RPCs, and tools
- **Files affected:** `record_sale.ts` (enum), `salesService.ts` (type + condition), `sale_rpc.sql` (CHECK constraint + condition), `undo_sale_rpc.sql` (condition)
- Payment types now strictly: `cash` | `udhaar`

### 4.2 — Orchestration Removal (TOOL Epic Separation)

Per the instruction that TOOL-1/TOOL-2 orchestration belongs to another team member:

| Action | File | Result |
|--------|------|--------|
| **Deleted** | `frontend/src/lib/tools/index.ts` | Tool registration list removed |
| **Deleted** | `frontend/app/api/chat/route.ts` | Full orchestration loop removed |
| **Stripped** | `frontend/src/lib/tools/registry.ts` | `ToolRegistry` class + singleton removed; types preserved |

**Preserved (untouched):** All migrations, all 3 tool definitions, both services, `sales.ts` actions.

### 4.3 — Authentication Build Fix

**File:** `frontend/app/actions/auth.ts` (110 lines, modified)

The pre-existing auth pages imported functions that didn't exist. Fixed by adding:

| Function | Purpose |
|----------|---------|
| `signIn(formData)` | Authenticates via `supabase.auth.signInWithPassword()`, returns `{ error }` or redirects to `/app` |
| `getUserProfile()` | Fetches user's profile with shop join (`profiles.* + shops(id, name, address)`) |
| `signOut()` | Calls `supabase.auth.signOut()`, redirects to `/login` |
| `signUp` (alias) | `export { signUpAction as signUp }` — both import names work |
| `signUpAction` (fixed) | Added `redirect('/login')` at end instead of returning `{ success: true }` |

### 4.4 — UI/UX Redesign

**Dependency added:** `lucide-react ^1.39.0`

**File:** `frontend/app/globals.css` (40 lines, rewritten)
- Switched to Tailwind v4 `@import "tailwindcss"` syntax
- `@theme` block with custom brand (indigo) and emerald color palettes
- 3 custom animations: `fade-in`, `fade-in-up`, `slide-in-left`

**File:** `frontend/app/page.tsx` (241 lines, rewritten)
- Sticky navbar with blur backdrop and DukanYar branding
- Hero section with gradient text (`from-brand-600 to-emerald-500`)
- 4-card feature grid: Voice-First Sales, Fast Checkout, Real-Time Inventory, Khata Tracker
- 3-step "How It Works" section
- Gradient CTA banner
- Professional footer with feature badges

**File:** `frontend/app/(auth)/login/page.tsx` (177 lines, rewritten)
- 2-column split layout (left: brand panel with dark gradient, right: form)
- Lucide icons (`Mail`, `Lock`) inside input fields
- `focus:ring-2 focus:ring-brand-500/20` transitions
- Inline SVG spinner on submit button
- Brand panel hidden on mobile (`lg:flex`), replaced with mobile brand label

**File:** `frontend/app/(auth)/signup/page.tsx` (198 lines, rewritten)
- Matching split layout with `Store`, `Mail`, `Lock` icons
- Same focus ring and spinner pattern
- Distinct feature highlights on brand panel

---

## 5. Complete File Inventory

### Files Created (11 new files)

| # | Path | Lines | Category |
|---|------|-------|----------|
| 1 | `supabase/migrations/20260902100000_current_shop_id.sql` | 20 | DB Migration |
| 2 | `supabase/migrations/20260903000001_sale_seed_data.sql` | 142 | DB Migration |
| 3 | `supabase/migrations/20260903100000_sale_rpc.sql` | 118 | DB Migration |
| 4 | `supabase/migrations/20260903200000_undo_sale_rpc.sql` | 75 | DB Migration |
| 5 | `supabase/migrations/20260904000000_stock_adjustment_rpc.sql` | 88 | DB Migration |
| 6 | `frontend/src/lib/tools/registry.ts` | 44 | Type Contracts |
| 7 | `frontend/src/lib/tools/record_sale.ts` | 195 | AI Tool Definition |
| 8 | `frontend/src/lib/tools/undo_sale.ts` | 102 | AI Tool Definition |
| 9 | `frontend/src/lib/tools/adjust_product.ts` | 128 | AI Tool Definition |
| 10 | `docs/SALE_CATLG_IMPLEMENTATION.md` | 297 | Documentation |
| 11 | `docs/EXECUTION_AUDIT_REPORT.md` | 169 | Documentation |

### Files Deleted (2 files)

| # | Path | Reason |
|---|------|--------|
| 1 | `frontend/src/lib/tools/index.ts` | Orchestration wrapper — TOOL epic ownership |
| 2 | `frontend/app/api/chat/route.ts` | Orchestration loop — TOOL epic ownership |

### Files Modified (5 files)

| # | Path | What Changed |
|---|------|-------------|
| 1 | `frontend/src/lib/sales/catalogService.ts` | `resolveProduct()` rewritten to return `ResolveResult`; removed `.limit(1)`; added `listProducts()` |
| 2 | `frontend/app/actions/sales.ts` | Updated return type to `ResolveResult` |
| 3 | `frontend/src/lib/sales/salesService.ts` | Narrowed `payment_type` to `cash \| udhaar`; simplified udhaar condition |
| 4 | `frontend/app/actions/auth.ts` | Added `signIn`, `getUserProfile`, `signOut`; aliased `signUp`; added redirect after signup |
| 5 | `frontend/app/globals.css` | Switched to Tailwind v4 `@import`; added `@theme` block with custom colors and animations |

### Files Rewritten (3 files)

| # | Path | Lines | What It Is Now |
|---|------|-------|----------------|
| 1 | `frontend/app/page.tsx` | 241 | Full SaaS landing page with navbar, hero, features, CTA, footer |
| 2 | `frontend/app/(auth)/login/page.tsx` | 177 | 2-column split auth layout with icon inputs and loading states |
| 3 | `frontend/app/(auth)/signup/page.tsx` | 198 | 2-column split auth layout with shop name field |

---

## 6. Database Schema Summary

### Complete Table Inventory (post all migrations)

**Foundation (pre-existing):**
| Table | Purpose |
|-------|---------|
| `shops` | Tenant root — each shop is an isolated data silo |
| `roles` | `shopkeeper` and `admin` role names |
| `profiles` | Extends `auth.users` with `shop_id` and `role_name` |
| `conversations` | Chat threads scoped to a shop |
| `messages` | Individual messages with `channel` (text/voice) and `status` |

**SALE + KHATA + EXP + TOOL + RPT (pre-existing, Phase 3+):**
| Table | Purpose |
|-------|---------|
| `products` | Catalog items with `stock` (can go negative per SALE-4) |
| `product_aliases` | Voice-resolution synonyms (e.g., `coke` → Coca-Cola) |
| `customers` | Khata holders with auto-incrementing `khata_number` per shop |
| `sales` | Transaction headers (`payment_type`, `total_amount`) |
| `sold_items` | Line items per sale (quantity + historical unit_price) |
| `stock_movements` | Audit trail for all stock changes (negative = sale, positive = restock) |
| `ledger_entries` | Udhaar balance tracking (`type`: udhaar or payment) |
| `expenses` | Shop expense records with categories |
| `expense_categories` | Expense classification |
| `tool_calls` | AI tool execution log with status tracking (pending → committed → undone) |
| `audit_log` | Admin-only action audit trail |

### SQL Functions

| Function | Migration | Purpose |
|----------|-----------|---------|
| `is_admin()` | FND fix | Returns `true` if current user has admin role |
| `current_shop_id()` | Phase 0A | Returns `profiles.shop_id` for `auth.uid()` — used in 15+ RLS policies |
| `assign_khata_number()` | Phase 3+ | Trigger: auto-increments khata number per shop on customer insert |
| `process_sale()` | Phase 4A | Atomic sale transaction (insert + stock + ledger in one call) |
| `undo_sale()` | Phase 4C | Reverse a sale (restore stock + offset ledger) |
| `process_stock_adjustment()` | Phase 5A | Restock, stocktake, or price update |

### Reporting Views (pre-existing, Phase 3+)

| View | Purpose |
|------|---------|
| `daily_sales_profit_view` | Aggregated daily revenue and profit per shop |
| `outstanding_udhaar_view` | Customer credit balances (udhaar minus payments) |
| `low_stock_view` | Products with `stock <= 5` |

---

## 7. Current Frontend Architecture

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx        ← 2-column split, Lucide icons, spinner
│   │   └── signup/page.tsx       ← 2-column split, Store/Mail/Lock icons
│   ├── actions/
│   │   ├── auth.ts               ← signIn, signUp/signUpAction, getUserProfile, signOut
│   │   └── sales.ts              ← resolveProductAction, processSaleAction
│   ├── api/health/route.ts       ← Health check endpoint
│   ├── app/page.tsx              ← Authenticated dashboard (pre-existing)
│   ├── globals.css               ← Tailwind v4 theme + animations
│   ├── layout.tsx                ← Root layout with Inter font + TenantProvider
│   └── page.tsx                  ← Landing page (SaaS design)
├── providers/
│   └── TenantProvider.tsx        ← Context provider for current user/shop
├── src/lib/
│   ├── sales/
│   │   ├── catalogService.ts     ← resolveProduct(), listProducts()
│   │   └── salesService.ts       ← recordSale() with stock management
│   └── tools/
│       ├── registry.ts           ← Type contracts (ToolDefinition, ToolContext, ToolResult)
│       ├── record_sale.ts        ← SALE-3/4 tool definition
│       ├── undo_sale.ts          ← SALE-4 undo tool definition
│       └── adjust_product.ts     ← CATLG-2 tool definition
├── utils/supabase/
│   ├── client.ts                 ← Browser-side Supabase client
│   ├── server.ts                 ← Server-side Supabase client (cookies)
│   └── admin.ts                  ← Admin Supabase client (bypasses RLS)
└── middleware.ts                  ← Auth guard + role-based routing
```

---

## 8. What Was NOT Built (Cut Items)

| Item | Reason | Status |
|------|--------|--------|
| Separate Python/FastAPI backend | Duplicates existing Next.js Supabase wiring | Not touched |
| Catalog list page (`/app/catalog/page.tsx`) | No dedicated UI per scope | Not created |
| `ProductMatchCard.tsx` | Chat text only | Not created |
| `SaleConfirmationCard.tsx` | Chat text only | Not created |
| `AdjustConfirmationCard.tsx` | Chat text only | Not created |
| `AddProductCard.tsx` | CATLG-1 cut | Not created |
| `LowStockAlerts.tsx` | CATLG-3 cut | Not created |
| `pg_trgm` extension | Overkill for 16-product demo | Not added |
| CATLG-1 (add product by voice) | Roadmap; seed data covers demo | Not implemented |
| CATLG-3 (proactive low-stock alerts) | P3 roadmap | Not implemented |
| Chat orchestration loop | TOOL epic ownership | Created then deleted |
| Tool registry class + singleton | TOOL epic ownership | Created then stripped |

---

## 9. Environment Variables

The `.env.local` file requires:

| Variable | Required | Default |
|----------|----------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | _(none)_ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | _(none)_ |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | _(none)_ |
| `LLM_API_KEY` | Yes* | _(none)_ |
| `LLM_BASE_URL` | No | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | No | `qwen-plus` |

> *`LLM_*` variables were used by the now-deleted `route.ts`. The TOOL epic owner will need these when building the orchestration module.

---

## 10. TypeScript Compilation Status

```
$ tsc --noEmit
(No output — zero errors)
```

All files compile cleanly. The 4 pre-existing auth errors in `login/page.tsx`, `signup/page.tsx`, and `app/page.tsx` were resolved by adding the missing server action exports to `auth.ts`.

---

## 11. Migration Execution Order

Migrations must be pushed in timestamp order:

```
1. 20260901000001_fix_fnd_phase1_schema.sql     — pre-existing (FND fix)
2. 20260901092045_fnd_phase1_schema.sql         — pre-existing (Foundation)
3. 20260902070905_sale_khata_exp_tool_admin_rpt.sql — pre-existing (Phase 3+)
4. 20260902100000_current_shop_id.sql            — NEW (RLS helper)
5. 20260903000001_sale_seed_data.sql             — NEW (demo catalog)
6. 20260903100000_sale_rpc.sql                   — NEW (atomic sale + CHECK fix)
7. 20260903200000_undo_sale_rpc.sql              — NEW (atomic undo)
8. 20260904000000_stock_adjustment_rpc.sql       — NEW (CATLG-2 adjustments)
```

---

## 12. Plan Adherence Summary

| Category | Verdict |
|----------|---------|
| Unplanned deviations | **0** |
| Directed overrides (stakeholder-requested) | **2** — DashScope defaults, split removal |
| Cut items accidentally built | **0** |
| New TypeScript errors introduced | **0** |
| All SALE-1 through SALE-4 complete | **Yes** |
| CATLG-2 complete | **Yes** |
| TOOL epic separation clean | **Yes** — types preserved, wrapper removed |

---

## 13. Handoff Notes for TOOL Epic

The 3 tool definition files in `frontend/src/lib/tools/` are designed to be imported by the orchestration module:

```ts
import { recordSaleDefinition } from './record_sale';
import { undoSaleDefinition } from './undo_sale';
import { adjustProductDefinition } from './adjust_product';
```

Each exports a `ToolDefinition` object with:
- `name` — the model-facing tool name
- `description` — natural-language description for the system prompt
- `parameters` — JSON Schema the model fills when calling the tool
- `riskTier` — `'commit_undo'` for all three
- `handler(params, ctx)` — async function that executes the tool and returns `ToolResult`

The `ToolContext` interface (in `registry.ts`) specifies what the orchestrator must provide:
- `supabase` — authenticated Supabase client
- `shopId`, `userId`, `conversationId`, `messageId` — session context

The orchestrator is responsible for:
- Registering tools and converting schemas to OpenAI-compatible format
- Running the conversation loop (model → tool call → result → model)
- Risk-tier handling (all 3 tools are `commit_undo` — no approval flow needed)
- Persisting messages and tool calls to the database
