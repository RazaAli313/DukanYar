# Epic — Udhaar / Credit Ledger (Phase 3)

**Goal:** Manage customer credit (*udhaar*) — register customers by khata number with a
CNIC fallback anchor, log goods given on credit, take repayments (approval-gated), and
answer balance lookups by voice. This is the emotional core of the product: udhaar is
the pain point shopkeepers most want solved.

**Ticket prefix:** KHATA

**Suggested build order:** KHATA-1 (customer registration) first — no ledger without
customers. Then KHATA-2 (log udhaar) and KHATA-4 (lookup), then KHATA-3 (repayment),
which is approval-gated and money-in.

**Depends on:** TOOL (registry, orchestration, risk-tiered confirm/undo), AUTH-3 (shop
scoping). Owns its own tables; registers its tools as additive files.

**Sources:** Stakeholder grilling session (this conversation) — khata# primary id, CNIC
fallback; khata# present ⇒ udhaar; repayment/money-in needs approval; giving vs repaying
distinguished by verb/intent; occasional customer without khata# looked up by CNIC.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| KHATA-1 | Customer registration (khata# + CNIC) | To Be Done | TBD | TBD | TBD |
| KHATA-2 | Log udhaar tool (goods on credit) | To Be Done | TBD | TBD | TBD |
| KHATA-3 | Udhaar repayment tool (approval-gated) | To Be Done | TBD | TBD | TBD |
| KHATA-4 | Udhaar lookup (by khata# or CNIC fallback) | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
