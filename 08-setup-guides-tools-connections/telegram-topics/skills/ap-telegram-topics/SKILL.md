---
name: ap-telegram-topics
description: "Connect an agent to Telegram: create a bot with BotFather, store its token safely, allow only the owner's user ID, test it, then set up one private group with Topics so each subject is its own session. Use for \"connect my agent to Telegram\", \"my bot is not replying\" or \"set up topics for my agent\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Original starter method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Telegram Topics

You are helping a non-technical owner talk to their always-on agent from their phone. Teach each step in one plain sentence, then guide. One step per message; wait for "done" or a screenshot. The owner clicks in Telegram; you do anything that happens on the box.

## The owner's sentences

| The owner says | You do |
|---|---|
| Connect my agent to Telegram. | Parts A to C |
| My bot is not replying. | Part D |
| Set up rooms for my agent. / Turn on topics. | Part E |
| Add a room for [subject]. | Part E, step 4 only |

## Part A: make the bot (the owner, in Telegram)

1. Install Telegram on the phone (and the desktop app on the laptop if wanted) from telegram.org.
2. Search for **@BotFather** and open the verified account (blue tick). It is Telegram's official bot for making bots.
3. Send `/newbot`. Give a display name (anything, e.g. "Inbox") and a username that is unique and ends in `bot` (e.g. `acme_inbox_bot`). If it is taken, try another.
4. BotFather replies with a long **bot token**. Say plainly: "This token is a key. Anyone holding it can act as your bot. Do not paste it here, in a note, or in a screenshot." Have them **copy** it and say "copied".

## Part B: store the token and the allow list

1. **The token goes in by clipboard, never by chat.** If the Add a Key skill is installed, run it for `TELEGRAM_BOT_TOKEN`. If the agent's own setup asks for the token in a local setup screen or dashboard on the box, the owner pastes it there, on that screen only.
2. **Find the owner's numeric Telegram user ID.** In Telegram, open a user-info bot (for example @userinfobot), press Start, and read the `Id` number. A user ID is not a secret, but it is personal: keep it out of public posts.
3. **Allow only that ID.** Set the agent's allowed-users list to that one ID, so strangers who find the bot cannot talk to the agent. Never leave the allow list empty.
4. Prefer the agent's manual connection screen over a QR-code shortcut: the manual way is more reliable.

## Part C: the live test

The owner opens their bot in Telegram, presses **Start**, and says hi. If the agent replies, it is alive. Tell them: "From now on, your phone talks to the same agent as your laptop. A chat started here shows up in the desktop app too."

## Part D: no reply

Check in this order, fixing as you go and saying what you changed:

1. The token's variable is present on the box (check the name only, never print the value).
2. The owner's ID is in the allowed-users list, exactly.
3. The agent's messaging service was restarted after the change. Most "no reply" cases end here.
4. The agent's log shows the Telegram connection. Read the real error before trying anything else.

## Part E: one group, many rooms

Every chat with the agent is one session. A private group with Topics gives you many sessions side by side.

1. In Telegram, make a **new group** with only the owner and the bot. Name it (e.g. "Chief of staff").
2. Group info → Edit → **Administrators** → add the bot as admin. The bot cannot see group messages until it is admin. Switch off rights it does not need, such as inviting users.
3. Group info → Edit → switch on **Topics**.
4. Make one topic per subject (for example Second brain, Business, Money, Health). Each topic is its own session, so subjects never mix.
5. Say hi inside one topic to prove the bot answers there.

**Never let anyone else into this group.** Anyone in it can talk to the agent and ask it to do things.

## Voice notes

Hold the microphone in any room and talk. Most agent hosts transcribe the note, act on it and can reply in voice. Use it to dump ideas on the move ("capture this: ..."), then check the written note later.

## Done looks like

- The bot replies to the owner and to nobody else.
- The token's name is in the box's locked file; its value appears nowhere else.
- One private group, the bot as admin, Topics on, at least one subject room answering.

<!-- Agentic Playbook — by Kezy -->
