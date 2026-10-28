---
name: ap-meta-account-readiness
description: "Read-only account readiness check for Meta connector access, scope, account selection, and tool availability."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Meta Account Readiness

Use before any review, launch plan, or report.

## Required Checks
1. Confirm the connector is Meta's hosted Ads connector.
2. Confirm the login flow used a Meta or Facebook-owned domain.
3. Confirm the account label the owner wants reviewed.
4. Confirm current scope. Start read-only.
5. List available ad accounts.
6. List campaigns, ad sets, and ads for the selected account.
7. Pull a tiny read-only insights sample at ad-set or ad level.

## Output
Return:
- ready: yes/no.
- selected account label.
- scope tier.
- visible campaigns/ad sets/ads.
- missing setup items.
- next safe step.

## Stop Conditions
- No account is visible.
- Connector is not official Meta.
- Scope is unclear.
- Any action would change spend or status.
