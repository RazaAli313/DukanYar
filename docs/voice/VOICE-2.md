### VOICE-2 — Speech-to-text (STT) integration

| Field | Value |
| :---- | :---- |
| Ticket ID | VOICE-2 |
| Ticket Name | Speech-to-text (STT) integration |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | VOICE-1 (captured audio) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation); Alibaba Cloud AI Hackathon 2026 research (Qwen speech input supports Urdu) |

**Description:** As a shopkeeper, I want my spoken Urdu turned into text, so that the
assistant can process what I said through the same conversation endpoint the text
pillar uses.

**Acceptance Criteria:**
```gherkin
Feature: Voice pillar — speech-to-text

  Scenario: Spoken Urdu is transcribed
    Given the shopkeeper submits a recording of an Urdu sentence
    When the audio is sent to the speech-to-text service
    Then a text transcript of the utterance is returned

  Scenario: Transcript is shown for confirmation
    Given a transcript has been produced
    Then it is displayed to the shopkeeper as the recognized text before or alongside the assistant's reply

  Scenario: Transcript feeds the shared conversation endpoint
    Given a transcript has been produced
    Then it is submitted to the same conversation endpoint that typed messages use, tagged as the voice channel

  Scenario: Unrecognizable audio is handled
    Given the recording is silent or unintelligible
    When transcription returns empty or low-confidence text
    Then the shopkeeper is prompted to try again rather than sending garbage to the model
```
