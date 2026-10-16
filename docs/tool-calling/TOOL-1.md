### TOOL-1 — Tool registry & schema convention

| Field | Value |
| :---- | :---- |
| Ticket ID | TOOL-1 |
| Ticket Name | Tool registry & schema convention |
| Status | To Be Done |
| Priority | P0 — Blocker |
| Dependencies | TEXT-2 (conversation endpoint) |
| Estimate | BE: TBD \| FE: TBD |
| Source References | Stakeholder grilling session (this conversation) — registry pattern so feature tools are additive files, not central-router edits |

**Description:** As an engineer, I want each backend action exposed to the model as a
self-registering tool with a declared schema, so that feature epics add tools by
dropping in a new file rather than editing a shared router — keeping merge conflicts
near zero.

**Acceptance Criteria:**
```gherkin
Feature: Tool-calling — registry and schema convention

  Scenario: A tool self-registers from its own file
    Given a new tool is defined in its own module
    When the backend starts
    Then the tool is discovered and available to the model without editing any central list

  Scenario: Each tool declares a machine-readable schema
    Given a registered tool
    Then it exposes a name, description, and typed parameter schema the model can call against

  Scenario: Adding a tool causes no shared-file conflict
    Given two engineers each add a different tool on separate branches
    When both branches merge
    Then no shared registry file was edited by either, so there is no conflict

  Scenario: Duplicate tool names are rejected
    Given two tools register the same name
    Then startup fails with a clear error rather than silently shadowing one
```
