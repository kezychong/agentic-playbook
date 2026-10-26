---
stage: draft
---
# Routing reference — agent instructions

## Current pairings
| Work | Model | Effort |
|---|---|---|
| Plan, specification, analysis, synthesis, judgment | PLANNER_MODEL | high |
| Final review of work against its plan | PLANNER_MODEL | high |
| Default building, fixes, prose and research reading | BUILDER_MODEL | medium |
| Explicit Opus lane or required Claude-only tool | ALTERNATE_BUILDER_MODEL | high |
| Pure mechanical work with no choices | MECHANICAL_MODEL | high |
| Genuine judgment inside an Opus builder, if advisor exists | PLANNER_MODEL | xhigh, one consult |
| planner/reviewer continuity fallback | ALTERNATE_BUILDER_MODEL | xhigh intent; disclose inherited effort |

These are workflow requirements, not an available-model catalogue. Check the installed app's catalogue and current provider evidence.
Use the role-specific model and effort pairings above.
Research reading in the Opus lane uses high effort.
Raise Astra medium to high only after observed drift warrants a bounded retry; record the change.
Opus builder xhigh is only for an explicitly requested long unattended run.

## Effort calibration
Where no role-specific pairing above fixes effort, run these tests in order.
- Answer is already in the input; find, label, map or reformat it: low.
- Judge independent items against a written rubric: medium.
- Pieces change each other's meaning and require balancing: high.
- A silent mistake would poison later stages and cannot be caught cheaply: one supported step above the tension test.
Use observed symptoms: truncation and unwanted changes suggest too much effort; missed connections suggest too little.
Retry one step up only after failure. Effort labels differ between providers; never assume equal capability.
Verify supported settings before launch; unsupported settings can error instead of falling back.

## Separate evidence-processing roles
If the task includes a knowledge-refining pipeline, do not confuse its note inspection with final plan-faithfulness review.
Preserve an existing measured role assignment until a bounded paired evaluation supports changing it.
Template roles, when these models and effort settings are available: quote-backed extraction MECHANICAL_MODEL xhigh; concepts ALTERNATE_BUILDER_MODEL medium;
contradiction search ALTERNATE_BUILDER_MODEL medium; note synthesis ALTERNATE_BUILDER_MODEL high; note inspection ALTERNATE_BUILDER_MODEL high;
filing ALTERNATE_BUILDER_MODEL high; for packet audit, choose a model measured on this task or label the assignment untested.
These are template role assignments, not performance promises for the member's data.
Run deterministic quote and restricted-source checks first. Cheap challengers may run mechanical checks, not replace judgment by habit.
Provide the real allowed destination list rather than naming a filing convention.
For open-ended conflict search, use isolated repeat passes, merge their evidence, and bring genuine disagreements to the user.
Do not call a single search exhaustive. Preserve conditional contradictions instead of automatically making newer sources win.

## Hermes context and identity
Use the active, verified Hermes profile when Hermes is involved; do not install or assume it just to use this skill.
Keep the user's main profile model unchanged. Route only the bounded task.
Use the installed profile's supported routing adapter, not a private machine's hardcoded path.
The route must read the live identity and operating contract, usually SOUL.md and workspace/HERMES.md.
Workspace CLAUDE.md and AGENTS.md should point to those live files, not duplicate their contents.
If a bridge is missing, create a pointer only within the authorized profile, verify readability and retry once.
Each routed prompt includes the job, audience, format, intended action, truth status, approval boundary,
exact readable sources, relevant skills, one or two voice examples, done criteria and return format.
Use the existing route template if available. Never put credentials in a prompt file.
Use the user's signed-in connection; do not copy credentials or inject secret environment values.
Restrict review routes to readable task sources and read-only tools. Verify repository access before requesting review.
If the route cannot read it, stage a bounded non-secret review bundle in an authorized readable workspace.
If an installed Grok research route is available, current X-feed discovery can use it, bounded to three turns with write and spawn tools denied.
Keep raw model returns as internal audit receipts when needed; redact sensitive content before sharing.
