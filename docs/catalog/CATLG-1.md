### CATLG-1 — Add product by voice

| Field | Value |
| :---- | :---- |
| Ticket ID | CATLG-1 |
| Ticket Name | Add product by voice |
| Status | To Be Done |
| Priority | P3 — Low |
| Dependencies | SALE-1 (catalog), TOOL-2 (orchestration), TOOL-3 (confirm/undo) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — voice catalog building is roadmap |

**Description:** As a shopkeeper, I want to add a new product by voice — "naya item Lays
50 rupay 30 packet" — so that I can grow my catalog without typing. Because this writes
the catalog everything depends on, the parse is confirmed before commit.

**Acceptance Criteria:**
```gherkin
Feature: Catalog — add product by voice

  Scenario: New product is created from a spoken description
    Given the shopkeeper says a product name, price, and opening quantity
    When the add-product tool runs
    Then a confirmation card shows the parsed name, price, and quantity for approval

  Scenario: Approved add creates the product
    Given the parsed product is approved
    Then it is created in the catalog with the stated price and opening stock

  Scenario: Duplicate product is detected
    Given a product with a very similar name already exists
    Then the shopkeeper is warned and asked whether to add or adjust the existing one

  Scenario: Missing fields are queried
    Given the spoken description lacks a price or quantity
    Then the assistant asks for the missing field instead of guessing
```
