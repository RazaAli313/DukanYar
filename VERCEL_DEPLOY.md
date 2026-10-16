# DukanYar Vercel deployment

DukanYar deploys as one Vercel project with two Services:

```text
https://your-project.vercel.app
├── /*       Next.js frontend
└── /api/*  FastAPI backend

Supabase
├── PostgreSQL
└── Authentication
```

The root `vercel.json` is the source of truth. It builds `frontend/` as a
Next.js service, builds `backend/` as a FastAPI service, and routes `/api/*` to
the backend. The browser therefore uses the same origin and does not need a
separate backend hostname.

Vercel Services and the Python runtime are currently Beta. They support this
polyglot monorepo, ASGI, and streaming responses, but production deployments
should still be smoke-tested after each release.

## 1. Prepare Supabase

1. Create or select the production Supabase project.
2. Apply every migration under `supabase/migrations/` in filename order.
3. In Supabase Authentication → URL Configuration, set the Vercel production
   URL as the Site URL and add the required preview/production redirect URLs.
4. Keep CI on a separate test Supabase project. Never provide production
   credentials through `TEST_SUPABASE_URL` or `TEST_SUPABASE_KEY`.

## 2. Create the Vercel project

1. Import this Git repository into Vercel.
2. Leave **Root Directory** at the repository root.
3. Select the **Services** framework preset if Vercel does not infer it from
   `vercel.json`.
4. Keep Fluid Compute enabled for the Python service.

The local Vercel CLI must be version 48.1.8 or newer for current FastAPI
support. To run both services locally without cloud authentication:

```bash
vercel dev -L
```

## 3. Configure environment variables

Add these in Vercel Project Settings → Environment Variables. Apply secrets to
Production and use separate non-production values for Preview/Development.

### Required browser configuration

```text
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<Supabase anon key>
```

`NEXT_PUBLIC_API_URL=/api` is already committed in
`frontend/.env.production`; override it only if the deployment is intentionally
split across domains.

Values prefixed with `NEXT_PUBLIC_` are included in the browser bundle. The
Supabase anon key is designed for client use; never place the service-role key
in one of these variables.

### Required server secrets

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<Supabase service-role key>
SUPABASE_SERVICE_ROLE_KEY=<same service-role key, used by admin server actions>

LLM_BASE_URL=<OpenAI-compatible base URL>
LLM_API_KEY=<provider API key>
LLM_MODEL=<model with tool-calling support>
```

`SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `LLM_API_KEY` must be Vercel
Secret variables. Do not commit them or prefix them with `NEXT_PUBLIC_`.

### Runtime configuration

```text
CORS_ORIGINS=https://your-project.vercel.app

LLM_REASONING_EFFORT=none
LLM_MAX_CONTEXT_TURNS=8

STT_PROVIDER=groq
GROQ_STT_API_KEY=<Groq API key>
# SPEECHMATICS_API_KEY=<key>  # when STT_PROVIDER=speechmatics

TTS_PROVIDER=edge
TTS_VOICE=ur-PK-AsadNeural
TTS_RATE=+0%
TTS_TRANSLITERATE=false
```

For preview deployments, same-origin `/api` calls do not require preview URLs
to be added to CORS. Supabase Auth redirect URLs still need to cover whichever
preview authentication flow you intend to test.

## 4. Deploy

Git integration creates preview deployments for branches and deploys the
configured production branch. For a manual preview deployment, use a current
Vercel CLI from the repository root:

```bash
vercel deploy
```

Do not promote a deployment until the migration set and environment variables
match that deployment environment.

## 5. Release verification

Verify the public boundaries on the deployed domain:

```text
GET  /api/health                              -> 200 {"status":"ok"}
GET  /login                                   -> login page
POST /api/conversations/{id}/messages         -> SSE meta/delta/action/done
POST /api/conversations/actions/{id}/confirm  -> executes a pending action once
POST /api/conversations/actions/{id}/reject   -> rejects without writing
DELETE /api/conversations/actions/{id}        -> undoes an undoable action
```

In a test shop, run one action from each risk tier:

- read-only: daily summary or low stock;
- commit-with-undo: expense, sale, udhaar, or inventory adjustment;
- approval-required: repayment or add product, testing both reject and confirm.

Confirm that refreshing restores the latest action card, repeated confirmation
returns HTTP 409, undo restores the previous state, and stock/khata balances
remain correct.

## Platform constraints

- Function request and response bodies are limited to 4.5 MB. Keep voice clips
  short; larger media should upload directly to object storage.
- Functions are request-driven, not permanent processes. Do not add an
  always-running worker to the FastAPI process.
- LLM orchestration is bounded to five tool rounds in application code so a
  request cannot loop indefinitely.
