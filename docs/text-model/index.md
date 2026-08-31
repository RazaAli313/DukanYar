# Epic — Text ⇄ Model (Dev 1)

**Goal:** Let a shopkeeper type a message and get a natural conversational reply from
the model in their own language (Urdu / Roman-Urdu / English), rendered in a chat UI
and persisted as history. This pillar proves the model *understands and responds*
before any tool-calling exists — and it publishes the conversation endpoint that the
VOICE pillar reuses. No tools, no business logic in Phase 1.

**Ticket prefix:** TEXT

**Suggested build order:** TEXT-1 (chat input UI) and TEXT-2 (model integration)
first — TEXT-1 can build against a stubbed reply while TEXT-2 wires the real model,
then they meet. TEXT-3 (persistence) and TEXT-4 (language handling & persona) layer
on once a round-trip works.

**Contract published to VOICE:** a single "send a user message, get an assistant
reply" endpoint. VOICE calls it with transcribed text and never depends on this
pillar's internals.

**Sources:** Stakeholder grilling session (this conversation) — voice-first but
multimodal (typing alongside voice), Urdu-native interaction; Alibaba Cloud AI
Hackathon 2026 (use Qwen models).

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| TEXT-1 | Chat input UI | Done | Usman | — | — |
| TEXT-2 | Model integration & streaming reply | Done | Usman | — | — |
| TEXT-3 | Conversation persistence & history | To Be Done | TBD | TBD | TBD |
| TEXT-4 | Urdu / Roman / English handling & assistant persona | Done | Usman | — | — |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
