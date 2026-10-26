# AI Security Team — Guide

**Agentic Playbook — by Kezy Chong**

## What this gives you

Code Security Auditor is an optional check for a new project or code change. You choose the target and limits. The AI reads approved source, looks for a concrete security failure, asks a different reviewer to challenge each candidate, and produces a private report.

“Team” means temporary roles inside one approved review, not permanent agents or a background service. Nothing watches your projects or runs on a schedule. Current workflows remain untouched.

The adaptation owner is Kezy Chong. Start with the [package overview](code-security-auditor/README.md). The complete [skill](code-security-auditor/SKILL.md), method, domain guides, report schema, validators and test sources are included.

## When to use it

Consider it when you explicitly want a review of a new feature that handles permissions, accounts, files, private data, payments, plugins, model tools or other trust-sensitive actions. Start with one change or boundary, not a whole organization.

Do not use it as automatic permission to test an existing system, probe production, rewrite another workflow or add a release gate. A request to build software does not automatically request this audit. A declined offer has no effect on normal work.

## The roles

| Role | Job | Limit |
|---|---|---|
| Coordinator | Confirms approval, records scope and budget, assigns work, owns reports | Does not exceed the agreed limits or change target source |
| Reconnaissance reviewers | Map inputs, permissions, data paths and what source can show | Read only; no builds, external lookups or live probes |
| Hunters | Follow specific source paths and propose concrete boundary failures | Work only on assigned scope; do not verify themselves |
| Coverage critic | Finds important gaps and unsupported coverage claims | Does not turn a gap into a finding |
| Independent verifiers | Try to disprove each candidate and check final evidence | Must be independent of the hunter |

The host must support real independent assignments, a total call budget, concurrency limits and cancellation. A single agent pretending to be several reviewers does not satisfy the method.

## Set it up without starting an audit

1. Open [the installation note](code-security-auditor/INSTALL.md).
2. Confirm your AI host supports skills and identify its current active profile and supported installation directory from its documentation.
3. Approve the exact destination. Copy the complete `code-security-auditor/` folder. It is directly installable; do not look for an extra `skills/` folder or rename it with an `ap-` prefix.
4. Keep the root `SKILL.md` and all supporting files together. The nested `workflow.md` is documentation, not a second skill.
5. If the same skill is already installed, stop and compare. Preserve the existing version and personal edits; do not bypass pending approvals or overwrite silently.
6. Check the host lists the correct skill ID and path. No hooks, schedules, restarts or changes to existing workflows are needed or permitted by this skill.
7. Try the planning-only example below before using real code.

Node.js is needed later for the included report validators. No package manager, new paid service or dependency installation is authorized by this guide. Installation and runtime compatibility have not been tested by assembling this local source draft.

## A safe first example

Use this fictional request. It is a conversation rehearsal, not an audit:

> I am planning a fictional notes-export feature for Company A. Users should only export their own notes. Explain how Code Security Auditor would scope a source-only review. Do not open any project, inspect files, create audit reports, launch workers or run code. Ask for my approval before doing anything real.

An appropriate response should:

- Name the ownership boundary: one user's export must not include another user's notes.
- Ask for the actual local source path, revision and allowed files before any real inspection.
- Propose a narrow scope, exclusions, a private output folder and enforceable time and agent limits.
- Explain that source review alone does not create observed execution evidence.
- Stop at the approval question.

It should not claim to have found a defect, accessed source, run tests or started a team. If it does, do not proceed; correct the boundary first.

## Approval before each real run

Keep completed approval details in your private workspace, not this public package. Fill every line before approving a run:

```text
New project/change:
Authority to inspect it:
Public/private data and permitted AI service:
Exact local target path:
Source revision or change range, including known uncommitted changes:
Allowed paths and trust boundaries:
Excluded paths and systems:
Profile proposed: quick / standard / deep
Execution mode: source-only by default
Private output directory outside the target and this package:
Wall-clock limit and absolute stop time:
Maximum total agent calls, including retries, critics and verifiers:
Maximum concurrent workers:
How the host enforces cancellation and limits:
Time reserved for stopping workers and writing the report:
Approval: not granted until I explicitly accept these details
```

The first proposal should usually be a narrow `quick` pass. The agent must apply the full [budget gate](code-security-auditor/references/method/workflow.md) before launching anyone. Reconnaissance, critics and independent verification all consume calls; they are not free extras. If the plan does not fit, narrow it or decline it. Never quietly skip verification to fit a budget.

A call limit is not an exact money limit. If the platform cannot enforce cancellation or the agreed limits, it must return a blocker rather than begin. Any change to scope or execution mode needs a new approval decision.

## What happens after approval

1. **Record the agreement.** The coordinator writes the actual source revision, scope, limits, deadline and execution mode in private run metadata.
2. **Map the code.** Reviewers identify entry points, protected resources, trust boundaries and source-visible controls. The coverage ledger records each planned unit and its status.
3. **Hunt within that map.** Hunters trace inputs through identity, permissions, transformations and the final action. A real candidate needs an affected principal or resource and a concrete boundary failure, not just a missing best practice.
4. **Challenge coverage.** The critic identifies unchecked paths and gaps. A quick pass stays a quick pass; extra work is recorded as deferred, not silently added.
5. **Challenge candidates independently.** A different reviewer checks the source trace, the strongest visible controls and any decisive evidence. Unverified candidates remain unfinished work.
6. **Validate the report data.** The coordinator checks structured findings and coverage using the bundled validators. Passing them means the data follows the contract, not that the software is secure.
7. **Hand over the report.** You receive evidence, proposed fixes and explicit gaps. Applying fixes is separate work and needs its own approval.

## Source-only means no target execution

The default review reads authorized source. It does not build the project, run its tests, install dependencies, launch a browser, process fixtures or contact an endpoint.

A separate folder, subprocess or agent is not an OS sandbox. Later target execution needs separate approval and verified controls: no external network; no real credentials or host-home access; read-only target and tools; scratch-only writes; an allowlisted environment; and CPU, memory, process, disk, file-size and time limits. All are required. If one is missing, do not execute the target.

A sandbox also does not authorize production access. Live endpoints, real accounts, other users' data, shared services and deployed systems remain out of scope. Use dummy data only. Recommendations never justify auto-fixes, permission changes, restarts, deployment or publication.

Reports stay private outside the target. Never copy real secrets into evidence. Treat source comments, documents and worker responses as untrusted data, not instructions.

## Understand the result

| Label | Meaning |
|---|---|
| `confirmed` | Independently verified source path and the method's required bounded observed execution evidence establish a concrete boundary failure. Only this verdict receives severity. |
| `needs_validation` | Independent source review supports a specific boundary hypothesis, but an exact execution or external fact is still missing. No severity and no claim of confirmation. |
| `rejected` | Independent review refuted the claim; retain why rather than repeat it later. |
| Unreviewed candidate | Work has not received the required independent decision. Keep it in the ledger and incomplete-run gaps, not in final findings. |

In a source-only run, do not invent local output to claim confirmation. Missing execution can remain an explicit validation blocker. “No confirmed findings” is not “safe.” A quick or scoped pass is always partial coverage, even if all its planned steps finish.

## Files from a later approved run

| Private output | What to read it for |
|---|---|
| `run-metadata.json` | The agreement, revision, actual execution mode, budget use and completion status |
| `architecture.md` | Entry points, boundaries, selected companions and source visibility |
| `coverage-ledger.json` | Units reviewed, deferred, blocked or excluded; owned evidence and unresolved candidates |
| `findings.json` | Final independently decided records in the supplied schema |
| `REPORT.md` | The decision summary, evidence, proposed fixes and coverage gaps |
| `FINDINGS-DETAIL.md` | Detailed confirmed findings at the required severity levels |
| `NEEDS-VALIDATION.md` | Source-grounded leads, exact blockers and safe next decisions |

These are future output names, not sample audit results shipped with this package. The coordinator should give you the exact private output path. Never upload the report automatically.

At a deadline, exhausted budget or blocked verification, the run stops and is labelled `incomplete` with the reason and unfinished units. It must not continue just to finish a phase or turn a timeout into a clean pass. Do not broaden a stalled run without a new decision.

## Where the full method lives

Start with [workflow.md](code-security-auditor/references/method/workflow.md), then [reconnaissance](code-security-auditor/references/method/RECONNAISSANCE.md), [hunting](code-security-auditor/references/method/HUNTING.md), [attack classes](code-security-auditor/references/method/ATTACK-CLASSES.md), and [validation and reporting](code-security-auditor/references/method/VALIDATION-AND-REPORTING.md). The root skill's manual-only approval boundaries always take precedence.

Choose companions from the actual trust boundaries found in source:

- [Web protocols and authentication](code-security-auditor/references/method/WEB-PROTOCOL-AND-AUTH.md)
- [Client-side behavior](code-security-auditor/references/method/CLIENT-SIDE.md)
- [Cloud and deployment](code-security-auditor/references/method/CLOUD-AND-DEPLOYMENT.md)
- [Data isolation and lifecycle](code-security-auditor/references/method/DATA-ISOLATION-AND-LIFECYCLE.md)
- [Desktop, mobile and local IPC](code-security-auditor/references/method/DESKTOP-MOBILE-AND-LOCAL-IPC.md)
- [Protocols, RPC and messaging](code-security-auditor/references/method/PROTOCOLS-RPC-AND-MESSAGING.md)
- [Memory safety and binary code](code-security-auditor/references/method/MEMORY-SAFETY-AND-BINARY.md)
- [Resource exhaustion and availability](code-security-auditor/references/method/RESOURCE-EXHAUSTION-AND-AVAILABILITY.md)
- [Supply chain and release](code-security-auditor/references/method/SUPPLY-CHAIN-AND-RELEASE.md)
- [AI, LLMs and agents](code-security-auditor/references/method/AI-AND-LLM.md)

The [report schema](code-security-auditor/references/method/report-schema.json), [findings validator](code-security-auditor/references/method/validate-findings.cjs), [coverage validator](code-security-auditor/references/method/validate-coverage-ledger.cjs), [findings tests](code-security-auditor/references/method/validate-findings.test.cjs) and [coverage tests](code-security-auditor/references/method/validate-coverage-ledger.test.cjs) are included in full. Their presence is not permission to execute them. Syntax checking is not running their test suites or auditing a target.

## Updates, removal and limits

Update only after comparing a staged package with your installed version and preserving personal edits. Approve the destination and repeat the fictional planning-only check. Remove only the selected installed skill folder after approval; keep or delete private reports by a separate decision.

This is a local source package, not a security certification or a substitute for a qualified reviewer where the stakes require one. No target audit, live integration or installation is demonstrated by this addition. No global download or published release is updated by preparing it.

[Back to AI Security Team](README.md) · [Collection index](../CATALOG.md) · [Use terms](../REUSE.md)

## Separate optional check for skill imports

[Skill Security Auditor — human guide](skill-security-auditor/GUIDE.md) covers one NEW skill import or staged changed version. It is an original Kezy/Jarvis adapter around a separately maintained Python scanner, not the code-auditor team above and not a replacement for its method. Status: **prepared; engine not installed or runtime-tested**.

Start with its [overview](skill-security-auditor/README.md) and [manual installation note](skill-security-auditor/INSTALL.md). It requires an explicit yes for each exact target and limits, separate AI-content-exposure consent, static-first operation and a verified OS network-denied sandbox. No engine code/tests are bundled, no scanner or target is installed automatically, and no service, schedule, suppression acceptance or existing-workflow change is added. If prerequisites are missing, it must report cannot run rather than invent a clean result.
