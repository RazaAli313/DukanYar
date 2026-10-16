### CATLG-2 — Adjust / restock by voice

| Field | Value |
| :---- | :---- |
| Ticket ID | CATLG-2 |
| Ticket Name | Adjust / restock by voice |
| Status | To Be Done |
| Priority | P3 — Low |
| Dependencies | SALE-1 (catalog), SALE-2 (item resolution), TOOL-3 (confirm/undo) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — restock/adjust ("Coke ki 24 bottle aur aa gayi") makes inventory feel alive |

**Description:** As a shopkeeper, I want to restock or correct a product by voice — "Coke
ki 24 bottle aur aa gayi" or "Coke ab 60 ka" — so that inventory and prices stay current
without typing.

**Acceptance Criteria:**
```gherkin
Feature: Catalog — adjust and restock

  Scenario: Restock increases stock
    Given Coke has 22 in stock
    When the shopkeeper says 24 more Coke arrived
    Then Coke stock becomes 46

  Scenario: Price update changes the price
    Given Coke sells for 50
    When the shopkeeper says Coke is now 60
    Then Coke's price becomes 60 for future sales

  Scenario: Stock correction overwrites the count
    Given the shopkeeper counts shelf stock and states the true number
    Then the product's stock is set to that number

  Scenario: Adjust resolves to an existing product
    Given the spoken product name is fuzzy
    Then it resolves to the existing catalog item (reusing sale item resolution), not a new product
```
