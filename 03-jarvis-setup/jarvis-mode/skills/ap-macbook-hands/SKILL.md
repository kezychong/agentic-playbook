---
name: ap-macbook-hands
description: "Operate an approved Mac screen with verified UI steps."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Main computer hands

Hands are an optional JARVIS Mode extra for a member whose main computer is a
Mac. This skill is installed only when the member chose that extra.

## Two pairs of hands

- `computer_use` acts on the agent host's screen.
- `__JARVIS_HANDS_COMMAND__` acts on the member's configured
  main computer. The installer writes that selected profile's private
  `jarvis/hands/config.json`; the command refuses missing or invalid config.

Use the installed path through the terminal tool. The command never chooses a
host or profile for the member.

## The loop

1. `__JARVIS_HANDS_COMMAND__ status` — check readiness first.
2. `__JARVIS_HANDS_COMMAND__ call list_windows '{"on_screen_only":true}'`
   — start with the small on-screen list; it includes app, pid, window id and title.
3. `__JARVIS_HANDS_COMMAND__ call get_window_state '{"pid":501,"window_id":42,"query":"save","max_elements":60}'`
   — keep the result's `snapshot_id`; always pass `query` or `max_elements`.
4. Act with that same `snapshot_id` and `element_index`, then read the window again:
   `__JARVIS_HANDS_COMMAND__ call click '{"pid":501,"snapshot_id":"<id>","element_index":7}'`
5. Check the new state before reporting what happened. Never repeat an action blindly.

`hotkey` takes a `keys` list. `press_key` takes `key` and `modifiers`.
Run `describe <tool>` before the first use of a tool. `list_apps` is about 49 KB
on a typical computer, so use it only to check whether an app exists; those
kilobytes are too large for the normal loop. Use `launch_app` with its `bundle_id`
to open an app.

Screenshots are saved locally and returned as `screenshot_file_path`; open that
path with the vision tool when you need to see the screen.

## Focus and privacy

The driver acts in the background. Do not call `bring_to_front` unless the
member asks to watch; it takes the member's focus. A window that is off screen,
on another Space, or unresolved must be reported before asking to bring it forward.

- Never type a password, payment number, or one-time code.
- Never create an account, buy, send, post, publish, or delete without the member's word in this conversation.
- Keep private screen content out of logs, reports, and other agents' briefs.
- On a spoken call, say the planned action once and report within about twenty seconds.

## When it is not ready

- Exit 5: grant Accessibility and Screen Recording to CuaDriver on the main computer.
- Exit 3: the configured computer is asleep or unreachable.
- Exit 4: CuaDriver is not installed at the configured driver path.
- Exit 6: try `__JARVIS_HANDS_COMMAND__ wake` once; the daemon could not start.
- Exit 1: the driver refused; read its `error` and `message`, then fix the cause.
- Exit 124: the outcome is unknown; inspect the window before acting again.
- Exit 2: the local guard refused the request; do not route around it.
