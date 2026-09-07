# Vercel Deployment Guide

## Architecture

On Vercel, both the frontend and backend are deployed together from the mono-repo root:

| Layer | Vercel build | URL pattern |
|---|---|---|
| Next.js frontend | `@vercel/next` from `frontend/` | `/*` |
| FastAPI backend | `@vercel/python` from `api/index.py` | `/api/*` |

`vercel.json` rewrites every `/api/:path*` request to the Python serverless function (`api/index.py`). Mangum translates the Lambda-style invocation to ASGI so FastAPI routes work normally.

## Step 1 — Import the repo on Vercel

1. Go to vercel.com → New Project → Import Git Repository
2. Select this repo
3. **Root Directory**: leave blank (use repo root)
4. Vercel will auto-detect the `vercel.json` and build both projects

## Step 2 — Environment Variables

Set these in **Vercel Project Settings → Environment Variables**.

### Required (all environments)

```
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<service_role_key>

# LLM (OpenAI-compatible — Gemini, Groq, Qwen, etc.)
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=<your_key>
LLM_MODEL=gemini-2.0-flash

# CORS — allow your Vercel domain (add preview URLs as needed)
CORS_ORIGINS=https://dukanyar.vercel.app

# Frontend Supabase (prefix NEXT_PUBLIC_ so the browser gets them)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key>

# Frontend API base — /api routes to the Python function via vercel.json rewrite
NEXT_PUBLIC_API_URL=/api
```

### STT (Voice input)

```
STT_PROVIDER=groq          # or speechmatics
GROQ_STT_API_KEY=<key>     # if STT_PROVIDER=groq
SPEECHMATICS_API_KEY=<key> # if STT_PROVIDER=speechmatics
```

### TTS (Voice output)

```
# Option A: edge-tts (free, no key, default)
TTS_PROVIDER=edge
TTS_VOICE=ur-PK-AsadNeural

# Option B: Azure (more reliable on serverless)
# TTS_PROVIDER=azure
# AZURE_SPEECH_KEY=<key>
# AZURE_SPEECH_REGION=eastus
# TTS_VOICE=ur-PK-AsadNeural
```

### Optional tuning

```
LLM_REASONING_EFFORT=none   # none=Groq/Qwen, minimal=Gemini
LLM_MAX_CONTEXT_TURNS=8
TTS_RATE=+0%
TTS_TRANSLITERATE=false
```

## Step 3 — Supabase Auth Redirect URL

In Supabase Dashboard → Authentication → URL Configuration:
- Add `https://dukanyar.vercel.app/**` to Redirect URLs
- Add `https://dukanyar.vercel.app` to Site URL

## Notes

- Cold starts: the Python function is ~20–30 MB (supabase + openai + mangum). First request after idle may take 3–5 s.
- Streaming (SSE): Mangum + Vercel support streaming responses. The chat endpoint streams token deltas in real time.
- The `/api/health` Next.js route handler is shadowed by the Python function rewrite — this is fine; FastAPI also serves `GET /api/health`.
