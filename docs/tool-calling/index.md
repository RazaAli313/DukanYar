# Epic — Tool-Calling & Orchestration (Phase 2)

**Goal:** Give the model the ability to *act*, not just talk. Introduce a tool
registry, the orchestration loop that turns a text/voice message into tool calls and
a reply, and the risk-tiered confirm/undo framework — so every feature epic (SALE,
KHATA, EXP, RPT) can plug in its own tools as additive files without editing a
central router. This is the bridge between the Phase-1 pillars and the Phase-3
features.

**Ticket prefix:** TOOL

**Suggested build order:** TOOL-1 (registry) first — it defines the plug-in contract
every feature depends on. Then TOOL-2 (orchestration loop) which consumes the
registry. TOOL-3 (confirm/undo) and TOOL-4 (on-screen action confirmation) layer on
and are largely independent of each other.

**Depends on:** TEXT-2 (conversation endpoint), VOICE-2 (transcript feeds same
endpoint). Both channels reuse this orchestration unchanged.

**Sources:** Stakeholder grilling session (this conversation) — modular pipeline
(STT → tool-calling → TTS), registry pattern to avoid merge conflicts, risk-tiered
commit model (approval for money-in; commit+undo for logging).

| ID | Name | Status | Build Engineer | QA | DM |
| :---- | :---- | :---- | :---- | :---- | :---- |
| TOOL-1 | Tool registry & schema convention | To Be Done | TBD | TBD | TBD |
| TOOL-2 | Model tool-calling orchestration loop | To Be Done | TBD | TBD | TBD |
| TOOL-3 | Risk-tiered confirmation & undo framework | To Be Done | TBD | TBD | TBD |
| TOOL-4 | On-screen action confirmation | To Be Done | TBD | TBD | TBD |
| **Total** |  |  | **TBD** | **TBD** | **TBD** |

<!--
Estimate hours (BE/FE, on each ticket) and QA/DM hours (index-only) were not
provided by the stakeholder and have not been guessed — fill in once estimation
happens, then recompute the Total row.
-->
