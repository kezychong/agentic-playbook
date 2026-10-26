#!/usr/bin/env python3
"""Tests for the workspace readers: they must read what is there, and never
invent what is not."""

from __future__ import annotations

import datetime as dt
import pathlib
import sys
import tempfile
import unittest

ANALYTICS_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANALYTICS_DIR))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import make_synthetic_workspace  # noqa: E402
import workspace_read as wr  # noqa: E402


ENTRY_TEXT = """# Library entry: challenges the viewer's own diagnosis

Filed: 2026-08-14
Posted: 2026-08-12
Account normal: 4,200 views
This post: 15,000 views
Multiple: 3.6x
Words captured: transcript
Mechanism family: challenge_belief
First frame: a face, watched

## The opening line, as data
Quoted for analysis only.

## First frame
A face, watched, filling the frame.

## The proof device
A client conversation on screen.

## Format
Talking to camera.

## The ask at the end
Follow for the next one.

## The mechanism
Challenges the audience's own diagnosis before offering an answer.

## Source and trust level
- Account and platform: @ledgerlane, Instagram
- Trust level: someone in my niche
- Link: https://example.test/p/abc123
"""


class LibraryEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.content_os = pathlib.Path(self.temp.name) / "content-os"
        (self.content_os / "library").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name: str, text: str):
        (self.content_os / "library" / name).write_text(text, encoding="utf-8")

    def test_reads_every_field_written_in_the_header(self):
        self.write("2026-08-14 - ledgerlane - challenge.md", ENTRY_TEXT)
        entry = wr.read_library_entries(self.content_os)[0]
        self.assertEqual(entry.filed_on, dt.date(2026, 8, 14))
        self.assertEqual(entry.posted_on, dt.date(2026, 8, 12))
        self.assertEqual(entry.account, "ledgerlane")
        self.assertFalse(entry.is_own)
        self.assertEqual(entry.account_normal, 4200)
        self.assertEqual(entry.views, 15000)
        self.assertEqual(entry.multiple, 3.6)
        self.assertEqual(entry.link, "https://example.test/p/abc123")
        self.assertTrue(entry.first_frame_observed)
        self.assertEqual(entry.dimensions["mechanism_class"], "challenge_belief")
        self.assertEqual(entry.dimensions["format"], "talking_to_camera")
        self.assertEqual(entry.dimensions["cta"], "follow")
        self.assertEqual(entry.dimensions["visual_open"], "face")
        self.assertEqual(entry.flags, ())

    def test_someone_in_my_niche_is_not_read_as_my_own_account(self):
        self.write("2026-08-14 - ledgerlane - challenge.md", ENTRY_TEXT)
        entry = wr.read_library_entries(self.content_os)[0]
        self.assertFalse(entry.is_own)

    def test_own_account_entry_is_marked_own(self):
        own = ENTRY_TEXT.replace("@ledgerlane, Instagram", "mine, Instagram").replace(
            "someone in my niche", "my own results"
        )
        self.write("2026-08-14 - mine - own-win.md", own)
        entry = wr.read_library_entries(self.content_os)[0]
        self.assertTrue(entry.is_own)

    def test_missing_numbers_are_flagged_not_guessed(self):
        stripped = "\n".join(
            line
            for line in ENTRY_TEXT.splitlines()
            if not line.startswith(("Multiple:", "This post:", "Account normal:"))
        )
        self.write("2026-08-14 - ledgerlane - nonumbers.md", stripped)
        entry = wr.read_library_entries(self.content_os)[0]
        self.assertIsNone(entry.multiple)
        self.assertIn("no_multiple_recorded", entry.flags)

    def test_unmarked_first_frame_never_counts_as_watched(self):
        inferred = ENTRY_TEXT.replace("First frame: a face, watched", "First frame: probably a face")
        self.write("2026-08-14 - ledgerlane - inferred.md", inferred)
        entry = wr.read_library_entries(self.content_os)[0]
        self.assertFalse(entry.first_frame_observed)
        self.assertEqual(entry.dimensions["visual_open"], wr.UNKNOWN)
        self.assertIn("visual_not_marked_watched", entry.flags)

    def test_missing_library_folder_returns_nothing(self):
        empty = pathlib.Path(self.temp.name) / "nowhere"
        self.assertEqual(wr.read_library_entries(empty), [])

    def test_franchise_cards_in_a_subfolder_are_not_read_as_entries(self):
        (self.content_os / "library" / "franchises").mkdir()
        (self.content_os / "library" / "franchises" / "a-franchise.md").write_text(
            "# Franchise: the numbers-first franchise\n", encoding="utf-8"
        )
        self.write("2026-08-14 - ledgerlane - challenge.md", ENTRY_TEXT)
        entries = wr.read_library_entries(self.content_os)
        self.assertEqual(len(entries), 1)


class ResearchStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.content_os = pathlib.Path(self.temp.name) / "content-os"
        self.content_os.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_reads_a_table(self):
        (self.content_os / "research-state.md").write_text(
            "# Research state\n\n"
            "| Handle | Median views | Sample | Date measured | Last run |\n"
            "|---|---|---|---|---|\n"
            "| @ledgerlane | 4,200 | 30 | 2026-07-10 | 2026-08-22 |\n",
            encoding="utf-8",
        )
        state = wr.read_research_state(self.content_os)
        self.assertEqual(state["ledgerlane"].median_views, 4200)
        self.assertEqual(state["ledgerlane"].sample_size, 30)
        self.assertEqual(state["ledgerlane"].measured_on, dt.date(2026, 7, 10))
        self.assertEqual(state["ledgerlane"].last_run, dt.date(2026, 8, 22))

    def test_reads_per_account_blocks(self):
        (self.content_os / "research-state.md").write_text(
            "# Research state\n\n## @taxtruths\n\n"
            "- median_views: 3.1k\n- sample size: 30\n"
            "- date measured: 2026-07-11\n- last run: 2026-08-21\n",
            encoding="utf-8",
        )
        state = wr.read_research_state(self.content_os)
        self.assertEqual(state["taxtruths"].median_views, 3100)
        self.assertEqual(state["taxtruths"].last_run, dt.date(2026, 8, 21))

    def test_reads_one_line_per_account(self):
        (self.content_os / "research-state.md").write_text(
            "# Research state\n\n"
            "- @cfoclare \u2014 median 61,000 views, sample 30, measured 2026-07-12, last run 2026-08-20\n"
            "- @smallbizsam: median 900 views, sample 24, measured 2026-07-13, last run 2026-08-20\n",
            encoding="utf-8",
        )
        state = wr.read_research_state(self.content_os)
        self.assertEqual(state["cfoclare"].median_views, 61000)
        self.assertEqual(state["cfoclare"].measured_on, dt.date(2026, 7, 12))
        self.assertEqual(state["smallbizsam"].median_views, 900)

    def test_missing_file_is_not_an_error(self):
        self.assertEqual(wr.read_research_state(self.content_os), {})


class WatchlistTests(unittest.TestCase):
    def test_lanes_are_read_and_the_filed_table_is_ignored(self):
        with tempfile.TemporaryDirectory() as name:
            content_os = pathlib.Path(name) / "content-os"
            content_os.mkdir(parents=True)
            make_synthetic_workspace.build(pathlib.Path(name))
            families = wr.read_watchlist_families(content_os)
            self.assertEqual(families["ledgerlane"], "competitor")
            self.assertEqual(families["cfoclare"], "authority")
            self.assertEqual(families["smallbizsam"], "underdog")
            self.assertEqual(families["toolmaker_jo"], "outside_industry")
            self.assertNotIn("date", families)


class PostedLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.content_os = pathlib.Path(self.temp.name) / "content-os"
        self.content_os.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_sections_fields_and_repeated_stats(self):
        (self.content_os / "posted.md").write_text(
            "# Posted\n\n"
            "## 2026-08-16 - The three numbers I check first\n\n"
            "- platform: instagram\n"
            "- format: screen recording\n"
            "- link: https://example.test/p/three\n"
            "- hook: I check three numbers first.\n"
            "- job: authority\n"
            "- franchise: The numbers-first franchise\n"
            "- stats: views 4200, saves 90 (as of 2026-08-17)\n"
            "- stats: views 14200, saves 310, watch time 11s (as of 2026-08-19)\n"
            "- multiple: 3.8x vs median 3700 of last 12 (as of 2026-08-19)\n",
            encoding="utf-8",
        )
        pieces = wr.read_posted_ledger(self.content_os)
        self.assertEqual(len(pieces), 1)
        piece = pieces[0]
        self.assertEqual(piece.posted_on, dt.date(2026, 8, 16))
        self.assertEqual(piece.title, "The three numbers I check first")
        self.assertEqual(piece.platform, "instagram")
        self.assertEqual(piece.job, "authority")
        self.assertEqual(piece.multiple, 3.8)
        self.assertEqual(len(piece.stats), 2)
        self.assertEqual(piece.stats[0].as_of, dt.date(2026, 8, 17))
        self.assertEqual(piece.latest_metric("views"), 14200)
        self.assertEqual(piece.latest_metric("saves"), 310)
        self.assertIsNone(piece.latest_metric("follows"))

    def test_a_stats_line_with_no_as_of_date_keeps_its_words(self):
        (self.content_os / "posted.md").write_text(
            "## 2026-08-16 - A piece\n\n- stats: views 900\n", encoding="utf-8"
        )
        piece = wr.read_posted_ledger(self.content_os)[0]
        self.assertIsNone(piece.stats[0].as_of)
        self.assertEqual(piece.stats[0].metrics["views"], 900)
        self.assertIn("views 900", piece.stats[0].raw)

    def test_missing_ledger_is_not_an_error(self):
        self.assertEqual(wr.read_posted_ledger(self.content_os), [])


if __name__ == "__main__":
    unittest.main()
