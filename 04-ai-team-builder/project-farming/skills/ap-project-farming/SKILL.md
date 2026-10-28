---
name: ap-project-farming
description: "A comprehensive project review that checks a project against its own plan and reports the gap honestly, with evidence and a faithfulness score. Use for \"review this against the plan\", \"what's actually built versus what we said\" or \"audit this project\"."
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Project Farming

## Who This Is For

The member using this skill is a smart business owner, not a technical person. They work inside the Claude app or the Codex app and never open a terminal.

The agent reading this skill does all the checking itself: finding the plan, inventorying what is really built, running any status checks, and reading logs. Narrate this in plain words as you go ("checking what's actually running now"). Never hand the member a command or a technical step to run themselves.

Find the plan, find the reality, and report the gap honestly, ranked and backed by evidence. Comprehensive means comprehensive: the whole project gets scanned, not a sample of it. Never cut the scope of the sweep to save tokens.

This is an assessment, not a fix. It reports what it finds. You decide what to act on.

## Method

### 1. Find the plan
The plan is whatever document states intent: a roadmap, a README's promises, a task board, a brief, decision notes, a PRD, or a project instructions file. If more than one plan exists and they disagree, the newest one wins, but flag the conflict rather than picking silently. If there's no written plan at all, say that up front and reconstruct intent from decisions and history before judging anything against it.

### 2. Inventory what's actually there
Check what really exists and runs: files, deliverables, scripts, scheduled jobs, published pages, data. Verify live state, don't trust the documentation. A doc that says "this runs nightly" is a claim, not a fact, until you've seen the schedule or the log confirm it. Open the URLs. Run the status checks. Read the logs.

### 3. Run it as an orchestrated sweep
If ap-orchestrator-astra is installed, plan the review dimensions first, then fan out parallel agents, one per subsystem or area. The orchestrator does the planning and the judgement; cheaper models do the reading. Give each agent a self-contained brief and an output rule ("outcomes, not process: only what the review needs to verify"). Verification is the floor: anything an agent reports back is unverified until you have personally seen the evidence behind it. Never let an unchecked subagent claim into the review.

### 4. Score the gap
For every commitment the plan makes, classify it: **faithful** (built as promised), **drifted** (built differently, on purpose or not), **abandoned** (never built), or **silently replaced** (something else now does the job with nobody deciding that on purpose). Drift isn't automatically bad: sometimes reality turned out better than the plan. Tell "the plan was wrong and reality improved on it" apart from "reality decayed and needs fixing." Also flag anything the plan never asked for: risks, dead weight, or improvements worth having.

### 5. Report
Lead with a verdict line: an X/10 faithfulness score and the one-sentence reason why. Then:
- **Gaps, ranked by impact.** Each one backed by evidence (a file and line, a log excerpt, a URL that returns an error), not just a conclusion.
- **Improvements**, split into quick wins (fixable this week) and structural changes (need a real decision first).
- **Path back to faithful**, the next actions in order, smallest first.

Evidence, then recommendation, then wait. You decide what gets fixed and when. If the ask was "review it and fix the easy stuff", handle the quick wins in the same pass and hold the structural changes for a decision.

## What not to do
- Reviewing the project against what it *should* be in your own head instead of its actual stated plan.
- Writing "everything looks good" with no receipts. A review that finds nothing checked nothing.
- Sampling three files and calling it comprehensive.
- Quietly fixing things mid-review. The deliverable here is the assessment, not the fix.


<!-- Agentic Playbook — by Kezy -->
