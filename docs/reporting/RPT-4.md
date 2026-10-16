### RPT-4 — Low-stock report

| Field | Value |
| :---- | :---- |
| Ticket ID | RPT-4 |
| Ticket Name | Low-stock report |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | RPT-1 (views), SALE-1 (stock levels) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — low-stock as a report; proactive push alerts are roadmap (see CATLG) |

**Description:** As a shopkeeper, I want to see or ask which items are running low, so
that I know what to restock. Proactive push notifications are out of scope here (see
CATLG roadmap); this is an on-demand report.

**Acceptance Criteria:**
```gherkin
Feature: Reporting — low stock

  Scenario: Items below threshold are listed
    Given products have stock levels and a low-stock threshold
    When the shopkeeper asks what is running low
    Then products at or below their threshold are listed with current stock

  Scenario: Threshold is configurable
    Given a product has a low-stock threshold
    Then changing that threshold changes whether it appears in the report

  Scenario: Nothing low is reported clearly
    Given all products are above threshold
    Then the report states nothing is running low
```
