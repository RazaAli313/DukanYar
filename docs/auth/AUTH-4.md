### AUTH-4 — Role-based landing (shopkeeper app vs admin console)

| Field | Value |
| :---- | :---- |
| Ticket ID | AUTH-4 |
| Ticket Name | Role-based landing (shopkeeper app vs admin console) |
| Status | To Be Done |
| Priority | P2 — Normal |
| Dependencies | AUTH-2 (roles & guards) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — shopkeepers use the counter app; admins (platform builders) use a separate console |

**Description:** As a user, I want to land in the right place for my role after login —
shopkeepers in the counter app, admins in the admin console — so that each role sees
only what is relevant to them.

**Acceptance Criteria:**
```gherkin
Feature: Auth pillar — role-based landing

  Scenario: Shopkeeper lands in the counter app
    Given a shopkeeper logs in
    Then they are taken to the shopkeeper app surface (chat/voice screen)

  Scenario: Admin lands in the admin console
    Given an admin logs in
    Then they are taken to the admin console surface

  Scenario: Deep-linking respects role
    Given a shopkeeper opens an admin-console URL directly
    Then they are redirected away and do not see admin content

  Scenario: Unauthenticated users are sent to login
    Given a signed-out visitor opens any protected URL
    Then they are redirected to the login screen
```
