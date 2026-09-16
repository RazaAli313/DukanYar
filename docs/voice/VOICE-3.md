### VOICE-3 — Text-to-speech (TTS) reply playback

| Field | Value |
| :---- | :---- |
| Ticket ID | VOICE-3 |
| Ticket Name | Text-to-speech (TTS) reply playback |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | VOICE-2 (transcript → reply), TEXT-2 (assistant reply text) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation); Alibaba Cloud AI Hackathon 2026 research (Qwen realtime does NOT synthesize Urdu output — voice source must be swappable) |

**Description:** As a shopkeeper, I want to hear the assistant's reply spoken aloud,
so that I don't have to look at the screen while serving a customer. Because the Urdu
voice source is a known risk, the spoken-reply path must sit behind an adapter that
can be swapped without changing capture or STT.

**Acceptance Criteria:**
```gherkin
Feature: Voice pillar — spoken reply playback

  Scenario: Assistant reply is spoken aloud
    Given the assistant returns a text reply
    When text-to-speech is invoked
    Then the reply is played back as audio to the shopkeeper

  Scenario: Voice source is behind a swappable adapter
    Given the Urdu voice provider may change (Alibaba lacks Urdu speech output)
    Then the text-to-speech provider is accessed through an adapter interface
    And swapping the provider requires no change to capture (VOICE-1) or STT (VOICE-2)

  Scenario: Reply is always shown on screen too
    Given voice output may be unavailable or muted
    Then the assistant reply is always displayed as text in addition to being spoken

  Scenario: Playback failure degrades gracefully
    Given text-to-speech fails
    Then the shopkeeper still sees the reply as text and the app does not crash or hang
```
