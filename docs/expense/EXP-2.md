### EXP-2 — Log-expense tool (commit + undo)

| Field | Value |
| :---- | :---- |
| Ticket ID | EXP-2 |
| Ticket Name | Log-expense tool (commit + undo) |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | EXP-1 (schema), TOOL-2 (orchestration), TOOL-3 (commit/undo) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — voice-log expense, commit + undo |

**Description:** As a shopkeeper, I want to log an expense by voice or text, so that
"bijli ka bill 3000" records a 3000 expense immediately with a quick undo.

**Acceptance Criteria:**
```gherkin
Feature: Expenses — log expense

  Scenario: Expense logged from a message
    Given the shopkeeper says "bijli ka bill 3000"
    When the log-expense tool runs
    Then a 3000 expense is recorded with a category inferred as utilities/bijli if possible

  Scenario: Commit with undo
    Given an expense is logged
    Then it commits immediately and can be undone from the confirmation card

  Scenario: Missing amount is queried
    Given the shopkeeper mentions an expense with no amount
    Then the assistant asks for the amount instead of recording zero
```
