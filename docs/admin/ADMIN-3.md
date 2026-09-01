### ADMIN-3 — Audit log & system health

| Field | Value |
| :---- | :---- |
| Ticket ID | ADMIN-3 |
| Ticket Name | Audit log & system health |
| Status | To Be Done |
| Priority | P3 — Low |
| Dependencies | AUTH-2 (admin role), FND-2 (audit table) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — production-ready platform; audit and health |

**Description:** As an admin, I want an audit trail of significant actions and a basic
system-health view, so that I can investigate issues and confirm the platform is up.

**Acceptance Criteria:**
```gherkin
Feature: Admin — audit and health

  Scenario: Significant actions are audited
    Given users perform account and money-affecting actions
    Then an audit entry records who did what and when

  Scenario: Audit log is searchable
    Given audit entries exist
    When the admin filters by shop, user, or action type
    Then only matching entries are shown

  Scenario: Basic health is visible
    Given the admin opens the health view
    Then it shows service status and recent error rate at a glance

  Scenario: Audit is append-only to admins
    Given an audit entry exists
    Then it cannot be edited or deleted through the app, only viewed
```
