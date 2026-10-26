---
name: ap-morning-brief
description: "Draft a goal-linked morning brief and review cards."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. It is the recipe Hermes follows for your morning brief. Drag it into the Hermes chat and say: Read this and ask me what goes in my morning brief.

# Morning brief: one page a morning, the first version of your Today

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it into the Hermes app chat (or send it on Telegram) and say: Read this and ask me what goes in my morning brief." Do nothing else with this file.

**For Hermes.** You are the member's chief of staff. From today you send them one page every morning: first the one thing that moves them closer to their goals today, with its first draft already written inside the card, then what changed and what is waiting on them. They answer by reply ("Yes, go." or "Fix: ..."). It is the first version of their own Today dashboard. You learn what goes in it with a short interview, make the first one now, then put it on your own timer.

## The member's sentences

| The member says | You do |
|---|---|
| Read this and ask me what goes in my morning brief. | Part A, then Part B |
| Make my first morning brief now and send me the link on Telegram. | Part C |
| Yes, go. | Part D: do card 1. "Yes, go: card 3." does card 3 |
| Fix: [one thing]. | Part D: fix it, and teach BRIEF.md |
| Send me my morning brief every morning at [your time], with the link on Telegram. Add it to my jobs list. | Part E |
| What runs on its own? (new session) | Read the jobs list in the brain's AGENTS.md and name every row, the morning brief included |

Accept loose wording too: "interview me for my brief", "make today's brief", "brief me every day at 7", "go ahead", "change the brief so ...".

## Rules for this pack

- **Where things are.** Your home comes from `hermes profile` (or `$HERMES_HOME`); never assume `~/.hermes`. Below, HOME means that Hermes home. Your own workspace is `HOME/workspace` and holds your own `AGENTS.md`. The brain folder is named in the `My brain folder is` line of `HOME/SOUL.md` (or the first line of `HOME/workspace/AGENTS.md`); below, `<brain>` means that full path. Brain paths in this pack are relative to `<brain>`: use full paths.
- **Keep this pack.** Copy the file the member gave you to `<brain>/_System/packs/ap-morning-brief.md` (replace an older copy). Under `## Packs you have` in the brain's AGENTS.md add one line once: `- Morning brief: when I say "Make my first morning brief now and send me the link on Telegram.", "Yes, go.", "Fix: ..." or "Send me my morning brief every morning at ...", read _System/packs/ap-morning-brief.md and follow it.` That section lists packs, so it belongs in the brain's manual. Change nothing else in that file except the jobs row in Part E. Why: a new chat without the pack makes up its own brief.
- **Your files.** BRIEF.md lives in your own workspace: `HOME/workspace/BRIEF.md`. Today's pages live in `HOME/workspace/review-pages/`. Never put BRIEF.md in the brain, never write a HERMES.md.
- **Pointers, not copies.** BRIEF.md says where to look; it never pastes brain notes in.
- **Quiet hours are for your timer.** They stop messages you start on your own. When the member asks you for something in the chat (make the brief, send the link, run it once), they want it now: do it now.
- **Decide, do it, report.** Follow their Ask first list and obtain approval before sending, publishing, spending, deleting, installing, scheduling or changing live profiles/accounts.
- **Plain words.** No file paths or version numbers in what you tell the member unless they ask. If stuck, say which step and what you saw, then: "Record the failing step without secrets and consult your host support documentation."

## Part A: read what you already know

Read these before asking anything, and note what each already answers:

1. `HOME/GOALS.md`: the goals, the scoreboard with its **Leading** numbers (weekly actions they control, with targets) and **Lagging** numbers (results), and the Jobs I could take.
2. `HOME/workspace/AGENTS.md`: the **Alone**, **Ask first** and **Contact** lists (where you reach them, hours that are fine and not fine).
3. `HOME/memories/USER.md` and `HOME/SOUL.md`: their name, rhythm, how they like to hear from you.
4. `<brain>/_System/tools-list.md`: every tool they use and whether you can read it.
5. `<brain>/_System/brain-map.md` (the People list), `<brain>/_System/RECENT.md` (the 72-hour brief) and `<brain>/06. Signals/Signals overview.md`.

A file is missing or empty? Carry on, and ask a bit more there. If `HOME/workspace/BRIEF.md` already exists, say what it holds in two lines and ask once: change some answers, start fresh, or keep it.

## Part B: the interview, then BRIEF.md

Open in one line: "I've read your goals and rules, so I'll only ask six short questions, one at a time. Each one starts with what I already know."

Ask **one question at a time** and wait for the answer. Start each one with what the brain already says, in your own words, and ask if it is right or what to change. Reflect each answer back in one line before the next question. If the member already gave answers in their message, use them and ask only what is missing.

1. **What you decide each morning.** Offer: their engine goal from GOALS.md and its weekly action. "Each morning, is the big call which [weekly action] to do next, or something else?"
2. **The number you watch.** Offer: the Leading numbers in the scoreboard, with their weekly targets, and the Lagging result each one drives. Ask which one leads the page every morning.
3. **Who matters.** Offer: the people in the brain map and anyone named in GOALS.md. Ask whose messages and asks always make the page.
4. **What to leave out.** Offer: the tools you can read from the tools list, and the jobs that ran normally. Ask what never needs a card (for example, a made-up bakery owner: "jobs that ran fine, newsletters, anything about my old shop").
5. **What time it lands.** Offer: the start of their fine hours from the Contact list. Ask the time and their timezone.
6. **Quiet hours.** Offer: the not-fine hours from the Contact list. Ask if they still hold for the brief and any message about it.

Then write `HOME/workspace/BRIEF.md` (back up an older copy into `HOME/backups/` first):

```
# My morning brief
Lands: every morning at <time>, <timezone>, as a link on Telegram
Quiet hours: <hours>

## What I decide each morning
## The number I watch
<the Leading number, its weekly target, the goal and Lagging number it drives; where it is counted>
## Who matters
## Leave out
## Where to look
<the brain's 72-hour brief, Signals, the Inbox, and each readable tool from the tools list they want in>
## The page
The one thing first, with its first draft inside the card. Then the week's leading number. Then at most three cards: what changed since yesterday and what is waiting on me, each with its own content and one action.
Page link: not published yet
## Learned from fixes
```

Fill each section in the member's own words. Read every line back to them and say: "That is your brief. Tell me any line that is wrong and I will fix it now." Fix what they name in place and show the changed line. Then say: "Next, tell me: Make my first morning brief now and send me the link on Telegram."

## Part C: make today's brief

Used for the first brief and by your timer every morning.

1. **Read** `HOME/workspace/BRIEF.md`, `HOME/GOALS.md`, the Ask first list in `HOME/workspace/AGENTS.md`, and everything under Where to look. For "what changed", read what is new since the last brief (or the last 24 hours on the first one): `_System/RECENT.md`, new or moved Signals in `06. Signals/`, new notes in `01. Inbox/`, and the readable tools BRIEF.md names. Leave out everything under Leave out.
2. **Pick the one thing:** the single action today that moves the member closest to one named goal, through the Leading number in BRIEF.md. Prefer a job you can draft for them (a message, an offer, a post, a plan) so their part is one reply. Write the **whole first draft**, ready to send or use, not an outline. If doing it would spend money or delete something, the card says so plainly, with the amount.
3. **Build one page with the required ap-html-output skill** (include its complete folder; if absent, stop at a Markdown draft and report the missing dependency), phone first:
   - Header: `Good morning, <name>` and today's date, with the line that this is the first version of their Today.
   - **Card 1, your one thing today:** the goal it serves, one line of why today with the leading number (this week's count against the target), the full draft inside the card, where it came from, and two buttons: **Yes, go** and **Fix** (each copies its reply text for the member to paste).
   - **The week's leading number:** this week's count against the weekly target, and the Lagging result beside it. Count it from what the brain and their tools show; if it cannot be counted, write "not counted yet". Never guess a number.
   - **Then at most three cards**, what changed since yesterday and what is waiting on them, most important first. Each card carries its own content (the email or message itself, the Signal with its counts, the facts), never "go and look at X". Each has one action, with a draft reply when the action is a reply, and **Yes, go** / **Fix**. Fewer cards on a quiet day.
   - A folded "Left out today" line for what you skipped, and a footer: "This is the first version of your Today."
   - Save it as `HOME/workspace/review-pages/<YYYY-MM-DD>-morning-brief.html` with its Markdown sidecar beside it. The sidecar keeps every card's title, draft and action word for word, so a later chat can act on "Yes, go." without the page.
4. **Optional publishing, only after approval.** here.now is an external integration, not included. If unavailable or unapproved, keep the local page and skip remote delivery. If approved, use the configured publishing integration. On the first brief, publish a new site and write its link on the `Page link:` line of BRIEF.md. Every morning after, update that same site, so the link never changes: it is their Today. Open the link once and check the page title says Good morning. If publishing fails (for example, no here.now key), keep the local page, say so in one line, and tell the member: "Configure the optional publishing credential through secure local account setup; do not paste it in chat." (optional publishing setup).
5. **Send the link.** The line is: `Good morning, <name>. Your one thing today: <card 1 title>. <link>`
   - **In a chat with the member:** they asked for it just now, so send it now: `hermes send -t telegram "<the line>"`, and say the same line in the chat. If publishing failed, send the line without the link and say why. If the send fails, say the error in one line: no home channel means the member sends `/sethome` to their bot in Telegram, then you send again.
   - **When you run as the timed job** (the prompt came from your timer): do not send anything yourself. Your final reply is exactly the line, nothing else; the timer delivers it to Telegram.

## Part D: replies

- **"Yes, go."** means card 1; "Yes, go: card 3." means card 3. Find the card on today's page or in today's sidecar. The member saw the whole draft, so their yes covers exactly what the card shows: do it now (send the message, publish the post, make the change), then report in one line what you did and the new leading number. If doing it needs anything the card did not show that is on their Ask first list, spends money or deletes something, ask first in one line.
- **"Fix: [x]."** Fix it: rewrite the draft or the card, rebuild the page, update the same site, and send the line again the same way as Part C step 5. Then add one dated line under `## Learned from fixes` in BRIEF.md, in plain words, so tomorrow's brief is better (for example: `2026-03-04: drafts to cafés stay under 80 words`). Read the line back.

## Part E: your own timer

The morning brief is your own timed job: you run it, not a helper bot.

1. **Time and timezone.** Take the time from the member's sentence (or BRIEF.md's Lands line) and update the Lands line if it changed. Your timer uses `hermes config get timezone`; if that is empty it uses the box clock (`date +%Z`). If neither is the member's timezone, set yours with `hermes config set timezone <their IANA zone, e.g. Asia/Singapore>`.
2. **Telegram can be reached.** `hermes send --list telegram` shows a home target. If not, tell the member to send `/sethome` to their bot in Telegram first.
3. **One job, never two.** The job's prompt is:
   `Read BRIEF.md and Part C of <brain>/_System/packs/ap-morning-brief.md, and make today's brief. Make a new page every morning, even if one exists. Your final reply is exactly the line from Part C step 5, never [SILENT].`
   Why the last sentence: a timed job that thinks nothing is new answers [SILENT] and nothing is delivered. Look in `hermes cron list` for a job named `Morning brief`. If it exists, use `hermes cron edit <id>` to set its time (`--schedule "<M> <H> * * *"`), `--deliver telegram`, `--workdir <HOME>/workspace` and the prompt above (`--prompt`). If not, create it:
   `hermes cron create "<M> <H> * * *" "<the prompt above>" --name "Morning brief" --deliver telegram --workdir <HOME>/workspace --skill <ap-html-output skill> --skill <here.now skill>`
   Fill in the full paths and the two skill names exactly as `hermes skills list` shows them. Delivery goes from your timer to your Telegram home channel; the job itself never runs `hermes send`.
4. **One row in the jobs list.** Under `## Jobs that run on their own` in the brain's AGENTS.md, add this row to the table (or replace the existing Morning brief row, so there is exactly one): `| Morning brief | One page with your one thing and what changed | Every morning at <time>, your time | Hermes (chief of staff) |`. If the section has no table yet, add the header `| Job | What it does | When | Run by |` and its `|---|---|---|---|` line under the rule line. Back up the brain's AGENTS.md into `<brain>/05. Archives/` with the date first. The jobs section stays last.
5. **Run it once now:** `hermes cron run <id>`. The scheduler picks it up within a minute; if `hermes cron status` says the scheduler is not running, run `hermes cron tick` once. Then read `hermes cron list`: the job shows its last run and no delivery error, and today's page exists. Tell the member: "Your morning brief is on my timer for <time> every morning. I just ran it once: check Telegram."

A box asking to approve a change to AGENTS.md is Hermes's own check on its rule files: the member clicks Run.

## Done looks like

- `<brain>/_System/packs/ap-morning-brief.md` exists, and the Packs you have line appears once.
- `HOME/workspace/BRIEF.md` holds the member's answers in their words, the Page link line and a Learned from fixes section; every line was read back.
- Today's page and its sidecar sit in `HOME/workspace/review-pages/`: card 1 holds a named goal, the leading number and the full draft, then the leading number and at most three cards, each with its own content and one action. The link opens, and the line went to Telegram and into the chat.
- `hermes cron list` shows exactly one `Morning brief` job, at the member's time, delivering to Telegram, working in `HOME/workspace`, last run without a delivery error. The jobs list has exactly one Morning brief row naming Hermes (chief of staff).

## Known fixes

- **Nothing arrived on Telegram from the timer:** read the job's delivery error in `hermes cron list`. No home channel: the member sends `/sethome` to their bot. Telegram not connected: the member tells Claude Code: "Connect to my box and fix Hermes."
- **The page will not publish:** the here.now key is missing or not readable. Keep the local page and tell the member: "Configure the optional publishing credential through secure local account setup; do not paste it in chat."
- **"What runs on its own?" leaves out the brief:** an old session. The member clicks New session (or sends /new on Telegram) and asks again.
- **The member wants a different time:** they say the timer sentence again with the new time; Part E changes the same job and the same row.

## Report back

1. After the interview: "Your brief is written: <the number you watch>, <who matters>, landing at <time>. Next: Make my first morning brief now and send me the link on Telegram."
2. After the first brief: "Your first morning brief is ready: <the line>. Reply Yes, go. to do the one thing, or Fix: ... to change anything."
3. After the timer: "Your morning brief is my first timed job, every morning at <time>, your time, with the link on Telegram. It is in your jobs list. Ask me any time: What runs on its own?"

## Runtime path conventions and optional integrations

Paths such as HOME, 00. System, 07. World Model, Signals, RECENT.md and AUTOMATIONS.md describe a future user-approved runtime workspace. They are not pre-existing files supplied by this package. Resolve them from the user's confirmed vault manifest and profile. For a new PARA vault use the included ap-second-brain-setup templates; if a referenced file or automation is absent, record it missing and ask only for the information needed. Do not fabricate configured services. Optional GBrain, here.now, Telegram and scheduler integrations must be separately configured and authorized; no connector is bundled here.
