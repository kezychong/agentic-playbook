---
name: ap-connect-to-capture
description: "Link the owner's WhatsApp through WhatsApp Web on the box, write one read-only reader per connected tool, and add them to the existing nightly capture without a new job. Use for \"connect my WhatsApp\", \"give my Capture bot my tools list\" or \"connect [tool] to my nightly capture\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag it onto your brain folder, then tell Hermes: Read ap-connect-to-capture.md in my brain folder and connect my WhatsApp.

# Connect to Capture: WhatsApp, your tools and your old notes, into your capture

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-connect-to-capture.md in my brain folder and connect my WhatsApp." Do nothing else with this file.

**For Hermes.** The member dragged this file into their brain folder. First, link the member's WhatsApp through WhatsApp Web on this box. Then hand the Capture bot every tool on `_System/tools-list.md` (made on Stage 8) so each joins the **Nightly chat capture** it already runs at 23:00 (Stage 5). You add **no new scheduled job**. Test each tool once, now, and report.

## The member's sentences

| The member says | You do |
|---|---|
| Read ap-connect-to-capture.md in my brain folder and connect my WhatsApp. | Part 0, then report |
| Give my Capture bot my tools list and start capturing. | Parts A to D, then report (pour in old notes first if you have them) |
| Connect [tool] to my nightly capture. | Parts A to C for that one tool |

## Rules for this pack

- Keep this pack: move this file into `_System/packs/` (replace an older copy) and add one line under `## Packs you have` in AGENTS.md naming the sentences above and this file.
- **Keys:** read them only from `~/.hermes/.env` by name, inside the command that uses them. Never print, copy or repeat a value. A key that is missing: tell the member, in one line, to tell Claude Code on the laptop "Add a key for [tool]." Never ask for a key in chat.
- **Sign-ins:** where a tool connects by signing in, start the tool's own sign-in flow and give the member the link or the steps; a password is typed only by the member, on the tool's own page, never into the chat.
- The capture rules are the Capture bot's own (one source = one whole note, title naming the real subject, source line; keep decisions, promises, facts, ideas, lessons; skip small talk, setup chatter and anything secret). Do not restate or change them here.
- Report in plain words, no file paths unless asked. If stuck: "Record the failing step without secrets and consult your host support documentation."

## Part 0: connect WhatsApp

A personal WhatsApp number has no connector, plugin, MCP or API. The way in is WhatsApp Web on this box, the same page the member would open on a laptop.

1. **A browser on the box.** If this box has no browser Hermes can drive, install Chromium for it (on a VPS it runs without a screen). Use one browser profile for the Capture bot that survives restarts, so tonight's capture and every later one use the same WhatsApp link. Check Hermes's own browser docs for the current way on this box.
2. **Open web.whatsapp.com** in that browser.
3. **Show the QR code:** take a screenshot of WhatsApp's QR code and show it to the member in the Hermes app. Tell them: "On your phone, open WhatsApp, Settings, Linked devices, Link a device, and scan this." If the code expires before they scan, show the new one.
4. **Prove it:** read the newest chat's title and tell the member the title only, not its content.
5. On the WhatsApp row of the tools list, set Route to `WhatsApp Web` and Status to `connected`. If WhatsApp is not on the list yet, add it under Fulfilment.
6. Any other tool whose Route is a web page (`browser`) on the tools list (a tool whose only way in is its own web page): same steps with its own page; a password is typed by the member on that page, never in the chat.

Report: "Your WhatsApp is linked. Next, say: Give my Capture bot my tools list and start capturing."

## Part A: one reader per tool

For each tool on the tools list: use its Stage 8 route to read the last 24 hours (its Hermes plugin, its MCP, its API with the key from the locked drawer, its CLI, or for WhatsApp and any `browser` row the logged-in browser from Part 0). Write a short reader script into the Capture bot's `scripts/` folder (`<capture-bot home>/scripts/read-<tool>.sh`) that prints the last 24 hours as plain text (who, when, what), one thread or conversation per block, and nothing else. A tool that cannot connect by connector, plugin, MCP or API/CLI: set its Route to `browser` and run Part 0 step 6 for it.

## Part B: join the nightly capture

1. Add one step to `_System/jobs/nightly-chat-capture-prompt.md`, after the chat export step and before the notes are written: "Run each `read-<tool>.sh` in your `scripts/` folder; treat each thread or conversation it prints like a chat: one note per meaningful one, with a source line naming the tool and the date."
2. Update the job's row in the jobs table: the What it does column now names the connected tools. The time (23:00) and Run by (Capture bot) do not change. Do not create another job.

## Part C: test each tool now

Run each reader once and write at most one note per tool, the newest meaningful thread, into `01. Inbox/agent-drops/` with the usual capture rules. Set the row's Status to `connected` (worked) or leave it with the error in one plain line. A tool that cannot connect by connector, plugin, MCP or API/CLI: set its Route to `browser` and run Part 0 step 6 for it. Then show the member the tools table: a tick for each tool that worked, or what is missing in one plain line.

## Part D: check

Start a new session yourself and answer "What runs on its own?" from the jobs table: still the one Nightly chat capture at 23:00 (and nothing else unless the member made it), now naming WhatsApp and the connected tools.

## Report back

1. "Connected to your nightly capture: [tools]. Still missing a key or sign-in: [tools]."
2. One line per tested tool: what it found, and the title of its test note.
3. "Nothing new runs on its own: your 23:00 capture now reads these tools too. Once Dreaming and Recall is approved, your Link, Organise and Signal bots run every night after it."
