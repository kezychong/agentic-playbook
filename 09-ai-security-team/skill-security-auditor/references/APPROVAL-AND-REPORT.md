# Approval and report contract

Agentic Playbook — by Kezy Chong

[Skill Security Auditor](../SKILL.md) · [Guide](../GUIDE.md) · [Use terms](../USE-TERMS.md)

## Per-run approval record

Use this as a private form, not a completed authorization. Keep it outside the target, installed skill directories and playbook. Do not fill unknown values optimistically. An approval to prepare documentation is not permission to run the scanner.

```text
Run ID:
New skill import or changed version (not an installed/live target):
Authority to inspect:
Exact original staged directory:
Exact immutable/read-only snapshot directory:
Revision/version and locally recorded content hashes:
Allowed files and exclusions (with reasons):
Data classification; credential-bearing material excluded or run blocked:
Exact private engine executable and verified engine identity:
Exact private output JSON, run record and human report paths:
Exact approved sandbox/supervisor and evidence of enforcement:
Network: deny all, including loopback; no shared sockets:
Filesystem: read-only input/toolchain; private scratch/output only:
Environment: explicit allowlist; empty disposable home; no credentials:
Mode: static-only; zero scanner model calls:
Maximum directory entries inspected during inventory:
Maximum regular files: 100 or a smaller agreed value:
Maximum total source bytes: 5,000,000 or a smaller agreed value:
Maximum bytes per file: 500,000 or a smaller agreed value:
Absolute start/stop time and timezone:
Total wall clock: at most 180 seconds including inventory and closeout:
Scanner allowance: at most 150 seconds, clipped to remaining time:
Closeout reserve: 30 seconds:
CPU, memory, process, disk/scratch and output caps (exact values):
Process-tree termination mechanism and owner:
Maximum concurrent scanner invocations: 1:
Automatic retries: 0:
AI-content-exposure decision, separate from scan consent:
  none / exact approved files or sanitized report portions:
  assistant/provider, recipients, purpose, retention assumptions and byte cap:
Per-run yes: not granted until these details are explicitly accepted:
```

The first proposal should set inventory entry allowance to 200 (including directories and hidden entries); a larger tree needs a new scope decision, not an unbounded walk. Enumerate only within the approved root; do not follow symlinks or open special files. Agree numerical OS quotas before approval: this template deliberately does not pretend a sandbox exists. All preparation of the snapshot must fit the accepted read and time limits. No archives are primary trial inputs; nested content still requires bounded scanner and OS containment.

If approved material unexpectedly contains credentials, stop, avoid sending the value to any model or report, and ask for an owner-prepared sanitized copy. No credential collection, vault access or login is part of this procedure. Do not redact the original in place or silently remove a risky file and call the remaining skill checked.

## Exposure is its own decision

Permission to read files locally with a deterministic process is different from permission to show their contents to Jarvis's model. Source excerpts, path names, report findings and snippets may reveal private information. Before a `read_file` result or scanner output is returned to the assistant, confirm that its approved exposure scope covers it. With no exposure consent, a human runs/reads locally and provides only the separately approved sanitized result. Do not announce an independent AI review if none occurred.

Semantic scanning is not enabled by this form. It requires a separate design/approval beyond this static-only adapter; a scan yes and a report-sharing yes are neither a provider login nor permission to remove `--no-llm`.

## Private outputs from a future approved run

- `run-record.json`: actual approvals, identities, paths, mode, quotas, start/stop times, exit code, supervisor evidence and any stop reason. Adapter-owned record, not an engine-native schema.
- `engine-report.json`: unmodified engine JSON, if produced. Retain privately; no source-brand stripping or relabelling of native evidence. Do not fabricate a report if the engine failed.
- `REVIEW.md`: original Skill Security Auditor human summary, with findings requiring attention and clear coverage gaps. It is not a republished engine report.

Treat all three as private. Evidence should use file/line references and minimal non-secret excerpts only if separately approved. Preserve enough to explain the conclusion without copying entire private skills. Do not publish, sync, upload or install anything as a reporting side effect.

## Decision order

1. **Did it run within authority and containment?** If not started, label `blocked`; if stopped after starting, label `incomplete` or `failed` with the observed cause. Unexpected network/model activity or an escaped quota is a policy failure, never a clean result.
2. **Is the result interpretable?** Record the actual exit code. Missing, malformed, truncated or wrong-target reports are incomplete. Compare target identity and all approved inventory entries with reported coverage; reconcile differences as analyzed, excluded, unsupported or missing. Check target hashes again locally; changes invalidate the run.
3. **Was the requested scope covered?** Require `execution_successful: true` and explicit `analysis_completeness.is_complete: true` for a completed engine scope. Inspect `status`, ledger exceptions, scope exclusions, analyzer statuses, entirely/partially uninspected counts and limitations. A percentage alone is insufficient. Missing required fields are unknown, not true by default.
4. **What was not done?** Record model analysis as not requested, live advisory lookup as unavailable under network denial, and target execution as not performed. Engine completeness is relative to its declared analysis profile and exclusions; it cannot override a gap in the user's requested scope. OSV fallback does not prove dependencies current or safe.
5. **Were findings hidden?** Require no chosen baseline, `suppressed_count: 0` and an empty `suppressed` list for this trial. Unexpected suppression blocks acceptance. Do not generate a baseline, apply an author-shipped baseline, accept all findings, or weaken a rule to improve the score. A later proposed waiver needs a separate human decision per finding with evidence and expiry; no waiver is applied by this adapter.
6. **What does the evidence support?** Separate static pattern/signature/syntax findings from semantic hypotheses, incomplete-analysis warnings and observed runtime effects. No target execution occurred; do not call a static finding a demonstrated exploit. Review high-severity issues even if the aggregate score is low.

## Allowed human-summary labels

| Label | Use it when |
|---|---|
| `blocked — not run` | Approval, engine, sandbox, path or enforceable limits are missing before launch |
| `incomplete` | Timeout, skipped required work, unsupported content, resource limits, denied online lookup relevant to scope, missing evidence or unknown coverage |
| `failed` | Fatal engine error or policy violation; also disclose incomplete coverage |
| `findings need review` | Evidence identifies issues requiring human triage; show completeness separately |
| `bounded static check completed` | All agreed static checks finished with interpretable evidence; disclose exclusions and absent semantic/live/runtime checks |

Never use “clean”, “certified safe”, “fully audited” or “approved to install” as the adapter verdict. Even a completed bounded check may miss malicious behavior. When findings and incompleteness coexist, show both, rather than choosing the friendlier label.

## Handover shape

```text
Skill Security Auditor — [actual label]
Target and version/hash: [actual values]
Mode and actual work: [static; semantic not requested; target not executed]
Execution/coverage: [actual exit, completeness and exceptions]
Findings: [reviewable issues or no findings within the checked scope]
Unknowns: [exclusions, offline advisory limits, unsupported/unfinished work]
Limits: [actual duration/files/bytes; enforcement or violation]
Evidence: [exact private paths; no secrets]
Decision needed: [review, defer, reject, or separately consider installation]
No target installation, suppression, fix or workflow change performed.
```

These brackets are placeholders, not scanner output. Close the run; do not schedule a retry or leave workers running.
