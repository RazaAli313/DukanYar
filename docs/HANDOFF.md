# TEXT + VOICE module — handoff / progress

**Owner:** Usman (Muhammad Usman Tariq)
**Branch:** `feat/text-voice-module` → PR against `develop` (Raza reviews & merges)
**Last updated:** 2026-08-31
**Module scope:** the TEXT pillar (TEXT-1..4) and the VOICE pillar (VOICE-1..4).
Tickets: `docs/text-model/`, `docs/voice/`. Read each ticket's `.md` +
`user-stories.md` + `index.md` before starting it.

---

## Project context (short)

DukanYar = voice-first, multimodal (voice **and** text) Urdu AI assistant for small
Pakistani retail shopkeepers. One-week Alibaba Cloud AI Hackathon.

- **Stack:** Next.js (frontend) + FastAPI (backend, managed with `uv`) + Supabase (DB/auth).
- **Phase 1** = Foundation + TEXT + VOICE + AUTH. **No tool-calling / business logic** yet —
  the model only *converses*. Tools come in Phase 2.
- Formal cross-team contracts were **dropped** (not worth it for a one-week build).
- **LLM plan:** build against **Gemini Flash free tier** (OpenAI-compatible endpoint),
  switch to **Qwen** before the final demo. Keep the LLM call behind a thin wrapper so
  the swap is a config change.
- **Voice plan:** likely **ElevenLabs** for STT (Scribe) + TTS. Alibaba/Qwen recognizes
  Urdu speech but does **not** synthesize Urdu speech output — so TTS (VOICE-3) must sit
  behind a swappable adapter.

## Division of labour

| Who | Owns |
| --- | --- |
| **Usman** (this branch) | TEXT + VOICE feature: chat UI, LLM integration, message persistence logic, voice capture / STT / TTS |
| **Sheheryar** | Supabase connection, table migrations, Auth. Not started as of 2026-08-31; will pull this branch's scaffold and drop his work into `backend/app/db.py` + `backend/app/auth.py` |
| **Raza** | Team lead — reviews PRs, merges to `develop` |

---

## What is DONE

### Branch setup
- `feat/text-voice-module` cut from `feature/user-stories`, then `develop` merged in
  (brings `docs/ERD.md` — FigJam link + consolidated schema description).
- Pushed to `origin`. **No PR opened yet** — open it against `develop` once tickets are done.

### Scaffold — commit `7b39d4e` `chore: scaffold frontend + backend`
```
frontend/                 Next.js 16, App Router, TypeScript, Tailwind 4, src/ dir
                          `npm run build` passes. Boilerplate CLAUDE.md/AGENTS.md
                          were added by create-next-app — delete if unwanted.
backend/                  uv project (pyproject.toml + uv.lock), Python 3.13
  app/main.py             FastAPI app, CORS, GET /health -> {"status": "ok"}
  app/config.py           pydantic-settings; reads .env (app, CORS, Supabase, LLM keys)
  app/db.py               STUB — get_supabase() raises NotImplementedError. Sheheryar owns.
  app/auth.py             STUB — get_current_user() returns a fixed fake shopkeeper
                          (CurrentUser{user_id, shop_id, role}). Keep the shape.
  app/routers/            empty — feature routers mount here
  app/services/           empty — llm.py / voice.py go here
  .env.example            copy to .env
frontend/.env.example     NEXT_PUBLIC_API_URL=http://localhost:8000
README.md                 run-locally steps for both apps
```

Run locally:
```bash
# backend
cd backend && uv sync && cp .env.example .env && uv run fastapi dev app/main.py

# frontend
cd frontend && npm install && cp .env.example .env.local && npm run dev
```

### Docs read / facts locked
- `docs/text-model/` — all four tickets + user-stories + index.
- **Confirmed Phase-1 DB schema** (from `docs/foundation/FND-2 ... ERD.pdf`,
  `docs/text-model/TEXT-2 TEXT-3 ... ERD.pdf`, and `docs/ERD.md`):

| table | columns |
| --- | --- |
| `shops` | id PK, name, created_at |
| `roles` | id PK, name (`shopkeeper` \| `admin`) |
| `users` | id PK, shop_id FK, role_id FK, email UK, password_hash, created_at |
| `conversations` | id PK, shop_id FK, user_id FK, created_at |
| `messages` | id PK, conversation_id FK, sender (`user` \| `assistant`), text, channel (`text` \| `voice`), status (`pending` \| `streaming` \| `complete` \| `failed`), created_at, transcription_confidence (float, nullable — voice only) |

---

## NEXT: TEXT-1 — Chat input UI (not started)

UI only, built against a **stubbed** reply (per `index.md` build order). React state
only — no persistence (that's TEXT-3).

Acceptance criteria (`docs/text-model/TEXT-1.md`):
- Submit a typed message → appears as a "user" bubble; input clears, ready for next.
- Assistant reply arrives → appears as an "assistant" bubble beneath it.
- While waiting → visible pending indicator until reply or error.
- Urdu-script message renders right-to-left and stays readable.

### 5 open decisions (were pending when handed off — pick before coding)

| # | Question | Recommended default |
| --- | --- | --- |
| 1 | Where is the stub reply? | Pure frontend stub (`setTimeout` + canned reply), structured so TEXT-2 swaps in the real API call. No backend yet. |
| 2 | Route for the chat screen | `/` (home) — app is single-purpose, voice-first |
| 3 | RTL handling | Per-message auto-detect: if the text contains Arabic-script chars, set that bubble's `dir="rtl"`. Better for code-switching than a whole-app flip. |
| 4 | Theme | Dark, echoing the mockup (`mockups/dukanyaar-mockup.html`: slate-900 + emerald accents) for later consistency |
| 5 | UI copy language (placeholder, send button, errors) | Roman-Urdu (e.g. "Apna message likhein…", "Bhejein") |

The mockup is a **POS dashboard** prototype, not a chat UI — no direct design
reference for the chat thread; use it only for palette/tone.

---

## Then, in order

- **TEXT-2** — `POST /conversations/{id}/messages` in FastAPI. LLM call behind
  `app/services/llm.py` (Gemini now / Qwen later, OpenAI-compatible). Streaming reply.
  Channel-agnostic (voice reuses it). Clear error + retry without losing the typed text.
  *Needs a Gemini API key — https://aistudio.google.com → Get API key (free).*
- **TEXT-3** — persist user + assistant messages to `messages`, reload history in order,
  scope every query by `shop_id`, feed recent turns as context to the LLM.
  *Needs Sheheryar's real `db.py` (Supabase client) + tables.*
- **TEXT-4** — system persona ("polite, concise AI shop employee"), Urdu / Roman-Urdu /
  English code-switching, reply in the user's register, ask a short clarifying question
  when input is ambiguous.
- **VOICE-1** — push-to-talk mic capture (hold to record, release to send), mic-permission
  handling, ignore empty/near-empty clips.
- **VOICE-2** — captured audio → STT (ElevenLabs Scribe / Whisper) → transcript → the
  **same** `/messages` endpoint tagged `channel=voice`; set `transcription_confidence`;
  prompt retry on empty / low-confidence.
- **VOICE-3** — assistant reply text → TTS **behind an adapter interface**
  (`app/services/voice.py`), so the provider can be swapped without touching capture or
  STT. Always show the reply as text too; degrade gracefully if TTS fails.
- **VOICE-4** — full speak→hear loop; voice + text share one conversation thread;
  a mis-transcription can be fixed by typing without restarting.

---

## Conventions

- One migration file per epic, additive, timestamped. Never edit another epic's migration.
- Each pillar owns its own folders; no shared central file everyone edits.
- Branch names: Conventional Branch (`feat/`, `fix/`, `docs/`, `chore/`).
- Commits: Conventional Commits style.
