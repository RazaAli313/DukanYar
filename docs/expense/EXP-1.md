### EXP-1 — Expenses schema & categories

| Field | Value |
| :---- | :---- |
| Ticket ID | EXP-1 |
| Ticket Name | Expenses schema & categories |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | FND-2 (migration convention), AUTH-3 (shop scoping) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — expense tracking |

**Description:** As a shopkeeper, I want expenses stored with an amount, an optional
category, and a date, so that money going out is captured and can later feed profit
summaries.

**Acceptance Criteria:**
```gherkin
Feature: Expenses — schema

  Scenario: Expenses table exists and is shop-scoped
    Given the expense migration has run
    Then an expenses table exists with amount, optional category, note, and date
    And each expense belongs to exactly one shop

  Scenario: Sensible default categories exist
    Given a shopkeeper logs an expense without naming a category
    Then it is stored as uncategorized rather than rejected

  Scenario: Amount is required and positive
    Given an expense is created
    Then it must have a positive amount
```
