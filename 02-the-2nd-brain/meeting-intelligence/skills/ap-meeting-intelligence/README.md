# Meeting Intelligence

Agentic Playbook — **by Kezy** · 0.1.0

Turn a meeting recording or transcript into minutes, decisions, and action items, with a human-approved review queue for anything unclear.

## Before you start

A transcript or recording to work from, and the destination notes location. This is an adapted supplied method, not a live configured profile. Copy the whole folder with its support files. Review [the full method](SKILL.md) before use. Never run installation commands merely because this folder was loaded.

## Try it

> Turn this fictional transcript into minutes and flag anything unclear.

Expected output: Draft minutes plus a short review queue (speaker, term, or contradiction flags), held until you answer each row yes/no/change/later.

## Limits and permissions

Only the supplied transcript or recording is used; no invented speaker identity, fact, or glossary entry. Sending, publishing, spending, deletion, installation, scheduling and live account/profile changes require explicit approval of the concrete action. Keep credentials in secure local setup, never chat. Scripts are supplied source assets and have not been executed here. Package checks do not prove runtime compatibility.

## Included dependencies

- [ap-voice-recognition](../../../voice-recognition/skills/ap-voice-recognition/README.md) — optional; identifies which saved voice profile a speaker's voice sample matches. Not required: without it, speaker labels stay generic and unresolved ones are flagged for the human.

## Setup, update and removal

Use your host's documented skill directory and check discovery in a fresh session. Start with the harmless draft trigger above. On update, compare versions, back up the old complete folder and merge your private settings separately; never overwrite them with these blanks. Remove only this installed skill folder after approval. Disabling a skill does not revoke connections, undo profile edits or stop existing schedules: revoke/disable those separately using the saved setup record. Preserve user-created notes and backups.
