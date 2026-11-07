#!/usr/bin/env python3
"""Offline regression tests for check_video_plan.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from check_video_plan import MAX_BYTES, load_plan, validate_plan

EXAMPLES = HERE.parent / "examples"
CHECKER = HERE / "check_video_plan.py"


class PlanValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = json.loads((EXAMPLES / "fictional-video-plan.json").read_text(encoding="utf-8"))

    def test_valid_fixture_passes_with_only_review_warnings(self) -> None:
        errors, warnings = validate_plan(self.valid)
        self.assertEqual(errors, [])
        self.assertTrue(any("pending" in warning for warning in warnings))

    def test_invalid_fixture_blocks_evidence_consent_and_actions(self) -> None:
        invalid = json.loads((EXAMPLES / "invalid-video-plan.json").read_text(encoding="utf-8"))
        errors, _ = validate_plan(invalid)
        joined = "\n".join(errors)
        self.assertIn("undeclared source id", joined)
        self.assertIn("confirmed consent is required", joined)
        self.assertIn("production.paid_calls", joined)
        self.assertIn("production.publish", joined)

    def test_unknown_claim_source_is_rejected(self) -> None:
        plan = deepcopy(self.valid)
        plan["claims"][0]["source_ids"] = ["NOT-THERE"]
        errors, _ = validate_plan(plan)
        self.assertTrue(any("undeclared source id" in error for error in errors))
        self.assertNotIn("NOT-THERE", "\n".join(errors))

    def test_credential_like_key_is_rejected_without_echoing_value(self) -> None:
        plan = deepcopy(self.valid)
        plan["production"]["api_key_private-fragment"] = "do-not-print-this-value"
        errors, _ = validate_plan(plan)
        joined = "\n".join(errors)
        self.assertIn("credential-like fields", joined)
        self.assertNotIn("private-fragment", joined)
        self.assertNotIn("do-not-print-this-value", joined)

    def test_external_action_true_is_rejected(self) -> None:
        for field in ("paid_calls", "publish", "send"):
            with self.subTest(field=field):
                plan = deepcopy(self.valid)
                plan["production"][field] = True
                errors, _ = validate_plan(plan)
                self.assertTrue(any(f"production.{field}" in error for error in errors))

    def test_review_ready_requires_completed_review_gates(self) -> None:
        plan = deepcopy(self.valid)
        plan["status"] = "review-ready"
        errors, warnings = validate_plan(plan)
        self.assertTrue(any("cannot remain pending" in error for error in errors))
        self.assertEqual(warnings, [])

    def test_failed_and_missing_review_gates_are_rejected(self) -> None:
        failed = deepcopy(self.valid)
        failed["review"]["claims"] = "failed"
        errors, _ = validate_plan(failed)
        self.assertTrue(any("failed review" in error for error in errors))

        missing = deepcopy(self.valid)
        del missing["review"]["message"]
        errors, _ = validate_plan(missing)
        self.assertTrue(any("required review gate is missing" in error for error in errors))

    def test_duplicate_source_and_person_ids_are_rejected(self) -> None:
        source_plan = deepcopy(self.valid)
        source_plan["sources"].append(deepcopy(source_plan["sources"][0]))
        errors, _ = validate_plan(source_plan)
        self.assertTrue(any("duplicate source id" in error for error in errors))

        person_plan = deepcopy(self.valid)
        person_plan["people"] = [
            {"id": "P1", "role": "speaker", "consent": "confirmed"},
            {"id": "P1", "role": "speaker", "consent": "confirmed"},
        ]
        errors, _ = validate_plan(person_plan)
        self.assertTrue(any("duplicate person id" in error for error in errors))

    def test_wrong_schema_and_non_object_root_are_rejected(self) -> None:
        wrong_schema = deepcopy(self.valid)
        wrong_schema["schema_version"] = "2.0"
        errors, _ = validate_plan(wrong_schema)
        self.assertTrue(any("schema_version" in error for error in errors))
        self.assertEqual(validate_plan([])[0], ["root: expected a JSON object"])

    def test_type_confused_status_fields_are_rejected_without_crashing(self) -> None:
        mutations = [
            ("status", lambda plan: plan.__setitem__("status", [])),
            ("format", lambda plan: plan.__setitem__("format", {})),
            ("source permission", lambda plan: plan["sources"][0].__setitem__("permission", [])),
            ("claim status", lambda plan: plan["claims"][0].__setitem__("status", {})),
            ("review status", lambda plan: plan["review"].__setitem__("message", [])),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                plan = deepcopy(self.valid)
                mutate(plan)
                errors, _ = validate_plan(plan)
                self.assertTrue(errors)

    def test_source_id_whitespace_is_normalized_consistently(self) -> None:
        plan = deepcopy(self.valid)
        plan["sources"][0]["id"] = " S1 "
        plan["claims"][0]["source_ids"] = [" S1 "]
        errors, _ = validate_plan(plan)
        self.assertEqual(errors, [])

    def test_person_requires_confirmed_consent(self) -> None:
        plan = deepcopy(self.valid)
        plan["people"] = [{"id": "P1", "role": "speaker", "consent": "not-applicable"}]
        errors, _ = validate_plan(plan)
        self.assertTrue(any("confirmed consent is required" in error for error in errors))

    def test_unsupported_permission_and_sourceless_verified_claim_are_rejected(self) -> None:
        permission_plan = deepcopy(self.valid)
        permission_plan["sources"][0]["permission"] = "pending"
        errors, _ = validate_plan(permission_plan)
        self.assertTrue(any("permission" in error for error in errors))

        claim_plan = deepcopy(self.valid)
        claim_plan["claims"][0]["source_ids"] = []
        errors, _ = validate_plan(claim_plan)
        self.assertTrue(any("need a source" in error for error in errors))

    def test_review_ready_with_completed_gates_passes_without_warnings(self) -> None:
        plan = deepcopy(self.valid)
        plan["status"] = "review-ready"
        plan["review"] = {gate: "passed" for gate in plan["review"]}
        errors, warnings = validate_plan(plan)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_review_ready_requires_passed_full_playback(self) -> None:
        plan = deepcopy(self.valid)
        plan["status"] = "review-ready"
        plan["review"] = {gate: "passed" for gate in plan["review"]}
        plan["review"]["full_playback"] = "not-applicable"
        errors, _ = validate_plan(plan)
        self.assertTrue(any("full_playback" in error and "must pass" in error for error in errors))

    def test_symlink_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "plan.json"
            link = Path(temp_dir) / "link.json"
            target.write_text(json.dumps(self.valid), encoding="utf-8")
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                load_plan(link)

    def test_directory_and_oversized_input_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "regular file"):
                load_plan(directory)

            oversized = directory / "oversized.json"
            oversized.write_bytes(b" " * (MAX_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "exceeds"):
                load_plan(oversized)

    def test_bounded_read_rejects_file_larger_than_reported_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            oversized = Path(temp_dir) / "grew-after-size-check.json"
            oversized.write_bytes(b" " * (MAX_BYTES + 1))
            actual = os.stat(oversized)
            fields = list(actual)
            fields[6] = 0
            reported_small = os.stat_result(fields)
            with patch("check_video_plan.os.fstat", return_value=reported_small):
                with self.assertRaisesRegex(ValueError, "exceeds"):
                    load_plan(oversized)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are not supported")
    def test_named_pipe_is_rejected_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fifo = Path(temp_dir) / "plan.fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, "regular file"):
                load_plan(fifo)

    def test_cli_exit_codes_and_redacted_output(self) -> None:
        valid_run = subprocess.run(
            [sys.executable, str(CHECKER), str(EXAMPLES / "fictional-video-plan.json")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(valid_run.returncode, 0, valid_run.stdout + valid_run.stderr)
        self.assertTrue(json.loads(valid_run.stdout)["valid"])

        invalid_run = subprocess.run(
            [sys.executable, str(CHECKER), str(EXAMPLES / "invalid-video-plan.json")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(invalid_run.returncode, 1, invalid_run.stdout + invalid_run.stderr)
        self.assertFalse(json.loads(invalid_run.stdout)["valid"])

        with tempfile.TemporaryDirectory() as temp_dir:
            malformed = Path(temp_dir) / "malformed.json"
            malformed.write_text("{not-json", encoding="utf-8")
            malformed_run = subprocess.run(
                [sys.executable, str(CHECKER), str(malformed)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(malformed_run.returncode, 2)
            result = json.loads(malformed_run.stdout)
            self.assertFalse(result["valid"])
            self.assertTrue(result["errors"][0].startswith("input:"))

            type_confused = Path(temp_dir) / "type-confused.json"
            type_confused_plan = deepcopy(self.valid)
            type_confused_plan["status"] = []
            type_confused.write_text(json.dumps(type_confused_plan), encoding="utf-8")
            type_confused_run = subprocess.run(
                [sys.executable, str(CHECKER), str(type_confused)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(type_confused_run.returncode, 1)
            type_confused_result = json.loads(type_confused_run.stdout)
            self.assertFalse(type_confused_result["valid"])
            self.assertTrue(any("status" in error for error in type_confused_result["errors"]))

            duplicate_keys = Path(temp_dir) / "duplicate-keys.json"
            duplicate_payload = json.dumps(self.valid).replace(
                '"publish": false',
                '"publish": true, "publish": false',
                1,
            )
            duplicate_keys.write_text(duplicate_payload, encoding="utf-8")
            duplicate_run = subprocess.run(
                [sys.executable, str(CHECKER), str(duplicate_keys)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(duplicate_run.returncode, 2)
            duplicate_result = json.loads(duplicate_run.stdout)
            self.assertFalse(duplicate_result["valid"])
            self.assertIn("duplicate JSON key", duplicate_result["errors"][0])

            missing = Path(temp_dir) / "private-fragment-missing.json"
            missing_run = subprocess.run(
                [sys.executable, str(CHECKER), str(missing)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(missing_run.returncode, 2)
            self.assertNotIn("private-fragment", missing_run.stdout)


if __name__ == "__main__":
    unittest.main()
