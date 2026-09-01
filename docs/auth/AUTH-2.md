### AUTH-2 — RBAC: shopkeeper vs admin roles & guards

| Field | Value |
| :---- | :---- |
| Ticket ID | AUTH-2 |
| Ticket Name | RBAC — shopkeeper vs admin roles & guards |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | AUTH-1 (authenticated users), FND-2 (roles table) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — two roles: shopkeeper (user) and admin (platform builder) |

**Description:** As the platform, I want each user to carry a role (shopkeeper or
admin) and I want routes and endpoints guarded by role, so that shopkeepers cannot
reach admin capabilities and vice versa.

**Acceptance Criteria:**
```gherkin
Feature: Auth pillar — role-based access control

  Scenario: Every user has a role
    Given a user account exists
    Then it has exactly one role of either "shopkeeper" or "admin"

  Scenario: Shopkeeper is blocked from admin endpoints
    Given a logged-in shopkeeper
    When they request an admin-only endpoint or route
    Then access is denied with a forbidden response

  Scenario: Admin is allowed on admin endpoints
    Given a logged-in admin
    When they request an admin-only endpoint or route
    Then access is granted

  Scenario: Guards apply on the server, not just the UI
    Given a route is hidden in the UI for a role
    When that role calls the underlying endpoint directly
    Then the server still enforces the role check and denies unauthorized access
```
