---
pack: ap-attention-brief
brand: template
version: 1.0.0
updated: 2026-09-05
stage: shipped
---
# Settings for ap-attention-brief

Your agent fills these blanks by asking one question at a time.
Examples show the shape only.
They never grant access or become your settings.

## Who I am

- Name:
- Business in one line:
- Who I serve:

Example: A bakery owner serving local households.

## Where things live

Use locations inside your chosen working folder.
Your agent finds the folder with you.

- Working folder:
- Open-items file:
- Day-note pattern:
- Existing goals and main-task source:
- Run record:
- Run logs folder:
- Reply location:
- Brief output file, if chosen:

Example: `bakery/`, `open-items.md`, and `day-notes/YYYY-MM-DD.md`.
Example run record: `attention-state.json`.
Example logs folder: `attention-logs/`.
Example reply location: today's day note.
These example paths are relative to the working folder.

## Accounts and platforms

Names only, never passwords.
An empty permission means no access.

- Calendar account and allowed calendars:
- Email allowed, yes or no:
- Email account and allowed folders:
- Chats allowed, yes or no:
- Chat account and allowed conversations:
- My identity for mentions:
- Private delivery destination or output file:
- Preferred agent app:
- Computer that runs the routine:

Example: Read the bakery calendar; email and chats are off.
Example delivery: a private daily note the owner opens.

## Voice and style

- Preferred language:
- Style changes:

Use short sentences and at most 10 morning lines.
Lead with the decision or action that needs me.
Attach a source and checked time to each line.
No hype or repeated nudges.

## Rules I have set

- Setup answers complete, yes or no:
- Timezone:
- Morning time, suggested 08:00:
- Evening time, suggested 21:00:
- One reminder deadline or interval:
- Active days, daily unless changed:
- Today's main task and completion proof:
- Existing routine to reuse, if any:
- Changes I have requested:

Example only: Europe/London; 08:00 morning; 21:00 evening; one reminder at 21:30.
Example main task: Finalize the weekend menu.
Example proof: The owner-approved menu file.

Use one shared list for morning and evening.
Only I, or a verdict with checked proof, may close an item.
Keep overdue items visible until closed or explicitly parked.
Never contact other people.
Never read accounts I have not allowed.
Use `[SILENT]` only after successful checks find nothing requiring attention.
An unanswered evening close gets at most one reminder attempt.
Text nagging is a proven-failed channel.

## Numbers I allow it to cite

- Approved benchmarks and their dates:

Default: none.
Calendar times and task counts come from this run's checked sources.
Old numbers are dated snapshots, never current facts.
