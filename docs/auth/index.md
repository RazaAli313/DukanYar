# Epic — Auth, RBAC & Tenancy (Dev 3)

**Goal:** Establish who a person is and what they may touch — sign-up/login for the
two roles (**shopkeeper** and **admin**), role-based access control, and per-shop
data isolation so one shopkeeper can never see another's data. This pillar is fully
independent of TEXT and VOICE and publishes a `currentUser` / `currentShop` context
that the other pillars read.

**Ticket prefix:** AUTH

**Suggested build order:** AUTH-1 (authentication) first, since identity underpins
everything else. Then AUTH-2 (RBAC) and AUTH-3 (tenancy) — related but separable.
AUTH-4 (role-based landing) last, once both roles and guards exist.

**Contract published on day 1:** a stub `currentUser` / `currentShop` so TEXT and
VOICE can scope data before real auth lands, then swapped for the real thing without
changing callers.

**Sources:** Stakeholder grilling session (this conversation) — two roles
(shopkeeper users, admin platform-builders), production-ready multi-tenant platform,
khata identity is shop-scoped.

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| AUTH-1 | Authentication (signup, login, sessions) | To Be Done | TBD | TBD | TBD |
| AUTH-2 | RBAC — shopkeeper vs admin roles & guards | To Be Done | TBD | TBD | TBD |
| AUTH-3 | Tenancy — per-shop data isolation | To Be Done | TBD | TBD | TBD |
| AUTH-4 | Role-based landing (shopkeeper app vs admin console) | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
