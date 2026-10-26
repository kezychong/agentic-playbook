# Manual installation — Code Security Auditor

Agentic Playbook — by Kezy Chong

[Use terms](USE-TERMS.md): personal or internal business use and modification only; keep the required credit. Redistribution, resale, publication or rebranding needs written permission. Independent third-party rights remain in force.

Adaptation owner: Kezy Chong.

This note describes a future user-approved copy. It does not install or run anything.

1. Read [SKILL.md](SKILL.md), the [method](references/method/workflow.md) and the supporting files. Confirm your host supports folder-based skills, independent workers and enforceable cancellation and budgets.
2. Ask your host to identify its actual active profile, supported skill directory and discovery rules using its current official documentation. Choose project or user scope deliberately. Do not assume that another AI app uses the same directory.
3. Approve the exact destination before copying. Install the complete `code-security-auditor/` folder, with this root `SKILL.md` and all of `references/method/`. Do not install the topic folder or just the Markdown entrypoint. Do not run any included script while copying.
4. If that ID already exists, compare it first. Preserve a rollback copy outside directories scanned for skills. Do not overwrite, bypass a pending approval or modify another profile. Keep one intended active version.
5. Use the host's read-only skill listing to check the loaded ID is `code-security-auditor` and the path is the approved one. Loading should do nothing else. If discovery is cached, consult the host's documentation; do not restart services as part of this skill.
6. Ask for a planning-only explanation with fictional inputs: “Explain your approval questions for a new notes-export feature. Do not inspect a target, create reports, launch workers or run code.” The expected response is a draft plan and approval questions, not an audit result.

## Before any real audit

Separately approve the exact target, source revision, allowed paths, exclusions, private output directory, execution mode, deadline, total worker-call budget and concurrency. Verify enforcement before launching. No approval means no audit. A missing sandbox means no target execution.

## Updating or removing

Stage and compare a new complete folder before any replacement. Preserve personal edits privately and repeat the planning-only check after an approved update. To remove it, approve removal of only the selected installed folder, then check discovery again. This skill creates no schedules, hooks, accounts or connections to clean up. Private reports are separate and must not be deleted as a side effect.

Installation, host compatibility and live behavior have not been tested by preparing this source package.
