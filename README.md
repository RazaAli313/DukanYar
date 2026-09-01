# DukanYar

Voice-first, multimodal AI assistant for small retail shopkeepers in Pakistan.
Engineering docs and tickets live in [`docs/`](docs/README.md).

## Repo layout

```
frontend/   Next.js (App Router, TypeScript, Tailwind) — chat UI
backend/    FastAPI service (managed with uv) — conversation + voice endpoints
docs/       epic tickets, user stories, ERD
mockups/    static HTML mockup
```

## Run locally

### Backend

```bash
cd backend
uv sync
cp .env.example .env        # fill in values
uv run fastapi dev app/main.py    # http://localhost:8000  (health: /health)
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                 # http://localhost:3000
```

## Branching

Feature branches use Conventional Branch naming (`feat/`, `fix/`, `docs/`, `chore/`)
and are opened as PRs against `develop`.
