# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../../08-setup-guides-tools-connections/manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

---
stage: draft
---

## What it does

Audits your skills and automations and makes them shorter, cheaper, and better. Most skills were written for a weaker model, so they're padded with handholding the smarter model no longer needs. This one reads the whole thing, traces a real run if one exists, cuts the instructions that aren't earning their keep, and checks three things at once: speed, token cost, and how good the output actually is. You get ranked recommendations with the specific evidence behind each one. It only changes anything once you say go.

## What you need first

Your agent app. That's it.

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in the selected complete skill folder so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Type `/ap-skill-levelup` and it should ask which skill, automation, or workflow you want tuned up.

## How to use it

1. Point it at one thing that feels slow, expensive, or bloated: a skill, a recurring job, an agent workflow, a content system. Or point it at everything and say "audit all my skills."
2. Say "tune up this skill", "trim this down", or "why is this so slow."
3. It reports back with ranked recommendations, each tagged to the axis it improves (speed, cost, or quality) with the evidence behind it, and for cuts, how much shorter the skill gets.
4. Approve what you want applied. It saves a copy of the original first, applies the change, then tests before and after so you can see the difference.

Example: "Audit all my skills and tell me which ones are bloated. Start with the worst one."

## What it will NOT do

- It will not change anything without your approval first.
- It will not optimize one thing (like speed) while quietly making another thing (like output quality) worse. It checks all three every time.
- It will not cut the parts that carry your own preferences, standards, and approval rules. Those are the reason your skills exist.
- It will not skip the before/after test once a change is approved.

---

*Part of the Agentic Playbook build.*
