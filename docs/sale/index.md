# Epic — Sales & Inventory (Phase 3)

**Goal:** Record a sale from one natural utterance, resolve the items against the
catalog, and decrement inventory automatically — the hero flow of the product. A cash
sale is a plain log; when a khata number is present the sale is credit (handled with
KHATA). The shopkeeper's spoken amount is the recorded total.

**Ticket prefix:** SALE

**Suggested build order:** SALE-1 (catalog + seed) first — nothing resolves without
products. Then SALE-2 (item resolution) and SALE-3 (record-sale tool), then SALE-4
(inventory decrement) which depends on the sale writing.

**Depends on:** TOOL (registry + orchestration + confirm/undo), AUTH-3 (shop scoping).
This epic owns its tables and registers its tools as additive files.

**Sources:** Stakeholder grilling session (this conversation) — hero flow
sale→inventory→udhaar; item resolution fuzzy + confirm + auto-add; pre-seeded catalog
for demo; spoken amount is source of truth; out-of-stock flags but never blocks.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| SALE-1 | Product catalog & seed data | To Be Done | TBD | TBD | TBD |
| SALE-2 | Item resolution (fuzzy match + confirm + auto-add) | To Be Done | TBD | TBD | TBD |
| SALE-3 | Record-sale tool (cash vs udhaar by khata presence) | To Be Done | TBD | TBD | TBD |
| SALE-4 | Inventory decrement & out-of-stock flagging | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
