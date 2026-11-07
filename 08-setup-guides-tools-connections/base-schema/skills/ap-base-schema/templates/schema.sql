-- <Venture> — SQLite schema (generated from the Base Blueprint). Build-order matters.
-- Real builds go through the build manifest: this becomes migrations/M001-up.sql (plus a
-- M001-down.sql that undoes it), checked by scripts/check_manifest.py and rehearsed by
-- scripts/rehearse.py before the approved project-relative target is touched.
-- Keep separate data scopes in separate database files.

PRAGMA foreign_keys = ON;

-- 1) No-link tables first (people, counterparties, classification, period, settings) --------
CREATE TABLE settings (
  id        INTEGER PRIMARY KEY CHECK (id = 1),   -- single row
  tax_rate  REAL,                                 -- ask; never hardcode in a formula
  currency  TEXT,
  as_of_override TEXT                             -- rehearsals only; NULL = today (see report_day)
) STRICT;
INSERT INTO settings (id) VALUES (1);

CREATE TABLE client (
  id            INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,
  reg_no        TEXT,
  tax_no        TEXT,
  billing_email TEXT
  -- onboarding payload filled once via a form/CSV; add columns as the interview found them
) STRICT;

-- 2) Spine (own plain columns only) ----------------------------------------------------------
CREATE TABLE project (              -- <-- rename to the real spine noun
  id          INTEGER PRIMARY KEY,
  title       TEXT NOT NULL,
  client_id   INTEGER REFERENCES client(id),
  stage       TEXT,                 -- from the lifecycle stages
  started_on  TEXT,                 -- ISO 'YYYY-MM-DD'
  finished_on TEXT
) STRICT;

-- 3) Transaction / execution tables (own columns + FK to parent) -----------------------------
CREATE TABLE sales_invoice (
  id          INTEGER PRIMARY KEY,
  project_id  INTEGER REFERENCES project(id),
  amount      REAL,
  invoice_date TEXT,               -- accrual date
  paid_date   TEXT                 -- cash date; filled = paid (status derives from this)
) STRICT;

CREATE TABLE ap_invoice (
  id          INTEGER PRIMARY KEY,
  project_id  INTEGER REFERENCES project(id),
  amount      REAL,
  paid_date   TEXT
) STRICT;

CREATE TABLE period ( month TEXT PRIMARY KEY );   -- '2026-01', '2026-02', ...

-- 4) Views: derived numbers (never stored) ---------------------------------------------------
CREATE VIEW project_money AS
SELECT p.id, p.title,
       COALESCE(SUM(si.amount), 0) AS total_in,
       COALESCE((SELECT SUM(a.amount) FROM ap_invoice a WHERE a.project_id = p.id), 0) AS total_out,
       COALESCE(SUM(si.amount),0)
         - COALESCE((SELECT SUM(a.amount) FROM ap_invoice a WHERE a.project_id = p.id),0) AS gross_profit,
       CASE WHEN COUNT(si.id) > 0 AND SUM(CASE WHEN si.paid_date IS NULL THEN 1 ELSE 0 END) = 0
            THEN 'Paid' ELSE 'Owing' END AS payment_status
FROM project p
LEFT JOIN sales_invoice si ON si.project_id = p.id
GROUP BY p.id;

CREATE VIEW monthly_pl AS
SELECT pr.month,
       (SELECT COALESCE(SUM(amount),0) FROM sales_invoice WHERE strftime('%Y-%m', paid_date) = pr.month) AS cash_in,
       (SELECT COALESCE(SUM(amount),0) FROM ap_invoice    WHERE strftime('%Y-%m', paid_date) = pr.month) AS cash_out
FROM period pr ORDER BY pr.month;

-- 5) Indexes on FK columns you filter/join on ------------------------------------------------
CREATE INDEX ix_sales_invoice_project ON sales_invoice(project_id);
CREATE INDEX ix_ap_invoice_project    ON ap_invoice(project_id);

-- 6) Acceptance: made-up fixtures live in the build manifest and run in scripts/rehearse.py;
--    the two real past records are typed in at the build's stop-for-owner step, then
--    SELECT * FROM project_money;  SELECT * FROM monthly_pl;  and check every number by hand.

-- 7) Record Home patterns — copy only what the Record Home Map calls for -------------------
--    (references/record-home-map.md). Table names here are examples; keep the shapes.
--    Keep the RAISE wording: rehearse.py looks for 'is a copy', 'handed over' and 'frozen'.

-- 7a) Meta tables and the report date: needed as soon as the map has one Copy.
CREATE TABLE record_home (                 -- filled from the manifest's map at build, not here
  kind         TEXT PRIMARY KEY,
  table_name   TEXT,
  role         TEXT NOT NULL CHECK (role IN ('source','mirror','intake','snapshot','not_held')),
  max_age_days INTEGER
) STRICT;

CREATE TABLE import_guard (
  id   INTEGER PRIMARY KEY CHECK (id = 1),
  open INTEGER NOT NULL CHECK (open IN (0, 1))   -- only the import step opens it, in its own transaction
) STRICT;
INSERT INTO import_guard VALUES (1, 0);

CREATE TABLE import_log (                  -- every value an import changed
  id         INTEGER PRIMARY KEY,
  table_name TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  field      TEXT NOT NULL,
  old_value  TEXT,
  new_value  TEXT
) STRICT;

CREATE VIEW report_day AS
  SELECT COALESCE((SELECT as_of_override FROM settings WHERE id = 1), date('now')) AS as_of;

-- 7b) Copy (mirror): payments received, copied by hand import from the accounting software.
--     If payments are copied in, drop paid_date from sales_invoice and derive "paid" from
--     this table instead — one fact, one home (R11).
CREATE TABLE received_payment (
  id          INTEGER PRIMARY KEY,
  source_ref  TEXT NOT NULL UNIQUE,        -- the home's own number; re-imports update, never duplicate
  amount      REAL NOT NULL,
  paid_date   TEXT NOT NULL,
  match_ref   TEXT,                        -- the project code the team types into the home's reference box
  sync_status TEXT NOT NULL CHECK (sync_status = 'imported_by_hand'),
  last_synced TEXT NOT NULL,               -- the export's date
  sync_note   TEXT
) STRICT;

CREATE TRIGGER received_payment_ro_ins BEFORE INSERT ON received_payment WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'received_payment is a copy: change it in its home'); END;
CREATE TRIGGER received_payment_ro_upd BEFORE UPDATE ON received_payment WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'received_payment is a copy: change it in its home'); END;
CREATE TRIGGER received_payment_ro_del BEFORE DELETE ON received_payment WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'received_payment is a copy: change it in its home'); END;

CREATE TRIGGER received_payment_log AFTER UPDATE ON received_payment
BEGIN
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'source_ref', OLD.source_ref, NEW.source_ref
    WHERE OLD.source_ref IS NOT NEW.source_ref;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'amount', CAST(OLD.amount AS TEXT), CAST(NEW.amount AS TEXT)
    WHERE OLD.amount IS NOT NEW.amount;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'paid_date', OLD.paid_date, NEW.paid_date
    WHERE OLD.paid_date IS NOT NEW.paid_date;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'match_ref', OLD.match_ref, NEW.match_ref
    WHERE OLD.match_ref IS NOT NEW.match_ref;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'sync_status', OLD.sync_status, NEW.sync_status
    WHERE OLD.sync_status IS NOT NEW.sync_status;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'last_synced', OLD.last_synced, NEW.last_synced
    WHERE OLD.last_synced IS NOT NEW.last_synced;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'received_payment', NEW.source_ref, 'sync_note', OLD.sync_note, NEW.sync_note
    WHERE OLD.sync_note IS NOT NEW.sync_note;
END;

-- 7c) Request (intake): the team asks the accountant to raise an invoice; the home returns its number.
CREATE TABLE invoice_request (
  id             INTEGER PRIMARY KEY,
  project_id     INTEGER NOT NULL REFERENCES project(id),
  drafted_on     TEXT NOT NULL,
  amount_asked   REAL,                     -- ⛔ never summed as money: count the Copy, not the request
  handed_over_on TEXT,
  returned_ref   TEXT                      -- filled once, when the home answers
) STRICT;

CREATE TRIGGER invoice_request_frozen BEFORE UPDATE ON invoice_request
WHEN OLD.handed_over_on IS NOT NULL AND (
     NEW.project_id IS NOT OLD.project_id OR NEW.drafted_on IS NOT OLD.drafted_on
  OR NEW.amount_asked IS NOT OLD.amount_asked OR NEW.handed_over_on IS NOT OLD.handed_over_on
  OR (OLD.returned_ref IS NOT NULL AND NEW.returned_ref IS NOT OLD.returned_ref))
BEGIN SELECT RAISE(ABORT, 'request already handed over: only the returned number can be filled in'); END;
CREATE TRIGGER invoice_request_keep BEFORE DELETE ON invoice_request WHEN OLD.handed_over_on IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'request already handed over: it stays on record'); END;

-- 7d) Frozen figure (snapshot): closed-month revenue, written once by the month-end step.
CREATE TABLE month_close (
  month     TEXT PRIMARY KEY CHECK (month GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'),
  revenue   REAL NOT NULL,
  frozen_on TEXT NOT NULL
) STRICT;
CREATE TRIGGER month_close_frozen_upd BEFORE UPDATE ON month_close
BEGIN SELECT RAISE(ABORT, 'frozen figure: never changed'); END;
CREATE TRIGGER month_close_frozen_del BEFORE DELETE ON month_close
BEGIN SELECT RAISE(ABORT, 'frozen figure: never changed'); END;

-- 7e) Stale copies: one UNION line per Copy table.
CREATE VIEW stale_copies AS
  SELECT h.kind, h.table_name, m.last_copy, h.max_age_days, r.as_of,
         CAST(julianday(r.as_of) - julianday(m.last_copy) AS INTEGER) AS age_days
  FROM record_home h
  JOIN (SELECT 'received_payment' AS t, MAX(last_synced) AS last_copy FROM received_payment) m
    ON m.t = h.table_name
  CROSS JOIN report_day r
  WHERE h.role = 'mirror'
    AND (m.last_copy IS NULL OR julianday(r.as_of) - julianday(m.last_copy) > h.max_age_days);
