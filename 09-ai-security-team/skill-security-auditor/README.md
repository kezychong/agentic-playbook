# Skill Security Auditor

**Agentic Playbook — by Kezy Chong**

An optional, manual review for one new skill import or staged changed version. Kezy's original Jarvis adapter sets the approval, privacy, containment and reporting rules around an external Python scanner. It is **not a renamed copy of that software**, and Kezy does not claim authorship of the external engine.

**Status: prepared; engine not installed or runtime-tested.**

## Start here

1. Read the [human guide](GUIDE.md) and try its fictional planning-only example.
2. Read the [skill instructions](SKILL.md), [source-verified interface](references/ENGINE-INTERFACE.md) and [approval/report contract](references/APPROVAL-AND-REPORT.md).
3. For a future user-approved adapter copy, follow [manual installation](INSTALL.md). A source checkout is not an installed scanner, and copying this adapter does not install one.

## What is included

- Original adapter instructions, human guide, installation note and two interface/safety references.
- [Package manifest](PACKAGE.json) and an unchanged copy of the collection [use terms](USE-TERMS.md).
- No engine code, engine tests, dependencies, runtime scripts, model configuration or service host.

The external engine's source and original licence remain private outside this package. The collection terms cover the original adapter only, not the independent scanner or other third-party software. Private provenance is maintained separately; no original software is relabelled or relicensed here.

## Boundaries

Explicit yes for each exact target, paths, time/file/byte caps and private output. Static-first, one scanner invocation at a time, no automatic retries, no credentials, no live sources, no target execution. AI content exposure needs its own consent, even if only Jarvis reads the report.

**`--no-llm` is not offline.** The source-inspected interface lacks a dedicated OSV-disable or universal network-off switch. A verified OS network-denied sandbox is mandatory; without it, the adapter must report **cannot run**. No sandbox or installed engine is supplied or assumed.

No automatic installation after scanning, no suppression acceptance, no fixes, hooks, schedules, workflow changes or restarts. A low score is not a safety certificate. Incomplete work stays incomplete.

For code changes rather than skill imports, use the separate Code Security Auditor package in the AI Security Team topic. Its method is unchanged by this addition.
