# Manual installation note — Agentic Playbook, by Kezy

This is documentation, not an instruction to install on load. Review the complete folder and
[manual host guide](../../../../08-setup-guides-tools-connections/manual-setup.md). Obtain approval
before changing a live host. Older app-specific steps below are conditional on current host
support; no installation or integration has been tested. Preserve existing versions.

---
stage: draft
---

# VSL → Book a Call

**Version:** 1.0.0 · Updated 2026-09-10

## What it does

Writes the 15 to 20 minute video that sits in front of your calendar. You answer an interview about your offer, your proof and the three things a buyer has to believe before they will book. Your agent turns that into a spoken script on a minute-by-minute map, with every claim tied to something you can show, and a close that invites the right people onto a call and tells the wrong people not to book.

Before you read a word of it, the script passes fifteen automatic checks (length by speaking time, no price on video unless you said so, no scarcity you cannot back, the call described honestly) and a second agent that has never seen your project grades it against the rules. You get the script, the grade, and what still needs your decision.

It does not record, upload or publish anything. It writes.

## What you need first

The Claude app or the Codex app. That is it. Your agent handles anything else it needs.

## Install

Download the zip, open your agent on the machine you work on, and say:

```
Install the skill in the selected complete skill folder so I can use it in every project.
```

## Use it

Open the folder for the offer you sell and say:

```
Use ap-vsl-book-a-call. Interview me first, one question at a time, then build the records and write the script. Do not write anything before I have answered.
```

Answer the questions. The ones that matter most: who this is not for, the one sentence that defines a win, what you call your method, and how many calls a week you can actually take.

## What comes back

- `versions/vsl-v1.md` - the spoken script with `[mm:ss]` markers.
- `foundation/` - offer, proof ledger, story beats, call spec. Reused on every future video.
- A gate report and a judge table telling you what passed and what to decide.

Read it aloud once with a timer before you record. If it runs long, cut the origin story before you cut the proof.
