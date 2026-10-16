from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import conversations, dashboard, khata, voice


class ServicePrefixMiddleware:
    """Expose the same app directly and below Vercel Services' `/api` route."""

    def __init__(self, app, prefix: str) -> None:
        self.app = app
        self.prefix = prefix
        self.prefix_bytes = prefix.encode()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] in {"http", "websocket"}:
            path = scope.get("path", "")
            if path == self.prefix or path.startswith(f"{self.prefix}/"):
                scope = {
                    **scope,
                    "path": path[len(self.prefix) :] or "/",
                    "root_path": f"{scope.get('root_path', '')}{self.prefix}",
                }

                raw_path = scope.get("raw_path")
                if isinstance(raw_path, bytes) and raw_path.startswith(
                    self.prefix_bytes
                ):
                    scope["raw_path"] = (
                        raw_path[len(self.prefix_bytes) :] or b"/"
                    )

        await self.app(scope, receive, send)


app = FastAPI(title=f"{settings.app_name} API")

# Vercel Services preserves the public `/api` prefix when forwarding requests.
# Stripping it here keeps route declarations and direct local development clean.
app.add_middleware(ServicePrefixMiddleware, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Feature routers are mounted here as tickets land:
app.include_router(conversations.router, prefix="/conversations")
app.include_router(voice.router, prefix="/voice")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(khata.router, prefix="/khata")
