# User Stories — text-model TEXT

## TEXT-1 — Chat input UI
**As a** shopkeeper
**I want** to type a message and see the conversation as a chat thread
**So that** I can interact with the assistant by text when voice isn't practical (noisy shop, quiet needed, or to correct a misheard command)

**Acceptance criteria** (from TEXT-1.md):
- Typing a message and submitting it makes it appear in the thread as a "user" bubble, and the input field clears and is ready for the next message
- When the assistant reply is received, it appears in the thread as an "assistant" bubble beneath the shopkeeper's message
- While a reply has not yet arrived, a visible pending indicator is shown until the reply arrives or an error is displayed
- A message written in Urdu script renders right-to-left and remains readable

_Tickets: docs/text-model/TEXT-1.md_

## TEXT-2 — Model integration & streaming reply
**As a** shopkeeper
**I want** the assistant's replies to come from the language model, exposed through a single conversation endpoint that voice can also reuse
**So that** I get relevant natural answers, and the voice pillar can send transcribed text through the same endpoint without duplicating this logic

**Acceptance criteria** (from TEXT-2.md):
- When a user message is submitted to the conversation endpoint and the backend calls the language model, the model's reply is returned to the caller and rendered in the thread
- The endpoint behaves identically regardless of whether the source message was typed (text UI) or transcribed (voice pillar)
- When the model supports streaming, partial reply text is delivered progressively rather than only after the full reply is ready
- If the model call fails or times out, the caller receives a clear error and the UI shows a retry affordance without losing the typed message

_Tickets: docs/text-model/TEXT-2.md_

## TEXT-3 — Conversation persistence & history
**As a** shopkeeper
**I want** my conversation saved and reloaded
**So that** I can see earlier messages after closing and reopening the app, and so the assistant can use recent context within a conversation

**Acceptance criteria** (from TEXT-3.md):
- When the shopkeeper sends a message and receives a reply, both the user message and the assistant reply are stored against their conversation
- When the shopkeeper reopens the app on an existing conversation, the previous messages are shown in order
- When a shopkeeper loads their history, only their own shop's messages are returned, never another shop's, even when other shops have conversations
- When a new message is sent on a conversation with prior messages, the backend includes recent prior turns as context in the model call

_Tickets: docs/text-model/TEXT-3.md_

## TEXT-4 — Urdu / Roman / English handling & assistant persona
**As a** shopkeeper
**I want** the assistant to understand how I actually speak — Urdu mixed with Roman-Urdu and English product words — and to reply like a helpful shop employee
**So that** the interaction feels natural rather than like a foreign chatbot

**Acceptance criteria** (from TEXT-4.md):
- Given a code-switched message like "2 coke aur 1 chips reh gaye", the assistant responds coherently to the mixed Urdu-English message
- When the shopkeeper writes in Urdu (or Roman-Urdu), the assistant's reply is in the same language register, not defaulted to formal English
- With a system persona defining a polite, concise shop-employee assistant, the assistant's replies are short, respectful, and shopkeeper-appropriate rather than verbose or generic
- When the shopkeeper's message is ambiguous or unreadable, the assistant asks a short clarifying question instead of guessing

_Tickets: docs/text-model/TEXT-4.md_
