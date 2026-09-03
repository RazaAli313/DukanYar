# DukanYar — build status

_As of 2026-09-03. Branch `feat/text3-persistence` (has **everything**: TEXT/VOICE +
EXPENSE/KHATA + TEXT-3 persistence + the shopkeeper UI + SALE/KHATA/EXP tools)._

## TL;DR

- **Working end-to-end today:** login → dashboard → pick a mode → speak/type →
  confirmation card → record → shows in Khata. For **sale, kharcha, udhaar**
  (give + repay + lookup + register-new-customer). Voice in/out works.
- **Backend:** solid, ~86 tests passing against real Supabase.
- **Frontend:** built, typechecks, production build passes. **Not yet clicked
  through live in a browser** — expect small wiring/visual bugs.
- **Biggest gaps:** signup is broken for real new users (demo account works),
  nothing is deployed, no admin console, no TOOL registry, no undo buttons.

---

## Epic-by-epic

Legend: ✅ done · 🟡 partial · ❌ not started

### FND — Foundation
| Ticket | Status | Notes |
|---|---|---|
| FND-1 monorepo + CI + deploy | 🟡 | Repo ✅, CI workflow ✅, LICENSE ✅. **Not deployed** (needs Vercel + Render/Railway). |
| FND-2 Phase-1 schema | ✅ | shops/roles/profiles/conversations/messages exist. |
| FND-3 app shell + PWA + config | 🟡 | App shell ✅ (bottom nav, one layout, theme). **No PWA** (manifest/service worker). Config centralised ✅. |

### TEXT — Text ⇄ Model
| Ticket | Status | Notes |
|---|---|---|
| TEXT-1 chat input UI | ✅ | Text input in the conversation screen. |
| TEXT-2 model integration + streaming | ✅ | `llm.py`, SSE streaming, `/conversations/.../messages`. |
| TEXT-3 conversation persistence & history | ✅ | One thread per shop, `GET /conversations/history`, DB-derived context, 51 tests. |
| TEXT-4 Urdu/Roman/English + persona | ✅ | `prompts.py` persona; voice transcripts now romanised so the whole thread reads Roman-Urdu. |
| TEXT-5 dashboard + mode conversation screen | 🟡 | Dashboard + `/record/[mode]` + ConfirmationCard built. **Live browser shakeout pending.** |

### VOICE — Voice ⇄ Model
| Ticket | Status | Notes |
|---|---|---|
| VOICE-1 push-to-talk | ✅ | `usePushToTalk`, wired into the conversation screen. |
| VOICE-2 STT | ✅ | Speechmatics via `/voice/transcribe`; transcript romanised on the backend. |
| VOICE-3 TTS playback | ✅ | edge-tts via `/voice/speak`, `useReplySpeech`. |
| VOICE-4 end-to-end loop + parity | ✅ | Voice and text interchangeable in one thread. |
| _STT/TTS quality upgrade (ElevenLabs / Uplift AI)_ | ❌ | Provider is swappable via `.env` (`LLM_*`, `STT_PROVIDER`, `TTS_PROVIDER`). Not evaluated. |

### AUTH — Auth, RBAC & Tenancy
| Ticket | Status | Notes |
|---|---|---|
| AUTH-1 signup / login / sessions | 🟡 | **Login works. Signup is broken for new users** — the `handle_new_user` DB trigger auto-creates the profile row, then `signUp()` in `frontend/app/actions/auth.ts` tries to INSERT it again → PK collision → orphan user + shop. Fix: change that INSERT to an UPDATE (attach `shop_id`), and/or use the service-role admin client. The seeded `demo@dukanyar.com` account works fine. |
| AUTH-2 RBAC shopkeeper vs admin | 🟡 | `profiles.role_name`, `get_current_user` returns role, middleware guards `/admin`. **No admin surface exists.** |
| AUTH-3 tenancy / RLS | 🟡 | Backend uses the service_role key + scopes every query by `shop_id` (works — sale/khata/expense/TEXT-3 all shop-isolated). RLS policies on the tables are **messy and partly broken**: `current_shop_id()` reads `app_metadata.shop_id`, which **nothing populates**, so any RLS-bound query from the frontend would return nothing. The frontend avoids this by reading through the backend. |
| AUTH-4 role-based landing | 🟡 | Shopkeeper → `/app` ✅. Admin → `/admin` (doesn't exist yet). Signed-out → `/login` ✅. |
| `backend/app/auth.py` | — | Was a stub; TEXT-3 made it a **provisional** real dependency (verifies the Supabase token, reads `shop_id`/`role_name` from `profiles`). The AUTH epic owns the final version. |

### TOOL — Tool-Calling & Orchestration
| Ticket | Status | Notes |
|---|---|---|
| TOOL-1 tool registry | ❌ | No self-registering registry. Mode → handler is hard-wired in `conversations.py`. |
| TOOL-2 orchestration loop | 🟡 | **Design changed:** the shopkeeper picks the mode on the dashboard, so there is no intent classifier. Per mode the LLM does a structured parse → the router emits a confirmation card → an explicit confirm endpoint executes. Works for sale/kharcha/udhaar. Not a general multi-tool loop. |
| TOOL-3 risk-tiered confirm / undo | 🟡 | Every record action is confirm-then-commit (a card + "Haan"). **Undo is not wired to the UI** — `reverse_sale`, `reverse_ledger_entry`, `delete_expense` exist in the services but there is no undo button. |
| TOOL-4 on-screen action confirmation | ✅ | `ConfirmationCard` shows amount / items / customer, always on screen, unknown items flagged. Missing: an undo control on the recorded card. |

### SALE — Sales & Inventory
| Ticket | Status | Notes |
|---|---|---|
| SALE-1 catalog + seed | 🟡 | `products` / `product_aliases` exist; "Demo Dukan" has 16 products + Roman/Urdu aliases. **No seed migration or script in the repo** (seeded straight in the dashboard). Inventory screen ("Maal") ✅. |
| SALE-2 item resolution | 🟡 | Exact → alias → substring match, shows the pick on the card. **Not done:** ambiguity resolution ("two match equally → ask"), auto-add an unknown item (currently flagged "nahi mila" and blocks confirm). |
| SALE-3 record-sale tool | ✅ | Cash vs udhaar by khata presence; the stated total is stored as-is; confirm-then-commit. |
| SALE-4 inventory decrement + flag | ✅ | DB trigger decrements stock; negative stock flagged on the card. Not a single transaction (no rollback wrapper). Undo restores stock. |

### KHATA — Udhaar / Credit Ledger
| Ticket | Status | Notes |
|---|---|---|
| KHATA-1 customer registration | ✅ | `register_customer` + DB trigger assigns a per-shop khata number (1, 2, 3 …). Now inline in the udhaar flow — a new name + CNIC registers on the spot. **Bug found:** `customers` has no `created_by` column (worked around). |
| KHATA-2 log udhaar | ✅ | `log_udhaar`, confirm-then-commit. Undo exists (not UI-wired). |
| KHATA-3 udhaar repayment (approval-gated) | ✅ | `record_payment`; "jama / wapas / diye" routes to the payment path; confirmation gate. |
| KHATA-4 udhaar lookup | ✅ | "khata 1 ka udhaar batao" / "Akram ka kitna udhaar" → read-only balance, by khata # / CNIC / name. |
| _Per-customer khata screen_ | ❌ | The "Khata" tab shows the merged transaction ledger, not a per-customer view. `GET /khata/customers` (list + balances) exists but isn't rendered. |

### EXP — Expense Tracking
| Ticket | Status | Notes |
|---|---|---|
| EXP-1 schema + categories | 🟡 | Tables exist, categories seeded. **No repo migration** (dashboard drift — ask Sheheryar to commit the SQL). |
| EXP-2 log-expense tool | ✅ | `create_expense` + keyword category inference ("bijli" → Utilities); confirm-then-commit; "no amount → ask". |
| EXP-3 expense list & review | 🟡 | Expenses appear in the "Khata → Kharcha" tab. **No dedicated expense screen, no delete button** (`delete_expense` exists in the service). |

### RPT — Reporting & Summaries
| Ticket | Status | Notes |
|---|---|---|
| RPT-1 owned reporting views | 🟡 | Views exist in the migration, but `dashboard.py` / `ledger.py` query the base tables directly rather than the views. |
| RPT-2 daily sales & profit | 🟡 | `GET /dashboard/today` + the "Hisaab" screen show today's sale and profit. **Profit is a flat 8% of the sale total** (hackathon shortcut), not cost-of-goods. **Voice query ("aaj ki sale?") does NOT work** — the "Poocho" mode has no reporting tool, so the model says it can't look it up. |
| RPT-3 outstanding udhaar summary | 🟡 | Total outstanding shown on dashboard + Hisaab. "Who owes the most" list not done. Same voice-query limitation. |
| RPT-4 low-stock report | ✅ | Dashboard card + "Maal" screen low-stock filter. Threshold is hard-coded at 5 (not configurable). |

### ADMIN — Admin Console
| Ticket | Status |
|---|---|
| ADMIN-1..3 | ❌ Not started. `audit_log` table exists; no console, no shop/user management, no monitoring. |

### CATLG — Voice Catalog & Alerts (roadmap)
| Ticket | Status |
|---|---|
| CATLG-1 add product by voice | ❌ |
| CATLG-2 restock / adjust by voice | ❌ | "Maal" screen has a "restock jald aa raha hai" placeholder. |
| CATLG-3 proactive low-stock alerts | ❌ | On-demand low-stock report exists (RPT-4); no push. |

---

## What's left — prioritised

**Blockers for a clean demo**
1. **Fix signup** (AUTH-1) — INSERT → UPDATE in `auth.ts`, or the admin-client path. Sheheryar's `feat/fnd-supabase-auth` PR was heading here but doesn't compile and still INSERTs.
2. **Live browser shakeout** of the new UI — click every screen as `demo@dukanyar.com`, fix wiring/visual bugs.
3. **Deploy** — frontend to Vercel, backend to Render/Railway (CORS already configured).

**High value, not blocking**
4. Undo buttons on the confirmation cards (services already exist — TOOL-3).
5. Reporting via voice ("aaj ki sale kitni hui?") — add a read-only tool to "Poocho" mode (RPT-2/3).
6. Per-customer khata screen (KHATA — `/khata/customers` endpoint exists).
7. Dedicated expense list with delete (EXP-3).
8. STT/TTS quality — evaluate Uplift AI / ElevenLabs for Urdu (VOICE).

**Cleanup / debt**
9. **Migration drift** — `handle_new_user`, `handle_sold_item_stock`, `current_shop_id`, `set_*_updated_at` triggers, the EXP-1 schema, and the product seed all live **only in the Supabase dashboard**, not in migration files. A `supabase db reset` rebuilds a broken schema. Ask Sheheryar to commit them.
10. **Unapplied migration** `supabase/migrations/20260902190000_text3_conversation_shop_unique.sql` — needs the FND/migrations owner's ack (consequences in the file header).
11. Dashboard is ~4 s to load (many sequential Supabase reads) — batch or use the RPT views.
12. RLS is inconsistent; either fix `app_metadata.shop_id` population or accept "backend-only reads".
13. SALE-1 seed + EXP-1 schema need repo migrations.
14. Admin console (ADMIN) and voice catalog (CATLG) — untouched.

**Not in scope for the hackathon** (per Qoder's cut list, agreed): mobile-perfect polish, Azure TTS, full audit log, admin console.

---

## Branch / PR situation

- **`feat/text3-persistence`** — the working branch. Contains TEXT-1..5, VOICE-1..4, EXP, KHATA, TEXT-3, the shopkeeper UI, and the SALE/KHATA/EXP record tools. Stacked on top of the expense/khata work (which is stacked on text/voice), so its eventual PR carries all of it — tell Raza the merge order or review it as one bundle.
- **`feat/fnd-supabase-auth`** (Sheheryar) — open PR, **still has the 3 review bugs**: doesn't compile (`login`/`signup` import `signIn`/`signUp`, which his `auth.ts` no longer exports), the profile INSERT drops `email` (NOT NULL), and it INSERTs the profile that the trigger already made. See `docs/reviews/` history / the review shared earlier.
- `feature/user-stories` — merged, deleted.
