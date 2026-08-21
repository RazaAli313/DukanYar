### TOOL-4 — On-screen action confirmation

| Field | Value |
| :---- | :---- |
| Ticket ID | TOOL-4 |
| Ticket Name | On-screen action confirmation |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | TOOL-2 (orchestration loop) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — always show the parsed result (amount, item, customer) on screen so money is never ambiguous |

**Description:** As a shopkeeper, I want every action the AI takes shown clearly on
screen — amount, items, customer/khata — so that money is never ambiguous even when
the spoken reply is brief or the Urdu voice is unavailable.

**Acceptance Criteria:**
```gherkin
Feature: Tool-calling — on-screen action confirmation

  Scenario: Parsed action is rendered visually
    Given the model executes an action from a message
    Then the app shows a structured card of what was recorded (amount, items, khata/customer)

  Scenario: Screen output accompanies every voice reply
    Given a spoken reply is produced
    Then the same information is also shown on screen, never voice-only

  Scenario: Ambiguous parse is highlighted
    Given a field was uncertain (e.g. unknown item, unclear amount)
    Then it is visually flagged so the shopkeeper can correct it

  Scenario: Confirmation card exposes undo or approve
    Given an action was committed (undo) or awaits approval (approve)
    Then the matching control is present on the confirmation card
```
