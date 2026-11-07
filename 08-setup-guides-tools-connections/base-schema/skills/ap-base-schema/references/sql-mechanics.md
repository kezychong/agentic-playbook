# SQLite mechanics

> How the design becomes a real local SQLite database.
> The SQL uses SQLite and Python's standard-library `sqlite3`; no database server is required.

## Column types (SQLite affinity — few, and loose)
- `TEXT` — names, codes, **dates** (store ISO `YYYY-MM-DD` / `YYYY-MM-DDTHH:MM:SS`), choices.
- `INTEGER` — counts, ids, booleans (0/1).
- `REAL` — money and quantities. (For exact currency you *may* store integer cents; `REAL` is
  fine for a small business base — say which you chose.)
- ⚠️ SQLite does **not** enforce types hard (affinity, not strict types). Optionally use
  `STRICT` tables (`CREATE TABLE ... (...) STRICT;`) to make types enforced — recommend it.

## Keys and links
- Auto id: `id INTEGER PRIMARY KEY` (rowid alias; auto-increments).
- A **link** = a foreign key column on the **child** pointing at the parent's id:
  `project_id INTEGER REFERENCES project(id)`.
- ⚠️ **Foreign keys are OFF by default in SQLite.** Every connection must run
  `PRAGMA foreign_keys = ON;` or the `REFERENCES` are decorative. Put it at the top of every
  script that touches the DB.

## Roll-ups and derived numbers = VIEWs (never stored)
A rollup is a `VIEW` with a `JOIN` + aggregate — the equivalent of Lark's `.SUM()`/`.COUNTIF()`:

```sql
-- money never sits on the spine; the spine's totals are a view
CREATE VIEW project_money AS
SELECT p.id, p.title,
       COALESCE(SUM(si.amount), 0)                                   AS total_in,
       COALESCE((SELECT SUM(ap.amount) FROM ap_invoice ap
                 WHERE ap.project_id = p.id), 0)                     AS total_out,
       COALESCE(SUM(si.amount),0)
         - COALESCE((SELECT SUM(ap.amount) FROM ap_invoice ap
                     WHERE ap.project_id = p.id),0)                  AS gross_profit
FROM project p
LEFT JOIN sales_invoice si ON si.project_id = p.id
GROUP BY p.id;

-- status derived from a filled date (nobody flips a switch)
-- expose as a column in a view:  CASE WHEN paid_date IS NOT NULL THEN 'Done' ELSE 'Pending' END

-- workload: count a person's in-progress tasks
CREATE VIEW employee_load AS
SELECT e.id, e.name, COUNT(t.id) AS active_tasks
FROM employee e
LEFT JOIN task t ON t.responsible_id = e.id AND t.status = 'In Progress'
GROUP BY e.id;
```

## Dates, months, and cash-vs-accrual
- Store dates as ISO `TEXT`. Month bucket = `strftime('%Y-%m', invoice_date)`.
- **Accrual vs cash** are two different questions — build both, labelled: accrual sums every
  invoice raised (`GROUP BY strftime('%Y-%m', invoice_date)`); cash sums by
  `strftime('%Y-%m', paid_date)`. Ask which they manage on; never let the two numbers get
  confused.

## The period table (stable monthly rows)
```sql
CREATE TABLE period (month TEXT PRIMARY KEY);   -- '2026-01', '2026-02', ...
CREATE VIEW monthly_pl AS
SELECT pr.month,
       (SELECT COALESCE(SUM(amount),0) FROM sales_invoice
          WHERE strftime('%Y-%m', paid_date) = pr.month) AS cash_in,
       (SELECT COALESCE(SUM(amount),0) FROM ap_invoice
          WHERE strftime('%Y-%m', paid_date) = pr.month) AS cash_out
FROM period pr ORDER BY pr.month;
```
Gives a row per month whether or not anything happened, and somewhere to put a budget column.

## Tax and settings — never hardcode
Don't bury a rate in a formula. Keep a one-row `settings` table (`tax_rate REAL`, `currency
TEXT`) or a column, and reference it. ⛔ Never assume a tax rate; ask.

## Traps (SQLite-specific, mostly quiet)
- **FKs off by default** → `PRAGMA foreign_keys = ON;` every time (above).
- **Loose typing** → a "number" column can silently hold text. Use `STRICT` tables, or validate.
- **`SUM` of no rows is `NULL`, not 0** → wrap with `COALESCE(SUM(x),0)` before arithmetic,
  or a `NULL` poisons the total.
- **Integer division** → `7/2 = 3`. Force real: `x * 1.0 / y`, and guard divide-by-zero:
  `CASE WHEN d = 0 THEN NULL ELSE n*1.0/d END`.
- **Date math needs ISO text** → `date('now')`, `julianday(a)-julianday(b)` for day gaps.
  A number like `14` in a date column is just the string "14", not a date.
  Manifest dates are checked as real calendar dates by Python; a JSON Schema pattern alone
  cannot prove that `2026-02-30` exists.
- **Reserved words** as bare identifiers (`order`, `group`, `transaction`) error or confuse —
  name tables to avoid them (R12).

## Build order (order matters — a link can't point at a table that doesn't exist yet)
1. `PRAGMA foreign_keys = ON;`
2. Tables with **no outgoing links** first: people, counterparties, classification, period, settings.
3. The **spine** table with its own plain columns (title, dates, stage, status, id).
4. Transaction + execution tables with their own plain columns **and** their FK columns to
   parents (parents already exist).
5. **VIEWs** — pull-throughs (JOINs), then spine rollups (`SUM`/`COUNT`), then counterparty/
   people second-order rollups, then the period `monthly_pl`.
6. Indexes on the FK columns you'll filter/join on (`CREATE INDEX ... ON child(parent_id);`).
7. **Enter the two real past records end to end**, then run each metric query and check every
   number by hand. ⛔ Not optional — a base that never had a real record is a drawing.

## Running it (local, stdlib)
Real builds go through the build manifest (`references/blueprint-and-build.md`):
```text
python scripts/check_manifest.py build-manifest.json   # plan is sound
python scripts/rehearse.py build-manifest.json         # throwaway copy, every check
python scripts/test_regressions.py                     # hostile and boundary regressions
```
Rehearsal migrations may use ordinary DDL/DML plus `PRAGMA foreign_keys = ON` and an integer
`PRAGMA user_version`. They must not attach/detach databases, vacuum to files, change journal,
WAL, writable-schema or temp-directory settings, load extensions, call external-file helper
functions, create virtual tables, or contain top-level transaction control (`BEGIN`, `COMMIT`,
`END`, `ROLLBACK`, `SAVEPOINT`, `RELEASE`). The rehearsal preflight and SQLite authorizer both
enforce the containment boundary. Its splitter accepts a boundary only when
`sqlite3.complete_statement` says the statement is complete, so trigger `BEGIN ... END` bodies
and quoted semicolons remain one statement.
Only after the owner's explicit approval are migrations applied to the project-relative target.
Use the same validated statement list as rehearsal and execute every statement with
`con.execute(statement)` between one explicit `con.execute("BEGIN")` and `COMMIT`; on any
exception, execute `ROLLBACK` while `con.in_transaction` is true, then re-raise. Do not use
`executescript`, whose implicit transaction handling can defeat this all-or-nothing boundary.
For a quick look at a design (no file kept): `sqlite3 :memory: < schema.sql`.
