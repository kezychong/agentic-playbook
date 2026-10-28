---
name: ap-basic-ad-buying-recipe
description: "Core two-campaign paid-media recipe: testing, scaling, and test/keep/pause/kill/scale decisions."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Basic Ad-Buying Recipe

Use this whenever the owner asks what to do with ads.

## Machine
- Testing campaign: finds winners cheaply with equal budget per concept.
- Scaling campaign: concentrates spend on proven winners.

## Inputs
- Offer being sold.
- Primary result type, such as sale, lead, booked call, application, or purchase.
- Target cost per result.
- Exact date range.
- Ad/ad-set numbers from the platform.
- Tracker row status, if available.

## Decisions
- Target Cost means target cost per result for the selected result type, not automatically cost per lead.
- Test: new concept enters testing at about 1 x Target Cost per day.
- Keep: near target or too little spend to judge.
- Pause recommendation: tracking is unclear, offer/result definition is missing, or spend is risky but signal is not clean enough to kill.
- Kill recommendation: spend >= 2 x Target Cost with zero or one result, or cost per result >= 1.5 x Target Cost with enough signal.
- Scale recommendation: about 10 or more results at or below Target Cost.

## Rules
- Never kill a winner only because result count is low.
- Never use account totals for cost-per-result decisions.
- Never execute without approval.

<!-- Agentic Playbook — by Kezy -->
