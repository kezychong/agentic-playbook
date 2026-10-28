---
name: ap-brain-installer
description: "Build the eight doors (Inbox to Sources), the AGENTS.md rulebook and the about-me note inside the brain folder. Use for \"build my brain\", \"finish building the eight doors\" or \"check my brain folder\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. It is the recipe Hermes follows to build the inside of your brain. Drag it into your brain folder, then tell Hermes: Read ap-brain-installer.md in my brain folder and build my brain.

# Brain Installer: build the eight doors

**If you are Claude Code on the laptop, stop here.** This pack is for Hermes. Tell the member: drag this onto your brain folder, then in the Hermes app click New session and say: Read ap-brain-installer.md in my brain folder and build my brain.

**For Hermes.** The member dragged this file into their brain folder and asked you to build their brain. Read all of it, ask the three questions, then show the build in one short list and build on the member's yes.

## The member's sentences

| The member says | You do |
|---|---|
| Read ap-brain-installer.md in my brain folder and build my brain. (Or any words like: build my brain, set up my second brain with this pack.) | Everything below |
| Finish building the eight doors from the brain installer. | Check what is missing against "Done looks like", build only that |
| Check my brain folder is built right. | "Done looks like" only, then report |
| List the doors in my brain folder. | List the eight doors, 01 to 08, each with its one-line meaning |
| What runs on its own? | Read the jobs section of AGENTS.md. Today it is empty: say "Nothing yet. Your first job arrives when you set up Capture Bot." |

## Rules for this pack

- You are Hermes, on the member's box. Their brain folder on the box: find its full path once with `hermes config get terminal.cwd` (set by Brain Folder Setup; if that is empty, `echo "$HOME/second-brain"`). It is `second-brain` in the box account's home folder: `/home/hermes/second-brain` on a rented server, the member's own Mac account on a Mac mini. On the laptop it has the member's own name; never make a second folder. Work from it. Syncthing mirrors everything you write to their laptop.
- Keep this pack: move this file into `_System/packs/` (make the folder if needed, replace an older copy). Add a section `## Packs you have` directly above `## Jobs that run on their own`, with one line: `- Brain installer: when I say "Finish building the eight doors from the brain installer." or "Check my brain folder is built right.", read _System/packs/ap-brain-installer.md and follow it.` If the member names this file and it is already in `_System/packs/`, use that copy. Why: a new chat without the pack makes up its own version.
- A file the member just dragged in may still be arriving through the mirror: if it is missing, or a `.syncthing.*.tmp` file sits beside it, wait a moment and look again.
- Ask the member before spending money, deleting things, installing, scheduling or changing a live profile. Prepare everything else as a short plan, apply it on approval, then report.
- Report in plain words: no file paths unless asked, no version numbers. If stuck, say which step and what you saw, then: "Record the failing step without secrets and consult your host support documentation."

## Goal

The inside of the brain, built on the box, and visible in the member's Finder within a minute.

1. Ask three questions, one at a time, and wait for each answer: "What should your agents call you? First name is fine." / "In one sentence, what does your business do, and for whom?" / "What is the one thing you most want your business to get done in the next three months?" A member who would rather not say gets "not yet set" on that line.
2. Then, once the member approves the short build list:
   - Eight doors, each a plain folder with a `README.md` of a title and one plain line saying what it holds: `01. Inbox` (anything dropped fast, sorted later), `02. Projects` (anything with a finish line), `03. Areas` (the parts of life and work that never end), `04. Resources` (reference from outside, not their own company truth), `05. Archives` (done and parked, never deleted), `06. Signals` (one note per Signal: what keeps coming up across your notes, counted), `07. World Model` (the lasting truth about them and their work), `08. Sources` (permanent streams of raw material).
   - `01. Inbox/agent-drops/`, for anything an agent captures on its own.
   - Inside `07. World Model`: `company/`, `people/`, `decisions/`, `digital-twin/` (empty until the Twin writes there).
   - `_System/` with a short `README.md`: the machinery that brings agents the right material. Nobody writes there by hand.
   - `07. World Model/company/about-me-and-my-business.md`: a title, the three answers as three plain lines, and a last line `source: the member's answers to the brain installer, <date>`.
   - A root `CLAUDE.md` holding only the line `@AGENTS.md` (Claude Code on the laptop reads it; never mention it to the member).
   - The rulebook `AGENTS.md`, in exactly these five sections, in this order:
     1. `## What this folder is`: a second brain, one folder of plain text notes; every agent (Hermes, Claude Code, any other) reads this file first, every session, before it writes anything.
     2. `## Read this first`: one line only: read this file at the start of every session.
     3. `## The eight doors`: one line per door as above, with `agent-drops` and the four World Model folders named
     4. `## The loop`: new material comes in through doors 01 and 08, the Link bot breaks each source into small one-idea notes and links them, the Organise bot files them into the right door, and the Signal bot counts what keeps coming up and writes one note per Signal into 06; 07 only takes what I settle with my yes. Agents write those notes straight in, each with a `source:` line; nothing waits for approval. Signal is mine: an agent flags what keeps coming up, and I judge what it means. The loop's short name is CLOSE: Capture, Link, Organise, Signal, Execute. When I say capture, save or note this (in the app or on Telegram), write it as a new note in `01. Inbox` with a `source:` line (where and when I sent it), then tell me the note's name. Never keep it only in your own memory.
     5. `## Jobs that run on their own`: holding only this rule line, as the very last line of the file: `Every job that runs on its own is listed here, one line each: what it does, when it runs and which bot runs it.`
3. Keep this pack (Rules above). That adds `## Packs you have` just above the jobs section.
4. Report, then tell the member: "Click New session before you ask me about your doors: I keep my old copy of AGENTS.md until a new session starts."

## Done looks like

- The eight door folders, 01 to 08, exist, each with its README.
- `agent-drops` and the four World Model folders exist; the about-you note ends with its `source:` line.
- `grep -c '^## ' AGENTS.md` prints 6 (the five sections plus Packs you have), Packs you have sits directly above Jobs that run on their own, and `tail -1 AGENTS.md` prints exactly the rule line.
- `cat CLAUDE.md` prints exactly `@AGENTS.md`.
- `## The loop` in AGENTS.md holds the capture rule (capture, save or note this goes to `01. Inbox` as a note).
- `_System/packs/ap-brain-installer.md` exists and the dragged copy is gone from the folder root.

## Traps

- The jobs section is always the last section, and its rule line stays its last line until the first job adds a table under it (Capture Bot's nightly capture). Later packs depend on that shape.
- The approval line for the agents (what they ask before doing) is written later by the Chief of Staff Interview. Do not write it today.
- You keep your old copy of AGENTS.md until a new session starts, so in this same chat you may still describe the folder as it was. That is why the member clicks New session before asking about the doors.
- Hermes ships a built-in skill called second-brain-vault. This folder is the vault: never write a vault, notes or doors anywhere else.
- If AGENTS.md already exists and the member said the build sentence, this is a second run: ask before replacing it. On the finish sentence, keep what is there and build only what is missing.

## Report back

1. "Your brain now has eight doors: Inbox, Projects, Areas, Resources, Archives, Signals, World Model and Sources."
2. "It has a rulebook, AGENTS.md, that every agent reads. Its list of jobs that run on their own is empty for now. Your first job arrives when you set up Capture Bot."
3. "Everything is on your laptop too: watch the doors appear in your Finder."
