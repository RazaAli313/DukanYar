### TOOL-3 — Risk-tiered confirmation & undo framework

| Field | Value |
| :---- | :---- |
| Ticket ID | TOOL-3 |
| Ticket Name | Risk-tiered confirmation & undo framework |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | TOOL-2 (orchestration loop) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — money-in/repayment needs approval; logging/expenses commit + undo |

**Description:** As a shopkeeper, I want risky money-in actions to be confirmed before
they commit, and routine logging to commit immediately with a quick undo, so that my
ledger is protected without every action costing an extra step.

**Acceptance Criteria:**
```gherkin
Feature: Tool-calling — risk-tiered confirmation and undo

  Scenario: Money-in actions require approval before commit
    Given a tool is classified as approval-required (e.g. udhaar repayment, payment/finance)
    When the model wants to call it
    Then the shopkeeper is shown the parsed action and must confirm before it writes

  Scenario: Logging actions commit then allow undo
    Given a tool is classified as commit-with-undo (e.g. udhaar logging, expense)
    When it is called
    Then it commits immediately and a prominent undo is available

  Scenario: Undo reverses the last committed action
    Given a commit-with-undo action just committed
    When the shopkeeper undoes it
    Then its effects are reversed and the ledger returns to its prior state

  Scenario: A tool declares its own risk tier
    Given each tool declares approval-required or commit-with-undo
    Then the framework enforces that tier without per-call special-casing
```
