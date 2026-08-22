# User Stories — catalog CATLG

## CATLG-1 — Add product by voice
**As a** shopkeeper
**I want** to add a new product by voice — "naya item Lays 50 rupay 30 packet"
**So that** I can grow my catalog without typing, with the parse confirmed before commit since this writes the catalog everything depends on

**Acceptance criteria** (from CATLG-1.md):
- When the shopkeeper says a product name, price, and opening quantity and the add-product tool runs, a confirmation card shows the parsed name, price, and quantity for approval
- When the parsed product is approved, it is created in the catalog with the stated price and opening stock
- When a product with a very similar name already exists, the shopkeeper is warned and asked whether to add or adjust the existing one
- When the spoken description lacks a price or quantity, the assistant asks for the missing field instead of guessing

_Tickets: docs/catalog/CATLG-1.md_

## CATLG-2 — Adjust / restock by voice
**As a** shopkeeper
**I want** to restock or correct a product by voice — "Coke ki 24 bottle aur aa gayi" or "Coke ab 60 ka"
**So that** inventory and prices stay current without typing

**Acceptance criteria** (from CATLG-2.md):
- When Coke has 22 in stock and the shopkeeper says 24 more Coke arrived, Coke stock becomes 46
- When Coke sells for 50 and the shopkeeper says Coke is now 60, Coke's price becomes 60 for future sales
- When the shopkeeper counts shelf stock and states the true number, the product's stock is set to that number
- When the spoken product name is fuzzy, it resolves to the existing catalog item (reusing sale item resolution), not a new product

_Tickets: docs/catalog/CATLG-2.md_

## CATLG-3 — Proactive low-stock alerts
**As a** shopkeeper
**I want** to be told when an item is running low without asking
**So that** I restock before it runs out — "Coke khatam ho raha hai"

**Acceptance criteria** (from CATLG-3.md):
- When a product's stock drops to or below its low-stock threshold and the next sale decrements it past the threshold, a low-stock alert is raised for that product
- When a low-stock alert is raised, the shopkeeper sees it in the app (and, if enabled, is spoken it)
- When a product already alerted as low has further sales, it does not re-alert on every subsequent sale until restocked above threshold
- When the product is restocked above its threshold while a low-stock alert is active, the alert clears

_Tickets: docs/catalog/CATLG-3.md_
