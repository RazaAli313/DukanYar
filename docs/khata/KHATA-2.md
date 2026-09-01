### KHATA-2 — Log udhaar tool (goods on credit)

| Field | Value |
| :---- | :---- |
| Ticket ID | KHATA-2 |
| Ticket Name | Log udhaar tool (goods on credit) |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | KHATA-1 (customers), TOOL-2 (orchestration), TOOL-3 (commit/undo), SALE-3 (credit sale hand-off) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — khata# present ⇒ udhaar; logging commits + undo (not approval) |

**Description:** As a shopkeeper, I want giving goods on credit to add to a customer's
udhaar balance immediately, so that "khata 12 pe 450 udhaar" raises khata 12's balance
by 450 with a quick undo if I misspoke.

**Acceptance Criteria:**
```gherkin
Feature: Khata — log udhaar

  Scenario: Udhaar increases the customer balance
    Given khata 12 currently owes 0
    When 450 of udhaar is logged against khata 12
    Then khata 12's balance becomes 450

  Scenario: Ledger entry is recorded
    Given udhaar is logged
    Then a ledger entry records the amount, timestamp, and link to the originating sale if any

  Scenario: Logging commits with undo, not approval
    Given udhaar logging is a commit-with-undo action
    When it is logged
    Then it commits immediately and can be undone

  Scenario: Undo reverses the balance
    Given 450 was just logged to khata 12
    When the shopkeeper undoes it
    Then khata 12's balance returns to its prior value
```
