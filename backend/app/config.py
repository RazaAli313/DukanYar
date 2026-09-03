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
    # TEXT-3: how many prior turns are replayed to the model. The thread itself
    # is never truncated — this caps only what each request sends, so tokens and
    # latency stay flat as the conversation grows.
    llm_max_context_turns: int = 8

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

    # Voice TTS (VOICE-3) — provider behind app.services.voice.synthesize()
    tts_provider: str = "edge"  # "edge" | "azure"
    tts_voice: str = "ur-PK-AsadNeural"  # or ur-PK-UzmaNeural (female)
    tts_rate: str = "+0%"  # edge-tts prosody rate ("+0%", "-10%", ...)
    # Roman-Urdu replies read poorly on ur-PK voices; when true, a Groq call
    # transliterates to Urdu script before synthesis (falls back to the
    # original text on any error).
    tts_transliterate: bool = False
    # Azure Speech (TTS_PROVIDER=azure) — REST endpoint, no SDK
    azure_speech_key: str = ""
    azure_speech_region: str = ""  # e.g. "eastus"

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
