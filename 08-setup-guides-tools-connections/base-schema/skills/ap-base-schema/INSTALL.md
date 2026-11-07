# Manual installation note — Agentic Playbook, by Kezy

This package is documentation and source code. Loading it does not install dependencies, create a database, or import data.

## Requirements

- Python 3.10+
- SQLite 3.37+
- `jsonschema`

Create an isolated environment using the method supported by your host, then install `jsonschema` there. Preserve existing environments and versions unless the owner approves a change.

## Keep the package intact

Copy the complete `ap-base-schema` folder, including:

- `SKILL.md`
- `references/`
- `templates/`
- `scripts/`

The scripts resolve the schema and example files relative to this folder. They do not require a fixed home directory.

## Verify the fictional example

From the `ap-base-schema` folder, run through the host's command tool:

```text
python scripts/check_manifest.py templates/example-manifest/build-manifest.json
python scripts/rehearse.py templates/example-manifest/build-manifest.json
```

Both commands must exit 0. The rehearsal creates a temporary folder using Python's temporary-file API and removes it on completion. To place scratch files in an approved location, add `--scratch PATH` to the rehearsal command.

## Before real use

Choose project-relative draft, data, and backup folders. Keep real records out of the manifest and fictional fixtures. Review the proposed target path, backup method, acceptance metrics, and rollback steps before approving a real build.
