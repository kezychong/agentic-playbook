---
name: ap-connect-my-machines
description: "Connect a laptop and an always-on box with Tailscale, then set up key-only SSH with a short host name so the laptop agent can work on the box. Use for \"connect my two machines\", \"set up Tailscale\" or \"connect me to my box\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Connect My Machines

Two parts. Part 1 joins both machines into one private Tailscale network. Part 2 gives the laptop agent key-only SSH to the box under the short name `box` (some packs call it `mybox`: use one name and tell the owner which). Run Part 1 from whichever agent can reach each machine; run Part 2 from the coding agent on the laptop.

## Part 1: one private network (Tailscale)
You are helping a non-technical person connect two of their machines with Tailscale. Read this whole brief, then teach first, guide second. One step at a time. Wait for them to confirm each step worked before giving the next one.

### The setup you are working with

- **Machine 1 (the box):** a headless machine (usually a Mac mini) with no screen attached. It runs their Hermes agent 24/7. It sits at home or in an office.
- **Machine 2 (the laptop):** the computer they actually work on. This is probably the machine they are talking to you from.
- **The goal:** the laptop can always reach the box, from home, a cafe, or another country, using one stable name. This is what makes SSH and the Hermes dashboard work from anywhere.

Explain Tailscale in plain English before installing anything. A good frame: Tailscale builds a private hallway between their machines. No matter where each machine physically is, they act like they are in the same room. Nobody else is in the hallway.

### What to do

1. **Check whether Tailscale is already there.** On each machine, check before installing (`tailscale status` in a terminal, or look for the Tailscale icon in the menu bar). Do not reinstall what exists.
2. **Install Tailscale on the laptop.** Send them to https://tailscale.com/download and tell them exactly what to click for their OS. On a Mac, the Mac App Store version is the easiest.
3. **Create one Tailscale account.** They sign up once (Google or Apple sign-in is fine). Stress this: **both machines must sign in to the SAME account.** Two accounts = two separate hallways that never meet.
4. **Install Tailscale on the box.** If you are Hermes running on the box, or a coding agent with terminal access to it, do the install yourself and tell them what you did. If you cannot reach the box yourself, have them ask Hermes in its chat: "Install Tailscale on this machine and sign in to my Tailscale account." Hermes lives on the box and can run the install; for a headless machine the sign-in prints a link they open on the laptop. Only if Hermes truly cannot do it: they plug a screen into the box and you point them click by click. Never have them type SSH or terminal commands.
5. **Verify the hallway.** Run `tailscale status` on either machine. Both machines should be listed. Have them note the box's Tailscale name (something like `your-box.tailnet-name.ts.net`) or its 100.x.x.x address.
6. **Prove it end to end yourself.** If you can run commands where you are, ping the OTHER machine by its Tailscale name from your side (box to laptop works just as well as laptop to box). If they have Claude Code or Codex on the laptop, have them ask it to ping the box. Never ask the owner to type the ping themselves. When it works, tell them plainly: this now works from any network in the world, not just home wifi.

### Rules while you guide

- One step per message. Wait for "done" or a screenshot before continuing.
- No jargon without a household comparison in the same sentence.
- If a step fails, ask what they see on screen, then adjust. Do not repeat the same instruction louder.
- Never ask them to edit config files by hand if you can do it or there is a clickable way.
- End by writing down (for them) the box's Tailscale name and what it is for: "this is the address of your box, it works from anywhere."

## Part 2: key-only access from the laptop
You are running on a non-technical person's laptop. Their other machine is a headless box (usually a Mac mini) that runs their Hermes agent 24/7. Both machines are already on the same Tailscale account (Part 1 of this skill; if not, run Part 1 first). Your job: set up passwordless SSH from this laptop to the box, prove it works, and leave the person with plain-English asks instead of commands. Explain each step in one friendly sentence before you run it. Never make them type a command.

### What to do

1. **Find the box on the tailnet.** Run `tailscale status` (the Tailscale CLI on macOS lives at `/Applications/Tailscale.app/Contents/MacOS/Tailscale` if `tailscale` is not on PATH). Identify the box's Tailscale name (like `your-box.tailnet-name.ts.net`) or 100.x address. If you cannot tell which machine is the box, ask them what the box is called.
2. **Ask for the box's username.** Explain plainly: "this is the account name your box uses, the one Hermes was set up under." If they don't know it, they can ask Hermes in chat: "What is this machine's username?" (`whoami`).
3. **Check whether SSH already works.** Try `ssh -o BatchMode=yes -o ConnectTimeout=5 <user>@<box> true`. If it succeeds, skip to step 6.
4. **Make a key and hand it to the box.** If no SSH key exists, create one (`ssh-keygen -t ed25519`, no passphrase, default path). Then get the public key onto the box. Preferred: `ssh-copy-id <user>@<box>` (they will type the box's password ONCE; tell them this is the one and only time). If password login to the box is refused because Remote Login is off, tell them: "Ask Hermes in your chat: 'Turn on Remote Login on this Mac so my laptop can connect.'" Then retry.
5. **Write the shortcut.** Add a `Host` block to `~/.ssh/config` so the box has one short name (e.g. `Host box`), with the user and Tailscale hostname filled in.
6. **Prove it end to end.** Run `ssh box "echo connected && hostname"`. Show them the output and say plainly: your laptop can now reach your box from anywhere in the world, with no password.
7. **Teach the new reflex (this is the real deliverable).** Tell them: from now on, you never SSH anywhere. You open me (or Codex) on your laptop and ask in plain English. Give them these three example asks, verbatim:
   - "On my box, check if my Hermes agent is running fine."
   - "On my box, add this API key safely to my Hermes .env." (then paste the key when asked)
   - "Open my Hermes dashboard in my browser." (you create the tunnel with `ssh -f -N -L 9119:localhost:9119 box` and open http://localhost:9119 for them)
8. **Leave a note.** Save a short file on their laptop (e.g. `~/box-connection.md`) recording: the box's name, the shortcut (`box`), and the three example asks. Tell them where it is.

### Rules while you work

- One step at a time, one sentence of plain English before each action. Household comparisons ("an SSH key is a house key your laptop keeps; we're putting a copy of the lock on your box").
- They approve; you type. Never dictate a command for them to enter.
- If anything fails, read the real error and fix it yourself. Only involve them when a password or a Hermes-side ask is genuinely needed.
- End by having THEM try one ask ("On my box, what folders are in the home directory?") so they feel the new reflex work.

<!-- Agentic Playbook — by Kezy -->
