### SALE-3 — Record-sale tool (cash vs udhaar by khata presence)

| Field | Value |
| :---- | :---- |
| Ticket ID | SALE-3 |
| Ticket Name | Record-sale tool (cash vs udhaar by khata presence) |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | SALE-2 (resolved items), TOOL-2 (orchestration), TOOL-3 (commit/undo) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — khata# present ⇒ udhaar, absent ⇒ cash; spoken amount is source of truth; commit + undo |

**Description:** As a shopkeeper, I want to record a sale by voice or text with the
amount I state, so that "2 coke 1 chips 450" logs a sale of 450. If I name a khata
number the sale is credit (linked via KHATA); otherwise it is a cash sale.

**Acceptance Criteria:**
```gherkin
Feature: Sales — record a sale

  Scenario: Cash sale when no khata number is given
    Given the shopkeeper says an item list and amount with no khata number
    When the record-sale tool runs
    Then a cash sale is logged with its line items and the stated total

  Scenario: Credit sale when a khata number is given
    Given the shopkeeper names a khata number
    Then the sale is recorded as udhaar and handed to the khata ledger for that customer

  Scenario: Spoken amount is the recorded total
    Given the shopkeeper states 450 for the sale
    Then 450 is stored as the sale total regardless of catalog price sums

  Scenario: Sale commits with undo
    Given a sale is recorded
    Then it commits immediately and can be undone from the confirmation card
```
