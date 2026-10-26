# AI Security Team

**Agentic Playbook — by Kezy Chong**

Two optional, manual security reviews: Code Security Auditor for a new project or code change, and Skill Security Auditor for a new skill import or staged changed version. The code auditor uses focused reviewers and independent verification; the skill auditor provides original Kezy/Jarvis instructions around an external Python scanner. Neither is an always-on service.

## Start here

1. Read the complete [guide](GUIDE.md).
2. Try the guide's fictional planning-only example. It does not open a target or launch an audit.
3. Read [Code Security Auditor](code-security-auditor/README.md) and its [manual installation note](code-security-auditor/INSTALL.md).
4. Copy the complete `code-security-auditor/` folder only after approving a destination. Do not overwrite an existing version blindly.

## Included packages

- [Code Security Auditor](code-security-auditor/README.md) — skill ID `code-security-auditor`; adaptation owner Kezy Chong.
- [Package manifest](code-security-auditor/PACKAGE.json).

- [Skill Security Auditor](skill-security-auditor/README.md) — skill ID `skill-security-auditor`; adapter owner Kezy Chong. Original instructions, not a renamed or bundled scanner. Status: **prepared; engine not installed or runtime-tested**.
- [Skill auditor human guide](skill-security-auditor/GUIDE.md), [manual installation](skill-security-auditor/INSTALL.md) and [package manifest](skill-security-auditor/PACKAGE.json). Read these separately from the code-auditor setup above. Copy nothing until the exact destination is approved; name conflicts stop for a decision.

Each standalone adapter keeps its requested skill ID and is copied from its named folder; unlike the older collection packages, there is no extra `skills/ap-…/` nesting. Copying Skill Security Auditor does not install its external engine.

## Boundaries

Manual approval for each target, scope, deadline and agent budget. Source-only unless an OS sandbox is independently verified and execution is separately approved. No live targets, schedules, hooks, restarts, automatic fixes or changes to existing workflows. Loading the skill starts nothing.

Local source draft. Package syntax and link checks are not audit results, runtime tests or proof that a target is safe. The full method, report schema, validators and test sources are included; no target audit or installation is part of this addition.

The preceding team/method description applies to Code Security Auditor. Skill Security Auditor ships documentation only, with no engine code or tests. Its static-only invocation still requires verified OS network denial because `--no-llm` does not disable online dependency checks. It requires a per-run yes, exact paths, time/file/byte limits, one scanner invocation at a time, no automatic retries and separate AI-content-exposure consent. Missing containment means cannot run; incomplete work never becomes a clean verdict. No automatic target installation or suppression acceptance.

[Collection index](../CATALOG.md) · [Start here](../START-HERE.md) · [Use terms](../REUSE.md)
