# User Stories — tool-calling TOOL

## TOOL-1 — Tool registry & schema convention
**As an** engineer
**I want** each backend action exposed to the model as a self-registering tool with a declared schema
**So that** feature epics add tools by dropping in a new file rather than editing a shared router — keeping merge conflicts near zero

**Acceptance criteria** (from TOOL-1.md):
- When a new tool is defined in its own module and the backend starts, the tool is discovered and available to the model without editing any central list
- A registered tool exposes a name, description, and typed parameter schema the model can call against
- When two engineers each add a different tool on separate branches and both branches merge, no shared registry file was edited by either, so there is no conflict
- If two tools register the same name, startup fails with a clear error rather than silently shadowing one

_Tickets: docs/tool-calling/TOOL-1.md_

## TOOL-2 — Model tool-calling orchestration loop
**As a** shopkeeper
**I want** a single message to trigger the right action(s) and get a reply, with the platform's loop selecting tools, executing them, and summarizing the result back to the model
**So that** saying "khata 12 pe 2 coke 450 udhaar" records the sale, updates inventory, and logs the udhaar in one turn

**Acceptance criteria** (from TOOL-2.md):
- When a registered tool matches the shopkeeper's intent and they send a message, the model selects that tool with parameters extracted from the message
- When a message implies several actions (sale + inventory + udhaar) and the loop runs, all required tools execute and the reply reflects the combined result
- A message arriving from either the text UI or the voice pillar flows through the identical orchestration loop
- If a tool raises an error mid-loop, the shopkeeper is told what failed and no partial claim of success is made

_Tickets: docs/tool-calling/TOOL-2.md_

## TOOL-3 — Risk-tiered confirmation & undo framework
**As a** shopkeeper
**I want** risky money-in actions to be confirmed before they commit, and routine logging to commit immediately with a quick undo
**So that** my ledger is protected without every action costing an extra step

**Acceptance criteria** (from TOOL-3.md):
- When a tool classified as approval-required (e.g. udhaar repayment, payment/finance) is about to be called by the model, the shopkeeper is shown the parsed action and must confirm before it writes
- When a tool classified as commit-with-undo (e.g. udhaar logging, expense) is called, it commits immediately and a prominent undo is available
- When the shopkeeper undoes a commit-with-undo action that just committed, its effects are reversed and the ledger returns to its prior state
- Each tool declares approval-required or commit-with-undo, and the framework enforces that tier without per-call special-casing

_Tickets: docs/tool-calling/TOOL-3.md_

## TOOL-4 — On-screen action confirmation
**As a** shopkeeper
**I want** every action the AI takes shown clearly on screen — amount, items, customer/khata
**So that** money is never ambiguous even when the spoken reply is brief or the Urdu voice is unavailable

**Acceptance criteria** (from TOOL-4.md):
- When the model executes an action from a message, the app shows a structured card of what was recorded (amount, items, khata/customer)
- When a spoken reply is produced, the same information is also shown on screen, never voice-only
- When a field was uncertain (e.g. unknown item, unclear amount), it is visually flagged so the shopkeeper can correct it
- When an action was committed (undo) or awaits approval (approve), the matching control is present on the confirmation card

_Tickets: docs/tool-calling/TOOL-4.md_
