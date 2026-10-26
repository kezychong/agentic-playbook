> Agentic Playbook — by Kezy. Optional manual procedure; untested in this repackage. Loading this document does not authorize execution. Obtain approval for installation, scheduling, sending, publishing, spending, deletion and live profile/account changes. Keep secrets out of chat.

---
stage: shipped
---

# WhatsApp Capture: Install and Use

## What it does

Every two hours, your agent reads new WhatsApp messages and saves them as notes in your second brain inbox.
It uses WhatsApp Web on your always-on machine (your Mac mini or your VPS). Your agent works out which one.
You get one note per person or group, plus a short daily digest of who messaged and how many times.
It only reads. It never sends, replies, reacts, or deletes anything.

Adapted from the supplied workshop method. Repackaged as Agentic Playbook — by Kezy.

## Who this is for

- You are a business owner who talks to clients and your team on WhatsApp.
- You use the Claude app, the Codex app, or a Hermes agent in chat.
- You do not need technical skills. Your agent does all setup and file work.

## What you need first

- An always-on machine: a Mac mini or a VPS (a rented computer in the cloud).
- A second brain with an inbox folder.
- Your phone with WhatsApp on it, for one QR scan.

## Good to know

- WhatsApp has no official way to save chats automatically from a personal number. So this reads WhatsApp Web the way you would.
- It runs gently: once every two hours. Heavy automation can get a number restricted.
- It saves text from the day you choose (today is recommended). It does not copy your full history.
- Photos, voice notes, and files are not saved. The note says "[photo]" or "[voice note]" instead.
- Login codes, passwords, and card numbers are replaced with "[code removed]".
- Muted and archived chats are skipped unless you ask. Say "Also save my archived chats" to include them.
- When your agent opens a chat to save it, WhatsApp marks it as read. Unread badges clear every two hours, and senders may see blue ticks if you have read receipts on. Your agent asks you to reply OK to this before linking.

## Install

Install it on the agent that runs on your always-on machine, because that is where the capture runs. If you use Hermes, send the zip to your Hermes agent in chat as an attachment. Otherwise, open the Claude app or the Codex app on your laptop and your agent will set it up on your always-on machine.

Download the zip and say:

```
Install this skill from ap-whatsapp-capture-v1.0.0.zip and set up my WhatsApp capture.
```

Your agent installs what it needs itself. You never touch a file.
Then it asks you four short questions:
1. Which machine it found. Reply OK.
2. Scan the QR code your agent shows you in the chat. On your phone: WhatsApp, Settings, Linked devices, Link a device. Reply OK.
3. Chats to never save, like a family group. Reply NONE or list the names.
4. When to start saving from. Reply TODAY (recommended) or give a date.

## Check it worked

Right after you link, your agent runs one capture and shows you:
- today's digest note, for example `whatsapp/2026-09-29-digest.md` in your inbox;
- one chat note, for example `whatsapp/chats/<chat name>.md`;
- the time of the next run.

Later, ask:

```
Is my WhatsApp capture working?
```

It tells you the last time it saved messages and when it runs next.

## How to use it

It runs on its own every two hours. You can also say:

```
Run my WhatsApp capture now.
```

```
Don't save my family group anymore.
```

```
Re-link my WhatsApp.
```

If WhatsApp logs out, your agent pauses and sends you one message. Say "Re-link my WhatsApp" and scan the new code.

## How to undo

Say:

```
Stop my WhatsApp capture.
```

Your agent removes the schedule and tells you which linked device to remove. Then on your phone: WhatsApp, Settings, Linked devices, tap that device, tap Log out.
Your saved notes stay in your inbox. If you ask your agent to delete them, it backs them up first and asks you to reply YES before anything is deleted.

Recording calls with Plaud? Ask your agent to connect Plaud's MCP and pull new transcripts every morning into the same inbox.
