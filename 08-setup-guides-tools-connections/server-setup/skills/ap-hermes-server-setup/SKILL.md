---
name: ap-hermes-server-setup
description: "Rent a Hostinger VPS with plain Ubuntu, set up key-only SSH as `my box`, install Hermes, Claude Code and the Claude subscription plugin, and get Hermes's first hello. Use for \"set up my server and Hermes\" or \"finish the rented-server setup pack\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. It is the recipe Claude Code follows to set up your server and Hermes. Drag it into Claude Code and type: Use this rented-server setup pack to set up my server and Hermes. Use my Chrome, and only stop when you need me.
>
> **Using a Mac mini instead?** Use ap-mac-mini-setup in this package instead.

# Hermes Server Setup: rent your server, Claude Code moves in, Hermes says hello

**If you are Hermes on the member's box, stop here.** This pack is for Claude Code on the member's laptop, because it sets up the server you run on. Tell the member in one line: "This one is for Claude Code on your laptop: add it to a Claude Code chat and say: Connect to my box and finish the rented-server setup pack (ap-hermes-server-setup)." Do nothing else with this file.

**For Claude Code.** The member took this file from the Server Setup package and dragged it into your chat. Read all of it now. The member says one sentence. From it you run the whole setup, part after part, and stop only when you need the member (see The run, in order). After every part, tell the member in one or two plain lines what just happened and exactly what to do or say next. The member should never have to guess the next step.

**If a step behaves differently** from this pack: stop, tell the member in one plain sentence what you saw, try the known fix, and report what you changed.

## Goal

By the end of today the member has:

1. This pack installed as a Claude Code skill, so any new chat can pick up where they left off.
2. A rented Hostinger server with plain Ubuntu, reached with your own SSH key, saved under the name **my box**, with password login turned off. You set up the SSH key yourself, in Hostinger, with the browser.
3. On that server: the latest Hermes, Claude Code, and the Claude subscription plugin, all under one normal user named `hermes`.
4. Claude Code on the server logged in to the member's Claude Max plan (one login link the member approves).
5. Hermes set to the Claude subscription plugin, with the strongest Claude model on the plan as its default, and Hermes's first hello shown to the member.

**Names.** Some guides call the plugin "the Claude SDK plugin". It is the same thing: the Claude subscription plugin for Hermes, `claude-subscription-directsdk`, which runs Hermes on the member's Claude plan through Claude Code.

## Who does what

- **You (Claude Code on the member's Mac)** do every step on the laptop, in the browser, and on the server. The member never types a command.
- **The member** rents the server in Hostinger (following Part B), adds the Claude extension to Chrome if it is missing (Part A), signs in to Hostinger only if the browser is not signed in already, clicks **Always allow** if the browser's site card appears in Part D, clicks Authorize on claude.ai, copies one code and types "copied", and checks their usage meter on claude.ai.
- Use the member's chosen permission mode; never switch it for them. Say in one short line what each step does as you go.
- Report in plain words. No jargon without a one-line explanation. Never print a secret: no password, key, token or one-time code ever appears in the chat or in a file you show. Keep the server's IP address out of the chat too: members often share screenshots.
- The member's brain folder and its rulebook, `AGENTS.md`, arrive on Stage 4. If a brain folder with an `AGENTS.md` already exists on this Mac, read that `AGENTS.md` first and follow it.

## The member's sentences, word for word

| Part | The member says | You run |
|---|---|---|
| 4 | Use this rented-server setup pack to set up my server and Hermes. Use my Chrome, and only stop when you need me. | The whole run below, Parts A to H |
| 4 | Use this rented-server setup pack to set up my server and Hermes. Use my Chrome. The Hostinger page is already open. (a common variant) | The same: the whole run below, Parts A to H |
| 4 | done | Carry on after the member signs in, rents, or clicks what you asked |
| 4 | copied | Part G, step 4 |
| any | Connect to my box and finish the rented-server setup pack (ap-hermes-server-setup). | Check what exists, then run only the missing parts |
| any | Connect to my box and fix Hermes. | Known fixes, then `hermes doctor` |
| later | Switch Hermes to the lighter model until my reset. | Part I |

## The run, in order

When the member sends the sentence, run these parts one after the other. Do not wait for another sentence between parts:

1. **Part A:** save this pack as a skill, check your browser tool, say the three-line plan.
2. **Part C:** make the key.
3. **Part D:** open Hostinger in the browser, add the key, copy the address. If the member has no server yet, run Part B first, then come back.
4. **Part E:** walk in, save my box, turn password login off.
5. **Part F:** install Hermes, Claude Code on the box and the plugin.
6. **Part G:** the Claude Max login.
7. **Part H:** point Hermes at the plugin and get its first hello. Then Report back.

**Stop only for these moments.** Each time, say in one plain line exactly what the member should do, and wait for "done" (or "copied"):

- Add the Claude extension to Chrome, only if it is not there yet (Part A, step 2).
- Sign in to Hostinger, only if the browser is not signed in already, and any verification code, CAPTCHA or "Always allow" card that comes with it.
- Rent the server, only if they have none yet (Part B).
- A yes before you save the key, only if your browser tool asks for one.
- On claude.ai: check the account, click Authorize, click Copy code, type copied.

Everything else you do yourself, with one short line on what each step does. If the member has to leave part way, tell them the sentence that continues later: "Connect to my box and finish the rented-server setup pack (ap-hermes-server-setup)."

**Coming back later.** If the member says "Connect to my box and finish the rented-server setup pack (ap-hermes-server-setup)", check what already exists, in this order, and start from the first thing missing: the key file `~/.ssh/mybox_ed25519`, `ssh mybox true`, `hermes --version`, `claude --version`, `claude auth status`, the plugin list (`hermes plugins list`), the model setting. If the key exists but `ssh mybox true` fails, the key was probably never saved in Hostinger: run Part D.

## Part A: install this pack (start of the run)

1. **Save this pack as a skill,** so a new chat in any folder can find it. Find the file the member dragged in (usually `~/Downloads/ap-hermes-server-setup.md`; if none is there, `mdfind -name ap-hermes-server-setup` and pick the newest). Make the folder `~/.claude/skills/day-2-setup-pack/` and build `SKILL.md` with one shell command: `printf` the frontmatter below, then append the pack from the line "# rented-server setup pack" to the end with `sed -n '/^# rented-server setup pack/,$p' <file>`. Never retype the pack yourself: copy it with the shell.
   ```
   ---
   name: ap-hermes-server-setup
   description: Rent the member's Hostinger server, set up its SSH key in Hostinger with the browser, install Hermes, Claude Code and the Claude subscription plugin, log in to the member's Claude Max plan, and get Hermes's first hello. Use when the member mentions the rented-server setup pack (ap-hermes-server-setup), my box, setting up SSH or Hermes on their server, or says copied during the Claude login.
   ---
   ```
   If `~/.claude/skills/ap-hermes-server-setup/SKILL.md` already exists, replace it with this version and say so in one line.
   **Check:** `head -3 ~/.claude/skills/ap-hermes-server-setup/SKILL.md` shows the `---` line and `name: ap-hermes-server-setup`, and `grep -c "^## Part" ~/.claude/skills/ap-hermes-server-setup/SKILL.md` counts the same parts as the dropped file. No reload needed in this chat: the pack is already in it. New chats find the skill on their own. The skill works in local chats in the Code tab of the Claude app, not in Cowork.
2. **Check your browser.** Part D needs you to open web pages and click in them. The member's sentence says Use my Chrome: that is the member asking for Claude in Chrome, so use it even though the Claude app offers its own browser first. If its tools are not loaded yet, load them (search your tools for claude-in-chrome). **Why Chrome:** the member usually rented the server in Chrome, so Hostinger is usually signed in there already, and nobody signs in twice. Second choice: the Claude app's own built-in browser, which starts with no saved logins, so the member signs in to Hostinger once more. Computer use does not count: it can only look at a browser, never click in it. Do not open any Hostinger page yet.
   - **Claude in Chrome is not connected?** Tell the member in one line: "I work in your Chrome, where you are already signed in to Hostinger. Please add the Claude extension: click Add to Chrome, then sign in with this same Claude account, and say done." Open the page for them: `open -a "Google Chrome" "https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn"`. After done, check again. If it still does not show, ask the member to quit and reopen Chrome, then check once more. If this chat still cannot see it, tell the member in one line to open a new chat and say: Connect to my box and finish the rented-server setup pack (ap-hermes-server-setup). (a chat that is already open may not see the extension until a new chat starts)
   - **The member would rather not add it,** or it will not connect: use the built-in browser, and tell the member they will sign in to Hostinger there once.
   - **No browser tool at all:** say so in one line now and tell the member that in Part D you will guide their clicks instead. It still works.
3. **Tell the member, in these three short lines:**
   - "The rented-server pack is installed as a skill."
   - "Now I set up your server and Hermes, start to finish, and tell you what each step does."
   - "I stop only when I need you, for example to click Authorize on claude.ai."

   Then go straight on to Part C.

## Part B: the member rents the server (the member's job)

The member usually rents the server first, with the choices below, before sending the sentence. If Part D step 3 finds no new server in their account, stop and say: "You have no server yet. Rent it now in your normal browser with the choices below, and say done when hPanel shows it as Running." Then wait. If the member asks, or pastes a screenshot of a Hostinger screen, help with these choices:

- Page: **hostinger.com/vps-hosting**, the direct route. Not Hostinger's Hermes page: that one installs an app template on the server.
- Plan: **KVM 2** (8 GB of memory). Period: **1 month** is fine to start.
- If a "Ready to use AI" add-on or any credit bundle is ticked, untick it. The member's Claude Max plan runs Hermes.
- Location: the one nearest the member.
- Operating system: in the cart, under **Choose what to install**, the **Plain OS** tab, then **Ubuntu**, the newest version. Not a control panel or an application (Hermes, Docker and the like).
- Root password: click **Generate** and save it in the Passwords app (or 1Password) as "Hostinger server". It is the spare key for emergencies; you never need it.
- After payment, **Secure your VPS access**: leave **Add SSH key** empty (you add the key in Part D), then **Next**.
- **Additional features**: leave **Monarx malware scanner** and **Docker manager** unticked, then **Finish setup**. Both can be added later; the server stays plain.
- Offers after payment: **No, thanks**.
- Setup takes a few minutes. Hostinger says up to 10 minutes. The waiting screen is normal.

Never ask the member for the root password, their Hostinger password or card details, and never type them.

## Part C: make the key

Tell the member in one line: "First I make a key for your server: think of it as a house key that only this Mac holds."

1. Make a key pair only for this server, with no passphrase, so you can use it without a prompt:
   `ssh-keygen -t ed25519 -f ~/.ssh/mybox_ed25519 -N "" -C "mybox"`
   If `~/.ssh/mybox_ed25519` already exists, do not overwrite it. Ask the member whether this is a second server.
2. **Check:** `cut -c1-11 ~/.ssh/mybox_ed25519.pub` prints `ssh-ed25519`. The `.pub` file is the public half: it goes into Hostinger and is not a secret. The other file never leaves this Mac.
3. Put the public half on the clipboard too, as a fallback: `pbcopy < ~/.ssh/mybox_ed25519.pub`

## Part D: add the key in Hostinger with the browser

This is where the member sees browser use: you open a web page and click buttons, the way a person would. Before each click, say in one short line what you are clicking and why, so the member can follow on screen.

**Rules for the browser:**

- Never type a password, card number or one-time code. Sign-ins, payments and verification codes are the member's. When a page asks for one, hand the browser to the member and wait.
- Never solve a CAPTCHA or a "prove you are human" check. Ask the member to do it.
- Touch only the new server. If the account has more than one server, ask the member which one is new before you click anything on it. Never rebuild, reset, stop or delete any server, and never change its operating system or root password.
- Never buy anything, never accept an offer, never click an upgrade or add-on.
- If a card asks to let Claude act on a Hostinger page (Allow once, Always allow, Deny, in the app or in Chrome), tell the member: click **Always allow**. This is the browser's own safety check and it can appear even in Bypass permissions.
- Your browser tool has its own rules, separate from Bypass permissions: saving a form or changing account settings can need the member's yes in the chat first. When it does, ask once, in one line, and wait for yes (Part D, step 5).
- Add the key only on the hPanel SSH keys page, never through the Hostinger API or a Hostinger MCP: a key attached by the API can fail to reach the running server.
- Hostinger changes its screens. If a page looks different from these steps, follow what the screen says, and tell the member in one line what you saw.

**Steps:**

1. Tell the member: "Now I open Hostinger in the browser. Watch. I do the clicking." Open https://hpanel.hostinger.com/ in your browser tool.
2. If Hostinger shows a sign-in page, stop and say: "Please sign in to Hostinger in this browser window. I never type your password. Say done when you see your Hostinger home page." Wait for "done". (Claude in Chrome uses Chrome's existing logins, so a member who rented the server in Chrome is usually signed in already and this step is skipped. The Claude app's own browser starts with no saved logins, so there the member signs in to Hostinger, including Continue with Google if that is how they signed up. Google may refuse Continue with Google inside the app's own browser: see Known fixes.)
3. Open the VPS list: go to https://hpanel.hostinger.com/vps, or find VPS under **More services**, or click the new server's card on hPanel home. (hPanel home has no VPS item in its left menu.) If a short survey pops up, click **Skip**. On the new server's row click **Manage**. **Check before you continue:** judge the OS by the name at the top of **Overview**: it should read Ubuntu and Running. **Docker Manager** in the server's menu is normal on plain Ubuntu and is not a template. If the list has no server at all, the member has not rented one yet: run Part B, then come back here. If it still shows a setup form or "Set up", tell the member setup is not finished and wait. If it shows an app template (for example a "Hermes Agent configuration" form with a Deploy button, or "Docker and Traefik" as the OS), stop: see Known fixes, "Server runs a template".
4. Open the server's **Settings**, then **SSH keys**. Click **+ SSH key** (it may say **Add SSH key**). A shortcut sits at the bottom of **Overview**: the **SSH key** card, **Manage**. Ignore the **Hermes Agent** and **OpenClaw** items in hPanel's left bar and the **Agent** button at the top: they are Hostinger's own installs and chat, not the Hermes you install here.
5. The **Add SSH Key** box has one field, **SSH key content**. Click inside it and enter the whole contents of `~/.ssh/mybox_ed25519.pub`, exactly, on one line (it starts with `ssh-ed25519` and ends with `mybox`). There is no name box: Hostinger names the key from its last word, so it shows as `mybox`. The **Save** button stays grey until the box is filled. If your browser rules need the member's yes before you click Save, ask once, in one line: "I am about to save your server's key in Hostinger. Say yes to go ahead." Wait for yes. Click **Save**.
6. **Check:** the key `mybox` now shows in the SSH keys list. It usually shows at once, with no prompt, and works on the running server straight away. If Hostinger asks whether to add it to the server or restart anything, tell the member what it says and choose the option that adds the key without rebuilding or wiping the server.
7. **Save the server's address yourself. The member does nothing here.** Click **Overview** and read the **IPv4 address** from the page with your browser tool (reading the page text is enough). Save it to a private file with one command: `umask 077; printf '%s\n' '<the address>' > ~/.ssh/mybox.addr`. Never write the address in your chat message: the chat folds tool details away, so it stays out of what the member sees and screenshots. **Check without printing it:** `tr -d '[:space:]' < ~/.ssh/mybox.addr | grep -Eqx '([0-9]{1,3}\.){3}[0-9]{1,3}' && echo address-saved`. Do not use the page's copy icon: Claude in Chrome's clicks cannot write to the Mac's clipboard while Chrome is in the background. Only if you cannot read the page at all, ask the member: "Please click the copy icon beside the IPv4 address on this page, then say done." Part E then reads the clipboard instead.
8. Tell the member, in two lines: "Your key is saved in Hostinger and I have your server's address. Now I walk in." And: "This page shows your server's address. If you share a screenshot of it, crop the address out first." Go straight on to Part E.

**If you have no browser tool:** guide the member instead, one click at a time: "Open hpanel.hostinger.com/vps and click Manage on your new server. Click Settings, then SSH keys, then + SSH key. Click inside the SSH key content box, press Command and V to paste (the key is on your clipboard), and click Save. There is no name box; the key shows as mybox. Then click Overview, click the copy button beside the IPv4 address, come back here and say done." When they say done, check the clipboard without printing the address: `pbpaste | tr -d '[:space:]' | grep -Eqx '([0-9]{1,3}\.){3}[0-9]{1,3}' && echo address-copied`. Then continue with Part E.

## Part E: walk in

**The address stays out of your chat messages.** It went into a private file once, in Part D step 7 (or onto the clipboard, if the member copied it). Step 1 moves it into `~/.ssh/config` without printing it. From then on every command uses the names `mybox-root` and `mybox`, never the address.

1. **Save the names my box and my box root first.** Read the address from the file saved in Part D, step 7 (or from the clipboard, if the member copied it) and write both host blocks with one script that never echoes it:
   ```
   ip=$( { cat ~/.ssh/mybox.addr 2>/dev/null || pbpaste; } | tr -d '[:space:]')
   if grep -Eq '^Host (mybox|mybox-root)$' ~/.ssh/config 2>/dev/null; then echo "mybox-already-in-config"
   elif ! printf '%s' "$ip" | grep -Eqx '([0-9]{1,3}\.){3}[0-9]{1,3}'; then echo "no-address"
   else
     mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/config && chmod 600 ~/.ssh/config
     printf '\n# my box: the member'"'"'s Hermes server (rented-server setup)\nHost mybox\n  HostName %s\n  User root\n  IdentityFile ~/.ssh/mybox_ed25519\n  IdentitiesOnly yes\n  ServerAliveInterval 30\n\nHost mybox-root\n  HostName %s\n  User root\n  IdentityFile ~/.ssh/mybox_ed25519\n  IdentitiesOnly yes\n  ServerAliveInterval 30\n\n' "$ip" "$ip" >> ~/.ssh/config
     rm -f ~/.ssh/mybox.addr; pbcopy < /dev/null; echo "config-written"
   fi
   ```
   `no-address`: go back to Part D, step 7. `mybox-already-in-config`: ask the member whether this is a second server before you change anything. Both names log in as root for now; Part F, step 2 moves `mybox` to the `hermes` user.
   A memory saved from a chat is kept for that folder only, so also add one line to `~/.claude/CLAUDE.md` (create it if missing), which every chat in every folder reads: `"My box" is the member's Hermes server: reach it with ssh mybox (as root: ssh mybox-root).` In any new chat, in any folder, "Connect to my box" must work.
2. **First login, as root, with the key.** `LogLevel=ERROR` keeps ssh from printing the address in its first-visit notice:
   `ssh -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR mybox-root 'uname -sr; lsb_release -ds; awk "/MemTotal|MemAvailable/" /proc/meminfo; df -h /; command -v hermes || echo "hermes: not installed"'`
   If this says `Permission denied (publickey)`, Hostinger may still be adding the key: wait 30 seconds and try once more. Then see Known fixes. If an error message shows the address, do not repeat it in the chat.
   **Check:** `ssh mybox true` succeeds.
3. **Set the server to the member's own timezone,** so every timed job later ("each morning", "every morning at 8") fires at their local time. Read the zone on the Mac with `readlink /etc/localtime | sed "s#.*/zoneinfo/##"`. Newer Ubuntu refuses the old-style names some Macs report (for example `US/Pacific`): if `ssh mybox-root 'timedatectl list-timezones' | grep -x <zone>` finds nothing, use the modern name for the same zone (`US/Pacific` is `America/Los_Angeles`). Then set it:
   `ssh mybox-root "timedatectl set-timezone <zone>"`
   **Check:** `ssh mybox-root timedatectl` shows that zone.
4. Turn off password login, key only:
   `ssh mybox 'printf "PasswordAuthentication no\nKbdInteractiveAuthentication no\n" > /etc/ssh/sshd_config.d/00-key-only.conf && sshd -t && systemctl reload ssh'`
   The `00-` name matters: the first value sshd reads wins, and Ubuntu cloud images may carry a later file that turns passwords on.
5. **Check, in a second session before you close anything:** `ssh mybox 'sshd -T | grep -Ei "^(passwordauthentication|kbdinteractiveauthentication)"'` shows `no` for both, and `ssh mybox true` and `ssh mybox-root true` still work.
6. **Report to the member:** that it runs plain Ubuntu, how much memory and disk it has, said as how much is in use and how much is left, in those words, that it runs on their local time, that password login is off (only this Mac's key opens it), and that Hermes is not installed yet. No version numbers and no IP address in the chat. Then say: "Your server is set up and only this Mac can get in. Now I install Hermes." Go straight on to Part F.

## Part F: install Hermes, Claude Code and the plugin

Tell the member: "Now Hermes. I install everything, you click Authorize once, then Hermes says hello." The member watches. Tell them in one line before each step what you are doing.

**Installers: read first, then run.** For steps 4 and 5, download the installer to the laptop first, read it, tell the member in one plain line what it does and that it comes from the official site, copy that exact file to the box (`scp`), check the copy matches (`shasum`), and run the copy. If the member is still in Auto mode, this route also passes Auto mode's check, which blocks `curl ... | bash`. If a "Bypass all permissions?" box appears, the member clicks **Bypass permissions**.

1. **System up to date, basic tools:**
   `ssh mybox 'export DEBIAN_FRONTEND=noninteractive; apt-get update && apt-get -y upgrade && apt-get -y install tmux curl git ca-certificates'`
   **Check:** `ssh mybox 'tmux -V && git --version'`. Then check whether the upgrade needs a restart: `ssh mybox 'test -f /var/run/reboot-required && echo reboot-needed'`. If it prints `reboot-needed`, tell the member in one line, reboot (`ssh mybox reboot`), wait a minute, and check `ssh mybox true`.
2. **One normal user for Hermes, Claude Code and every later job:**
   ```
   ssh mybox 'id hermes 2>/dev/null || adduser --disabled-password --gecos "" hermes
   usermod -aG sudo hermes
   echo "hermes ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-hermes && chmod 440 /etc/sudoers.d/90-hermes && visudo -cf /etc/sudoers.d/90-hermes
   install -d -m 700 -o hermes -g hermes /home/hermes/.ssh
   install -m 600 -o hermes -g hermes /root/.ssh/authorized_keys /home/hermes/.ssh/authorized_keys
   loginctl enable-linger hermes'
   ```
   Why a normal user: Claude Code refuses some unattended modes as root, and the brain jobs from Stage 9 run as this user. Linger lets this user's services keep running with nobody logged in.
   Then change `~/.ssh/config` so **my box** logs in as `hermes`. `mybox-root` (made in Part E, step 1) stays root. This edits only the `User` line of the `Host mybox` block, so the address never appears:
   `sed -i '' '/^Host mybox$/,/^$/s/^  User root$/  User hermes/' ~/.ssh/config`
   **Check:** `ssh mybox 'whoami; sudo -n true && echo sudo-ok'` prints `hermes` and `sudo-ok`, and `ssh mybox-root whoami` prints `root`.
3. **Command path for non-interactive logins.** The desktop app (Stage 3) and later jobs run commands without a login shell, so `~/.local/bin` must be on the path there too:
   `ssh mybox 'grep -q "HERMES_PATH_LINE" ~/.bashrc || sed -i "1i export PATH=\"\$HOME/.local/bin:\$PATH\"  # HERMES_PATH_LINE" ~/.bashrc'`
   **Check (after step 4):** `ssh mybox 'hermes --version'` works without a full path.
4. **The latest Hermes** (docs: https://hermes-agent.nousresearch.com/docs/getting-started/installation):
   ```
   curl -fsSL -o /tmp/hermes-install.sh https://hermes-agent.nousresearch.com/install.sh
   ```
   Read `/tmp/hermes-install.sh`, and tell the member in one plain line what it does and that it comes from Hermes's official site. Then copy it, check the copy matches, and run the copy:
   ```
   scp /tmp/hermes-install.sh mybox:/tmp/hermes-install.sh
   shasum -a 256 /tmp/hermes-install.sh; ssh mybox 'sha256sum /tmp/hermes-install.sh'
   ssh mybox 'bash /tmp/hermes-install.sh --non-interactive'
   ```
   The installer's `--non-interactive` flag skips the stages that need input (check the flag's spelling on the install page on the day). **Do not run `hermes setup`, and do not pick Anthropic in any Hermes wizard.** Hermes's own Claude sign-in costs extra, outside the member's plan; the plugin in step 6 runs on the plan.
   The installer tries an optional desktop-control extra (Hermes "computer-use") that fails on a server with no screen. That warning is harmless; tell the member in one line before it appears.
   **Check:** `ssh mybox 'hermes --version'`. Open the plugin page (https://hermes-agent.nousresearch.com/docs/plugins/claude-subscription-directsdk) and read the Hermes minimum it states. If the installed Hermes is older, run `ssh mybox 'hermes update'` and check again.
5. **Claude Code on the server, for the `hermes` user** (docs: https://code.claude.com/docs/en/setup):
   ```
   curl -fsSL -o /tmp/claude-install.sh https://claude.ai/install.sh
   ```
   Read `/tmp/claude-install.sh` and tell the member in one plain line what it does. Then copy it, check the copy matches, and run the copy as `hermes`:
   ```
   scp /tmp/claude-install.sh mybox:/tmp/claude-install.sh
   shasum -a 256 /tmp/claude-install.sh; ssh mybox 'sha256sum /tmp/claude-install.sh'
   ssh mybox 'bash /tmp/claude-install.sh && ~/.local/bin/claude --version'
   ```
   The plugin page names the Claude Code version it was qualified on. Keep both version numbers in your own notes, not in the chat. Do not pin a version unless the plugin fails in Part H (see Known fixes).
6. **The Claude subscription plugin:**
   `ssh mybox 'hermes plugins install claude-subscription-directsdk'`
   After installing, Hermes listed the plugin as "not enabled". Turn it on: `ssh mybox 'hermes plugins enable claude-subscription-directsdk-experimental'`. It is harmless if it was already on.
   **Check:** the install reports success, and `ssh mybox 'hermes doctor'` shows no plugin load error.
   Never set `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL` or any Bedrock, Vertex or Foundry switch for this user: the plugin refuses to run when they are set.
7. Tell the member: "Hermes, Claude Code and the plugin are on your box. Next, the one login only you can approve." Go straight on to Part G. Keep the version numbers in your own notes, not in the chat.

## Part G: the one login only the member can approve

Claude Code on the server must log in to the member's own Claude Max plan. You relay it; the member clicks.

1. Start the login inside tmux, as `hermes`:
   `ssh mybox 'tmux kill-session -t claude-login 2>/dev/null; tmux new-session -d -s claude-login "claude auth login"; sleep 4; tmux capture-pane -p -J -t claude-login'`
2. Find the full `https://` link in that output (`-J` joins wrapped lines). Open it in the member's normal browser on the laptop: `open "<link>"`. Do not click anything on this page yourself, even if you have a browser tool: approving a login is the member's click.
3. **Hand back to the member, and wait:** "claude.ai is open in your browser. Sign in to your Claude Max account if it asks. Check the account shown at the bottom of the page: if it is not your Max account, click Switch account first. Then click Authorize, click Copy code, come back here and type copied. Do not paste the code into this chat."
4. When the member types "copied", pass the code from the laptop clipboard straight into the waiting login, never printing it:
   `pbpaste | ssh mybox 'tmux load-buffer - && tmux paste-buffer -t claude-login && tmux send-keys -t claude-login Enter'`
   Then clear the laptop clipboard: `pbcopy < /dev/null`.
5. **Check:** `ssh mybox 'sleep 3; tmux capture-pane -p -J -t claude-login | tail -5; claude auth status; echo exit=$?'` shows a successful login and `exit=0`. Then `ssh mybox 'tmux kill-session -t claude-login'`. Tell the member which account and plan `claude auth status` shows. If it is a Team or Enterprise plan and not their Max plan, say so plainly and run the login again from step 1.
6. If the code expired or the login failed: start again from step 1 and open the new link.
7. **Tell the member (same claude.ai visit):** "While you are on claude.ai, open Settings, then Usage. The weekly bar is your meter. Leave usage credits off: the switch beside them stays grey." You do nothing on the server for this. Go straight on to Part H.

## Part H: Hermes says hello

1. Point Hermes at the plugin. Either run `hermes model` inside tmux (`tmux new-session -d -s hmodel "hermes model"`, read the screen with `tmux capture-pane -p -J`, choose with `tmux send-keys`) and pick **Claude Subscription DirectSDK (Experimental)**, or write the config directly: provider `claude-subscription-directsdk-experimental` (docs: plugin page).
2. Pick **the strongest Claude model on the member's plan** from the plugin's model list: the most capable model that runs on the Max plan's normal weekly allowance, not one that draws usage credits. Model names change every few weeks; if two look equal, pick the newest. Do not name the model to the member; say "the strongest Claude model on your plan".
3. **Check:** `ssh mybox 'hermes doctor'` is clean for the provider, and `claude auth status` still exits 0.
4. Ask Hermes to say hello in one short sentence, with a one-shot chat: `ssh mybox 'hermes -z "Say hello to me in one short sentence."'`. Show the member Hermes's reply exactly as written.
5. **Say to the member, in these words:** "This plugin is new and experimental, and Anthropic has not said it approves it."
6. **Report back** (see the last section) and remind the member to post a screenshot of Hermes's first reply, with no password or IP address in view.

## Part I: near the weekly limit (used later)

The plugin uses the plan faster than Claude Code does. When the member says "Switch Hermes to the lighter model until my reset.":

1. Set Hermes's default to the lighter Claude model the plugin lists (run `hermes model` in a tmux session and pick it inside the Claude Subscription DirectSDK provider, or set it in Hermes's config).
2. **Check:** Hermes answers one short test question on the new model.
3. Tell the member the day their weekly limit resets (they can see it under Settings, Usage on claude.ai) and that you will switch back when they ask.

## Known fixes

| What you see | Fix |
|---|---|
| No browser tool in this chat (Part A step 2 or Part D) | First try Claude in Chrome, as in Part A step 2: the member adds the Claude extension, signs in with the same Claude account, keeps Chrome open, and starts a new chat if this one cannot see it. If that fails, guide the member's clicks instead, as in Part D, "If you have no browser tool". Everything after Part D is the same. |
| Browser tool stops answering in Part D (Claude in Chrome) | Ask the member to keep Chrome open and reconnect the extension. Then check the SSH keys list before adding the key again, so it is not saved twice. |
| Google refuses the sign-in in the app's own browser (Part D, step 2) | Tell the member: "Google blocks sign-in inside this browser. Please sign in to Hostinger with your email and password instead, or we switch to Claude in Chrome." For Chrome, see the first row. Google often blocks sign-in inside built-in app browsers. |
| Hostinger asks for a verification code, a CAPTCHA, or a new sign-in in the middle of Part D | Hand the browser to the member: "Hostinger wants to check it's you. Please finish that in the browser and say done." Never type the code yourself. |
| You cannot find **SSH keys** in the server's Settings | Hostinger moved it. Look in the server's own menu first (not the account settings). If you still cannot find it, take a screenshot, tell the member what you see in one line, and either open the server's **Web console** (button at the top right of the server's page) and append the one `mybox` public key line to `/root/.ssh/authorized_keys`, changing nothing else, or switch to guiding their clicks. If the console asks for a login, hand it to the member: they type root and the root password from their Passwords app; you never type it. |
| Server runs a template, not plain Ubuntu (for example a "Hermes Agent configuration" form with a Deploy button, or "Docker and Traefik" as the OS; Docker Manager in the menu alone is not a template) | Do not fill the form or click Deploy, and do not change the operating system yourself: it wipes the server and sets a new root password, which is the member's. Tell the member: "Your server runs Hostinger's template. Open your server's OS & Panel, then Operating System. Under Plain OS click Ubuntu, keep the newest version, click Next, tick the box (the server is empty), click Next, click Generate and save the root password in your Passwords app, then click Change OS. Say done when it shows Running again." It can take up to 10 minutes. Then redo Part D from step 3: a rebuild may drop the saved key. |
| `Permission denied (publickey)` in Part E | Wait 30 seconds and try once more. If it still fails, the key did not reach the server: open the server's SSH keys page again in the browser (Part D, steps 4 to 6), check `mybox` is listed, and add it again if not. |
| `Host key verification failed` after a rebuild | The server was rebuilt. Remove the old line without printing the address: `ssh-keygen -R "$(ssh -G mybox </dev/null | awk '/^hostname /{print $2}')" >/dev/null 2>&1`, then connect again with `ssh -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR mybox-root true`. |
| Locked out after turning passwords off | Only if the key also fails: Hostinger's **Web console** is the rescue door: the Web console button at the top right of the server's Overview page in hPanel (the member signs in to Hostinger; if the console asks, the login is root and the root password saved in their Passwords app, which the member types). Remove `/etc/ssh/sshd_config.d/00-key-only.conf` there, fix the key, and redo Part E. |
| Plugin shows "Failed to load user provider plugin" | Hermes is older than the plugin needs. `hermes update`, then install the plugin again. |
| Plugin says it cannot find `claude` | `~/.local/bin` is not on the path for this user: redo Part F step 3, or reinstall Claude Code as `hermes`. The plugin's own hint is `npm install -g @anthropic-ai/claude-code`; prefer the native installer. |
| Plugin refuses "conflicting native auth/backend overrides" | An Anthropic key or endpoint variable is set for `hermes`. Remove it from `~/.hermes/.env` and the shell files, then retry. |
| Plugin broke after Claude Code updated itself | Reinstall the qualified version named on the plugin page (download `install.sh` to the laptop, read it, copy it to the box as in Part F step 5, then `ssh mybox 'bash /tmp/claude-install.sh <version>'`) and set `DISABLE_AUTOUPDATER` to `1` in `~/.claude/settings.json` under `env` for `hermes`. Tell the member; the weekly update job (Stage 9) must then respect the pin. |
| Hermes Desktop shows a red card "The AI service returned an error ... Retry in a moment or switch provider", and Retry fails again. `~/.hermes/logs/agent.log` on the box says `Native returned a tool outside the current host inventory`. | A known, open bug in the Claude subscription plugin: Claude sometimes calls a Hermes tool by its short name, and the plugin rejects the whole request. Upstream: NousResearch/hermes-plugin-claude-subscription-directsdk issues #39 and #62, fix proposed in PR #49. Check whether PR #49 is merged; the bug can happen even on the catalog's newest reviewed commit. The member says "Connect to my box and fix Hermes." Confirm that line in the log, then read the issues and PR #49. If the installed plugin already has the fix, the cause is something else. If not, back up the plugin file the PR changes, apply the PR #49 fix as a local patch, and test it (full tool names pass, a short name matching a Hermes tool passes, an unknown name is still rejected with a clear error). Restart every Hermes process that loaded the plugin: the gateway if it runs (`hermes gateway restart`), and the Hermes desktop app's own server process on the box, which the gateway restart does not touch (stop it with a plain `kill <pid>`; the app starts a fresh one). Check a one-line question answers: `hermes -z "Reply with the one word pong."`. Then add one report-only line to the weekly update job (Stage 9; note it for Stage 9 if the job does not exist yet): if a newer plugin replaces the patched file, the log says so. Never re-patch silently. Tell the member in one plain line. |
| `claude auth status` fails later | The login expired. Run Part G again: one link, one click. |
| The login link is cut off | Capture again with `tmux capture-pane -p -J -S -50`, rebuild the full link, open it. |
| The strongest model is refused | Use the lighter model for now, tell the member in one line, and note it in the setup record. |
| Anything else | Read the error, try one fix, and tell the member in one plain sentence. They say "Connect to my box and fix Hermes." whenever Hermes misbehaves. |

## Jobs

Stage 2 adds no scheduled job. The brain's jobs list, the "Jobs that run on their own" section of the brain's `AGENTS.md`, is made on Stage 4; the weekly Hermes update job joins it on Stage 9. Nothing to add today.

## Report back to the member

Keep it to six short lines, plain words, no secrets, no IP address, no version numbers and no model names:

1. "Your server is ready: plain Ubuntu, key only, saved as my box."
2. "Your box runs on your local time."
3. "Hermes, Claude Code and the Claude plugin are installed."
4. "Claude Code on your box is logged in to your Claude plan."
5. "Hermes runs on the strongest Claude model on your plan."
6. "Here is Hermes's first reply:" followed by the reply.

If you stopped early, say exactly where, what you saw, and the one sentence that continues: "Connect to my box and finish the rented-server setup pack (ap-hermes-server-setup)."
