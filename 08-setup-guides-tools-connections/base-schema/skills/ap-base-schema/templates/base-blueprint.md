---
type: base-blueprint
operation: "<Operation>"
db_path: data/<operation>.db
manifest: build-manifest.json
truth: unverified
status: draft
tags: [type/base-blueprint, source/agent]
---

# <Operation> Base Blueprint (SQLite)

> Draft. Every business figure is one the owner supplied or a clearly marked blank. The target
> is a project-relative local SQLite file. Building or filling it requires explicit owner approval.

## Scope and data boundaries
- Covers: <approved scope>
- Kept separate from: <other operations or sensitive data categories>
- Build approver: <role or name>

## The spine
One row per **<unit>**. Approximate annual volume: **<owner-supplied value or unknown>**.

Representative fictional example: <fictional example used only to explain the shape>.

## Stage flow
`<stage>` → `<stage>` → `<stage>`

Trigger for each transition: <owner-supplied event or evidence>.

## Record Home Map
<Paste the filled map from `templates/record-home-map.md`, one line per kind of record.>

Routes, never above the evidence: <kind> · step <0–2> · <proof and date>.

No connectors and no write-back in this build.

## Tables

### <table_name>
Purpose: one row per <thing>.
Reader and use: <who reads it, for what decision, and when>.
Links: <child>.<parent>_id → <parent>(id).

| Column | Type | Reader and use |
|---|---|---|
| id | INTEGER PRIMARY KEY | stable local identifier |
| … | TEXT / INTEGER / REAL | … |

### Views on it
- `<view_name>` — <what it computes and which owner question it answers>.

## Metric traceability (= acceptance test)

| Regular owner question | Where the answer comes from | Missing inputs |
|---|---|---|
| … | … | … |

## Build order
1. Enable foreign keys.
2. Create no-link and metadata tables.
3. Create the spine table.
4. Create transaction and execution tables with links.
5. Add copy, request, frozen-figure, and audit guards.
6. Create views.
7. Create indexes.
8. Validate the build manifest.
9. Rehearse on a throwaway database.
10. Stop for owner approval before creating or filling the real database.
11. After approval, hand-import and test two owner-supplied records; check every metric by hand.

## Deliberately not built
- <Every Not kept here line from the Record Home Map, with its real home.>
- <Thing> — <why it is omitted and what evidence would justify adding it>.

## Later phases
- Phase 2: …
- Phase 3: …
