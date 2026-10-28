---
name: ap-import-ai-exports
description: "Convert approved AI exports into indexed conversation notes."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Import AI Exports

Turns a raw export folder (a folder of files the owner downloaded from ChatGPT or Claude) into plain, readable notes they can actually use. Every conversation becomes one note. Nothing in the original export folder is changed or deleted.

## Step 1: Find the export

Ask the owner where the export folders are, if not already told. They are usually sitting in the read-only "Source Mirror" folder outside the vault (the safe holding area for raw exports, listed in `_System/VAULT_MANIFEST.md`). Never edit, move, or delete anything in that folder. Only read from it.

## Step 2: Read the export file

Both ChatGPT and Claude exports include a file called `conversations.json`, a plain text file listing every conversation.

- **ChatGPT export:** each conversation has a title, a create_time (the date it happened, stored as a number), and a "mapping", which is the back-and-forth thread of messages in a tree shape. Walk it in order and keep only the messages actually written by the user or the assistant that contain real text. Skip empty or system messages.
- **Claude export:** each conversation has a name, a created_at date, and a list called chat_messages, where each message has a sender (human or assistant) and text. Simpler to walk since it is already in order.

## Step 3: Write one note per conversation

Use the template at `_System/templates/conversation-note.md`. Each note gets:
- A top label block (called frontmatter): `type: conversation`, `status: inbox`, `source: chatgpt` or `source: claude`, `created:` the original conversation date (not today's date).
- A one-paragraph gist you write yourself, summarizing what the conversation was about.
- Key points, as a short bullet list.
- The cleaned-up transcript below that.

Filename: `YYYY-MM-DD Short Title.md` using the conversation's own date.

Save ChatGPT notes to `01. Inbox/imports/converted/chatgpt/` and Claude notes to `01. Inbox/imports/converted/claude/`. Create those two folders the first time, they are not part of the starter structure.

## Step 4: Work in batches, track progress

Process about 25 conversations at a time. After each batch, add one line to `02. Projects/Second Brain Setup/LOG.md` saying how many are done. If the import stops partway through (closed early, ran out of time), the next run checks which note files already exist and picks up where it left off, instead of starting over.

## Step 5: Build the master list

Create or update `01. Inbox/imports/INDEX.md`, one line per conversation: date, title, a ten-word gist, and a suggested destination (which folder it probably belongs in), or the word "archive" if it looks like throwaway content (a one-off tech support question, testing the AI, etc).

## Step 6: Catch AI-written claims about the owner

Some Claude exports include an AI-written summary of "what it remembers" about the owner: their habits, preferences, or facts about their life or business. This is a guess by the AI, not a verified fact. If you find one of these summaries, write it into a single note, `01. Inbox/ai-memory-claims.md`, status: inbox, formatted as a checklist the owner can check off ("confirmed" or "not true") one claim at a time. Never treat anything on that list as true until the owner confirms it themselves.

## Step 7: Attachments

Leave attachments (images, files) where they are in the Source Mirror folder. A note can mention or link to an attachment by its file name, but the file itself stays put.

## Edge cases to watch for

- **Two conversations with the same title.** Add the time of day, or a short distinguishing word, to the filename so one does not overwrite the other.
- **Missing or broken date.** If a conversation has no usable date, use the date you are running the import on, and add a line inside the note flagging that the original date was missing.
- **Very long conversation.** Still write it as one note. Do not split a single conversation across multiple files. Keep the gist short even if the transcript underneath is long.
- **Empty or near-empty conversation** (a stray test message, an accidental click). Skip writing a full note for it, but still list it in the master list, marked "archive".
- **Non-English text or code snippets inside a conversation.** Keep them as-is in the transcript. Do not translate or reformat them.

## Example of one finished note

A short example, so you know what "done" looks like:

```
---
type: conversation
status: inbox
source: chatgpt
created: 2026-03-14
---

## Gist
The owner worked through pricing options for a new service package, landing on
a three-tier structure they wanted to test with clients.

## Key points
- Considered flat fee vs. percentage-based pricing
- Decided to start with three tiers, mid-tier as the recommended default
- Wants to revisit after the first five client conversations

## Transcript
...cleaned back-and-forth goes here...
```

## End report

Tell the owner in plain terms:
- How many conversations came in from each source.
- How many look like junk (candidates for "archive").
- The 10 conversations that look most valuable, and one line each on why (a real business idea, a decision they made, a plan they wrote out, etc).

## Included support

The vault runtime paths above are created by [ap-second-brain-setup](../ap-second-brain-setup/README.md). Its `templates/vault/` contains the blank manifest, rules and templates. Use the installed vault paths only after setup; keep raw exports outside the vault.

<!-- Agentic Playbook — by Kezy -->
