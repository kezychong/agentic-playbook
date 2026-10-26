---
stage: shipped
---
# Goal contract reference

This is a rebuilt practical playbook, informed by a proven autonomous-task prompting framework.
Read the whole reference before drafting. It travels with this pack and has no sibling-skill dependency.

## 1. Mechanics and evidence limits

Documentation checked 2026-09-09. Verify the member's actual app before giving activation instructions.

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

## 2. Complete task contract

```text
GOAL
One end state, verified by stated checks.
CONTEXT
Project, stack, current state, working folder, audience, known constraints.
SUCCESS CRITERIA (ALL MUST BE TRUE)
Numbered, independent checks. Include operation without the defined errors and visible proof.
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
Success: every required acceptance criterion is implemented; documented setup, build, and start checks pass;
the main user flows are demonstrated; relevant tests pass; the final diff is reviewed.
First identify actual project commands and baseline their results. Add the smallest suitable test setup if missing.
Work milestone by milestone with small changes and a current PROGRESS.md.
Use browser or automated flow checks where relevant. Preserve the agreed stack and service boundaries.
At completion, rerun the required suite and map every acceptance criterion to its current evidence.
If blocked, report completed work, remaining work, blocker, evidence, attempts, and smallest next input.
```

### Existing feature

```text
/goal Implement @SPEC.md while preserving public behavior outside its stated changes.
Read project rules, inspect affected files and nearby tests, and follow existing patterns.
Success: each specified flow works; relevant tests and final project checks pass; the diff is reviewed for regressions.
Work through discovery, implementation, tests, flow verification, and final audit. Record results in PROGRESS.md.
Before completion, list every acceptance criterion with fresh proof. Missing proof remains unfinished or explicitly blocked.
```

### Bug fix

```text
/goal Fix @BUG.md and demonstrate that its reproduction no longer fails.
First reproduce the issue or document why reproduction is unavailable. Identify the cause before patching.
Change one hypothesis at a time. Preserve unrelated behavior and existing assertions.
Add a regression check where practical and run the relevant verification after each change.
Success: reproduction passes, required project checks pass, and the report includes cause, changes, proof, and remaining risk.
If reproduction remains unavailable, gather evidence and name the smallest missing input.
```

### File migration

```text
/goal Complete the approved file migration in @PLAN.md and prove every source has the intended destination.
Before changes, record the source inventory, destination rules, and collision policy.
Preserve contents and metadata required by the plan. Do not change unrelated files.
Verify counts, paths, and content checksums after each batch. Record completed batches so recovery does not repeat work.
Success: every planned item has verified destination evidence; no unexplained loss, collision, or duplicate remains.
Report unresolved items with their evidence. Never treat a partial batch as the completed migration.
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
