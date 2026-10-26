#!/usr/bin/env python3
"""
Unit tests for outlier_math.py (18 cases).

Run them from the analytics folder with the standard-library test runner:

    python3 -m unittest discover -s tests -p "test_*.py"

No third-party packages, no environment to build, nothing to install.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ANALYTICS_DIR = pathlib.Path(__file__).resolve().parent.parent
FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(ANALYTICS_DIR))

import outlier_math  # noqa: E402


class ComputeMedianTests(unittest.TestCase):
    def test_median_of_odd_length_list(self):
        self.assertEqual(outlier_math.compute_median([12000, 15000, 9000, 20000, 11000]), 12000)

    def test_empty_list_raises(self):
        with self.assertRaises(outlier_math.InputError):
            outlier_math.compute_median([])

    def test_negative_value_raises(self):
        with self.assertRaises(outlier_math.InputError):
            outlier_math.compute_median([1000, -5, 2000])


class EvaluateCandidateTests(unittest.TestCase):
    def test_outlier_flagged_at_exactly_3x(self):
        result = outlier_math.evaluate_candidate("edge", 30000, creator_median=10000)
        self.assertEqual(result["outlier_multiple"], 3.0)
        self.assertTrue(result["is_outlier"])

    def test_just_under_3x_not_flagged(self):
        result = outlier_math.evaluate_candidate("under", 29400, creator_median=10000)
        self.assertLess(result["outlier_multiple"], 3.0)
        self.assertFalse(result["is_outlier"])

    def test_zero_median_reports_no_baseline_instead_of_crashing(self):
        result = outlier_math.evaluate_candidate("nobaseline", 5000, creator_median=0)
        self.assertIsNone(result["outlier_multiple"])
        self.assertFalse(result["is_outlier"])
        self.assertIn("no valid baseline", result["note"])

    def test_recency_flag_fresh(self):
        result = outlier_math.evaluate_candidate("fresh", 40000, creator_median=10000, age_days=5)
        self.assertTrue(result["recency_flag"].startswith("FRESH"))

    def test_recency_flag_stale(self):
        result = outlier_math.evaluate_candidate(
            "stale", 40000, creator_median=10000, age_days=120, recency_window_days=90
        )
        self.assertTrue(result["recency_flag"].startswith("STALE"))

    def test_recency_flag_unknown_when_age_missing(self):
        result = outlier_math.evaluate_candidate("noage", 40000, creator_median=10000)
        self.assertTrue(result["recency_flag"].startswith("UNKNOWN"))

    def test_negative_views_raises(self):
        with self.assertRaises(outlier_math.InputError):
            outlier_math.evaluate_candidate("bad", -100, creator_median=10000)


class ParseCandidateArgTests(unittest.TestCase):
    def test_label_views(self):
        c = outlier_math.parse_candidate_arg("post_a:64000")
        self.assertEqual(c, {"label": "post_a", "views": 64000.0, "age_days": None})

    def test_label_views_age(self):
        c = outlier_math.parse_candidate_arg("post_a:64000:5")
        self.assertEqual(c, {"label": "post_a", "views": 64000.0, "age_days": 5.0})

    def test_malformed_raises(self):
        with self.assertRaises(outlier_math.InputError):
            outlier_math.parse_candidate_arg("post_a")

    def test_non_numeric_views_raises(self):
        with self.assertRaises(outlier_math.InputError):
            outlier_math.parse_candidate_arg("post_a:notanumber")


class FixtureIntegrationTests(unittest.TestCase):
    """Runs the fixture JSON exactly the way the weekly job runs it: via stdin."""

    def setUp(self):
        fixture_path = FIXTURES_DIR / "creator_sample.json"
        self.fixture_raw = fixture_path.read_text()

    def test_fixture_via_stdin_module_call(self):
        import io

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(self.fixture_raw)
        try:
            output = outlier_math.run_from_stdin(recency_window_days=90)
        finally:
            sys.stdin = old_stdin

        self.assertEqual(output["creator"], "example_account")
        self.assertEqual(output["creator_median"], 12000)

        by_label = {r["label"]: r for r in output["results"]}

        # post_a_outlier: 64000 / 12000 = 5.33x, fresh (5 days) -> outlier + FRESH
        self.assertTrue(by_label["post_a_outlier"]["is_outlier"])
        self.assertAlmostEqual(by_label["post_a_outlier"]["outlier_multiple"], 5.33, places=2)
        self.assertTrue(by_label["post_a_outlier"]["recency_flag"].startswith("FRESH"))

        # post_b_borderline: 33000 / 12000 = 2.75x -> NOT an outlier (below 3x)
        self.assertFalse(by_label["post_b_borderline"]["is_outlier"])
        self.assertAlmostEqual(by_label["post_b_borderline"]["outlier_multiple"], 2.75, places=2)

        # post_c_normal: 13500 / 12000 = 1.125x -> not an outlier
        self.assertFalse(by_label["post_c_normal"]["is_outlier"])

        # post_d_stale_outlier: 80000 / 12000 = 6.67x -> outlier BUT stale (120d > 90d window)
        self.assertTrue(by_label["post_d_stale_outlier"]["is_outlier"])
        self.assertTrue(by_label["post_d_stale_outlier"]["recency_flag"].startswith("STALE"))

    def test_fixture_via_subprocess(self):
        """End-to-end smoke test: invoke the file itself, reading stdin."""
        proc = subprocess.run(
            [sys.executable, str(ANALYTICS_DIR / "outlier_math.py"), "--stdin"],
            input=self.fixture_raw,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, msg=f"stderr: {proc.stderr}")
        output = json.loads(proc.stdout)
        self.assertEqual(output["creator_median"], 12000)
        by_label = {r["label"]: r for r in output["results"]}
        self.assertTrue(by_label["post_a_outlier"]["is_outlier"])

    def test_args_mode_matches_stdin_mode(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(ANALYTICS_DIR / "outlier_math.py"),
                "--recent-views", "12000", "15000", "9000", "20000", "11000",
                "--candidate", "post_a_outlier:64000:5",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, msg=f"stderr: {proc.stderr}")
        output = json.loads(proc.stdout)
        self.assertEqual(output["results"][0]["outlier_multiple"], 5.33)
        self.assertTrue(output["results"][0]["is_outlier"])

    def test_bad_input_exits_2(self):
        proc = subprocess.run(
            [sys.executable, str(ANALYTICS_DIR / "outlier_math.py"), "--stdin"],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
