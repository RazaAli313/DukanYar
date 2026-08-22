# User Stories — expense EXP

## EXP-1 — Expenses schema & categories
**As a** shopkeeper
**I want** expenses stored with an amount, an optional category, and a date
**So that** money going out is captured and can later feed profit summaries

**Acceptance criteria** (from EXP-1.md):
- Once the expense migration has run, an expenses table exists with amount, optional category, note, and date, and each expense belongs to exactly one shop
- When a shopkeeper logs an expense without naming a category, it is stored as uncategorized rather than rejected
- When an expense is created, it must have a positive amount

_Tickets: docs/expense/EXP-1.md_

## EXP-2 — Log-expense tool (commit + undo)
**As a** shopkeeper
**I want** to log an expense by voice or text
**So that** "bijli ka bill 3000" records a 3000 expense immediately with a quick undo

**Acceptance criteria** (from EXP-2.md):
- When the shopkeeper says "bijli ka bill 3000" and the log-expense tool runs, a 3000 expense is recorded with a category inferred as utilities/bijli if possible
- Once an expense is logged, it commits immediately and can be undone from the confirmation card
- When the shopkeeper mentions an expense with no amount, the assistant asks for the amount instead of recording zero

_Tickets: docs/expense/EXP-2.md_

## EXP-3 — Expense list & review
**As a** shopkeeper
**I want** to see my recent expenses on screen
**So that** I can review and correct what was logged

**Acceptance criteria** (from EXP-3.md):
- When expenses have been logged and the shopkeeper opens the expenses screen, their expenses are shown most recent first with amount, category and date
- When multiple shops have expenses, a shopkeeper sees only their own shop's expenses
- When a wrong expense is in the list, the shopkeeper can delete it

_Tickets: docs/expense/EXP-3.md_
