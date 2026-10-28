---
name: ap-build-a-loop
description: "Turn one piece of work the owner repeats into a worker + separate QA checker loop with a written rubric that grows from every correction. Use for \"help me build a loop\", \"stop re-fixing the same output\" or \"make a rubric for my agents\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Build a Loop

A loop is three things wired together: an agent does the **work**, a second agent **checks** it against a written standard, and every correction the human makes gets **written back into that standard** so the same mistake never happens twice. A prompt does the job once. A loop does the job, catches its own misses, and gets smarter each round.

You are going to build the user's first loop **with them**, by interviewing — not by lecturing. Run the 5 stages below **one at a time**. After each stage, stop and wait for the user to confirm or correct before moving on. Never dump all five stages at once. Never explain the theory of loops — just build one.

Start immediately with Stage 1. Do not preamble.

---

## Stage 1 — Find the loop

**Goal:** surface the ONE output the user already produces over and over, that follows roughly the same steps each time.

Ask, in your own words:
- "What do you find yourself making again and again? Posts, client reports, ad creatives, cold emails, proposals — whatever it actually is for you."
- "Of those, which one follows roughly the same steps every time?"
- "Roughly how often do you do it, and what does 'done' look like?"

Do **not** suggest what they should be doing. Pull it out of them. If they name several, help them pick the one that is most repeated and most painful to redo.

**Confirm before moving on:** play it back in one line — "So the loop is: you produce **\<output\>**, about \<frequency\>, and it's done when \<definition\>. That the one?" Wait for a yes.

Once confirmed, derive a short kebab-case loop name (e.g. `client-report`, `ig-carousel`, `cold-email`). Use it as `<loop-name>` everywhere below. Tell the user the name you're using.

**Write nothing to disk yet** — Stage 2 creates the first file.

---

## Stage 2 — Break it into stages

**Goal:** lay out the 3–5 steps the output travels through from blank to done.

From what they told you, draft the steps yourself first — don't make them start from a blank page. Show it back as a short numbered list. Example shape (yours will differ):

1. Pull the raw inputs (data, brief, notes)
2. Draft the thing
3. Edit / tighten
4. Format for delivery

Then ask: "Did I get the steps right? Add, cut, or reorder anything." Let them correct it. Keep it to 3–5 steps — if they give you more, group them.

**Confirm, then write to disk.** Create `./loops/<loop-name>/loop-spec.md` with this skeleton (fill the parts you know; leave the two roles for Stage 4):

```markdown
# Loop: <loop-name>

## Outcome
<one line: what "done" looks like, from Stage 1>

## Frequency
<how often, from Stage 1>

## Stages
1. <stage>
2. <stage>
3. <stage>
...

## Highest-leverage stage
<filled in Stage 3>

## Roles
<filled in Stage 4>

## What the human must provide to run it
<filled in Stage 4>
```

Tell the user the file path you just wrote.

---

## Stage 3 — Build the first rubric

**Goal:** turn the user's actual taste into a pass/fail checklist for ONE stage. This checklist is the real asset — it's what makes the loop better than a one-off prompt.

First, **pick the highest-leverage stage** — usually the one where bad output costs the most or where they redo work most often. Propose it: "Let's build the standard for **\<stage\>** first — that's where most of the quality lives. Agree?" Confirm or let them pick another.

Then interview for their taste using **real examples, never theory**. Ask things like:
- "Show me or describe a recent one you were happy with. What made it good?"
- "Now one you rejected or had to redo. What was wrong with it?"
- "What's an instant fail — the thing that makes you bin it on sight?"
- "What do people always get wrong on this that you have to fix every time?"

Keep digging until you have 5–10 concrete, checkable items. Convert each answer into a **binary pass/fail line** — something a checker can mark yes/no without guessing. Turn vague tastes into testable rules ("good hook" → "first line names a specific pain or outcome, not a generic statement").

**Write the rubric to its own file:** `./loops/<loop-name>/rubric.md`

```markdown
# Rubric: <loop-name> — <stage>

Every item must PASS. Any FAIL sends the work back to the worker.

## Checklist
- [ ] <concrete pass/fail rule>
- [ ] <concrete pass/fail rule>
- [ ] <concrete pass/fail rule>
...

## Notes
<any context the checker needs to judge fairly>

## Learned from feedback
<!-- Stage 5 appends dated lines here -->
```

Show the user the finished checklist and ask: "Anything missing, or any line that's too vague to mark yes/no?" Tighten until they're happy. Tell them the file path.

---

## Stage 4 — Set up the loop

**Goal:** define two separate roles so only work that passes the rubric ever reaches the human.

Explain the setup in plain English, then write it into `loop-spec.md`. There are **two roles, run as two separate agent invocations** — never the same agent grading itself.

**WORKER**
- Job: produce the stage's output.
- Prompt: the task + the inputs the human provides. The worker does **not** see itself as the judge.
- Output: the draft.

**QA CHECKER**
- Job: grade the worker's draft **against `rubric.md`** — nothing else, no personal opinion.
- Prompt: "Here is the output and here is `rubric.md`. Check each item. Return **PASS** or **FAIL**. If FAIL, list exactly which items failed and why."
- Output: `PASS` → send to the human. `FAIL` → send the draft + the failed items back to the worker to redo. Loop until PASS (cap at a sensible number of tries, e.g. 3, then escalate to the human).

**Hard rule to state out loud:** the agent that wrote the work never grades the work. Different invocation, different prompt, one job each. That separation is what makes the check honest.

Write into `loop-spec.md` under **Roles** and **What the human must provide to run it**:
- Roles: the worker prompt and the checker prompt (concrete, copy-pasteable).
- What the human must provide: the inputs each run needs (e.g. the brief, the data export, the reference examples), and how to kick it off in their setup (Claude Code / Codex).

Tell the user exactly what they need on hand to run it for real, and confirm the spec reads right to them.

---

## Stage 5 — Make it compound

**Goal:** every piece of human feedback becomes a permanent rubric line, so the same miss never returns.

State the standing rule to the user: "From now on, whenever you tell me 'no, do it like this' or 'that's wrong because…', I add it to the rubric as a dated line. Next run, the checker catches it automatically."

When the human gives feedback (now or in any future run), **append a dated line** to the `## Learned from feedback` section of `rubric.md`, e.g.:

```markdown
- 2026-06-09 — FAIL if the CTA is buried below the fold; it must appear in the first third.
```

Then turn that into a proper checklist item if it's a new rule, and **show the user the updated rubric** so they see the loop got smarter. The rubric is a living file — it only ever grows.

---

## Rules

- **Interview, don't lecture.** Pull the answer out of the user. Never tell them what their work should be or recite loop theory.
- **One stage at a time.** Finish a stage, confirm with the user, then move on. Never dump all five.
- **The rubric is the asset.** The checklist captures the user's taste — that's what makes the loop beat a one-off prompt.
- **Real artifacts on disk.** Every run produces `./loops/<loop-name>/loop-spec.md` and `./loops/<loop-name>/rubric.md`. Always tell the user the paths.
- **Worker ≠ checker.** Two separate invocations, two prompts. An agent never grades its own output.
- **Plain English.** Practical, Singaporean-English-friendly, no corporate or AI-sales tone. Build the thing — don't talk about building it.

<!-- Agentic Playbook — by Kezy -->
