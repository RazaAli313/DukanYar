### AUTH-3 — Tenancy: per-shop data isolation

| Field | Value |
| :---- | :---- |
| Ticket ID | AUTH-3 |
| Ticket Name | Tenancy — per-shop data isolation |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | AUTH-1 (users linked to shops), FND-2 (shop-scoped tables) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — production-ready multi-tenant; khata data is shop-scoped |

**Description:** As a shopkeeper, I want my shop's data fully isolated from every
other shop, so that no other user can ever read or change my sales, conversations, or
customers. As the platform, I want this enforced at the data layer, not just in
application code.

**Acceptance Criteria:**
```gherkin
Feature: Auth pillar — tenancy and data isolation

  Scenario: Data is scoped to the acting shop
    Given a shopkeeper belongs to shop A
    When they read or write shop-scoped data
    Then only shop A's rows are visible or affected

  Scenario: Cross-shop access is impossible
    Given a shopkeeper from shop A
    When a request attempts to read shop B's data by id
    Then the request returns nothing (or is denied), never shop B's data

  Scenario: Isolation is enforced at the data layer
    Given shop-scoped tables
    Then row-level access rules restrict rows by the acting shop
    And the rules hold even if an application query forgets to filter by shop

  Scenario: Admin oversight is explicit, not accidental
    Given an admin needs cross-shop visibility later
    Then any cross-shop read is an intentional admin-role capability, never available to a shopkeeper
```
