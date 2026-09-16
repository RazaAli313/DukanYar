### AUTH-1 — Authentication (signup, login, sessions)

| Field | Value |
| :---- | :---- |
| Ticket ID | AUTH-1 |
| Ticket Name | Authentication (signup, login, sessions) |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | FND-2 (users/shops tables) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — shopkeeper registers a shop; production-ready |

**Description:** As a shopkeeper, I want to create an account for my shop and log in,
so that my data is private to me and persists across sessions and devices.

**Acceptance Criteria:**
```gherkin
Feature: Auth pillar — authentication

  Scenario: Shopkeeper signs up and a shop is created
    Given a new shopkeeper completes signup
    Then a user account is created and linked to a newly created shop
    And they are logged in

  Scenario: Returning user logs in
    Given an existing user with valid credentials
    When they log in
    Then a session is established and they reach their app

  Scenario: Invalid credentials are rejected
    Given a login attempt with wrong credentials
    Then access is denied with a clear message and no session is created

  Scenario: Session persists and can be ended
    Given a logged-in user
    When they reopen the app
    Then their session is still valid until it expires or they log out
    And logging out ends the session and requires login again
```
