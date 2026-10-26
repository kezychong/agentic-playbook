---
name: ap-start-project
description: "Create project continuity files after a preview."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Start Project

## Who this is for

This is for a business owner using the Claude app or Codex app. The agent handles setup and explains decisions in plain English.

## Outcome

Create a small project memory system so a fresh agent can understand the goal, current truth, prior decisions, recent work, roadmap, and next action without relying on chat history.

## Workflow

### 1. Inspect before changing anything

1. Locate the intended project home.
2. Decide whether this is a new project or an existing project.
3. For an existing project, inventory its files, folders, instructions, plans, logs, and decision records.
4. Ask only for facts that are essential and cannot be learned from the project. Never invent the goal, owner, success measure, deadline, or current status.

### 2. Show a preview

Before writing, show:

- the proposed project home;
- whether the project is new or existing;
- the files that will be created;
- any existing files that will be preserved;
- any proposed change to an existing file or folder;
- the few facts still needed.

Wait for approval of the preview. Never overwrite, rename, move, merge, or reorganize existing work without specific approval.

### 3. Build the right path

For a new project:

- Create `inputs/`, `decisions/`, `deliverables/`, and `archive/`.
- Create the six continuity files listed below.

For an existing project:

- Keep its present structure.
- Create only the approved missing continuity files.
- Add the four neutral folders only if the owner approved them in the preview.
- Preserve existing instructions and incorporate them without erasing their meaning.

### 4. Create six tailored continuity files

Use these assets as structural guides. Write real project facts, remove coaching text, and leave no generic setup markers.

1. [`AGENTS.md`](assets/AGENTS-template.md): the single source for project rules and working behavior.
2. [`CLAUDE.md`](assets/CLAUDE-template.md): a short compatibility pointer to `AGENTS.md`, not a second rulebook.
3. [`LOG.md`](assets/LOG-template.md): an append-only record of completed work.
4. [`DECISIONS.md`](assets/DECISIONS-template.md): meaningful choices, reasons, and reversal conditions.
5. [`ROADMAP.md`](assets/ROADMAP-template.md): outcomes, milestones, and what comes next.
6. [`STATE.md`](assets/STATE-template.md): the current truth, active focus, blockers, and next action.

Explain the memory loop in the finished files:

- Instructions tell the agent how to work.
- Decisions stop old arguments from repeating.
- The log records what was done.
- The roadmap shows where the project is going.
- State says what is true now.

### 5. Install the update rule

Put this rule in `AGENTS.md`: after work changes the project, append to `LOG.md`, refresh `STATE.md`, update `ROADMAP.md` when milestones move, and record meaningful choices in `DECISIONS.md`.

Seed each file from verified project facts. If no prior decision or blocker exists, say that plainly instead of inventing one.

### 6. Run the cold-start check

Read only the six continuity files and confirm a fresh agent can answer:

1. What is this project?
2. What is true now?
3. What was decided?
4. What happened recently?
5. What should happen next?

Repair any missing or conflicting answer before finishing.

### 7. Give one compact receipt

Return one short receipt with:

- files created or updated;
- files preserved;
- unresolved questions;
- the next action.

Do not add a second summary.

## Guardrails

- Preview before every write.
- Protect existing work by default.
- Do not reorganize an existing project without approval.
- Keep `AGENTS.md` as the one instruction source.
- Tailor every file to evidence from the real project.
- Keep the system small enough that a fresh agent will actually read it.

## Preserve the full continuity workflow
Before scaffolding, distinguish a milestone-based build from recurring delivery. Respect the member's existing capacity limit if they have one; never invent a limit. If the direction is unresolved, offer a short stress test before creating a project around it.
Add a boot route to AGENTS.md: read STATE.md, ROADMAP.md and the latest project handoff before continuing. A session ending mid-task saves a handoff to the member's chosen durable location. Keep root files for instructions and current state; put outputs in their approved body folders and avoid parallel trackers.
Register the new project in the member's existing index or project map when authorized, and verify the link works. If no index exists, offer one rather than inventing a private registry. Keep decision records distinct from personal beliefs. Do not invent first-person claims or names from ambiguous dictation.
