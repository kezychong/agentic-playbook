---
name: ap-insights-pass
description: "Judge counted Signals with the owner and add a hunch pass that connects notes into testable Insights. Use for \"show me my top Signals\", \"run my hunch pass\" or \"keep this one, bin the rest\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag it onto your brain folder, then tell Hermes: Read ap-insights-pass.md in my brain folder and add the hunch pass to my Signal bot.

# Insights Pass: judge your Signals, add the hunch pass

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-insights-pass.md in my brain folder and add the hunch pass to my Signal bot." Do nothing else with this file.

**For Hermes.** The member dragged this file into their brain folder. Two jobs. First, judge Signals the CLOSE way whenever the member asks (Part J), and check the judging they already did today. Second, give the Signal bot a second job, the **hunch pass**, run it once now, and report (Parts A to C). You keep no scheduled job yourself.

## Three kinds of record, never blurred

- A **Signal** is *counted*: one thing that came up in 3 or more small notes this week and more than the week before. One note per Signal in `06. Signals/`, made and counted by the Signal bot (Stage 6, nightly since Stage 10). A model never invents a count.
- An **Insight** is *guessed*: notes from different parts of the brain connected into an idea worth testing, with its source notes, a test and an owner. The hunch pass writes them into `06. Signals/Insights/`. A guess is never a Signal. An Insight connects notes; it need not depend on a Signal.
- The **World Model** is *settled*: what the member now holds true or decided, in `07. World Model`. Nothing enters 07 without the member's yes to that specific belief or decision; their sentence is that yes.

## The member's sentences

| The member says | You do |
|---|---|
| Show me my top Signals and the notes behind each one. | Part J1 |
| Watch [x], drop [y], mark [z] done, and write what I now hold true into my World Model with the date and why. | Part J2, then read the World Model line back |
| Keep [x], drop [y], and write what I now hold true into my World Model with the date and why. (older wording) | Part J2: "keep" means watch |
| Read ap-insights-pass.md in my brain folder and add the hunch pass to my Signal bot. | Part J3, then Parts A to C, then report |
| Run my hunch pass now. | Part C (a run by hand), then report the Insights |
| Keep [the one worth testing], bin the rest. | Mark each Insight in that Insights note `verdict: keep` or `verdict: bin`; kept ones stay in `06. Signals/Insights/` with `type: forecast`; binned ones move to `06. Signals/_closed/`. Keep means worth testing, not a settled belief or permission to promote it into World Model. |

Accept loose wording too: "show me my Signals", "watch this one, drop that one", "keep this one" (= watch), "that one is done" or "I acted on it" (= done), "run the hunch pass".

## Rules for this pack

- You are Hermes, on the member's box. The brain folder: find its full path once with `hermes config get terminal.cwd` (set on Stage 4; if that is empty, `echo "$HOME/second-brain"`). It is `second-brain` in the box account's home folder: the `hermes` user's home on a rented server, the member's own Mac account on a Mac mini; below, `<brain>` means that full path. Keep this pack: move this file into `_System/packs/` (replace an older copy) and add or update one line under `## Packs you have` in AGENTS.md: `- Signals and Insights: when I say "Show me my top Signals and the notes behind each one.", "Watch [x], drop [y], mark [z] done, and write what I now hold true into my World Model with the date and why.", "Run my hunch pass now." or "Keep [the one worth testing], bin the rest.", read _System/packs/ap-insights-pass.md and follow it; accept the loose wording listed there too.`
- Needs the Signal bot from Stage 6. If `hermes profile list` has no `signal-bot`, stop and tell the member to do Stage 6 first.
- The Signal bot owns the counts. Never change a `## Backed by` line, a count or a `status:` it set, except the member's own words `acted on` and `dropped`.
- Ask the member only before spending money or deleting things. Report in plain words, no file paths unless asked. If stuck: "Record the failing step without secrets and consult your host support documentation."

## Part J: judging Signals (the Judge step of CLOSE)

### J1. "Show me my top Signals and the notes behind each one."

1. Read `06. Signals/Signals overview.md` (the Signal bot rewrites it every run) and the open Signal notes in `06. Signals/` (not `_closed/`, not `Insights/`).
2. Take the top 3, strongest first, as the overview orders them. For each, show: the thing in plain words, its `status`, this week's and last week's counts, then each note behind it from `## Backed by` (the note's name, its date and its quote, word for word). Then one line on what it touches, from `## Touches`.
3. End with: "You are the judge. For each one, pick: watch it (it stays on your tally chart and I keep counting it), drop it (just noise, it goes in the drawer), or done (you already acted on it, it goes in the drawer marked done). Nothing is deleted. Then tell me what you now hold true and why."
4. No Signals yet (a young brain): say so in one line, then show the top 3 from `## Counting from today` the same way, and say: "These are not Signals yet. You can still tell me what you now hold true about one of them, and I'll write it into your World Model."

### J2. "Watch [x], drop [y], mark [z] done, and write what I now hold true into my World Model with the date and why."

1. **The why is the member's.** If they did not say what they now hold true, or why, ask once in one line. Never write a reason for them.
2. **Watch** (older word: keep). The Signal note stays in `06. Signals/` and the Signal bot keeps counting it. Add one line under its top lines: `judged: watch <date>`. Its status stays the Signal bot's.
3. **Drop.** Set `status: dropped`, add `judged: drop <date> · <the member's reason, if they gave one>`, then move the note into `06. Signals/_closed/` (make the folder if it is missing; a note with the same name there gets the date added to its name). Never delete it. Then add one dated line under `## Link rules` in AGENTS.md, so the Signal bot does not open it again: `- <date>: I dropped the Signal "<the thing>". Count it under Counting from today; never make it an open Signal again unless I ask.`
4. **Done** (also: acted on). If the member says one is done or they acted on it (made a project, a task, a decision or a change), set `status: acted on`, add `done: [[<the project or task note>]]`, and move it to `06. Signals/_closed/` the same way.
5. **The World Model line.** Append one line to `07. World Model/decisions/What I hold true.md` (if it is missing, make it with the title `# What I hold true` and one plain line: "Things I settled, one dated line each, with why and the Signal or Insight behind it."):
   `- <date> · <what the member now holds true, in their words> · why: <their reason> · from: [[<the Signal note>]]`
   One line per thing they settled. Link by the note's name only, never a path, so the link still works after a move to `_closed/`.
6. Read back to the member: the World Model line, word for word, and where each Signal now sits (watched: still on the chart in 06. Signals; dropped or done: in the drawer, _closed).

### J3. On install: check the judging already done

The member may have judged Signals before this pack arrived (for example in an earlier session). When you install this pack, check that work once: every Signal the member dropped today is in `_closed/` with `status: dropped` and its Link rules line; every World Model line from today has a date, a why and a `from:` link to its Signal. Fix what is missing in place, never rewrite the member's words, and say in one line what you fixed (or "Your Signal judgements are all in order.").

## Part A: the hunch pass prompt

Write `_System/jobs/hunch-pass-prompt.md`, short and plain. It says:

1. Read AGENTS.md first. Count the Signal notes in `06. Signals` (not `_closed`, not `Insights`). If there are fewer than 20 and this is a timed run (the run message does not say "a run by hand"), write no Insights: end the log with one line, "waiting: <N> of 20 Signals", and stop. A run by hand always goes ahead. Otherwise pick up to 5 notes added or changed in the last 7 days, outside `_System` and hidden folders.
2. For each, search the brain for 2 or 3 related notes from a **different** door or project (a client note with a book note, a chat with a project). Same-topic matches do not count. Old notes count: an idea written down months ago and forgotten is exactly what this pass should find again.
3. Ask: what do these notes suggest together that none says alone? Keep at most **3** Insights, the least obvious ones. No Insight is better than a weak one.
4. Write `06. Signals/Insights/Insights <date>.md`. For each Insight: a plain title, the suggested connection in two lines, one `source:` line per note, an `owner:` line (the member, unless they named someone), a **test** (what to count or try, and what result would prove it), and `verdict: ` left empty for the member.
5. Never call an Insight a Signal. Never act on one, and never write one into `07. World Model`: only the member's yes to a specific settled belief or decision settles anything. End `_System/state/logs/hunch-pass-<date>.log` with one line: date, notes read, Insights written.

## Part B: the routine and the jobs list

1. If the Signal bot already has a weekly hunch pass (or idea pass) job from an older setup, keep that one and skip to step 2. Only if no such job exists, create `hermes -p signal-bot cron create "30 4 * * <d>" "Read _System/jobs/hunch-pass-prompt.md and follow it." --name "hunch pass" --workdir "<brain>" --deliver local`, once a week, on a day with no other weekly job.
2. Add or update its one row under `## Jobs that run on their own`: `| hunch pass | Connects notes from different parts of your brain into up to 3 Insights to test, from 20 Signals | Once a week, 04:30 your time | Signal bot |`. Read the row back.

## Part C: run it once now (and on "Run my hunch pass now.")

A run by hand goes ahead below 20 Signals, so its message must say so. Start `hermes -p signal-bot -z "Read _System/jobs/hunch-pass-prompt.md and follow it. This is a run by hand. Today is <date>."` with your terminal tool's background option (`background: true`), then check today's `_System/state/logs/hunch-pass-<date>.log` about once a minute until its last line is there. Judge it by the Insights note, never by a status line.

## Done looks like

- The Signal bot's cron list shows the 72-hour brief (Stage 10) and hunch pass. One new row on the jobs list; no job appears twice.
- One `Insights <date>.md` in `06. Signals/Insights/` with up to 3 Insights, each with sources, an owner and a test.
- `_System/packs/ap-insights-pass.md` exists and the Packs line names the sentences above.
- After a judgement: the watched Signal has a `judged: watch` line and stays in 06; the dropped one sits in `06. Signals/_closed/` with `status: dropped` and a Link rules line; `07. World Model/decisions/What I hold true.md` has the new dated line with a why and a link to its Signal.

## Traps

- A small brain may give zero or one Insight. That is fine; never pad to 3.
- An idea that only restates one note is a summary, not an Insight. Drop it.
- A watched Signal is still counted by the Signal bot every night; watching it changes nothing in its counts.
- "Keep it" alone is a keep, not a belief. A kept Insight remains worth testing in `06. Signals/Insights/`; never automatically promote it. Never write a World Model line the member did not say: ask what they now hold true.

## Report back

1. "Your Signal bot now has a second job, the hunch pass. Once a week, once your brain holds 20 Signals, it connects notes from different parts of your brain and suggests up to 3 Insights to test. Until then it tells you how many it has."
2. "First run: <K> Insights in 06. Signals, Insights. Each is a guess with sources, an owner and a test, not a Signal. Reply keep or bin: kept ones stay there, binned ones move to _closed."
3. The one J3 line about today's Signal judgements.
