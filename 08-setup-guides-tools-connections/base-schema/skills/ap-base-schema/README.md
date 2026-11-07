# Base Schema

Agentic Playbook — **by Kezy**

Design a local SQLite database around one repeated unit of work and the metrics its owner actually needs.

Start with [the complete workflow](SKILL.md). This public package is version 0.2.0.

## Prerequisites

- A skill-capable host with access to this complete folder.
- Python 3.10 or later.
- SQLite 3.37 or later for `STRICT` tables.
- The Python `jsonschema` package for manifest validation.
- A project workspace where drafts, migrations, fictional fixtures, and approved data can remain separate.

See [INSTALL.md](INSTALL.md) and the [manual host setup guide](../../../manual-setup.md).

## Example trigger

> Use ap-base-schema to design a local SQLite database for a fictional repair studio. Ask one question at a time. Do not propose tables until we agree on the weekly metrics. Draft the Record Home Map, blueprint, SQL, and build manifest. Validate and rehearse with fictional fixtures only. Do not create a real database or import real records without my explicit approval.

## Outputs

- a Base Blueprint;
- a Record Home Map;
- versioned SQL migrations and `schema.sql`;
- a build manifest with blockers, checkpoints, fixture checks, metrics, and rollback steps;
- validation and throwaway-rehearsal results.

## Limits

A passing rehearsal proves only that the fictional manifest and permitted migrations behave as specified. It does not prove that the owner's inputs are complete, that a connector exists, or that real data is correct. Rehearsal uses SQL screening, SQLite authorizer/defensive settings, and an isolated temporary working directory, but it is not an OS sandbox and cannot defend against a compromised SQLite/Python library or host; platform-managed temporary storage may still be used. Missing business numbers stay unknown. Build, import, connector, and dashboard steps require separate approval.
