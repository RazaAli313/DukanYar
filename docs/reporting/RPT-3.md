### RPT-3 — Outstanding udhaar summary tool

| Field | Value |
| :---- | :---- |
| Ticket ID | RPT-3 |
| Ticket Name | Outstanding udhaar summary tool |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | RPT-1 (views), TOOL-2 (orchestration) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — total outstanding udhaar across customers |

**Description:** As a shopkeeper, I want to know the total udhaar owed to me across all
customers, so that I know how much money is out on credit.

**Acceptance Criteria:**
```gherkin
Feature: Reporting — outstanding udhaar

  Scenario: Total outstanding udhaar is reported
    Given several customers carry balances
    When the shopkeeper asks how much udhaar is outstanding
    Then the reply states the sum of all customer balances for the shop

  Scenario: Top debtors can be listed
    Given customers with balances
    When the shopkeeper asks who owes the most
    Then the largest balances are listed with khata numbers

  Scenario: Zero outstanding is reported clearly
    Given no customer owes anything
    Then the reply states nothing is outstanding
```
