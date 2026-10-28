---
name: ap-relationship-wiki
description: "Keep a private relationship wiki: one sourced note per person, links to life areas, open promises both ways, and a short brief before a meeting, call or message. People are proposed, never added without approval. Use for \"add [person] to my relationship wiki\", \"brief me on [person]\" or \"who do I owe a follow-up\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Original starter method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Relationship Wiki

Private by default. These notes hold personal information about real people: keep them out of any shared or public folder, and never paste them into a public page.

## Where they live

- Five-folder vault (Second Brain Setup): `03. Areas/People/`.
- Eight-door brain: `07. World Model/people/`.
- One file per person: `<First Last>.md`. One person, one file; merge duplicates on approval.

## The note

```markdown
---
type: person
status: active        # active | dormant | archived
relationship: client  # client | partner | team | supplier | friend | family | other
areas: [Business]     # life areas this person touches
last_contact: YYYY-MM-DD
---
# <Name>

**Who:** one line — role, organisation, how you know them.
**How we met:** date and context. source: <note or meeting>

## What I know
- <fact> — source: <note, meeting or message, with date>

## Open loops
- I owe: <promise> — due <date> — source: <where it was said>
- They owe: <promise> — due <date> — source: <where>

## How to work with them
- <preference, e.g. prefers voice notes over email> — source: <where>

## Log
- YYYY-MM-DD — <one line of what happened> — source: <where>
```

Every line of fact carries a `source:`. A line with no source is a guess: do not write it.

## The owner's sentences

| The owner says | You do |
|---|---|
| Add [person] to my relationship wiki. | Draft the note from what the brain already holds; show it; write on yes. |
| Brief me on [person]. | Part B |
| Who do I owe a follow-up? | List every `I owe` open loop, oldest first, with its source. |
| Update my relationship wiki from this meeting / chat. | Part C |
| Run my people check. | Part D |

## Part A: proposing, not adding

1. When a new name appears (a meeting, an email, a capture), do **not** create a note. Add it to a short **proposed people** list with the source line and why it may matter.
2. Show the list when the owner asks, or once in the weekly check. They answer yes, no, merge with [existing person], or later.
3. Never guess who someone is from context alone. A name in a transcript with no clear identity stays proposed.

## Part B: the brief

Before a meeting, call or message, give a brief that fits on a phone screen:

1. Who they are, in one line.
2. Last contact and what it was about.
3. Open loops both ways.
4. Two or three things worth remembering (preferences, sensitivities, recent news they shared), each with its source.
5. A suggested opening line and one thing to ask.

Say plainly what the notes do not hold. Never fill gaps with guesses.

## Part C: after a meeting

From the meeting notes, propose updates per person: new facts, new open loops, a log line, `last_contact`. Show them grouped by person; write only what the owner approves. Promises go in Open loops with their source line.

## Part D: the weekly people check

1. Open loops past due, both ways.
2. Active people with no contact in 60 days (or the owner's chosen number): suggest a check-in or mark dormant.
3. Proposed people waiting for a decision.
4. Duplicates to merge.

Report the four lists; change nothing until the owner answers.

## Rules

- Personal data stays in the owner's private vault. No sending, sharing or publishing from these notes without explicit approval of that exact message.
- Linking a person to a life area (for example a trainer to Health) is a suggestion the owner confirms.
- On request, delete or archive a person's note completely; deletion is a separate approval.
