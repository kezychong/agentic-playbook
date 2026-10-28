---
name: ap-brain-folder-setup
description: "Mirror the brain folder between laptop and box with Syncthing and point Hermes at it. Use for \"run the brain folder setup pack\", \"open my brain folder\" or \"fix Hermes\" after the box exists."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. It is the recipe Claude Code follows to put your brain folder on your server and keep both copies matching. Drag it into Claude Code and type: Connect to my box and run the brain folder setup pack (ap-brain-folder-setup).

# Brain Folder Setup: mirror the brain folder and point Hermes at it

**If you are Hermes on the server, stop here.** This pack is for Claude Code on the member's laptop, and it already ran. The member wants their brain built. If `ap-brain-installer.md` is in the brain folder (or in `_System/packs/`), read it and follow it now. If it is not there, tell the member in one line: "This file is the mirror pack for Claude Code. For me, drag ap-brain-installer.md onto your brain folder and say: Read ap-brain-installer.md in my brain folder and build my brain." Do nothing else with this file.

**For Claude Code.** The member dragged this file into your chat. Read all of it, then run it from their one sentence without stopping, except where it says the member acts. You do this job, not Hermes, because it works on both machines, answers the macOS boxes on the laptop, and restarts Hermes. From Stage 4 on, the member talks to Hermes for everything else; you stay their mechanic.

## The member's sentences

| The member says | You do |
|---|---|
| Connect to my box and run the brain folder setup pack (ap-brain-folder-setup). | Everything below, then report |
| Open my brain folder in Finder. | Open it, then hand back the pin steps |
| Connect to my box and fix Hermes. | Later fixes, then `hermes doctor` |

## Goal

1. The brain folder the member made in their home folder on Stage 1 (any name) is found and used. Never make a second one.
2. The same folder lives on the box at `/home/hermes/second-brain`, whatever the laptop name, kept matching both ways by Syncthing with staggered versioning on both ends.
3. Syncthing comes back by itself after a stop, a Hermes restart and a server restart.
4. Every new Claude Code chat knows where "my brain folder" is.
5. Hermes works from `/home/hermes/second-brain`, so it reads the brain's AGENTS.md there.
6. This pack is saved as a Claude Code skill, so the Later fixes are there when the member says "Connect to my box and fix Hermes."

## Rules and names

- The box is **my box** from Stage 2 (`ssh mybox`, user `hermes`, passwordless sudo). If anything from Stage 2 is missing, run the missing parts of the rented-server setup pack (ap-hermes-server-setup) first.
- Say in one short line what each step does before you run it. Use the member's chosen permission mode; never switch it for them.
- The member never types a command and never downloads a tool. If the Syncthing app is missing, you install it. If the Mac ever asks for their own password, they type it into the box that asks, never into the chat.
- Never print a secret: no Syncthing API key, no device ID, no IP address in the chat.
- Report in plain words, no paths, no version numbers. If stuck, say which step and what you saw, then: "Record the failing step without secrets and consult your host support documentation."

## If my box is a Mac mini

First check: `ssh mybox uname`. `Linux` means a rented server: follow What to do exactly as written. `Darwin` means the member's Mac mini (set up with the Mac mini setup pack (ap-mac-mini-setup)): follow What to do with these changes:

- **The box user is the member's own Mac account**, not `hermes`, and there is no `mybox-root`. The box brain path is `/Users/<user>/second-brain`: read it once with `BOX_BRAIN=$(ssh mybox 'echo "$HOME/second-brain"')` in the same command that needs it. Use it wherever this pack says `/home/hermes/second-brain` (steps 2, 3, 6 and 8, and Done looks like). Never print the user name in the chat.
- **Step 4, Syncthing on the mini:** no apt and no systemd. Install it with Homebrew and run it as a background service that starts at boot, before anyone logs in: `ssh mybox 'brew install syncthing && sudo brew services start --sudo-service-user "$(id -un)" syncthing'`. **Check:** `ssh mybox 'sleep 5; sudo launchctl list | grep -c homebrew.mxcl.syncthing; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8384/'` prints `1` and 200 or 401. Homebrew's service keeps Syncthing alive if it stops. (If `--sudo-service-user` is refused, use `brew services start syncthing` instead: it then starts when the account logs in, which automatic login does after every restart.) Skip the `ufw` line: the mini has no `ufw`.
- **Step 6, the mini's API key** sits in `~/Library/Application Support/Syncthing/config.xml` on the mini (the same place as on the laptop); read it there with `ssh mybox`, never print it. The address in `tcp://<IP>:22000` is the mini's Tailscale address from `Host mybox`.
- **Step 7, survives restarts:** `ssh mybox 'sudo pkill -x syncthing; sleep 15; pgrep -x syncthing >/dev/null && echo active'` prints `active`; then `ssh mybox 'hermes gateway restart; sleep 5; pgrep -x syncthing >/dev/null && echo active; hermes gateway status'`. The optional full restart is `ssh mybox 'sudo shutdown -r now'` (or `sudo fdesetup authrestart -delayminutes 0` if `~/.claude/CLAUDE.md` says FileVault is on).
- **Step 8:** `hermes config set terminal.cwd "$BOX_BRAIN"`, with `BOX_BRAIN` set in the same command (or written as `$HOME/second-brain` inside the `ssh mybox '…'` quotes, which the mini expands).
- **Done looks like:** Syncthing's service is listed and came back after the stop test; everything else is the same.

## What to do

1. **Save this pack as a skill**: copy the dropped file (usually `~/Downloads/ap-brain-folder-setup.md`) into `~/.claude/skills/ap-brain-folder-setup/SKILL.md`, keeping this file's frontmatter, after the member approves. Copy it with the shell; never retype it.
2. **Find the brain folder**. It sits directly in the home folder and is not a Mac standard folder (Desktop, Documents, Downloads, Library, Movies, Music, Pictures, Public, Applications). The folder this chat is open in is the first guess. One candidate: confirm by name. Several: ask which one they made on Stage 1. On the Desktop, in Documents, iCloud or Dropbox: say why the brain lives in the home folder (those places have a courier of their own, and two couriers make duplicates), ask, and move it on yes. Leave whatever is already inside. Set `BRAIN` to its full path and look inside: `ls -A "$BRAIN"; du -sh "$BRAIN"`. Anything in it copies to the box as well; if it holds more than about 1 GB, say so and ask before you go on. Then make the box side: `ssh mybox 'mkdir -p ~/second-brain'`.
3. **Write the "My brain folder" line** into `~/.claude/CLAUDE.md`, under the Stage 2 my box line, exactly once: `"My brain folder" is \`<laptop path>\` on the laptop and \`/home/hermes/second-brain\` on my box, kept matching by Syncthing.` Every later pack reads the laptop path from it.
4. **Syncthing on the box**, from Syncthing's own apt repository, then as its own service that comes back after any stop:
   ```
   ssh mybox 'sudo mkdir -p /etc/apt/keyrings && sudo curl -fsSL -o /etc/apt/keyrings/syncthing-archive-keyring.gpg https://syncthing.net/release-key.gpg && echo "deb [signed-by=/etc/apt/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable-v2" | sudo tee /etc/apt/sources.list.d/syncthing.list && sudo apt-get update && sudo apt-get -y install syncthing'
   ssh mybox 'sudo mkdir -p /etc/systemd/system/syncthing@hermes.service.d && printf "[Service]\nRestart=always\nRestartSec=10\n" | sudo tee /etc/systemd/system/syncthing@hermes.service.d/override.conf && sudo systemctl daemon-reload && sudo systemctl enable --now syncthing@hermes'
   ```
   **Check:** `ssh mybox 'sleep 5; systemctl is-active syncthing@hermes; systemctl is-enabled syncthing@hermes'` prints `active` and `enabled`. If `ssh mybox 'sudo ufw status | head -1'` says active, `ssh mybox 'sudo ufw allow 22000'`.
5. **The Syncthing app on the Mac**. It carries Syncthing inside it, so no other tool is needed:
   ```
   url=$(curl -fsSL https://api.github.com/repos/syncthing/syncthing-macos/releases/latest | grep -o '"browser_download_url": *"[^"]*\.dmg"' | head -1 | sed 's/.*"\(https[^"]*\)"/\1/')
   curl -fL -o /tmp/Syncthing.dmg "$url"
   hdiutil attach -nobrowse -quiet -mountpoint /tmp/syncthing-dmg /tmp/Syncthing.dmg
   cp -R /tmp/syncthing-dmg/Syncthing.app /Applications/
   hdiutil detach -quiet /tmp/syncthing-dmg && rm /tmp/Syncthing.dmg
   ```
   If `/Applications` refuses the copy, use `~/Applications` (make the folder first). Before you open it, tell the member: "Your Mac will show two boxes. One asks if claude may control System Events: click Allow. The other asks to let Syncthing find devices on local networks: click Allow." Then `open -a Syncthing`, and make it start at login (this raises the System Events box):
   `osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Applications/Syncthing.app", hidden:true}'`
   **Check:** `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8384/` prints 200 or 401, not an error.
6. **Pair and share** through each side's REST API. The API key sits in each side's `config.xml` (Mac: `~/Library/Application Support/Syncthing/config.xml`; box: `~/.local/state/syncthing/config.xml`, or `~/.config/syncthing/config.xml` on older layouts); read it inside one command and never print it. Device IDs:
   ```
   MAC_ID=$(k=$(sed -n 's:.*<apikey>\(.*\)</apikey>.*:\1:p' ~/Library/Application\ Support/Syncthing/config.xml); curl -s -H "X-API-Key: $k" http://127.0.0.1:8384/rest/system/status | grep -o '"myID": *"[^"]*"' | sed 's/.*"\([A-Z0-9-]*\)"$/\1/')
   BOX_ID=$(ssh mybox 'f=$(ls ~/.local/state/syncthing/config.xml ~/.config/syncthing/config.xml 2>/dev/null | head -1); k=$(sed -n "s:.*<apikey>\(.*\)</apikey>.*:\1:p" "$f"); curl -s -H "X-API-Key: $k" http://127.0.0.1:8384/rest/system/status' | grep -o '"myID": *"[^"]*"' | sed 's/.*"\([A-Z0-9-]*\)"$/\1/')
   ```
   Then `POST /rest/config/devices` on each side: on the Mac add `BOX_ID` named `my box` with addresses `tcp://<IP>:22000` and `dynamic` (the IP from `Host mybox` in `~/.ssh/config`); on the box add `MAC_ID` named `laptop` with address `dynamic`. Then `POST /rest/config/folders` on both sides: folder ID `second-brain`, label the laptop folder's own name (`basename "$BRAIN"`), both device IDs, `"versioning": {"type": "staggered"}`; Mac path `"$BRAIN"`, box path `/home/hermes/second-brain`. Build the JSON with the path as a proper JSON string, so spaces and apostrophes are safe.
   **Check:** after a minute, `GET /rest/system/connections` shows `"connected": true` on both sides, versioning is `staggered` on both, and `GET /rest/db/status?folder=second-brain` says `"state": "idle"`.
7. **Survives restarts**:
   `ssh mybox 'sudo systemctl kill syncthing@hermes; sleep 15; systemctl is-active syncthing@hermes'` prints `active`, then
   `ssh mybox 'systemctl is-enabled syncthing@hermes; hermes gateway restart; sleep 5; systemctl is-active syncthing@hermes; hermes gateway status'` prints `enabled`, `active` and the messaging service running. Offer the full server reboot (`ssh mybox-root reboot`) only as optional, and only on a yes.
8. **Point Hermes at the folder**:
   `ssh mybox 'cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-brain-folder && hermes config set terminal.cwd /home/hermes/second-brain && hermes gateway restart; pkill -f "serve [-]-isolated"'`
   The desktop app's own server reads the config once at start; the `pkill` stops it and the app starts it again within seconds. **Check:** `ssh mybox 'grep -A4 "^terminal:" ~/.hermes/config.yaml'` shows `cwd: /home/hermes/second-brain`, and `hermes gateway status` shows it running (Telegram can time out on its first try after a restart; wait a minute before calling it a failure).
9. **Silent two-way check**: write one small file on each side, wait for it on the other (Syncthing waits about 10 seconds before it sends; give it two minutes), compare checksums, then delete both files and their copies in `.stversions` on both sides. Say nothing about it unless it fails.
10. **Report:** "Your brain folder from Stage 1, <name>, is now on both machines, and Syncthing keeps them matching, with versioning on. It comes back after restarts, Hermes now works from it, and every new chat knows where it is."

When the member says "Open my brain folder in Finder.": `open` the laptop path, then hand back one step at a time: "Press Cmd and the up arrow: now you see it in your home folder. Drag it into the sidebar, under Favorites." Then: "You never need to open it in Claude Code again: you have worked in it since Stage 1." Only if this chat is not in the brain folder: tell them to start a new chat, click the folder button, Open folder, and pick it.

## Done looks like

- `systemctl is-active` and `is-enabled` say active and enabled for `syncthing@hermes`, and it came back after the kill test.
- Both sides report each other connected, versioning staggered, folder idle.
- `grep -c '"My brain folder"' ~/.claude/CLAUDE.md` prints 1 with the right laptop path.
- `hermes config get terminal.cwd` (or the config file) shows `/home/hermes/second-brain`, the gateway is running, and the app's server was restarted.
- The two check files arrived both ways and are gone again.

## Traps (each one cost a run)

- The laptop name may hold spaces or an apostrophe: always write `"$BRAIN"` in quotes, and set `BRAIN=` again at the start of each command, since shell variables do not carry over between your commands.
- The box copy is always `/home/hermes/second-brain`. Never make a second brain folder on either side.
- A memory saved from this chat stays with this chat's folder only, which is why the line goes into `~/.claude/CLAUDE.md`.
- Desktop, iCloud and Dropbox folders already have a courier; two couriers on one folder make odd duplicates.
- Syncthing on the box must be its own service with `Restart=always`: otherwise Syncthing can stop after a Hermes restart.
- Two macOS boxes appear (System Events, local network).
- Hermes reads AGENTS.md only from its working folder; a fresh box has `.` there.
- `hermes gateway restart` never touches the desktop app's own `hermes serve --isolated` server, which reads its config once at start. Always add the `pkill`, written as `pkill -f "serve [-]-isolated"` so it does not kill its own shell.
- Never name Homebrew to the member: the app comes straight from the Syncthing release.

## Later fixes (for "Connect to my box and fix Hermes.")

- **The app does not see a change** (a new skill, a new working folder): `ssh mybox 'hermes gateway restart; pkill -f "serve [-]-isolated"'`, then the member clicks New session.
- **A red card in the Hermes app, "The AI service returned an error", and the box log says "Native returned a tool outside the current host inventory"**: a known open bug in the Claude subscription plugin. If the installed plugin lacks the fix, back up the file, apply it as a local patch, test that full tool names pass, a short name of a real Hermes tool passes and an unknown name is still refused, restart both servers, and check `hermes -z "Reply with the one word pong."` answers.
- **Night jobs or Hermes stop about 30 days after Stage 2**: the Claude login on the box expired. Run Part G of the rented-server setup pack (ap-hermes-server-setup): one link, one click.
- **Hermes cannot see the brain folder**: check both Syncthing sides are connected and `terminal.cwd` is set, then restart both servers.
- **Anything else**: read the error, try one fix, tell the member in one plain sentence, then run `hermes doctor`.
