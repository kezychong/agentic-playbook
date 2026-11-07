# Base Schema

**Agentic Playbook — by Kezy**

Design a local SQLite database from the decisions a business needs to make. The workflow finds the repeated unit of work, maps one home and one direction for each record type, derives tables from the metrics the owner wants, and produces a reviewable blueprint and build manifest before any real database is created.

## Included skill

- [Base Schema](skills/ap-base-schema/README.md): interview, design, validate, and rehearse a local SQLite schema.

## What stays separate

Design work is draft work. The blueprint, SQL, manifest validation, and throwaway rehearsal may proceed without touching live data. Creating a real database, importing records, or adding a connector requires the owner's explicit approval for that step.

## Setup

1. Read [START-HERE.md](START-HERE.md) and the skill's [installation note](skills/ap-base-schema/INSTALL.md).
2. Keep the complete `ap-base-schema` folder together.
3. Install Python 3.10+ and the `jsonschema` package in an isolated environment.
4. Run the included fictional manifest check and rehearsal before adapting the templates.
5. Keep real names, records, credentials, and business figures out of manifests and source control.

[Host setup guide](../manual-setup.md)

## Limits and reuse

The included example is fictional and exercises a throwaway SQLite database only. Its migration screening and SQLite connection defenses reduce file-escape risk but do not constitute an OS sandbox or protect against a compromised SQLite/Python library or host; platform-managed temporary storage may still be used. It does not prove that a proposed schema fits a real business. SQLite version, permissions, backup location, and the owner's acceptance metrics must be verified on the target host before an approved build. Preserve required legal notices. The collection is maintained by Kezy; no new blanket redistribution licence is implied.
