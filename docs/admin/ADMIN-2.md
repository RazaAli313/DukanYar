### ADMIN-2 — Voice & transcription monitoring

| Field | Value |
| :---- | :---- |
| Ticket ID | ADMIN-2 |
| Ticket Name | Voice & transcription monitoring |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | AUTH-2 (admin role), VOICE-2 (transcripts), TOOL-2 (actions) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — monitor voice usage and transcription accuracy |

**Description:** As an admin, I want to monitor voice usage and where transcription is
failing, so that I can improve the model prompts, catch Urdu recognition gaps, and prove
the voice pipeline works in the field.

**Acceptance Criteria:**
```gherkin
Feature: Admin — voice and transcription monitoring

  Scenario: Voice usage is visible
    Given voice interactions have occurred
    When the admin opens the monitoring screen
    Then counts of voice vs text interactions over time are shown

  Scenario: Low-confidence transcriptions are surfaced
    Given some transcriptions had low confidence or triggered retries
    Then they are listed so the admin can review recognition quality

  Scenario: Failed actions are traceable
    Given a voice command failed to produce an action
    Then the admin can see the transcript and the failure reason

  Scenario: Monitoring respects privacy scope
    Given monitoring shows interaction metadata
    Then access is restricted to admins and follows the platform's data-handling rules
```
