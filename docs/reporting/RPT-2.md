### RPT-2 — Daily sales & profit summary tool

| Field | Value |
| :---- | :---- |
| Ticket ID | RPT-2 |
| Ticket Name | Daily sales & profit summary tool |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | RPT-1 (views), TOOL-2 (orchestration) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — "aaj ki sale kitni hui?"; profit uses cost price |

**Description:** As a shopkeeper, I want to ask today's sales and profit and hear the
answer, so that "aaj ki sale kitni hui?" replies with the day's total and profit.

**Acceptance Criteria:**
```gherkin
Feature: Reporting — daily sales and profit

  Scenario: Today's sales total is reported
    Given sales were recorded today
    When the shopkeeper asks for today's sales
    Then the reply states the sum of today's sale totals and shows it on screen

  Scenario: Profit uses cost price
    Given products have cost prices
    When profit is reported
    Then profit is computed as sale totals minus cost of goods sold for the period

  Scenario: A period with no sales reports zero clearly
    Given no sales today
    Then the reply states there were no sales today rather than erroring

  Scenario: Report is read-only
    Given a summary is requested
    Then no data is modified by asking
```
