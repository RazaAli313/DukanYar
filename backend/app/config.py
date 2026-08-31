"""Centralized settings. Values come from environment / .env — never hard-coded."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "DukanYar"
    cors_origins: str = "http://localhost:3000"

    # Supabase (owned by the scaffold/auth work — placeholders for now)
    supabase_url: str = ""
    supabase_key: str = ""

    # LLM (TEXT-2) — OpenAI-compatible endpoint; Gemini now, Qwen later
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    # Provider-specific (Groq/Qwen: "none", Gemini 3: "minimal"); "" omits it
    llm_reasoning_effort: str = "none"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
