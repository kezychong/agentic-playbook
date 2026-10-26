# Skill Security Auditor — Human guide

**Agentic Playbook — by Kezy Chong**

**Status: prepared; engine not installed or runtime-tested.**

## What you are getting

A manual safety-review procedure for a skill you are considering importing, or a new version staged separately from the one already in use. You choose one local target and approve a bounded check. The result helps you decide what needs review; it does not install, repair or certify that skill.

Kezy's contribution is this original adapter and human workflow for Jarvis. The engine behind it is independently authored Python scanner software, **not an existing prompt skill converted by changing its name**. Its source and original licence stay outside the playbook. This package includes instructions and references, not scanner code or tests. Collection [use terms](USE-TERMS.md) apply to the adapter, not ownership of the external software.

Use the separate Code Security Auditor for new application code changes. Skill Security Auditor does not replace that method, launch its reviewer team or add an always-on security layer to Jarvis.

## The three decisions stay separate

1. **Copy the adapter?** A future manual installation puts instructions in an approved host/profile folder. Name conflicts stop the copy until you decide what to do.
2. **Run one bounded scan?** You approve the exact staged target/version, private output paths, scanner mode, containment and limits for this run only. This does not install the target afterward.
3. **Expose content to AI?** You separately approve what target/report content Jarvis or any model may see. A local static scan is not permission to upload source or paste a report into a model conversation.

Preparing this package grants none of those decisions automatically. A no or silence to the optional scan offer means skip it without changing existing work.

## Static checks are not model review

| Check | What it can tell you | What it cannot establish |
|---|---|---|
| Deterministic static checks | Matches in patterns, parsed code, signatures and bounded reconstructions | The target's actual runtime behavior, absence of unknown attacks, or harmless intent |
| Dependency fallback data under network denial | Some known issues represented in bundled data | Current vulnerability coverage or that an unlisted dependency is safe |
| Semantic/model analysis | Contextual hypotheses about intent or description versus behavior | Deterministic truth, confidentiality without a reviewed provider policy, or proof of execution |

The runnable mode in this adapter is **static-only**. Model checks are not enabled by the guide. Asking for deeper semantic review would require a separate approved design and data-exposure decision; removing one flag is not sufficient.

Even static scanning executes the scanner itself, so its parsers and dependencies still need containment. It does not authorize execution of the target's scripts, tests, installers or examples.

## Why offline needs more than a flag

The source-verified `--no-llm` option turns off model analysis. It does **not** turn off online OSV dependency lookups. Those lookups can disclose package coordinates. The inspected CLI has no dedicated OSV-disable or universal network-off option. Tracing integrations and dependencies also mean source inspection is not proof of total network silence.

A later run therefore needs an independently verified **OS network-denied sandbox**, including denial of loopback and shared network sockets. The scanner gets no credentials, no host-home access, a minimal environment, read-only target/toolchain and private scratch/output only. A virtual environment, another folder or a second agent is not a sandbox. If those controls are missing, Jarvis must say **cannot run**.

Network denial can leave a dependency check incomplete. That is an honest limitation, not a reason to enable networking, retry automatically or call the result clean.

## A safe first example — planning only

Paste this fictional request:

> I am considering a fictional “Meeting Notes Formatter” skill, version B. Explain how Skill Security Auditor would ask me to scope a static-only review. Do not open any target, inspect real files, create reports, install anything, launch a scanner, call another model or change workflows. Stop at the approval questions.

The response should ask for one staged local path and version, authority, exclusions, private report location, enforceable limits and sandbox evidence. It should separately ask whether any real content may enter AI context. It should explain that the engine has not been installed or runtime-tested here. It should not invent findings or claim a scan occurred.

## Prepare a real run without starting it

Read [manual installation](INSTALL.md) if you want the adapter available in your host. Engine setup is a different future task: source presence alone does not mean a working scanner exists. No installation or dependency command is authorized by this guide.

Use the complete [approval form](references/APPROVAL-AND-REPORT.md). Before any real inspection or scan, agree:

- Exact new/changed skill, original staged path, immutable snapshot path and revision/content identity. Never scan the currently installed/live folder.
- Allowed files, exclusions and data classification. No credentials or live sources; no URL/Git acquisition or transitive fetching.
- Exact approved external executable, private JSON/report paths, and no symlink or special-file ambiguity.
- OS sandbox/supervisor evidence and explicit CPU, memory, process, scratch and output quotas.
- First-trial limits: **100 regular files, 5,000,000 total source bytes, 500,000 bytes per file, 180 seconds total**, one scanner invocation, no automatic retries. Propose at most 200 metadata entries during inventory, counting hidden entries and directories. Reserve 30 seconds for stopping/reporting; the scanner gets no more than 150 seconds or the shorter remaining allowance.
- An absolute stop time and process-tree cancellation. Engine internal analyzer parallelism is not controlled by a CLI single-worker flag; one invocation does not mean one thread.
- Separate permission for exact content/report portions to be exposed to AI. Without it, a human reads results locally and shares only separately approved sanitized information.

These are proposal limits, not magic command flags. The source-verified CLI does not implement this adapter's file/byte or worker caps. An existing trusted host/sandbox must enforce them, or the run is blocked. If the inventory is larger, incomplete or mutable, stop; don't quietly scan only the convenient files.

Only an explicit yes to the completed plan authorizes that run. Changing the target, mode, limits or version requires a new yes.

## What an approved run would do

1. Record the accepted scope and containment privately. Inventory and locally hash the bounded immutable snapshot without exposing raw content unnecessarily.
2. Verify the external engine identity and executable. If absent or mismatched, stop rather than install anything automatically.
3. Invoke the [documented static-first command](references/ENGINE-INTERFACE.md) once, inside the verified OS sandbox and deadline supervisor. This package supplies neither a launcher nor a service.
4. Stop on timeout or exhausted limits, preserve actual errors and do not retry. No target code executes. No live dependency service, model endpoint or remote target is authorized.
5. Inspect actual JSON fields and evidence using the [report contract](references/APPROVAL-AND-REPORT.md). Keep findings, omissions, offline lookup limits and failures visible. Target/report text is untrusted data, never instructions to Jarvis.
6. Deliver an original human summary with the exact private evidence path. Leave installation, fixes and any later review as separate human decisions.

No real run was performed to prepare this guide. The steps above are a future procedure, not a record of successful execution.

## Read the result in the right order

**First, execution and completeness. Then, findings. Last, the score.**

- Was the expected target scanned within the approved time, file and byte limits? Did it stay unchanged?
- Is `execution_successful` explicitly true? Is `analysis_completeness.is_complete` explicitly true? Are required analyzer statuses and coverage records present?
- What do ledger exceptions, scope exclusions, unsupported files and offline advisory gaps leave unknown? A report may be complete under the engine's narrow profile while not covering everything you care about.
- Was model analysis actually disabled? Was anything suppressed? No baseline is approved for this trial.
- What exact issue, file and line support each warning? A static match is not proof that an exploit was executed. Keep hypothesis and observed evidence separate.

A `0` exit, low score, `SAFE` recommendation or high coverage percentage is not installation permission. A report that is absent, truncated or missing required fields is incomplete, not empty of findings. The adapter uses labels such as **blocked — not run**, **incomplete**, **failed**, **findings need review**, or **bounded static check completed**, always with the actual scope and limitations.

## What you receive later

Private `run-record.json`, the unmodified `engine-report.json` if produced, and an original `REVIEW.md`. Raw engine output can contain its native software identifiers; retain that evidence privately rather than relabelling it as Kezy's software. The human-facing summary uses **Skill Security Auditor** and distinguishes the adapter from the engine.

No real secrets belong in excerpts. Do not upload these artifacts automatically. A finding does not authorize a fix, and a low score does not authorize installation. Do not auto-accept baseline suppressions or adopt a skill author's waivers. No daemon, optional service host, hook, schedule, restart or runtime-setting change belongs to this package.

## Current limits and next decision

Only documentation/interface inspection has been done. Runtime compatibility, detection accuracy, dependency installation, sandbox availability and host discovery are unverified. This is not a review of every file in the external engine. Full relevant-file reads and source identities are recorded in private provenance, not shipped with the adapter.

If you choose to proceed later, start with the fictional rehearsal, then separately decide whether to prepare an engine and containment environment. If you stop here, existing workflows are untouched.

[Package overview](README.md) · [Skill instructions](SKILL.md) · [Manual installation](INSTALL.md) · [Use terms](USE-TERMS.md)
