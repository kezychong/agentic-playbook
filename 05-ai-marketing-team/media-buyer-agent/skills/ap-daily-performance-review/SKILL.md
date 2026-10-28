---
name: ap-daily-performance-review
description: "Daily review workflow that turns platform numbers into keep, pause, kill, graduate, scale, and watch recommendations."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Daily Performance Review

Use for daily or ad-hoc review.

## Inputs
- Exact date range.
- Offer being sold.
- Primary result type, such as sale, lead, booked call, application, or purchase.
- Target cost per result.
- Current testing campaign rows.
- Current scaling campaign rows.
- Ad-set or ad-level spend, results, cost per result, frequency, CPM, and status.
- Tracker status if available.

## Workflow
1. State the source and date range.
2. Classify each campaign: testing, scaling, old ride-out, or unrelated.
3. Review only current testing items for pause, kill, or graduate.
4. Review scaling items for fatigue, not default kills.
5. Produce proposal groups:
   - keep
   - pause recommended
   - kill recommended
   - graduate recommended
   - scale recommended
   - watch
   - setup issue

## Decision Math
- Target Cost means target cost per result for the selected result type. Do not assume it means cost per lead unless the owner says the result is a lead.
- Kill recommended: spend >= 2 x Target Cost with zero or one result.
- High-cost kill recommended: cost per result >= 1.5 x Target Cost after enough spend.
- Pause recommended: tracking is unclear, offer/result definition is missing, or spend is risky but signal is not clean enough to kill.
- Graduate recommended: about 10 or more results at or below Target Cost.
- Fatigue flag: cost per result 20-30% above Target Cost over 7 days, high frequency, or CPM rising with no result improvement.

## Output
For each recommendation include:
- item label
- date range
- spend
- results
- cost per result
- reason
- approval needed

Do not execute changes in this skill.
