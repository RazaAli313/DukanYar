### TEXT-3 — Conversation persistence & history

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-3 |
| Ticket Name | Conversation persistence & history |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | TEXT-2 (conversation endpoint), FND-2 (conversations/messages tables), AUTH-3 (shop scoping) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — conversation history, multi-tenant |

**Description:** As a shopkeeper, I want my conversation saved and reloaded, so that I
can see earlier messages after closing and reopening the app, and so the assistant
can use recent context within a conversation.

**Acceptance Criteria:**
```gherkin
Feature: Text pillar — conversation persistence

  Scenario: Messages are persisted
    Given the shopkeeper sends a message and receives a reply
    Then both the user message and the assistant reply are stored against their conversation

  Scenario: History reloads on return
    Given the shopkeeper has an existing conversation
    When they reopen the app
    Then the previous messages are shown in order

  Scenario: History is scoped to the shop
    Given two shops each have conversations
    When a shopkeeper loads their history
    Then only their own shop's messages are returned, never another shop's

  Scenario: Recent context is available to the model
    Given a conversation has prior messages
    When a new message is sent
    Then the backend includes recent prior turns as context in the model call
```
