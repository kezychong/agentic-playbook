---
name: ap-whatsapp-capture
description: "Capture approved chats with explicit read-receipt consent."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# WhatsApp Capture

Every two hours, you open WhatsApp Web on the member's always-on machine.
You read chats with new messages and save them as notes in their second brain inbox.
The member never forwards a message again. You know what was said.

Adapted from the supplied workshop method. Repackaged as Agentic Playbook — by Kezy.

## Who this is for

The member is a business owner who uses the Claude app, the Codex app, or a Hermes agent in chat.
They are not technical. You do all setup, installs, and file work.
They answer a few short questions and scan one QR code with their phone.
Never ask them to choose a technical option, open a file, or install anything.

## Why WhatsApp Web

WhatsApp has no official way to pull chats automatically from a personal number.
The WhatsApp Business API only covers business numbers.
So this skill reads WhatsApp Web the way a person would: open, read, save, leave.
Tell the member this plainly at setup. Heavy automation can get a number restricted, so this skill stays gentle.

Before linking, also tell them: "When I open a chat to save it, WhatsApp marks it as read. Your unread badges will clear every two hours, and people may see blue ticks if you have read receipts on. Reply OK to continue." Wait for OK. Do not link without it.

## One method, two machines

Work out which always-on machine the member has. Never ask them to pick.
- A Mac with a screen (usually a Mac mini): use the Mac mini version.
- A Linux server with no screen (a VPS, a rented computer in the cloud): use the VPS version.
- If you are running on the member's laptop, do the work on their always-on machine through the connection they already have. Install this skill for the agent on the always-on machine too, because the scheduled job runs there.
- The scheduled job starts that agent every two hours with the instruction "Run my WhatsApp capture now" and this skill. There is no separate program to maintain.
- If there is no always-on machine, stop. Tell them in one sentence that this skill needs a machine that stays on.

Read [the two machines guide](references/two-machines.md) before setup. It covers the browser, the QR link, and the schedule for each version.

Install whatever browser automation you need yourself (for example a Chromium browser plus a browser automation library).
Narrate it in plain words: "Setting up the browser I use to read WhatsApp Web. This takes a few minutes."

## Setup: four tap-in asks

Ask one at a time. Each answer should be one word or a short list.

1. **Machine.** Tell them which machine you found: "I will run this on your Mac mini. Reply OK." (or "your VPS").
2. **Link.** "On your phone, open WhatsApp, go to Settings, then Linked devices, then Link a device. Scan the code I show you. Reply OK when done."
3. **Exclude.** "Any chats I should never save, like a family group? Reply NONE or list the names."
4. **How far back.** "Should the first capture start from today? Reply TODAY (recommended) or give a date." WhatsApp Web only shows what the phone has synced. If they give an earlier date, save what each chat already shows back to that date, at human pace, once. Tell them older messages may be missing. After the first run, capture only new messages.

Find the second brain inbox folder yourself. If you cannot find one, ask once where their notes live.
Save their answers in the capture settings file from [the settings template](assets/capture-settings-template.md).
Keep that file at `<inbox>/whatsapp/capture-settings.md`.

## Every run: the capture rules

1. **Read only.** Never send, reply, react, delete, archive, or mark a chat as read on purpose. Opening a chat can show it as read on the phone. That is a side effect, never a goal.
2. **No media.** Never open or download photos, voice notes, videos, or files. Write `[photo]`, `[voice note]`, `[video]`, or `[document: file name]` in their place.
3. **Health check first.** If WhatsApp Web shows logged out, "phone not connected", or a QR code, stop. Do not retry in a loop. Tell the member in one plain sentence: "WhatsApp Capture is paused because WhatsApp logged out. Say 're-link my WhatsApp' and I will show you a new code."
4. **Only new messages.** Read the watermark for each chat: the time of the last message you saved. Take only newer messages.
5. **Only chats with new messages.** Skip chats on the exclude list. Skip muted and archived chats unless the member opted them in.
6. **Privacy filter before writing.** Replace one-time codes, verification codes, passwords, bank or card numbers, and API keys with `[code removed]`.
7. **Human pace.** One run every two hours. Open chats one at a time with short pauses. Never scroll back through old history in bulk.
8. **Write the notes.** Append to each chat note, write the digest, then update the watermarks and the last successful run time in the settings file.

## Output: where notes go

One running note per person or group, named by the chat name, never a phone number:
`<inbox>/whatsapp/chats/<Chat Name>.md`. Use [the chat note template](assets/chat-note-template.md).
Append a dated section each run. Each line is: time, who said it, text. The member's own messages show as "Me".

One short digest per day: `<inbox>/whatsapp/YYYY-MM-DD-digest.md`. Use [the digest template](assets/digest-template.md).
List each chat with new messages and how many. Add to the same day's digest on later runs.

The inbox is where raw files land before the member or their agent sorts them. Do not file captures anywhere else.
On the VPS version, notes reach the member's laptop through whatever sync their second brain already uses.

## Test: right after linking

Run one capture immediately. Then show the member:
- the digest note, with its file path;
- one chat note, with its file path;
- the schedule is set, and the time of the next run.
If the test fails, say what failed in one sentence and fix it before setting the schedule.

## Member requests

- "Run my WhatsApp capture now": run once, then report chats and message counts.
- "Re-link my WhatsApp": show a fresh QR code (on the VPS, send it as a picture in chat) and wait for OK.
- "Don't save <chat>" or "Also save my archived chats": update the settings file and confirm.
- "Is my WhatsApp capture working?": report the last successful run time and the next run time.
- "Stop my WhatsApp capture": remove the scheduled job. Then tell the member: "On your phone, open WhatsApp, go to Settings, then Linked devices, tap <the device name and last-active time you see for this browser>, and tap Log out." Fill in the real name so they do not log out their laptop. Keep their saved notes. If they ask you to delete them, first move the whatsapp folder into a dated backup folder and ask "Delete the backup too? Reply YES or KEEP." Delete only on YES.

## Hard rules

- Read only. Never send, reply, react, delete, or archive anything in WhatsApp.
- Never open or download media.
- Never claim full history or media capture. You capture new text from the chosen start, and only what WhatsApp Web shows.
- Filter codes, passwords, and account numbers before anything is written.
- One run every two hours. Stop on any logout and tell the member once.
- Chat names, never phone numbers, in file names.
- Do all setup and file work yourself, and tell the member where their notes live.

## Related

Recording calls with Plaud? Ask your agent to connect Plaud's MCP and pull new transcripts every morning into the same inbox.

## Files

| File | Read it when |
|---|---|
| [Two machines guide](references/two-machines.md) | Before setup, before re-linking, and when a run fails |
| [Settings template](assets/capture-settings-template.md) | At setup and whenever the member changes a choice |
| [Chat note template](assets/chat-note-template.md) | The first time you save a chat |
| [Digest template](assets/digest-template.md) | The first run of each day |
