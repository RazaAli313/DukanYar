### SALE-4 — Inventory decrement & out-of-stock flagging

| Field | Value |
| :---- | :---- |
| Ticket ID | SALE-4 |
| Ticket Name | Inventory decrement & out-of-stock flagging |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | SALE-3 (sale writes) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — sale decrements stock; out-of-stock is flagged, never blocks a real sale |

**Description:** As a shopkeeper, I want stock to drop automatically when I record a
sale, so that inventory stays current without me stating counts. If stock would go
negative the sale still records but is flagged.

**Acceptance Criteria:**
```gherkin
Feature: Sales — inventory decrement

  Scenario: Stock decrements on sale
    Given Coke has 24 in stock
    When a sale of 2 Coke is recorded
    Then Coke stock becomes 22

  Scenario: Undoing a sale restores stock
    Given a sale of 2 Coke decremented stock
    When the sale is undone
    Then the 2 units are returned to stock

  Scenario: Out-of-stock is flagged but not blocked
    Given Coke shows 1 in stock
    When a sale of 2 Coke is recorded
    Then the sale still records and the resulting negative/short stock is flagged on screen

  Scenario: Decrement is atomic with the sale
    Given a sale records multiple items
    Then all item decrements and the sale write succeed together or not at all
```
