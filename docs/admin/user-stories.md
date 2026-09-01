# User Stories — admin ADMIN

## ADMIN-1 — Shops & users management
**As an** admin
**I want** to see and manage every shop and user on the platform
**So that** I can support shopkeepers, deactivate abusive accounts, and understand adoption

**Acceptance criteria** (from ADMIN-1.md):
- When shops exist across the platform and the admin opens the shops screen, all shops are listed with owner, creation date, and activity summary
- When the admin opens a shop that has users, its users and their roles are shown
- When the admin deactivates a shop or user that must be suspended, that account can no longer log in until reactivated
- When a shopkeeper attempts to open the admin shops screen, access is denied

_Tickets: docs/admin/ADMIN-1.md_

## ADMIN-2 — Voice & transcription monitoring
**As an** admin
**I want** to monitor voice usage and where transcription is failing
**So that** I can improve the model prompts, catch Urdu recognition gaps, and prove the voice pipeline works in the field

**Acceptance criteria** (from ADMIN-2.md):
- When voice interactions have occurred and the admin opens the monitoring screen, counts of voice vs text interactions over time are shown
- When some transcriptions had low confidence or triggered retries, they are listed so the admin can review recognition quality
- When a voice command failed to produce an action, the admin can see the transcript and the failure reason
- Monitoring that shows interaction metadata is restricted to admins and follows the platform's data-handling rules

_Tickets: docs/admin/ADMIN-2.md_

## ADMIN-3 — Audit log & system health
**As an** admin
**I want** an audit trail of significant actions and a basic system-health view
**So that** I can investigate issues and confirm the platform is up

**Acceptance criteria** (from ADMIN-3.md):
- When users perform account and money-affecting actions, an audit entry records who did what and when
- When the admin filters audit entries by shop, user, or action type, only matching entries are shown
- When the admin opens the health view, it shows service status and recent error rate at a glance
- An audit entry cannot be edited or deleted through the app, only viewed

_Tickets: docs/admin/ADMIN-3.md_
