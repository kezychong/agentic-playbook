---
name: ap-score-your-brain
description: "Create, run and mark a fixed memory exam for a second brain, with the answer key kept off the box. Use for \"help me create a test for my second brain\", \"run my brain exam\" or \"why did my score drop\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Score Your Brain: a memory score out of 100

**If you are Hermes on the member's box, stop here.** This pack is for Claude Code on the member's laptop, because the answer key must stay where you cannot read it. Do not open or keep the rest of this file. Tell the member in one line: "This one is for Claude Code on your laptop: add it to a new Claude Code chat in your brain folder and say: Help me create a test for my second brain." Then delete your copy if it landed in the brain folder.

**For Claude Code.** The member downloaded this file from the Score Your Brain package and added it to a new chat in their brain folder (the plus, then Add files or photos). Read all of it now, then wait for the member's sentence. Members say these sentences in their own words, so match each one by what it asks for, not word for word.

**If a step behaves differently** from this pack: stop, tell the member in one plain sentence what you saw, try the known fix, and report what you changed.

## Why this exists

Members say "my agent does not seem to remember" and cannot say how badly. A feeling cannot be improved; a number can. Today the member's personal brain, about six days old, gets a fixed exam, marked the same way every time, and a score out of 100 with its range. Then every change (new notes, Stage 11's interview, Stage 15's meaning search, Stage 16's capture by hand, a new model) is checked the same way: did the score move by more than the normal spread between runs?

**What the score measures.** The exam goes through the route the member's agents really use: Hermes on the box, working from the brain folder, searching with GBrain, with its own memory and the 72-hour brief. So the main score measures the notes, the search and Hermes reading them. A small separate line, the chat check, measures whether a fact told to Hermes in a chat comes back, by Hermes's memory or by the Nightly chat capture (from Stage 5) turning it into a note.

**The research behind it.**

- LongMemEval, the standard test for an assistant whose facts change over time (Wu et al., ICLR 2025, arxiv.org/abs/2410.10813), tests five abilities. They are the five question types below.
- Facts told on purpose, with a date, make an answer key right by construction (Ground Truth First, arxiv.org/abs/2607.21962). The same paper found one memory system fell from 96% recall at three weeks to 72% at nine, so the exam re-runs every week.
- Diagnosing each miss by stage follows EvalMem (Liu et al., arxiv.org/abs/2609.22231): was the fact saved, did search return it, did the answer use it. EvalMem found search the most common place a memory fails. This pack adds one stage for a brain of notes: was the old note updated.
- The ranges below are Wilson 95% intervals, worked out for this pack, following Anthropic's advice to put error bars on every eval score (Miller, arxiv.org/abs/2411.00640).

## Goal

By the end of today the member has:

1. **Two answer rules in the brain's `AGENTS.md`, for questions about the member:** when they ask about themselves, their work or their business, name the note the answer came from; if the brain does not hold it, say "not in the brain" and never guess. The score assumes them (Part A). Every other question is answered as before.
2. **Their own brain exam:** up to 20 questions written from their own notes in five types, each with an answer key the member checked, plus two chat check facts they told Hermes. The keys live on the laptop in `~/brain-exam/`, outside the brain folder, so Syncthing never copies them to the box, GBrain never indexes them, and Hermes can never read them.
3. **A first score:** the exam asked three times on the box (twice if the member asks for twice), each question in a new one-shot Hermes session, as a plain question the way the member would type it. Marked by a separate grader that gets only the key and the answers, never the brain. One score out of 100, the average of the runs (each run and their spread are kept in the scorecard), points per type, failure types, and each miss diagnosed by stage.
4. **A dated scorecard in the brain**, `07. World Model/ledgers/brain-exam/`, numbers only, with its `source:` line, as the brain's `AGENTS.md` asks of every note.
5. **Fixes made by failure type** across the whole brain, not only for the questions that caught them.
6. **A weekly re-run:** a job on the box asks the same questions once a week, three times over, and its row sits on the brain's jobs list. Hermes messages the member on Telegram when it has run, and again with the score once it is marked. Marking happens on the laptop: "Grade my brain exam."
7. **A way to grow the exam:** every real forget becomes a question, and "Grow my brain exam." adds new ones from the newest notes. Grow it twice more in the first month (for example one and two weeks after the first run), aiming for about 50 questions by the end of the first month and 100 in month two.

## The five question types

| Type | LongMemEval ability | Of 20 | What it checks | The right answer |
|---|---|---|---|---|
| Single fact | Information extraction | 6 | One fact that sits in one note | The fact, and the note named |
| Two notes | Multi-session reasoning | 4 | An answer that needs two notes put together | Both parts, both notes named |
| What is true now | Knowledge updates | 3 | A fact that changed: an older note says one thing, a separate newer note says another | The newest fact. The old one is a fail |
| Dates and order | Temporal reasoning | 3 | When something happened, or what came first | The right date or order, with a note named |
| Not in the brain | Abstention | 4 | Something plausible that the brain does not hold | "Not in the brain." Any made-up answer is a fail |

- **Not in the brain is capped at 4 of 20, one in five at any size.** These questions are easier when the agent is told it may say "not in the brain", and Part A tells it exactly that. On another brain, where the agents were told it was allowed, they scored 8 of 8 on both runs; so did a second real brain. Capped, they cannot carry the score. Say this to the member plainly in the report.
- **A six-day-old brain may not fill every type.** Changed facts usually come from the Stage 5 import (old chats) against the Stage 4 note about the member or the Stage 5 and 6 Twin notes. If the brain holds fewer than three real changes in separate notes, write as many as it holds and fill the rest with single fact questions. Never plant an old fact to make an update question: an old and a new fact on the same page is a weak update question.
- A brain with little in it (a member who skipped the import) gets fewer questions: as many answerable ones as it can support, with not in the brain still capped at one in five. The score formula works at any size. Say so in one line.
- On one real brain, two notes lost the most points (6 of 16 across both runs), single fact lost 5 of 24, what is true now 1 of 12, and dates none. Its misses: not found 5, missed part of the answer 4, wrongly said not in the brain 1; nothing invented, nothing stale. Another brain lost points on two other weak spots: stale pages, where an old page still states an overruled fact with no pointer to the newer one, and dropped detail, where an answer leaves out one must-have fact. So never drop the two notes or what is true now types when the brain can support them.

## The marking (the same every time)

| Points | When |
|---|---|
| 2 | Right, with every must-have fact in the key, nothing stated as fact that the notes do not hold, and names a real note that holds it |
| 1 | Some must-have facts; or right but names no note, or names a note that does not hold it; or right but also states as fact something the notes do not hold |
| 0 | Wrong, gives the old fact as current, makes something up, says "not in the brain" when the brain does hold it, or timed out twice |

Not in the brain scores 2 or 0: 2 only if Hermes says the brain does not hold it and invents nothing. The chat check scores like single fact, except the right source is the chat or Hermes's memory, or, once the Nightly chat capture has made one, a note.

**Score** = points ÷ (2 × questions marked) × 100. With 20 marked, each point is 2.5 on the score. The score is the mean of the runs: three by default, two if the member asked for twice. The spread is the lowest run to the highest. Tell the member one score; keep the spread for judging change (Part J step 5).

**Unmarked only when the box is at fault.** A timeout is not a box fault. When Hermes runs out of time on one question, it was usually still searching for a fact it could not find, and leaving that answer out would turn a memory miss into a smaller total and push the score up. So:

- The exam script asks a timed-out question once more, at the end of the same pass. If it times out again, it is marked 0, failure type not found.
- An answer is unmarked only when the cause is the box: the answer says GBrain could not be reached, the answer says the Claude plan's usage limit was hit, Hermes failed to start or crashed (an exit code other than 0 and 124), or every answer in the pass failed.
- If fewer than 18 of 20 answers in a run are marked (nine in ten at any size), report no score for that exam. Say why in one line, fix the box (Known fixes), and run the exam again.

## How far to trust a score

- A score of 85 from 20 questions could really be anywhere from about 64 to 95; from 100 questions, about 77 to 91. (Wilson 95% intervals at 17 of 20 and 85 of 100; see The research behind it.) So 20 questions is enough to start and to find the kinds of failure, not to split hairs.
- The same brain on the same questions moves between runs: one real brain's first two runs scored 90 and 80; another brain's scored 90 and 82.5. In a sample run, three runs of the same brain scored 94, 88 and 94, so its score was 92. One run is never enough: three by default, reported as one averaged score, with the spread kept in the scorecard.
- So the exam grows: every real miss becomes a question, and "Grow my brain exam." adds new questions from the newest notes (Part J), aiming for about 50 by the end of the first month and 100 in month two. Change is always judged on the same questions (Part J step 5).

## Before you start

- **Find the member's own names first.** Every command in this pack writes the box as `mybox` and the brain folder on the box as `~/second-brain`. Those are this collection's default names; the member may use others. Before you run anything, find the real ones, in this order, and stop at the first that answers:
  1. `~/.claude/CLAUDE.md`: the "My box" line (Stage 2) gives the ssh name, and the "My brain folder" line (Stage 4) gives the laptop path.
  2. The brain's own `AGENTS.md` (in the laptop brain folder): any line naming the server, the ssh name or where the brain lives on the box.
  3. `~/.ssh/config`: the `Host` names. If only one points at a server, try it: `ssh -o BatchMode=yes <name> 'ls -d ~/*/AGENTS.md'` shows where the brain sits on the box (the folder holding the same `AGENTS.md`).
  4. If two or more could fit, ask the member one question: "Which of these is your Hermes server: <names>?"
  Tell the member in one line what you found ("Your box is `mini`, your brain on it is `~/vault`."), then use those names in place of `mybox` and `~/second-brain` in every command, script and file path below, including the exam script in Part D (its `BRAIN=` line) and the Python lines that open `AGENTS.md`.

- The brain folder's laptop path is in the "My brain folder" line of `~/.claude/CLAUDE.md` (Stage 4). Call it `BRAIN` and always quote it: `BRAIN="<the full path>";` at the start of each Mac command that uses it. The box copy is `~/second-brain` in the box account's home (`ssh mybox 'echo "$HOME/second-brain"'` gives its full path).
- The box and search are up:
  ```
  ssh mybox 'systemctl --user is-active gbrain-serve; hermes mcp test gbrain 2>&1 | tail -2; cd ~/second-brain && hermes -z "Reply with the one word pong."'
  ```
  You need `active`, a connected GBrain and `pong`. If not, run the Dreaming and recall pack's known fixes (Stage 10) first.
- Hermes's full path, for the exam script: `ssh mybox 'bash -lc "command -v hermes"'`.
- Hermes's memory folder, for the memory fingerprint: `ssh mybox 'ls ~/.hermes/memories/ 2>/dev/null'`. It usually holds `MEMORY.md` and `USER.md` (Stage 5's onboarding and the week 3 interview write into them). If the folder is missing, leave the fingerprint lines as they are; they record an empty fingerprint and nothing breaks.
- The jobs helper and the nightly index script exist: `ssh mybox 'test -f ~/second-brain/_System/jobs/add-job-row.py && test -x ~/second-brain/_System/jobs/gbrain-nightly-index-run.sh && echo jobs-ok'` (Stage 9). If not, run the Stage 9 packs first.
- The search setup: keyword only, or meaning search if the member added the Voyage key on Stage 8 and turned it on on Stage 10. Every scorecard records the setup.

## Who does what

- **You (Claude Code on the member's Mac)** are the examiner. You read the brain on the laptop, write the exam, keep the keys on the laptop, send only the questions to the box, run the exam, bring the answers back, start the separate grader, diagnose the misses, write the scorecard and make the fixes. The member never opens a command window.
- **The member** checks the answer key once (only they know what is true in their business), gives you two small facts and tells them to Hermes, agrees or disagrees with five marks after the first run, and says the sentences below.
- **Hermes on the box** is the one being tested. Each question goes to a new one-shot session (`hermes -z`), in the same words every time, from the brain folder, with no key anywhere it can read.
- **The grader** is a separate helper agent you start for the marking. You give it the key, the answers and your note check, all inside its prompt, and tell it to use no tools. It never gets the brain, GBrain or this chat.
- Bypass permissions is on (Stage 2), so nothing stops to ask. The one question you ask before acting is the deletion of Hermes's exam chats in Part D step 2: deleting things is the one kind of act that needs a yes first.
- Report in plain words: no server paths, no version numbers, no keys.

## The member's sentences, word for word

| Sitting | Who hears it | The member says | You run |
|---|---|---|---|
| 1 | Claude Code | Help me create a test for my second brain. (Or: Build my brain exam from my brain folder. Any sentence asking for a test or exam of their brain counts.) | Parts A and B |
| 1 | Claude Code | Keep all. (or: Approved.) / Fix [number]: [the right answer]. | Part C |
| 1 (optional) | Hermes, in a normal chat | The two chat check facts, in their own words, in passing | Nothing; Part C step 4 tells them what to say |
| 2 | Claude Code | Run my brain exam three times and score it. ("twice" means two runs; no number means three.) | Parts D, E, F and G |
| 2 | Claude Code | Agree. / [number] was right. | Part E step 5 |
| 3 | Claude Code | Fix what my brain exam found, and make it run every week. | Parts H and I |
| 3 | Hermes, in a new session | What runs on its own? | Nothing; Part I step 3 put the brain exam on the jobs list |
| 4, then any time | Claude Code | Add this to my brain exam: Hermes forgot [what it forgot]. | Part J step 1 |
| any | Claude Code | Grade my brain exam. | Part D step 7, then Parts E, F and G, for every finished run not yet marked. Marking only: it adds no questions. |
| Later (twice more in the first month) | Claude Code | Grow my brain exam. | First grade any finished run not yet marked, then Part J step 2 |
| any | Claude Code | Connect to my box and fix Hermes. | Known fixes, then `hermes doctor` |

"Fix [number]: [the right answer].", "[number] was right." and "Hermes forgot [what it forgot]." are shapes: the member fills the brackets with their own number and their own words, for example "Fix 7: the price is now 900." "Approved.", "approved", "all good" or "looks right" after the key means Keep all.

## Part A: the two answer rules (sitting 1)

The score assumes Hermes names its notes and says when the brain does not hold something. Check the brain's `AGENTS.md` has both rules, in one line, before the first run. The rules cover only questions about the member, their work and their business, so every agent still answers general questions and does general tasks as before. Edit it on the box, the way the Stage 9 pack does:

```
ssh mybox 'python3 - <<"PY"
import pathlib
p = pathlib.Path.home() / "second-brain" / "AGENTS.md"
t = p.read_text()
rule = "When I ask about me, my work or my business, name the note the answer came from. If the brain does not hold it, say \"not in the brain\". Never guess."
head = "## Read this first"
if head not in t:
    title, rest = t.split("\n", 1)
    t = title + "\n\n" + head + "\n\n" + rest
if rule not in t:
    i = t.index(head)
    j = t.find("\n## ", i + len(head))
    j = len(t) if j == -1 else j
    t = t[:j].rstrip("\n") + "\n" + rule + "\n" + t[j:]
    p.write_text(t)
print(t.count(rule))
PY'
```

**Check:** prints `1`, and `ssh mybox 'grep -A5 "^## Read this first" ~/second-brain/AGENTS.md'` shows the RECENT.md line from Stage 10 and the rule line, once. Tell the member in one line: "I added two rules to your brain's rulebook: when you ask about you, your work or your business, Hermes names the note the answer came from, and says not in the brain rather than guess."

## Part B: write the exam (sitting 1)

1. **The exam folder on the laptop, outside the brain:**
   ```
   mkdir -p ~/brain-exam/runs ~/brain-exam/grades ~/brain-exam/reports
   [ -f ~/brain-exam/README.md ] || printf '# Brain exam\n\nThe answer keys for my brain exam. Nothing here goes into my brain folder or onto my box, except the questions file.\n' > ~/brain-exam/README.md
   ```
   Save this pack there as `~/brain-exam/brain-exam-pack.md`, so any later chat can follow it. Find the file the member added (usually `~/Downloads/ap-score-your-brain.md`; an older copy may be named `score-your-brain-pack.md` or `D10-score-your-brain-pack.md`; if none is there, `mdfind -name score-your-brain` and pick the newest) and copy it with the shell: `cp "<that file>" ~/brain-exam/brain-exam-pack.md`. Never retype the pack yourself.
   **Check:** `ls -d ~/brain-exam` shows it, and it is not inside `"$BRAIN"`; `grep -c "^## Part" ~/brain-exam/brain-exam-pack.md` counts the same parts as the added file.
2. **Tell every chat where the exam lives.** Add one line to `~/.claude/CLAUDE.md`, under the Stage 4 "My brain folder" line, once:
   ```
   grep -q '"My brain exam"' ~/.claude/CLAUDE.md || printf '"My brain exam" lives in `~/brain-exam` on the laptop, outside my brain folder; follow `~/brain-exam/brain-exam-pack.md`. Nothing from it goes into my brain folder or onto my box, except the questions file.\n' >> ~/.claude/CLAUDE.md
   ```
   Then "Grade my brain exam." and "Grow my brain exam." work in any new chat.
3. **Read the brain on the laptop**, not through GBrain: you are the examiner, not the one being tested. Read `07. World Model` (company, people, decisions, digital-twin), `06. Signals`, `02. Projects` and `03. Areas`. Skip `01. Inbox`, `04. Resources` (other people's material, easy to guess), `05. Archives`, `_System` and every hidden folder.
4. **Draft up to 20 questions** in the mix above. For each:
   - Ask it the way the member would ask Hermes, in their words, in one clause. Split a two-part question into two.
   - Its answer sits in the brain now, in a note you can name. A not in the brain question is the opposite: plausible for this business, and absent. For each one, search the laptop brain for its key words (`grep -ril "<word>" "$BRAIN"`) and confirm nothing holds it.
   - **What is true now:** the old fact sits in a separate, older note. Record the old fact in the key: giving it counts as stale. On Stage 11 the newer note is often only days old and listed in the 72-hour brief; that is the real route today, so keep the question.
   - **Dates and order:** real dates only, never "last week", so the question means the same thing every week.
   - Prefer answers that matter to the member's work: offer, prices, clients, promises, goals, who does what. Mix easy and hard.
5. **The no-brain check.** Start a helper agent, give it only the questions, tell it to use no tools and give its best guess at each from general knowledge. Drop any question it gets right, and write a new one of the same type. On another brain a helper with no brain guessed one of 20 right and half of two others.
6. **Write the key** to `~/brain-exam/key.md`, one block per question, numbered q01 up:
   ```
   ## q07 · two notes
   Question: <the question>
   Must-have facts: 1) <fact> 2) <fact>
   Old answer that counts as stale: <only for what is true now>
   Notes that hold it: <path>; <path>
   Added: <today>, first exam
   Tags: <empty; Part H adds fix-touched>
   ```
   For not in the brain: `Right answer: says the brain does not hold it. Any specific answer is invented.` Keep must-have facts to one to three short facts, the ones a right answer cannot skip. Extra true detail is fine.
7. **Report:** "Your brain exam is drafted: N questions from your own notes, in five types. Next, you check every answer. Only you know what is true in your business."

## Part C: the member checks the key, then it is locked (sitting 1)

An agent-written key can be wrong: on another brain, the two graders flagged 3 of 20 keys as faulty, all found only after the runs.

1. Show the questions with their must-have facts, five at a time, as a short numbered list: question, then the facts in plain words. No note paths unless asked.
2. Say: "Tell me Keep all (or just: approved), or Fix and the number with the right answer." If the member says a question is not worth asking, swap it for a new one of the same type (Part B step 4 rules).
3. Apply each fix.
4. **The chat check (optional)**. Ask: "Give me two small facts about your business that are not written in any note, for example a supplier's name or a date you agreed with someone." Check each is in no note (`grep -ril`). Write them to `~/brain-exam/chat-key.md` as c01 and c02, each with today's date, in the key format. Then hand back: "Now tell Hermes both facts in a normal chat, on your phone or in the Hermes app, in passing, the way you would tell an assistant. Do not ask it to remember them." They join the exam from the first weekly run, 3 to 6 days from now (Part I step 1 picks the day).
5. **The questions file**, the only file that ever goes to the box: `~/brain-exam/questions.txt`, one line per question, `q01<TAB>question`. No type, no answer, no note names. Today's run leaves out the chat check: Part I step 4 adds the c lines for the weekly runs.
6. **Lock it:**
   ```
   cd ~/brain-exam && E=$(date +%F) && cp key.md "key-$E.md" && cp questions.txt "questions-$E.txt" && shasum -a 256 "key-$E.md" "questions-$E.txt" > "FROZEN-$E.txt" && printf 'Edition %s: %s questions, locked after the member checked every answer.\n' "$E" "$(grep -c . questions.txt)" >> changes.md
   ```
   A locked edition is never edited. Every later change is a new dated edition, written up in `changes.md` (Part J). If two editions are made on one day, add `-b` to the date.
7. **Report:** "Your brain exam is locked: N questions, and you checked every answer. The answers stay on your laptop, where Hermes can never read them."

## Part D: run it on the box (sitting 2)

1. **The exam script on the box, once.** It lives in `~/brain-exam/` on the box, outside `~/second-brain`, so it is never mirrored or indexed. The box holds the questions and, until you move them to the laptop, the answers; never the keys. Each run gets its own folder named by date and time.
   ```
   ssh mybox 'mkdir -p ~/brain-exam/runs && cat > ~/brain-exam/run-exam.sh && chmod +x ~/brain-exam/run-exam.sh' << 'EOF'
   #!/usr/bin/env bash
   # Brain exam. Installed by the Stage 11 Score your brain pack. Started by cron once a week, or by Claude Code on the laptop.
   # Catches search up, then asks Hermes every question three times (run1, run2, run3; --runs 2 for two), each time in a new one-shot session, from the brain folder.
   # Only the questions live on this box. The answer keys stay on the laptop.
   set -u
   NOINDEX=no; RUNS=3; WEEKLY=no
   while [ $# -gt 0 ]; do case "$1" in --no-index) NOINDEX=yes ;; --runs) RUNS="$2"; shift ;; --weekly) WEEKLY=yes ;; esac; shift; done
   export PATH="$HOME/.local/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
   HERMES=HERMES_FULL_PATH
   EX="$HOME/brain-exam"
   MEM="$HOME/.hermes/memories"
   BRAIN="$HOME/second-brain"
   RUN_ID="$(date +%F-%H%M)"
   OUT="$EX/runs/$RUN_ID"
   LOG="$BRAIN/_System/state/logs/brain-exam-$(date +%F).log"
   mkdir -p "$OUT" "$(dirname "$LOG")"
   echo "$RUN_ID" > "$EX/runs/LATEST"
   echo "=== Brain exam starting $(date) ===" >> "$LOG"
   cp "$EX/questions.txt" "$OUT/questions.txt"
   sha256sum "$EX/questions.txt" | cut -d' ' -f1 > "$OUT/questions.sha256"
   date -Is > "$OUT/START"
   # Search catches up first, so notes filed since the last nightly index can be found.
   # Skipped with --no-index when Claude Code has just run the index by hand.
   if [ "$NOINDEX" = no ]; then
     env -i HOME="$HOME" /bin/bash "$BRAIN/_System/jobs/gbrain-nightly-index-run.sh"
     tail -2 "$(ls -t "$BRAIN"/_System/state/logs/gbrain-nightly-index-*.log 2>/dev/null | head -1)" > "$OUT/INDEX" 2>/dev/null
     sleep 180   # Hermes reconnects to GBrain within about 3 minutes after the index
   fi
   cd "$BRAIN" || exit 1
   ask() { timeout 300 "$HERMES" -z "${2}" > "${3}/${1}.txt" 2>&1 < /dev/null; echo $? > "${3}/${1}.exit"; }
   for i in $(seq 1 "$RUNS"); do
     PASS="run$i"
     P="$OUT/$PASS"
     mkdir -p "$P"
     date -Is > "$P/START"
     cat "$MEM"/*.md 2>/dev/null | sha256sum | cut -d' ' -f1 > "$P/memory-before.sha256"
     while IFS=$'\t' read -r ID QUESTION || [ -n "${ID:-}" ]; do
       [ -z "${ID:-}" ] && continue
       ask "$ID" "$QUESTION" "$P"
     done < "$OUT/questions.txt"
     # A lone timeout usually means Hermes was still searching: ask that question once more, at the end of the pass.
     while IFS=$'\t' read -r ID QUESTION || [ -n "${ID:-}" ]; do
       [ -z "${ID:-}" ] && continue
       if [ "$(cat "$P/$ID.exit")" = "124" ]; then
         mv "$P/$ID.txt" "$P/$ID.first.txt"
         echo retried > "$P/$ID.retry"
         ask "$ID" "$QUESTION" "$P"
       fi
     done < "$OUT/questions.txt"
     cat "$MEM"/*.md 2>/dev/null | sha256sum | cut -d' ' -f1 > "$P/memory-after.sha256"
     # EXAM-CHATS: Part D step 2 puts the line here that deletes this pass's own Hermes chats (started after $P/START and opened with an exam question), before the next pass.
   done
   date -Is > "$OUT/DONE"
   N=$(ls "$OUT"/run*/*.exit 2>/dev/null | wc -l)
   T=$(grep -L '^0$' "$OUT"/run*/*.exit 2>/dev/null | wc -l)
   echo "=== Brain exam done: $N answers, $T not answered; waiting for marking on the laptop ===" >> "$LOG"
   # Weekly runs tell the member on Telegram (Hermes's home channel, Stage 3). No questions, no answers.
   if [ "$WEEKLY" = yes ]; then
     "$HERMES" send -t telegram "Your weekly brain exam has run ($N answers). In Claude Code on your laptop, say: Grade my brain exam. Your score comes here when it is marked." >> "$LOG" 2>&1 || echo "telegram message not sent" >> "$LOG"
   fi
   EOF
   ssh mybox "sed -i 's#HERMES_FULL_PATH#<the Hermes path from Before you start>#' ~/brain-exam/run-exam.sh"
   ```
   The questions go to Hermes exactly as the member would type them, with no label and no instruction to search, because that is how members ask. The log line in `_System/state/logs/` holds no question and no answer; it lets the 72-hour brief report the job like every other.
2. **Keep each pass out of the next one's reach** (do this once, and write what you found in `~/brain-exam/changes.md`). If Hermes keeps one-shot chats, a later pass could find an earlier pass's exam chats and copy its answers, and every later weekly run could find the last one's. The Nightly chat capture (from Stage 5) also reads the last 24 hours of Hermes chats (`hermes sessions export --newer-than 24h`) and skips exam chats: check `_System/jobs/nightly-scan-prompt.md` on the box carries the line "Skip any chat whose first message is one of the questions in ~/brain-exam/questions.txt (the text after the tab), if that file exists." and add it, word for word, if it is missing.
   - Ask one question by hand, then look: `ssh mybox 'cd ~/second-brain && hermes -z "What is the capital of France?" >/dev/null; hermes sessions list --limit 3; hermes sessions --help'`.
   - If the one-shot chat does not appear in the list, one-shot chats are not kept: nothing to do. Write "exam chats not kept by Hermes" in every scorecard.
   - If it appears and the help offers a way to delete a session, ask the member once: "Hermes keeps a copy of every chat. After each pass of every exam run I'll delete the exam's own chats, so the next pass starts clean and neither Hermes nor your Nightly chat capture learns the questions. Your other chats are never touched. OK?" On yes, replace the `# EXAM-CHATS` line, which sits inside the pass loop, with a line that deletes only sessions started after `$P/START` whose first message is exactly one of the questions in `$OUT/questions.txt` (the text after the tab), and, if the list shows a source, only one-shot sessions. A weekly pass runs for hours, so the member's own Telegram or app chats, and, once the weekly re-run is on, the timed job's session, start inside that window too: the start time alone is never enough. Build it from what the help text shows. Test it on a one-question run and check the list is clean of exam chats after each pass, and start one Telegram chat during the test pass; it must still be listed afterwards. Never guess the command. Write "exam chats deleted after each pass" in every scorecard.
   - If there is no delete, check `hermes profile --help` for a way to make a second profile with memory off that reads the same brain through GBrain. If there is one, make it, test it with the pong and one question that names a note, and run the exam under that profile (put its flag on the `ask` line). Its chats stay away from the member's own Hermes and the Nightly chat capture. Under it the chat check can come back only through a note, so write "chat check: notes only" in the scorecard.
   - Whatever you find, if a pass can still see an earlier pass's chats, leave the `# EXAM-CHATS` line as a comment and write "a later pass could see an earlier pass's chats" in every scorecard.
3. **Send the questions (only the questions):** `scp ~/brain-exam/questions-<edition>.txt mybox:brain-exam/questions.txt`.
   **Check:** `ssh mybox 'sha256sum ~/brain-exam/questions.txt'` matches the questions line in `~/brain-exam/FROZEN-<edition>.txt`.
4. **Both copies of the brain match.** Count the notes on each side:
   ```
   BRAIN="<the full path>"; find "$BRAIN" -name "*.md" -not -path "*/.*" | wc -l; ssh mybox 'find ~/second-brain -name "*.md" -not -path "*/.*" | wc -l'
   ```
   The two numbers must match. If they differ, wait a minute and count again (the mirror may be mid-copy); if they still differ, run the Stage 4 pack's mirror known fixes first.
5. **Start it.** Look at the box's clock first: `ssh mybox 'date +%H%M'`.
   - **Between 07:15 and 23:15 box time**, run it now. First catch search up by hand with the Stage 10 live-run command: `ssh mybox 'env -i HOME=$HOME /bin/bash ~/second-brain/_System/jobs/gbrain-nightly-index-run.sh; tail -4 ~/second-brain/_System/state/logs/gbrain-nightly-index-*.log'`. **Check:** the last lines say pass with a page count, then `=== gbrain-serve active ===`, and `ssh mybox 'hermes mcp test gbrain'` shows GBrain connected (it may take up to 3 minutes). Then start the exam in the background without a second index: `ssh mybox 'nohup ~/brain-exam/run-exam.sh --no-index > ~/brain-exam/run.log 2>&1 < /dev/null &'` (add `--runs 2` after `--no-index` if the member said twice).
   - **Between 23:15 and 07:15 box time**, the run would meet the night jobs: the 02:00 Link, Organise and Signal chain, the weekly link check at 04:30, the 05:00 index that pauses search and the weekly update that restarts Hermes at 05:15. So start it at 07:15 instead, after the night jobs; the script catches search up itself:
     ```
     ssh mybox 'T=$(date -d 07:15 +%s); [ "$T" -le "$(date +%s)" ] && T=$(date -d "tomorrow 07:15" +%s); nohup bash -c "sleep $(( T - $(date +%s) )); ~/brain-exam/run-exam.sh" > ~/brain-exam/run.log 2>&1 < /dev/null & echo started-waiting'
     ```
     (If the member said twice, put `--runs 2` after `run-exam.sh` in that line.) Tell the member: "It is late on your box, so the exam starts at 07:15 box time, after your night jobs. Each answer is cut off after 5 minutes, so this takes a while. When you are back, say: Grade my brain exam."
   When it starts now, tell the member, in these words: "Hermes is now answering each question three times, each time in a new session, and I'll average the runs into one score. Each answer is cut off after 5 minutes, so this takes a while; I'll tell you when it's done." Never promise a speed. If the laptop sleeps or the chat closes, the exam still runs on the box; the member says "Grade my brain exam." later.
6. Check every few minutes until `DONE` shows:
   `ssh mybox 'R=$(cat ~/brain-exam/runs/LATEST); echo $R; ls ~/brain-exam/runs/$R/DONE 2>/dev/null; ls ~/brain-exam/runs/$R/*/*.exit 2>/dev/null | wc -l'`
   Keep the run id it prints.
7. **Move the answers to the laptop**, then off the box:
   ```
   scp -r mybox:brain-exam/runs/<run id> ~/brain-exam/runs/
   ```
   **Check:** one answer file and one `.exit` file per question line in each run folder (`run1`, `run2`, `run3`), on the laptop. Then remove the answers from the box, keeping only `START`, `DONE` and the fingerprints, so no later session on the box can read old answers:
   ```
   ssh mybox 'find ~/brain-exam/runs/<run id> -type f ! -name DONE ! -name START ! -name "*.sha256" -delete; find ~/brain-exam/runs/<run id> -type f | wc -l'
   ```
   It prints 12 for three runs (9 for two): the run's own `START` and one per pass, `DONE`, the questions fingerprint and two memory fingerprints per pass. This moves the exam's own answers to the laptop; it removes nothing of the member's, so it needs no question. The run's `questions.sha256` must match an edition's `FROZEN` line: mark the run against that edition, never against the newest key by default. If the two memory fingerprints in a pass differ, Hermes saved something during the exam: note it for the scorecard.
8. **Decide what is marked**, before the grader sees anything. Go through each answer with its `.exit`:
   - `0`: marked.
   - `124` after the retry (a `.retry` file sits beside it): marked, 0 points, failure type not found. Tell the grader so.
   - Unmarked, because the box was at fault: the answer says GBrain could not be reached or the usage limit was hit, or the exit code is anything other than 0 and 124, or every answer in the pass failed.
   If fewer than 18 of 20 answers in any run are marked (nine in ten at any size), stop: report no score, say why in one line, fix it (Known fixes), and run the exam again from step 5.

## Part E: mark it with a separate grader (sitting 2)

1. **The note check first** (you do this, not the grader). For each answer, find the notes Hermes named (paths, file names, or titles without `.md`). In the laptop brain, check each exists and holds the must-have words:
   ```
   BRAIN="<the full path>"; n="<name as Hermes gave it>"; f=$(find "$BRAIN" \( -name "$n" -o -name "$n.md" \) -not -path "*/.*" | head -1); if [ -n "$f" ]; then echo "exists: ${f#$BRAIN/}"; grep -c -i -e "<must-have word 1>" -e "<must-have word 2>" "$f" || true; else echo missing; fi
   ```
   Write one line per answer to `~/brain-exam/runs/<run id>/note-check.txt`, for example `run1 q07: named plan.md, exists, holds the facts`.
2. **Write the grading prompt** once to `~/brain-exam/grading-prompt.md`:
   ```
   You are the grader for a brain exam. Everything you need is below: the answer key, every answer with its status, and a note check.
   Use no tools. Do not open any file or folder, do not search anything, and do not use anything you know about this person.
   Mark each question in each run: 2 = right, with every must-have fact, nothing stated as fact beyond what the key or the note check supports, and the note check shows a named note that exists and holds it (or it is one of the key's notes); 1 = some must-have facts, or right with no valid note, or right but also states as fact something the key and note check do not support; 0 = wrong, gives the stale answer as current, makes something up, or says the brain does not hold it when the key says it does.
   For "not in the brain" questions: 2 only if it says the brain does not hold it and invents nothing; otherwise 0.
   For chat check questions (c lines): as above, but the right source is the chat, Hermes's memory, or a note.
   An answer with status TIMED OUT TWICE is 0, failure type not found. An answer with status UNMARKED is left out: do not mark it. Every other answer is marked.
   Give each mark below 2 one failure type: not found, stale, missed a must-have, overclaim, invented, wrongly refused, no note named. Add one short reason.
   Extra true detail beyond the key is fine. Be strict about missing must-have facts and stale facts. Mark against the key exactly as written; if you think a key is wrong, still mark against it and say so in key_issue.
   Return only JSON: [{"id":"q01","run":"run1","mark":2,"fail":"","why":"...","key_issue":""}]
   ```
3. **Start the grader as a separate helper agent**, not in your own head: its prompt is the grading prompt, then the key of the matching edition (and `chat-key.md` if c lines were asked), then every answer file with its status from Part D step 8, then `note-check.txt`. Nothing else: not this chat, not the brain, not the questions' notes. Save what it returns to `~/brain-exam/grades/<run id>-grader1.json`. **First score only, start a second grader** the same way, on its own, and save `grader2.json`. Report how many marks differ and the gap between the two graders' scores, next to the gap between the runs. On one real brain the two graders agreed on 39 of 40 marks (85 against 86.25), while the runs differed by 10.
4. **Add it up.** Per run: points ÷ (2 × marked) × 100. Score = the mean of the runs; spread = lowest to highest run; gap = highest minus lowest. Also points per type per run, and a count of each failure type. The chat check is its own line: points out of 4 per run, never in the main score. Where two graders differ, use grader 1 for the headline and show both.
5. **First score only, check the grader**. Show the member the three lowest-marked answers and two answers picked at random from those marked 2, each beside its key. On another brain the first grading was too kind and had to be redone strictly, so full marks get a look too. Ask: "Do you agree with these marks? Say Agree, or the number and what was right." If the member shows a mark broke the marking rules against the key as written, correct that mark and write "grader corrected by the member: N marks" in the scorecard. If the member says the key itself was wrong, retire that question the Part J step 6 way. Never change a key to raise a score.

## Part F: diagnose each miss by stage (sitting 2)

For every question marked below 2 in any run, and every chat check miss, find the first stage that failed. You do this on the laptop, with the brain; the grader never does.

1. **Saved?** Is the fact in any note? `grep -ril "<must-have word>" "$BRAIN"`, skipping hidden folders. If no note holds it: **not saved**.
2. **Updated?** For a stale answer, or any what is true now question: does an older note still state the old fact with no pointer to the newer one? If yes: **not updated**.
3. **Found?** The fact is saved and current, but Hermes did not name the note that holds it, or said not in the brain. Search caught up just before the run (Part D step 5, or the script's own index on a weekly run), so ask GBrain on the box, through Claude Code's own connection (Claude Code on the box sees GBrain):
   `ssh mybox 'cd ~/second-brain && ~/.local/bin/claude -p "Use your gbrain tools to search my brain for: <the question>. Print only the paths of the top five notes, one per line." --permission-mode bypassPermissions'`
   Key note in the top five: **found by search, not used by Hermes**. Not there: **not found by search**. If the key note was written or changed after the run started, it is neither: record **not indexed yet** and leave it out of the stage counts.
4. **Read right?** Hermes named the right note but dropped a must-have fact or claimed more than it holds: **misread**.
5. **The chat check, every run day.** For each chat fact, record three things: whether it came back (its mark), whether it had become a note by run day and where (`grep -ril`; the Nightly chat capture, from Stage 5, may already have turned a chat fact into a note: record which route brought it back, memory or capture), and whether it sits in Hermes's memory files: `ssh mybox 'grep -il "<fact word>" ~/.hermes/memories/*.md'`.
6. **Did Hermes's memory change since Stage 11?** Keep the first run's `run1/memory-before.sha256` as `~/brain-exam/memory-day11.sha256`. On every later run, compare that run's `run1/memory-before.sha256` with it and record yes or no. Stage 11's interview writes into Hermes's memory, so after Stage 11 a yes is expected; a chat check fact that was in memory on Stage 10 and is gone later is worth one line in the report.
7. Write the full report, with each question, both marks, the reasons, the stage and the notes involved, to `~/brain-exam/reports/<run id>.md` on the laptop, never into the brain.

## Part G: the scorecard in the brain (sitting 2)

1. **The ledger folder, once.** Make it, and name it in the brain's own map, so every agent knows what it is:
   ```
   BRAIN="<the full path>"; mkdir -p "$BRAIN/07. World Model/ledgers/brain-exam"; [ -f "$BRAIN/07. World Model/ledgers/README.md" ] || printf '# Ledgers\n\nNumbers recorded over time, one dated note each. First ledger: brain-exam, the score of my brain exam.\n' > "$BRAIN/07. World Model/ledgers/README.md"
   ssh mybox 'python3 - <<"PY"
   import pathlib
   p = pathlib.Path.home() / "second-brain" / "AGENTS.md"
   t = p.read_text()
   old = "and `digital-twin`, what the Digital Twin has learned."
   new = "`digital-twin`, what the Digital Twin has learned, and `ledgers`, numbers recorded over time, such as the brain exam score."
   if "`ledgers`" not in t and old in t:
       p.write_text(t.replace(old, new, 1))
   print(p.read_text().count("`ledgers`"))
   PY'
   ```
   **Check:** prints `1`. If the doors line was reworded since Stage 4 and `0` prints, add `ledgers` to the 07 line by hand in the same plain style. Add one line for `ledgers` to `07. World Model/README.md` too.
2. **Write the scorecard** to `"$BRAIN/07. World Model/ledgers/brain-exam/<run id>-brain-exam.md"`. **Numbers only: no question wording, no answers, no facts from the key, no note paths, no question numbers**, or the brain would learn where its exam's answers sit. Format, with one real brain's numbers standing in:
   ```
   # Brain exam score, <run id>

   Score: 92.0 out of 100 (average of 3 runs: 94.0, 88.0, 94.0; spread 88.0 to 94.0; gap 6.0)
   Marked: 20 of 20 (unmarked, box at fault: none; timed out twice, marked 0: none)
   Exam edition: <edition date>, <N> questions
   Same questions as the last score: <N>, <score> against <last score>; verdict: <better / about the same / worse / first score>
   First 20 questions (the trend line): <score>
   Questions whose notes a fix touched: <score>, or none yet
   Questions added since the last fix, from notes no fix touched: <score>, or none yet
   Search setup: keyword / keyword and meaning; search caught up before the run: <yes / no>
   Graders: <one / two, marks that differ: N>
   Exam chats: <deleted after each pass / not kept by Hermes / a later pass could see an earlier pass's chats>; Hermes memory changed during the run: <no / yes>; since Stage 11: <no / yes / first score>
   Chat check: <points> of 4 in each run; became a note: <n> of <n>; in Hermes's memory: <n> of <n> (not in the main score)
   What changed since the last score: <what the member or you changed, or: first score>; after score: <yes / too soon after the fixes / first score>

   | Question type | Run 1 | Run 2 | Run 3 |
   |---|---|---|---|
   | Single fact (<n>) | <points>/<max> | <points>/<max> | <points>/<max> |
   | Two notes (<n>) | <points>/<max> | <points>/<max> | <points>/<max> |
   | What is true now (<n>) | <points>/<max> | <points>/<max> | <points>/<max> |
   | Dates and order (<n>) | <points>/<max> | <points>/<max> | <points>/<max> |
   | Not in the brain (<n>) | <points>/<max> | <points>/<max> | <points>/<max> |

   | Mistake | All runs |
   |---|---|
   | Not found | <n> |
   | Missed a must-have | <n> |
   | Wrongly refused | <n> |
   | Stale | <n> |
   | Overclaim | <n> |
   | Invented | <n> |
   | No note named | <n> |

   | Where each miss started | All runs |
   |---|---|
   | Not saved | <n> |
   | Not updated | <n> |
   | Not found by search | <n> |
   | Found by search, not used | <n> |
   | Misread | <n> |

   source: brain exam, asked of Hermes on my box, marked on my laptop by a separate grader; keys, answers and question numbers kept outside the brain
   ```
   The score line shows a sample brain's three runs (94, 88, 94: score 92); every other number is a blank here. On the member's scorecard every number comes from their own runs (two columns if they asked for twice), and the mistake counts may also be split by run.
3. **Hand back:** "Open Obsidian, then 07. World Model, ledgers, brain-exam: your first scorecard is there."
4. **Report to the member**, in this shape, with their own numbers: "Your brain scored N out of 100, the average of three runs. It is strongest on <type> and weakest on <type>. Across all runs: <counts of the mistakes that happened>. Most misses started at <stage>: <one plain line, for example two old notes still state your old price and do not point to the new one>." Then two honest lines: "Twenty questions is a starting line: a score of 85 from 20 questions could really be anywhere from about 64 to 95, and from 100 questions about 77 to 91. That is why the exam grows." and "Not in the brain questions are the easy ones, because your rulebook tells Hermes it may say so; they are capped at one in five so they cannot carry the score." Do not walk the member through each run or the spread unless they ask; it sits in the scorecard. Then: "Say: Fix what my brain exam found, and make it run every week."
5. **Send the score to the member's phone**, every time you mark a run (first score, weekly runs, "Grade my brain exam."), through Hermes's Telegram home channel from Stage 3, the way the Stage 6 Signal message goes. Numbers and plain words only, never a question or an answer:
   ```
   ssh mybox 'hermes send -t telegram "Your brain exam score: <N> out of 100. <verdict line>. Scorecard: 07. World Model, ledgers, brain-exam."'
   ```
   The verdict line follows Part J step 5: "Better than last time." only when the change beats the normal spread; otherwise "About the same as last time." (or "First score.", or "Lower than last time." only when it is worse by that rule). **Check:** it exits 0 and the member sees it. If it fails, the home channel is missing: the Stage 3 pack's known fix (send `/sethome` to the bot). The score is still in the ledger; say so in one line.

## Part H: fix by failure type (sitting 3)

Fix the kind of fault across the whole brain, not only the note the exam caught. If you fix only the exam's notes, the score goes up and the brain does not get better.

**Keep the edit list.** Append every note you edit, one path per line with today's date, to `~/brain-exam/fixed-notes.txt`. Then add `fix-touched` to the Tags line, in the next edition's key, of every question whose key note is on that list. Part J uses both to keep the comparison honest: you know every key, so the questions that judge your fixes must come from notes you did not touch.

| Where the miss started | Fix, across the whole brain |
|---|---|
| Not saved | Ask the member for the truth in one line. Write it as a dated note in the right door with `source: told by <first name>, <date>`: a fact told on purpose, with a date, is right by construction. |
| Not updated (stale) | Find every note that still states the old fact. At the top of each add `Replaced on <date>: see [[<newer note>]]`. Never delete the old note. On another brain both stale answers came from old pages with no pointer to the newer ruling. |
| Not found by search | If the fact is split across small notes, write one note that holds it whole, titled in the words the member would ask with; keep the small notes, each pointing to it. On another brain one rule spread over near-duplicate pages lost points on both runs. From Stage 15, meaning search also helps when the words do not match. |
| Found by search, not used by Hermes | Hermes answered without searching. Add one line under "Read this first" in `AGENTS.md` (the Part A way): "Search the brain with GBrain before answering a question about my business or my life." |
| Misread | Make the note plainer: one fact per line, each with its date. |
| Invented, overclaim, no note named | Check the Part A rule line is in `AGENTS.md`. If it is and it keeps happening, say so in the report: it is the model's reading, and the weekly score will show whether it lasts. |

Then:

1. Tell the member what you changed in plain words, one line per kind of fix.
2. **When the after score counts.** The 72-hour brief lists recently changed notes and every new session reads it, so a run within three days of a fix would hand Hermes the fixed notes. The first weekly run is 3 to 6 days from today (Part I step 1), so when the fixes are made today, it is the after score. Any run less than three days after a later fix is scored as usual, and its scorecard says "too soon after the fixes to count as the after score"; the next weekly run is the after score. GBrain picks up the fixes at its nightly index (03:15), and the exam script catches search up again before each weekly run. It also includes what Stages 11 and 12 change; the scorecard's What changed line names them.

## Part I: the weekly re-run (sitting 3)

1. **Pick the day and time.** Read the whole schedule: `ssh mybox 'crontab -l'`. It holds the GBrain nightly index (05:00, pauses search) and the weekly update (05:15, once a week, restarts Hermes). The bots' routines are not in it: read them with `ssh mybox 'for b in capture-bot link-bot organise-bot signal-bot; do hermes -p $b cron list; done'`: the Nightly chat capture (23:00), the nightly Link, Organise and Signal chain (02:00), the weekly link check (04:30, once a week) and the 72-hour brief (every two hours at :45). Pick the first day of the week that is 3 to 6 days from today and has no other weekly job. That keeps the chat facts at least three days old at their first asking, makes the first weekly run the after score (Part H step 2), and gives a second score before Stage 16. Start it at **07:15 box time**, after the night's jobs. A weekly exam can last up to its answers times 5 minutes, plus the retries; with 50 questions that is 150 answers over three runs, so at the 5-minute cut-off it can take most of the day, though most answers take far less. Starting at 07:15 keeps it clear of the night jobs. If the member's crontab shows another job in the morning, pick a clear block and say why in one line. The 72-hour brief overlaps every window; it only writes one file, so leave it.
   Never write the day's name in the crontab comment, the jobs list, the report or anything the member sees: say "once a week".
2. **Put it on the timer**, without disturbing any other line (replace `<d>` with the day number you picked, 0 to 6):
   `ssh mybox '(crontab -l 2>/dev/null | grep -v run-exam.sh; echo "15 7 * * <d> $HOME/brain-exam/run-exam.sh --weekly >> $HOME/brain-exam/run.log 2>&1") | crontab -'`
   **Check:** `ssh mybox 'crontab -l | grep -c run-exam.sh'` prints `1`, and the other lines are unchanged. Then test the weekly message once: `ssh mybox 'hermes send -t telegram "Your brain exam is now on a weekly timer. I will message you here each time it runs."'` exits 0 and the member sees it on their phone.
3. **Add its row to the jobs list, and say why in the rule line**, so Hermes can answer "What runs on its own?" and no later chat "fixes" the exam job:
   `ssh mybox 'python3 ~/second-brain/_System/jobs/add-job-row.py "Brain exam" "Asks Hermes the brain exam questions three times, each in a new session; the answers wait on the box for marking on your laptop, and Hermes messages you when it has run" "Once a week at 07:15, your time" "Your box's timer, asking Hermes"'`
   Then add why to the rule line above the table, once:
   ```
   ssh mybox 'python3 - <<"PY"
   import pathlib
   p = pathlib.Path.home() / "second-brain" / "AGENTS.md"
   t = p.read_text()
   old = "what it does, when it runs and which bot runs it."
   new = "what it does, when it runs and which bot runs it. The brain exam is the one job that asks Hermes itself, because Hermes is what it tests."
   if new not in t and old in t:
       p.write_text(t.replace(old, new, 1))
   print(p.read_text().count(new))
   PY'
   ```
   **Check:** `ssh mybox 'grep -c "^| Brain exam |" ~/second-brain/AGENTS.md'` prints `1`, and the rule script prints `1`. If it prints `0`, the rule line was reworded since Stage 4: add the same sentence after it by hand. The jobs list now holds seven jobs so far. The exam job runs from the box's own timer and only asks Hermes; it is not a helper bot's job, because the bots work from the same brain Hermes is tested on.
4. **Add the chat check to the weekly exam.** Append the c lines from `chat-key.md` to `~/brain-exam/questions.txt` (`c01<TAB>question`, asking for the fact in plain words, never quoting it), lock a new edition (Part C step 6; same day, so `-b`), and send it to the box (Part D step 3, with its check). The first weekly run is 3 to 6 days after the member told Hermes, so the facts are tested from then on.
5. **Marking on the laptop**. The keys stay on the laptop, so marking happens there. If this chat offers scheduled tasks (the Claude app has them), make one for the afternoon of the exam day, once a week, working in the brain folder, with the instruction: "Grade my brain exam." (marking ends by sending the score to the member's phone, Part G step 5) It runs only when the Mac is awake and the app is open. With or without it, the answers wait on the box: the 72-hour brief shows "waiting for marking on the laptop", and "Grade my brain exam." in any chat marks every finished run not marked yet, oldest first: a run whose box folder shows `DONE` and still holds answers (bring it over with Part D steps 7 and 8), or a run on the laptop with no grades file. Grading only marks: it adds no questions.
6. **Report:** "Every week your box asks Hermes the same questions, three times, on its own, and Hermes messages you on Telegram when it has run and again with your score once it is marked. It is on your jobs list, so Hermes knows. Say Grade my brain exam any time after a run, and I'll mark it and add the score to your ledger. On Stages 20 and 27, say Grow my brain exam, and I'll add new questions."

## Part J: grow the exam and keep it honest (sitting 3, then twice more in the first month)

1. **Every real forget becomes a question** ("Add this to my brain exam: Hermes forgot [what it forgot].", for example the new price). Check the brain holds the right fact now; if not, ask the member for it and write it as a dated note with a `source:` line (Part H, not saved). Write one question of the matching type with its key, show it to the member for Keep or Fix, and add it to `~/brain-exam/queue.md`. A real miss is a better question than any you invent.
2. **"Grow my brain exam."** First grade any finished run not yet marked (Parts D step 7 to G). Then:
   - Add the queued real misses first. Then write new questions from notes added or changed since the last edition, in the same five types, with not in the brain still at most one in five, each through the no-brain check (Part B step 5). **Leave out every note on `~/brain-exam/fixed-notes.txt`**: you edited those notes knowing the keys, so a question written from them would judge your own fix. Tag any new question whose key note a fix touched as `fix-touched` anyway, if one slips through a moved or renamed note.
   - Aim for about 50 questions by the end of the first month: the exam grows twice more in that month, so about 15 new questions each time, as many as the new notes can honestly support. Then keep adding toward 100 in month two. Never pad with weak questions to reach a number.
   - **Chat check.** At the first growth, ask the member for two more chat facts (c03, c04), to tell Hermes now. The Nightly chat capture exists from Stage 5, so the chat-fact report shows memory or capture for each: both routes are tested.
   - Show the new keys to the member for Keep all or Fix (Part C), lock a new edition, write in `changes.md` what was added and why, and send the new questions to the box (Part D step 3, with its check). Otherwise the weekly job keeps asking the old edition.
3. **Never drop a question to move the score.** Only a wrong key is retired (step 6). The first 20 stay forever as the trend line; the score on the same questions is the fair comparison.
4. **Three groups on every scorecard after a fix:** the first 20 (the trend line), the questions whose notes a fix touched (`fix-touched`), and the questions added since the last fix from notes no fix touched. The last group is the honest check of whether the brain got better, not only the exam.
5. **Better, worse, or about the same**, always on the same questions: **better** only if the new lowest run is above the old highest run; **worse** only if the new highest run is below the old lowest run; otherwise **about the same**, a change smaller than the normal spread between runs. Say "better" to the member only when this rule says so, even if the average rose a point or two. If the fix-touched questions rose and the questions from untouched notes did not, say so plainly: the fix helped the exam more than the brain.
6. **A faulty key**, found at any time (a note moved, a fact the member says was wrong all along, a not in the brain question the brain now answers): do not edit the locked key. Retire the question in the next edition with one line in `changes.md`, and report the score with and without it until then. A key change after the answers were seen is always shown beside the score on the key as written.
7. **Saturation.** If a type scores full marks three weekly runs in a row, add harder questions of that type (two notes instead of one, a fact that changed twice).
8. Nothing from `~/brain-exam` goes into the brain folder, and the keys stay on the laptop.

## Known fixes

| What you see | Fix |
|---|---|
| Every answer says Hermes cannot reach GBrain | Search is down, not memory. Those answers are unmarked and the run has no score. Run the Dreaming and recall pack's known fixes (Stage 10), then run the exam again. |
| One answer timed out (exit 124) | Not a box fault. The script already asked it again; a second timeout is marked 0, not found. Leave it in the score. |
| Many answers timed out, or answers mention a usage limit | The box was busy, GBrain was paused, or the Claude plan's usage limit was hit. Check the run did not overlap another job (`crontab -l`) and the member's usage meter. Usage-limit answers are unmarked. If fewer than 18 of 20 are marked, there is no score: run it again at a clear time. |
| `hermes: command not found` in `run.log` | The script's Hermes path is wrong. Redo Before you start and the `sed` line in Part D step 1. |
| The check loop ends at once with few answers | It read an old run. Take the run id from `runs/LATEST` and check that folder. |
| The run folder has no `INDEX` result, or it says fail | The script's own search catch-up did not pass. Run the Stage 10 nightly index command by hand, check it, and mark the run anyway; record "search caught up: no" on the scorecard. |
| The note counts on the laptop and box differ | The mirror is behind. Wait, count again, then the Stage 4 pack's mirror known fixes. |
| The memory fingerprints differ | Hermes saved something during the exam. Look at what changed in `~/.hermes/memories`, tell the member in one line, and write "memory changed during the run" in the scorecard. |
| Notes in the Inbox repeat exam questions (any run day) | The Nightly chat capture read exam chats. Redo Part D step 2. |
| Hermes cites its own memory, not a note | Mark it 1 at most (no valid note). If it keeps happening, check the Part A rule line. |
| The run's questions fingerprint matches no edition | The box asked an edited file. Send the newest locked questions again (Part D step 3) and re-run. |
| A later chat wants to move the brain exam job to a bot | Leave it: the rule line and the job's row say why the exam asks Hermes itself (Part I step 3). |
| The score jumps and nothing changed | Runs of the same brain can differ by 10 points; that is why the exam runs three times and averages. Compare ranges on the same questions (Part J step 5), and run it again before believing it. |
| The member wants to see the key | Open `~/brain-exam/key-<edition>.md` for them. It is theirs. It just stays out of the brain folder. |
| No Telegram message after a weekly run or a marking | Hermes's home channel is missing: the member sends `/sethome` to their bot (Stage 3 pack). The run and the score are unaffected. |
| A new chat does not know "my brain exam" | The line is missing from `~/.claude/CLAUDE.md`: redo Part B step 2. |
| Anything else | Read the error, try one fix, tell the member in one plain sentence. Their repair sentence, any time: "Connect to my box and fix Hermes." |

## Jobs

This pack adds one row under "Jobs that run on their own" in `AGENTS.md`: the **brain exam**, once a week at 07:15 box time, on a stage 3 to 6 days after Stage 11 with no other weekly job (Part I), run by the box's own timer and asking Hermes, because Hermes is what it tests. Each weekly run ends with a short Telegram message to the member, and marking sends the score. Its marking happens on the laptop, because the keys never leave it. With the Nightly chat capture from Stage 5 and the five Stage 9 jobs, the list holds seven by the end of Stage 10.

## Report back to the member

Plain words, no paths, no keys:

1. During sitting 1: "I added two rules to your rulebook, for questions about you and your business, and drafted N questions from your own notes, in five types."
2. After sitting 1: "Your exam is locked, and you checked every answer. The answers stay on your laptop, where Hermes can never read them. Hermes now has your two chat facts; they join the exam at its first weekly run."
3. After sitting 2: the Part G step 4 report, with the member's own numbers.
4. After sitting 3: "I fixed these kinds of fault across your brain: <one line each>. Every week your box asks the same questions three times on its own and Hermes messages you; its first weekly run, 3 to 6 days from now, is your after score. Each time Hermes forgets something real, say: Add this to my brain exam. After a weekly run, say: Grade my brain exam. On Stages 20 and 27, say: Grow my brain exam, aiming for about 50 questions by Stage 30."

If something is still stuck, say exactly which step and what you saw, and suggest: "Record the failing step without secrets and consult your host support documentation."
