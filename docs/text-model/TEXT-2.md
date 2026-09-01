### TEXT-2 — Model integration & streaming reply

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-2 |
| Ticket Name | Model integration & streaming reply |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | FND-1 (backend), FND-2 (conversations/messages tables) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation); Alibaba Cloud AI Hackathon 2026 (use Qwen models) |

**Description:** As a shopkeeper, I want the assistant's replies to come from the
language model, so that I get relevant natural answers. As Dev 2 (voice), I want this
exposed as a single conversation endpoint, so that voice can reuse it by sending
transcribed text.

**Acceptance Criteria:**
```gherkin
Feature: Text pillar — model integration

  Scenario: User message reaches the model and returns a reply
    Given a user message is submitted to the conversation endpoint
    When the backend calls the language model
    Then the model's reply is returned to the caller and rendered in the thread

  Scenario: Endpoint is channel-agnostic
    Given both the text UI and the voice pillar call the same conversation endpoint
    When either sends a text message
    Then the endpoint behaves identically regardless of whether the source was typed or transcribed

  Scenario: Reply streams incrementally
    Given the model supports streaming
    When a reply is being generated
    Then partial text is delivered progressively rather than only after the full reply is ready

  Scenario: Model or network failure is handled
    Given the model call fails or times out
    When the backend cannot produce a reply
    Then the caller receives a clear error and the UI shows a retry affordance without losing the typed message
```
