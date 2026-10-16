### KHATA-4 — Udhaar lookup (by khata# or CNIC fallback)

| Field | Value |
| :---- | :---- |
| Ticket ID | KHATA-4 |
| Ticket Name | Udhaar lookup (by khata# or CNIC fallback) |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | KHATA-2 (ledger balances) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — "Ali ka kitna udhaar hai?"; CNIC fallback when khata# forgotten |

**Description:** As a shopkeeper, I want to ask how much a customer owes and hear the
answer, so that "khata 12 ka kitna udhaar hai?" replies with the balance — and if the
khata number is forgotten, I can look them up by CNIC.

**Acceptance Criteria:**
```gherkin
Feature: Khata — udhaar lookup

  Scenario: Lookup by khata number
    Given khata 12 owes 250
    When the shopkeeper asks the balance for khata 12
    Then the reply states 250 and it is shown on screen

  Scenario: Fallback lookup by CNIC
    Given a customer forgot their khata number
    When the shopkeeper looks them up by CNIC
    Then the correct customer and balance are returned

  Scenario: Unknown customer is handled
    Given a khata number or CNIC with no record
    Then the shopkeeper is told no such customer exists rather than a wrong balance

  Scenario: Lookup is read-only
    Given a balance lookup
    Then no ledger entry or balance change results from asking
```
