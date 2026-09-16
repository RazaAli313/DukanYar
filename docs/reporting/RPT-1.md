### RPT-1 — Reporting views (owned read layer)

| Field | Value |
| :---- | :---- |
| Ticket ID | RPT-1 |
| Ticket Name | Reporting views (owned read layer) |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | SALE, KHATA, EXP tables exist |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — read across contexts via views this epic owns, to avoid coupling |

**Description:** As an engineer, I want reporting to read other modules only through
DB views defined and owned by this epic, so that reporting stays decoupled and a schema
change elsewhere cannot silently break its queries.

**Acceptance Criteria:**
```gherkin
Feature: Reporting — owned read layer

  Scenario: Reporting reads via its own views
    Given reporting needs sales, udhaar, and expense data
    Then it queries DB views defined in this epic's migration, not other epics' tables directly

  Scenario: Views are shop-scoped
    Given reporting views return rows
    Then every row is scoped to the acting shop

  Scenario: A view isolates upstream changes
    Given an upstream table adds or renames a column behind its view's contract
    Then reporting queries continue to work as long as the view's shape is preserved
```
