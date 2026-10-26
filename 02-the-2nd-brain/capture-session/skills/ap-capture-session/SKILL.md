---
name: ap-capture-session
description: "Turn a working conversation into approved durable notes."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Capture Session

## Who This Is For

The member using this skill is a smart business owner, not a technical person. They work inside the Claude app and never open a terminal.

The agent reading this skill does all the scanning and filing itself: reading the conversation, drafting the candidate list, and writing the approved notes into the vault. Narrate this in plain words. The member only ever approves, cuts, or edits a list, never touches a file path themselves.

Most of what you learn in a working session with Claude Code disappears the moment you close the
window. The decisions, the realisations, the "oh, THAT is how it works" moments. They were never
written down, so next month you solve the same problem again from scratch.

This skill is the fix. At the end of a session it reads the whole conversation, pulls out the few
things worth keeping, and files them into your vault as atomic notes. That is the **Capture** step of
the CODE loop (Capture, Organize, Distill, Express). Capture is where the loop starts. Everything
downstream (triage, weekly sweep, your wiki) is fed by what you capture here.

This is a teaching tool as much as a filing tool. As you work, name what you are doing so the person
learns the rhythm, not just the output.

## The one rule that makes this work

**Quality over quantity.** Three notes worth re-reading in six months beat fifteen notes nobody opens
again. Be ruthless. If a candidate would not change a future decision or teach a future you something,
cut it. A short capture list is a sign the skill is working, not failing.

## What to capture

Scan the conversation for these four kinds of thing.

### Concepts learned
- New terms that got explained (for example "RAG", "atomic note", "MOC", "idempotent").
- Mental models or frameworks that came up.
- A "how it actually works" explanation that closed a knowledge gap.
- File as: an atomic note, the concept written in the user's own context, not a textbook definition.

### Decisions made
- Architecture or tooling choices ("we are using folders, not a database", "no automations until the
  vault has real notes in it").
- Process decisions ("captures go to agent-drops, never the Inbox root").
- File as: a decision note that records the choice AND the reasoning, so the "why" survives.

### Insights and realisations
- The moment two ideas connected.
- A correction to something the user believed before.
- A strategic takeaway worth acting on.
- File as: an atomic note, or a line added to an existing note if one already covers the topic.

### Open questions raised
- Things asked but not fully answered.
- Topics flagged for "later".
- File as: a short note tagged `#status/inbox` so the next triage surfaces it.

## What to skip

- Back-and-forth debugging, retries, and error messages.
- Commands run and files moved (operational noise, not knowledge).
- Anything already written to a file during the session (a note created, a doc edited). It is already
  captured. Do not duplicate it.
- Pleasantries, restated instructions, and the model thinking out loud.

## Source attribution (expressed-from)

The user cannot see which vault files were Read during the session. You can. Before writing any
capture, scan your own Read tool-call history for this session and list every vault file you opened.
Those go into the capture's frontmatter as `expressed-from:`.

What counts:
- Only files inside this vault. Skip external web pages, skip the `.claude/` skill files, skip system
  configs.
- Only files opened with the Read tool. Skip search hits and folder listings.
- One entry per file, even if Read more than once.
- Use the vault-relative path, not the full machine path.

Why it matters: this turns every capture into a provenance record. The new note plus the sources that
informed it. Later, when you ask "where did this idea come from", the trail is already there. If the
list is long (more than ten files), keep only the ones that actually informed the note being written.

## Where captures go

Every capture is written into `01. Inbox/agent-drops/` as its own `.md` file.

Do not write into the Inbox root, and do not try to file captures straight into their final home.
Dropping them in `agent-drops/` is deliberate: it is the holding area automated processes write to,
and the Daily Inbox Triage (see `00. System/AUTOMATIONS.md`) routes each one to its real destination
later, tagging and wiki-linking it on the way. One job per step. You capture. Triage routes.

## Output format

One file per captured item, in `01. Inbox/agent-drops/`:

```markdown
---
tags: [status/inbox, type/atomic, source/conversation]
captured: YYYY-MM-DD
session-topic: "[one-line topic of this session]"
expressed-from:
  - 00. System/CLAUDE.md
  - 02. Projects/{SomeProject}/notes/[file-you-read].md
---

# [Title — the insight itself IS the title, written as a full thought]

[2 to 5 sentences explaining the concept, decision, or insight in the user's own context.]

Related: [[a relevant note, if an obvious one exists]]
```

Tag rules (from `00. System/TAG_TAXONOMY.md`):
- Always `#status/inbox` (triage promotes it later).
- Type: `#type/atomic` for a fact or insight, `#type/decision` for a decision, `#type/idea` for a
  half-formed thought, `#type/sop` for a repeatable process.
- Source: `#source/conversation` (this is a chat). Use `#source/user-belief` only if the user stated
  it as their own conviction.

`expressed-from:` may be omitted only if zero vault files were Read this session (rare, most sessions
touch at least `CLAUDE.md`).

**Naming:** `YYYY-MM-DD_session_[slug].md`
Example: `2026-06-17_session_no-automations-until-vault-has-real-notes.md`

## Prose-as-title

The title is the insight, not a label. Write the headline of the note as a complete thought.

- Weak: "Note about automations"
- Strong: "Automations stay dormant until the vault has real notes to act on"
- Weak: "Folder decision"
- Strong: "Captures go to agent-drops so the Inbox root stays the user's own space"

A good title means the note is useful from the file list alone, before it is even opened.

## Process

1. Scan the full conversation from the start to now.
2. Scan your Read tool-call log. List every vault file you opened (this becomes `expressed-from:`).
3. List the candidate captures in chat. For each, show the proposed title, type, and `expressed-from:`
   list. Do NOT write any file yet.
4. Wait. The user approves, removes, or edits the list. They decide what gets kept.
5. Write the approved captures into `01. Inbox/agent-drops/` with full frontmatter.
6. Report: "Filed X captures with Y unique sources attributed. Your next triage will route them."

## Rules

- ALWAYS show the candidate list before writing. The user approves what gets captured. Never silent.
- One concept per file. Keep each note atomic.
- If a capture belongs in a note that already exists, say so and offer to add a line to it instead of
  creating a new file.
- Do not capture what the vault already records. Check first.
- Plain language. Write the way one person talks to another. No corporate filler, no em-dashes, no
  "it is not X, it is Y" flourishes. The note has to read like the user wrote it.

## Worked example (calibration)

A 40-minute session where the user set up their vault and pushed back on adding automations early.

**A good capture list looks like this (3 items, not 12):**

1. `#type/decision` — "No automations until the vault has real notes to act on"
   (the user decided to ship the vault empty and add cron jobs only once there was content to route)
2. `#type/atomic` — "Atomic notes route by topic, not into one Resources dumping ground"
   (the realisation that a note about you goes to `03. Areas/Self/`, a project note to that project)
3. `#type/atomic` — "An agent writing to the Inbox uses agent-drops so the Inbox root stays yours"

**What got cut, and why:**
- The five `mkdir` commands that built the folders (operational, not knowledge).
- The two times Claude mis-read a path and corrected it (debugging noise).
- The welcome.md test note (already written to a file this session, so already captured).
- "Obsidian is a note app" (the user already knew it, it taught nobody anything).

Three keepers, eight cuts. That ratio is healthy.

## Graduate to automatic (the loop you grow into)

This skill captures the chat you are in right now, and only when you run it. The next level is
automatic: a nightly process that reads every finished Claude Code session across all your projects,
filters out the noise, and files the few durable lessons on its own, with no prompting.

That is the **Memory Compaction** automation specced in your `00. System/AUTOMATIONS.md` (it builds on
session-memory tooling like claude-mem). It is marked PLANNED there on purpose. You install it once the
manual habit is real and the vault has enough sessions to be worth mining. Until then, run this skill
by hand at the end of sessions that taught you something. The manual rep is what makes the automatic
version worth installing later.

## Runtime path conventions and optional integrations

Paths such as HOME, 00. System, 07. World Model, Signals, RECENT.md and AUTOMATIONS.md describe a future user-approved runtime workspace. They are not pre-existing files supplied by this package. Resolve them from the user's confirmed vault manifest and profile. For a new PARA vault use the included ap-second-brain-setup templates; if a referenced file or automation is absent, record it missing and ask only for the information needed. Do not fabricate configured services. Optional GBrain, here.now, Telegram and scheduler integrations must be separately configured and authorized; no connector is bundled here.
