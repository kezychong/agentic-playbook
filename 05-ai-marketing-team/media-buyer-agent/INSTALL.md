> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: draft
---

# Media Buyer Agent - Install

## Who this is for
- A business owner who runs Meta ads and wants daily or ad-hoc review help, but keeps the final say on spend, pauses, kills and budgets.
- Your main agent already runs and answers you in chat.

## What is in this folder
- `media-buyer-onboarding-pack` - the part YOU read: questionnaire, spend-safety agreement, connection guides, first-week runbook, go-live checklist, QA scenarios.
- `media-buyer-distribution` - the part your AGENT reads: identity, operating rules, config templates and examples.
- `skills/` - the nine canonical Media Buyer Agent skills.

## Stage before installation
Point your agent at this folder and say:

"Read INSTALL.md, then stage my Media Buyer Agent after the onboarding questionnaire. Start at media-buyer-onboarding-pack/START-HERE.md. Do not install or connect anything."

## For the agent doing the install
Walk the owner through `media-buyer-onboarding-pack/START-HERE.md` in order. Stage a separate copy of `media-buyer-distribution`, copy the nine skill folders into its `skills/`, and fill placeholders from the owner's answers. Connect the ad account **read-only** first. Profile installation (for example `hermes profile install ./<staged copy> --name media-buyer`) needs separate approval and a check of the host's current profile schema. Run `media-buyer-onboarding-pack/QA-SCENARIOS.md` before any real spend decision. Never change budgets, status or creatives without the owner's explicit approval of that exact change.
