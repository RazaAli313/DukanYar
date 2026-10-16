# User Stories — voice VOICE

## VOICE-1 — Push-to-talk capture
**As a** shopkeeper
**I want** to press and hold a big mic button to record what I say and release to send
**So that** I can capture a command reliably in a noisy shop without accidental triggers

**Acceptance criteria** (from VOICE-1.md):
- Pressing and holding the mic button while speaking captures audio while held, and releasing the button ends capture and submits the audio
- The first time the mic button is pressed, the browser permission prompt is triggered, and if denied, a clear message explains that voice needs mic access
- While the shopkeeper is holding the mic button, a clear recording indicator is shown for the duration of capture
- A momentary tap with no speech does not submit an empty or near-empty recording

_Tickets: docs/voice/VOICE-1.md_

## VOICE-2 — Speech-to-text (STT) integration
**As a** shopkeeper
**I want** my spoken Urdu turned into text
**So that** the assistant can process what I said through the same conversation endpoint the text pillar uses

**Acceptance criteria** (from VOICE-2.md):
- When a recording of an Urdu sentence is sent to the speech-to-text service, a text transcript of the utterance is returned
- Once a transcript is produced, it is displayed to the shopkeeper as the recognized text before or alongside the assistant's reply
- The produced transcript is submitted to the same conversation endpoint that typed messages use, tagged as the voice channel
- If the recording is silent or unintelligible and transcription returns empty or low-confidence text, the shopkeeper is prompted to try again rather than sending garbage to the model

_Tickets: docs/voice/VOICE-2.md_

## VOICE-3 — Text-to-speech (TTS) reply playback
**As a** shopkeeper
**I want** to hear the assistant's reply spoken aloud, through a spoken-reply path that sits behind a swappable adapter given the Urdu voice-source risk
**So that** I don't have to look at the screen while serving a customer

**Acceptance criteria** (from VOICE-3.md):
- When the assistant returns a text reply and text-to-speech is invoked, the reply is played back as audio to the shopkeeper
- The text-to-speech provider is accessed through an adapter interface, so swapping the Urdu voice provider requires no change to capture (VOICE-1) or STT (VOICE-2)
- The assistant reply is always displayed as text in addition to being spoken, since voice output may be unavailable or muted
- If text-to-speech fails, the shopkeeper still sees the reply as text and the app does not crash or hang

_Tickets: docs/voice/VOICE-3.md_

## VOICE-4 — End-to-end voice loop & multimodal parity
**As a** shopkeeper
**I want** the full speak → hear loop to work in one flow, with voice and text interchangeable
**So that** I can start a thought by voice and finish it by typing (or vice versa) within the same conversation

**Acceptance criteria** (from VOICE-4.md):
- When the shopkeeper holds the mic, speaks an Urdu sentence, and releases, the utterance is transcribed, sent to the model, and the reply is both shown and spoken, with the whole loop completing without manual steps between stages
- When the shopkeeper sends one message by voice and the next by typing, both appear in the same conversation thread in order
- When a voice message has received a reply and the shopkeeper types a follow-up, the assistant treats it as a continuation with the prior voice turn as context
- When a spoken command was mis-transcribed, the shopkeeper can correct it by typing without restarting the conversation

_Tickets: docs/voice/VOICE-4.md_
