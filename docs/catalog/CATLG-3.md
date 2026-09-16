### CATLG-3 — Proactive low-stock alerts

| Field | Value |
| :---- | :---- |
| Ticket ID | CATLG-3 |
| Ticket Name | Proactive low-stock alerts |
| Status | To Be Done |
| Priority | P3 — Low |
| Dependencies | SALE-4 (stock levels), RPT-4 (low-stock logic) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — proactive low-stock alerts are roadmap beyond the on-demand report |

**Description:** As a shopkeeper, I want to be told when an item is running low without
asking, so that I restock before it runs out — "Coke khatam ho raha hai."

**Acceptance Criteria:**
```gherkin
Feature: Catalog — proactive low-stock alerts

  Scenario: Crossing the threshold raises an alert
    Given a product's stock drops to or below its low-stock threshold
    When the next sale decrements it past the threshold
    Then a low-stock alert is raised for that product

  Scenario: Alert is shown to the shopkeeper
    Given a low-stock alert is raised
    Then the shopkeeper sees it in the app (and, if enabled, is spoken it)

  Scenario: Alert does not repeat endlessly
    Given a product already alerted as low
    Then it does not re-alert on every subsequent sale until restocked above threshold

  Scenario: Restocking clears the alert
    Given a low-stock alert is active
    When the product is restocked above its threshold
    Then the alert clears
```
