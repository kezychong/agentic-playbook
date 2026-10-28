---
name: ap-tracker-and-creative-json-update
description: "Approval-gated template for updating tracker rows and each creative's JSON data without client-specific fields."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Tracker and Creative JSON Update

Use when the owner wants tracker rows and creative JSON records updated after a review, launch,
kill, graduate, scale, or creative QA decision.

## What This Skill Does

- Reads the tracker first.
- Reads the creative JSON first.
- Matches each tracker row to one creative record by stable creative ID.
- Produces a dry-run change set before writing.
- Updates only owner-approved fields.
- Keeps tracker rows and creative JSON records in sync.

## Required Inputs

- Tracker source and tab/table label.
- Creative JSON source or path.
- Stable creative ID field.
- Tracker row ID or explicit range.
- Current date range and source for performance numbers.
- Owner-approved action and exact fields to update.

## Generic Creative JSON Shape

Each creative should have one record:

```json
{
  "creative_id": "creative_001",
  "name": "Short human label",
  "concept": "Concept or angle",
  "status": "testing",
  "tracker": {
    "source": "tracker label",
    "tab": "Testing",
    "row_id": "2"
  },
  "qa": {
    "decision": "approve",
    "notes": []
  },
  "performance": {
    "date_range": "YYYY-MM-DD to YYYY-MM-DD",
    "spend": 0,
    "results": 0,
    "cost_per_result": null
  },
  "decision": {
    "recommended_action": "watch",
    "approved_action": null,
    "approval_reference": null,
    "updated_at": null
  }
}
```

## Workflow

1. Read tracker headers and current rows.
2. Read and parse the creative JSON as structured JSON.
3. Match each requested row to exactly one creative record by `creative_id`.
4. Refuse if the match is missing, duplicated, or based only on a fuzzy name.
5. Build a dry-run table with:
   - tracker row/range
   - creative ID
   - current tracker values
   - proposed tracker values
   - current JSON fields
   - proposed JSON fields
6. Ask for approval before writing.
7. After approval, update only the named tracker fields and JSON fields.
8. Preserve unknown JSON fields.
9. Report exactly what changed and what was left unchanged.

## Common Field Updates

Tracker row fields:
- status
- launch date
- end date
- action
- spend
- results
- cost per result
- notes

Creative JSON fields:
- `status`
- `tracker.row_id`
- `qa.decision`
- `qa.notes`
- `performance.date_range`
- `performance.spend`
- `performance.results`
- `performance.cost_per_result`
- `decision.recommended_action`
- `decision.approved_action`
- `decision.approval_reference`
- `decision.updated_at`

## Refusals

Refuse to write when:
- owner approval is missing.
- creative ID is missing or duplicated.
- tracker row identity is uncertain.
- the requested update would overwrite a frozen row's performance fields.
- the JSON cannot be parsed as valid JSON.
- the change would delete unknown fields.
- the requested value is not backed by a source/date range.

## Output

Before approval, return:
- matched creative IDs.
- proposed tracker changes.
- proposed JSON changes.
- fields intentionally left unchanged.
- exact approval sentence needed.

After approval, return:
- executed tracker changes.
- executed JSON changes.
- any skipped fields and why.
- source and date range used.

<!-- Agentic Playbook — by Kezy -->
