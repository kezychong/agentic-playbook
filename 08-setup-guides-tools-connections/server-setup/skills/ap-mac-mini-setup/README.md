# Mac Mini Setup

Agentic Playbook — **by Kezy** · 0.1.0

A spare Mac mini becomes a box only your agents use: no screen, always on, reachable from your laptop.

## Before you start

A Mac mini you can dedicate to agents (no Apple ID, no saved passwords, no banking on it), Claude Code on it, and Tailscale on both machines. Copy the whole folder with its support files and required companion folders. Review [the full method](SKILL.md) before use. Never run installation commands merely because this folder was loaded.

## Try it

> Show me the Mac mini box steps as a checklist. Change no settings yet.

Expected output: The step list (power, auto-login, screen access, Hermes, optional Codex, connect file) with each macOS prompt the owner will see.

## Limits and permissions

This recipe deliberately sets the box so agents act without approval prompts. That is a trust decision for the owner: read it before you agree, and keep nothing personal on the machine. Sending, publishing, spending, deletion, installation, scheduling and live account/profile changes require explicit approval of the concrete action. Keep credentials in secure local setup, never chat. Scripts are supplied source assets and have not been executed here. Package checks do not prove runtime compatibility.

## Included dependencies

- [Connect My Machines](../../../connect-my-machines/README.md) — required: the laptop reaches the mini over Tailscale.

## Setup, update and removal

Use your host's documented skill directory and check discovery in a fresh session. Start with the harmless draft trigger above. On update, compare versions, back up the old complete folder and merge your private settings separately; never overwrite them with these blanks. Remove only this installed skill folder after approval. Disabling a skill does not revoke connections, undo profile edits or stop existing schedules: revoke/disable those separately using the saved setup record. Preserve user-created notes and backups.
