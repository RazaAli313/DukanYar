# TEXT + VOICE module — handoff / progress

**Owner:** Usman (Muhammad Usman Tariq)
**Branch:** `feat/text-voice-module` → PR against `develop` (Raza reviews & merges)
**Last updated:** 2026-09-01 (TEXT-1, TEXT-2, TEXT-4 and the whole VOICE epic done; TEXT-3 blocked on DB)
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

## DONE: TEXT-1 — Chat input UI

Frontend-only chat screen at `/`. All state is React-local, no persistence.

**Files created:**
```
frontend/src/lib/types.ts             Message, Sender, MessageStatus types
frontend/src/lib/rtl.ts               isRtl() per-bubble Arabic-script detection
frontend/src/lib/chatApi.ts           sendMessage() stub — TEXT-2 swap point
frontend/src/components/chat/
  ChatScreen.tsx                      Main view (h-dvh, centered 720px column)
  ChatThread.tsx                      Scrollable message list + empty state
  ChatBubble.tsx                      User/assistant bubbles, RTL, timestamps
  ChatInput.tsx                       <form> Enter-to-send, arrow-up icon button
  PendingIndicator.tsx                Staggered bouncing dots
```

**5 decisions resolved:** frontend stub (`setTimeout` + canned), route `/`, per-message
RTL auto-detect, dark theme (slate-900 + emerald), Roman-Urdu UI copy.

`next build` passes clean.

---

## DONE: TEXT-2 — Model integration & streaming reply

Stateless streaming endpoint (no DB yet — frontend sends recent turns in the body).

**Files:**
```
backend/app/services/llm.py           stream_reply() — openai.AsyncOpenAI vs any
                                      OpenAI-compatible endpoint; provider swap
                                      = config only. (TEXT-4 prepends SYSTEM_PROMPT here.)
backend/app/routers/conversations.py  POST /conversations/{id}/messages — SSE
                                      (named events: delta / done / error)
backend/app/main.py                   mounts the conversations router
frontend/src/lib/chatApi.ts           real fetch + SSE parser (buffered), 30s timeout,
                                      onDelta/onComplete callbacks
frontend/src/lib/types.ts             MessageStatus += "streaming"
frontend/src/components/chat/ChatScreen.tsx   streams reply, per-tab conversationId,
                                      id-based retry (no dup user bubble)
frontend/src/components/chat/ChatThread.tsx   retry button on assistant error bubble
```

Tested: streaming, Roman-Urdu, multi-turn context, Urdu RTL, error + retry.
`next build` + backend import clean.

---

## DONE: TEXT-4 — Language handling & assistant persona

System prompt in `backend/app/prompts.py` (`SYSTEM_PROMPT`), prepended in
`llm.py`. Covers: polite "dukaan ka AI assistant" persona (aap, concise, no
markdown), reply in the shopkeeper's language/register (Roman-Urdu / Urdu
script / English / code-switched), ask ONE clarifying question on vague input
instead of guessing, and — critical for Phase 1 — never fake a save/record
(no tools yet; only explicit "record kar do" gets a "feature coming soon" line).
`reasoning_effort` is now config-driven (`LLM_REASONING_EFFORT`, provider-specific).

Tested 8-turn conversation: persona, language switching, no-fake-save, and
arithmetic all pass. Urdu *script* quality is model-limited (see LLM note below).

---

## DONE: VOICE-1 — Push-to-talk capture

Frontend-only. Hold the mic to record, release to send. No new npm deps, no
backend changes, the audio blob never leaves the browser.

**Files created:**
```
frontend/src/lib/voice/usePushToTalk.ts   Capture state machine — getUserMedia +
                                          MediaRecorder. Statuses idle/requesting/
                                          recording/denied/error. Guards:
                                          MIN_RECORD_MS=450, MIN_BLOB_BYTES=2048,
                                          MAX_RECORD_MS=60000 (safety auto-stop).
                                          Discards a clip if released while the
                                          permission prompt is still open; always
                                          stops mic tracks; unmount cleanup.
frontend/src/lib/voice/stt.ts              transcribeAudio(clip) STUB — 600ms delay,
                                          returns a random fixed Urdu sentence.
                                          VOICE-2 swap point (Speechmatics).
frontend/src/components/voice/
  PushToTalkButton.tsx                     Big emerald mic (mockup SVG). Pointer
                                          events + setPointerCapture (release off
                                          the button still sends). animate-ping
                                          ring while recording; long-press menu /
                                          text selection suppressed; spinner on
                                          "requesting"; muted-mic on "denied".
  RecordingIndicator.tsx                   Pulsing dot + "Sun raha hoon…" + m:ss
                                          timer, aria-live. Shown for the whole
                                          capture.
  VoiceBar.tsx                             Release flow: stop() -> guard -> stub
                                          transcript -> onSend (same path typed
                                          messages take). Re-checks disabled at
                                          release; transient "bohat mukhtasar"
                                          hint on a too-short tap; denied/error
                                          notice pointing to browser mic settings.
```

**Shared-file edit (only one):** `frontend/src/components/chat/ChatScreen.tsx` —
renders `<VoiceBar onSend={handleSend} disabled={isPending} />` between
`<ChatThread>` and `<ChatInput>`. Nothing else touched.

`next build` + `next lint` pass clean (0 errors).

**Decisions:** dedicated voice bar above the input (not a small mic in the input
row) to keep the mic big and voice-first; `channel:"voice"` tagging deferred to
VOICE-2 (its AC; backend `MessageRequest.channel` already defaults to `"text"`).

**Known / expected:** the transcript is a stub — it ignores your speech and
returns a random canned sentence. Real STT is VOICE-2 and replaces ONLY the body
of `transcribeAudio()` in `lib/voice/stt.ts`; capture and UI don't change.
Secure-context only (mic is unavailable over plain HTTP — fine on localhost, the
demo host must be HTTPS). Primary target Chrome; mime negotiation covers Safari.

---

## DONE: VOICE-2 — Speech-to-text (STT) integration

Captured clip → backend proxy → Speechmatics → real transcript → the shared
`/conversations` endpoint tagged `channel="voice"`. Transcript shows as the user
bubble; low-confidence / empty → retry prompt, nothing sent.

**Files created:**
```
backend/app/services/stt.py     transcribe(audio, content_type) -> Transcript{text,
                                confidence}. Provider behind one interface, picked
                                by STT_PROVIDER:
                                - speechmatics (default): batch REST — create job
                                  (multipart data_file + config JSON, language "ur",
                                  operating_point "enhanced", additional_vocab from
                                  STT_EXTRA_VOCAB) → poll GET /jobs/{id} (~1s, ~25s
                                  cap) → GET transcript?format=json-v2 → join words,
                                  mean word confidence.
                                - groq: whisper-large-v3 on the LLM key; confidence
                                  approximated from segment avg_logprob.
backend/app/routers/voice.py    POST /voice/transcribe (multipart file) -> {transcript,
                                confidence}. 10MB cap, 502 if unconfigured, 422 empty.
```

**Files edited:**
```
backend/app/config.py           + stt_provider, stt_language, stt_extra_vocab,
                                speechmatics_* , groq_stt_* ; helpers
                                stt_extra_vocab_list, effective_groq_stt_key
backend/app/main.py             mounts voice.router at /voice
backend/app/prompts.py          + VOICE_LANGUAGE_HINT — voice turns reply in
                                Roman-Urdu (STT gives Urdu script → gpt-oss-120b
                                hallucinates script; Roman-Urdu is its strong register)
backend/app/services/llm.py     stream_reply(turns, channel="text") — appends
                                VOICE_LANGUAGE_HINT as a 2nd system msg when voice
backend/app/routers/conversations.py  passes body.channel into stream_reply
backend/.env.example            + STT_PROVIDER / SPEECHMATICS_API_KEY / STT_EXTRA_VOCAB / ...
backend/pyproject.toml          pins httpx (was transitive via fastapi[standard])
frontend/src/lib/voice/stt.ts   real transcribeAudio() — uploads blob to
                                /voice/transcribe, 40s timeout, returns
                                {transcript, confidence}. exports STT_MIN_CONFIDENCE=0.5
frontend/src/lib/chatApi.ts     sendMessage(..., channel: "text"|"voice" = "text")
                                — added to request body
frontend/src/lib/types.ts       + Channel type, optional Message.channel
frontend/src/components/chat/ChatScreen.tsx   handleSend(text, channel); user bubble
                                tagged; retry keeps the original channel
frontend/src/components/voice/VoiceBar.tsx     confidence/empty gate → "Awaaz saaf
                                samajh nahi aayi" retry prompt; else onSend(t, "voice");
                                error toast; "Likh raha hoon…" while transcribing
```

**Config to run:** `backend/.env` needs `STT_PROVIDER=speechmatics` +
`SPEECHMATICS_API_KEY=...` (+ optional `STT_EXTRA_VOCAB`). A-B test Whisper with
`STT_PROVIDER=groq` (reuses `LLM_API_KEY`).

**Tested:** real Urdu / code-switched speech → transcript (Urdu script) → Roman-Urdu
reply; silence → retry prompt, no `/conversations` call; `channel:"voice"` in the
payload. `next build` + `next lint` + backend import all clean.

**Known / expected:** transcript is Urdu script (no Roman-Urdu STT mode exists);
`additional_vocab` biases but doesn't guarantee accented English words ("chips"
still misheard sometimes). `transcription_confidence` is computed and gated
client-side but NOT persisted (no DB yet — TEXT-3).

---

## DONE: VOICE-3 — Text-to-speech reply playback

Voice-turn reply text → backend TTS adapter → MP3 → played aloud. Reply is always
shown as text; audio degrades gracefully (failure / autoplay-block → tap-to-play).

**Files created:**
```
backend/app/services/voice.py   synthesize(text, voice=None) -> mp3 bytes. Provider
                                behind one interface, picked by TTS_PROVIDER:
                                - edge (default): edge-tts, no key, ur-PK neural
                                  voices via Edge's (unofficial) endpoint.
                                - azure: same ur-PK voices via Azure Speech REST +
                                  SSML (needs AZURE_SPEECH_KEY/REGION). SSML MUST
                                  carry xmlns=".../synthesis" or Azure ignores
                                  <voice> and uses the region default (Hindi in
                                  centralindia).
                                Optional TTS_TRANSLITERATE: a Groq call rewrites the
                                Roman-Urdu reply to Urdu script before synthesis
                                (ur-PK voices read Latin text poorly / truncate);
                                best-effort, falls back to the original on error.
                                TTSError on failure.
frontend/src/lib/voice/tts.ts   synthesizeSpeech(text) -> audio Blob, 20s timeout.
frontend/src/lib/voice/useReplySpeech.ts   one <audio>; speak(id,text)/stop();
                                status idle|loading|playing|blocked|error; autoplay
                                reject = "blocked" not error; supersede guard.
frontend/src/components/voice/ReplaySpeechButton.tsx   🔊 Suniye / ⏹ Rokiye control.
```

**Files edited:**
```
backend/app/routers/voice.py    + POST /voice/speak {text} -> audio/mpeg (502 if
                                unconfigured, 422 empty, 8k-char cap)
backend/app/config.py           + tts_provider, tts_voice, tts_rate, tts_transliterate,
                                azure_speech_key, azure_speech_region
backend/.env.example            + TTS_PROVIDER / TTS_VOICE / TTS_RATE / TTS_TRANSLITERATE
                                / AZURE_SPEECH_KEY / AZURE_SPEECH_REGION
backend/pyproject.toml          + edge-tts
frontend/src/lib/types.ts       + Message.spoken?: boolean
frontend/src/components/chat/ChatScreen.tsx   accumulates reply text; on a voice-turn
                                reply completing → marks spoken + speech.speak(...)
frontend/src/components/chat/ChatThread.tsx + ChatBubble.tsx   render the replay
                                button for spoken, complete assistant messages
```

**Config to run:** nothing required — `TTS_PROVIDER=edge` (default) needs no key,
just internet. For Azure: `TTS_PROVIDER=azure` + `AZURE_SPEECH_KEY` +
`AZURE_SPEECH_REGION` (short name, e.g. `centralindia`). `TTS_VOICE` picks the
voice for either provider: `ur-PK-AsadNeural` (M) / `ur-PK-UzmaNeural` (F).

**Tested:** voice message → reply spoken aloud; replay button works; broken
provider → text only, no hang; `TTS_TRANSLITERATE=true` improves ur-PK
pronunciation and fixes edge-tts mid-sentence truncation. `next build` +
`next lint` + backend import clean.

**Known / expected:** edge-tts is an unofficial MS endpoint — fine for dev, can
rate-limit / break / truncate; switch to Azure for the demo (0.5M chars/mo free).
Roman-Urdu on ur-PK voices is rough without `TTS_TRANSLITERATE`. Azure vs edge
quality difference is modest once transliteration is on. No audio caching/storage.

---

## DONE: VOICE-4 — End-to-end loop & multimodal parity

Frontend-only. Because voice already rides the same `handleSend` path as typed
text, 3 of the 4 ACs were satisfied by the architecture — this adds the polish.

**AC status:**
- Full voice round-trip, no manual steps → already worked (VOICE-1→2→3 chain).
- Voice + text in one thread, in order → already worked; voice turns now show a 🎤 tag.
- Typed follow-up uses the prior voice turn as context → already worked (`toTurns`
  is channel-agnostic; backend prepends all prior turns).
- Mis-transcription recovery → **reinterpreted: re-speak, not re-type.** Shopkeepers
  don't type Urdu and voice is the primary input, so a "correct by typing"
  affordance is the wrong tool. Instead: a "↺ Ghalat? Phir bolein" button on the
  most recent voice turn discards it + everything after and invites a fresh
  recording.

**Files edited:**
```
frontend/src/components/chat/ChatBubble.tsx    🎤 tag on voice user bubbles;
                                "↺ Ghalat? Phir bolein" button
frontend/src/components/chat/ChatThread.tsx    finds the most recent voice user
                                turn (even behind later text turns); shows the
                                redo button there when not mid-reply
frontend/src/components/chat/ChatScreen.tsx    handleRedoVoice() — stop audio,
                                slice the thread to before that turn, flash a
                                "Phir boliye" prompt; speech.stop() at the start
                                of every send; 🔊/🔇 header toggle (speakReplies,
                                default ON) — now EVERY reply is spoken (voice or
                                text), not just voice turns
frontend/src/components/voice/VoiceBar.tsx     onCaptureStart (stops a playing
                                reply when a new recording begins); `notice` prop
                                for the "Phir boliye" prompt
```

**Tested:** full voice loop with no clicks between stages; voice+text interleaved
in order with 🎤 tags; typed follow-up carries voice context; ↺ redo discards the
turn + trailing turns and re-records cleanly; 🔊 toggle mutes/unmutes all replies
and stops in-flight playback. `next build` + `next lint` clean. No backend change.

**Known / expected:** redo trims the thread from the chosen turn onward (its reply
and any later turns, including typed ones) — intentional, a bad base turn usually
makes the rest of the exchange wrong too. `speakReplies` state is per-tab, not
persisted.

---

## LLM provider — current state (2026-09-01)

Google locked new API keys to `gemini-3.6-flash` only (20 requests/day free) —
**Gemini free tier is unusable** for this. Now on **Groq free tier**:
```
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...            # console.groq.com — free
LLM_MODEL=openai/gpt-oss-120b  # best free option for Roman-Urdu; qwen3.x-27b was weaker
LLM_REASONING_EFFORT=low       # Groq now REJECTS "none" for gpt-oss-120b — must be low/medium/high
```
Roman-Urdu is coherent; Urdu script still hallucinates on gpt-oss-120b. **Before the
demo**, switch to Alibaba Model Studio Qwen (`qwen-plus`/`qwen-max`, free tier ~1M
tokens) — better Urdu + aligns with the hackathon. Swap = 3 `.env` lines, no code.
Groq also has `whisper-large-v3` (STT) on the same key — useful for VOICE-2.

---

## NEXT: TEXT-3 — Conversation persistence & history

Persist user + assistant messages to the `messages` table, reload history in order,
scope every query by `shop_id`, feed recent turns as context to the LLM.
**Needs Sheheryar's real `db.py` (Supabase client) + the `conversations` / `messages`
tables.** Until those land, TEXT-3 is blocked — do TEXT-4 first if so.

## The VOICE epic — DONE (all 4)

All reuse TEXT-2's stateless `POST /conversations/{id}/messages`. Details in the
"DONE: VOICE-1/2/3/4" sections above.

- **VOICE-1** — push-to-talk capture.
- **VOICE-2** — Speechmatics STT (Groq whisper A-B fallback); `channel=voice`
  threaded through to a Roman-Urdu reply nudge.
- **VOICE-3** — TTS adapter in `backend/app/services/voice.py`; edge-tts (default)
  + Azure REST, `ur-PK` voices, optional Groq transliteration to Urdu script.
- **VOICE-4** — full loop + multimodal parity; 🎤 tags, "↺ Ghalat? Phir bolein"
  re-speak recovery, 🔊/🔇 speak-all-replies toggle.

## Blocked until Sheheryar's DB lands

- **TEXT-3** — persistence (see above). Not blocking anything else — do it whenever the
  `conversations` / `messages` tables + `backend/app/db.py` (real Supabase client) exist.

---

## Conventions

- One migration file per epic, additive, timestamped. Never edit another epic's migration.
- Each pillar owns its own folders; no shared central file everyone edits.
- Branch names: Conventional Branch (`feat/`, `fix/`, `docs/`, `chore/`).
- Commits: Conventional Commits style.
