---
name: ap-create-goal-prompt
description: "Build a measurable goal prompt with stopping rules."
metadata:
  version: "0.2.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.2.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Create a Goal Prompt

## Who this is for

A business owner who uses Hermes Agent, the Claude app, or Codex and describes work in plain English.
The agent handles setup, file checks, and technical details. Explain any needed member action in the app.

## Agent setup

Read [Goal contract reference](references/goal-mode.md) before drafting.
This pack needs no extra software for prompt writing. Detect the current agent, its supported goal feature, and the active session.
If setup is missing, handle supported setup yourself and explain the next app action simply.
Never assume a paid service, a separate machine, another skill, or an existing project plan is available.
Do not start a goal merely because the member asked you to write its prompt.

## What this produces

One paste-ready completion contract: the finished result, boundaries, work loop, evidence, and stopping conditions.
Use existing context. Do not launch research subagents or require a separate saved prompt card.
For a large or unresolved task, route to a planning/research pass first.
Use an available researched-prompt skill if installed; otherwise conduct that planning in the current app.
Do not silently invent its missing specification. Return here when the plan is agreed.

## 1. Target and missing information

Choose the target from the request or app context. Use Hermes when the work will run in Hermes, Claude Code in a Claude coding session, and Codex when the context names Codex.
State an assumption if the target is uncertain; do not borrow commands or runtime claims from a different target.
The essential question is what observable check proves completion.
If missing, ask exactly one question: "What check would show you that this is finished?"
Translate the answer into commands and printed results yourself using the project context.
Take scope, working folder, and constraints from context; state assumptions outside the final prompt.
Ask no more than three short questions total. Give a recommendation before any optional choice.

## 2. Fill the contract

Use the full reference skeleton. Every final prompt includes:

- GOAL: one finished outcome and its verification.
- SUCCESS CRITERIA: numbered conditions; all must pass independently.
- CONSTRAINTS: preserved behavior, allowed files, inputs, tools, and services.
- BOUNDARIES: files, folders, tools, systems, and conversations that are in scope.
- STOP WHEN: conditions that require the agent to stop and ask rather than continue.
- WORK LOOP: milestones, small changes, verification, debugging, and progress record.
- COMPLETION AUDIT: current evidence for each criterion.
- BLOCKED STOP: completed work, remaining work, exact blocker, evidence, and smallest next input.

Preserve the ten operating rules in the reference. Use only rules relevant to the agreed task.
For Claude Code, require commands plus their visible results in the conversation.
Its completion judge cannot independently inspect files. Avoid "looks right" or "production-ready" as acceptance criteria.
For Codex, also show evidence in the conversation, including artifact checks when relevant.
Do not assert that Codex shares Claude Code's evaluation internals.
For Hermes, format the contract as a `/goal` headline followed by `verify:`, `constraints:`, `boundaries:`, and `stop when:` lines. Keep the finished outcome in the headline and make every field concrete.
Hermes uses its configured `goals.max_turns` budget and pauses when that budget is exhausted. Do not invent a turn count or treat the budget as a success condition.
Append "Or stop after 20 turns." for Claude Code unless the member supplies another turn bound.
A bound limits a run; reaching it never counts as successful delivery.
For Codex, use only supported goal controls and any bound the member requested.

For Hermes, provide the controls separately from the goal block:

- `/goal status`, `/goal pause`, `/goal resume`, and `/goal clear` manage the active goal.
- `/subgoal <criterion>` adds a required criterion without replacing the goal; list, remove, or clear subgoals only with supported `/subgoal` commands.
- Offer `/goal gate add <command>` only for a deterministic, read-only verification command. Never propose a gate that writes, installs, sends, deletes, restarts, or changes external state.
- Goal contracts, subgoals, and gates stay with their Hermes session and can be restored by resuming that session. Starting a fresh session is not a resume.
- Remind the member that setting a new goal replaces the previous goal. Confirm the observed controls if the installed version differs.

Include both sentences exactly:

> After every step: run all tests and show the output before marking done.

> Completion must be based on fresh evidence from the current workspace, not assumptions, previous summaries, or partial checks.

Define "all tests" as the complete agreed verification set for that step, established before work starts.
At completion, rerun the full required acceptance checks. Do not hide omitted or failing checks.
This reconciles the source's all-tests sentence with its smallest-relevant-check working loop.

Keep lasting project rules and commands in AGENTS.md or CLAUDE.md.
Keep full specifications and milestones in PLAN.md, SPEC.md, or BUG.md.
Reference only files that exist and are available to the executing app.
If an overflow plan must be created, obtain confirmation for that file write unless already authorized.

## 3. Check and return

- One clear finish line; every criterion has a demonstrable check and result.
- No contradictions, vague quality adjectives, or unsupported runtime promises.
- No estimates in hours or days. A turn bound is allowed.
- Count the complete final prompt, including its prefix and newlines. Keep it at most 4,000 characters.
- Warn outside the block when above 3,800 characters.
- Above 4,000: move detail to an authorized plan file and shorten the prompt. Never truncate required scope.
- Show assumptions outside the block. Return one fenced text block followed by the exact character count.
- Replace template slots yourself. Nothing in the final block should need editing before pasting.
- If the app lacks the documented slash command, preserve the contract and explain the supported goal action.
- If no goal feature is available, label it an ordinary task prompt. Do not promise automatic continuation.
- For Hermes, keep controls, subgoals, and gate commands outside the paste-ready goal block so they are deliberate follow-up actions.

## Worked example

Request: "Create a Hermes goal prompt to fix the flaky sign-in test."
Assumption: inspection confirmed the test command, isolated scope, and active Hermes goal support.

```text
/goal Make test/auth pass five consecutive runs of `npm test -- test/auth`, with all five outputs shown.
verify: run `npm test -- test/auth` five consecutive times and show each current result in the final response; here, all tests means that agreed five-run check. After every step: run all tests and show the output before marking done. Completion must be based on fresh evidence from the current workspace, not assumptions, previous summaries, or partial checks.
constraints: preserve test assertions and unrelated tests; fix the underlying cause; do not hide failures.
boundaries: the sign-in implementation, `test/auth`, and directly related configuration only.
stop when: reproduction is unavailable, required access is missing, or the fix would require changing assertions or unrelated behavior; report evidence and the smallest next input.
```

Once the test is stable, a suitable optional read-only gate is `/goal gate add npm test -- test/auth`. Use `/subgoal <criterion>` if a new acceptance condition appears. The configured Hermes turn budget applies, and completion still requires current command output in the conversation.

The reference includes Hermes mechanics plus target-neutral new-app, existing-feature, bug-fix, and file-migration templates that remain usable with Claude Code and Codex.
