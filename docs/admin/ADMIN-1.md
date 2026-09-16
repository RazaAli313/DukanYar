  ### ADMIN-1 — Shops & users management

  | Field | Value |
  | :---- | :---- |
  | Ticket ID | ADMIN-1 |
  | Ticket Name | Shops & users management |
  | Status | Done |
  | Priority | P2 — Normal |
  | Dependencies | AUTH-2 (admin role & guards) |
  | Estimate | BE: TBD \| FE: TBD |
  | Source References | Stakeholder grilling session (this conversation) — admin manages the platform's shops and users |

  **Description:** As an admin, I want to see and manage every shop and user on the
  platform, so that I can support shopkeepers, deactivate abusive accounts, and understand
  adoption.

  **Acceptance Criteria:**
  ```gherkin
  Feature: Admin — shops and users

    Scenario: Admin lists all shops
      Given shops exist across the platform
      When the admin opens the shops screen
      Then all shops are listed with owner, creation date, and activity summary

    Scenario: Admin views users of a shop
      Given a shop has users
      When the admin opens that shop
      Then its users and their roles are shown

    Scenario: Admin can deactivate a shop or user
      Given a shop or user must be suspended
      When the admin deactivates it
      Then that account can no longer log in until reactivated

    Scenario: Only admins reach this screen
      Given a shopkeeper attempts to open the admin shops screen
      Then access is denied
  ```
