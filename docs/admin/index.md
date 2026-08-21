# Epic — Admin Console (Phase 4)

**Goal:** Give the platform builders (admin role) oversight across all shops — manage
shops and users, monitor voice/transcription quality, and see an audit trail and system
health. This is the second of the two roles and what makes the product "production, two
roles" rather than a single-tenant demo.

**Ticket prefix:** ADMIN

**Suggested build order:** ADMIN-1 (shops & users) first, then ADMIN-2 (voice/
transcription monitoring) and ADMIN-3 (audit & health) in parallel.

**Depends on:** AUTH-2 (admin role & guards). Reads across shops **only** as an explicit
admin capability, via owned views/service endpoints — never a shopkeeper capability.

**Sources:** Stakeholder grilling session (this conversation) — two roles: shopkeeper
(user) and admin (platform builder); voice/transcription accuracy monitoring; audit.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| ADMIN-1 | Shops & users management | To Be Done | TBD | TBD | TBD |
| ADMIN-2 | Voice & transcription monitoring | To Be Done | TBD | TBD | TBD |
| ADMIN-3 | Audit log & system health | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
