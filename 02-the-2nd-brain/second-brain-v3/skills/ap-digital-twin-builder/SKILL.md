---
name: ap-digital-twin-builder
description: "Interview the owner into five sourced Digital Twin notes, build the Brain Map the night bots file by, and draft replies in the owner's voice. Use for \"start my Digital Twin interview\", \"build my Brain Map\" or \"draft a reply in my voice\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

> **For you, the member:** you never need to read this file. Drag it onto your brain folder, then tell Hermes: Read ap-digital-twin-builder.md in my brain folder and start my Digital Twin interview.

# Digital Twin Builder: Digital Twin interview and Brain Map

**If you are Claude Code on the member's laptop, stop here.** This pack is for Hermes on the member's box. Tell the member in one line: "This one is for Hermes: drag it onto your brain folder, then in the Hermes app say: Read ap-digital-twin-builder.md in my brain folder and start my Digital Twin interview." Do nothing else with this file.

**For Hermes.** The member dragged this file into their brain folder. Read all of it, keep it (Rules), then run the part their sentence names: the interview (one sitting, or two if needed), then the Brain Map that tells the Link and Organise bots what goes where, then show, fix and reply in their voice any time after.

## The member's sentences

| The member says | You run |
|---|---|
| Read ap-digital-twin-builder.md in my brain folder and start my Digital Twin interview. | Part B |
| Start my Digital Twin interview. | Part B |
| Continue my Digital Twin interview. | Part B, resume |
| Build my Brain Map. | Part E only (also for a member whose Twin was made before this part existed) |
| Show me what my Twin wrote about me. | Part C, show |
| Fix my Digital Twin note on my voice. This line is wrong: [the line]. The truth is: [what is true]. Keep its source line. | Part C, fix (any of the five notes) |
| Draft a reply to this enquiry in my voice: [the enquiry] | Part D |

## Rules for this pack

- You are Hermes, on the member's box. Their brain folder on the box: find its full path once with `hermes config get terminal.cwd` (set on Stage 4; if that is empty, `echo "$HOME/second-brain"`). It is `second-brain` in the box account's home folder: the `hermes` user's home on a rented server, the member's own Mac account on a Mac mini. On the laptop it has the member's own name; never make a second folder. Work from it.
- **Start check, every part:** the eight doors and AGENTS.md exist at the root. If they are missing, say: "Your brain isn't finished building yet. Tell me: Finish building the eight doors from the brain installer. Then ask me again." and stop.
- Keep this pack: move this file into `_System/packs/` (replace an older copy). Under `## Packs you have` in AGENTS.md add one line: `- Digital Twin: when I say "Start my Digital Twin interview.", "Continue my Digital Twin interview.", "Build my Brain Map.", "Show me what my Twin wrote about me.", "Fix my Digital Twin note ..." or "Draft a reply to this enquiry in my voice: ...", read _System/packs/ap-digital-twin-builder.md and follow it.` That section sits directly above `## Jobs that run on their own`.
- A file the member just dragged in may still be arriving through the mirror: if it is missing or a `.syncthing.*.tmp` file sits beside it, wait a moment and look again.
- **Ask only what the brain does not already hold.** Before the first question, read `07. World Model/company/about-me-and-my-business.md` (the Stage 4 answers), anything already in `07. World Model/` and any notes about the member in `01. Inbox/agent-drops/`. Show what you already know in one short summary. Skip every question it already answers; offer the rest.
- The member approves the plan once at the start. The Brain Map's folder list is shown for the member to correct in one reply (Part E). Each interview note is written with a `source:` line.
- Ask the member before spending money, deleting things, installing, scheduling or changing a live profile. Prepare everything else as a short plan, apply it on approval, then report.
- Report in plain words: no file paths unless asked, no version numbers. If stuck, say which step and what you saw, then: "Record the failing step without secrets and consult your host support documentation."

## Part B: the interview (one or two sittings)

1. If `_System/digital-twin/progress.md` holds answers, this is a resume: "Picking up at question <ID>, you've done <N> of 30." Otherwise create it (all 30 IDs pending) and a `questions/` folder, and say: thirty questions in three batches, a safe stop after batch 2, answers save as they go, typing or speaking is fine.
2. **For each question, in order:** skip it if the brain already answers it (count it as done, quoting the note); otherwise look for a guess in the brain's notes and earlier answers; show the question, how many of 30 are done, and the guess with its sources, then offer confirm, clarify, update, skip or quit (no guess: answer, skip or quit). Push a vague answer at most three times ("Can you give me a real example?", "Walk me through what actually happened.", "What did that cost you?"), then take what they give.
3. **Save before the next question:** `_System/digital-twin/questions/<ID>.md` (question, guess and sources, final answer) and the mark in `progress.md`. Then "Locked in." On quit: "Locked in. Say Continue my Digital Twin interview any time."
4. After batch 2: "That's 25 of 30. This is the safe place to stop. Everything so far is saved. If you stop here, say Build my Brain Map. so your bots know where your notes go tomorrow."
5. **After all 30**, write five articles in the first person, quoting the member's own words, straight into `07. World Model/digital-twin/`: `Voice.md`, `Values.md`, `Goals.md`, `How I decide.md`, `How I work.md`. Each ends with `## Sources`, one line per fact (`source: Digital Twin interview, question <ID>, <date>` or `source: <note path>`). A sixth only for one strong pattern that fits none of the five. Nothing goes to a drafts folder; nothing waits for approval. Report the counts and the five names, and say any line can be fixed with the fix sentence. Then go straight on to Part E in the same chat.

**Batch 1 (14):** A1 Your origin story: three or four chapters that shaped you. A2 What were you like as a kid; what lit you up? A3 The hardest thing you have been through, and what it taught you. A4 Forget your job title: who are you, in three sentences? A5 What do you want true about yourself in ten years that is not true today? B1 Your ideal day ten years from now: who, what, how it feels. B2 The one thing you want to build in your lifetime, even if no one knew. B3 What problem are you uniquely placed to solve, and why you? B4 With unlimited money and no status, how would you spend your time? B5 What is actually missing between now and that ideal day? C1 Three to five things you refuse to compromise on, even when it costs you. C2 What makes you truly angry? C3 A recent decision where you took the harder path for a principle: which principle? C4 The worst thing someone could honestly say about you that would sting.
**Batch 2 (11):** D1 What comes easy to you but seems hard to most people? D2 What do you do unpaid that others charge for? D3 Your unique mix of skills, experience and perspective. D4 Your unfair advantages: relationships, knowledge, access, a head start. E1 The questions you reach for on a hard decision. E2 A belief most smart people would disagree with, that you would defend. E3 A question you have wrestled with for years without a clean answer. E4 How do you know something is true; your gut check? F1 Five to ten people who shaped how you think, and what each taught you. F2 Books, talks or ideas that keep coming back to you. F3 Who do you study, and who should you study but do not?
**Batch 3 (5):** G1 The frustration that keeps coming back every few months. G2 What are you avoiding right now? G3 What should you stop doing but have not? H1 When are you most alive; what conditions bring your best work? H2 A successful next twelve months: three concrete outcomes.

## Part E: Build my Brain Map

Why: tomorrow the Link and Organise bots file the member's notes. They can only do that if they know the member's real projects, the parts of life and work they look after, and what they read about. This part writes that down once, as folders and one short map. Run it at the end of the interview, or on its own when the member says "Build my Brain Map." (a member who made their Twin earlier: use the Twin notes they already have; do not re-run the interview).

1. **Read** `07. World Model/company/about-me-and-my-business.md`, every note in `07. World Model/digital-twin/`, the answers in `_System/digital-twin/questions/` (Goals, B5 and H2 name projects; how they work names the business), and the folders already in `02. Projects`, `03. Areas` and `04. Resources`. Fewer than 10 answers and no about-me note: say "I need a bit more about you first. Say: Continue my Digital Twin interview." and stop.
2. **Draft three lists, in the member's own words:**
   - **Projects** (`02. Projects`): one folder per live project with a finish line, an end date or a clear goal. Only what they are doing now or this year.
   - **Areas** (`03. Areas`): the ongoing things they look after, usually 4 to 8: the parts of their business (sales, clients, team, money in the business), and health, family and personal money.
   - **Resources** (`04. Resources`): the topics they read and learn about, usually 3 to 6.
   For each folder: one line on what belongs there, and the signals that mean a note belongs there: people's first names, clients, places, words they use.
3. **Show it in one message and ask for one reply**: "Here is how I'll file your notes. Change anything in one reply: rename, add, remove or move a folder. Or say Looks good." Example of the shape (a made-up bakery owner): Projects: Second shop opening (by March). Areas: Sales, Staff, Suppliers, Health, Family. Resources: Baking, Small business marketing. Take their one reply as it is; do not ask again. If they say nothing new, use the draft.
4. **Make the folders**: `02. Projects/<name>`, `03. Areas/<name>`, `04. Resources/<name>`, each with a `README.md` of the one line. Keep any folder that already exists; never rename, move or delete one the member made.
5. **Write `_System/brain-map.md`**, short and plain, in exactly this shape:

```
# Brain Map
Updated: <date> · source: Digital Twin interview and about-me note, approved by the member <date>

## Folders
02. Projects/Second shop opening | the new shop: lease, fit-out, opening day | Dana (landlord), "new shop", "fit-out", Harbour Street
03. Areas/Sales | orders, prices, regular customers | "orders", "wholesale", "price", café names
03. Areas/Staff | hiring, rosters, training | Sam, Priya, "roster", "shift"
03. Areas/Health | sleep, training, check-ups | "gym", "doctor", "sleep"
03. Areas/Family | home life and plans with family | Leo, Mia, "school", "holiday"
04. Resources/Baking | techniques and recipes they read about | "sourdough", "proofing", "flour"

## People
Dana -> 02. Projects/Second shop opening
Sam -> 03. Areas/Staff

## When unsure
Leave the note in 01. Inbox and suggest a folder in the run report. Never invent a new folder without the member's yes.
```

   One line per folder: `path | what belongs here | signals`. The People list maps each person they named to one project or area. `05. Archives`, `06. Signals`, `07. World Model` and `08. Sources` are not in the map: the Organise bot files only into the folders listed here.
6. **Add one line** to AGENTS.md, as the last line of `## The loop`: `Link and Organise read _System/brain-map.md before every run; when I approve a new folder, add it to the map the same day.`
7. **Report**: "Your Brain Map is ready: <P> projects, <A> areas, <R> topics, <N> people. Tomorrow your Link and Organise bots file every note by it. When a note fits nowhere, they leave it in your Inbox and suggest a folder; say yes and I add it to the map."

New folder later: when the member approves a folder suggested in a run report (or says "Add a folder for ..."), make it with its README, add its line (and any people) to `_System/brain-map.md`, and change the `Updated:` date.

## Part C: show and fix

- Unfinished interview? Offer "Continue my Digital Twin interview." first.
- **Show:** list the files in `07. World Model/digital-twin/`, a sentence or two from each, then ask what sounds wrong.
- **Fix:** open the note they named (unclear: ask which of the five once), replace only the quoted line with their truth in their words, keep every `source:` line, and add `source: correction from the member, <date>` under `## Sources`. Name any other stale line in one line and leave it.

## Part D: a reply in their voice

Read `Voice.md` (and `Values.md` when price, fit or promises come up). Write the reply in the chat, short enough to send as it is, in their words and rhythm. Leave gaps like `[your price]` for any fact the brain does not hold; never make one up. Under it, one line on which notes shaped it.

## Traps

- Only the member's own words, and what they clearly agreed to, count as notes about them.
- Leave out passwords, card numbers, ID numbers and home addresses; count them in the report.
- Flag a date that does not line up inside the note; never guess it.
- The five notes arrive together at the end: say so up front.
- A note you made that looks wrong: remove it and say so.
- A chat that already ran a made-up interview stays confused: start a fresh session yourself and pick up from `progress.md`.
- A usage limit is not breaking it: the progress files carry on in any new session.
- The Brain Map is not a World Model note: it lives in `_System/brain-map.md`, never in `07. World Model`, and its folders sit only in 02 to 04.
- Folder names in the member's words, never jargon ("Sales", not "Revenue operations"). A project without a finish line is an area.

## Report back

- Start: "Here is what I already know about you: <one short summary>. I'll only ask what's missing: <N> questions."
- End: "I wrote five notes about you straight into your World Model. Nothing waits for approval: they are already part of your brain." Then Part E's list, and after their reply, Part E's report.
- Fix: "Fixed, with its sources kept. I read these notes whenever I need to know you, so the fix counts from now on."

<!-- Agentic Playbook — by Kezy -->
