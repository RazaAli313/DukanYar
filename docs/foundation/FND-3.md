### FND-3 — App shell, shared config & environment

| Field | Value |
| :---- | :---- |
| Ticket ID | FND-3 |
| Ticket Name | App shell, shared config & environment |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | FND-1 (repo) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — mobile-first PWA, voice-first but multimodal |

**Description:** As an engineer, I want a mobile-first app shell with shared layout,
theming, and centralized environment/secret configuration, so that each pillar
renders inside a consistent frame and reads config the same way without duplicating
setup.

**Acceptance Criteria:**
```gherkin
Feature: Foundation — app shell and shared configuration

  Scenario: Mobile-first shell renders
    Given a user opens the app on a phone-sized viewport
    Then a responsive shell renders with a header and a content area
    And the layout is usable one-handed at typical phone widths

  Scenario: Installable as a PWA
    Given the app is served over the deployment URL
    Then it exposes a web app manifest and a service worker
    And a supported mobile browser offers to install it to the home screen

  Scenario: Centralized environment configuration
    Given the app needs secrets and environment values
    Then both frontend and backend read configuration from a single documented mechanism
    And no secret is hard-coded in source

  Scenario: Shell provides slots for pillars
    Given the TEXT, VOICE, and AUTH pillars each render UI
    Then the shell exposes a place for pillar screens to mount without editing a shared central menu file
```
