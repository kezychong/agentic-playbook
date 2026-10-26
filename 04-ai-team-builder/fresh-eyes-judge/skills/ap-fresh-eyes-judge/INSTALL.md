# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../../08-setup-guides-tools-connections/manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

---
stage: draft
---
# Fresh Eyes Judge: Install and Use

Included locally: use this complete skill folder; no external download is required.

This skill checks one finished piece of work against its original brief.
It gives PASS, NEEDS REPAIR, or FAIL, with proof for every requirement.
It saves a verdict file and a repair list your builder can use.

Works in Claude Code and in Codex.

## What you need first
- Your agent's app.
- The downloaded the included complete skill folder.
- The original brief and the work you want checked.

## Install
Say this to your agent:
> Install the skill in my downloaded the included complete skill folder so I can use it in every project.

Your agent opens the download and handles setup.
It installs any needed requirements and tells you what it installed.
You do not need to run setup steps yourself.

## Check it worked
Say:
> Use Fresh Eyes Judge on the practice example included with the skill.

On first use, it asks where to save verdicts.
Then it asks whether you want a short result in chat.
It saves those answers for later runs.
The practice result should be NEEDS REPAIR because the requested button label is missing.

## How to use it
1. Open a fresh conversation with your agent.
2. Give it the original brief and the finished work.
3. Say: "Give this fresh eyes and check every requirement against the brief."
4. Answer any question about what counts as done.
5. Read the verdict and follow its link to the saved file.
6. Give the repair list to your builder if changes are needed.

A brief is your recipe; the finished work is the cake being checked.
For example, a bakery's page draft can be checked against a one-paragraph brief.
A same-agent review carries a caveat because the builder already knows its own work.
Use a different model than the one that built it, if you can.

## What it will NOT do
- Change the work or rewrite your brief.
- Treat "done" from the builder as proof.
- Judge style unless your brief asks for it.
- Call a missing check a pass.
- Hide uncertainty; it lists what it could not verify when evidence is missing.
