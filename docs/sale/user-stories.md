# User Stories — sale SALE

## SALE-1 — Product catalog & seed data
**As a** shopkeeper
**I want** a catalog of my products with price and stock, pre-seeded with a realistic set for the demo
**So that** sales can resolve items and track quantities, and "2 coke" always resolves

**Acceptance criteria** (from SALE-1.md):
- Once the catalog migration has run, a products table exists with name, sale price, stock quantity, and cost price, and products are scoped to a shop
- Applying seed data to a fresh demo shop creates roughly 15–20 realistic products with sensible prices and opening stock
- A product like "Coca-Cola 345ml" can store alternate names (e.g. "coke", "thanda") to aid later resolution
- When a shopkeeper opens the inventory screen, they see each product with its current stock and price

_Tickets: docs/sale/SALE-1.md_

## SALE-2 — Item resolution (fuzzy match + confirm + auto-add)
**As a** shopkeeper
**I want** spoken item names like "coke" or "thanda" matched to the right product, with my pick shown so I can correct it
**So that** sales record against the correct SKU without me stating exact names

**Acceptance criteria** (from SALE-2.md):
- When the shopkeeper says "2 coke" and item resolution runs, it matches the most likely catalog product and shows which one it picked
- When resolution picks the wrong size or product, the shopkeeper can correct it from the confirmation card without redoing the whole sale
- When a spoken item matches no product, the shopkeeper is prompted to add it once, after which it resolves in future
- When two products match equally well, the shopkeeper is asked which one instead of a silent arbitrary pick

_Tickets: docs/sale/SALE-2.md_

## SALE-3 — Record-sale tool (cash vs udhaar by khata presence)
**As a** shopkeeper
**I want** to record a sale by voice or text with the amount I state
**So that** "2 coke 1 chips 450" logs a sale of 450, recorded as credit against a named khata number or as cash otherwise

**Acceptance criteria** (from SALE-3.md):
- When the shopkeeper says an item list and amount with no khata number and the record-sale tool runs, a cash sale is logged with its line items and the stated total
- When the shopkeeper names a khata number, the sale is recorded as udhaar and handed to the khata ledger for that customer
- When the shopkeeper states 450 for the sale, 450 is stored as the sale total regardless of catalog price sums
- Once a sale is recorded, it commits immediately and can be undone from the confirmation card

_Tickets: docs/sale/SALE-3.md_

## SALE-4 — Inventory decrement & out-of-stock flagging
**As a** shopkeeper
**I want** stock to drop automatically when I record a sale
**So that** inventory stays current without me stating counts, even when stock would go negative

**Acceptance criteria** (from SALE-4.md):
- When Coke has 24 in stock and a sale of 2 Coke is recorded, Coke stock becomes 22
- When a sale of 2 Coke that decremented stock is undone, the 2 units are returned to stock
- When Coke shows 1 in stock and a sale of 2 Coke is recorded, the sale still records and the resulting negative/short stock is flagged on screen
- When a sale records multiple items, all item decrements and the sale write succeed together or not at all

_Tickets: docs/sale/SALE-4.md_
