---
name: ap-approval-gated-actions
description: "Safety gate for all Meta writes, live spend, status, budget, tracker, and launch changes."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Approval-Gated Actions

Use before any platform write or live action.

## Actions That Require Approval
- launch
- create a campaign, ad set, or ad, even paused
- duplicate an existing campaign, ad set, or ad as a new paused object
- unpause
- pause
- kill
- edit campaign, ad set, or ad settings
- increase budget
- decrease budget when it changes delivery
- edit tracker row
- edit creative JSON record
- send external message

## Approval Must Include
- action
- account or campaign/ad/ad-set label
- budget or status change
- source campaign/ad-set/ad label when duplicating
- whether the action is chat-only, a paused platform write, or a live spend change
- timing
- owner confirmation in the same conversation

## If Approval Is Missing
Do not execute. Reply with:
- recommendation
- risk
- exact approval sentence needed

## If Approval Is Present
Before executing, repeat:
- what will change
- what will not change
- rollback path
- source used

Then label result executed.

<!-- Agentic Playbook — by Kezy -->
