---
name: ap-creative-quality-gate
description: "Creative QA gate for mobile legibility, layout, claims, aspect ratio, and launch readiness."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Creative Quality Gate

Use before any ad goes live.

## Hard Rejects
- Headline unreadable at mobile feed scale.
- Garbled or misspelled text.
- Fake social UI or fake device frame.
- Unsupported hard claim.
- Wrong aspect ratio.
- Identifiable face without confirmed rights.
- Landing page or offer mismatch.
- Too many ideas in one creative.

## Review Sizes
- Feed scale: about 480 px wide.
- Thumbnail scale: about 150 px wide.
- Native aspect: 1:1, 4:5, or 9:16 as intended.

## Score
Return one of:
- approve
- revise
- reject

## Output
Include:
- decision
- failed gates
- exact fix
- launch readiness
- whether owner approval is still needed
