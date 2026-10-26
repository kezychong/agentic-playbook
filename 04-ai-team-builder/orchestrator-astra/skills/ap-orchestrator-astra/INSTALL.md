# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../../08-setup-guides-tools-connections/manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

---
stage: draft
version: "1.0.0"
---

# Orchestrator — Astra

For a business owner who wants an AI team to finish a job with several parts.
planner/reviewer plans the work. Astra builds the pieces. A fresh planner/reviewer reviewer checks the result against the plan.
This is the usual version to choose.

## Add it once
1. Download this skill package.
2. Open the Claude app or Codex app and attach the downloaded package.
3. Paste this sentence:

> Install this ap-orchestrator-astra skill for me. Check which required models and connections I already have. Handle the setup, preserve any existing version, and explain any missing access in plain words. Do not start a project yet.

If you already use Hermes, you can give its chat the same package and sentence.
You do not need Hermes or a second computer to begin.
A subscription does not guarantee every named model is available. Your agent checks access and explains any missing model.

## Check it is ready
Say:

> Show me that ap-orchestrator-astra is installed and readable. Explain who plans, who builds, and who checks. Do not launch any work.

## Give it a job
Say:

> Use ap-orchestrator-astra to plan and complete this job: [describe the result I want]. Show the finished result and the evidence that it works.

Your agent saves progress between groups of work. If an account reaches its usage limit, it gives you one resume sentence.
Use that sentence when access returns. Your saved work stays available.
Installing the skill does not start recurring jobs, publish anything, or buy credits.
