# User Stories — auth AUTH

## AUTH-1 — Authentication (signup, login, sessions)
**As a** shopkeeper
**I want** to create an account for my shop and log in
**So that** my data is private to me and persists across sessions and devices

**Acceptance criteria** (from AUTH-1.md):
- When a new shopkeeper completes signup, a user account is created and linked to a newly created shop, and they are logged in
- When an existing user with valid credentials logs in, a session is established and they reach their app
- A login attempt with wrong credentials is denied with a clear message and no session is created
- A logged-in user's session stays valid across reopening the app until it expires or they log out, and logging out ends the session and requires login again

_Tickets: docs/auth/AUTH-1.md_

## AUTH-2 — RBAC: shopkeeper vs admin roles & guards
**As the** platform
**I want** each user to carry a role (shopkeeper or admin) with routes and endpoints guarded by role
**So that** shopkeepers cannot reach admin capabilities and vice versa

**Acceptance criteria** (from AUTH-2.md):
- Every user account has exactly one role of either "shopkeeper" or "admin"
- When a logged-in shopkeeper requests an admin-only endpoint or route, access is denied with a forbidden response
- When a logged-in admin requests an admin-only endpoint or route, access is granted
- Even when a route is hidden in the UI for a role, the server still enforces the role check and denies unauthorized access if that role calls the underlying endpoint directly

_Tickets: docs/auth/AUTH-2.md_

## AUTH-3 — Tenancy: per-shop data isolation
**As a** shopkeeper
**I want** my shop's data fully isolated from every other shop, enforced at the data layer rather than only in application code
**So that** no other user can ever read or change my sales, conversations, or customers

**Acceptance criteria** (from AUTH-3.md):
- When a shopkeeper belonging to shop A reads or writes shop-scoped data, only shop A's rows are visible or affected
- When a request from a shopkeeper in shop A attempts to read shop B's data by id, the request returns nothing (or is denied), never shop B's data
- On shop-scoped tables, row-level access rules restrict rows by the acting shop, and the rules hold even if an application query forgets to filter by shop
- Any cross-shop read is an intentional admin-role capability, never available to a shopkeeper

_Tickets: docs/auth/AUTH-3.md_

## AUTH-4 — Role-based landing (shopkeeper app vs admin console)
**As a** user
**I want** to land in the right place for my role after login — shopkeepers in the counter app, admins in the admin console
**So that** each role sees only what is relevant to them

**Acceptance criteria** (from AUTH-4.md):
- When a shopkeeper logs in, they are taken to the shopkeeper app surface (chat/voice screen)
- When an admin logs in, they are taken to the admin console surface
- When a shopkeeper opens an admin-console URL directly, they are redirected away and do not see admin content
- When a signed-out visitor opens any protected URL, they are redirected to the login screen

_Tickets: docs/auth/AUTH-4.md_
