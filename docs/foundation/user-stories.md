# User Stories — foundation FND

## FND-1 — Scaffold monorepo, CI & deployment skeleton
**As an** engineer
**I want** a single deployed monorepo with a frontend app, a backend service, and a CI pipeline
**So that** the three Phase-1 pillars have a common place to build and a live URL to demo from day 1

**Acceptance criteria** (from FND-1.md):
- A fresh clone of the repository contains a frontend application and a backend service in a single repo, each with its own dependency manifest and a documented "run locally" command
- The repository contains an OSI-approved LICENSE file at its root (hackathon open-source requirement)
- On every push to any branch, CI installs dependencies, builds both apps, and reports pass or fail on the commit
- Once deployed, opening the deployment URL loads a placeholder frontend page and can reach a backend health endpoint that returns OK

_Tickets: docs/foundation/FND-1.md_

## FND-2 — Database schema & migrations (Phase-1 tables)
**As an** engineer
**I want** the Phase-1 database tables created through versioned migrations
**So that** the AUTH, TEXT, and VOICE pillars have the shops, users, roles, and conversation storage they need

**Acceptance criteria** (from FND-2.md):
- Running the migration command against a clean database creates all Phase-1 tables, and re-running it makes no further changes (idempotent)
- A "shops" table, a "users" table, and a "roles" table exist, and a user row references exactly one shop and one role
- A "conversations" table and a "messages" table exist, and a message records its conversation, its sender (user or assistant), its text, and its input channel (text or voice)
- The Phase-1 schema is introduced in a single timestamped migration file owned by this epic, and no other epic's migration file is edited
- No sales, inventory, udhaar, or expense tables are created in this migration — feature tables are intentionally deferred to Phase 3

_Tickets: docs/foundation/FND-2.md_

## FND-3 — App shell, shared config & environment
**As an** engineer
**I want** a mobile-first app shell with shared layout, theming, and centralized environment/secret configuration
**So that** each pillar renders inside a consistent frame and reads config the same way without duplicating setup

**Acceptance criteria** (from FND-3.md):
- Opening the app on a phone-sized viewport renders a responsive shell with a header and a content area, usable one-handed at typical phone widths
- The app is served over the deployment URL with a web app manifest and a service worker, and a supported mobile browser offers to install it to the home screen
- Both frontend and backend read configuration from a single documented mechanism, with no secret hard-coded in source
- The shell exposes a place for the TEXT, VOICE, and AUTH pillar screens to mount without editing a shared central menu file

_Tickets: docs/foundation/FND-3.md_
