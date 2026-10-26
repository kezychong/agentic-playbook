---
type: reference
status: organized
source: system
created: 2026-07-24
---

# Tag Taxonomy: the starter set

This is a small, deliberate list. If a tag isn't here, it doesn't exist yet. Add it here first, with one line on when to use it, before you use it anywhere else.

## Status tags: where a note is in its life

- `#status/inbox`: dropped in, not yet routed anywhere.
- `#status/organized`: routed to its proper home in the vault.
- `#status/distilled`: the key ideas have been pulled out into their own atomic notes.

Where status lives: every note carries a `status:` line in its top block (inbox, organized, distilled), and the `#status/` tags are the same values written as searchable tags. When a skill says "update the status", update the `status:` line, and the tag too if the note carries one. The two must never disagree.

## The truth line: who stands behind a note

This one is a `truth:` line in the note's top block, not a tag. Two values only:

- `truth: owner`: the owner said it or signed off on it.
- `truth: unverified`: an AI wrote it and the owner has not confirmed it.

Rule: the agent never flips `unverified` to `owner` on its own. Only the owner's word does that.

Pure reference notes (an article summary, a converted document) don't need a truth line. Notes that speak for the owner, their opinions, positions, decisions, beliefs, always do.

## Type tags: what kind of note it is

- `#type/note`: a general note or a single atomic idea.
- `#type/conversation`: an AI conversation kept for reference.
- `#type/playbook`: a repeatable, step-by-step way of doing something.
- `#type/sop`: a fixed procedure that should be followed the same way every time.
- `#type/decision`: a record of a choice that was made, and why.
- `#type/meeting`: notes from a meeting or a call.
- `#type/idea`: a rough idea, not yet developed.

## Business tags: which business a note belongs to

These get created during setup day, one per business, from the Phase 1 interview. Use a short lowercase word from the business name, and keep the `#biz/` prefix:

- `#biz/[short-name]`: [business name]. (One line like this per business.)
- `#biz/personal`: anything about the owner personally, not tied to one business.

If a business folder is later renamed, rename its tag here in the same change. Keep the `#biz/` prefix the same either way.

## Adding a new tag

If you're about to invent a tag on the spot, stop. Add it to this file first, in the matching section, with one line saying when to use it. Then use it. Tags invented in passing get lost and stop meaning anything.
