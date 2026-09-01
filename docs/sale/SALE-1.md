### SALE-1 — Product catalog & seed data

| Field | Value |
| :---- | :---- |
| Ticket ID | SALE-1 |
| Ticket Name | Product catalog & seed data |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | FND-2 (migration convention), TOOL-1 (registry) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — pre-seeded ~15–20 product catalog for the demo; cost price stored for later profit math |

**Description:** As a shopkeeper, I want a catalog of my products with price and stock,
so that sales can resolve items and track quantities. For the demo the catalog is
pre-seeded with a realistic set so "2 coke" always resolves.

**Acceptance Criteria:**
```gherkin
Feature: Sales — product catalog

  Scenario: Products table with price, stock and cost
    Given the catalog migration has run
    Then a products table exists with name, sale price, stock quantity, and cost price
    And products are scoped to a shop

  Scenario: Demo catalog is seeded
    Given a fresh demo shop
    When seed data is applied
    Then roughly 15–20 realistic products exist with sensible prices and opening stock

  Scenario: Products carry common aliases
    Given a product like "Coca-Cola 345ml"
    Then it can store alternate names (e.g. "coke", "thanda") to aid later resolution

  Scenario: Catalog is viewable
    Given a shopkeeper opens the inventory screen
    Then they see each product with its current stock and price
```
