---
name: ap-weekly-sweep
description: "Review vault health and propose next actions."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Weekly Sweep

A once-a-week look over the whole vault (the owner's folder of notes) to spot what is piling up, what got missed, and what is worth turning into real notes next. This skill only looks and reports. It never moves, deletes, or edits anything on its own.

## Step 1: Check the Inbox for age

Count how many items in `01. Inbox/` are older than 7 days. If there are any, note that a triage run (the `ap-triage-inbox` skill) is worth doing soon.

## Step 2: Check for unrouted conversations

Open `01. Inbox/imports/INDEX.md` (the master list from imported ChatGPT and Claude conversations) and count how many conversations still have no destination folder chosen, meaning they were never actually filed anywhere.

## Step 3: Spot-check the paper trail

Look at recent file moves and compare them against `01. Inbox/WHERE-DID-IT-GO.md` (the log every move is supposed to get a row in). Flag any move you can see happened but that has no matching row in that file.

## Step 4: Find orphan notes

Find notes that have no links to or from any other note, and no status tag at all. List the worst 10 of these, the ones most likely to be forgotten because nothing points to them.

## Step 5: Suggest what to distill next

Look through notes that have been routed into a folder but never turned into small standalone notes yet (status is not `#status/distilled`). Pick the 3 meatiest ones, the ones with the most ideas worth pulling out, as next week's ap-distill candidates.

## Step 6: Bring back decisions due for a check-back

Look for notes with `type: decision` whose `review_date` has passed and whose `outcome:` is still `pending`. Take at most the 2 oldest.

For each one, prepare one plain question with the full story inline, so the owner needs zero memory to answer it. Shape it like this: "On [date] you decided [what] because [why]. Still true, changed, or dead?" These questions go into the chat headlines, alongside the other things the owner needs to know this week.

When the owner answers, write their answer into that decision note, with today's date, set `outcome:` to what they said, and set a new `review_date` if they want another look later.

This is the one exception to "this skill never edits anything": writing the owner's own answer into a decision note, after they give it, is allowed. The sweep still never moves or deletes a file, and never changes a decision note without the owner's answer sitting right there.

Never surface more than 2 check-backs in one sweep, even if more are due. If more are waiting, add one line to the report saying how many.

## Step 7: Write the report

Write one short report note to `_System/reports/YYYY-MM-DD-weekly-sweep.md` with a short label block at the top (frontmatter) and six short sections matching the steps above (Inbox age, unrouted conversations, paper-trail gaps, orphan notes, ap-distill candidates, decisions due for check-back). Keep each section a few lines, not a wall of text.

Also add one meter line to the report: count the notes by status (inbox, organized, distilled) and state the distilled share (what percent are distilled), next to last week's number from the previous report, so the owner can see whether that share is going up or down.

Then tell the owner, in chat, the 3 headlines they actually need to know this week, in plain language. Nothing technical, just what needs their attention.

## Reminder

This skill never moves a file, deletes a file, or changes a tag. It only looks, counts, and proposes. Any actual cleanup happens when the owner says yes and another skill (like `ap-triage-inbox` or `ap-distill`) runs.

## Worked example of a headline

A good headline for the owner sounds like: "You have 9 notes sitting in your Inbox for over a week, want me to sort them?" or "The three chats from your ChatGPT import that look most useful still have not been filed anywhere, want me to file them?" Short, specific, and something they can say yes or no to right away.

## Edge cases to watch for

- **Nothing needs attention this week.** Still write the report note, just with short sections saying so. Tell the owner in chat that everything looks clean, do not invent a problem to report.
- **The reports folder does not exist yet.** Create `_System/reports/` the first time this runs; after that it will already be there.
- **Two sweeps run in the same week by accident.** Check the reports folder for a report already dated this week before writing a new one; if one exists, update it rather than creating a second file for the same week.
- **A huge backlog** (Inbox has 50-plus old items, or the unrouted list is very long). Still just report the count and propose the next step. Do not attempt to fix a huge backlog yourself inside this skill.

## Why this matters

A second brain only stays useful if someone checks on it regularly. This sweep is that regular checkup: a fast, low-effort way for the owner to know whether their notes are staying organized or starting to pile up, without them having to dig through folders themselves.

## What the report note looks like

A short label block at the top (type, date, status), followed by the six sections in this order: Inbox age, unrouted conversations, paper-trail gaps, orphan notes, ap-distill candidates, and decisions due for check-back, plus the status meter line (inbox, organized, distilled counts and the distilled share versus last week). Each section is a few bullet points, not paragraphs. Anyone opening the file later, even the owner months from now, should be able to read it in under a minute and know exactly what state the vault was in that week.

## How this fits with the other three skills

Weekly sweep is the checkup, not the fix. It points at problems that the other skills solve: `ap-triage-inbox` handles the Inbox pileup and unrouted conversations it finds, `ap-distill` handles the candidates it proposes, and `ap-import-ai-exports` is what originally created the exports list this sweep checks for gaps in. The one thing weekly sweep does do itself is decisions: it asks the check-back questions in chat, and once the owner answers, it writes that answer straight into the decision note. Beyond that, running weekly sweep changes nothing else in the vault. It only tells the owner what to run next, and why.

## Included support

The vault runtime paths above are created by [ap-second-brain-setup](../ap-second-brain-setup/README.md). Its `templates/vault/` contains the blank manifest, rules and templates. Use the installed vault paths only after setup; keep raw exports outside the vault.

<!-- Agentic Playbook — by Kezy -->
