#!/usr/bin/env python3
"""Tests for the weekly review arithmetic."""

from __future__ import annotations

import datetime as dt
import pathlib
import sys
import tempfile
import unittest

ANALYTICS_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANALYTICS_DIR))

import review_numbers as rn  # noqa: E402

AS_OF = dt.date(2026, 8, 24)


def ledger(*sections: str) -> str:
    return "# Posted\n\n" + "\n\n".join(sections) + "\n"


def piece(date: str, title: str, views: int, fmt: str = "talking to camera", extra: str = "") -> str:
    return (
        f"## {date} - {title}\n\n"
        f"- platform: instagram\n"
        f"- format: {fmt}\n"
        f"- link: https://example.test/p/{title.replace(' ', '-').lower()}\n"
        f"- job: reach\n"
        f"- stats: views {views}, likes 40, comments 5 (as of {date})\n"
        f"{extra}"
    )


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.content_os = pathlib.Path(self.temp.name) / "content-os"
        self.content_os.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, text: str):
        (self.content_os / "posted.md").write_text(text, encoding="utf-8")

    def test_bands_follow_the_doctrine(self):
        self.assertEqual(rn.band_for(0.5), "weak")
        self.assertEqual(rn.band_for(0.7), "normal")
        self.assertEqual(rn.band_for(1.4), "normal")
        self.assertEqual(rn.band_for(1.5), "strong")
        self.assertEqual(rn.band_for(2.9), "strong")
        self.assertEqual(rn.band_for(3.0), "outlier")
        self.assertEqual(rn.band_for(None), "unknown")

    def test_multiple_is_measured_against_earlier_comparable_pieces_only(self):
        self.write(
            ledger(
                piece("2026-08-01", "one", 1000),
                piece("2026-08-05", "two", 1000),
                piece("2026-08-09", "three", 3000),
                piece("2026-08-20", "four", 9000),
            )
        )
        result = rn.review(self.content_os, None, AS_OF)
        rows = {row["title"]: row for row in result["pieces"]}
        self.assertIsNone(rows["one"]["multiple"])
        self.assertEqual(rows["four"]["baseline_median"], 1000)
        self.assertEqual(rows["four"]["multiple"], 9.0)
        self.assertEqual(rows["four"]["band"], "outlier")
        self.assertTrue(rows["four"]["winner"])
        self.assertEqual(rows["four"]["winner_reason"], "three times the baseline")

    def test_a_different_format_is_not_a_comparable_piece(self):
        self.write(
            ledger(
                piece("2026-08-01", "talking one", 1000),
                piece("2026-08-05", "screen one", 9000, fmt="screen recording"),
            )
        )
        rows = {row["title"]: row for row in rn.review(self.content_os, None, AS_OF)["pieces"]}
        self.assertIsNone(rows["screen one"]["baseline_median"])
        self.assertIn("no comparable piece", rows["screen one"]["note"])

    def test_a_thin_baseline_says_so(self):
        self.write(ledger(piece("2026-08-01", "one", 1000), piece("2026-08-05", "two", 1200)))
        rows = {row["title"]: row for row in rn.review(self.content_os, None, AS_OF)["pieces"]}
        self.assertIn("thin", rows["two"]["comparable_note"])

    def test_business_signal_wins_without_the_reach(self):
        self.write(
            ledger(
                piece("2026-08-01", "one", 4000),
                piece("2026-08-05", "two", 4000),
                piece(
                    "2026-08-20",
                    "quiet but paid",
                    400,
                    extra="- enquiries: 2 booked calls, both named this piece\n",
                ),
            )
        )
        rows = {row["title"]: row for row in rn.review(self.content_os, None, AS_OF)["pieces"]}
        row = rows["quiet but paid"]
        self.assertEqual(row["band"], "weak")
        self.assertTrue(row["winner"])
        self.assertEqual(row["winner_reason"], "business signal without the reach")

    def test_missing_numbers_are_listed_never_filled_in(self):
        self.write(ledger("## 2026-08-20 - no numbers yet\n\n- platform: instagram\n- format: talking to camera\n"))
        result = rn.review(self.content_os, None, AS_OF)
        row = result["pieces"][0]
        self.assertIsNone(row["views"])
        self.assertIsNone(row["multiple"])
        self.assertIn("no view count recorded", row["note"])
        self.assertIn("views", row["missing"]["public"])
        self.assertIn("saves", row["missing"]["only_you_can_see"])
        self.assertEqual(len(result["needs_numbers"]), 1)

    def test_the_review_window_filters_what_is_judged(self):
        self.write(
            ledger(piece("2026-07-01", "old", 1000), piece("2026-08-20", "recent", 1000))
        )
        result = rn.review(self.content_os, dt.date(2026, 8, 17), AS_OF)
        self.assertEqual(result["pieces_in_ledger"], 2)
        self.assertEqual(result["pieces_in_window"], 1)

    def test_an_empty_ledger_is_a_valid_answer(self):
        result = rn.review(self.content_os, None, AS_OF)
        self.assertEqual(result["pieces_in_ledger"], 0)
        self.assertEqual(result["winners"], [])


if __name__ == "__main__":
    unittest.main()
