# Epic — Foundation (Layer 0)

**Goal:** Stand up the thin, shared skeleton every pillar builds inside — a
deployed monorepo, the database with its Phase-1 tables and a migration
convention, and a minimal app shell — so that the TEXT, VOICE, and AUTH pillars
can start on day 1 without re-plumbing infrastructure. This is ground to stand on,
not a feature; it is built once and then frozen.

**Ticket prefix:** FND

**Suggested build order:** FND-1 (scaffold + deploy) first, since nothing exists
until the monorepo and pipeline do. Then FND-2 (schema + migrations) and FND-3
(app shell + shared config) — these two are independent of each other and can
build in parallel once the repo exists.

**Scope note:** Phase-1 tables only — `shops`, `users`, `roles`, `conversations`,
`messages`. Business/feature tables (sales, inventory, udhaar, expenses) are
deliberately deferred to Phase 3 (tool-calling), so the schema stays small.

**Sources:** Stakeholder grilling session (this project's scoping conversation);
Alibaba Cloud AI Hackathon 2026 constraints (deploy on Alibaba Cloud, use Qwen
models, open-source repo with license).

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| FND-1 | Scaffold monorepo, CI & deployment skeleton | To Be Done | TBD | TBD | TBD |
| FND-2 | Database schema & migrations (Phase-1 tables) | To Be Done | TBD | TBD | TBD |
| FND-3 | App shell, shared config & environment | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
