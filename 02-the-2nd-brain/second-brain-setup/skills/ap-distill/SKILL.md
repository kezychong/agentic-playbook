---
name: ap-distill
description: "Extract lasting ideas into small linked notes."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Distill

Takes one already-filed source (a note, a converted conversation, a document) and breaks it into small, standalone notes, one idea per note. This is how good ideas stop being buried inside long documents and become things the owner can actually find and use later.

## Step 1: Read the whole source

Read the entire note or document, start to finish, before pulling anything out. Do not skim.

## Step 2: Find the ideas worth keeping

Look for 3 to 12 ideas that would still matter a year from now. Good candidates:
- A rule or principle the owner or someone else stated.
- An offer, price, or term (these need an "as of" date stamped on them, since they change).
- A process or set of steps someone follows.
- A decision that was made, and why.

Skip small talk, one-off details, and anything that will not matter later.

## Step 3: Write one note per idea

Use the template at `_System/templates/atomic-note.md`. For each idea:
- The title of the note IS the idea, written as a full sentence someone could act on (not a vague label).
- The body is 3 to 6 sentences, in plain words, explaining the idea fully enough that it makes sense with zero memory of where it came from.
- Link back to the source note it came from.
- Link to the relevant business shelf (the topic folder inside `03. Areas/` it relates to).
- If a number in the idea can change over time (a price, a member count, a result), stamp it with an "as of [date]" note.
- Give the note a `truth:` line in its top block. Use `truth: owner` if the idea is something the owner themselves said or decided in the source. Use `truth: unverified` if it came from external content, or is the AI's own read on things. (`_System/TAG_TAXONOMY.md` explains the truth line.)

Where the note lives:
- If it is specific to one business area, save it next to the source, in the same folder.
- If it is general knowledge that could apply anywhere, save it in `04. Resources/` instead.

## Step 4: Mark the source as done

Tag the source note `#status/distilled`. At the top of the source note, add a short list titled "Distilled into:" linking to every new note you created from it.

Also give the source note two findability lines in its top block, if it does not have them yet: a `summary:` line with one plain sentence saying what is inside, and an `aliases:` line listing the names the owner actually uses for this thing in conversation, if any. These are what let the agent find the right note on the first try later.

## Step 5: Respect the privacy line

Never ap-distill anything that touches the privacy rule (ID numbers, account numbers, contracts with financial details, personal client information). If a source is partly sensitive, only ap-distill the safe parts, and add one line noting what you left out and why.

## Quality check before finishing

Read each new note back as if you had never seen the source. If it does not fully make sense on its own, add a sentence or two until it does.

## Worked example

Say the source is a converted conversation where the owner talked through how they handle a certain kind of client complaint. That single conversation might yield three separate atomic notes: one titled something like "Always acknowledge the complaint before offering a fix", one on the specific script they use to respond, and one on the follow-up timing they settled on. Each becomes its own short note, each links back to the original conversation, and each sits on the shelf for whichever part of the business that complaint process belongs to.

## Edge cases to watch for

- **A source with only one idea in it.** It is fine to create just one note. Do not stretch a single idea into several thin notes just to hit a number.
- **A source with more than 12 ideas.** Pick the strongest 12 and mention in your end report that more may be worth a second pass later.
- **An idea that already has a very similar note elsewhere in the vault.** Do not create a duplicate. Instead, link the source to the existing note and mention this in your report.
- **A price or number that might already be out of date by the time you read it.** Still write the note, but stamp the number with the date you found it, so the owner knows to double check it if they are reading it much later.

## End report

Tell the owner in plain terms:
- Which source you distilled.
- How many new notes you created.
- What you linked them to.

## Included support

The vault runtime paths above are created by [ap-second-brain-setup](../ap-second-brain-setup/README.md). Its `templates/vault/` contains the blank manifest, rules and templates. Use the installed vault paths only after setup; keep raw exports outside the vault.
