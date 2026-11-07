-- M001 up: example compliance desk (all made up). Version 0 -> 1.
-- Applied by the build in one transaction, with PRAGMA foreign_keys = ON on the connection.
-- record_home is filled from the manifest's map by the build, not here.
CREATE TABLE settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  currency TEXT,
  as_of_override TEXT
) STRICT;
INSERT INTO settings (id) VALUES (1);

CREATE TABLE record_home (
  kind TEXT PRIMARY KEY,
  table_name TEXT,
  role TEXT NOT NULL CHECK (role IN ('source','mirror','intake','snapshot','not_held')),
  max_age_days INTEGER
) STRICT;

CREATE TABLE import_guard (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  open INTEGER NOT NULL CHECK (open IN (0, 1))
) STRICT;
INSERT INTO import_guard VALUES (1, 0);

CREATE TABLE import_log (
  id INTEGER PRIMARY KEY,
  table_name TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  field TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT
) STRICT;

-- Source: born here
CREATE TABLE deadline (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('licence','audit','filing','reconciliation','other')),
  owner_role TEXT NOT NULL,
  due_on TEXT NOT NULL,
  done_on TEXT,
  evidence_path TEXT
) STRICT;

-- Mirror: copy of a regulator's public register
CREATE TABLE licence (
  id INTEGER PRIMARY KEY,
  source_ref TEXT NOT NULL UNIQUE,
  regulator TEXT NOT NULL,
  expires_on TEXT,
  status_in_home TEXT,
  sync_status TEXT NOT NULL CHECK (sync_status = 'imported_by_hand'),
  last_synced TEXT NOT NULL,
  sync_note TEXT
) STRICT;

-- Intake: request handed to its real home
CREATE TABLE licence_request (
  id INTEGER PRIMARY KEY,
  deadline_id INTEGER NOT NULL REFERENCES deadline(id),
  drafted_on TEXT NOT NULL,
  fee_quoted REAL,
  handed_over_on TEXT,
  handed_to_role TEXT,
  returned_ref TEXT
) STRICT;

-- Mirror: copy of the accounting software's paid bills
CREATE TABLE paid_bill (
  id INTEGER PRIMARY KEY,
  source_ref TEXT NOT NULL UNIQUE,
  amount REAL NOT NULL,
  currency TEXT NOT NULL,
  paid_on TEXT NOT NULL,
  match_ref TEXT,
  sync_status TEXT NOT NULL CHECK (sync_status = 'imported_by_hand'),
  last_synced TEXT NOT NULL,
  sync_note TEXT
) STRICT;

-- Snapshot: month-end result, frozen
CREATE TABLE month_close (
  month TEXT PRIMARY KEY CHECK (month GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'),
  reconciled INTEGER NOT NULL CHECK (reconciled IN (0, 1)),
  difference REAL NOT NULL,
  checked_by_role TEXT NOT NULL,
  frozen_on TEXT NOT NULL
) STRICT;

-- Source, minimised: opaque client code only, never a name
CREATE TABLE onboarding_exception (
  id INTEGER PRIMARY KEY,
  client_code TEXT NOT NULL CHECK (client_code GLOB 'C-[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]'),
  reason TEXT NOT NULL,
  opened_on TEXT NOT NULL,
  closed_on TEXT,
  escalated INTEGER NOT NULL DEFAULT 0 CHECK (escalated IN (0, 1))
) STRICT;

-- Mirrors are read-only outside the import step
CREATE TRIGGER licence_ro_ins BEFORE INSERT ON licence WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'licence is a copy: change it in its home'); END;
CREATE TRIGGER licence_ro_upd BEFORE UPDATE ON licence WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'licence is a copy: change it in its home'); END;
CREATE TRIGGER licence_ro_del BEFORE DELETE ON licence WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'licence is a copy: change it in its home'); END;
CREATE TRIGGER paid_bill_ro_ins BEFORE INSERT ON paid_bill WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'paid_bill is a copy: change it in its home'); END;
CREATE TRIGGER paid_bill_ro_upd BEFORE UPDATE ON paid_bill WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'paid_bill is a copy: change it in its home'); END;
CREATE TRIGGER paid_bill_ro_del BEFORE DELETE ON paid_bill WHEN (SELECT open FROM import_guard) = 0
BEGIN SELECT RAISE(ABORT, 'paid_bill is a copy: change it in its home'); END;

-- Every value an import changes is logged
CREATE TRIGGER paid_bill_log AFTER UPDATE ON paid_bill
BEGIN
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'source_ref', OLD.source_ref, NEW.source_ref
    WHERE OLD.source_ref IS NOT NEW.source_ref;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'amount', CAST(OLD.amount AS TEXT), CAST(NEW.amount AS TEXT)
    WHERE OLD.amount IS NOT NEW.amount;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'currency', OLD.currency, NEW.currency
    WHERE OLD.currency IS NOT NEW.currency;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'match_ref', OLD.match_ref, NEW.match_ref
    WHERE OLD.match_ref IS NOT NEW.match_ref;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'paid_on', OLD.paid_on, NEW.paid_on
    WHERE OLD.paid_on IS NOT NEW.paid_on;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'sync_status', OLD.sync_status, NEW.sync_status
    WHERE OLD.sync_status IS NOT NEW.sync_status;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'last_synced', OLD.last_synced, NEW.last_synced
    WHERE OLD.last_synced IS NOT NEW.last_synced;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'paid_bill', NEW.source_ref, 'sync_note', OLD.sync_note, NEW.sync_note
    WHERE OLD.sync_note IS NOT NEW.sync_note;
END;
CREATE TRIGGER licence_log AFTER UPDATE ON licence
BEGIN
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'source_ref', OLD.source_ref, NEW.source_ref
    WHERE OLD.source_ref IS NOT NEW.source_ref;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'regulator', OLD.regulator, NEW.regulator
    WHERE OLD.regulator IS NOT NEW.regulator;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'expires_on', OLD.expires_on, NEW.expires_on
    WHERE OLD.expires_on IS NOT NEW.expires_on;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'status_in_home', OLD.status_in_home, NEW.status_in_home
    WHERE OLD.status_in_home IS NOT NEW.status_in_home;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'sync_status', OLD.sync_status, NEW.sync_status
    WHERE OLD.sync_status IS NOT NEW.sync_status;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'last_synced', OLD.last_synced, NEW.last_synced
    WHERE OLD.last_synced IS NOT NEW.last_synced;
  INSERT INTO import_log (table_name, source_ref, field, old_value, new_value)
    SELECT 'licence', NEW.source_ref, 'sync_note', OLD.sync_note, NEW.sync_note
    WHERE OLD.sync_note IS NOT NEW.sync_note;
END;

-- A request is frozen once handed over, except for filling in the returned number once
CREATE TRIGGER licence_request_frozen BEFORE UPDATE ON licence_request
WHEN OLD.handed_over_on IS NOT NULL AND (
     NEW.deadline_id IS NOT OLD.deadline_id OR NEW.drafted_on IS NOT OLD.drafted_on
  OR NEW.fee_quoted IS NOT OLD.fee_quoted OR NEW.handed_over_on IS NOT OLD.handed_over_on
  OR NEW.handed_to_role IS NOT OLD.handed_to_role
  OR (OLD.returned_ref IS NOT NULL AND NEW.returned_ref IS NOT OLD.returned_ref))
BEGIN SELECT RAISE(ABORT, 'request already handed over: only the returned number can be filled in'); END;
CREATE TRIGGER licence_request_keep BEFORE DELETE ON licence_request WHEN OLD.handed_over_on IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'request already handed over: it stays on record'); END;

-- Frozen figures never change
CREATE TRIGGER month_close_frozen_upd BEFORE UPDATE ON month_close
BEGIN SELECT RAISE(ABORT, 'frozen figure: never changed'); END;
CREATE TRIGGER month_close_frozen_del BEFORE DELETE ON month_close
BEGIN SELECT RAISE(ABORT, 'frozen figure: never changed'); END;

-- Views
CREATE VIEW report_day AS
  SELECT COALESCE((SELECT as_of_override FROM settings WHERE id = 1), date('now')) AS as_of;

CREATE VIEW deadline_list AS
  SELECT 'DL-' || printf('%04d', id) AS code, id, title, kind, owner_role, due_on, done_on
  FROM deadline;

CREATE VIEW due_next_30_days AS
  SELECT r.as_of, d.code, d.title, d.owner_role, d.due_on
  FROM deadline_list d CROSS JOIN report_day r
  WHERE d.done_on IS NULL AND d.due_on >= r.as_of AND d.due_on <= date(r.as_of, '+30 days');

CREATE VIEW overdue AS
  SELECT r.as_of, d.code, d.title, d.owner_role, d.due_on,
         CAST(julianday(r.as_of) - julianday(d.due_on) AS INTEGER) AS days_late
  FROM deadline_list d CROSS JOIN report_day r
  WHERE d.done_on IS NULL AND d.due_on < r.as_of;

CREATE VIEW licences_expiring AS
  SELECT r.as_of, l.source_ref, l.regulator, l.expires_on, l.last_synced AS copy_taken_on,
         CASE WHEN julianday(r.as_of) - julianday(l.last_synced) > h.max_age_days THEN 1 ELSE 0 END
           AS copy_is_stale
  FROM licence l CROSS JOIN report_day r JOIN record_home h ON h.table_name = 'licence'
  WHERE l.expires_on >= r.as_of AND l.expires_on <= date(r.as_of, '+90 days');

CREATE VIEW months_not_reconciled AS
  SELECT month, difference, frozen_on FROM month_close WHERE reconciled = 0 OR difference <> 0;

CREATE VIEW fees_paid_by_deadline AS
  SELECT d.code, d.title, COALESCE(SUM(b.amount), 0) AS paid, MAX(b.last_synced) AS copy_taken_on
  FROM deadline_list d LEFT JOIN paid_bill b ON b.match_ref = d.code
  GROUP BY d.id HAVING COUNT(b.id) > 0;

CREATE VIEW unmatched_bills AS
  SELECT b.source_ref, b.amount, b.match_ref
  FROM paid_bill b LEFT JOIN deadline_list d ON d.code = b.match_ref
  WHERE d.code IS NULL;

CREATE VIEW money_paid_total AS
  SELECT COALESCE(SUM(amount), 0) AS paid, MAX(last_synced) AS copy_taken_on FROM paid_bill;

CREATE VIEW open_exceptions AS
  SELECT COUNT(*) AS open_count, MIN(opened_on) AS oldest_opened_on
  FROM onboarding_exception WHERE closed_on IS NULL;

CREATE VIEW stale_copies AS
  SELECT h.kind, h.table_name, m.last_copy, h.max_age_days, r.as_of,
         CAST(julianday(r.as_of) - julianday(m.last_copy) AS INTEGER) AS age_days
  FROM record_home h
  JOIN (SELECT 'licence' AS t, MAX(last_synced) AS last_copy FROM licence
        UNION ALL SELECT 'paid_bill', MAX(last_synced) FROM paid_bill) m ON m.t = h.table_name
  CROSS JOIN report_day r
  WHERE h.role = 'mirror'
    AND (m.last_copy IS NULL OR julianday(r.as_of) - julianday(m.last_copy) > h.max_age_days);

CREATE INDEX ix_licence_request_deadline ON licence_request(deadline_id);
CREATE INDEX ix_paid_bill_match ON paid_bill(match_ref);

PRAGMA user_version = 1;
