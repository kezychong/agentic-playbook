# Create Goal Prompt

Agentic Playbook — **by Kezy** · 0.2.0

Build a measurable goal prompt with stopping rules for Hermes Agent, Claude Code, or Codex.

## Before you start

A concrete objective, acceptance evidence and a bounded working area. This is an adapted supplied method, not a live configured profile. Copy the whole folder with its support files and required companion folders. Review [the full method](SKILL.md) before use. Never run installation commands merely because this folder was loaded.

## Try it

> Turn “draft our customer handbook” into a bounded goal prompt.

Expected output: A copyable objective, fresh-evidence checks, constraints, boundaries, progress expectations and stopping conditions. Hermes output uses the generic `/goal` contract fields `verify`, `constraints`, `boundaries`, and `stop when`, with supported controls explained separately.

## Hermes goal support

Hermes goals use the turn budget configured by the host. The skill does not invent or change that value. It can also explain `/goal status`, pause, resume and clear; add criteria with `/subgoal`; and suggest a deterministic read-only quality gate. The active goal, its contract, subgoals and gates persist with the Hermes session and return when that session is resumed. Completion evidence must be freshly produced and visible in the conversation.

## Limits and permissions

Creating a prompt does not start a goal or authorize autonomous external actions. Sending, publishing, spending, deletion, installation, scheduling and live account/profile changes require explicit approval of the concrete action. Keep credentials in secure local setup, never chat. Scripts are supplied source assets and have not been executed here. Package checks do not prove runtime compatibility.

## Included dependencies

No other packaged skill is required.

## Setup, update and removal

Use your host's documented skill directory and check discovery in a fresh session. Start with the harmless draft trigger above. On update, compare versions, back up the old complete folder and merge your private settings separately; never overwrite them with these blanks. Remove only this installed skill folder after approval. Disabling a skill does not revoke connections, undo profile edits or stop existing schedules: revoke/disable those separately using the saved setup record. Preserve user-created notes and backups.
