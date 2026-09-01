### TEXT-4 — Urdu / Roman / English handling & assistant persona

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-4 |
| Ticket Name | Urdu / Roman / English handling & assistant persona |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | TEXT-2 (model integration) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — Urdu-native, code-switching, "AI shopkeeper employee" persona |

**Description:** As a shopkeeper, I want the assistant to understand how I actually
speak — Urdu mixed with Roman-Urdu and English product words — and to reply like a
helpful shop employee, so that the interaction feels natural rather than like a
foreign chatbot.

**Acceptance Criteria:**
```gherkin
Feature: Text pillar — language handling and persona

  Scenario: Understands code-switched input
    Given the shopkeeper writes "2 coke aur 1 chips reh gaye"
    When the message is processed
    Then the assistant responds coherently to the mixed Urdu-English message

  Scenario: Replies in the shopkeeper's language
    Given the shopkeeper writes in Urdu (or Roman-Urdu)
    Then the assistant's reply is in the same language register, not defaulted to formal English

  Scenario: Employee persona is applied
    Given a system persona defines a polite, concise shop-employee assistant
    When the assistant replies
    Then its tone is short, respectful, and shopkeeper-appropriate rather than verbose or generic

  Scenario: Handles unclear input gracefully
    Given the shopkeeper's message is ambiguous or unreadable
    Then the assistant asks a short clarifying question instead of guessing
```
