### TEXT-5 — Chat UI integration & history rendering

| Field | Value |
| :---- | :---- |
| Ticket ID | TEXT-5 |
| Ticket Name | Chat UI integration & history rendering |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | TEXT-3 (BE persistence, done), AUTH `app_metadata.shop_id` fix, frontend app-tree reconciliation |
| Estimate | BE: 0 \| FE: TBD |
| Source References | TEXT-3 review (2026-09-02) — AC "history reloads on return" is a UI scenario left unmet by the backend-only TEXT-3 |

**Description:** As a shopkeeper, I want the chat screen to actually appear in the
app and show my previous messages when I return, so that the conversation
persistence built in TEXT-3 is something I can see and use.

TEXT-3 delivered the backend only. This ticket makes it visible.

**Why this is its own ticket:** the chat UI has never rendered. `feat/auth`
created a root `frontend/app/` tree while `feat/text-voice-module` built the whole
chat UI under `frontend/src/app/`. Next.js serves only one app directory — the
root one wins — so `src/app/page.tsx`, the only place `ChatScreen` is mounted, is
dead code. Fixing that touches auth-owned files and is not TEXT-3's job.

**Known work:**

| Task | Notes |
| :-- | :-- |
| Reconcile the two `app/` trees | Delete `src/app/`; keep `src/components` + `src/lib` |
| Merge `globals.css` | `src/app/globals.css` is Tailwind **v4** (`@import`, `@theme`, theme tokens, keyframes) — the chat components need it. Root `app/globals.css` uses **v3** directives (`@tailwind base`) though v4 is installed |
| Fonts | Chat components expect Geist (`--font-geist-sans`); root layout loads Inter |
| Mount `ChatScreen` | On `/app`, replacing or alongside the placeholder dashboard |
| Attach the token | `supabase.auth.getSession()` → `Authorization: Bearer <access_token>` on every `chatApi` call |
| Load history on mount | `GET /conversations/history` → map `{role, content}` → the frontend `Message` shape (`sender`, `text`) |
| Drop the client-generated conversation id | The server resolves the shop's thread; read it from the SSE `meta` event |
| Stop sending `recent_turns` | The backend ignores it; context comes from the DB |
| Fix `middleware.ts` | Selects `profiles.role`; the column is `role_name`, so admin/shopkeeper redirects never fire |

**Blocked on:** `public.current_shop_id()` reads `app_metadata.shop_id`, which
nothing populates. The TEXT-3 backend does not depend on it (service_role +
manual scoping), but any RLS-bound frontend read does. Owned by the AUTH epic.

**Acceptance Criteria:**
```gherkin
Feature: Text pillar — chat UI integration

  Scenario: The chat screen is reachable
    Given a signed-in shopkeeper
    When they open the app
    Then the chat screen renders with its own theme and fonts intact

  Scenario: History reloads on return
    Given the shopkeeper has an existing conversation
    When they reopen or refresh the app
    Then the previous messages are shown in order

  Scenario: Requests are authenticated
    Given the shopkeeper sends a message
    Then the request carries their Supabase access token
    And the reply is persisted against their shop's thread

  Scenario: Auth pages keep working
    Given the globals.css and layout are reconciled
    When the login and signup pages are opened
    Then their styling is unbroken
```
