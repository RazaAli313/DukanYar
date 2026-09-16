"""Vercel serverless entry-point for the DukanYar FastAPI backend.

Vercel's Python runtime runs on AWS Lambda under the hood, so we wrap the
ASGI app with Mangum.  Mangum translates Lambda proxy events <-> ASGI
scope/receive/send, including chunked streaming for the SSE chat endpoint.

Route mapping
─────────────
vercel.json rewrites  /api/:path*  ->  /api/index
Mangum's api_gateway_base_path="/api" strips "/api" before routing, so
FastAPI sees  /conversations/…  /dashboard/…  /voice/…  /khata/…  etc.

Environment variables (set in Vercel project settings)
───────────────────────────────────────────────────────
SUPABASE_URL, SUPABASE_KEY
LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
CORS_ORIGINS          comma-separated frontend origins, e.g. https://dukanyar.vercel.app
STT_PROVIDER, SPEECHMATICS_API_KEY, GROQ_STT_API_KEY
TTS_PROVIDER, AZURE_SPEECH_KEY, AZURE_SPEECH_REGION   (optional)
"""

from __future__ import annotations

import os
import sys

# ── sys.path surgery ─────────────────────────────────────────────────────────
# api/index.py lives at  <repo>/api/index.py
# The backend package is at  <repo>/backend/app/…
# All internal imports use `from app.*`, so <repo>/backend must be on the path.
_HERE = os.path.dirname(os.path.abspath(__file__))   # <repo>/api
_REPO = os.path.dirname(_HERE)                        # <repo>
_BACKEND = os.path.join(_REPO, "backend")             # <repo>/backend

for _p in (_BACKEND, _REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── import the FastAPI app ────────────────────────────────────────────────────
# This triggers settings validation, router wiring, and tool-registry bootstrap.
from app.main import app as _fastapi_app  # noqa: E402

# ── Mangum wrapper ────────────────────────────────────────────────────────────
from mangum import Mangum  # noqa: E402

# lifespan="off"      Vercel functions are stateless; startup/shutdown have
#                     nowhere to run.
# api_gateway_base_path="/api"
#                     Strips "/api" from the incoming path before routing so
#                     FastAPI sees /conversations/… not /api/conversations/…
handler = Mangum(_fastapi_app, lifespan="off", api_gateway_base_path="/api")

# Vercel Python runtime invokes the callable named `app` or `handler`.
# Expose both so either mode works.
app = handler
