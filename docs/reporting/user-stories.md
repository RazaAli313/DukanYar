# User Stories — reporting RPT

## RPT-1 — Reporting views (owned read layer)
**As an** engineer
**I want** reporting to read other modules only through DB views defined and owned by this epic
**So that** reporting stays decoupled and a schema change elsewhere cannot silently break its queries

**Acceptance criteria** (from RPT-1.md):
- When reporting needs sales, udhaar, and expense data, it queries DB views defined in this epic's migration, not other epics' tables directly
- Every row returned by a reporting view is scoped to the acting shop
- When an upstream table adds or renames a column behind its view's contract, reporting queries continue to work as long as the view's shape is preserved

_Tickets: docs/reporting/RPT-1.md_

## RPT-2 — Daily sales & profit summary tool
**As a** shopkeeper
**I want** to ask today's sales and profit and hear the answer
**So that** "aaj ki sale kitni hui?" replies with the day's total and profit

**Acceptance criteria** (from RPT-2.md):
- When sales were recorded today and the shopkeeper asks for today's sales, the reply states the sum of today's sale totals and shows it on screen
- When products have cost prices and profit is reported, profit is computed as sale totals minus cost of goods sold for the period
- When no sales occurred today, the reply states there were no sales today rather than erroring
- Requesting a summary is read-only — no data is modified by asking

_Tickets: docs/reporting/RPT-2.md_

## RPT-3 — Outstanding udhaar summary tool
**As a** shopkeeper
**I want** to know the total udhaar owed to me across all customers
**So that** I know how much money is out on credit

**Acceptance criteria** (from RPT-3.md):
- When several customers carry balances and the shopkeeper asks how much udhaar is outstanding, the reply states the sum of all customer balances for the shop
- When the shopkeeper asks who owes the most, the largest balances are listed with khata numbers
- When no customer owes anything, the reply states nothing is outstanding

_Tickets: docs/reporting/RPT-3.md_

## RPT-4 — Low-stock report
**As a** shopkeeper
**I want** to see or ask which items are running low
**So that** I know what to restock, as an on-demand report (proactive push notifications are out of scope here — see CATLG roadmap)

**Acceptance criteria** (from RPT-4.md):
- When products have stock levels and a low-stock threshold and the shopkeeper asks what is running low, products at or below their threshold are listed with current stock
- Changing a product's low-stock threshold changes whether it appears in the report
- When all products are above threshold, the report states nothing is running low

_Tickets: docs/reporting/RPT-4.md_
