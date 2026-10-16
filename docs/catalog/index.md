# Epic — Voice Catalog & Alerts (Roadmap)

**Goal:** Let shopkeepers build and maintain their catalog by voice — add new products
and adjust/restock existing ones — and receive proactive low-stock alerts. This is the
*write* half of inventory (SALE covers the decrement/read half) and is deliberately
roadmap: it is messier to parse and can corrupt the catalog the rest of the product
depends on, so it comes after the core flows are solid.

**Ticket prefix:** CATLG

**Suggested build order:** CATLG-2 (restock/adjust) before CATLG-1 (add product) —
adjusting an existing product is simpler and lower-risk than full product creation.
CATLG-3 (proactive alerts) last.

**Depends on:** SALE (catalog + stock), TOOL (registry, orchestration, confirm/undo).

**Sources:** Stakeholder grilling session (this conversation) — add/adjust products by
voice deferred to roadmap; pre-seed catalog for demo instead; proactive low-stock alerts
are roadmap beyond the on-demand RPT-4 report.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| CATLG-1 | Add product by voice | To Be Done | TBD | TBD | TBD |
| CATLG-2 | Adjust / restock by voice | To Be Done | TBD | TBD | TBD |
| CATLG-3 | Proactive low-stock alerts | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
