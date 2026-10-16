# Epic — Reporting & Summaries (Phase 3)

**Goal:** Answer "how's the shop doing?" by voice — today's sales, profit, outstanding
udhaar, and low-stock items. This epic is **read-only**: it reads sales, khata, and
expense data **through DB views it defines itself**, so a schema change in another epic
can't break its build. A spoken daily-profit number is the natural demo finale.

**Ticket prefix:** RPT

**Suggested build order:** RPT-1 (reporting views) first — the read layer everything
else queries. Then RPT-2, RPT-3, RPT-4 in parallel; they are independent of each other.

**Depends on (read-only):** SALE, KHATA, EXP data via owned views; TOOL for the query
tools. Writes nothing to other epics' tables.

**Sources:** Stakeholder grilling session (this conversation) — daily summaries, profit
(needs cost price), outstanding udhaar total, low-stock; read across contexts via views.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| RPT-1 | Reporting views (owned read layer) | To Be Done | TBD | TBD | TBD |
| RPT-2 | Daily sales & profit summary tool | To Be Done | TBD | TBD | TBD |
| RPT-3 | Outstanding udhaar summary tool | To Be Done | TBD | TBD | TBD |
| RPT-4 | Low-stock report | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
