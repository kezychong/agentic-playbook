---
name: ap-mac-mini-setup
description: "Turn a spare Mac mini into a headless agent box (never sleeps, logs in by itself, Hermes running) and write the file that connects the laptop. Use for \"set up this Mac mini as my agent box\" or \"connect me to my box\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Mac Mini Setup

**Agent box setup: steps for Claude Code on the Mac mini.**

You are Claude Code, running in the Code tab of the Claude app on the member's Mac mini. The member never opens Terminal and never types a command: you run every command yourself, and anything they must do is a click or a macOS pop-up. The member may have done only the first steps (logged in, installed the Claude app). Step 1 checks the rest and walks them through anything missing. Your job: turn this Mac mini into a headless box that agents run on, with no approval prompts, then hand the member one file to connect their laptop.

## Rules

- Do every step yourself. Stop only where a step says Member:.
- Talk to the member in short, plain sentences. No jargon. One step at a time.
- Never print a password, key, token or full IP address in the chat. Members post screenshots.
- Passwords are only ever typed into a macOS box, never into the chat. To read one, use this inside the same command that uses it, then unset it:
  ```
  osascript -e 'text returned of (display dialog "Your Mac mini password (the one you log in with):" default answer "" with hidden answer buttons {"OK"} default button "OK")'
  ```
- Check each step with the check given. If a check fails, fix it, then check again. Do not move on with a failed check.
- If the member comes back later and says "continue the box setup", run the checks in order and start at the first one that fails.

## Step 0: the safety agreement (do not skip)

Show the member this, word for word:

> This Mac mini is about to become a computer for AI agents only. Agents on it will run commands, click buttons and approve pop-ups without asking you first. That is the point, and it is also the risk: anything on this Mac mini, an agent can read, change or delete. So: no personal Apple ID, no iCloud, no saved passwords, no banking, no personal photos or files on this Mac mini. Keep those on your laptop. The mini stays at home, is only reachable through your private Tailscale network, and you can wipe it any time. Type I understand to continue.

Continue only when the member types "I understand" (any capitalisation). Then check:

- `defaults read MobileMeAccounts Accounts 2>/dev/null | grep -c AccountID` prints 0 or errors (no Apple ID signed in). If an Apple ID is signed in, tell the member: "Please sign out of your Apple ID first: System Settings, click your name at the top, Sign Out. Say done." Wait.

## Step 1: check the member's part

- **Remote Login:** `nc -z -G 2 127.0.0.1 22 && echo ok`. **Screen Sharing:** `nc -z -G 2 127.0.0.1 5900 && echo ok`. If either fails: `open "x-apple.systempreferences:com.apple.Sharing-Settings.extension"` and tell the member which switch to turn on. Wait for done, check again.
- **Tailscale:** `T=/Applications/Tailscale.app/Contents/MacOS/Tailscale; $T status --json | plutil -extract BackendState raw -o - -; $T status --json | plutil -extract Self.DNSName raw -o - -` prints `Running` and a name ending in `.ts.net` (use `plutil`, not `python3`: on a fresh Mac, `python3` opens an install pop-up). If Tailscale is not installed (`test -d /Applications/Tailscale.app` fails): `open https://tailscale.com/download/mac` and tell the member: "Download Tailscale, open it, and sign in (Google or Apple is fine). Use the same account on your laptop later. Say done." If installed but not `Running`: `open -a Tailscale` and ask the member to sign in. Save the name without the trailing dot as `BOXNAME` (keep it for Step 9; do not show it).
- **Who you are:** `id -un` (the mini user; do not print it to the member) and `id -Gn | grep -qw admin && echo admin`. Must be admin. If not, stop and tell the member this account must be an administrator.

## Step 2: admin rights without asking every time

Agents on this box must never stop at a sudo password. One macOS password box, then never again. Tell the member first: "A macOS box will ask for your Mac mini password once. Type it there, not here." Then:

```
osascript -e 'do shell script "echo \"'"$(id -un)"' ALL=(ALL) NOPASSWD: ALL\" > /etc/sudoers.d/agent-box && chmod 440 /etc/sudoers.d/agent-box && visudo -cf /etc/sudoers.d/agent-box" with administrator privileges'
```

**Check:** `sudo -n true && echo ok`.

## Step 3: never sleep, come back after a power cut

```
sudo pmset -a sleep 0 disksleep 0 displaysleep 10 womp 1 autorestart 1 powernap 0; sudo systemsetup -setrestartfreeze on >/dev/null 2>&1; pmset -g | grep -E "^ *(sleep|disksleep|autorestart|womp) "
```

**Check:** sleep 0, disksleep 0, autorestart 1, womp 1.

## Step 4: log in by itself after a restart

Agents and Hermes only run while the account is logged in. Run `fdesetup status`.

- **If FileVault is Off:** tell the member "One more password box." Read the password with the hidden box and run `printf '%s\n' "$PW" | sudo sysadminctl -autologin set -userName "$(id -un)" -password -; unset PW`.
- **If FileVault is On:** ask the member, with two choices: "FileVault is on. It protects files if someone steals the mini, but after a power cut the mini waits at a password screen and your agents stay off until you type it. For an agent box that stays at home, turning it off is normal. Which do you want?" **Turn FileVault off (recommended)** / **Keep it on**.
  - **Turn off:** read the password with the hidden box, `printf '%s\n' "$PW" | sudo fdesetup disable -user "$(id -un)" -password -` (or `sudo fdesetup disable` with the password on input if that form is refused), then the autologin line from "If FileVault is Off" above, then `unset PW`. Turning off finishes in the background.
  - **Keep on:** change nothing. Tell the member: "After a power cut, open Screen Sharing from your laptop and type your password once." For restarts you start yourself, always use `sudo fdesetup authrestart -delayminutes 0`.

**Check (FileVault off):** `sudo defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser` prints the user (do not show it) and `sudo test -f /etc/kcpassword && echo ok`.

## Step 5: give agents hands (the switches only a person can flip)

Apple lets no program flip these. The member clicks them once, now, while the screen is plugged in. Open each page in turn and wait for "done" before the next:

- **Accessibility** (agents can click and type): `open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"`
- **Screen & System Audio Recording** (agents can see the screen): `open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"`
- **Full Disk Access** (agents can read every folder): `open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`
- **Automation** is asked for app by app the first time an agent controls an app; tell the member to click OK or Allow when those appear during this setup.

For each page tell the member: "Turn on Claude. If it isn't in the list, click +, open Applications, pick Claude. If macOS asks to quit Claude, click Later, then come back." Also turn on Hermes and Codex if they appear in the list later.

**Check:**

- Screen: `screencapture -x /tmp/agentbox-shot.png && sips -g pixelWidth /tmp/agentbox-shot.png | tail -1; rm -f /tmp/agentbox-shot.png`: a width shows, and the picture is not just the desktop wallpaper (if the width is under 1280, note it for Step 8).
- Clicks: `osascript -e 'tell application "System Events" to get name of first process whose frontmost is true'` prints an app name (approve the Automation pop-up if it appears).
- Disk: `ls ~/Library/Mail >/dev/null 2>&1 && echo ok`.

## Step 6: Homebrew and basic tools

- If `command -v brew` finds nothing: `NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`, then add `eval "$(/opt/homebrew/bin/brew shellenv)"` to `~/.zprofile` and run it.
- `brew install tmux git ffmpeg yt-dlp python@3.12 syncthing`.

**Check:** `brew --version && tmux -V && ffmpeg -version | head -1`.

## Step 7: Hermes, with no approval prompts

1. **Install the latest Hermes** (docs: https://hermes-agent.nousresearch.com/docs/getting-started/installation): `curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/hermes-install.sh && bash /tmp/hermes-install.sh --non-interactive`. Do not run `hermes setup`, and never pick Anthropic in a Hermes wizard (that costs extra, outside the member's Claude plan).
2. **Claude plan plugin:** `hermes plugins install claude-subscription-directsdk && hermes plugins enable claude-subscription-directsdk-experimental`. Point Hermes at it (`hermes model`, pick Claude Subscription DirectSDK (Experimental) and the strongest Claude model listed). Never set `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_BASE_URL`.
3. **No approval prompts:** this box is for agents. Run these four, exactly:
   ```
   hermes config set approvals.mode off && hermes config set approvals.cron_mode approve && hermes config set approvals.single_query_mode approve && hermes config set approvals.unattended_mode approve
   ```
   **Check:** `hermes config get approvals.mode` prints `off`. (`off` is the same as running Hermes with `--yolo`; the other three stop scheduled jobs, one-shot `hermes -z` runs and webhooks from refusing risky commands when nobody is there to say yes.) Tell the member in one line: "Hermes on this mini will not stop to ask before running commands. That is what this box is for."
4. **Start Hermes as a service** that comes back after restarts: `hermes gateway install && hermes gateway start`. **Check:** `hermes --version`, `hermes doctor` shows no provider or plugin error, `hermes gateway status` shows it running, and `hermes -z "Say hello in one short sentence."` answers. Show the member the reply.

## Step 8: Codex in full-access mode (if the member uses ChatGPT)

Ask: "Do you also use ChatGPT? If yes, I'll set up Codex too." On no, skip to the screen note at the end of this step.

1. `brew install --cask codex 2>/dev/null || brew install codex`.
2. Write `~/.codex/config.toml` (merge if it exists):
   ```
   approval_policy = "never"
   sandbox_mode = "danger-full-access"
   ```
3. Sign in: run `codex login` in tmux, open the link it prints, and let the member sign in. **Check:** `codex exec "print the word pong"` answers without asking for approval.

**Screen note.** If Step 5's screen width was under 1280 or no screen will stay plugged in: tell the member "When the screen is unplugged, some Mac minis shrink the screen to a tiny size and agents can't click well. A small HDMI 'dummy plug' (about $10 online) fixes it. Keep the screen plugged in until it arrives, or skip it if your agents don't click on screen."

## Step 9: the file that connects the laptop

Write `~/Desktop/connect-to-my-box.md` with exactly this, filling in the two values (BOXNAME from Step 1, the user from `id -un`):

````markdown
# Connect this laptop to my box

You are Claude Code (the Code tab of the Claude app) on the member's laptop. The member never opens Terminal or types a command; you run everything. Their agent box is a Mac mini on their Tailscale network.
- Box name: <BOXNAME>
- Box user: <USER>

1. Check Tailscale on this laptop: `/Applications/Tailscale.app/Contents/MacOS/Tailscale status` lists the box name. If not, ask the member to open the Tailscale app and sign in to the same account as the mini.
2. Make a key if none exists: `test -f ~/.ssh/mybox_ed25519 || ssh-keygen -t ed25519 -N "" -f ~/.ssh/mybox_ed25519 -C mybox`.
3. Add to ~/.ssh/config (once):
   Host mybox
     HostName <BOXNAME>
     User <USER>
     IdentityFile ~/.ssh/mybox_ed25519
     IdentitiesOnly yes
     ServerAliveInterval 30
4. Copy the key to the box. The member types the Mac mini password once, in a macOS password box, never in this chat and never in Terminal:
   Write a tiny helper that shows the box: `printf '#!/bin/sh\nosascript -e %s\n' "'text returned of (display dialog \"Your Mac mini password (the one you log in with):\" default answer \"\" with hidden answer buttons {\"OK\"} default button \"OK\")'" > ~/.ssh/mybox-askpass && chmod 700 ~/.ssh/mybox-askpass`
   Tell the member: "A box will pop up asking for your Mac mini password. Type it there and click OK." Then run:
   `SSH_ASKPASS=~/.ssh/mybox-askpass SSH_ASKPASS_REQUIRE=force ssh-copy-id -i ~/.ssh/mybox_ed25519.pub -o StrictHostKeyChecking=accept-new mybox </dev/null; rm -f ~/.ssh/mybox-askpass`
5. Check: `ssh -o BatchMode=yes mybox 'hostname && hermes gateway status'` works with no password.
6. Remember it: add a line to ~/.claude/CLAUDE.md: "My box is my Mac mini: ssh mybox."
7. Restart test: `ssh mybox 'sudo shutdown -r now'` (or `sudo fdesetup authrestart -delayminutes 0` if FileVault is on). Wait 2 minutes, then repeat the check in 5 until it works (up to 5 minutes).
8. Tell the member: "Your laptop now reaches your box from anywhere. Unplug the Mac mini's screen, keyboard and mouse. Keep it on power and internet. Say done." Then run the check in 5 one last time.
9. Tell the member: "Done. From now on every pack is the same for you: wherever it says 'my box', that's your Mac mini."
````

Then tell the member: "Last step. On your Mac mini's Desktop there's a file called connect-to-my-box.md. Right-click it, Share, AirDrop, and send it to your laptop. On your laptop, open the Claude app, click the Code tab, drag the file in from Downloads, and type: Connect me to my box." (No AirDrop? Email it to yourself, or put it in iCloud Drive on the laptop.)

## Report to the member

Short, plain: what's on (never sleeps, logs in by itself, agents can see and click, Hermes running with no approvals, Codex if chosen), and the one thing left (AirDrop the file to the laptop). Remind them: nothing personal on this Mac mini, ever.
