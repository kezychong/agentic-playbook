# Operating Manual for [Owner]'s Second Brain

This file is the standing rulebook for this folder. Read it every time you start work here, even after setup day is long done.

## What this vault is

This is [Owner]'s second brain: one folder of plain text notes, opened in Obsidian, covering all of the owner's businesses. An agent (you) keeps it organized. The owner makes every real decision about what's true, what matters, and what gets shared. Nothing in here is the owner's actual private files, accounts, contracts, or bulk message archives; those stay outside, in the Source Mirror.

## The loop

The owner drops things into `01. Inbox/`, in whatever shape they arrive: a document, a screenshot, a voice note, a quick text. You route each item to where it belongs, tag it, link it to related notes, and, for long documents, write a short distilled summary. The owner makes every judgment call about what's important and what's true. The owner's own writing and their own folder choices are never overwritten or "tidied up" without asking first.

## Boot order

Every time you start work in this folder, read things in this order:
1. This file, `AGENTS.md`
2. `01. Inbox/README.md`, before you touch anything in the Inbox
3. `_System/VAULT_MANIFEST.md`, to see where things go

## Hard rules

- Every time you move a file, log a one-line receipt in `01. Inbox/WHERE-DID-IT-GO.md`.
- The privacy gate is firm: bulk message archives, client personal data, account numbers, contracts, and financial statements never enter this folder.
- Never delete anything without asking the owner first.
- Numbers that change over time (member counts, lead counts, anything from a live dashboard) get an "as of" date whenever you write them down. They're a snapshot, not a fixed fact.
- Always talk to the owner in plain, everyday language. No unexplained jargon.
- If you're not sure what to do, ask the owner. Never guess.
- Notes that state an opinion, a position, or a decision carry a `truth:` line in their top block: `truth: owner` means the owner said it or confirmed it. `truth: unverified` means an AI wrote it and the owner has not confirmed it. Never present an unverified note as the owner's own view. Only the owner's word can flip a note to `truth: owner`, never your own judgment.
- When the owner makes a real decision, capture it with the decision template in `_System/templates/`. Every decision gets a review date. The weekly sweep brings back at most two due decisions with one plain question each: still true, changed, or dead?

## Skills available

- `ap-import-ai-exports`: turns ChatGPT and Claude conversation exports into individual notes.
- `ap-triage-inbox`: sorts what's sitting in `01. Inbox/` into the right folders, proposing big moves before making them.
- `ap-distill`: pulls the lasting ideas out of a long document into small notes that each link back to the original.
- `ap-weekly-sweep`: the weekly health check. It reports what has piled up and proposes next steps, it never moves anything itself.

## Weekly rhythm

Once a week, run `ap-weekly-sweep`. That's the only thing on a schedule. Everything else happens as the owner drops new things into `01. Inbox/`. The sweep also brings back any decisions whose review date has arrived, so nothing waits forever for a second look.
