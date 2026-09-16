### FND-1 — Scaffold monorepo, CI & deployment skeleton

| Field | Value |
| :---- | :---- |
| Ticket ID | FND-1 |
| Ticket Name | Scaffold monorepo, CI & deployment skeleton |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | None |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation); Alibaba Cloud AI Hackathon 2026 (deploy on Alibaba Cloud, open-source repo) |

**Description:** As an engineer, I want a single deployed monorepo with a frontend
app, a backend service, and a CI pipeline, so that the three Phase-1 pillars have a
common place to build and a live URL to demo from day 1.

**Acceptance Criteria:**
```gherkin
Feature: Foundation — monorepo scaffold, CI and deployment

  Scenario: Monorepo contains both apps
    Given a fresh clone of the repository
    Then it contains a frontend application and a backend service in a single repo
    And each has its own dependency manifest and a documented "run locally" command

  Scenario: Repository is open-source compliant
    Given the hackathon requires an open-source submission
    Then the repository contains an OSI-approved LICENSE file at its root

  Scenario: CI runs on every push
    Given an engineer pushes a commit to any branch
    When CI runs
    Then it installs dependencies, builds both apps, and reports pass or fail on the commit

  Scenario: Deployed skeleton is reachable on Alibaba Cloud
    Given the skeleton has been deployed
    When a user opens the deployment URL
    Then the frontend loads a placeholder page and can reach a backend health endpoint that returns OK
```
