---
name: ap-drop-your-chats
description: "Place a ChatGPT or Claude chat export whole into 08. Sources with a progress file, without reading it. Use for \"put my chat export in my Inbox\" or \"my export came late\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag your ChatGPT or Claude export zip onto 01. Inbox in your brain folder, drag this file onto your brain folder, then tell Hermes: Read ap-drop-your-chats.md in my brain folder and put my chat export in my Inbox.

# Drop Your Chats: put your old chats in the brain

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-drop-your-chats.md in my brain folder and put my chat export in my Inbox." Do nothing else with it.

**For Hermes.** The member dragged their chat export (the zip they requested from their AI app) onto `01. Inbox` and this file onto the brain folder. Today you only **place** the export: the whole raw export goes into `08. Sources`, untouched, because a whole chat export is too long for one Inbox note. You do not read the chats or write notes from them. The Capture bot (made with the Capture Bot package) does that in its Nightly chat capture at 23:00, working through the whole export, each meaningful conversation as one whole note in `01. Inbox/agent-drops/`, linked back to the export.

## The member's sentences

| The member says | You do |
|---|---|
| Read ap-drop-your-chats.md in my brain folder and put my chat export in my Inbox. | Everything below, then report |
| My export came late. Put it in my Inbox. (any later day) | The same steps |

## Rules for this pack

- You are Hermes, on the member's box. The brain folder there: find its full path once with `hermes config get terminal.cwd` (set on Stage 4; if that is empty, `echo "$HOME/second-brain"`). It is `second-brain` in the box account's home folder: the `hermes` user's home on a rented server, the member's own Mac account on a Mac mini. Work from it.
- A file the member just dragged in may still be arriving through the mirror. A big export takes longer: if the zip is missing, or a `.syncthing.*.tmp` file sits beside it, wait and look again (up to a few minutes) before you say it is not there.
- Keep this pack: move this file into `_System/packs/` (replace an older copy) and add one line under `## Packs you have` in AGENTS.md: `- Drop your chats: when I say "Put my chat export in my Inbox." or "My export came late.", read _System/packs/ap-drop-your-chats.md and follow it.`
- Ask the member before spending money, deleting things, installing, scheduling or changing a live profile. Prepare everything else as a short plan, apply it on approval, then report.
- Report in plain words, no file paths unless asked. If stuck, say what you saw, then: "Record the failing step without secrets and consult your host support documentation."

## Steps

1. Find the export in `01. Inbox/`: a zip (or folder) holding `conversations.json`. ChatGPT and Claude both use that name; several exports are fine.
2. Unzip each into `08. Sources/chat-exports/<tool>-<date>/`, keeping only `conversations.json` (and any `projects.json` or `memories.json`). Leave images, audio, video, billing and account files out. Move the zip itself into that folder, so nothing of it is left in `01. Inbox`.
3. Count the conversations in each export. Write `08. Sources/chat-exports/<tool>-<date>/progress.md` with one line: `0 of <N> chats done`. The Capture bot's Nightly chat capture reads this file and works through the whole export until it is done.
4. Check the Capture bot's jobs list (`hermes -p capture-bot cron list`) shows Nightly chat capture. If the Capture bot is not made yet, say: "Your export is safe in 08. Sources. Set up your Capture bot (the Capture Bot package) and it starts on it that night."
5. Nothing else. Do not open the chats or write notes from them.

## Done looks like

- One `08. Sources/chat-exports/<tool>-<date>/` folder per export, with `conversations.json`, the zip and `progress.md`.
- Nothing of the export left in `01. Inbox`; no notes written from the chats yet.

## Traps

- No export found and no email yet: say "No export yet. When it comes, drag the zip onto 01. Inbox and tell me: My export came late. Put it in my Inbox." Then stop. No export at all is fine: the Inbox fills from what the member captures.
- The download link dies about a day after the email lands: if the member says the link expired, tell them to request the export again, once.

## Report back

1. "Your chat export is safe: <N> conversations from <tool>. Nothing is thrown away: the whole export is kept in 08. Sources."
2. "Your Capture bot works through it every night at 23:00 until they're all done, and keeps each conversation where you made a decision, a promise or a plan, or gave facts or ideas, as one whole note in your Inbox. You get a Telegram line with how far it is, like: 50 of 1,240 chats done."
