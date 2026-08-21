### TEXT-1 — Chat input UI

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-1 |
| Ticket Name | Chat input UI |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | FND-3 (app shell) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — multimodal, mobile-first |

**Description:** As a shopkeeper, I want to type a message and see the conversation
as a chat thread, so that I can interact with the assistant by text when voice isn't
practical (noisy shop, quiet needed, or to correct a misheard command).

**Acceptance Criteria:**
```gherkin
Feature: Text pillar — chat input UI

  Scenario: Sending a typed message
    Given the shopkeeper is on the chat screen
    When they type a message and submit it
    Then their message appears in the thread as a "user" bubble
    And the input field clears and is ready for the next message

  Scenario: Assistant reply appears in the thread
    Given the shopkeeper has sent a message
    When the assistant reply is received
    Then it appears in the thread as an "assistant" bubble beneath their message

  Scenario: Pending state while waiting
    Given the shopkeeper has sent a message
    When the reply has not yet arrived
    Then a visible pending indicator is shown until the reply arrives or an error is displayed

  Scenario: Right-to-left rendering for Urdu
    Given the shopkeeper writes in Urdu script
    Then that message renders right-to-left and remains readable
```
