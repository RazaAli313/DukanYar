### VOICE-4 — End-to-end voice loop & multimodal parity

| Field | Value |
| :---- | :---- |
| Ticket ID | VOICE-4 |
| Ticket Name | End-to-end voice loop & multimodal parity |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | VOICE-1, VOICE-2, VOICE-3, TEXT-2 |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — voice-first but multimodal; voice and text interchangeable |

**Description:** As a shopkeeper, I want the full speak → hear loop to work in one
flow, and I want voice and text to be interchangeable, so that I can start a thought
by voice and finish it by typing (or vice versa) within the same conversation.

**Acceptance Criteria:**
```gherkin
Feature: Voice pillar — end-to-end loop and multimodal parity

  Scenario: Full voice round-trip
    Given the shopkeeper holds the mic, speaks an Urdu sentence, and releases
    Then the utterance is transcribed, sent to the model, and the reply is both shown and spoken
    And the whole loop completes without manual steps between stages

  Scenario: Voice and text share one conversation
    Given the shopkeeper sends one message by voice and the next by typing
    Then both appear in the same conversation thread in order

  Scenario: Switching channel mid-conversation
    Given a voice message received a reply
    When the shopkeeper types a follow-up
    Then the assistant treats it as a continuation with the prior voice turn as context

  Scenario: A stumble in voice can be recovered by text
    Given a spoken command was mis-transcribed
    Then the shopkeeper can correct it by typing without restarting the conversation
```
