---
stage: shipped
---
# Goal contract reference

This is a rebuilt practical playbook, informed by a proven autonomous-task prompting framework.
Read the whole reference before drafting. It travels with this pack and has no sibling-skill dependency.

## 1. Mechanics and evidence limits

Documentation checked 2026-11-07. Verify the member's actual app and installed version before giving activation instructions.

Hermes Agent: `/goal <text>` creates or replaces the standing objective and starts its first turn. A structured inline contract uses the first line as the outcome and recognizes these public field forms:

```text
/goal <one observable finished outcome>
verify: <current command, inspection, or artifact evidence that proves it>
constraints: <behavior and data that must not change>
boundaries: <files, folders, tools, systems, and conversations in scope>
stop when: <conditions that require user input or a new decision>
```

The lifecycle controls are `/goal status`, `/goal pause`, `/goal resume`, and `/goal clear`. `/goal show` displays the active contract. A new goal replaces the old one.
`/subgoal <criterion>` adds another required criterion while preserving the original goal. With no argument it lists criteria; `remove <N>` and `clear` manage them.
`/goal gate add <command>` adds an exit-code quality gate. This pack recommends gates only when the command is deterministic and read-only; never turn an install, write, deletion, restart, message, publication, or external-state change into a gate.
Hermes uses the host's configured `goals.max_turns` value, then pauses rather than declaring success. `/goal resume` starts another configured budget window.
The goal contract, subgoals, and gates are stored with the session and return when that same session is resumed. They are not a global goal shared by unrelated or fresh sessions.
The judge evaluates the latest response, so the completion report must display fresh evidence from the current workspace, such as command output, a file excerpt, or an artifact inspection. A claim without visible proof is not enough.
Source: [Hermes Agent persistent goals](https://hermes-agent.nousresearch.com/docs/user-guide/features/goals).

Claude Code: one goal per session. A new condition starts work; a replacement replaces the current condition.
The condition limit is 4,000 characters. A separate small model reads conversation evidence, without running tools.
It can return unmet, met, or impossible. The default evaluation model depends on the provider.
Use command-plus-visible-result criteria. A turn bound can be part of the condition.
The status command is `/goal`; clearing uses `/goal clear` or `/clear`.
Resume retains an active condition but resets usage and turn baselines.
Background work can defer evaluation. Goal support and hook-policy restrictions depend on the installed version.
Agents can use supported non-interactive execution when separately requested; members stay in their app.
A goal does not grant additional permissions. Check the current requirements before troubleshooting.
Source: [Claude Code goal documentation](https://code.claude.com/docs/en/goal).

Codex: official command documentation describes a persistent goal on the active chat.
It documents `/goal <objective>`, view, edit, pause, resume, and clear, and a 4,000-character objective limit.
The current desktop tool interface may expose different controls. Use the observed supported interface.
Do not infer a hidden evaluator from Claude Code's design or claim artifacts automatically prove completion.
Source: [OpenAI developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli).

These checks concern documented mechanics. They do not prove the member's installed version or a successful run.
An installed launcher or package alone does not establish the desktop app's available goal controls; verify them in the active app.

Across Hermes, Claude Code, and Codex, keep the outcome, proof, constraints, boundaries, and blocked-stop conditions even when the target uses different labels or controls. Status/view, pause, resume, and clear are shared lifecycle concepts, not permission to assume identical command syntax or evaluator internals.

## 2. Complete task contract

```text
GOAL
One end state, verified by stated checks.
VERIFY
Fresh commands, observations, or artifact checks that demonstrate the end state.
CONTEXT
Project, stack, current state, working folder, audience, known constraints.
SUCCESS CRITERIA (ALL MUST BE TRUE)
Numbered, independent checks. Include operation without the defined errors and visible proof.
CONSTRAINTS
Behavior, data, interfaces, and approved resources that must be preserved.
BOUNDARIES
Files, folders, tools, systems, accounts, and conversations that are in scope.
STOP WHEN
Decisions, missing access, unsafe actions, or scope changes that require the member.
OPERATING RULES
Plan first; work autonomously within scope; verify; debug; use relevant available tools;
no unfinished placeholders; record progress; stay on goal; handle blockers; audit before stopping.
QUALITY BAR
Specific measurable limits or checks. Put subjective style guidance in project rules.
WORK LOOP
Inspect -> implement one milestone -> verify -> fix -> record -> next milestone.
FINAL DELIVERABLE
Evidence for each criterion; changed files; how to run, test, or deploy where relevant;
decisions and known limitations.
COMPLETION AUDIT
Rerun every required acceptance check in the current workspace and map results to criteria.
BLOCKED STOP
Completed work, remaining work, exact blocker, evidence, attempted checks, smallest next input.
```

Replace every slot with known facts before returning a final prompt.
For a business task, a check may be a reconciled row count or a verified output file rather than software tests.
The agent must surface those results just as clearly.

## 3. Ten operating rules

1. Plan first: inspect the agreed specification and identify real verification commands.
2. Work autonomously: complete authorized milestones without repeated routine permission requests.
3. Self-verify: inspect outputs after each step and rerun all required checks at completion.
4. Debug yourself: investigate failed checks; do not leave fixable failures for the member.
5. Use every relevant available tool: choose tools that can demonstrate the outcome, within current permissions.
6. No placeholders: required features must work; mark external blockers explicitly.
7. Progress log: keep milestones, decisions, checks, and remaining work in a resumable record.
8. Stay on goal: avoid unrelated redesign, extra features, or changes beyond the stated boundaries.
9. If blocked: record evidence and continue independent authorized work; report the unresolved blocker clearly.
10. Check success before stopping: evaluate every criterion, not just the most recently finished subtask.

A real execution host can have stricter rules for when a goal is marked blocked. Follow that host's rules.
Never mark completion merely because the run reached its turn or usage limit.

## 4. Failure prevention

Use these two lines in every contract:

"After every step: run all tests and show the output before marking done."
"Completion must be based on fresh evidence from the current workspace, not assumptions, previous summaries, or partial checks."

Set the verification scope before work. Use relevant checks after changes and the full acceptance suite at the end.
This is a practical guard against unsupported completion; no measured improvement rate is claimed.
For Hermes, put the concrete proof check in `verify:` and require the final response to show its current result. A read-only gate strengthens this check but does not replace the visible evidence report.
For drift, keep one coherent outcome and a supported stopping bound.
For wasted usage, baseline the checks and keep changes reversible using the project's normal version-control workflow.
After a compressed conversation or resume, read the plan and progress record and rerun checks.

## 5. Put information in the right file

The goal carries the outcome and proof requirements.
AGENTS.md or CLAUDE.md carries durable project layout, setup, test commands, conventions, and do-not rules.
PLAN.md carries the full scope, milestones, acceptance checks, exclusions, and recovery information.
SPEC.md can hold a feature description. BUG.md can hold reproduction details.
PROGRESS.md records completed milestones, command results, decisions, blockers, and remaining work.
Use the project's existing equivalents when available. Do not create redundant records.
First agree the plan; then create the goal against that plan. An unfinished planning request is not a final goal.

### Project-rules template

```markdown
# Project rules
## Purpose and layout
[What the project does and where its main files live.]
## Setup and verification
[Actual install, run, lint, typecheck, build, and test commands discovered by the agent.]
## Constraints
[Preserved behavior, boundaries, and conventions.]
## Done
[Required checks, main-flow verification, and review evidence.]
```

### Plan template

```markdown
# Plan
## Purpose and audience
[What the finished result lets the intended user do.]
## User flows
[Actions and observable outcomes.]
## Milestones
[Each milestone, its acceptance check, and evidence to capture.]
## Constraints and exclusions
[What stays unchanged and what is outside this task.]
## Recovery
[How to resume safely without duplicating completed changes.]
## Final acceptance
[Exact checks and required evidence.]
```

## 6. Reasoning guidance

Preserve the distinction between reasoning-capable models and ordinary models when choosing prompt detail.
For reasoning-capable models, prefer a direct objective and verification criteria; do not demand hidden chain-of-thought.
For other models, give an explicit external plan, milestones, and concise checkable explanations when useful.
The relevant capability is structured work and verification, not access to private reasoning.
The benefit of extra reasoning instructions varies with model and version; avoid universal performance claims.
If version-specific wording or benchmark gains matter, verify official documentation or original research first.
Do not carry historical percentages or model-specific wording rules forward as current facts.

## 7. Rebuilt use-case templates

These are drafting templates. Resolve file references, commands, and scope before delivering the final prompt.
Include the two exact evidence sentences from section 4 in every final version.

### New app

```text
/goal Deliver the working v1 in @PLAN.md, following @AGENTS.md.
verify: rerun every acceptance check in @PLAN.md; show current setup, build, start, test, main-flow, and diff-review results.
constraints: preserve the agreed stack, interfaces, data, and service choices; do not leave required placeholders.
boundaries: the files, tools, and services authorized by @PLAN.md and @AGENTS.md.
stop when: a required service or credential is unavailable, the plan needs a product decision, or completion requires work outside those boundaries; report evidence and the smallest next input.
```

### Existing feature

```text
/goal Implement @SPEC.md while preserving public behavior outside its stated changes.
verify: demonstrate each specified flow; rerun relevant tests and final project checks; show a current regression-focused diff review.
constraints: preserve public behavior outside @SPEC.md and follow existing project rules and patterns.
boundaries: affected implementation files, nearby tests, and directly related documentation or configuration.
stop when: the specification conflicts with current behavior, required access is missing, or a change outside these boundaries is necessary; show evidence and request the smallest decision.
```

### Bug fix

```text
/goal Fix @BUG.md and demonstrate that its reproduction no longer fails.
verify: show the original reproduction passing, the regression check, and all required current project-check results; report the cause, changes, proof, and remaining risk.
constraints: preserve unrelated behavior and existing assertions; change one supported hypothesis at a time.
boundaries: the failing path, its direct dependencies, regression test, and necessary documentation only.
stop when: the issue cannot be reproduced, required access or data is missing, or the fix requires unrelated behavior changes; show evidence and name the smallest missing input.
```

### File migration

```text
/goal Complete the approved file migration in @PLAN.md and prove every source has the intended destination.
verify: compare final source and destination inventories, counts, paths, required metadata, and content checksums; show evidence for every planned item and every exception.
constraints: preserve content and required metadata; follow the approved destination and collision rules; do not alter unrelated files.
boundaries: only the sources, destinations, tools, and batches named in @PLAN.md.
stop when: an unplanned collision, unexplained mismatch, permission problem, or destructive exception appears; preserve the current state and report the exact items and evidence.
```

## 8. Better finish lines

Instead of "improve performance", name a benchmark threshold and the correctness checks that must remain green.
Instead of "build my app", point at an agreed plan and its acceptance checks.
Instead of "keep going until perfect", list observable requirements.
Instead of an unrelated backlog, choose one coherent release or milestone.
Instead of "production-ready", specify the needed deployment, performance, security, and monitoring checks.

## 9. Final evidence table

```markdown
| Criterion | Current command or observation | Result | Status |
|---|---|---|---|
| [Required outcome] | [Actual check and output location] | [Observed result] | [Pass or unresolved] |

Changed files: [actual files]
How to run or inspect: [supported steps]
Decisions: [material choices]
Known limitations: [remaining risk or unavailable checks]
```
