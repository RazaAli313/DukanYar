### SALE-2 — Item resolution (fuzzy match + confirm + auto-add)

| Field | Value |
| :---- | :---- |
| Ticket ID | SALE-2 |
| Ticket Name | Item resolution (fuzzy match + confirm + auto-add) |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | SALE-1 (catalog), TOOL-4 (on-screen confirmation) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — hybrid resolution: fuzzy-match, show pick, undo to fix, auto-add unknown items |

**Description:** As a shopkeeper, I want spoken item names like "coke" or "thanda"
matched to the right product, with my pick shown so I can correct it, so that sales
record against the correct SKU without me stating exact names.

**Acceptance Criteria:**
```gherkin
Feature: Sales — item resolution

  Scenario: Fuzzy match to the most likely product
    Given the shopkeeper says "2 coke"
    When item resolution runs
    Then it matches the most likely catalog product and shows which one it picked

  Scenario: Wrong pick is correctable
    Given resolution picked the wrong size or product
    Then the shopkeeper can correct it from the confirmation card without redoing the whole sale

  Scenario: Unknown item is offered for quick add
    Given a spoken item matches no product
    Then the shopkeeper is prompted to add it once, after which it resolves in future

  Scenario: Ambiguous match asks rather than guesses silently
    Given two products match equally well
    Then the shopkeeper is asked which one instead of a silent arbitrary pick
```
