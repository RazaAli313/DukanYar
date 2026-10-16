# Epic — Expense Tracking (Phase 3)

**Goal:** Let a shopkeeper log a shop expense by voice or text — "bijli ka bill 3000" —
so the app captures money going out, rounding out the "full employee" story alongside
sales and udhaar. Commit-with-undo; no approval needed.

**Ticket prefix:** EXP

**Suggested build order:** EXP-1 (schema) first, then EXP-2 (log-expense tool), then
EXP-3 (list/review UI).

**Depends on:** TOOL (registry, orchestration, commit/undo), AUTH-3 (shop scoping).
Reuses the exact voice→commit pattern from SALE, so it is cheap.

**Sources:** Stakeholder grilling session (this conversation) — expense tracking is
MVP-light, commit + undo, same voice pattern as sales.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| EXP-1 | Expenses schema & categories | Done (in DB) | Sheheryar | TBD | TBD |
| EXP-2 | Log-expense tool (commit + undo) | To Be Done | TBD | TBD | TBD |
| EXP-3 | Expense list & review | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
