### TOOL-2 — Model tool-calling orchestration loop

| Field | Value |
| :---- | :---- |
| Ticket ID | TOOL-2 |
| Ticket Name | Model tool-calling orchestration loop |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | TOOL-1 (registry), TEXT-2 (conversation endpoint) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — modular pipeline, one utterance can trigger a chain of actions |

**Description:** As a shopkeeper, I want a single message to trigger the right
action(s) and get a reply, so that saying "khata 12 pe 2 coke 450 udhaar" records the
sale, updates inventory, and logs the udhaar in one turn. As the platform, the loop
must select tools, execute them, and summarize the result back to the model for a
natural reply.

**Acceptance Criteria:**
```gherkin
Feature: Tool-calling — orchestration loop

  Scenario: A message triggers the correct tool
    Given a registered tool matches the shopkeeper's intent
    When they send a message
    Then the model selects that tool with parameters extracted from the message

  Scenario: One utterance can trigger a chain of tools
    Given a message implies several actions (sale + inventory + udhaar)
    When the loop runs
    Then all required tools execute and the reply reflects the combined result

  Scenario: Same loop serves text and voice
    Given a message arrives from either the text UI or the voice pillar
    Then it flows through the identical orchestration loop

  Scenario: A tool failure is reported, not swallowed
    Given a tool raises an error mid-loop
    Then the shopkeeper is told what failed and no partial claim of success is made
```
