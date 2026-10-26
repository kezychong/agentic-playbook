#!/usr/bin/env python3
"""Tests for the patterns feed generator.

They run against a made-up workspace built in a temporary folder, never
against anyone's real workspace.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ANALYTICS_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANALYTICS_DIR))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import build_patterns as bp  # noqa: E402
import make_synthetic_workspace  # noqa: E402
from feed_contract import FeedValidationError, validate_feed  # noqa: E402

TODAY = dt.date(2026, 8, 24)


class FeedBaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.content_os = make_synthetic_workspace.build(self.root, today=TODAY)
        self.history = self.content_os / "analytics" / "pattern-history.json"

    def tearDown(self):
        self.temp.cleanup()

    def build(self, *, as_of=TODAY, confirmed=False, profile="member"):
        feed, snapshot = bp.build_feed(
            self.content_os,
            as_of=as_of,
            weekly_confirmed=confirmed,
            profile=bp.PROFILES[profile],
            history_path=self.history,
        )
        return feed, snapshot

    def weekly_runs(self, weeks: int, profile: str = "member"):
        feed = snapshot = None
        for index in range(weeks, -1, -1):
            as_of = TODAY - dt.timedelta(days=7 * index)
            feed, snapshot = self.build(as_of=as_of, confirmed=True, profile=profile)
            bp.append_history(self.history, snapshot)
        return feed


class ContractTests(FeedBaseTest):
    def test_generated_feed_passes_its_own_contract(self):
        feed, _ = self.build()
        validate_feed(feed)

    def test_empty_workspace_still_produces_a_valid_honest_feed(self):
        with tempfile.TemporaryDirectory() as name:
            empty = pathlib.Path(name) / "content-os"
            empty.mkdir(parents=True)
            feed, _ = bp.build_feed(
                empty,
                as_of=TODAY,
                weekly_confirmed=False,
                profile=bp.PROFILES["member"],
                history_path=empty / "analytics" / "pattern-history.json",
            )
            validate_feed(feed)
            self.assertEqual(feed["patterns"], [])
            self.assertEqual(feed["test_next"], [])
            self.assertEqual(feed["collecting_evidence"], [])
            self.assertIsNone(feed["freshness"]["w2_last_success"])
            self.assertTrue(
                any("library is empty" in note for note in feed["quality"]["scan_exceptions"])
            )

    def test_contract_catches_a_filled_owner_angle(self):
        feed = self.weekly_runs(6)
        self.assertTrue(feed["test_next"], "expected at least one test-next card")
        feed["test_next"][0]["owner_angle"] = "my take on this"
        with self.assertRaises(FeedValidationError):
            validate_feed(feed)

    def test_contract_catches_a_broken_selection_funnel(self):
        feed, _ = self.build()
        feed["corpus"]["selection_funnel"]["analyzed"] = 999
        with self.assertRaises(FeedValidationError):
            validate_feed(feed)


class HonestyTests(FeedBaseTest):
    def test_entries_without_numbers_never_enter_the_maths(self):
        feed, _ = self.build()
        reasons = feed["quality"]["expansion"]["unusable_reasons"]
        self.assertIn("no multiple recorded on the entry", reasons)
        self.assertGreaterEqual(feed["quality"]["quarantined"], 1)
        supporting = {
            code for record in feed["patterns"] for code in record["supporting_shortcodes"]
        }
        no_numbers = [
            path.name
            for path in (self.content_os / "library").glob("*no-numbers*.md")
        ]
        self.assertTrue(no_numbers)
        from workspace_read import stable_id

        excluded = stable_id(f"library/{no_numbers[0]}")
        self.assertNotIn(excluded, supporting)

    def test_no_trend_calls_before_there_is_history_to_compare(self):
        feed, _ = self.build()
        self.assertEqual(feed["views"]["rising"], [])
        self.assertEqual(feed["views"]["cooling"], [])
        self.assertTrue(
            any("withheld" in note for note in feed["quality"]["scan_exceptions"])
        )
        for record in feed["patterns"]:
            self.assertEqual(record["gate_receipt"]["scan_state"], "unmeasured")

    def test_trend_calls_unlock_once_weekly_history_exists(self):
        feed = self.weekly_runs(6)
        states = {record["gate_receipt"]["scan_state"] for record in feed["patterns"]}
        self.assertEqual(states, {"measured"})
        self.assertTrue(feed["views"]["rising"], "expected a rising pattern after six weeks")
        self.assertFalse(
            any("withheld" in note for note in feed["quality"]["scan_exceptions"])
        )

    def test_a_visual_pattern_only_uses_frames_someone_watched(self):
        feed, _ = self.build()
        visual_records = [record for record in feed["patterns"] if record["pattern"]["is_visual"]]
        self.assertTrue(visual_records)
        for record in visual_records:
            self.assertEqual(record["quality"]["visual_evidence_mode"], "observed_frames_ocr")
        caption_only = [
            path.name for path in (self.content_os / "library").glob("*caption-only-read*.md")
        ]
        from workspace_read import stable_id

        inferred = stable_id(f"library/{caption_only[0]}")
        for record in visual_records:
            self.assertNotIn(inferred, record["supporting_shortcodes"])

    def test_one_own_win_is_not_called_proven_at_member_scale(self):
        feed, _ = self.build()
        for record in feed["patterns"]:
            if record["own_proven"]:
                self.assertGreaterEqual(len(record["own_evidence_shortcodes"]), 2)
        singles = [
            record
            for record in feed["patterns"]
            if len(record["own_evidence_shortcodes"]) == 1
        ]
        self.assertTrue(singles, "expected some patterns backed by a single own post")
        for record in singles:
            self.assertFalse(record["own_proven"])

    def test_the_two_profiles_behave_as_documented_on_the_same_data(self):
        member_feed, _ = self.build(profile="member")
        full_feed, _ = self.build(profile="full")
        # The original counting floors are built for a much larger corpus, so
        # on one owner's data they call almost nothing a live trend.
        self.assertGreater(
            len(member_feed["views"]["emerging"]), len(full_feed["views"]["emerging"])
        )
        # And the original treats a single own win as proof, which floods a
        # small corpus. That is exactly why the member profile asks for two.
        self.assertGreater(
            sum(record["own_proven"] for record in full_feed["patterns"]),
            sum(record["own_proven"] for record in member_feed["patterns"]),
        )
        self.assertIn("member", member_feed["scope_note"])
        self.assertIn("full", full_feed["scope_note"])

    def test_a_post_measured_too_early_is_held_back_and_counted(self):
        feed, _ = self.build()
        self.assertGreaterEqual(feed["quality"]["pending_maturation"], 1)
        self.assertIn(
            "measured before the post was two days old",
            feed["quality"]["expansion"]["unusable_reasons"],
        )


class ShapeTests(FeedBaseTest):
    def test_the_fields_the_board_reads_are_present(self):
        feed = self.weekly_runs(6)
        self.assertEqual(feed["schema_version"], "patterns-feed-v1")
        self.assertIsNotNone(feed["freshness"]["w2_last_success"])
        record = feed["patterns"][0]
        current = record["windows"]["days_14"]
        for key in (
            "distinct_creator_count",
            "eligible_reel_count",
            "distinct_family_count",
            "creator_coverage",
        ):
            self.assertIn(key, current)
        for key in ("clean_support_share", "visual_evidence_mode", "pending_maturation_excluded"):
            self.assertIn(key, record["quality"])
        card = feed["test_next"][0]
        self.assertEqual(card["snapshot_date"], feed["last_confirmed_snapshot"])
        self.assertEqual(card["owner_angle"], "")
        self.assertGreaterEqual(len(card["evidence_refs"]), 2)

    def test_test_next_only_appears_on_a_confirmed_build(self):
        feed, _ = self.build(confirmed=False)
        self.assertEqual(feed["test_next"], [])
        self.assertTrue(feed["provisional"])

    def test_record_ids_are_stable_across_builds(self):
        first, _ = self.build()
        second, _ = self.build()
        self.assertEqual(
            [record["record_id"] for record in first["patterns"]],
            [record["record_id"] for record in second["patterns"]],
        )


class HistoryTests(FeedBaseTest):
    def test_history_keeps_at_most_thirteen_snapshots(self):
        for index in range(20):
            snapshot = {
                "snapshot_date": (TODAY - dt.timedelta(days=7 * index)).isoformat(),
                "accounts_total": 5,
                "accounts_measured": 5,
                "scan_coverage": 1.0,
                "records": {},
            }
            bp.append_history(self.history, snapshot)
        stored = bp.load_history(self.history)
        self.assertEqual(len(stored), bp.HISTORY_LIMIT)
        self.assertEqual(stored, sorted(stored, key=lambda item: item["snapshot_date"]))

    def test_rebuilding_the_same_day_replaces_that_snapshot(self):
        _, snapshot = self.build(confirmed=True)
        bp.append_history(self.history, snapshot)
        bp.append_history(self.history, snapshot)
        stored = bp.load_history(self.history)
        self.assertEqual(len(stored), 1)

    def test_a_damaged_history_file_does_not_stop_a_build(self):
        self.history.parent.mkdir(parents=True, exist_ok=True)
        self.history.write_text("this is not json", encoding="utf-8")
        feed, _ = self.build()
        validate_feed(feed)


class WriteAndLockTests(FeedBaseTest):
    def test_atomic_write_leaves_no_partial_file(self):
        target = self.content_os / "analytics" / "patterns.json"
        bp.write_json_atomic(target, {"hello": "world"})
        self.assertTrue(target.is_file())
        self.assertFalse(target.with_suffix(".json.partial").exists())
        self.assertEqual(json.loads(target.read_text())["hello"], "world")

    def test_a_second_build_on_the_same_workspace_is_refused(self):
        lock = self.content_os / "analytics" / "patterns.json.lock"
        handle = bp.acquire_lock(lock)
        try:
            with self.assertRaises(bp.LockBusy):
                bp.acquire_lock(lock)
        finally:
            bp.release_lock(handle, lock)
        self.assertFalse(lock.exists())

    def test_a_stale_lock_is_taken_over(self):
        import os
        import time

        lock = self.content_os / "analytics" / "patterns.json.lock"
        handle = bp.acquire_lock(lock)
        bp.release_lock(handle, lock)
        lock.write_text("", encoding="utf-8")
        old = time.time() - bp.LOCK_STALE_SECONDS - 60
        os.utime(lock, (old, old))
        handle = bp.acquire_lock(lock)
        bp.release_lock(handle, lock)


class CommandTests(FeedBaseTest):
    def run_build(self, *args):
        return subprocess.run(
            [sys.executable, str(ANALYTICS_DIR / "build_patterns.py"), *args],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_end_to_end_write(self):
        proc = self.run_build("--workspace", str(self.root), "--as-of", TODAY.isoformat())
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        written = json.loads((self.content_os / "analytics" / "patterns.json").read_text())
        validate_feed(written)
        summary = json.loads(proc.stdout)
        self.assertEqual(summary["as_of_date"], TODAY.isoformat())
        self.assertGreater(summary["entries_read"], 10)

    def test_dry_run_writes_nothing(self):
        proc = self.run_build(
            "--workspace", str(self.root), "--as-of", TODAY.isoformat(), "--dry-run"
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertFalse((self.content_os / "analytics" / "patterns.json").exists())

    def test_missing_workspace_exits_2(self):
        with tempfile.TemporaryDirectory() as name:
            proc = self.run_build("--workspace", name)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("no content-os folder", proc.stderr)


if __name__ == "__main__":
    unittest.main()
