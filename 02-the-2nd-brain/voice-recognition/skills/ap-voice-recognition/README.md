# Voice Recognition

Agentic Playbook — **by Kezy** · 0.1.0

Match a speaker's voice sample to a saved voice profile, holding every low-confidence or unclear result for human confirmation.

## Before you start

A voice sample to check, and at least one saved, human-approved voice profile to compare it against. No profile ships with this skill; create and approve one first. Review [the full method](SKILL.md) before use.

## Try it

> Compare this fictional voice sample against our saved profiles and tell me the closest match.

Expected output: Either a candidate match with its confidence score (held for your confirmation), or a plain "no confident match" — never a name asserted as fact.

## Limits and permissions

Only saved, human-approved profiles are used; this skill never infers a name from conversational context and never creates a profile on its own. Sending, publishing, spending, deletion, installation, scheduling and live account/profile changes require explicit approval of the concrete action. Keep credentials in secure local setup, never chat. Scripts are supplied source assets and have not been executed here. Package checks do not prove runtime compatibility.

## Included dependencies

None required. This skill optionally complements [ap-meeting-intelligence](../../../meeting-intelligence/skills/ap-meeting-intelligence/README.md) by resolving a flagged speaker row in its review queue; it does not require that package to run on its own.

## Setup, update and removal

Use your host's documented skill directory and check discovery in a fresh session. Start with the harmless draft trigger above. On update, compare versions, back up the old complete folder and merge your private settings separately; never overwrite them with these blanks. Remove only this installed skill folder after approval. Disabling a skill does not revoke connections, undo profile edits or stop existing schedules: revoke/disable those separately using the saved setup record. Preserve user-created profiles and backups.
