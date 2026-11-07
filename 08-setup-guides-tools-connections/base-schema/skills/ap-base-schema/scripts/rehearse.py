#!/usr/bin/env python3
"""Rehearse a build on a throwaway copy, before anything real is built.

  rehearse.py <build-manifest.json> [--scratch <directory>] [--keep]

Builds a throwaway SQLite file in a temp folder from the manifest's migrations, fills
record_home from the map, loads every made-up fixture in order (copies only through the
import step), and runs: each migrate checkpoint's readback, each fixture's checks, the Monday
numbers, the built-in guard checks for every copy, request and frozen-figure table, undo of
every migration, and restore from a backup. Prints PASS/FAIL per check, then deletes the temp
folder (unless --keep). It never opens the target database named in the manifest.

Migration SQL is screened and constrained with SQLite connection defenses before it can run,
and runs with the temp folder as cwd. This is defense in depth, not an OS sandbox; see SKILL.md.

Exit 0 = all pass, 1 = a check failed, 2 = could not run (manifest errors, unwritten migrations).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("check_manifest", HERE / "check_manifest.py")
cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cm)

RECEIPT_COLS = {"sync_status", "last_synced", "sync_note"}
PROBE = "rehearsal_probe"
MACHINE_CHECKS = {"tables_exist", "views_exist", "triggers_exist", "columns_match", "user_version",
                  "foreign_key_check_empty", "integrity_check_ok", "row_count", "query_returns",
                  "refused", "same_as_backup"}
DANGEROUS_FUNCTIONS = {"edit", "load_extension", "readfile", "writefile", "zipfile"}
DANGEROUS_PRAGMAS = {
    "data_store_directory", "journal_mode", "legacy_file_format", "temp_store_directory",
    "temp_store", "trusted_schema", "wal_checkpoint", "writable_schema",
}
TRANSACTION_CONTROL = {"BEGIN", "COMMIT", "END", "ROLLBACK", "SAVEPOINT", "RELEASE"}


class UnsafeMigrationError(sqlite3.DatabaseError):
    """Migration SQL asked SQLite for an operation outside rehearsal containment."""


def _sql_code(sql: str, preserve_identifiers: bool = False) -> str:
    """Replace comments and quoted regions so safety checks see only executable tokens."""
    out: list[str] = []
    i = 0
    while i < len(sql):
        pair = sql[i:i + 2]
        if pair == "--":
            end = sql.find("\n", i + 2)
            i = len(sql) if end < 0 else end
            out.append(" ")
        elif pair == "/*":
            end = sql.find("*/", i + 2)
            if end < 0:
                raise UnsafeMigrationError("unsafe migration SQL: unterminated block comment")
            i = end + 2
            out.append(" ")
        elif sql[i] in "'\"`[":
            opener = sql[i]
            closer = "]" if opener == "[" else opener
            i += 1
            identifier: list[str] = []
            while i < len(sql):
                if sql[i] == closer:
                    if closer != "]" and i + 1 < len(sql) and sql[i + 1] == closer:
                        identifier.append(closer)
                        i += 2
                        continue
                    i += 1
                    break
                identifier.append(sql[i])
                i += 1
            else:
                raise UnsafeMigrationError("unsafe migration SQL: unterminated quoted value")
            out.append("".join(identifier) if preserve_identifiers and opener != "'" else " ")
        else:
            out.append(sql[i])
            i += 1
    return "".join(out)


def split_migration_sql(sql: str) -> list[str]:
    """Split SQL where SQLite reports complete statements, including trigger bodies."""
    statements: list[str] = []
    pending: list[str] = []
    for character in sql:
        pending.append(character)
        if character == ";" and sqlite3.complete_statement("".join(pending)):
            statement = "".join(pending).strip()
            if _sql_code(statement).strip():
                statements.append(statement)
            pending.clear()
    remainder = "".join(pending)
    if _sql_code(remainder).strip():
        if not sqlite3.complete_statement(remainder + ";"):
            raise UnsafeMigrationError("unsafe migration SQL: incomplete SQL statement")
        statements.append(remainder.strip())
    return statements


def validate_migration_sql(sql: str) -> list[str]:
    """Return complete statements after rejecting operations outside containment."""
    statements = split_migration_sql(sql)
    callable_code = _sql_code(sql, preserve_identifiers=True)
    for statement in statements:
        code = _sql_code(statement).strip()
        normalized = code[:-1].rstrip() if code.endswith(";") else code
        first = re.match(r"([A-Z]+)\b", normalized, re.IGNORECASE)
        if first and first.group(1).upper() in TRANSACTION_CONTROL:
            raise UnsafeMigrationError(
                "unsafe migration SQL: top-level transaction-control statements are forbidden")
        if re.search(r"\b(ATTACH|DETACH|VACUUM)\b", normalized, re.IGNORECASE):
            raise UnsafeMigrationError("unsafe migration SQL: ATTACH, DETACH and VACUUM are forbidden")
        if re.match(r"^PRAGMA\b", normalized, re.IGNORECASE) and not (
                re.fullmatch(r"PRAGMA\s+(?:main\.)?user_version\s*=\s*[0-9]+", normalized, re.IGNORECASE)
                or re.fullmatch(r"PRAGMA\s+foreign_keys\s*=\s*(?:ON|1)", normalized, re.IGNORECASE)):
            raise UnsafeMigrationError(
                "unsafe migration SQL: only PRAGMA foreign_keys = ON and user_version = <integer> are allowed")
        if re.search(r"\bCREATE\s+VIRTUAL\s+TABLE\b", normalized, re.IGNORECASE):
            raise UnsafeMigrationError("unsafe migration SQL: virtual tables are forbidden")
    functions = "|".join(sorted(DANGEROUS_FUNCTIONS))
    if re.search(rf"\b(?:{functions})\s*\(", callable_code, re.IGNORECASE):
        raise UnsafeMigrationError("unsafe migration SQL: external-file SQL functions are forbidden")
    return statements


def containment_authorizer(action, arg1, arg2, _database, _trigger):
    """Second line of defense, including dangerous operations hidden in views/triggers."""
    if action in {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
                  sqlite3.SQLITE_CREATE_VTABLE, sqlite3.SQLITE_DROP_VTABLE}:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA and (arg1 or "").lower() in DANGEROUS_PRAGMAS:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or arg1 or "").lower() in DANGEROUS_FUNCTIONS:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


class Rehearsal:
    def __init__(self, manifest: dict, base: Path, work: Path):
        self.m = manifest
        self.base = base
        self.work = work
        self.results: list[tuple[str, bool, str]] = []
        self.roles = {l["table"]: l["role"] for l in manifest["record_home_map"] if l["table"]}
        self.as_of = manifest["acceptance"]["as_of"]

    # -- plumbing -----------------------------------------------------------------------
    def record(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append((name, bool(ok), detail))

    @staticmethod
    def connect(path: Path) -> sqlite3.Connection:
        con = sqlite3.connect(path, isolation_level=None)
        con.enable_load_extension(False)
        if hasattr(con, "setconfig"):
            for name, enabled in (
                    ("SQLITE_DBCONFIG_DEFENSIVE", True),
                    ("SQLITE_DBCONFIG_ENABLE_LOAD_EXTENSION", False),
                    ("SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER", False),
                    ("SQLITE_DBCONFIG_TRUSTED_SCHEMA", False),
                    ("SQLITE_DBCONFIG_WRITABLE_SCHEMA", False)):
                option = getattr(sqlite3, name, None)
                if option is not None:
                    con.setconfig(option, enabled)
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA temp_store = MEMORY")
        con.execute("PRAGMA trusted_schema = OFF")
        con.set_authorizer(containment_authorizer)
        return con

    def migration_sql(self, g: dict, side: str) -> str:
        return (self.base / g[f"{side}_file"]).read_text(encoding="utf-8")

    @staticmethod
    def apply(con: sqlite3.Connection, sql: str) -> None:
        statements = validate_migration_sql(sql)
        con.execute("BEGIN")
        try:
            for statement in statements:
                con.execute(statement)
            con.execute("COMMIT")
        except BaseException:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise

    @staticmethod
    def names(con, kind: str) -> set[str]:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,))}

    @staticmethod
    def columns(con, table: str) -> list[str]:
        return [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]

    @staticmethod
    def data_hash(con) -> str:
        h = hashlib.sha256()
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            h.update(t.encode())
            for row in con.execute(f'SELECT * FROM "{t}" ORDER BY rowid'):
                h.update(repr(row).encode())
        return h.hexdigest()

    @staticmethod
    def shape(con) -> list:
        out = []
        for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            out.append((t, tuple(r[1:6] for r in con.execute(f'PRAGMA table_info("{t}")'))))
        out.append(tuple(sorted(con.execute(
            "SELECT type, name, tbl_name FROM sqlite_master WHERE type IN ('view','trigger','index')"))))
        return out

    @staticmethod
    def same(a, b) -> bool:
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            return len(a) == len(b) and all(Rehearsal.same(x, y) for x, y in zip(a, b))
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) \
                and not isinstance(a, bool) and not isinstance(b, bool):
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
        return a == b

    def probe(self, con, sql: str, params=()) -> tuple[bool, str]:
        """Run a write that must be refused; always undone. Returns (refused, message)."""
        con.execute(f"SAVEPOINT {PROBE}")
        try:
            con.execute(sql, params)
            return False, "NOT refused"
        except sqlite3.DatabaseError as e:
            return True, str(e)
        finally:
            con.execute(f"ROLLBACK TO {PROBE}")
            con.execute(f"RELEASE {PROBE}")

    def restore_check(self, con) -> tuple[bool, str]:
        before_hash, before_shape = self.data_hash(con), self.shape(con)
        backup = self.work / "rehearsal-backup.db"
        backup.unlink(missing_ok=True)
        dest = sqlite3.connect(backup)
        con.backup(dest)
        dest.close()
        con.execute("CREATE TABLE rehearsal_bad_change (x TEXT)")
        con.execute("INSERT INTO rehearsal_bad_change VALUES ('a deliberate bad change')")
        src = sqlite3.connect(backup)
        src.backup(con)
        src.close()
        ok = self.data_hash(con) == before_hash and self.shape(con) == before_shape
        return ok, "" if ok else "restored file differs from the backup"

    # -- import step (the only writer of copy tables) ----------------------------------
    def import_rows(self, con, table: str, rows: list[dict], export_date: str, note: str | None,
                    crash_after: int | None = None) -> dict:
        seen: dict[str, dict] = {}
        rejected: set[str] = set()
        for r in rows:
            ref = r["source_ref"]
            if ref in seen and seen[ref] != r:
                rejected.add(ref)
            seen.setdefault(ref, r)
        clean = [r for ref, r in seen.items() if ref not in rejected]
        cols = sorted({c for r in clean for c in r if c not in RECEIPT_COLS},
                      key=lambda c: (c != "source_ref", c))
        all_cols = cols + ["sync_status", "last_synced", "sync_note"]
        sets = ", ".join(f'"{c}" = excluded."{c}"' for c in all_cols if c != "source_ref")
        sql = (f'INSERT INTO "{table}" ({", ".join(chr(34) + c + chr(34) for c in all_cols)}) '
               f'VALUES ({", ".join("?" * len(all_cols))}) ON CONFLICT(source_ref) DO UPDATE SET {sets}')
        before = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        log_before = con.execute("SELECT COUNT(*) FROM import_log").fetchone()[0]
        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute("UPDATE import_guard SET open = 1")
            for i, r in enumerate(clean):
                if crash_after is not None and i == crash_after:
                    raise RuntimeError("simulated crash mid-import")
                con.execute(sql, [r.get(c) for c in cols] + ["imported_by_hand", export_date, note])
            con.execute("UPDATE import_guard SET open = 0")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        return {"new_rows": con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] - before,
                "values_changed": con.execute("SELECT COUNT(*) FROM import_log").fetchone()[0] - log_before,
                "rejected": sorted(rejected)}

    # -- checks -------------------------------------------------------------------------
    def run_check(self, con, chk: dict) -> tuple[bool, str]:
        kind, target, expect = chk["check"], chk["target"], chk.get("expect")
        targets = [target] if isinstance(target, str) else target
        if kind in ("tables_exist", "views_exist", "triggers_exist"):
            missing = set(targets) - self.names(con, kind.split("s_")[0])
            return not missing, f"missing: {sorted(missing)}" if missing else ""
        if kind == "columns_match":
            got = self.columns(con, target)
            return got == expect, f"got {got}"
        if kind == "user_version":
            got = con.execute("PRAGMA user_version").fetchone()[0]
            return got == expect, f"got {got}"
        if kind == "foreign_key_check_empty":
            got = con.execute("PRAGMA foreign_key_check").fetchall()
            return not got, f"got {got[:3]}"
        if kind == "integrity_check_ok":
            got = con.execute("PRAGMA integrity_check").fetchone()[0]
            return got == "ok", f"got {got}"
        if kind in ("row_count", "query_returns"):
            is_name = re.fullmatch(r"[a-z][a-z0-9_]{1,40}", target) is not None
            if kind == "row_count":
                sql = f'SELECT COUNT(*) FROM "{target}"' if is_name else target
                got = con.execute(sql).fetchone()[0]
                return got == expect, f"got {got}"
            rows = [list(r) for r in con.execute(f'SELECT * FROM "{target}"' if is_name else target)]
            if isinstance(expect, list):
                return self.same(rows, expect), f"got {rows}"
            got = rows[0][0] if len(rows) == 1 and len(rows[0]) == 1 else rows
            return self.same(got, expect), f"got {got}"
        if kind == "refused":
            refused, msg = self.probe(con, target)
            return refused and expect in msg, msg
        if kind == "same_as_backup":
            return self.restore_check(con)
        return False, f"{kind} can't run in a rehearsal"

    def load_fixture(self, con, f: dict) -> None:
        for table, rows in f["rows"].items():
            if table == "record_home":
                for r in rows:
                    cols = list(r)
                    con.execute(f'INSERT INTO record_home ({", ".join(cols)}) VALUES ({", ".join("?" * len(cols))}) '
                                f'ON CONFLICT(kind) DO UPDATE SET '
                                + ", ".join(f"{c} = excluded.{c}" for c in cols if c != "kind"),
                                [r[c] for c in cols])
            elif table == "settings":
                for r in rows:
                    con.execute(f'UPDATE settings SET {", ".join(f"{c} = ?" for c in r)} WHERE id = 1', list(r.values()))
            elif self.roles.get(table) == "mirror":
                by_date: dict[str, list[dict]] = {}
                for r in rows:
                    by_date.setdefault(r.get("last_synced", self.as_of), []).append(
                        {k: v for k, v in r.items() if k != "last_synced"})
                for export_date, batch in by_date.items():
                    self.import_rows(con, table, batch, export_date, f"rehearsal {f['id']}")
            else:
                for r in rows:
                    cols = list(r)
                    con.execute(f'INSERT INTO "{table}" ({", ".join(chr(34) + c + chr(34) for c in cols)}) '
                                f'VALUES ({", ".join("?" * len(cols))})', [r[c] for c in cols])

    # -- built-in guard checks, for every table the map gives a guarded role -------------
    def guard_checks(self, con) -> None:
        for table, role in self.roles.items():
            con.row_factory = sqlite3.Row
            row = con.execute(f'SELECT * FROM "{table}" ORDER BY rowid LIMIT 1').fetchone()
            con.row_factory = None
            if role in ("mirror", "intake", "snapshot") and row is None:
                self.record(f"guard {table}: has a fixture row to test with", False, "no rows")
                continue
            if role == "mirror":
                self.mirror_checks(con, table, dict(row))
            elif role == "intake":
                self.intake_checks(con, table)
            elif role == "snapshot":
                self.snapshot_checks(con, table, dict(row))

    @staticmethod
    def changed(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v + 1
        return (v or "") + "#changed"

    def mirror_checks(self, con, table: str, row: dict) -> None:
        business = [c for c in self.columns(con, table) if c != "id" and c not in RECEIPT_COLS]
        for label, sql, params in (
                ("change", f'UPDATE "{table}" SET sync_note = sync_note WHERE id = ?', (row["id"],)),
                ("delete", f'DELETE FROM "{table}" WHERE id = ?', (row["id"],)),
                ("type in", f'INSERT INTO "{table}" ({", ".join(business + ["sync_status", "last_synced"])}) '
                            f'VALUES ({", ".join("?" * (len(business) + 2))})',
                 [row["source_ref"] + "#rehearsal-insert" if c == "source_ref" else row[c] for c in business]
                 + ["imported_by_hand", self.as_of])):
            refused, msg = self.probe(con, sql, params)
            self.record(f"guard {table}: {label} outside the import step is refused", refused and "is a copy" in msg, msg)
        con.row_factory = sqlite3.Row
        current = [dict(r) for r in con.execute(f'SELECT * FROM "{table}"')]
        con.row_factory = None
        by_receipt: dict[tuple[str, str | None], list[dict]] = {}
        for r in current:
            by_receipt.setdefault((r["last_synced"], r["sync_note"]), []).append(
                {c: r[c] for c in business})
        again = [self.import_rows(con, table, rows, date, note)
                 for (date, note), rows in by_receipt.items()]
        self.record(f"guard {table}: importing the same rows again adds and changes nothing",
                    all(x["new_rows"] == 0 and x["values_changed"] == 0 for x in again), str(again))
        synth = [{**{c: row[c] for c in business}, "source_ref": f"{row['source_ref']}#rehearsal-crash-{i}"}
                 for i in (1, 2)]
        try:
            self.import_rows(con, table, synth, self.as_of, "rehearsal crash", crash_after=1)
            crashed = False
        except RuntimeError:
            crashed = True
        left = con.execute(f'SELECT COUNT(*) FROM "{table}" WHERE source_ref LIKE ?',
                           (f"{row['source_ref']}#rehearsal-crash-%",)).fetchone()[0]
        guard = con.execute("SELECT open FROM import_guard").fetchone()[0]
        self.record(f"guard {table}: a crash mid-import leaves nothing half-written and the lock shut",
                    crashed and left == 0 and guard == 0, f"left={left} guard={guard}")
        other = next((c for c in business if c != "source_ref"), None)
        if other:
            base_row = {c: row[c] for c in business}
            ref = f"{row['source_ref']}#rehearsal-conflict"
            res = self.import_rows(con, table, [{**base_row, "source_ref": ref},
                                                {**base_row, "source_ref": ref, other: self.changed(row[other])}],
                                   self.as_of, "rehearsal conflict")
            n = con.execute(f'SELECT COUNT(*) FROM "{table}" WHERE source_ref = ?', (ref,)).fetchone()[0]
            self.record(f"guard {table}: two different lines with one number are rejected, not guessed",
                        res["rejected"] == [ref] and n == 0, str(res))
        marker = con.execute("SELECT COALESCE(MAX(id), 0) FROM import_log").fetchone()[0]
        audit_row = {c: row[c] if c == "source_ref" else self.changed(row[c]) for c in business}
        self.import_rows(con, table, [audit_row], "2099-12-30", "rehearsal audit coverage")
        logged = [r[0] for r in con.execute(
            "SELECT field FROM import_log WHERE id > ? AND table_name = ? AND source_ref = ? ORDER BY field",
            (marker, table, row["source_ref"]))]
        expected = sorted(c for c in self.columns(con, table)
                          if c not in {"id", "source_ref", "sync_status"})
        self.record(f"guard {table}: every changed non-ID field is logged",
                    logged == expected, f"logged={logged} expected={expected}")

    def intake_checks(self, con, table: str) -> None:
        cols = self.columns(con, table)
        if not {"handed_over_on", "returned_ref"} <= set(cols):
            self.record(f"guard {table}: has handed_over_on and returned_ref", False, f"columns: {cols}")
            return
        con.row_factory = sqlite3.Row
        row = con.execute(f'SELECT * FROM "{table}" WHERE handed_over_on IS NOT NULL LIMIT 1').fetchone()
        con.row_factory = None
        if row is None:
            self.record(f"guard {table}: has a handed-over fixture row", False, "none")
            return
        refused, msg = self.probe(con, f'UPDATE "{table}" SET handed_over_on = ? WHERE id = ?', ("1900-01-01", row["id"]))
        self.record(f"guard {table}: a handed-over request can't be changed", refused and "handed over" in msg, msg)
        if row["returned_ref"] is not None:
            refused, msg = self.probe(con, f'UPDATE "{table}" SET returned_ref = ? WHERE id = ?',
                                      (row["returned_ref"] + "#changed", row["id"]))
            self.record(f"guard {table}: the returned number can't be changed once filled", refused and "handed over" in msg, msg)
        refused, msg = self.probe(con, f'DELETE FROM "{table}" WHERE id = ?', (row["id"],))
        self.record(f"guard {table}: a handed-over request can't be deleted", refused, msg)

    def snapshot_checks(self, con, table: str, row: dict) -> None:
        info = list(con.execute(f'PRAGMA table_info("{table}")'))
        pk = [r[1] for r in info if r[5]]
        rest = [r[1] for r in info if not r[5]]
        where = " AND ".join(f'"{c}" = ?' for c in pk)
        keys = [row[c] for c in pk]
        if rest:
            refused, msg = self.probe(con, f'UPDATE "{table}" SET "{rest[0]}" = ? WHERE {where}',
                                      [self.changed(row[rest[0]])] + keys)
            self.record(f"guard {table}: a frozen figure can't be changed", refused and "frozen" in msg, msg)
        refused, msg = self.probe(con, f'DELETE FROM "{table}" WHERE {where}', keys)
        self.record(f"guard {table}: a frozen figure can't be deleted", refused and "frozen" in msg, msg)
        cols = list(row)
        refused, msg = self.probe(con, f'INSERT INTO "{table}" ({", ".join(chr(34) + c + chr(34) for c in cols)}) '
                                       f'VALUES ({", ".join("?" * len(cols))})', [row[c] for c in cols])
        self.record(f"guard {table}: a second figure for the same period is refused", refused, msg)

    # -- the whole rehearsal ------------------------------------------------------------
    def run(self) -> None:
        m = self.m
        self.record("migration SQL runs from the isolated rehearsal folder", Path.cwd() == self.work,
                    f"cwd={Path.cwd()} work={self.work}")
        db = self.work / "rehearsal.db"
        con = self.connect(db)
        self.record("SQLite has STRICT tables (3.37+)", sqlite3.sqlite_version_info >= (3, 37, 0), sqlite3.sqlite_version)
        migrate_cps = {c["migration"]: c for c in m["checkpoints"] if c["kind"] == "migrate"}
        for g in m["migrations"]:
            try:
                self.apply(con, self.migration_sql(g, "up"))
                self.record(f"{g['id']} up applies", True)
            except sqlite3.DatabaseError as e:
                self.record(f"{g['id']} up applies", False, str(e))
                return
            for chk in migrate_cps[g["id"]]["readback"]:
                if chk["check"] in MACHINE_CHECKS:
                    ok, detail = self.run_check(con, chk)
                    self.record(f"{migrate_cps[g['id']]['id']} readback: {chk['check']}", ok, detail)

        extra = self.names(con, "table") - set(self.roles) - cm.META_TABLES - {"sqlite_sequence"}
        self.record("every table has a line in the map", not extra, f"no line: {sorted(extra)}")
        if "record_home" in self.names(con, "table"):
            for l in m["record_home_map"]:
                con.execute("INSERT INTO record_home (kind, table_name, role, max_age_days) VALUES (?,?,?,?)",
                            (l["kind"], l["table"], l["role"], l["freshness"]["max_age_days"]))
        elif "mirror" in self.roles.values():
            self.record("record_home table exists (the map has copies)", False)
        has_clock = "settings" in self.names(con, "table") and "as_of_override" in self.columns(con, "settings")
        if has_clock:
            con.execute("UPDATE settings SET as_of_override = ? WHERE id = 1", (self.as_of,))
        else:
            self.record("settings.as_of_override exists, so results don't depend on today's date", False)

        for f in m["acceptance"]["fixtures"]:
            try:
                self.load_fixture(con, f)
            except sqlite3.DatabaseError as e:
                self.record(f"{f['id']} loads", False, str(e))
                continue
            for chk in f["then"]:
                ok, detail = self.run_check(con, chk)
                self.record(f"{f['id']} {f['case']}: {chk['check']} {str(chk['target'])[:60]}", ok, detail)

        for q in m["acceptance"]["metrics"]:
            cols = ", ".join(f'"{c}"' for c in q["columns"]) if q.get("columns") else "*"
            try:
                rows = [list(r) for r in con.execute(f'SELECT {cols} FROM "{q["answered_by"]}"')]
                self.record(f"{q['id']} {q['monday_question'][:60]}", self.same(rows, q["expected_with_fixtures"]), f"got {rows}")
            except sqlite3.DatabaseError as e:
                self.record(f"{q['id']} {q['monday_question'][:60]}", False, str(e))

        self.guard_checks(con)
        self.record("foreign keys clean", not con.execute("PRAGMA foreign_key_check").fetchall())
        self.record("integrity ok", con.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
        ok, detail = self.restore_check(con)
        self.record("restore from backup gives back the exact contents", ok, detail)
        con.close()

        fresh = self.connect(self.work / "undo.db")
        for g in m["migrations"]:
            self.apply(fresh, self.migration_sql(g, "up"))
        built = self.shape(fresh)
        try:
            for g in reversed(m["migrations"]):
                self.apply(fresh, self.migration_sql(g, "down"))
            left = fresh.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            version = fresh.execute("PRAGMA user_version").fetchone()[0]
            self.record("undoing every migration leaves an empty file at version 0",
                        not left and version == 0, f"left={left} version={version}")
            for g in m["migrations"]:
                self.apply(fresh, self.migration_sql(g, "up"))
            self.record("building again after undo gives the same shape", self.shape(fresh) == built)
        except sqlite3.DatabaseError as e:
            self.record("undo migrations apply", False, str(e))
        fresh.close()


def main(argv: list[str]) -> int:
    cm.ensure_jsonschema(Path(__file__).resolve(), argv)
    ap = argparse.ArgumentParser(description="Rehearse a base-schema build on a throwaway copy.")
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--scratch", type=Path,
                    help="existing approved directory in which to create the throwaway folder")
    ap.add_argument("--keep", action="store_true", help="keep the temp folder for inspection")
    a = ap.parse_args(argv)
    m, errors, warnings, notes = cm.check(a.manifest)
    if errors:
        for e in errors:
            print(f"ERROR  {e}")
        print("could not rehearse: fix the manifest first")
        return 2
    unwritten = [g["id"] for g in m["migrations"] if g["up_sha256"] is None or g["down_sha256"] is None]
    if unwritten:
        print(f"could not rehearse: migrations not written and fingerprinted yet: {', '.join(unwritten)}")
        return 2
    scratch = a.scratch.resolve() if a.scratch else None
    if scratch is not None and (not scratch.is_dir() or not os.access(scratch, os.W_OK)):
        print(f"could not rehearse: scratch directory is missing or not writable: {scratch}")
        return 2
    manifest_dir = a.manifest.resolve().parent
    if scratch is not None and (scratch == manifest_dir or manifest_dir in scratch.parents):
        print("could not rehearse: scratch directory must be outside the manifest folder")
        return 2
    work = Path(tempfile.mkdtemp(prefix="base-schema-rehearsal-", dir=scratch)).resolve()
    r = Rehearsal(m, a.manifest.resolve().parent, work)
    original_cwd = Path.cwd()
    try:
        os.chdir(work)
        r.run()
    finally:
        os.chdir(original_cwd)
        if not a.keep:
            shutil.rmtree(work, ignore_errors=True)
    width = max(len(n) for n, _, _ in r.results)
    for name, ok, detail in r.results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {'' if ok else detail}".rstrip())
    for w in warnings:
        print(f"WARN  {w}")
    failed = sum(1 for _, ok, _ in r.results if not ok)
    print(f"\n{m['build_id']} rev {m['revision']}: {len(r.results) - failed}/{len(r.results)} checks passed "
          f"(SQLite {sqlite3.sqlite_version}). Temp folder {'kept: ' + str(work) if a.keep else 'removed'}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
