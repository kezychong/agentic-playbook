# Loop Spec — <loop name>
<!-- This file is the contract for one loop. It says what the loop produces, the steps it goes through, and who does what. Keep it short. The real asset is rubric.md — this file just points at it. Both files live under ./loops/<loop-name>/. -->

## Outcome
<!-- ONE line. The repeatable result this loop exists to produce. Not a goal, not a vision — the actual thing that lands on your desk again and again. -->
<e.g. "A finished LinkedIn post, ready to paste and publish">

## Frequency
<!-- How often you produce this. -->
<e.g. "3x a week">

## Stages
<!-- 3–5 steps this output goes through from blank page to done. Each step should be something you could hand to a different person. If you have more than 5, you've bundled two loops — split them. -->
1. <blank → first draft. e.g. "Pull the raw idea + source notes into a draft">
2. <draft → shaped. e.g. "Write the hook and tighten to one idea">
3. <shaped → checked. e.g. "Run it against the rubric">
4. <checked → done. e.g. "Format, add line breaks, final read">
5. <optional 5th step>

**Highest-leverage stage (the one this loop builds first):** <which stage number, and why — usually the one where bad output costs you the most>

## Roles
<!-- A loop is two jobs that NEVER overlap. The worker makes the thing. The checker grades it against the rubric and sends failures back. The worker never grades its own work — that's the whole point. Two separate agent invocations, two prompts. -->

### WORKER
- **Produces:** <the exact output of the chosen stage — be specific>
- **Model / tool:** <e.g. Claude Code (Sonnet), Codex, a specific subagent>
- **Gets as input:** <what you hand it — brief, source notes>
- **Prompt:** <the task + the inputs. The worker does NOT judge its own work.>
- **Hands off:** <its draft output, to the checker — not to the human>

### QA CHECKER
- **Grades against:** `./loops/<loop-name>/rubric.md`
- **Model / tool:** <a SEPARATE run/agent from the worker — different session or different model>
- **Prompt:** "Here is the output and here is rubric.md. Check each item. Return PASS or FAIL. If FAIL, list exactly which items failed and why."
- **Returns:** `PASS` or `FAIL` + a short reason per failed item
- **On FAIL:** sends the draft back to the worker with the failed items, worker revises, checker re-grades. Loop until PASS or <max retries, e.g. 3>, then escalate to the human.
- **On PASS:** only then does the output reach you (the human).

## What the human must provide to run it
<!-- The minimum you have to hand over each run for the loop to work without you babysitting it. If this list is long, the loop isn't ready — tighten the brief. Note how you kick it off (Claude Code / Codex). -->
- <e.g. the raw idea / topic in one line>
- <e.g. any source material or links the worker can't invent>
- <e.g. anything non-negotiable for THIS run that isn't already in the rubric>
- <how to kick it off: e.g. "run the worker prompt in Claude Code, then the checker in a fresh session">

## Maturity
<!-- Where this loop is right now. Move the marker as the loop earns trust. The job is to climb from L1 to L4 — at L4 the rubric does the checking and you only spot-review. -->
- [ ] **L1 — Prompt by hand.** You prompt, you check, you fix. No rubric yet.
- [ ] **L2 — Loop exists, human is QA.** Worker runs, but YOU are the checker against the rubric.
- [ ] **L3 — QA agent first-passes.** The QA checker grades first; you only review what it passes.
- [ ] **L4 — Rubric mature, review rare.** Gates catch nearly everything. You spot-check occasionally.

**👉 You are here: <L1 / L2 / L3 / L4>** — <one line on what has to happen to reach the next level>

## Changelog
<!-- Dated, newest at top. One line per change to this loop's shape (new stage, role swap, model change, maturity bump). Rubric edits go in rubric.md's "Learned from feedback" log, not here. -->
- <YYYY-MM-DD> — Loop created. <starting maturity, e.g. L1>

<!-- Agentic Playbook — by Kezy -->
