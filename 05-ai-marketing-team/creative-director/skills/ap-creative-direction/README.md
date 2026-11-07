# Creative Direction

Agentic Playbook — **by Kezy**

Turn a video objective and permitted evidence into a reviewable production plan.

## Prerequisites

A clear objective, intended viewer, permitted sources, known rights and consent, practical production limit and named reviewers.

## Try it

> Create a local video canvas for fictional Company A. Use only the supplied fictional product note and screenshot. Mark missing proof. Do not call paid tools or publish anything.

## Expected output

A source register, claim ledger, format decision, video canvas, production handoff, hold list and next approval decision.

## Included files

- `templates/video-canvas.md` — blank planning surface.
- `templates/evidence-ledger.csv` — blank source, claim and consent register.
- `templates/review-handoff.md` — version and approval record.
- `examples/fictional-video-plan.json` — harmless checker fixture.
- `examples/invalid-video-plan.json` — fictional blocked-action and missing-evidence fixture.
- `scripts/check_video_plan.py` — dependency-free structural gate.
- `scripts/test_check_video_plan.py` — offline regression tests.

The example statuses are illustrative test data, not real-world verification. The CSV is a blank planning register; the JSON checker uses the status values documented in the example plans.

## Limits

Runtime status: the package is an unexecuted source draft. Within it, only the checker has offline regression coverage. The creative workflow, integrations, renderers and external actions are untested. A passing file check is not a rights decision, quality review or permission to publish.