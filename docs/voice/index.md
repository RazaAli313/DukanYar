# Epic — Voice ⇄ Model (Dev 2)

**Goal:** Let a shopkeeper hold a button, speak in Urdu, and hear a spoken reply —
by wrapping the TEXT pillar's conversation endpoint with speech-to-text on the way in
and text-to-speech on the way out. Voice and text are interchangeable (multimodal):
anything you can do by typing you can do by speaking, and vice versa. This pillar
proves the voice loop works before any tool-calling exists.

**Ticket prefix:** VOICE

**Suggested build order:** VOICE-1 (push-to-talk capture) first — it's the entry
point and can be tested with a stub transcript. Then VOICE-2 (STT) and VOICE-3 (TTS)
independently against a stubbed conversation endpoint. VOICE-4 stitches the full
loop and proves multimodal parity once TEXT-2's endpoint is live.

**Key constraint (from research):** Alibaba's realtime voice models can *recognize*
Urdu speech but do **not** synthesize Urdu speech output. The spoken-reply path
(VOICE-3) must therefore be built behind an adapter so the Urdu voice source can be
chosen/swapped without touching capture or STT. Track this as an explicit risk.

**Sources:** Stakeholder grilling session (this conversation) — voice-first,
push-to-talk for MVP, multimodal; Alibaba Cloud AI Hackathon 2026 research (Qwen
speech input supports Urdu; speech output does not).

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| VOICE-1 | Push-to-talk capture | Done | Usman | TBD | TBD |
| VOICE-2 | Speech-to-text (STT) integration | Done | Usman | TBD | TBD |
| VOICE-3 | Text-to-speech (TTS) reply playback | To Be Done | TBD | TBD | TBD |
| VOICE-4 | End-to-end voice loop & multimodal parity | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
