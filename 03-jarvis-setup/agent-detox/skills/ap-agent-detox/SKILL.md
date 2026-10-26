---
name: ap-agent-detox
description: "Audit and shorten agent instructions with backups."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Agent Detox

Over time, as the member gives feedback, the agent keeps adding lines to its instruction files.
Over months they fill with "do not do this, do not do that".
Smarter models need less hand-holding. A long rulebook limits their judgment and makes them slower.
This skill finds those files, interviews the member, backs everything up, and cuts the files down to the few lines that matter.

Adapted from the supplied workshop method. Repackaged as Agentic Playbook — by Kezy.

## Who this is for

A non-technical business owner who uses the Claude app, the Codex app, or talks to Hermes in chat.
They never hunt for files or edit them. You do all file work and explain it in plain words.
They answer short questions and reply YES or CHANGE.

## Explain it in one breath

Before starting, tell the member:
"Picture a new hire handed a 40-page rulebook. They freeze and check every page before acting. Now picture a sharp hire with a three-line brief. They move fast and use their head. We are turning your agent back into the second hire."

## Step 1. Find the instruction files

Search yourself. Never ask the member for paths.
Look for these, including any file they pull in (lines starting with `@`, or "read this file first"):

- Hermes: `SOUL.md` and `HERMES.md` in the Hermes home folder (`~/.hermes/`), in every profile folder under it, and in each profile's workspace.
- Claude: `CLAUDE.md` in `~/.claude/` and in the member's main project folders.
- Codex and other agents: `AGENTS.md` in `~/.codex/` and in the main project folders.
- The member's second brain folder (their notes folder): its own `AGENTS.md` or `CLAUDE.md`.

If you run on a different machine from Hermes, check what you can reach and name what you could not.
If the Hermes files are out of reach, say: "Your Hermes files live on your always-on machine. Send this same zip to your Hermes agent in chat and say detox my agent. I will clean the files on this computer now." Then continue with the files you can reach.
Fill the "Before" table in [the detox report](assets/detox-report-template.md):
file, size in characters, rough count of rules (each instruction line or bullet), and count of lines with "do not", "don't", "never" or "avoid".
Show the table and the total characters. Say which files you will work on. Change nothing yet.

## Step 2. Interview, one question at a time

Ask at most six questions. For each one, offer your recommended answer drawn from the existing files, so the member can reply "yes".

1. Who is this agent to you? (Example: "You are my chief of staff.")
2. What is the one goal it helps you reach?
3. Two or three traits for how it works with you. (Examples: "You come to me with solutions, not problems." "You use first-principles thinking.")
4. Your non-negotiables: money, privacy, and anything that cannot be undone.
5. What does it keep getting wrong right now?
6. Is there any line you want kept word for word?

Reflect the answers back in one short block. Save only what they confirm.

## Step 3. Back up every file

Before touching any file, copy it into a folder named `detox-backups` beside it.
Name the copy `<file>.pre-detox.<date>-<time>.bak`, for example `detox-backups/SOUL.md.pre-detox.2026-09-29-1430.bak`.
Take this pre-detox copy once per detox, before the first change. Later edits in the same detox never replace it.
Never overwrite an existing backup. If a name is taken, add `-2`, `-3` and so on.
The `.bak` ending stops agents from loading the backup as live instructions.
Nothing is ever deleted. Record every backup location in the report.

## Step 4. Sort every line

Put every existing line into one of three piles. Fill the "Sort" section of the report.

- KEEP: role and identity, the main goal, personality, and true non-negotiables (money, privacy, anything that cannot be undone).
- MOVE: step-by-step procedures and rules for one kind of task. Offer to turn each into a skill or a separate reference note the agent opens only when that job comes up. Skills load only when needed; always-loaded files load on every message.
- CUT: "do not" rules and examples a current model no longer needs, duplicates, stale notes, and feedback that already became a skill.

When a line is borderline, and it protects money, privacy, or something permanent, KEEP it.
Everything else borderline goes to MOVE, never straight to CUT.

## Step 5. Rewrite

Identity file (`SOUL.md`, or the identity part of a `CLAUDE.md` or `AGENTS.md`):
cut it down to about three important lines. Role, goal, how the member works. Give the character count.
Aim for concise identity files without imposing a character limit or removing safety rules.

Operating files (`HERMES.md`, `CLAUDE.md`, `AGENTS.md`): keep the minimum.
The KEEP lines, the non-negotiables, and one line pointing to where moved material now lives.

Rewrite each surviving prohibition as short positive guidance where you can.
"Never send money without asking" becomes "Ask me before any payment."
Keep the non-negotiables explicit. Plain words beat clever phrasing.

## Step 6. Show before and after, then ask once

Fill the "After" table: characters and rule count, per file and in total.
Show the full new text of every file. List what moved and where it will live.
Then ask exactly one question:

"Apply this? Reply YES or CHANGE <what>."

On CHANGE, revise and show again. Apply nothing until the member says YES.

## Step 7. Apply and test

Write the new files. Create any skills or reference notes from the MOVE pile the member approved.
If you are Hermes editing your own files, write the new files now. They take effect in the next session, so the test below uses a new chat.

Then test in a fresh session. Ask the member to open a new chat and say:
"Who are you, and what do you always check with me first?"
Then give one normal everyday request, for example "Plan my top three priorities for tomorrow."
Confirm the agent still knows its role and states the non-negotiables. If it misses one, add that line back and test again.

Tell the member:
- where the backups are, in plain words;
- the one sentence that undoes everything: "Restore my agent files from the detox backup."

## Step 8. Suggest the next detox

Say: "Run this again once a month, or whenever your agent feels slow again. Just say: detox my agent."

## Restore

When the member says "Restore my agent files from the detox backup":
find the newest `.pre-detox.` copy of each file in `detox-backups`.
First save the current file as `<file>.pre-restore.<date>-<time>.bak` in the same folder, so the detox version is kept. Never overwrite an existing backup.
Then put the pre-detox copy back under its original name.
Read the restored file list back to the member.

## Hard rules

- Back up before every change. Delete nothing.
- The KEEP list always survives: role, goal, personality, and the lines that protect money, privacy, and anything that cannot be undone.
- Apply nothing until the member replies YES.
- Never claim a measured speed-up number. Say the detox removes the bloat that slows the agent down.
- Do all file work yourself. Tell the member where things live in plain words.

## Files

| File | Use it when |
|---|---|
| [Detox report](assets/detox-report-template.md) | From Step 1 onward. Fill it as you go and save it beside the backups. |
