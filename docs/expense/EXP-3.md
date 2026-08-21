### EXP-3 — Expense list & review

| Field | Value |
| :---- | :---- |
| Ticket ID | EXP-3 |
| Ticket Name | Expense list & review |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | EXP-2 (expenses recorded) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — multimodal review on screen |

**Description:** As a shopkeeper, I want to see my recent expenses on screen, so that I
can review and correct what was logged.

**Acceptance Criteria:**
```gherkin
Feature: Expenses — list and review

  Scenario: Recent expenses are listed
    Given expenses have been logged
    When the shopkeeper opens the expenses screen
    Then their expenses are shown most recent first with amount, category and date

  Scenario: List is shop-scoped
    Given multiple shops have expenses
    Then a shopkeeper sees only their own shop's expenses

  Scenario: An expense can be removed
    Given a wrong expense is in the list
    Then the shopkeeper can delete it
```
