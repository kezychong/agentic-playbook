---
name: ap-link-organise-signal-bots
description: "Make the Link, Organise and Signal helper bots and their chain script. Use for \"make my Link, Organise and Signal bots\" or \"run my Link, Organise and Signal now\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag it onto your brain folder, then tell Hermes: Read ap-link-organise-signal-bots.md in my brain folder and make my Link, Organise and Signal bots.

# Link, Organise and Signal Bots: three helper bots and their chain

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-link-organise-signal-bots.md in my brain folder and make my Link, Organise and Signal bots." Do nothing else with this file.

**For Hermes.** The member dragged this file into their brain folder. Make three helper bots (Link bot, Organise bot, Signal bot), write their prompts and the **chain script** that runs them one after the other, and report. Do not run the chain yet: the member starts the first run with its own sentence (below). This pack makes **no scheduled job**: the chain runs only when the member asks. The Dreaming and Recall pack (ap-dreaming-and-recall) puts it on a nightly timer, after approval.

## What you are making

Three helpers, each its own Hermes profile on this box, each shown as its own bot in the Hermes desktop app. They do the L, the O and the S of CLOSE. When the member asks, they run as **one chain**, in this order; if one step fails, the chain stops and the member gets one Telegram line saying which step.

1. **Small notes (Link bot).** First it reads `_System/brain-map.md`, the map of the member's folders made at the end of Stage 5. Then, for each new source in `01. Inbox` (the whole capture, and its long original in `08. Sources` when the note points there), it writes small notes, **one reusable idea each**: a decision, a promise, a fact, an idea or a lesson. Each small note quotes its line(s) from the source word for word, links back to the original, and links to related notes, each link with the words that prove it. One idea worth reusing, never one note per sentence: a tweet or a short video usually gives 1 note, a 2-hour meeting about 10 to 20. Small talk and setup chatter are skipped. The original is never changed, so nothing is lost.
2. **Organise (Organise bot).** It reads the brain map too, then files each small note (and each whole original still in the Inbox) into a folder the map lists under `02` to `05`, and removes links that point to notes that no longer exist. A note that fits no listed folder stays in the Inbox, and the run report suggests a folder for the member to approve. It never makes a folder without the member's yes.
3. **Signal (Signal bot).** It counts. For each thing that keeps coming up across the small notes, it counts the notes from the last 7 days and the 7 days before. A thing in **3 or more notes this week AND more than last week** is a Signal: it gets its own note in `06. Signals/`, with one dated line per note behind it. It rewrites `06. Signals/Signals overview.md` and tells the member on Telegram only about Signals that are new or moved today, at most 3.

Words: a **small note** = one idea from one source, made by the Link bot. **Signal** = one thing counted across the small notes that moved enough (3+ this week and more than last week). The number is always the count of its dated lines, never a number the bot makes up. Capture never splits and never writes small notes.

No brain map, no run: if `_System/brain-map.md` is missing, the bots stop and you tell the member to say "Build my Brain Map." first (the end of Stage 5, the Digital Twin Builder pack, Part E).

Models: no model name is fixed here, because models and plans change and every member is different. Before Part A, find out what this member actually runs: their current provider and login (a Claude subscription, a ChatGPT/Codex subscription, another provider or an API key) and the models that login can use today (`hermes model` / `hermes config get model.default` / the provider's own model list). Then give each bot the right weight on that same login:

- **Link bot = the strong everyday model** (today: newest Sonnet on Claude, newest Sol on GPT). It reads every whole source, even a 2-hour transcript, and must quote lines word for word, so do not go cheapest here.
- **Organise bot = the everyday model** (today: newest Sonnet on Claude, newest Luna on GPT). It matches each small note to a folder on the brain map.
- **Signal bot = the best model** (today: newest Opus on Claude, newest Astra on GPT). It reads only the small notes, so it uses the fewest tokens, and grouping them so the counts are right is the hardest judgement the brain makes.

Those names are today's examples, not rules: if a newer or renamed model now fills that role on the member's login, use it. If the login only offers one model, use it for all three. Choose for them, then tell the member in one line which model each bot got and why, and that they can switch any of them later.

## The member's sentences

| The member says | You do |
|---|---|
| Read ap-link-organise-signal-bots.md in my brain folder and make my Link, Organise and Signal bots. | "First: door 06", then Parts A to F, then the set-up report |
| Run my Link, Organise and Signal now. | Part G: a run by hand (the first, or any later day), then the run report |
| Fix my Link, Organise and Signal bots. | Check "Done looks like"; redo only what is missing (often the AGENTS.md lines in Part F), then report |
| That's wrong. (about a small note, a link, where a note went, or a signal) | Fix it, add one dated line under `## Link rules` in AGENTS.md so it does not happen again, read the line back |

Accept loose wording too: "set up my three bots", "make my Link, Organise and Signal bots", "run my bots now".

## Rules for this pack

- You are Hermes, on the member's box. The brain folder there: find its full path once with `hermes config get terminal.cwd` (set on Stage 4; if that is empty, `echo "$HOME/second-brain"`). It is `second-brain` in the box account's home folder: the `hermes` user's home on a rented server, the member's own Mac account on a Mac mini. Never make a second folder. Work from it. Below, `<brain>` means that full path; write it out in full in commands and files.
- Keep this pack: move this file into `_System/packs/` (replace an older copy) and add one line under `## Packs you have` in AGENTS.md: `- Link, Organise and Signal bots: when I say "Run my Link, Organise and Signal now.", read _System/packs/ap-link-organise-signal-bots.md and follow Part G.` That section sits directly above `## Jobs that run on their own`.
- **Make no scheduled job today**, for any bot or for yourself. The jobs table does not change today. If these bots already have scheduled routines from an earlier setup, pause them (`hermes -p <bot> cron pause <id>`) and remove their rows from the jobs table; the Stage 10 pack sets the timers.
- A file just dragged in may still be arriving through the mirror: if it is missing or a `.syncthing.*.tmp` file sits beside it, wait a moment and look again.
- Ask the member before spending money, deleting things, installing, scheduling or changing a live profile. Prepare everything else as a short plan, apply it on approval, then report.
- **First, approval pop-ups.** Check `hermes config get approvals.mode` and `hermes config get security.protected_instruction_files`. If they are already `off` and `false`, carry on. If not, do not change them yourself (Hermes won't lower its own safety settings). Stop and tell the member in one message: "Before I set this up: open Claude Code on your laptop and paste this: Connect to my box and run hermes config set approvals.mode off and hermes config set security.protected_instruction_files false, then tell me it's done. Then come back and say the same sentence again: Read ap-link-organise-signal-bots.md in my brain folder and make my Link, Organise and Signal bots." When they come back, check both settings again, then do every step below.
- Long or background commands: never use `nohup` or `&`; your terminal refuses them. Use your terminal tool's background option (`background: true`) instead.
- Report in plain words, no file paths unless asked. If stuck, say which step and what you saw, then: "Record the failing step without secrets and consult your host support documentation."

## First: door 06 is called 06. Signals

Door 06 holds only what the Signal bot finds across notes. If the brain still has a folder named `06. Brain` (older Stage 4 installs made it with that name), rename it before anything else, once:

1. If `06. Signals` does not exist, `mv "<brain>/06. Brain" "<brain>/06. Signals"`. If both exist, move everything from `06. Brain` into `06. Signals` (a note with the same name gets the date added to its name), then remove the empty `06. Brain`. Never delete a note.
2. Replace `06. Brain` with `06. Signals` in every note, README and (in the one AGENTS.md edit, Part F) every AGENTS.md line that names it (path links such as `[[06. Brain/...]]` included). Leave name-only links as they are; they keep working.
3. Door 06's `README.md`: title `06. Signals`, one line: `What the Signal bot finds across your notes.`
4. In AGENTS.md, door 06's line in `## The eight doors` reads: `06. Signals: what the Signal bot finds across your notes.`
5. Check: `ls <brain>` shows `06. Signals` and no `06. Brain`; `grep -rl "06. Brain" <brain> --exclude-dir=.stversions` finds nothing outside `_System/packs/`.

## Part A: make the three bots

Do these steps for `link-bot` (Link bot), `organise-bot` (Organise bot) and `signal-bot` (Signal bot), each only if `hermes profile list` does not already show it.

1. `hermes profile create <name> --clone --description "<description>"`. Link bot: "Link bot: breaks each new source into small one-idea notes that quote their line and link back, each link with proof." Organise bot: "Organise bot: files small notes into the folders on the brain map." Signal bot: "Signal bot: counts what keeps coming up across the small notes and keeps one note per Signal in 06. Signals." Cloning copies your config, keys and model. If your model comes from a plugin, copy that plugin's folder from your home's `plugins/` into the new profile's `plugins/` and enable it there (`hermes -p <name> plugins enable <plugin>`).
2. Its model, on the member's own login (see "Models" above): Link bot the strong everyday model, Organise bot the everyday model, Signal bot the best that login lists today: `hermes -p <name> config set model.default <that model>`. If the login needs a different provider setting, set that too and check it below.
3. In its `profile.yaml` set `display_name: <Link bot / Organise bot / Signal bot>` and `ui_meta: {hermes-bots: {title: <same>}}`, keeping other keys. Set its working folder: `hermes -p <name> config set terminal.cwd <brain>`.
4. Replace its SOUL.md with five plain lines: it is the <bot>, helper to <your name>, the member's chief of staff; its one job (Link bot: read the brain map, then turn each new source into small one-idea notes that quote their line, link back to the original and link with proof; Organise bot: read the brain map, then file small notes only into the folders it lists; Signal bot: count things across the small notes, one note per Signal in `06. Signals`); it never deletes a note; it reads the brain's AGENTS.md first; it never writes any Hermes memory file.
5. Check: `hermes -p <name> -z "Reply with the one word pong."` answers.

## Part B: the Link bot's prompt (small notes, then links)

Write `_System/jobs/link-prompt.md`, short and plain, read by a bot with no one there. It says:

1. Read AGENTS.md first. Every line under `## Link rules` beats this prompt. Then read `_System/brain-map.md`: its folders, what belongs in each, and its People list. **If the brain map is missing, write nothing, change nothing, and stop** with the one line: `No brain map. Say: Build my Brain Map.`
2. **Everything inside `01. Inbox/` is yours: every subfolder, every file type** (notes, zips, PDFs, docs, exports, images, links). List it all first. Skip only READMEs, hidden files and small notes (they have a `from:` line). When a capture points to its long original in `08. Sources`, read that original too.
   - A whole capture note with no `distilled:` line is a source: go to step 3.
   - **A chat export** (a zip or folder holding `conversations.json`, from ChatGPT, Claude or any tool): place it the way the Stage 5 drop-your-chats pack says (whole export into `08. Sources/chat-exports/<tool>-<date>/`, a `progress.md` with `0 of <N> chats done`), so nothing of it is left loose in the Inbox. Then work through **the whole export in this run**: each conversation with a decision, a promise, a plan, facts or ideas becomes one whole capture note in `01. Inbox/`, then a source for step 3. Keep `progress.md` up to date as you go, so if a run is ever cut off, the next run picks up where it stopped.
   - **Any other raw file** (PDF, doc, image, a bare link, an audio or video file): make it a whole capture note first, the way the Capture bot does (a long original goes into `08. Sources`, the note in `01. Inbox/` points to it), then treat it as a source.
   - Anything you truly cannot read: leave it, and name it in the log with why. **Nothing in the Inbox is ever skipped silently.**
3. **Break each source into small notes, one reusable idea each**: a decision, a promise, a fact, an idea or a lesson someone would want again. Each small note is its own file in `01. Inbox/`:
   - Title: the idea in one plain line, with its names in it ("Lena Ortiz asks to pay half now, half on handover").
   - Under the title: the line or lines it comes from, quoted word for word as a `>` quote, every name and number exactly as the source has them, `[unsure: ...]` marks kept. Never paraphrase inside the quote; never add an opinion.
   - **Quote only the source's own words**: what was said, written or shown in the original. Never quote the capture's own parts: its title, its `source:`/`captured:` lines, its "What this is" lines, its names-checked list, its notes on how it was captured, or any caveat or `<!-- -->` line Capture added.
   - `from: [[<source note name>]]` (the whole capture) and `happened: <date>` when the source says when.
   - `type: decision | promise | fact | idea | lesson`.
4. **Noise rules.** One idea worth reusing, never one note per sentence: lines that say the same thing go into one note with all their quotes. A tweet, a short video or a typed idea usually gives 1 note; an article a few; a 2-hour meeting about 10 to 20. Skip small talk, greetings, setup chatter ("can you hear me?", "let me share my screen") and anything said only to keep the talk going. A source with nothing worth reusing gets 0 notes and a reason in the log.
5. **Then links, few and with proof.** On each small note, under `## Links`, one per line: `- [[<name>]] (<person | company | project | area | came from | related>): "<quoted words>"`. **At most 5 links per small note, usually 3**: the person it is mostly about, the project or area note it plainly belongs to (only if that note already exists), and one other small note about the same decision or promise. The `from:` line is the link back to the original; do not repeat it here. Each link carries words quoted from the note that prove it. No proof, no link. Never link only because two notes share a topic, and never link everyone who happened to speak. **A link always points to a note, never to a folder.** Link by the note's name only, never by path (notes move). Where a note belongs is the Organise bot's job: it files the note into the folder, so the folder never needs a link.
6. **Link only to what already exists.** A link may point only to a note: one already in the brain (a person, company, project or area note), or another small note from today. A person on the brain map's People list may be linked by name (its spelling) even if they have no note yet. **Never make a new person, company, project or area note.** A new name that matters (it comes up in 2 or more of today's small notes) goes in the log as `Suggested new note: <name> (seen in <N> notes)` for the member to approve; leave it as plain words in the notes.
7. **Write only into the new small notes.** Never add back-links, lines or sections to any other note, and never change the original. On the whole capture, add only two things at the very end: a `## Small notes` list linking every small note made from it, and `distilled: <date>`. Nothing above them changes by one byte. Never touch the original in `08. Sources`.
8. Add `linked: <date>` as the last line of every small note. The Organise bot files only notes with that line.
9. Write `_System/link-logs/<date>.md`: first one line `Inbox at start: <N> items`, then one row per item (what it was, small notes made, links on them, or skipped and why), then any `Suggested new note:` lines, ending with one line exactly like: `<date> · sources: <N> · small notes: <K> · links: <L> · nothing to keep: <Z>`. Links = the lines under `## Links` on today's small notes, nothing else.

## Part C: the Organise bot's prompt

Write `_System/jobs/organise-prompt.md`, short and plain. It says:

1. Read AGENTS.md first. Every line under `## Link rules` beats this prompt. Then read `_System/brain-map.md`. **If the brain map is missing, move nothing and stop** with the one line: `No brain map. Say: Build my Brain Map.`
2. File each note anywhere inside `01. Inbox/` (any subfolder) that has a `linked:` line (the small notes), and each whole capture with a `distilled:` line, **only into a folder the brain map lists** under `02. Projects`, `03. Areas`, `04. Resources` or `05. Archives`. Use the map's line for each folder (what belongs there, its example people and words) to choose. A whole capture goes to the folder where most of its small notes went.
3. **Fits no listed folder → it stays in the Inbox.** Add a `needs review:` line saying why and a `suggested folder:` line (an existing map folder, or a new one with a short name). Never make a folder and never add one to the brain map yourself: the member approves new folders.
4. Never move anything into `06. Signals` or `07. World Model`. Search the destination first and put the note beside a related one. Keep the `## Links`, `from:`, `source:`, `distilled:` and `linked:` lines. If a note with the same name is already there, add the date to the moved note's name and update every link to it. Read before moving; check each move landed. Never delete.
5. Then check links across the brain: any `[[...]]` that points to a note that no longer exists is removed (keep the plain words), except a link to a person on the brain map's People list: keep it even if that person has no note yet. Log each one.
6. Never move anything in `06. Signals`, `07. World Model`, `08. Sources`, `_System` or hidden folders.
7. Write `_System/organise-logs/<date>.md`: one row per note (from, to), then each note left in the Inbox with its suggested folder, then the dead links removed, ending with one line exactly like: `<date> · moved: <M> · review: <R> · dead links removed: <D>`. Each number is the count of rows you wrote above it, never a guess.

## Part D: the Signal bot's prompt

Write `_System/jobs/signal-prompt.md`, short and plain. It says:

1. Read AGENTS.md first. Read every small note (a note with a `from:` and a `linked:` line) whose `happened:` date (or `linked:` date) is in the last 14 days, wherever it now sits (outside `_System` and hidden folders). Use the small notes, not the full originals; open an original only to check a quote.
2. **Group, then count.** Group the small notes into **things**: one subject, ask, problem, idea or person-matter, named as a short phrase a person would say ("Clients asking to pay in parts"). A thing needs at least 2 notes; never make vague buckets like "business". Then, for each thing, count its notes **this period** (the last 7 days, by `happened:` date) and **last period** (the 7 days before). Count by listing the notes, never by guessing a number.
3. **The rule.** A thing is a **Signal** when it has **3 or more notes this period AND more than last period**. A thing that came up but did not grow is not a Signal. A young brain may have none for a while: that is normal, never invent one.
4. **One note per Signal**, `06. Signals/<the thing>.md`, kept for good and updated every run. At the top: `status:` (new, growing, steady or fading), `first seen:`, `last seen:`, `this period:`, `last period:`. Then the thing as the title. Then `## Backed by`: one line per small note, `- <happened date> · [[<small note>]] · "<its quote>"`. The count is these lines. Then `## Touches`: links to the projects and people its notes link to. A Signal never links to another Signal. An existing Signal with no notes this period becomes `fading`; `acted on` and `dropped` are the member's words, never yours; never touch `06. Signals/_closed/`.
5. **Rewrite `06. Signals/Signals overview.md`** every run: title `# Signals overview`, then `## Open Signals` (each Signal, strongest first, with its status and both counts), then `## Counting from today` (things that came up but are not Signals yet, with their counts). It is a view, not a Signal.
6. Write `_System/state/logs/signal-<date>.log`, ending with one line exactly like: `<date> · notes read: <N> · things: <T> · signals: <S> · new or moved: <M>`.
7. Send the member one Telegram message through the main Hermes: run `hermes send -t telegram "<message>"` with `HERMES_HOME` set to the main Hermes home. The message: `New or moved Signals today:` then at most 3 numbered lines, each `<the thing> (<status>): <this period> notes this week, <last period> the week before`, then `All Signals: 06. Signals, Signals overview.` None new or moved: `No new or moved Signals today. Things being counted: 06. Signals, Signals overview.` Your final reply is `[SILENT]`.

## Part E: the chain script (three bots, in order)

1. Write the chain script into the Link bot's own `scripts/` folder (`<link-bot home>/scripts/brain-chain.sh`; the home is in `hermes profile show link-bot`). Fill in the real brain path and the main Hermes home:

```bash
#!/usr/bin/env bash
# Link, Organise and Signal chain: Link bot, then Organise bot, then Signal bot. Stops at the first failure.
BRAIN="<brain>"; MAIN_HOME="<main Hermes home>"; D=$(date +%F)
cd "$BRAIN" || exit 1
command -v timeout >/dev/null || timeout() { perl -e 'alarm shift; exec @ARGV' "$@"; }  # a Mac mini has no timeout command
fail() { HERMES_HOME="$MAIN_HOME" hermes send -t telegram "Your Link, Organise and Signal run stopped at the $1 step. Ask Hermes: Run my Link, Organise and Signal now." >/dev/null 2>&1; echo "$D chain stopped: $1" >> _System/state/logs/brain-chain.log; exit 1; }
step() { # $1 bot  $2 prompt file  $3 file it must write  $4 step name
  timeout 2700 hermes -p "$1" -z "Read _System/jobs/$2 and follow it. Today is $D." >/dev/null 2>&1
  [ -s "$3" ] || fail "$4"
}
mkdir -p _System/state/logs _System/link-logs _System/organise-logs
step link-bot     link-prompt.md     "_System/link-logs/$D.md"            "Link (small notes and links)"
step organise-bot organise-prompt.md "_System/organise-logs/$D.md"        "Organise"
step signal-bot   signal-prompt.md   "_System/state/logs/signal-$D.log"   "Signal"
echo "$D chain ok" >> _System/state/logs/brain-chain.log
```

   `chmod +x` it. Each step is judged by the log file it must write, never by a status line.
2. Do not put it on a timer. The script runs only when the member says "Run my Link, Organise and Signal now." (Part G). The Stage 10 pack later makes it a nightly job and adds a weekly link check.

## Part F: your own lines in AGENTS.md

In the same AGENTS.md edit (with door 06's line and the Packs line), add these to your own `## Hermes` section (make the section above `## Packs you have` if it is missing):

- `- From the brain: when you answer from a brain note, end with (from: <note name>, <date>).`
- `- "That's wrong": fix the small note, link, folder or signal, then add one dated line under ## Link rules so the bots do not repeat it.`

Make an empty `## Link rules` section directly above `## Packs you have` if it is missing. Read the changed lines back. Then give the set-up report, and last, so the app's bot list shows the new bots, run `sleep 15; pkill -f "serve [-]-isolated"` with your terminal's background option (the app starts its server again within seconds; Telegram is not touched).

## Part G: the first run by hand ("Run my Link, Organise and Signal now.")

1. Say first, in one line: "Running your Link, Organise and Signal bots now, one after the other. This may take a while: a few minutes for a small Inbox, longer for a big one. I'll tell you here and on Telegram when it's done."
2. Start `<link-bot home>/scripts/brain-chain.sh` with your terminal tool's background option (`background: true`), so it keeps running however long it takes. Never run it in the foreground inside your own turn: a long run would be cut off when your turn or command times out. This makes no scheduled job. Then check `_System/state/logs/brain-chain.log` about once a minute (a short sleep, then read it) until a new line for today appears: `chain ok`, or `chain stopped: <step>`. Keep going until that line is there; do not end your turn before it.
3. If it stopped, say which step, what its log or the note showed, and offer to run it again. Do not report counts you did not read from the logs.
4. If it finished: read the last line of today's link log (sources, small notes, links), organise log (moved, left for review with their suggested folders) and signal log, and the new or moved Signals in `06. Signals/Signals overview.md`. Reply in chat with the run report below, and send the same text to Telegram with `hermes send -t telegram "<report>"`.

## Done looks like

- `hermes profile list` shows `link-bot` on the strong everyday model, `organise-bot` on the everyday model and `signal-bot` on the best model the member's own login offers, and each answered pong.
- No new scheduled job: `hermes -p link-bot cron list`, `hermes -p organise-bot cron list` and `hermes -p signal-bot cron list` show no active job, and the jobs table has no new row.
- The brain has `06. Signals` (no `06. Brain`), its README and AGENTS.md door line say what it holds.
- The three prompt files and the chain script exist; the two lines in your `## Hermes` section; a `## Link rules` section; AGENTS.md still ends with the jobs section.
- After any run, nothing in `01. Inbox` (or its subfolders) is untouched: every item was distilled and filed, placed in `08. Sources` (a chat export, with all its chats done), left with a `needs review:` line, or named in the link log with why.
- After the first run: each new source has small notes (one idea each, quoting its line, `from:` the original, `## Links` with at most 5 quoted-reason links, a `linked:` line), filed into folders on the brain map; each original is unchanged except a `## Small notes` list and `distilled:` line at its end; no new person, company or project note was made and no other note changed; `06. Signals/Signals overview.md` was rewritten today, and each Signal note's counts match its `## Backed by` lines.

## Traps

- A step is done only when its log file exists. The chain checks this; on the first run, never start the next bot by hand before the last one's log is there.
- Links by folder path break when a note moves. Name-only links (`[[Jane Tan]]`) keep working; that is why the Link bot never writes a path, except to `08. Sources`, which never moves.
- A young brain has few people, projects and repeats: a first run with few links and one or two signals is normal. Never invent a link or a signal to make the graph look full.
- Small notes never replace the original. If any text of a capture above its `## Small notes` list changed, or a file in `08. Sources` changed, the run was wrong: restore it from the Syncthing copy in `.stversions` and tell the member.
- Links are for finding things again, not for a full graph. More than 5 links on a note, a link to everyone who spoke, back-links written into other notes, or a new note for every name is noise: cut it, and add a line under `## Link rules`.
- One note per sentence is noise. If a short video gave five notes, or a meeting gave fifty, merge notes that carry the same idea and add a line under `## Link rules`.
- No brain map, no run. The bots never guess folders; a missing `_System/brain-map.md` stops Link and Organise and the member is asked to say "Build my Brain Map."
- A bot run with nobody there cannot approve a risky shell command. These prompts only read, write and move notes and send one Telegram line; keep other shell work out of them.
- Syncthing keeps old copies in `.stversions` inside the brain: never read or move from hidden folders (except to restore, above).
- An editor once padded the jobs table and a second header crept in. Read rows cell by cell; never add a second header. Never write a weekday name in a row.
- You keep your old copy of AGENTS.md until a fresh session: start a new session yourself before you answer "What runs on its own?". Today's answer is unchanged: the bots run only when asked until Stage 10.

## Report back

**After set-up:**

1. "Your Link, Organise and Signal bots are ready. You can see them in the Hermes app."
2. "When you ask, they run as one chain: the Link bot turns each new source into small notes, one idea each, quoting its line and linking back to the original, the Organise bot files them into the folders on your brain map, and the Signal bot counts what keeps coming up across your notes and tells you on Telegram about any Signal that is new or moved (at most 3). If a step fails, the chain stops and you get one Telegram line. Nothing runs on a timer yet: on Stage 10 they start running every night by themselves."
3. "To run them now, say: Run my Link, Organise and Signal now."

**After a run** (in chat, and the same text on Telegram):

1. "Done. Your Inbox had <I> items. <N> sources turned into <K> small notes, <L> links made, <M> notes filed into their folders (<R> left in your Inbox to look at)."
   If any were left: "These didn't fit a folder on your brain map:" then each note with its suggested folder, and "Say yes to a folder and I'll make it and file them."
   If a chat export was in the Inbox: "Your <tool> export (<C> chats) is safe in 08. Sources. All <C> chats are done."
   If anything couldn't be read: "I couldn't read:" then each item with why.
2. "New or moved Signals:" then up to three, numbered, each with its counts (this week, last week), or "No Signals yet. A Signal appears when something shows up in 3 or more notes in a week, and more than the week before."
3. "All your Signals are in 06. Signals; start with the note called Signals overview."
4. "Open Obsidian and click the graph icon to see your brain."
