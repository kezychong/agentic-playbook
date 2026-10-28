> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---

# Project Farming — Install & Use

## What it does

Runs a full, honest review of any project against its own plan. It finds the plan (roadmap, README, task board, whatever states the intent), checks what's actually built and running by looking at the real thing (not trusting the docs), and hands you back a scored gap report: what's faithful, what's drifted, what got abandoned, and what quietly got replaced without anyone deciding to. It's an assessment, not a fix. You decide what to act on.

## What you need first

The Claude app or the Codex app. That's it.

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in ~/Downloads/ap-project-farming.zip so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Tell your agent `/ap-project-farming` and it should ask which project you want reviewed and where its plan lives.

## How to use it

1. Point it at a project: a build, a content system, an agent setup, anything with a stated plan somewhere.
2. Say "do a comprehensive review of this project against the plan" or "audit this."
3. It reports back with a faithfulness score out of 10, ranked gaps with evidence, and a list of quick wins versus bigger structural fixes.
4. You decide what to fix and in what order. It does not touch anything by default.

Example: "Do a comprehensive review of my onboarding project against the plan and tell me what's actually built."

## Works with

If you also installed `ap-orchestrator-astra`, this skill uses it: the strongest model plans the review and judges the findings, and cheaper models do the reading in parallel. It works fine on its own too, just more slowly on a big project.

## What it will NOT do

- It will not fix anything on its own. It reports, you decide.
- It will not take a doc's word for it. It checks the real files, logs, and URLs before scoring anything faithful.
- It will not sample a few files and call it done. A real review checks the whole project.


<!-- Agentic Playbook — by Kezy -->
