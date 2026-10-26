---
stage: draft
---
# Execution and continuity — agent instructions

## Detect, then dispatch
Detect the active app, supported model identifiers, effort controls and installed runner versions using read-only inspection.
For Astra, treat Codex 0.153 as a historical compatibility baseline; verify current compatibility locally.
If routine runner setup is needed, the agent handles it within user-authorized setup and preserves rollback.
Never claim a model is available from its marketing name, an old minimum version, or a package installation alone.
Use explicit dispatch settings at every layer. An Astra runner command pattern is:
`codex exec -m ${BUILDER_MODEL} -c model_reasoning_effort=medium --sandbox workspace-write`.
Resolve that identifier against the installed catalogue before using it.
Writable roots must be limited to the assigned output folder, reports folder and scratch space.
Enable network only when the assigned task requires it, such as authorized dependency setup or source retrieval.
Feed a self-contained brief file. A background launch must close stdin (`< /dev/null`) or it can hang waiting for input.
All processes need a bounded deadline. Prefer the workspace's safe-run guard when installed.
Otherwise use the platform's scoped timeout and cancellation mechanism; never kill unrelated processes.
Track the exact run identifier or process identifier, output path, completion status and remaining work.
For long work, divide into checkpoints and monitor only that job. Never install a recurring monitor without authorization.

## Opus and review dispatch
Use a supported runner that explicitly supplies `{model: "${ALTERNATE_BUILDER_MODEL}", effort: "high"}` for Opus builders.
If the Agent tool has no effort control, use a supported workflow runner or verify the effective host setting.
For planner/reviewer review use `{model: "${PLANNER_MODEL}", effort: "high"}` after resolving the actual model.
A supported unattended Claude runner may use `--fallback-model ${FALLBACK_MODEL}`.
Verify current fallback support and effective effort. Do not equate the flag with successful fallback execution.
Use a native planner/reviewer advisor only when exposed by the active provider; never assume a historical beta exists.
One advisor consult per genuine Opus judgment is allowed. Otherwise report the question and stop that item.
An advisor is not the independent final reviewer. Astra builders always escalate judgment to the orchestrator.

## Authentication and read access
If one runner reports no login, inspect an already-selected native connection before asking for another login.
Never switch to a standby account automatically. A native bounded read-only review may be used if already available.
Verify the actual model/provider and read access in the completed receipt, not only the launch request.
A route may not broaden the project, publish, spend, change credentials, or approve itself.
Keep secrets out of environment pass-through and task prompts. Scope file access to the active profile and chosen project.

## Completion and resume
Empty output files or a missing background tracker handle do not prove failure.
Check the tracked process and stable output before retrying. Await completion without tight polling.
Call a route failed only with a real error exit, explicit failure evidence, or completed output with no usable result.
Save that evidence before selecting fallback. Preserve valid completed work byte-for-byte on resume.
Persist the plan, decisions, owned paths, artifacts, done/remaining queue, errors, actual models and run identifiers.
On resume, reread the selected handoff and current decisions. Verify artifacts before reusing them.
If the runner supports journal replay such as resumeFromRunId, resume the unfinished stages from that saved identifier.
Do not assume replay is free or supported; inspect the runner's behavior. Otherwise schedule only the unfinished work.
A missing planner/reviewer verdict remains an open gate, even when an Opus fallback kept the work moving.
