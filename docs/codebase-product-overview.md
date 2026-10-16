# DukanYar product and PRD overview

_Research note based on repository-owned documentation. Reviewed 2026-10-16. The latest explicitly dated status source is 2026-09-03, so “current” below means “current in the docs,” not independently verified runtime state._

## Executive summary

DukanYar is intended to be a mobile-first, voice-first AI shop assistant for small retail shopkeepers in Pakistan. A shopkeeper speaks or types in Urdu, Roman Urdu, or mixed Urdu/English; the assistant records sales, adjusts stock, manages customer credit (*udhaar/khata*), logs expenses, and answers business questions. Every spoken result also remains visible on screen. A second, internal admin role oversees shops, users, voice/transcription quality, audit events, and service health. Sources: [docs overview](README.md), [TEXT epic](text-model/index.md), [VOICE epic](voice/index.md), [ADMIN epic](admin/index.md).

The product’s emotional center is khata: remembering who owes what, identifying customers by a shop-local khata number with CNIC fallback, safely recording repayments, and answering balances at the counter. The “hero” commercial flow is one utterance that records a sale, decrements inventory, and—when a khata is named—adds the amount to that customer’s credit ledger. Sources: [KHATA epic](khata/index.md), [SALE epic](sale/index.md), [tool orchestration story](tool-calling/user-stories.md).

The latest status document says a substantial demo already exists: login, dashboard, mode selection, voice/text capture, confirmation, sales, expenses, udhaar give/repay/lookup, inventory views, and dashboard summaries. It also says the demo still has material blockers: signup is broken, deployment has not happened, browser shakeout is pending, undo controls and voice reporting are missing, and migrations/RLS have drift. Source: [build status](STATUS.md).

## Target users and jobs

### Primary: shopkeeper at the counter

The primary user is a small Pakistani retail shopkeeper who needs a low-friction “employee” while serving customers. The intended interaction is one-handed, fast, tolerant of noisy environments, and natural in Urdu/Roman Urdu with English product names. Text remains a first-class fallback for quiet settings, noisy transcription, or correcting a voice turn. Sources: [docs overview](README.md), [TEXT user stories](text-model/user-stories.md), [VOICE user stories](voice/user-stories.md), [foundation shell story](foundation/user-stories.md).

Core jobs:

- Record a cash or credit sale without navigating forms.
- Keep stock current as sales happen and see low-stock items.
- Register khata customers and track goods given, repayments, and balances.
- Log expenses such as electricity, rent, and supplies.
- Ask “how is the shop doing?” for sales, profit, outstanding credit, and low stock.
- Review and correct what the AI understood before or just after it writes data.

### Secondary: platform admin

The admin is described as “us, the platform builders,” not a shop employee. The admin needs cross-shop user/shop management, account suspension, voice/transcription failure review, audit filtering, and health/error visibility. Cross-shop access must be an explicit admin capability and never leak to a shopkeeper. Sources: [docs overview](README.md), [AUTH user stories](auth/user-stories.md), [ADMIN user stories](admin/user-stories.md).

### Engineering user

Several requirements exist primarily for the team: additive migrations, independently owned modules, per-shop RLS, swappable AI/STT/TTS providers, and tool files that can be added without merge conflicts. Sources: [development strategy](README.md), [TOOL epic](tool-calling/index.md), [VOICE epic](voice/index.md), [foundation user stories](foundation/user-stories.md).

## Intended experience and workflows

### 1. Enter by voice or text

The shopkeeper holds a large microphone button, speaks, and releases to submit. The app shows recording state, transcribes Urdu, displays the recognized text, runs the same conversation path used for typed input, shows the response, and optionally speaks it. Silent or low-confidence recordings should prompt a retry. Voice and text turns share one persisted thread and can alternate. Sources: [VOICE user stories](voice/user-stories.md), [TEXT persistence story](text-model/user-stories.md).

### 2. Record a sale

Example: “2 coke, 1 chips, 450” records a cash sale for the stated total of Rs 450. “Khata 12 pe 2 coke, 450 udhaar” records a credit sale and ledger entry. Product terms resolve through catalog names and aliases; ambiguous or unknown items should be surfaced instead of guessed. Stock decrements atomically with the sale, but insufficient stock should warn rather than block. The stated total—not the computed catalog total—is the source of truth. Sources: [SALE user stories](sale/user-stories.md), [SALE epic](sale/index.md).

### 3. Manage khata

A customer is registered with name and CNIC and assigned a shop-local khata number. Giving goods on credit raises the balance; repayment lowers it only after explicit approval; balance lookup is read-only and works by khata number or CNIC fallback. The docs also expect verb/intent to distinguish “gave credit” from “repaid/jama.” Sources: [KHATA user stories](khata/user-stories.md), [KHATA epic](khata/index.md).

### 4. Log and review expenses

An utterance such as “bijli ka bill 3000” creates a positive expense, infers Utilities where possible, and offers correction/undo. Expenses should be listed most recent first with amount, category, and date, and be deletable. Missing amounts require clarification rather than a zero-value write. Sources: [EXP user stories](expense/user-stories.md), [EXP epic](expense/index.md).

### 5. Ask for business summaries

The intended assistant can answer today’s sales and profit, total outstanding udhaar, largest debtors, and low-stock products. These are read-only queries. Profit is specified as sales minus cost of goods sold, and low-stock status is specified against a per-product configurable threshold. Sources: [RPT user stories](reporting/user-stories.md), [RPT epic](reporting/index.md).

### 6. Correct and trust actions

The original safety model has two tiers: routine logging commits immediately with a prominent undo, while money-in actions such as repayments wait for approval. Every action is also rendered in a structured card showing amount, items, and khata/customer, with uncertain fields visibly flagged. Source: [TOOL user stories](tool-calling/user-stories.md).

## Scope and milestone model

The planning docs describe a walking skeleton followed by vertical feature slices:

| Milestone | Intended outcome | Included epics |
|---|---|---|
| Phase 1 — pillars | Prove identity, persisted text conversation, and end-to-end voice conversation; no business tools yet | FND, TEXT, VOICE, AUTH |
| Phase 2 — action layer | Let the model invoke typed tools through a shared orchestration loop with confirmation/undo | TOOL |
| Phase 3 — shop operations | Deliver the hero flows and read-only summaries | SALE, KHATA, EXP, RPT |
| Phase 4 — operations/polish | Add platform administration and production oversight | ADMIN |
| Roadmap | Let the shopkeeper create/adjust the catalog by voice and receive proactive alerts | CATLG |

Source: [phase roadmap](README.md).

The execution strategy assigns a thin shared foundation first, then three parallel pillars (text/model, voice/model, auth/tenancy). Each publishes a contract early so the others can work against stubs. Later feature epics are meant to add their own tools and migrations without editing shared routers or other epics’ migrations. Source: [development strategy and ownership](README.md).

## Functional requirements by domain

| Domain | Minimum requirement in the product docs | Source |
|---|---|---|
| Identity | Signup creates a shop-linked user; login/session/logout work; shopkeeper and admin routes are server-guarded | [AUTH stories](auth/user-stories.md) |
| Tenancy | Every shop row is isolated at the data layer/RLS; cross-shop read is admin-only | [AUTH stories](auth/user-stories.md) |
| Conversation | Persist both sides, reload in order, use bounded recent context, stream when supported, preserve failed input for retry | [TEXT stories](text-model/user-stories.md) |
| Language | Understand Urdu, Roman Urdu, and code-switching; answer concisely in the user’s register; clarify ambiguity | [TEXT stories](text-model/user-stories.md) |
| Voice | Push-to-talk, visible capture/transcript, STT confidence handling, adapter-based TTS, text fallback | [VOICE stories](voice/user-stories.md) |
| Sales | Resolve aliases/ambiguity; stated total wins; cash vs khata credit; atomic stock update; negative stock warns | [SALE stories](sale/user-stories.md) |
| Khata | Shop-local khata number, CNIC fallback, auditable credit/payment entries, approval for repayments, read-only lookup | [KHATA stories](khata/user-stories.md) |
| Expenses | Positive amount, inferred/optional category, list/review/delete, clarification for missing amount | [EXP stories](expense/user-stories.md) |
| Reporting | Owned read views; COGS profit; outstanding/maximum debtors; configurable low-stock threshold | [RPT stories](reporting/user-stories.md) |
| Safety/UI | Structured action card, uncertainty flags, enforced approval/undo tier, text always present even with voice | [TOOL stories](tool-calling/user-stories.md) |
| Admin | Shops/users and suspension; transcription failure review; immutable audit view; system health | [ADMIN stories](admin/user-stories.md) |
| Catalog roadmap | Add, restock, set stock, and change price by voice; de-duplicated proactive low-stock alerts | [CATLG stories](catalog/user-stories.md) |

## Documented state versus intended scope

According to the 2026-09-03 status report, the implementation has gone beyond the phase labels in the older epic indices. Text, voice, conversation persistence, sales, expense logging, and core khata flows are reported working; the product uses a dashboard where the shopkeeper chooses `sale`, `udhaar`, `kharcha`, or `ask`, then enters a mode-specific parse/confirm/commit flow. Source: [build status](STATUS.md).

The same report identifies the highest-priority remaining work:

1. Fix new-user signup.
2. Click through and stabilize the frontend in a live browser.
3. Deploy frontend and backend.
4. Add undo controls to recorded cards.
5. Support voice/text reporting in “Poocho” mode.
6. Render a per-customer khata view.
7. Add a dedicated expense review/delete screen.
8. Improve Urdu STT/TTS quality.
9. Eliminate migration drift and repair the clean-database path.
10. Resolve the tenancy/RLS strategy and dashboard performance.

Source: [prioritized gaps in build status](STATUS.md).

## Current source-code snapshot

The current working tree is newer than `STATUS.md` and includes Vercel
deployment setup, the backend tool registry, generic approval/undo UI, and
dashboard fixes. Direct source inspection therefore supersedes several gaps in
the September 3 status snapshot:

- The deployed shape is defined as one Vercel Services project: Next.js routes
  plus a FastAPI service under `/api/*`. Configuration is documented,
  but the repository does not prove that a live production deployment exists.
- Signup now creates the shop through the admin client and upserts the generated
  profile, addressing the duplicate-profile flow described in `STATUS.md`.
- The confirmation card uses generic confirm, reject, and undo endpoints backed
  by audited tool-call records.
- A self-registering Python tool registry exposes every tool to one LLM-driven
  orchestration loop. Screen modes are prompt hints rather than hard-coded
  routing, and each tool owns its risk tier, presentation, and undo behavior.
- The admin console exists with overview, shops/users, voice telemetry, audit,
  and health tabs. Its implementation still needs runtime/RLS verification.
- Dashboard profit is now calculated from sold-item price minus product cost,
  replacing the documented flat 8% shortcut. Low stock remains hard-coded at 5.
- The general ledger UI exists, but the customer-list endpoint is still not
  rendered as a per-customer khata experience; expense deletion is available
  only through the immediate post-recording undo flow.

Local verification on 2026-10-16 found:

- `next build --webpack`: passes, with middleware/Edge warnings.
- `npm run lint`: fails with three errors and one hook warning, concentrated in
  admin typing, khata effect state, and the conversation recorder dependency.
- `pytest`: 72 passed and 16 failed. All 16 failures are conversation-router
  tests whose old fake LLM only mocks streaming; the newly added `ask` tool loop
  calls `tool_call_reply` and reaches an unmocked client. This is a test-contract
  regression and means the branch is not currently green, even though most
  service/auth/khata/expense coverage passes.

## Material inconsistencies and decisions to reconcile

There is no single canonical PRD/status source. The most important conflicts are:

1. **Architecture and platform constraints.** The main docs define Next.js + FastAPI + Supabase and explicitly allow any provider/deployment choice. Older execution reports call “no Python/FastAPI backend,” “no dedicated UI,” and Alibaba/Qwen hard constraints. The repository overview and later status follow the former architecture. Sources: [docs overview](README.md), [full session report](FULL_SESSION_REPORT.md), [root README](../README.md), [build status](STATUS.md).

2. **Automatic orchestration versus user-selected modes.** TOOL-2 specifies a single free-form message that can select and combine multiple tools. The status report says the design changed: the user picks a mode first, there is no intent classifier, and mode handlers are hard-wired. Decide whether modes are the actual MVP product or only a temporary demo scaffold. Sources: [TOOL stories](tool-calling/user-stories.md), [build status](STATUS.md).

3. **Safety semantics.** TOOL-3 specifies immediate commit + undo for routine logging and approval only for money-in. The latest status says every record action uses confirm-then-commit and no undo is wired. This affects speed at the counter and should be an explicit product decision, not an accidental implementation detail. Sources: [TOOL stories](tool-calling/user-stories.md), [build status](STATUS.md).

4. **Admin completion.** `admin/index.md` marks ADMIN-1..3 done, while `STATUS.md` says the admin console is not started. These cannot both be the project status. Sources: [ADMIN index](admin/index.md), [build status](STATUS.md).

5. **Epic status freshness.** Most epic indices still show “To Be Done” even when `STATUS.md` reports the work done or partial. Conversely, catalog docs call CATLG roadmap, a session report claims CATLG-2 complete, and the status report says CATLG is untouched. Sources: [epic index](README.md), [catalog index](catalog/index.md), [session report](FULL_SESSION_REPORT.md), [build status](STATUS.md).

6. **Sales atomicity.** SALE-4 requires sale and item decrements to succeed together or not at all. The session report claims an atomic `process_sale` RPC, but the latest status says recording/decrement is not wrapped as a single transaction. The database path must be verified and the stale statement removed. Sources: [SALE stories](sale/user-stories.md), [session report](FULL_SESSION_REPORT.md), [build status](STATUS.md).

7. **Reporting accuracy.** The reporting PRD requires profit from sale minus cost of goods sold and a configurable per-product threshold. The status report says profit is a flat 8% shortcut and low-stock uses a hard-coded threshold of 5. Those numbers should not be presented as correct accounting. Sources: [RPT stories](reporting/user-stories.md), [build status](STATUS.md).

8. **Product resolution scope.** SALE-2 calls for fuzzy matching, correction without restarting, prompted product creation, and explicit ambiguity handling. The latest status describes exact/alias/substring matching, no ambiguity dialogue, and unknown items blocking confirmation. Sources: [SALE stories](sale/user-stories.md), [build status](STATUS.md).

9. **Tenancy guarantee versus implementation.** AUTH-3 requires database-layer isolation even when app code forgets a filter. The status report says backend service-role reads bypass RLS and rely on explicit `shop_id`, while RLS is partly broken because JWT metadata is not populated. That does not yet satisfy the written guarantee. Sources: [AUTH stories](auth/user-stories.md), [build status](STATUS.md).

10. **Status artifacts are snapshots, not a maintained roadmap.** `STATUS.md` names a feature branch as containing “everything”; handoffs and reports describe historical intermediate trees, deleted paths, and now-resolved blockers. They are useful provenance but unsafe as current build instructions. Sources: [build status](STATUS.md), [TEXT/VOICE handoff](HANDOFF.md), [expense/khata handoff](expense-khata-handoff.md), [full session report](FULL_SESSION_REPORT.md).

## Proposed product definition for discussion

A coherent near-term MVP would be:

> A mobile counter assistant for Pakistani shopkeepers that reliably records sales, expenses, and khata transactions by voice or text; makes every parsed action legible before/after writing; preserves shop isolation; and answers a small set of factual shop questions.

For a credible demo/release, this implies prioritizing correctness and recoverability over broad feature count:

- Keep the four explicit modes for the first release if they materially improve extraction reliability, but label free-form multi-tool orchestration as a later capability.
- Use confirm-before-write for repayments and any high-risk catalog/account action. Choose either confirm-before-write or commit-with-undo for routine sale/expense/udhaar logs, then implement it consistently.
- Treat signup, tenancy, clean migrations, and deployment as release blockers.
- Treat real COGS reporting as required before calling the result “profit”; otherwise label the metric as an estimate or omit it.
- Finish the existing correction surfaces (undo, unknown/ambiguous item resolution, expense delete, customer khata view) before proactive alerts or catalog creation by voice.
- Defer the admin console unless the next milestone is a production pilot rather than a shopkeeper demo.

## Open questions for the team

1. Is the immediate target a hackathon demo, a pilot with real shops, or a production SaaS release?
2. Are dashboard modes the intended UX, or must one free-form conversation automatically choose/combine actions?
3. For routine writes, is the product rule “confirm first” or “commit with undo”?
4. Is spoken/stated sale total always authoritative even when it disagrees with line-item prices, and how should that discrepancy be displayed?
5. May stock go negative in a pilot, or should this become an approval/warning gate?
6. Is CNIC appropriate and legally/operationally acceptable to store for this use case, and what masking/retention controls are required?
7. Is “profit” allowed to be estimated, or must cost price and COGS be complete and auditable?
8. Does Phase 1 require an admin role/surface, or can admin be deferred behind operational scripts?
9. What is the source of truth for shop isolation: correct RLS with user-scoped clients, or service-role backend access with mandatory scoping and authorization tests?
10. Which model-provider constraints are still real: Alibaba/Qwen, or the current provider-neutral OpenAI-compatible adapter? Deployment is now decided as Vercel Services plus Supabase.
11. What offline/poor-connectivity behavior is required at a Pakistani retail counter?
12. Which document becomes canonical, and who updates ticket status/acceptance criteria when implementation decisions change?

## Recommended documentation cleanup

Create one short canonical PRD that owns the product promise, current MVP boundary, interaction/safety rules, and success criteria. Keep epic tickets as detailed acceptance criteria, `STATUS.md` as generated/current implementation status, and move historical handoffs/session reports under an archive label. Add a decision log for the mode-based UX, confirmation policy, tenancy model, accounting semantics, and provider/deployment choices. This would remove most of the ambiguity without discarding useful implementation history.
