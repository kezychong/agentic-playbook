---
name: ap-dreaming-and-recall
description: "Schedule the Link, Organise and Signal chain, the weekly link check and update, and install a local search engine for the brain with a 72-hour brief. Use for \"set up my Dreaming\", \"give my brain its search engine\" or \"turn on meaning search\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag it onto your brain folder, then tell Hermes: Read ap-dreaming-and-recall.md in my brain folder and set up my Dreaming.

# Dreaming and Recall: your brain works at night, and can find what it kept

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-dreaming-and-recall.md in my brain folder and set up my Dreaming." Do nothing else with this file.

**For Hermes.** Two halves. **Dreaming** puts the Link, Organise and Signal chain from Stage 6 on a nightly timer, adds the weekly link check and the weekly update. **Recall** installs GBrain (the brain's search engine), its nightly index and the 72-hour brief. Do Dreaming when the member says the first sentence, Recall when they say the second; if they say both in one message, do Dreaming first. Every job belongs to a helper bot or the box's own timer; you, the chief of staff, keep none.

## The member's sentences

| The member says | You do |
|---|---|
| Read ap-dreaming-and-recall.md in my brain folder and set up my Dreaming. | Parts D1 to D5, report |
| Give my brain its search engine. | Parts R1 to R4, report, then the restart |
| Turn on meaning search in my brain. | Part R5 |
| Check my brain's search engine works. | `hermes mcp test gbrain`, then one search with your own GBrain tool; name a real note |
| Run my Link, Organise and Signal now. | The Stage 6 pack's Part G (unchanged) |
| Run the 72-hour brief once now. | `hermes -p signal-bot cron run <the brief's job id>`, then read the first lines of `_System/RECENT.md` back |

## Rules for this pack

- You are Hermes, on the member's box. Their brain folder on the box: find its full path once with `hermes config get terminal.cwd` (set on Stage 4; if that is empty, `echo "$HOME/second-brain"`). It is `second-brain` in the box account's home folder: the `hermes` user's home on a rented server, the member's own Mac account on a Mac mini. Below, `<brain>` means that full path; write it out in full in commands, scripts and crontab lines. On the laptop it has the member's own name; never make a second folder.
- **Check `uname` once.** `Linux` is a rented server: follow every step as written. `Darwin` is the member's Mac mini: the steps are the same except where a step names its Mac mini way (the weekly update, the GBrain service and the nightly index). `crontab` works on both.
- Keep this pack: move this file into `_System/packs/` (replace an older copy) and add one line under `## Packs you have` in AGENTS.md naming the sentences above and this file. That section sits directly above `## Jobs that run on their own`; the jobs list is always the last section.
- **Set each job up once.** If `cron list` or the crontab already shows a job this pack makes (from an older setup), keep one, pause the copy, and keep one row. Never a second Link, Organise or Signal bot.
- Never write a weekday name in job names, crontab comments, rows or reports.
- Ask the member before spending money, deleting things, installing, scheduling or changing a live profile. Prepare everything else as a short plan, apply it on approval, then report.
- Report in plain words: no file paths unless asked, no version numbers. If stuck: "Record the failing step without secrets and consult your host support documentation."

## Why 02:00 (tell the member in one line)

The Capture bot reads the day at 23:00 and is long done by 02:00; the box is quiet; a long chain has hours to finish before morning; the top 3 signals wait on Telegram when the member wakes. The GBrain index runs after it, at 05:00, so search reads the night's new notes. The member may pick another hour; keep the order: capture, then chain, then index.

## Part D1: check Stage 6

`hermes profile list` shows `link-bot`, `organise-bot` and `signal-bot`, and `<link-bot home>/scripts/brain-chain.sh` exists (the Link, Organise and Signal bots pack (ap-link-organise-signal-bots), `_System/packs/ap-link-organise-signal-bots.md`). If not, say so in one line and follow that pack first. Check the box's timezone is the member's (`timedatectl` on Linux, `readlink /etc/localtime` on a Mac mini); if not, offer once to set it, so 02:00 means their night.

## Part D2: the nightly chain (02:00), a script job on the Link bot

1. Make it a script job, no agent: `hermes -p link-bot cron create "0 2 * * *" --name "Nightly Link, Organise and Signal" --script brain-chain.sh --no-agent --workdir "<brain>"`. Raise `cron.script_timeout_seconds` for the Link bot to 10800, so a long night is not cut off.
2. Row: `| Nightly Link, Organise and Signal | Link bot: small notes and links from new sources; Organise bot: into the Brain Map folders; Signal bot: what keeps coming up, into 06. Signals, top 3 on Telegram. Stops with one Telegram line if a step fails | Every night at 02:00, after the 23:00 capture | Link bot (runs the other two in order) |`.

## Part D3: the weekly link check (strongest model)

Prompt `_System/jobs/link-check-prompt.md`: pick 20 random links made by the Link bot in the last 7 days; for each, read the quoted reason and both notes; if the quote does not prove the link, remove the link and log why in `_System/link-logs/link-check-<date>.md`; if more than 2 of the 20 were wrong, add one plain rule to `## Link rules` in AGENTS.md and make your final reply one line for the member, and nothing else: `Link check: <W> of 20 links were wrong and are fixed; I added a rule so it does not repeat.` Otherwise your final reply is exactly `[SILENT]`. Never send it yourself: the job sends your final reply.

First check which login the member's Hermes uses and the models it lists today; stay on that login. Then write `<link-bot home>/scripts/link-check.sh`, the same shape as the Capture bot's nightly script (Stage 5), with the real brain path, the main Hermes home and the strongest model on that login:

```bash
#!/usr/bin/env bash
# Weekly link check: the Link bot does the work; this script sends its final reply to the member's Telegram through the main Hermes.
BRAIN="<brain>"; MAIN_HOME="<main Hermes home>"; MODEL="<the strongest model>"; D=$(date +%F)
cd "$BRAIN" || exit 1
REPLY=$(hermes -p link-bot -m "$MODEL" -z "Read _System/jobs/link-check-prompt.md and follow it. Today is $D.") || { echo "$D link check stopped"; exit 1; }
LINE=$(printf '%s\n' "$REPLY" | sed '/^[[:space:]]*$/d' | tail -1)
[ -z "$LINE" ] || [ "$LINE" = "[SILENT]" ] && exit 0
echo "$LINE"
SENT=$(HERMES_HOME="$MAIN_HOME" hermes send -t telegram "$LINE" 2>&1) || echo "Telegram did not take it: $(printf '%s' "$SENT" | tail -1)"
```

`chmod +x` it. Job: `hermes -p link-bot cron create "30 4 * * <d>" --name "Weekly link check" --script link-check.sh --no-agent --workdir "<brain>" --deliver local` (a day with no other weekly job). Row: `| Weekly link check | Checks 20 random links against their quoted reasons, fixes wrong ones; messages you only if more than 2 were wrong | Once a week at 04:30 | Link bot (the strongest model) |`.

## Part D4: the weekly update (the box's own timer)

A plain script, `_System/jobs/weekly-update-run.sh` (executable), on the box account's crontab at `15 5 * * <d>` (a day with no other weekly job). It cannot be a bot's routine: it restarts Hermes, which would stop the bot running it.

- Set a full PATH (`$HOME/.local/bin`, `$HOME/.bun/bin`, and on a Mac mini `/opt/homebrew/bin`). On Linux also export `XDG_RUNTIME_DIR=/run/user/$(id -u)` and `DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus` (so `systemctl --user` works from cron); a Mac mini needs neither. Wrap the work in a 10-minute timeout (a Mac mini has no `timeout` command: use `perl -e 'alarm 600; exec @ARGV' <command>`), and append to `_System/state/logs/weekly-update-<date>.log`.
- Note the versions before. Run `hermes update --yes`. Run `hermes plugins update` for the Claude subscription plugin, then check it is still pinned and `hermes doctor` passes. Never update Claude Code.
- GBrain: only if `_System/jobs/gbrain-pin.txt` exists (Part R1 writes it; until then skip GBrain). Follow `_System/jobs/gbrain-pin-steps.md`: pause `gbrain-serve`, reinstall the pin only if something moved it, start the service again whatever happens.
- Then `hermes gateway restart` and `pkill -f "serve [-]-isolated"`, check the gateway is running (`hermes gateway status`), one-line `hermes -z` question answers, and (if GBrain exists) `hermes mcp test gbrain` connects.
- The log ends with one pass or fail line, so the 72-hour brief can report it. Say in that line if the local plugin patch from the Stage 4 later fixes was overwritten, with: tell Claude Code "Connect to my box and fix Hermes."


## Part D5: run and report

Run the chain once now as its job (`hermes -p link-bot cron run <its id>`) and check `_System/state/logs/brain-chain.log` about once a minute until today's line appears (`chain ok` or `chain stopped: <step>`). The weekly update: a dry run only (`hermes update --check`, no apply, no restart). Report:

1. "Your Link, Organise and Signal bots now run every night at 02:00, right after your 23:00 capture, so your top 3 signals are on Telegram when you wake up. If a step fails, you get one Telegram line."
2. "Once a week a stronger model checks 20 links and fixes wrong ones; you only hear if more than 2 were wrong. And once a week a job updates Hermes so it stays current."
3. "Next, say: Give my brain its search engine."

## Recall

Explain three words in one line each when you report: GBrain (a librarian who has read every note), MCP (the standard plug an agent uses to reach a tool), a service (a program the box keeps running and restarts by itself).

## Part R1: install GBrain, keyless

- GBrain is not on npm (an unrelated npm package has the same name; never `npm install -g gbrain`). It runs on Bun. If `~/.bun/bin/bun` is missing, download Bun's official installer to a file, read it, then run that file. `unzip` must be installed first.
- Put `export PATH="$HOME/.bun/bin:$PATH"  # GBRAIN_PATH_LINE` as the first line of `~/.bashrc` (on a Mac mini, `~/.zshenv`) (cron and non-interactive shells skip the end, where Bun writes its own line).
- Install the pin: `bun install -g github:garrytan/gbrain#v0.59.0.0`. Check `~/.bun/install/global/node_modules/gbrain/package.json` says `0.59.0.0`. If the install stops on a post-install step, clone that tag, `GBRAIN_NO_AUTOPILOT_INSTALL=1 bun install && bun link`.
- `gbrain init --pglite --no-embedding`: the database lives in `~/.gbrain`, outside the brain, so the mirror never copies it. If GBrain asks about "ambient memory writeback", answer no.
- `gbrain apply-migrations --yes --no-autopilot-install`, `gbrain doctor`, then `gbrain import "<brain>" --no-embed` and one `gbrain search` for a word you know is in a note.
- Long installs: run them in the background and poll, so a tool timeout does not cut them.
- Write the pin: `v0.59.0.0` into `_System/jobs/gbrain-pin.txt`, and the steps in "Pinned version" below into `_System/jobs/gbrain-pin-steps.md`.

## Part R2: the shared service, then you and Claude Code

**The lock rule.** GBrain's database opens in one program at a time. Once the service runs, every typed `gbrain` command fails with "already open" unless you `systemctl --user stop gbrain-serve` first and `systemctl --user start gbrain-serve` after, even if the command failed. Never connect anyone to GBrain as its own `gbrain serve` command; that locks everyone out. On a Mac mini the same rule holds with `launchctl bootout gui/$(id -u)/ai.gbrain.serve` to stop and `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.gbrain.serve.plist` to start.

- Tokens, before the service starts: `gbrain auth create "hermes"` and `gbrain auth create "claude-code"`. Catch each `gbrain_<hex>` token in a variable and never print it. Yours goes into `~/.hermes/.env` as `GBRAIN_MCP_TOKEN` (chmod 600). Claude Code's goes straight into `claude mcp add --scope user --transport http gbrain http://127.0.0.1:3131/mcp --header "Authorization: Bearer $T"`. If a name exists, `gbrain auth revoke` it first.
- A service that keeps GBrain running. On Linux, a systemd user service `gbrain-serve`: `ExecStart=$HOME/.bun/bin/gbrain serve --http --port 3131` (the full path written out), a PATH that includes `.bun/bin` and `.local/bin`, `Restart=on-failure`, enabled at boot; linger must be yes. On a Mac mini, a launchd agent `~/Library/LaunchAgents/ai.gbrain.serve.plist` (label `ai.gbrain.serve`, the same command with the full path, the same PATH in `EnvironmentVariables`, `RunAtLoad` and `KeepAlive` true, logs into `~/.gbrain/serve.log`), loaded with `launchctl bootstrap gui/$(id -u) <plist>`; it starts when the account logs in, which automatic login does after every restart. Check it listens on `127.0.0.1:3131` only, never `0.0.0.0`.
- Back up `~/.hermes/config.yaml`, then set your own entry under `mcp_servers:` to `gbrain: {url: http://127.0.0.1:3131/mcp, headers: {Authorization: "Bearer ${GBRAIN_MCP_TOKEN}"}, connect_timeout: 60.0, enabled: true}`. Remove any old `gbrain` entry that uses `command:`. Keep the other entries.
- Check: `hermes mcp test gbrain` lists GBrain's tools, and `cd "<brain>" && claude mcp list` shows gbrain connected. Your own chat only gets the tools after the restart.

## Part R3: the nightly index job (05:00)

GBrain's import needs no thinking, so this job is a plain script on the box account's crontab, not a bot: it also stops and starts the GBrain service, which a bot's routine cannot do unattended.

- `_System/jobs/gbrain-nightly-index-run.sh` (executable): a full PATH with `.bun/bin` and `.local/bin` (and `/opt/homebrew/bin` on a Mac mini); on Linux exports `XDG_RUNTIME_DIR` and `DBUS_SESSION_BUS_ADDRESS`; logs to `_System/state/logs/gbrain-nightly-index-<date>.log`; stops `gbrain-serve` (on a Mac mini, the launchd agent) and sets a `trap` on EXIT that always starts it again and logs `=== gbrain-serve active ===`; runs `gbrain import "<brain>" --no-embed`; if `_System/jobs/meaning-search-on` exists, also `gbrain embed --stale`; on a lock or database error runs `gbrain doctor` once; never deletes anything; ignores GBrain's "upgrade available" notice; ends with one line: date, pass or fail, page count.
- Crontab line `0 5 * * * "<brain>/_System/jobs/gbrain-nightly-index-run.sh"` (the full path written out), added without touching other lines.
- Run it once with cron's bare settings (`env -i HOME=$HOME /bin/bash <script>`). Judge by the pass line and the service back to active.
- Row: "GBrain nightly index" | "Keeps the search engine caught up with new and changed notes (and meaning search, once your search key is in)" | "Every night at 05:00, your time, after Dreaming" | "Your box's timer (a plain script)".

## Part R4: the 72-hour brief (every two hours at :45), run by the Signal bot

- If `hermes profile list` has no `signal-bot`, the Link, Organise and Signal bots pack (ap-link-organise-signal-bots) has not run: say so in one line and stop; the member runs Stage 6 first.
- Prompt `_System/jobs/recent-brief-prompt.md`. It overwrites `_System/RECENT.md`, starting "Written by the 72-hour brief at <date and time>.", with three headings: `## Changed in the last 72 hours` (newest first, leaving out `_System/state`, RECENT.md itself and every hidden folder), `## In 01. Inbox now`, `## Jobs` (each jobs-list row with its last run and whether it worked, from the status the run's script prints and the newest logs in `_System/state/logs/`). It changes no other file.
- A pre-run script `recent-brief-status.sh` in the Signal bot's own `scripts/` folder prints, for `capture-bot`, `link-bot`, `organise-bot` and `signal-bot`, `hermes -p <bot> cron list` (name, last run, last status), and the last line of each newest log in `_System/state/logs/`.
- Row first, so the first brief lists itself: "72-hour brief" | "Rewrites _System/RECENT.md: what changed in the last 72 hours, what is in your Inbox, how every job ran" | "Every two hours" | "Signal bot (the lighter model)".
- Its routine: `hermes -p signal-bot cron create "45 */2 * * *" "Read _System/jobs/recent-brief-prompt.md and follow it." --name "[bot:signal-bot] 72-hour brief" --script recent-brief-status.sh --workdir "<brain>" --deliver local`, with `--model <the lightest model on the member's own login>` (check the models that login lists today; never say its name to the member). Then run it once now (`hermes -p signal-bot cron run <job id>`).
- AGENTS.md "Read this first": the line "Read _System/RECENT.md first in every fresh session." exactly once. Replace any older "If _System/RECENT.md exists ..." sentence and drop any sentence saying the brief arrives later.

## Part R6: report, then restart yourself

1. "Your brain now has a search engine, GBrain. It has read every note and can point me or Claude Code straight to the right one. It matches words for now. For meaning search, tell Claude Code on the laptop: Add a key for Voyage. Then say Turn on meaning search in my brain."
2. "Two more jobs run on their own: the nightly index at 05:00, after Dreaming, and the 72-hour brief every two hours, which every agent reads first in a new session."
3. Then the restart message, word for word.

## If you must restart yourself

Restarting Hermes ends this chat. Do it last: finish and report everything first, tell the member "I am restarting myself now. In a minute, click New session (on Telegram, type /new) and ask me to check it worked." Then start the restart with your terminal tool's own background option (Hermes refuses `nohup … &`), so it runs after your reply: `bash -c 'sleep 15; hermes gateway restart; pkill -f "serve --isolated"'`. The desktop app runs its own `hermes serve --isolated` server, which `hermes gateway restart` never touches; the pkill makes the app start a fresh one within seconds. If you do not come back, the member tells Claude Code: "Connect to my box and fix Hermes."

## Pinned version

GBrain known-good release: `v0.59.0.0`. Never upgrade past it; the pin changes only here, in a new version of this pack. Write these steps into `gbrain-pin-steps.md` for the weekly update job: (0) stop `gbrain-serve` (from cron, export `XDG_RUNTIME_DIR` first) and always start it again at the end; (1) read the pin; (2) if the installed release differs, `bun install -g github:garrytan/gbrain#<pin>`, then `gbrain apply-migrations --yes --no-autopilot-install` and `GBRAIN_NO_REEMBED=1 gbrain post-upgrade --no-autopilot-install`; (3) `gbrain doctor` and one search, pass or fail into the log.

## Part R5: "Turn on meaning search in my brain."

The member adds the Voyage key first with the ap-add-a-key skill (Claude Code on the laptop: "Add a key for Voyage."), so it is in `~/.hermes/.env` as `VOYAGE_API_KEY`. Check only that the name is there; never print the value. Name missing: tell the member in one line to tell Claude Code "Add a key for Voyage." Then: stop `gbrain-serve`; `set -a; . ~/.hermes/.env; set +a; gbrain config set VOYAGE_API_KEY "$VOYAGE_API_KEY" >/dev/null`; `gbrain init --force --pglite --embedding-model voyage:<the current Voyage embedding model GBrain's own docs name>`; `gbrain embed --stale`; `touch "<brain>/_System/jobs/meaning-search-on"`; start `gbrain-serve`; `hermes mcp test gbrain`. If the page count dropped, import again. If the two tokens stopped working, redo Part R2's tokens; that changes your `.env`, so restart yourself last (the rule above). Prove it with one search for a phrase that means the same as a note but uses other words. Cost: Voyage charges the member's own account, a few cents for a brain this size (an estimate).


## What done looks like

- Link bot: Nightly Link, Organise and Signal at 02:00 (script, no agent) and Weekly link check on the strongest model; one crontab line for the weekly update and one for the nightly index (05:00); Signal bot: the 72-hour brief.
- Rows on the jobs list: Nightly chat capture (23:00, from Stage 5), Nightly Link, Organise and Signal, Weekly link check, Weekly update, GBrain nightly index, 72-hour brief. No job appears twice.
- `gbrain-serve` active on `127.0.0.1:3131`; `hermes mcp test gbrain` passes; `_System/RECENT.md` written once; the read-first line once in AGENTS.md.
