# The Record Home Map

Use this map to keep one authoritative home and one direction for every kind of record.

Before any table is drawn, decide **where each kind of record lives**. The same fact kept in
two places drifts apart; one day they don't match and nobody knows which is right. The Record
Home Map stops that: **one line per kind of record**, saying where it's born, which way copies
flow, who looks after it, who may change it, and how old a copy may get.

## The rule

**Each kind of record has one home and one direction.** The home is the one place it is born
and changed. Everywhere else holds a copy that follows the home, and nobody edits the copy.
The rule is per kind, not per database: one database can hold copies and born-here tables side
by side, never one kind flowing both ways.

## Find the home: where does its number come from?

- Another system issues the number (bank, accounting software, a regulator) → that system is
  home; the database holds a **Copy**.
- The number is typed into a Word/Excel template → it's really born in the business. Recommend
  moving it into the database as **Born here**; say it as a recommendation, the owner decides.
- Nobody issues a number → the database becomes home when the first row is typed.
- Two systems both issue numbers for the same kind → that's the drift. Name it, ask the owner
  to pick one home. ⛔ Don't design around it.
- A home covers only part of a kind → either two kinds (each its own home) or one home with
  the other list downstream. Ask which. The losing list goes under "Deliberately not built".

## Five roles (exactly one per kind)

| Role | Say to the owner | SQL |
|---|---|---|
| **Born here** (source) | "This database is the original." | ordinary STRICT table |
| **Copy** (mirror) | "A copy of another system. Look, don't touch." | receipt columns + read-only guard triggers; filled only by the import step |
| **Request** (intake) | "Filled in here, sent to its real home, which gives it the official number." | `handed_over_on`, `returned_ref`; frozen after handover except `returned_ref` once |
| **Frozen figure** (snapshot) | "A number frozen on a date." | keyed by period; UPDATE/DELETE always refused |
| **Not kept here** (not_held) | "Lives elsewhere; listed so nobody builds a second copy." | no table; goes under "Deliberately not built" |

⛔ **A request is never counted as money.** Money totals count the official record (the copy),
never the request, or every payment appears twice.
⛔ **No write-back.** Editing a copy and pushing it home is refused. A request is not write-back:
it's a new ask, and the home answers with a number.

## The columns of each line

| Column | What goes in it |
|---|---|
| Kind of record | The owner's own name for it |
| Role | Born here · Copy · Request · Frozen figure · Not kept here |
| Home | The one system where the record is born and changed |
| Direction | born here · copy comes in · request goes out · frozen here · not kept |
| Home's number (source ref) | The home's own number, stored as text; how a re-import recognises a row |
| Match key | Only when a copy must tie to a row here (e.g. a project code typed into the bill's reference box). ⛔ Ask whether the home has a box that can carry it. If not: a person matches by hand, or the question can't be answered — say which |
| Freshness | How old the copy may be when read. Set from the Phase 6 numbers that read it. Every number built on a copy shows the copy's date |
| Data owner | Named person who keeps it right in its home. Never "the system" |
| Sync owner | Named person who notices when copies stop arriving and gets it fixed. Never "the system" or "automation" |
| Who may change it here | Born here: named roles · Copy: import step only · Request: team until handover, then nobody · Frozen figure: close step only, once |
| Route + proven step | How it travels and how far that's proven (ladder below), with proof and date |
| Sensitivity | normal / personal data / client money / regulator. Keep the least possible: a code not a name, a total not every line — and say what is kept instead |

## The ladder — never claim a step above the proof

0. **Not mapped yet.**
1. **Agreed on paper** — home, direction, number, match key and owners agreed.
2. **Database ready** — the table exists and holds copies imported by hand from an export
   file (`sync_status = 'imported_by_hand'`, `last_synced` = the export's date).
3. **Copies arrive by themselves** — needs a connector. ⛔ Not allowed in manifest format 1.0.
4. **Proven end to end** — one real change in the home arrived, no duplicate, nothing written
   back. ⛔ Connector-only, same as 3.

Every connector is its own project with the owner's explicit approval. Never pick a route on the
owner's behalf and never promise that some software can be connected: write what the owner or
vendor says, or "not known yet".

## Where records can live

- **A notes system** — notes, decisions, minutes, and policies.
- **A task system** — tasks and promises. A business database should not create a competing task list.
- **A work board** — team-owned work, normally a source of copies or Not kept here.
- **A local database** — one project-relative SQLite file for the approved scope.
- **Spreadsheets and export files.**
- **Outside systems** — bank, accounting software, a regulator's public register.
- **Paper and PDFs** — the database keeps the file's path (R7), not its contents.

## Two shapes to catch

- **Only spreadsheets.** Every table is Born here. Don't invent a Copy to look like a hub.
- **The spine itself is born elsewhere** (orders in a shop platform, bookings in a booking
  system). The spine is then a Copy, and the database adds Born-here tables keyed to it. Say
  so when Phase 1 surfaces it — it changes everything after.

## When to fill it

- Phase 0 adds: "Where does each kind of record get its number?"
- **After Phase 5:** one line per kind of record, using the blank in
  `templates/record-home-map.md`.
- **After Phase 6:** fill each line's freshness from the numbers that read it.
- ⛔ A table with no line in the map is not built. Every Not-kept line also goes under
  "Deliberately not built".
- Blanks stay blank, loudly: `⬜ ASK OWNER: <question>`. In the manifest they become blockers.

## SQLite mapping (technical build notes)

- **Copy:** `source_ref TEXT NOT NULL UNIQUE`, `sync_status TEXT NOT NULL CHECK (sync_status =
  'imported_by_hand')`, `last_synced TEXT NOT NULL`, `sync_note TEXT`. BEFORE INSERT/UPDATE/DELETE
  triggers `RAISE(ABORT, '<table> is a copy: change it in its home')` unless the one-row
  `import_guard.open = 1`, which only the import step sets inside its own transaction. Imports
  are `INSERT … ON CONFLICT(source_ref) DO UPDATE`; an AFTER UPDATE trigger writes each changed
  business value to `import_log`; conflicting duplicates inside one export file are rejected
  before any write; a crash rolls back the whole file and leaves the guard shut.
- **Request:** a BEFORE UPDATE trigger refuses any change once `handed_over_on` is set, except
  filling `returned_ref` once; BEFORE DELETE refuses a handed-over row. Money views never read it.
- **Frozen figure:** BEFORE UPDATE and BEFORE DELETE triggers always `RAISE`.
- **Meta tables** (always present when the map has a Copy): `settings` (one row; `as_of_override`
  for rehearsals), `record_home` (filled from the manifest's map, not by a migration),
  `import_guard`, `import_log`; views `report_day` and `stale_copies`.
- The triggers stop mistakes by ordinary programs that open the file. They do not stop someone
  with raw file access; host file permissions provide that boundary. Say so, and do not overclaim.
- The full pattern is in `templates/schema.sql` §7 and the runnable example in
  `templates/example-manifest/`.
