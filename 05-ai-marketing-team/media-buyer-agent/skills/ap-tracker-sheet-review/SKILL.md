---
name: ap-tracker-sheet-review
description: "Tracker/sheet workflow for row review, frozen-row protection, explicit ranges, and approval-gated row changes."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Tracker Sheet Review

Use when tracker rows matter to a review, launch, kill, graduate, or report.

## Principles
- Read first.
- Use explicit ranges or row labels.
- Never append blindly.
- Frozen rows stay frozen.
- Row changes require approval.

## Workflow
1. Identify tracker source and tab or table.
2. Read headers.
3. Find rows by stable labels, not by guessing.
4. Check launch date, end date, status, action, spend, results, and cost per result.
5. If a row is frozen, do not update performance numbers.
6. For a launch, prepare row values and explicit range.
7. For a kill or graduate, prepare end date, status, action, and freeze note.
8. If creative JSON also needs an update, hand off to ap-tracker-and-creative-json-update.

## Refusals
Refuse when:
- row identity is uncertain.
- owner has not approved a row write.
- the update would use append-style behavior.
- a frozen row would be overwritten.

## Output
Return a dry-run table:
- row
- proposed fields
- old value summary
- new value summary
- approval sentence needed

<!-- Agentic Playbook — by Kezy -->
