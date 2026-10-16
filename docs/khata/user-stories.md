# User Stories — khata KHATA

## KHATA-1 — Customer registration (khata# + CNIC)
**As a** shopkeeper
**I want** to register a credit customer once with their name and CNIC and get back a khata number
**So that** every later transaction is by khata number (or CNIC if they forget it) with no typing at the counter

**Acceptance criteria** (from KHATA-1.md):
- When the shopkeeper registers a customer with name and CNIC, a customer record is created and a khata number is assigned and shown
- When a shop registers multiple customers, each khata number is unique within that shop
- Once a customer is registered, their CNIC is stored and can later resolve them if the khata number is forgotten
- Registration can be completed by typing (recommended for the 13-digit CNIC) or by voice, since the platform is multimodal

_Tickets: docs/khata/KHATA-1.md_

## KHATA-2 — Log udhaar tool (goods on credit)
**As a** shopkeeper
**I want** giving goods on credit to add to a customer's udhaar balance immediately
**So that** "khata 12 pe 450 udhaar" raises khata 12's balance by 450 with a quick undo if I misspoke

**Acceptance criteria** (from KHATA-2.md):
- When khata 12 currently owes 0 and 450 of udhaar is logged against khata 12, khata 12's balance becomes 450
- When udhaar is logged, a ledger entry records the amount, timestamp, and link to the originating sale if any
- Since udhaar logging is a commit-with-undo action, it commits immediately when logged and can be undone
- When the shopkeeper undoes 450 that was just logged to khata 12, khata 12's balance returns to its prior value

_Tickets: docs/khata/KHATA-2.md_

## KHATA-3 — Udhaar repayment tool (approval-gated)
**As a** shopkeeper
**I want** a customer's repayment confirmed before it posts
**So that** a mis-heard amount on money coming in doesn't start a dispute — "khata 12 ne 200 jama karaye" should ask me to approve before reducing the balance

**Acceptance criteria** (from KHATA-3.md):
- When the shopkeeper says a customer repaid an amount and the repayment tool is invoked, the parsed customer and amount are shown and the shopkeeper must approve before it commits
- When khata 12 owes 450 and a repayment of 200 is approved, khata 12's balance becomes 250 and a payment entry is recorded
- When a repayment awaits approval and the shopkeeper rejects it, no payment is recorded and the balance is unchanged
- When both mention a khata number but the intent is "repaid / jama" rather than "gave / diye", the repayment (money-in) path is used, not the logging path

_Tickets: docs/khata/KHATA-3.md_

## KHATA-4 — Udhaar lookup (by khata# or CNIC fallback)
**As a** shopkeeper
**I want** to ask how much a customer owes and hear the answer
**So that** "khata 12 ka kitna udhaar hai?" replies with the balance — and if the khata number is forgotten, I can look them up by CNIC

**Acceptance criteria** (from KHATA-4.md):
- When khata 12 owes 250 and the shopkeeper asks the balance for khata 12, the reply states 250 and it is shown on screen
- When a customer forgot their khata number and the shopkeeper looks them up by CNIC, the correct customer and balance are returned
- When a khata number or CNIC has no record, the shopkeeper is told no such customer exists rather than a wrong balance
- A balance lookup is read-only — no ledger entry or balance change results from asking

_Tickets: docs/khata/KHATA-4.md_
