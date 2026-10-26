# Code Security Auditor

**Agentic Playbook — by Kezy Chong**  
Adaptation owner: Kezy Chong.

A manually requested, bounded security review for a new project or change. It looks for a real trust boundary failure, not just missing best practices. It recommends fixes but does not edit the target.

## Read in this order

1. [Install manually](INSTALL.md) — choose a destination and preserve any existing version.
2. [Skill instructions](SKILL.md) — activation, approval, budgets and safety rules.
3. [Complete method](references/method/workflow.md) — reconnaissance, hunting, coverage critics, independent validation, structured output and reporting.
4. [Attack-class guide](references/method/ATTACK-CLASSES.md) — choose domain companions based on actual boundaries.

Keep this entire folder together. The only skill entrypoint is the root `SKILL.md`; `references/method/workflow.md` is supporting documentation, not another skill. The [manifest](PACKAGE.json) declares this direct folder layout. No other Playbook skill is required.

## Use terms

Read the bundled [use terms](USE-TERMS.md), copied from the collection’s root `REUSE.md`. Personal and internal business use and modification are permitted with the required Kezy Chong credit. Redistribution, resale, publication and rebranding require written permission. Independent third-party rights remain in force. Keep the terms with this standalone folder.

## Requirements

An authorized local source copy; a supported agent host; enforceable wall-clock, total-call and concurrency limits; independent reviewer assignments; a private output folder outside the target; and an already installed Node.js runtime for report validators. Runtime compatibility is not established by this source draft. A missing dependency blocks the relevant step; nothing installs automatically.

## Harmless first use

Ask: “Explain the approval questions for a fictional new notes-export feature. Do not inspect files, launch workers, execute code or start an audit.”

Expected: a draft scope, exclusions, proposed limits, output-folder question and a request for approval. No findings or claims of checks performed.

## What stays off

No live probes, automatic triggers, schedules, hooks, restarts, existing-workflow integration, target edits, deployment or public reports. The default is source-only. Target execution needs separate approval and a verified OS sandbox. Installation and loading are never audit permission.

## Result of a later approved audit

A private report, source evidence, a coverage ledger, independently decided records and clear gaps. Confirmed, needs-validation and rejected records stay distinct. Unreviewed candidates are incomplete work, not findings. “No confirmed findings” is not “safe.”

The complete validator and regression-test source files are included beside the method. This package is a local source draft, not an installed or target-tested service.
