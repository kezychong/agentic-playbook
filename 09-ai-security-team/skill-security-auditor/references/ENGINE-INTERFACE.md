# External engine interface — Skill Security Auditor

Agentic Playbook — by Kezy Chong

[Use terms](../USE-TERMS.md) · [Skill](../SKILL.md) · [Human guide](../GUIDE.md)

**Source-inspected interface version: 2.13.1. Status: prepared; engine not installed or runtime-tested.** These are original interface notes, not copied engine documentation or a replacement licence. The scanner is independently authored third-party Python software. Its source, authorship, exact commit, original licence and file-level evidence are retained privately outside this package. No scanner source, test suite, installed environment or runtime script is included here.

## Resolve the executable, do not assume installation

Record the approved engine-source directory privately; this public placeholder is not an installation:

```text
<PRIVATE_ENGINE_SOURCE_DIR>
```

This is a source checkout, **not a promised executable path**. During a separate approved setup, the operator must record the exact absolute executable path and installed engine identity privately. `ENGINE_EXECUTABLE` below means that verified external entrypoint; it is not an alias, a renamed binary or a command shipped by this package. Do not guess a virtual-environment path, use a global executable discovered on PATH, run a package manager or import the source to make the example work.

The source metadata requires Python `>=3.12,<3.15` and additional dependencies. A Python interpreter alone is insufficient. Engine/dependency preparation is separate work and requires approval. Keep its original source and licence intact outside the playbook. Never substitute collection terms for its software licence.

## Static-first invocation — only inside verified containment

First satisfy the complete sandbox, path, quota and approval gates in [SKILL.md](../SKILL.md). The following is the **inner command**, not a complete sandbox launcher. It must never be pasted into an unrestricted host shell. No engine invocation, including help/version, was performed while preparing this package.

Resolve these values explicitly in the approved run contract:

- `ENGINE_EXECUTABLE`: approved absolute external entrypoint, read-only in the sandbox.
- `TARGET_DIR`: approved immutable local directory for one new/changed skill; no URL, archive or collection root.
- `OUTPUT_JSON`: fresh absolute private JSON path outside the target and playbook. No symlink ancestors or existing destination; parent must already be approved and writable/readable as required by the runtime.

```sh
"$ENGINE_EXECUTABLE" scan "$TARGET_DIR" \
  --no-llm \
  --format json \
  --output "$OUTPUT_JSON" \
  --fail-on-incomplete \
  --fail-on-findings
```

In Hermes, execute only through `terminal` under the operator's approved OS sandbox/supervisor, with a foreground timeout within the accepted deadline. A `terminal` timeout by itself does **not** establish network isolation, process-tree cancellation or byte/memory enforcement. No sandbox wrapper is supplied or assumed available. If an existing verified launcher cannot satisfy the contract, return **cannot run** rather than improvise one.

## What the pinned CLI actually accepts

The scan entrypoint's source declaration, not a guessed command, establishes these options:

| Interface | Source-observed behavior | Adapter policy |
|---|---|---|
| `scan INPUT` | Positional path or supported remote input | One approved local directory only |
| `--no-llm` | Sets requested/enabled model analysis false; default is model-enabled | Always present |
| `--format json` | Selects JSON; terminal, markdown and sarif also exist | JSON for coverage review |
| `--output PATH` | Writes a report; omission writes to stdout | Fresh private path; never the target |
| `--fail-on-incomplete` | Exit 1 on relevant incomplete analysis | Always present |
| `--fail-on-findings` | Exit 1 on any active finding | Always present |
| `--baseline PATH` / `--use-shipped-baseline` | Apply finding suppression; shipped baselines are not applied by default | Do not use |
| `--show-suppressed` | Displays suppressed findings; does not restore them to scoring | Not a substitute for disabling suppression |
| `--recursive` | Scans sub-skills | Do not use |
| `--transitive` and related depth/prefix options | Follow external references | Do not use |
| `--mcp-registry` | Separate registry-input mode | Do not use |
| `--yara-rules-dir PATH` | Loads additional signature rules | Do not use |

No dedicated OSV-off or universal network-disable CLI option was found in the complete pinned CLI. No per-run file-count, source-byte, process-memory or worker-count flag for this adapter was found either. Do not invent `--offline`, `--no-osv`, `--max-files` or `--workers` for this command. This table describes existing options, not permission to use the forbidden ones.

## Network denial is mandatory

`--no-llm` disables model analysis, **not online dependency checks**. The OSV client can send package names, versions and ecosystems to a vulnerability service and request vulnerability details. Failed/offline lookups may use a limited bundled fallback list and produce coverage limitations. A short or zero timeout is not a documented universal network-disable mode, so this adapter does not use timeout manipulation as its privacy control.

The CLI also constructs tracing configuration; ambient tracing/provider environment must not be inherited. Remote inputs and transitive traversal add acquisition paths, which this adapter forbids. Source review of these paths is not proof that every dependency is network-silent.

Therefore require OS-enforced denial of **all network egress, including loopback**, no shared network/authentication sockets, no credentials, and a minimal allowlisted environment. Merely switching Wi-Fi off or clearing a model key is not sufficient evidence of isolation. Preserve local logs privately; do not upload telemetry. If denial makes an analyzer incomplete, retain the gap; do not enable networking to obtain a green result.

## Limits are layered, not interchangeable

The source state defines aggregate defaults of 600 seconds, 64 MiB canonical workflow bytes and 10,000 artifacts. The resource document describes separate discovery, parsing, nested expansion and output ceilings. The README's older per-file summary is not an adequate operational bound; these notes do not treat it as a hard memory limit.

Those internal bounds are not the stricter adapter contract: 100 regular files, 5,000,000 total source bytes, 500,000 bytes per file, 180 seconds total with at most 150 seconds for the scanner. Inventory with bounded traversal first, make the accepted snapshot read-only, and apply independent OS resource limits. Hidden content and nested containers can expand work beyond visible text. Crossing any cap means stop and record incomplete work, not silently accept a subset.

One trial means one invocation and no automatic retries. The graph wires internal analyzer nodes in parallel. There is no verified CLI switch to serialize those nodes. Do not claim single-threaded execution; memory/CPU/process limits must contain internal parallelism.

## Exit codes and report fields

| Exit | Meaning at this pin | Human interpretation |
|---|---|---|
| `0` | No enabled strict gate fired and score is at most 50 | Read JSON and scope; not installation permission |
| `1` | Active findings, incomplete coverage with its gate enabled, or score above 50 | Review findings and coverage separately; it is not necessarily a crash |
| `2` | Input/internal/fatal execution failure | Failed/incomplete; do not accept a missing report as empty findings |
| Timeout, signal, other | No verified complete result | Incomplete; record actual exit/stop reason |

The single-skill JSON contains `skill`, `risk_assessment`, `components`, `issues`, `suppressed_count`, `suppressed`, `metadata`, `execution_successful` and `analysis_completeness`. The completeness object exposes status, `is_complete`, coverage counts, `ledger_exceptions`, `scope_exclusions`, `analyzer_statuses` and `limitations`. Require explicit valid values; never treat missing fields as success.

For the approved static-only mode, require `metadata.llm_requested` to be false and `metadata.meta_analysis_applied` false. Treat unexpected model-call telemetry as a policy failure. `metadata.llm_available` can reflect provider availability rather than actual execution; it does not prove a model ran. Empty `metadata.inference_usage` does not independently prove zero exposure or zero cost. Preserve actual telemetry; never fabricate it.

A normalized risk score can differ from the highest issue severity. Read `risk_assessment.max_issue_severity` and the individual `issues`, not just the headline band. Static findings are evidence to review, not a demonstrated exploit. A report's `SAFE` label cannot authorize installation.

## Evidence boundary

Full reads used for this interface: pinned README, package metadata, licence, complete CLI, graph wiring, workflow state, OSV client, report implementation, resource-bounds document and completeness document. Private provenance records their exact paths and source pin. The documentation verifier confirmed that these files match the pinned source. This is a focused interface study, **not a review of all repository files**, a test-suite run, a scanner security audit or a runtime validation. No detection-rate or speed claims are made.
