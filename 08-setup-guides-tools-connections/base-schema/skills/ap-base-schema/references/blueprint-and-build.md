# The blueprint, the phasing, the build, the close

## Output 1 — the Base Blueprint (`templates/base-blueprint.md`)

A single document. Every figure in it is one the owner said, or a blank waiting for one.
⛔ Never invent a number, a tax rate, or an annual volume to make it look finished.
It carries: the spine (+ rough annual volume), the stage flow (with triggers), the **Record
Home Map** (`references/record-home-map.md`), each table with its columns and the views on it,
the **metric-traceability** table (each Monday-morning question → the query/view that answers
it), the build order, and "deliberately not built" (every Not-kept line goes here too).

## Output 2 — `schema.sql` (`templates/schema.sql`)

The runnable DDL: `PRAGMA foreign_keys = ON;`, `CREATE TABLE … STRICT;` (tables in build-order),
FK columns, then `CREATE VIEW …` for every rollup and derived number, then `CREATE INDEX` on
FK columns, plus the §7 guard patterns for every Copy, Request and Frozen-figure line in the
map. Keep it in sync with the blueprint (the blueprint is the human view, the SQL is the
machine view; R11 — the SQL is generated from the blueprint's decisions). For a build it is
split into numbered migrations (below).

## Output 3 — the build manifest (`build-manifest.json` + `migrations/`)

The blueprint is for the owner; the manifest is for a **fresh build session** that was never
in the interview and must never need it. Format: `templates/build-manifest.schema.json`.
Worked, passing example: `templates/example-manifest/` — copy its shape.

- **Everything exact.** The map in machine form, checkpoints in order, each with a readback;
  migrations `M001-up.sql` / `M001-down.sql` (…) each fingerprinted (sha256) — no fingerprint,
  no run.
- **Blanks are blockers.** Every `⬜ ASK OWNER` becomes a blocker naming the checkpoint it
  holds. The build stops there and asks. ⛔ Never fill a blank to make it look finished.
- **Fixtures are fictional.** Invented records that exercise each rule (smooth, went
  wrong, duplicate, collision, stale, read-only, request-not-money, frozen, privacy,
  rollback) and the Monday numbers they must give at `acceptance.as_of`. Every fixture check
  is runnable: SQL or names, never prose. ⛔ Real records never go in the manifest.
- **Versions.** A changed plan is a new revision with `supersedes_sha256` = the old file's
  fingerprint; old revisions are kept. A build of revision 2+ must pass the exact preceding
  file with `--previous`; omission or a hash/revision mismatch is an error. Progress lives
  apart, in `build-status.json`.
- **Locks.** Format 1.0 refuses connectors, write-back, outside AI reading single rows, routes
  claimed above step 2, work boards or task systems as homes for new database rows, "the
  system" as an owner, absolute paths, and an approved build without owner confirmation.

Then run both with the package's Python environment, and fix until clean:
`python scripts/check_manifest.py build-manifest.json` and
`python scripts/rehearse.py build-manifest.json`.

## Phasing — never ship everything at once
- **Phase 1 — spine + money.** Spine table, one revenue table, one counterparty table, the
  stage column, the total views, two report queries. Answers "what's live and what's owed."
- **Phase 2 — work + people.** Tasks, deliverables, the people table, workload views.
- **Phase 3 — reporting.** Cost side (if any), the period table, the monthly P&L view, the
  onboarding form/intake for counterparties.

Say which phase each table belongs to when presenting, and get agreement on **Phase 1 scope**
before discussing the rest.

## The build (optional — only on the owner's explicit approval)

Design (map, blueprint, `schema.sql`, manifest, check, rehearsal) is draft work. **Creating the
`.db` or putting real data in it is a build step the owner approves** — recorded in the manifest
as `approval.state: approved_for_build`, with the approver, date, and proof, plus
`truth: confirmed`. Then follow the manifest's checkpoints in order:

1. **Preflight.** `check_manifest.py --for-build` passes: approval is recorded, every blocker
   is answered, every migration is fingerprinted, and revision 2+ has an exact `--previous`
   proof. If the target file exists, back it up first with SQLite's online backup into the
   approved project-relative backup folder.
2. **Rehearse.** `rehearse.py` on the manifest: every check passes, or stop.
3. **Migrate.** Apply each `Mnnn-up.sql` to the approved project-relative target in
   one transaction (`PRAGMA foreign_keys = ON` on the connection), fill `record_home` from the
   map, then run that checkpoint's readback. A command saying "ok" proves nothing.
4. ✋ **First hand import.** The owner's export file, through the import step only
   (`import_guard` opened inside the import's own transaction, upsert on `source_ref`,
   conflicting duplicates rejected before any write). Report new rows, changed values and
   rejected lines; show `unmatched_bills`-style lists, never drop them.
5. ✋ **Acceptance — the two real records.** The owner types in two real past units (one
   smooth, one that went wrong); run every Monday metric and **check each number by hand**
   with the owner. If any is wrong, the design is wrong — fix the blueprint and
   manifest (new revision) and rebuild; don't patch data. ⛔ A base that has never had a real
   record through it is a drawing, not a system.
6. **Finish.** `build-status.json`: each checkpoint done only with its readback matched; each
   route stated honestly (a hand import is step 2 at most). Keep the backup.

**Resuming:** read `build-status.json`, then compare the database with the manifest up to the
last finished checkpoint. On any difference, report it and wait — never "repair" towards the
manifest; the owner may have changed it on purpose.

**Rehearsal containment:** migration SQL is screened before execution; file-affecting SQLite
operations are denied again by the connection authorizer; extensions are disabled; and the
rehearsal runs from its temporary folder with defensive settings where supported. This does
not make the Python process an OS sandbox or defend against a compromised SQLite/Python
library or host. SQLite/the OS may use platform-managed temporary storage. Put genuinely
untrusted runtimes in a separate OS sandbox.

**Where it lives:** use one project-relative SQLite file for the approved scope. Store the
blueprint, manifest, migrations, target, and backups in owner-approved locations. If two data
categories must remain separate, use separate database files and document that decision.

## The close
1. The Base Blueprint document.
2. The Phase-1 build order, numbered, with nothing in it that isn't Phase 1 — and the
   manifest, checked and rehearsed clean, with its open blockers listed.
3. The metric-traceability table, framed as the acceptance test: build it, enter two real
   records, and if any number is wrong, the design is wrong and they come back.
4. One sentence on what was deliberately left out and what would have to change to add it.
5. Note that the **dashboards can read this `.db` directly** once it holds data — this is the
   design side; the dashboards are the read side.
