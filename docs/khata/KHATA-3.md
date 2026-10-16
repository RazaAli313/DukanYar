### KHATA-3 — Udhaar repayment tool (approval-gated)

| Field | Value |
| :---- | :---- |
| Ticket ID | KHATA-3 |
| Ticket Name | Udhaar repayment tool (approval-gated) |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | KHATA-2 (ledger balances), TOOL-3 (approval framework) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — money-in/repayment requires approval before commit; giving vs repaying distinguished by verb/intent |

**Description:** As a shopkeeper, I want a customer's repayment confirmed before it
posts, so that a mis-heard amount on money coming in doesn't start a dispute. "khata 12
ne 200 jama karaye" should ask me to approve before reducing the balance.

**Acceptance Criteria:**
```gherkin
Feature: Khata — udhaar repayment

  Scenario: Repayment is read back for approval
    Given the shopkeeper says a customer repaid an amount
    When the repayment tool is invoked
    Then the parsed customer and amount are shown and the shopkeeper must approve before it commits

  Scenario: Approved repayment reduces the balance
    Given khata 12 owes 450
    When a repayment of 200 is approved
    Then khata 12's balance becomes 250 and a payment entry is recorded

  Scenario: Rejected repayment changes nothing
    Given a repayment awaits approval
    When the shopkeeper rejects it
    Then no payment is recorded and the balance is unchanged

  Scenario: Repayment is distinguished from giving udhaar
    Given both mention a khata number
    When the intent is "repaid / jama" rather than "gave / diye"
    Then the repayment (money-in) path is used, not the logging path
```
