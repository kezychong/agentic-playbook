---
name: ap-add-a-key
description: "Add a service API key, token or password from the clipboard into the box's locked .env file without it appearing in chat, output or logs, and keep a names-only key list. Use for \"add a key for [service]\", \"I got a new key\", \"check my Telegram token\" or \"I pasted a key into a chat\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Add a Key

**If you are Hermes on the member's box, stop here.** This pack is for Claude Code on the member's laptop, because a key travels through the laptop's clipboard and must never pass through a chat. Tell the member in one line: "This one is for Claude Code on your laptop: add it to a Claude Code chat and say: Turn this into a skill." Do nothing else with this file.

**For Claude Code.** The member took this file from the Add a Key package and dragged it into your chat, then said "Turn this into a skill." Read all of it now, save it as a real skill you can reuse, then wait for the member's next sentence.

**If a step behaves differently** from this pack: stop, tell the member in one plain sentence what you saw, try the known fix, and report what you changed.

## Why a key never goes in chat

Everything typed to an agent is saved to a history file on that machine. Paste a key once and a copy sits in that log for good. So the key takes another road: the clipboard, piped straight to the box. The conversation only ever holds the recipe (`$(pbpaste)`), never the ingredient. Never run `pbpaste` on its own, not even to check: check the clipboard's length (`pbpaste | wc -c`), never its content.

## Goal

By the end of today the member has:

1. A saved ap-add-a-key skill, so "Add a key for [service]" always works the same safe way from now on, in this chat and in every new one.
2. A demo key added by the drill: it goes from the member's clipboard, over SSH, into the locked drawer on their box, and comes back shown masked, never in full.
3. The worked example run once: the key for the first tool on their tools list marked `needs a key` (Hermes made the list today), added and proved with one read. A member with no such tool skips this; their skill is still made.
4. Their Telegram token checked as present in the locked drawer.
5. A names-only key list started in their brain, so they can always see which keys exist without ever seeing a value.

## Before you start

- This builds on Stage 2 (the server saved as **my box**, `ssh mybox`, user `hermes`), Stage 4 (the brain folder mirrored between laptop and box), Stage 5 (the Capture bot) and today's tools list (`_System/tools-list.md` in the brain), where Hermes marked each tool's route and every tool that takes a key as `needs a key`.
- **The locked drawer** is the plain file every key lives in: `~/.hermes/.env` on the box. Some tools keep their own file instead. If you are not sure which file a tool reads, ask the member which tool the key is for, then check that tool's own setup notes before writing anywhere new. Never guess a new file.
- **Who uses the key:** Hermes reads it from the locked drawer, by name, when it reads that tool (through the tool's API or CLI). You only put the key in place; Hermes proves it when the member says "Show my tools table."

## The one rule above all others

**Pipe it, never print it.** Read a key from the clipboard only inside a command that pipes it straight to where it lives. Never run `pbpaste` on its own, not even to check what is there. The moment a key appears in your output, it is written into this chat's saved history, and the whole point of the drill is defeated. To check the clipboard holds something, check only its length: `pbpaste | wc -c`.

## Who does what

- **You (Claude Code)** read the key from the clipboard, write it into the right file over SSH, show it back masked, restart whatever needs it, test it, and add its name (never its value) to the key list.
- **The member** clicks copy on the key in the service's own site, then tells you "copied". The only place they may paste it is their own password manager, if they keep one; they never paste a key into this chat, a note, Telegram or anywhere else. If they ever try to paste one here, stop them and run this skill instead.
- One short line before each step. No jargon without a one-line explanation.

## The member's sentences, word for word

| Part | The member says | You run |
|---|---|---|
| 2 | Turn this into a skill. | Part A |
| 3 | Add a key for [tool]. (the first one is the worked example, Part C) | Part B, then Part C the first time |
| any, later | Add a key for [service]. (here.now Publishing uses it for here.now) | Part B |
| 3 | Check my Telegram token is in the locked drawer, and start my names-only key list. | Part D |
| any | I think I pasted a key into a chat somewhere. | Part E |
| any | Connect to my box and fix Hermes. | Known fixes, then `hermes doctor` |

## Part A: save the skill

1. Save this whole file as your own reusable skill, so "Add a key for..." works the same way in any future chat on this Mac without being taught again. Do exactly this:
   - Write it to `~/.claude/skills/ap-add-a-key/SKILL.md`. That makes it a personal skill, there in every chat on this Mac, not tied to one folder.
   - Replace the header at the very top (the block between the two `---` lines) with just the skill's name and a description: `name: ap-add-a-key`, and a `description:` line saying it adds an API key from the clipboard to the locked drawer on my box without ever showing it.
   - Rewrite the opening paragraph (the one starting "For Claude Code.") so it says this is the saved Add a Key skill: follow it whenever the member says "Add a key for...", and do not save it again.
   If the skill does not show up in a new chat, keep this file open for the rest of the session and follow it by hand every time.
2. **Check:** ask yourself "Add a key for a test service" and confirm you would follow Part B without re-reading this file.
3. **Report to the member:** "Your Add a Key skill is saved. From now on, just say 'Add a key for...' and I will handle it the same safe way."

## Part B: the ap-add-a-key drill (any service)

1. **Ask which service, in plain English**, and which tool on the box actually uses it (usually Hermes, or the tool's own CLI). If you are not sure, ask the member; do not guess.
2. **Ask the member to copy the key, not paste it here.** Say exactly: "Click copy on the key in [service]'s site. Paste it only into your password manager if you keep one, then click copy again and tell me copied. Never paste it into this chat, a note or Telegram."
3. **Check the clipboard holds something, without reading it:** `pbpaste | wc -c` prints a number greater than zero.
4. **Pipe it straight into the locked drawer.** First make sure the file ends with a line break, or the new key gets glued onto the last line and both keys break:
   ```
   ssh mybox 'f=~/.hermes/.env; if [ -s "$f" ] && [ -n "$(tail -c1 "$f")" ]; then echo >> "$f"; fi'
   ```
   Then append the key, one line, from the laptop:
   ```
   echo "SERVICE_KEY_NAME=$(pbpaste)" | ssh mybox "cat >> ~/.hermes/.env"
   ```
   Use the real environment variable name for that service in place of `SERVICE_KEY_NAME` (check the tool's own setup notes, or the existing `.env`, for its convention). If that variable already exists in the file, remove the old line first, touching only the variable name, never its value. If the sandbox blocks clipboard or network access for this one command, use the session's sandbox-off path just for this step.
5. **Confirm without showing any characters:** `ssh mybox "grep -q '^SERVICE_KEY_NAME=.' ~/.hermes/.env"`. Use only whether that command succeeds or fails.
6. **Restart whatever reads this key.** For keys Hermes reads: `ssh mybox 'hermes gateway restart; pkill -f "serve --isolated" || true'`. Since Stage 3 the Hermes desktop app runs its own Hermes server on the box (the `hermes serve --isolated` process), and `hermes gateway restart` does not touch it; the `pkill` stops it and the app starts it again by itself within seconds, with the new key (the same restart Hermes's own packs use). If the key belongs to a different tool, restart or reload that tool by its own command instead.
7. **Test it** with the smallest real check you can, for example one short question to Hermes that needs the new key. (The first key's own test is Part C.)
8. **Show the member the key back masked:** name only, and "in place", no characters of the value. For example: "SERVICE_KEY_NAME is in place." Never echo the file, never print the value, not even part of it.
9. **Add one line to the names-only key list** (Part D step 3) so it is not forgotten.
10. **Have the member clear the clipboard:** they copy any other short piece of text, or, on the machine that held it, you run `printf 'cleared' | pbcopy`. If they use a clipboard history app, tell them to delete the key's entry there too.

## Part C: the worked example, your first key

The worked example is the first tool on the member's tools list marked `needs a key`. Ask the member which one that is if you cannot see the list. Making the account and the key is the member's own step, on that tool's own site. If they have no tool that needs a key today, skip Part C and say so: "Your ap-add-a-key skill is made. Use it whenever a tool needs a key."

1. **Find the key page.** If the member cannot find where the tool makes keys, look it up in the tool's own help pages and tell them where it is. Prefer a key that can only read, if the tool offers that choice.
2. Run Part B in full for that key, under the variable name the tool's own docs use (or `<TOOL>_API_KEY` if they name none).
3. **Hand over to Hermes.** Tell the member: "Your [tool] key is in place. In the Hermes app, ask: Show my tools table." Hermes checks the name and proves one read through the tool.
4. **Report to the member:** "Your [tool] key is in place, shown by name only. Say Add a key for [tool] for each other tool marked needs a key."

## Part D: Telegram token and the names-only list

1. **Check the Telegram token is in the locked drawer**, without printing it:
   ```
   ssh mybox "grep -qE '^TELEGRAM_(BOT_)?TOKEN=.' ~/.hermes/.env"
   ```
   (Usually the name is `TELEGRAM_BOT_TOKEN`. Still check the file's real variable names first, and use the one you find.)
2. If it is missing, tell the member in one line and point back to the Stage 3 Telegram setup's BotFather route to get a token, then add it with Part B.
3. **Start or add to the names-only key list**, in the brain at `_System/KEY_LIST.md`. One line per key, name and the day it was added, never a value. For example:
   ```
   - TELEGRAM_BOT_TOKEN, added Stage 3, checked Stage 8
   - EXAMPLE_TOOL_API_KEY, added Stage 8
   ```
   If the file does not exist yet, create it with a one-line heading: "# Key list (names only, never values)".
   List every key in the locked drawer (usually `TELEGRAM_BOT_TOKEN`, and `GBRAIN_MCP_TOKEN` after Stage 10). Leave off plain settings that sit there too, such as timeouts, allowed Telegram users or the home channel. Some keys live outside the drawer: the second GBrain key from Stage 10, `claude-code`, sits in Claude Code's own settings file on the box. List those too, by name and where they live, never the value.
4. **Check:** the file exists, lists every key added so far by name only, and contains no value from the locked drawer or any other file a key lives in. Compare the list against each value inside one command that prints only "clean" or "found", never the value. Then wait for the mirror to bring the list to the box.
5. **Report to the member:** "Your Telegram token is in place," or the one-line fix if it was missing, and "Your names-only key list is started, at `_System/KEY_LIST.md` in your brain. It never holds a value, only names."

## Part E: if a key was ever pasted into a chat

If the member says a key was ever typed or pasted straight into any chat, Telegram message or note, even once, before this skill existed or by mistake:

1. Tell them plainly: "A key that was ever typed into a chat has to be treated as seen. Let's replace it, not just hide it."
2. Have them make a new key on that service's own site.
3. Add the new one with Part B.
4. Have them delete the old key on that service's site, so it can no longer be used.
5. **Report:** "Your [service] key is rotated. The old one no longer works anywhere."

## Known fixes

| What you see | Fix |
|---|---|
| `pbpaste \| wc -c` prints 0 | The member has not copied yet, or copied something else. Ask again: "Click copy on the key, then tell me 'copied'." |
| The locked drawer file does not exist yet | `ssh mybox 'mkdir -p ~/.hermes && touch ~/.hermes/.env && chmod 600 ~/.hermes/.env'`, then redo Part B step 4. |
| Two keys glued onto one line in the locked drawer (the file did not end with a line break before step 4) | Split the line by name, never printing it: `ssh mybox "sed -i 's/\(.\)SERVICE_KEY_NAME=/\1\nSERVICE_KEY_NAME=/' ~/.hermes/.env"`, using the new key's name. Then list names only: `ssh mybox "cut -d= -f1 ~/.hermes/.env"` shows each name on its own line. Redo the step 5 check for both keys. |
| The confirm check in Part B step 5 fails | The variable name in step 4 does not match the check in step 5. Use the same name in both, then check again. |
| Any part of a key appears in this chat by accident | Stop immediately. Treat it as pasted: run Part E on that key right away. |
| Hermes says the tool still needs a key after you added it | Check the name with the Part B step 5 check, and that it is the name the tool's own docs use. Then the member asks Hermes again in a new session: "Show my tools table." |
| The Telegram token check in Part D finds no match | The Stage 3 quick setup may use a different variable name. List the variable names actually in the file (names only, never run `cat` on the whole file where a value could show) and match by eye, then redo the check with the real name. |
| Anything else | Read the error, try one fix, tell the member in one plain sentence. Their repair sentence, any time: "Connect to my box and fix Hermes." |

## Jobs

Stage 8 adds no scheduled job. Once Connect to Capture is set up, the Capture bot's nightly capture reads each tool whose key is in place.

## Report back to the member

Plain words, no key values, no file contents, no IP address, no version numbers:

1. "Your Add a Key skill is saved. From now on, just say 'Add a key for...' and I will handle it the same safe way."
2. "Your [service] key is in place." (name only, every time)
3. "Your [tool] key is in place. Now ask Hermes: Show my tools table."
4. "Your Telegram token is in place," or the one-line fix if it was missing.
5. "Your names-only key list is started, at `_System/KEY_LIST.md` in your brain."

If something is still stuck, say exactly which step and what you saw, and suggest: "Record the failing step without secrets and consult your host support documentation."
