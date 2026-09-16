### FND-2 — Database schema & migrations (Phase-1 tables)

| Field | Value |
| :---- | :---- |
| Ticket ID | FND-2 |
| Ticket Name | Database schema & migrations (Phase-1 tables) |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | FND-1 (repo + backend service) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — khata#/CNIC identity model, two roles (shopkeeper/admin), conversation history |

**Description:** As an engineer, I want the Phase-1 database tables created through
versioned migrations, so that the AUTH, TEXT, and VOICE pillars have the shops,
users, roles, and conversation storage they need. Feature tables (sales, inventory,
udhaar, expenses) are intentionally out of scope here and deferred to Phase 3.

**Acceptance Criteria:**
```gherkin
Feature: Foundation — Phase-1 database schema via migrations

  Scenario: Migrations are versioned and repeatable
    Given a clean database
    When the migration command is run
    Then all Phase-1 tables are created
    And re-running the command makes no further changes (idempotent)

  Scenario: Core identity and tenancy tables exist
    Given migrations have run
    Then a "shops" table, a "users" table, and a "roles" table exist
    And a user row references exactly one shop and one role

  Scenario: Conversation storage exists for text and voice
    Given migrations have run
    Then a "conversations" table and a "messages" table exist
    And a message records its conversation, its sender (user or assistant), its text, and its input channel (text or voice)

  Scenario: One migration file owned by this epic
    Given the repository migration convention of one file per epic
    Then the Phase-1 schema is introduced in a single timestamped migration file
    And no other epic's migration file is edited

  Scenario: Feature tables are deferred
    Given Phase 1 excludes tool-calling and business logic
    Then no sales, inventory, udhaar, or expense tables are created in this migration
```
