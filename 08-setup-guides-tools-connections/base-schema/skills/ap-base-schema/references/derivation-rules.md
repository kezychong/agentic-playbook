# Derivation rules

These convert an interview answer into a design decision. Apply them out loud so the owner
learns the reasoning. (Terms in parentheses are the SQL form — keep those in the `schema.sql`,
not in speech to the owner.)

- **R1 Table or field.** If a thing can happen more than once per spine row, or carries its
  own dates, amounts, or attachments → a **table**. One value per row with nothing hanging off
  it → a **column**.
- **R2 Choice or link table.** Make it its own table (a row you link to) when you want to
  count by it, report it as a row, or attach things to it. Otherwise a plain choice
  (a `TEXT` column, optionally a `CHECK(... IN (...))`).
- **R3 Money rule.** Every amount lives on a transaction row that also has a date, a
  counterparty, and a document. The spine gets a **total via a VIEW** (`SUM` over the linked
  rows) — never a typed-in total.
- **R4 Grouping rule.** Any date you'll group a report by → store it as ISO text
  (`YYYY-MM-DD`) and bucket with `strftime('%Y-%m', date)` in the view. (No separate "text
  sibling" column needed as in Lark; `strftime` does it.)
- **R5 Status rule.** Derivable from evidence → a computed expression in a view
  (`CASE WHEN paid_date IS NOT NULL THEN 'Done' ELSE 'Pending' END`). Requires human judgment
  → a stored `TEXT` column.
- **R6 People rule.** A **people table + foreign key** when you need workload or capacity
  counts. A plain name/text column when you only need to record or notify.
- **R7 Proof rule.** Every point where the business must prove something (to a client,
  supplier, auditor, court) gets a place to hold the document — a `path`/`url` column, or an
  attachments child table — on the row where that thing happens.
- **R8 Code rule.** Anything humans say aloud ("job 214", "invoice 88") is an auto id
  (`INTEGER PRIMARY KEY`, optionally formatted in a view), not something typed.
- **R9 Pull-through rule.** A child row read on its own should show its parent's identity —
  in SQL that's a `JOIN` in the view, not a copied column. Don't duplicate the parent's name
  into the child table.
- **R10 Period rule.** Build a **period table** (one row per month, `month TEXT '2026-01'`)
  when they want month-over-month, budget-vs-actual, or a stable report shape with a row for
  every month even when nothing happened.
- **R11 One number, one home.** If two columns could ever disagree, one of them must be
  derived (a view), never stored twice.
- **R12 Naming rule.** Give tables clear, non-reserved names (avoid SQL keywords like `order`,
  `group`, `transaction` as bare table names — quote them or suffix them, e.g. `orders`,
  `job_stage`). One name means one thing; don't reuse a name for both a table and a column.
- **R13 Reader rule.** Every field must answer "who reads this and when." A field whose only
  answer is "might be useful someday" does not get built.

# Anti-patterns — refuse these

- **One giant table.** Sixty columns where six tables belong. Symptom: columns blank for most
  rows.
- **Typed totals.** Any sum a human keys in is wrong within a month. Derive it in a view.
- **Fields for reports nobody reads.** If it doesn't trace to a Phase-6 metric or a Phase-7
  proof, don't build it.
- **Copying the reference architecture.** Eleven tables on day one guarantees abandonment.
- **Modelling the business they wish they had.** Build for how work flows *today*.
- **A multi-value column for something they'll count by.** If they'll ask "how many by X",
  X is its own table with a foreign key.
- **Two places to record the same fact.** Pick one, derive the other.
