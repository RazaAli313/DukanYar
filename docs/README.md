# Dukanyar — Engineering Docs

Voice-first, multimodal AI assistant for small retail shopkeepers in Pakistan.
A shopkeeper talks (or types) to the app in Urdu; the app records sales, tracks
*udhaar* (credit), manages inventory and expenses, and reports back — with zero
typing or app-navigation required at the counter.

Two roles: **shopkeeper** (the counter app) and **admin** (us, the platform builders).

---

## Development strategy — walking skeleton, then vertical slices

We are **not** building horizontally (all DB, then all APIs, then all UI — which
blocks everyone and produces nothing demoable until the end) and **not** building
purely vertically (each feature re-plumbing its own auth/voice — which duplicates
the foundation and causes constant conflicts).

Instead:

1. **Layer 0 — Foundation.** A thin, shared, up-front skeleton: project scaffold +
   database tables & migrations + deploy. Cheap, built once, then frozen. It is
   ground to stand on, not a feature.
2. **Layer 1 — Three parallel pillars.** The real Phase-1 work, split so the three
   engineers almost never touch the same files.

```
docs/
  README.md            ← you are here
  foundation/          FND    — Layer 0: scaffold, DB schema + migrations, deploy
  text-model/          TEXT   — Dev 1: text input ⇄ model (conversational)
  voice/               VOICE  — Dev 2: voice input ⇄ model (STT + TTS)
  auth/                AUTH   — Dev 3: authentication, RBAC, tenancy
```

---

## Phase roadmap

Phase 1 deliberately excludes tool-calling. We first prove the three pillars work
end-to-end, then bolt intelligence and business logic on top.

| Phase | Scope | Status |
| :---- | :---- | :---- |
| **Phase 1 — Pillars** (this doc set) | Foundation + Text⇄Model + Voice⇄Model + Auth/RBAC. Model *converses*; no tools yet. | **In progress** |
| Phase 2 — Tool-calling | Tool registry + orchestration so the model can *act*, not just talk. | Later |
| Phase 3 — Feature tools | Sale + inventory, khata/udhaar (khata# + CNIC), expenses, reporting/summaries. | Later |
| Phase 4 — Admin & polish | Admin console (manage shops/users, voice/transcription monitoring, audit), low-stock alerts, voice catalog building. | Later |

---

## Phase-1 ownership (3 engineers, no cross-blocking)

| Dev | Pillar | Builds |
| :---- | :---- | :---- |
| Dev 1 | **TEXT** | typed message → model → text reply, rendered in a chat UI and persisted. Publishes the model-conversation endpoint the voice pillar reuses. |
| Dev 2 | **VOICE** | push-to-talk capture → speech-to-text → model → text-to-speech reply; voice and text are interchangeable (multimodal). |
| Dev 3 | **AUTH** | signup/login/sessions, roles (shopkeeper vs admin), per-shop data isolation, route guards. |

**Day-1 handshake (removes all blocking):** each pillar publishes a stub/contract
on day 1 — Foundation exposes deployed empty tables, Auth exposes a stub
`currentShop`/`currentUser`, Text exposes the conversation endpoint shape. From
day 2 the three pillars build against those contracts and never wait on each other.

---

## Conventions that keep merge conflicts near zero

- **One migration file per epic**, timestamped and additive. Never edit another
  epic's migration.
- **Additive files, not shared-file edits.** Each pillar owns its own folders
  (frontend route + backend module). No central file that everyone has to touch.
- **Read across contexts through views you own** (relevant from Phase 3 onward):
  reporting/admin read other modules only via DB views they define, so a schema
  change elsewhere can't break their build.
- **Contracts before implementations.** Publish the interface/stub first; swap in
  the real thing later without changing callers.

---

## Ticket format

Every epic folder has an `index.md` (parent) listing its child tickets, plus one
`.md` per ticket. Tickets carry a field table and **Gherkin** acceptance criteria.
Prefixes: `FND`, `TEXT`, `VOICE`, `AUTH`.

**Sources** for all Phase-1 scope: stakeholder grilling session (this project's
scoping conversation) and Alibaba Cloud AI Hackathon 2026 constraints (deploy on
Alibaba Cloud, use Qwen models, open-source repo). No estimates have been guessed;
`TBD` means "fill in at estimation."
