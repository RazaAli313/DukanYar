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

    # Voice STT (VOICE-2) — provider behind app.services.stt.transcribe()
    stt_provider: str = "speechmatics"  # "speechmatics" | "groq"
    stt_language: str = "ur"  # both providers output Urdu script
    # Comma-separated shop/product terms to bias recognition of code-switched
    # English words ("coke, sandwich, biscuit, udhaar, khata, ...").
    stt_extra_vocab: str = ""
    # Speechmatics batch
    speechmatics_api_key: str = ""
    speechmatics_url: str = "https://asr.api.speechmatics.com/v2"
    speechmatics_operating_point: str = "enhanced"  # "standard" | "enhanced"
    # Groq whisper-large-v3 fallback (A/B via STT_PROVIDER=groq)
    groq_stt_base_url: str = "https://api.groq.com/openai/v1"
    groq_stt_model: str = "whisper-large-v3"
    groq_stt_api_key: str = ""  # falls back to LLM_API_KEY when blank

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def stt_extra_vocab_list(self) -> list[str]:
        return [w.strip() for w in self.stt_extra_vocab.split(",") if w.strip()]

    @property
    def effective_groq_stt_key(self) -> str:
        return self.groq_stt_api_key or self.llm_api_key


settings = Settings()
