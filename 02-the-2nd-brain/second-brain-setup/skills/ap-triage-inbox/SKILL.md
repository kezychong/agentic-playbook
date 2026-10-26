---
name: ap-triage-inbox
description: "Classify and route inbox notes with a move ledger."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Triage Inbox

Looks at everything sitting in `01. Inbox/` and moves each item to where it actually belongs, following clear rules so nothing sensitive or unfinished gets misfiled.

## Step 1: Read the ground rules first

Before touching anything, read `01. Inbox/README.md`. Do this every single time, even if you have done it before. It may have been updated with new rules since your last run.

## Step 2: Classify every item, in this order

For each item in the Inbox, decide which bucket it falls into, checking in this order:

1. **SENSITIVE.** Anything with ID numbers, bank or investment account statements, contracts, or personal details about clients. Do not open it further than needed to tell what it is. Do not file it anywhere in the vault. Flag it to the owner and recommend they store it outside the vault instead, in a private, non-shared location.
2. **THE OWNER'S ACTIVE WORK.** Plans, drafts, or anything they are clearly still working on. This goes into the matching folder inside `02. Projects/`, matched to the project it belongs to. Never file active work as if it were just reference material.
3. **KNOWLEDGE.** Everything else. Route it using the table in `_System/VAULT_MANIFEST.md`, which lists which folder each type of content belongs in.

## Step 3: Decide how to handle the batch

- **More than about 20 items:** classify everything first without moving anything, then show the owner a short list: item, where it would go, and why, in one line each. Wait for their go-ahead before moving a single file.
- **20 or fewer, and all obvious:** go ahead and move them, then show the owner the list of what moved and where, after the fact.

## Step 4: Leave a paper trail

Every time you move a file, add one row to `01. Inbox/WHERE-DID-IT-GO.md`: the date, the file name, what kind of item it was, where it went, and a one-line reason why. Also change the note's status tag to `#status/organized`.

## Step 5: Never guess

If you cannot tell where something belongs, leave it in the Inbox, tag it `#status/inbox`, and write one short, specific question for the owner about it. Collect all your questions together and ask them in one batch at the end, not one at a time as you go.

## Worked example

Say the Inbox has 14 items. Three are drafts for a project the owner is mid-way through, so those go to that project's folder in `02. Projects/`. Four are general notes about running one part of their business, so those go to the matching shelf in `03. Areas/`. One is a scanned bank statement, so that gets flagged as SENSITIVE and left out of the vault entirely. Two are old notes nobody has touched in months that clearly belong in `05. Archives/`. The rest are unclear, so they stay in the Inbox with one question each, batched together at the end.

## Edge cases to watch for

- **A file that is both work-in-progress and sensitive** (for example, a draft proposal that includes a client's account number). Treat it as SENSITIVE first. Flag it, and suggest the owner split it: the safe parts can be filed once the sensitive details are removed.
- **A note with no clear topic at all** (a stray voice memo transcript, a half sentence). Leave it in the Inbox, tag it, and ask the owner directly whether it is worth keeping.
- **Duplicate content**, where the same idea already exists as a note somewhere else in the vault. Point this out to the owner rather than silently filing a duplicate.
- **An item that spans two projects.** Pick the project it is most tied to and mention the overlap to the owner rather than splitting one file into two.
- **An attachment with no note around it** (a photo, a screenshot, a downloaded file with no context). Still classify it using the same three buckets above. If its purpose is unclear, treat it as ambiguous and ask the owner rather than guessing at what it is for.

## Why the order matters

Checking SENSITIVE first, before anything else, means a private detail never accidentally gets treated as ordinary reference material and filed somewhere visible. Checking THE OWNER'S ACTIVE WORK second means an in-progress plan never gets buried in a reference folder where they would not think to look for it while they are still working on it. KNOWLEDGE only ever gets checked last, once the first two are ruled out.

## End report

Tell the owner in plain terms:
- How many items moved, and to where in general.
- How many were left behind (sensitive flags, or things needing their answer first).
- Any questions you have for them, grouped together.

## A quick sanity check before you finish

Before closing out, make sure every moved file has a matching row in `01. Inbox/WHERE-DID-IT-GO.md` and that nothing tagged SENSITIVE ended up saved anywhere inside the vault. If either check fails, fix it before reporting back to the owner.

## Included support

The vault runtime paths above are created by [ap-second-brain-setup](../ap-second-brain-setup/README.md). Its `templates/vault/` contains the blank manifest, rules and templates. Use the installed vault paths only after setup; keep raw exports outside the vault.
