# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../../08-setup-guides-tools-connections/manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

---
stage: draft
---

## What it does

Takes the working session you just finished and turns it into a reusable skill, so next time you don't have to re-explain the whole thing, you just run one command. It reconstructs what you did (including every correction you made along the way, which is the real spec) and writes a new skill file straight into your agent's skills folder.

## What you need first

The Claude app or the Codex app. That's it.

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in the selected complete skill folder so I can use it in every project.
```

You only need to do this once per machine. After that, it is there in every session.

## Check it worked

Tell your agent `/learn-skill` and it should start reviewing the current session and ask you what you'd say to trigger this again.

## How to use it

1. Finish a working session where you and your agent did something you know you'll do again.
2. Say "package this into a skill" or "we're done for today, save what we did."
3. It asks you what phrases you'd actually say to trigger it next time, and what "done" looks like.
4. It writes the new skill into your skills folder and tells you it will be ready next session (not this one, skills load fresh at the start).

Example: "We just built that weekly report the hard way three times now. Package it into a skill."

## What it will NOT do

- It will not turn a one-time task into a skill. If it's not going to happen again, it says so instead of creating clutter.
- It will not hard-code today's exact file names or numbers into the skill. It generalizes so the skill still works next time the details are different.
- It will not make the new skill available in the current session. It loads fresh starting next time you open your agent.

---

*Adapted for Agentic Playbook — by Kezy.*
