### KHATA-1 — Customer registration (khata# + CNIC)

| Field | Value |
| :---- | :---- |
| Ticket ID | KHATA-1 |
| Ticket Name | Customer registration (khata# + CNIC) |
| Status | To Be Done |
| Priority | P1 — High |
| Dependencies | FND-2 (migration convention), AUTH-3 (shop scoping) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — khata# primary id, CNIC fallback anchor; one-time typed registration, voice thereafter; multimodal |

**Description:** As a shopkeeper, I want to register a credit customer once with their
name and CNIC and get back a khata number, so that every later transaction is by khata
number (or CNIC if they forget it) with no typing at the counter.

**Acceptance Criteria:**
```gherkin
Feature: Khata — customer registration

  Scenario: New customer gets a khata number
    Given the shopkeeper registers a customer with name and CNIC
    Then a customer record is created and a khata number is assigned and shown

  Scenario: Khata number is unique per shop
    Given a shop registers multiple customers
    Then each khata number is unique within that shop

  Scenario: CNIC is captured for fallback lookup
    Given a customer is registered
    Then their CNIC is stored and can later resolve them if the khata number is forgotten

  Scenario: Registration is available by voice or typing
    Given the platform is multimodal
    Then registration can be completed by typing (recommended for the 13-digit CNIC) or by voice
```
