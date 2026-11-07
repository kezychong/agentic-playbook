#!/usr/bin/env python3
"""Deterministic security and correctness regressions for Base Schema."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
EXAMPLE = SKILL_DIR / "templates" / "example-manifest"
REHEARSE = HERE / "rehearse.py"
CHECK = HERE / "check_manifest.py"
_REHEARSE_SPEC = importlib.util.spec_from_file_location("base_schema_rehearse", REHEARSE)
assert _REHEARSE_SPEC is not None and _REHEARSE_SPEC.loader is not None
rehearse = importlib.util.module_from_spec(_REHEARSE_SPEC)
_REHEARSE_SPEC.loader.exec_module(rehearse)


class BaseSchemaRegressions(unittest.TestCase):
    def setUp(self) -> None:
        scratch_root = Path(os.environ.get("TMPDIR", tempfile.gettempdir()))
        self.temp = Path(tempfile.mkdtemp(prefix="base-schema-regression-", dir=scratch_root))
        self.example = self.temp / "example"
        shutil.copytree(EXAMPLE, self.example)
        self.manifest_path = self.example / "build-manifest.json"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def load_manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def save_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def run_script(self, script: Path, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            cwd=self.temp,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_rehearsal_rejects_external_file_sql_before_it_can_escape(self) -> None:
        escaped = self.temp / "escaped.db"
        migration = self.example / "migrations" / "M001-up.sql"
        original = migration.read_text(encoding="utf-8")
        hostile = {
            "attach": f"ATTACH DATABASE '{escaped}' AS escaped;",
            "detach": "DETACH DATABASE main;",
            "vacuum_into": f"VACUUM INTO '{escaped}';",
            "writable_schema": "PRAGMA writable_schema = ON;",
            "wal_mode": "PRAGMA journal_mode = WAL;",
            "temp_directory": f"PRAGMA temp_store_directory = '{self.temp}';",
            "load_extension": "SELECT load_extension('hostile');",
            "file_function": f"SELECT writefile('{escaped}', 'hostile');",
            "authorizer_quoted_function": f"SELECT \"writefile\"('{escaped}', 'hostile');",
            "virtual_table": "CREATE VIRTUAL TABLE hostile USING fts5(body);",
        }
        for label, payload in hostile.items():
            with self.subTest(label=label):
                escaped.unlink(missing_ok=True)
                migration.write_text(payload + "\n" + original, encoding="utf-8")
                manifest = self.load_manifest()
                manifest["migrations"][0]["up_sha256"] = hashlib.sha256(migration.read_bytes()).hexdigest()
                self.save_manifest(manifest)

                result = self.run_script(REHEARSE, self.manifest_path, "--scratch", self.temp)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                refusal = result.stdout + result.stderr
                self.assertTrue(
                    "unsafe migration SQL" in refusal or "not authorized" in refusal,
                    refusal,
                )
                self.assertFalse(escaped.exists(), "hostile migration escaped the rehearsal folder")

    def test_rehearsal_rejects_top_level_transaction_control(self) -> None:
        migration = self.example / "migrations" / "M001-up.sql"
        original = migration.read_text(encoding="utf-8")
        migration.write_text("COMMIT; BEGIN;\n" + original, encoding="utf-8")
        manifest = self.load_manifest()
        manifest["migrations"][0]["up_sha256"] = hashlib.sha256(migration.read_bytes()).hexdigest()
        self.save_manifest(manifest)

        result = self.run_script(REHEARSE, self.manifest_path, "--scratch", self.temp)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("transaction-control", result.stdout + result.stderr)

    def test_validator_rejects_every_top_level_transaction_control_family(self) -> None:
        hostile = (
            "BEGIN;",
            "begin immediate transaction;",
            "COMMIT TRANSACTION;",
            "END TRANSACTION;",
            "ROLLBACK TRANSACTION;",
            "ROLLBACK TO outer_savepoint;",
            "SAVEPOINT outer_savepoint;",
            "RELEASE SAVEPOINT outer_savepoint;",
        )
        for statement in hostile:
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(rehearse.UnsafeMigrationError, "transaction-control"):
                    rehearse.validate_migration_sql(statement)

    def test_statement_splitter_preserves_triggers_and_quoted_semicolons(self) -> None:
        con = rehearse.Rehearsal.connect(self.temp / "trigger.db")
        try:
            rehearse.Rehearsal.apply(con, """
                CREATE TABLE source (value TEXT);
                CREATE TABLE audit (value TEXT);
                CREATE TRIGGER source_audit AFTER INSERT ON source
                BEGIN
                  INSERT INTO audit VALUES ('trigger;body');
                END;
                INSERT INTO source VALUES ('outer;value');
                PRAGMA user_version = 7;
            """)

            self.assertEqual(con.execute("SELECT value FROM source").fetchone(), ("outer;value",))
            self.assertEqual(con.execute("SELECT value FROM audit").fetchone(), ("trigger;body",))
            self.assertEqual(con.execute("PRAGMA user_version").fetchone(), (7,))
        finally:
            con.close()

    def test_migration_rolls_back_all_statements_when_a_later_statement_fails(self) -> None:
        con = rehearse.Rehearsal.connect(self.temp / "atomic.db")
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                rehearse.Rehearsal.apply(con, """
                    CREATE TABLE must_not_survive (value TEXT);
                    INSERT INTO must_not_survive VALUES ('written before failure');
                    CREATE TABLE must_not_survive (other TEXT);
                """)

            self.assertIsNone(con.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'must_not_survive'"
            ).fetchone())
            self.assertFalse(con.in_transaction)
        finally:
            con.close()

    def test_for_build_refuses_every_open_blocker(self) -> None:
        manifest = self.load_manifest()
        manifest["truth"] = "confirmed"
        manifest["approval"] = {
            "state": "approved_for_build",
            "by": "Fictional owner",
            "on": "2026-10-15",
            "proof": "Fictional approval used only by this regression",
        }
        self.save_manifest(manifest)

        result = self.run_script(CHECK, self.manifest_path, "--for-build")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("open blocker B02", result.stdout + result.stderr)

    def test_for_build_refuses_revision_without_exact_previous_chain(self) -> None:
        manifest = self.load_manifest()
        manifest["revision"] = 2
        manifest["supersedes_sha256"] = "0" * 64
        manifest["truth"] = "confirmed"
        manifest["approval"] = {
            "state": "approved_for_build",
            "by": "Fictional owner",
            "on": "2026-10-15",
            "proof": "Fictional approval used only by this regression",
        }
        for blocker in manifest["blockers"]:
            blocker.update({
                "status": "answered",
                "answer": "Fictional test answer",
                "answered_by": "Fictional owner",
                "answered_on": "2026-10-15",
            })
        self.save_manifest(manifest)

        result = self.run_script(CHECK, self.manifest_path, "--for-build")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("revision 2 requires --previous", result.stdout + result.stderr)

    def test_checker_refuses_impossible_calendar_dates(self) -> None:
        manifest = self.load_manifest()
        manifest["made_on"] = "2026-02-30"
        self.save_manifest(manifest)

        result = self.run_script(CHECK, self.manifest_path)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("2026-02-30", result.stdout + result.stderr)
        self.assertIn("not a 'date'", result.stdout + result.stderr)

    def test_licence_expiry_view_includes_both_boundaries_but_not_expired_rows(self) -> None:
        manifest = self.load_manifest()
        fixture = next(item for item in manifest["acceptance"]["fixtures"] if item["id"] == "FX06")
        common = {"regulator": "Regulator A", "status_in_home": "active", "last_synced": "2026-10-01"}
        fixture["rows"]["licence"].extend([
            {"source_ref": "RA-EXPIRED", "expires_on": "2026-11-19", **common},
            {"source_ref": "RA-TODAY", "expires_on": "2026-11-20", **common},
            {"source_ref": "RA-DAY-90", "expires_on": "2027-02-18", **common},
        ])
        expected = [
            ["RA-0001-X", "2027-01-31", "2026-10-01", 1],
            ["RA-TODAY", "2026-11-20", "2026-10-01", 1],
            ["RA-DAY-90", "2027-02-18", "2026-10-01", 1],
        ]
        fixture["then"][0]["expect"] = expected
        metric = next(item for item in manifest["acceptance"]["metrics"] if item["id"] == "Q03")
        metric["expected_with_fixtures"] = expected
        self.save_manifest(manifest)

        result = self.run_script(REHEARSE, self.manifest_path, "--scratch", self.temp)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("RA-EXPIRED", result.stdout + result.stderr)

    def test_rehearsal_proves_every_changed_mirror_field_is_audited(self) -> None:
        result = self.run_script(REHEARSE, self.manifest_path, "--scratch", self.temp)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("guard paid_bill: every changed non-ID field is logged", result.stdout)
        self.assertIn("guard licence: every changed non-ID field is logged", result.stdout)

    def test_rehearsal_runs_from_its_isolated_working_directory(self) -> None:
        result = self.run_script(REHEARSE, self.manifest_path, "--scratch", self.temp)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("migration SQL runs from the isolated rehearsal folder", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
