### VOICE-1 — Push-to-talk capture

| Field | Value |
| :---- | :---- |
| Ticket ID | VOICE-1 |
| Ticket Name | Push-to-talk capture |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | FND-3 (app shell) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — push-to-talk chosen for MVP over wake-word |

**Description:** As a shopkeeper, I want to press and hold a big mic button to record
what I say and release to send, so that I can capture a command reliably in a noisy
shop without accidental triggers.

**Acceptance Criteria:**
```gherkin
Feature: Voice pillar — push-to-talk capture

  Scenario: Hold to record, release to send
    Given the shopkeeper is on a screen with the mic button
    When they press and hold the button and speak
    Then audio is captured while held
    And releasing the button ends capture and submits the audio

  Scenario: Microphone permission is requested clearly
    Given the app has not yet been granted microphone access
    When the shopkeeper first presses the mic button
    Then the browser permission prompt is triggered
    And if denied, a clear message explains that voice needs mic access

  Scenario: Recording state is visible
    Given the shopkeeper is holding the mic button
    Then a clear recording indicator is shown for the duration of capture

  Scenario: Accidental tap does not send empty audio
    Given the shopkeeper taps the button momentarily with no speech
    Then no empty or near-empty recording is submitted
```
