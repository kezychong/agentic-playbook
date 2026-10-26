#!/usr/bin/env python3
"""Unit test for cutcut.py: pins the EXACT keep and removed windows.

Hard requirement: this must pass before any edit runs. It pins the marker
semantics, each marker deletes the bad take before it plus the marker words, and
only the final take survives, plus the normalising that lets casing and
punctuation variants all match.

Run:  python3 tests/test_cutcut.py
Exit code 0 means pass.
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EDITING = os.path.dirname(HERE)
sys.path.insert(0, EDITING)

import cutcut  # noqa: E402

FIXTURE = os.path.join(HERE, "fixture_three_takes.json")
FINAL_TAKE = "The smartest owner builds machines that make content while you sleep."


def load_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


class TestNormalize(unittest.TestCase):
    def test_strips_space_and_punct_and_lowercases(self):
        self.assertEqual(cutcut.normalize(" Cut,"), "cut")
        self.assertEqual(cutcut.normalize(" cut."), "cut")
        self.assertEqual(cutcut.normalize(" Snip!"), "snip")
        self.assertEqual(cutcut.normalize(" content."), "content")
        self.assertEqual(cutcut.normalize(" month-end"), "monthend")


class TestMarkerDetection(unittest.TestCase):
    def test_finds_both_markers_across_casing_and_punct(self):
        words = cutcut.flatten_words(load_fixture())
        spans = cutcut.find_marker_spans(words, ["cut", "cut"])
        self.assertEqual(len(spans), 2, f"expected 2 markers, got {spans}")

    def test_no_false_marker_when_absent(self):
        words = cutcut.flatten_words(load_fixture())
        spans = cutcut.find_marker_spans(words, ["snip", "snip"])
        self.assertEqual(spans, [])

    def test_a_joined_marker_still_counts(self):
        # Said quickly, the engines return "CutCut" or "cut-cut" as one word. A
        # missed marker leaves the fumble in the video, so both shapes match.
        transcript = {"segments": [{"words": [
            {"word": " First", "start": 0.0, "end": 0.4},
            {"word": " attempt.", "start": 0.4, "end": 1.0},
            {"word": " CutCut", "start": 1.2, "end": 1.8},
            {"word": " Second", "start": 2.0, "end": 2.4},
            {"word": " attempt.", "start": 2.4, "end": 3.0},
        ]}]}
        result = cutcut.cutcut(transcript, "cut cut", 0, 0)
        self.assertEqual(result["markers_found"], 1)
        self.assertEqual(result["keep_windows"][0]["text"], "Second attempt.")

    def test_a_hyphenated_marker_still_counts(self):
        transcript = {"segments": [{"words": [
            {"word": " First", "start": 0.0, "end": 0.4},
            {"word": " attempt.", "start": 0.4, "end": 1.0},
            {"word": " cut-cut,", "start": 1.2, "end": 1.8},
            {"word": " Second", "start": 2.0, "end": 2.4},
            {"word": " attempt.", "start": 2.4, "end": 3.0},
        ]}]}
        result = cutcut.cutcut(transcript, "cut cut", 0, 0)
        self.assertEqual(result["markers_found"], 1)
        self.assertEqual(result["keep_windows"][0]["text"], "Second attempt.")


class TestCutList(unittest.TestCase):
    def setUp(self):
        self.result = cutcut.cutcut(
            load_fixture(), marker="cut cut",
            lead_pad_ms=120, tail_pad_ms=120,
        )

    def test_markers_found(self):
        self.assertEqual(self.result["markers_found"], 2)

    def test_exactly_one_keep_window(self):
        # The whole point: only the final take survives.
        self.assertEqual(len(self.result["keep_windows"]), 1)

    def test_keep_window_bounds_and_text(self):
        kw = self.result["keep_windows"][0]
        # final take starts 7.00 minus 0.12 lead, ends 10.50 plus 0.12 tail
        self.assertAlmostEqual(kw["start"], 6.88, places=3)
        self.assertAlmostEqual(kw["end"], 10.62, places=3)
        self.assertEqual(kw["text"], FINAL_TAKE)

    def test_removed_windows_exact(self):
        removed = self.result["removed_windows"]
        # Order: bad take 1, marker 1, bad take 2, marker 2
        self.assertEqual(len(removed), 4)

        self.assertEqual(removed[0]["reason"], "bad take before marker")
        self.assertAlmostEqual(removed[0]["start"], 0.0, places=3)
        self.assertAlmostEqual(removed[0]["end"], 2.4, places=3)

        self.assertEqual(removed[1]["reason"], "marker words")
        self.assertAlmostEqual(removed[1]["start"], 2.8, places=3)
        self.assertAlmostEqual(removed[1]["end"], 3.35, places=3)

        self.assertEqual(removed[2]["reason"], "bad take before marker")
        self.assertAlmostEqual(removed[2]["start"], 3.8, places=3)
        self.assertAlmostEqual(removed[2]["end"], 5.6, places=3)

        self.assertEqual(removed[3]["reason"], "marker words")
        self.assertAlmostEqual(removed[3]["start"], 6.0, places=3)
        self.assertAlmostEqual(removed[3]["end"], 6.6, places=3)

    def test_marker_words_not_in_kept_text(self):
        kept_text = " ".join(w["text"].lower() for w in self.result["keep_windows"])
        self.assertNotIn("cut cut", kept_text)

    def test_plain_summary_is_member_readable(self):
        lines = cutcut.plain_summary(self.result)
        joined = " ".join(lines)
        self.assertIn("marker", joined)
        self.assertIn("2 attempt(s)", joined)
        # the evidence trail must quote what is being removed
        self.assertIn("hand.", joined)


class TestNoMarkers(unittest.TestCase):
    def test_no_marker_keeps_everything_as_single_window(self):
        result = cutcut.cutcut(
            load_fixture(), marker="snip snip",
            lead_pad_ms=0, tail_pad_ms=0,
        )
        self.assertEqual(len(result["keep_windows"]), 1)
        self.assertEqual(result["markers_found"], 0)
        self.assertEqual(result["removed_windows"], [])
        self.assertAlmostEqual(result["keep_windows"][0]["start"], 0.0, places=3)
        self.assertAlmostEqual(result["keep_windows"][0]["end"], 10.50, places=3)

    def test_plain_summary_says_filmed_clean(self):
        result = cutcut.cutcut(load_fixture(), marker="snip snip",
                               lead_pad_ms=0, tail_pad_ms=0)
        self.assertIn("filmed clean", " ".join(cutcut.plain_summary(result)))


class TestLineScope(unittest.TestCase):
    """The record stage tells members to film the middle as ONE continuous take.
    Under the default scope a single fumble at the end of that take deletes the
    whole thing. Line scope is the road for that member: it deletes back to the
    fumbled line only."""

    def continuous_take(self):
        # Two finished sentences, then a fumbled third line, then the marker,
        # then the line said properly.
        return {"segments": [{"words": [
            {"word": " Margins", "start": 0.0, "end": 0.5},
            {"word": " are", "start": 0.5, "end": 0.8},
            {"word": " the", "start": 0.8, "end": 1.0},
            {"word": " whole", "start": 1.0, "end": 1.4},
            {"word": " game.", "start": 1.4, "end": 2.0},
            {"word": " Most", "start": 2.2, "end": 2.5},
            {"word": " people", "start": 2.5, "end": 2.9},
            {"word": " never", "start": 2.9, "end": 3.3},
            {"word": " check", "start": 3.3, "end": 3.7},
            {"word": " them.", "start": 3.7, "end": 4.2},
            {"word": " And", "start": 4.4, "end": 4.6},
            {"word": " the", "start": 4.6, "end": 4.8},
            {"word": " thing", "start": 4.8, "end": 5.2},
            {"word": " about", "start": 5.2, "end": 5.6},
            {"word": " uh", "start": 5.6, "end": 5.9},
            {"word": " cut", "start": 6.2, "end": 6.5},
            {"word": " cut", "start": 6.5, "end": 6.8},
            {"word": " And", "start": 7.2, "end": 7.4},
            {"word": " the", "start": 7.4, "end": 7.6},
            {"word": " fix", "start": 7.6, "end": 8.0},
            {"word": " is", "start": 8.0, "end": 8.3},
            {"word": " simple.", "start": 8.3, "end": 9.0},
        ]}]}

    def test_default_scope_deletes_the_whole_take(self):
        result = cutcut.cutcut(self.continuous_take(), "cut cut", 0, 0)
        self.assertEqual(len(result["keep_windows"]), 1)
        self.assertAlmostEqual(result["keep_windows"][0]["start"], 7.2, places=3)
        # everything good before the fumble is gone, which is the whole problem
        self.assertNotIn("Margins", result["keep_windows"][0]["text"])

    def test_line_scope_keeps_the_good_run_before_the_fumble(self):
        result = cutcut.cutcut(self.continuous_take(), "cut cut", 0, 0,
                               scope=cutcut.SCOPE_LINE)
        self.assertEqual(result["scope"], "line")
        self.assertEqual(len(result["keep_windows"]), 2)
        first = result["keep_windows"][0]
        self.assertAlmostEqual(first["start"], 0.0, places=3)
        self.assertAlmostEqual(first["end"], 4.2, places=3)
        self.assertIn("Margins", first["text"])
        self.assertIn("never check them.", first["text"])
        # the fumbled line and the marker are the only things removed
        removed = " ".join(w["text"] for w in result["removed_windows"])
        self.assertIn("And the thing about uh", removed)
        self.assertEqual(result["keep_windows"][1]["text"], "And the fix is simple.")

    def test_line_scope_falls_back_when_there_is_no_boundary(self):
        # A single unfinished line with no sentence end and no pause behaves
        # exactly like the default scope.
        transcript = {"segments": [{"words": [
            {"word": " one", "start": 0.0, "end": 0.3},
            {"word": " two", "start": 0.3, "end": 0.6},
            {"word": " cut", "start": 0.6, "end": 0.9},
            {"word": " cut", "start": 0.9, "end": 1.2},
            {"word": " three", "start": 1.4, "end": 1.8},
        ]}]}
        line = cutcut.cutcut(transcript, "cut cut", 0, 0, scope=cutcut.SCOPE_LINE)
        full = cutcut.cutcut(transcript, "cut cut", 0, 0)
        self.assertEqual(line["keep_windows"], full["keep_windows"])

    def test_long_removal_warns_the_member(self):
        long_take = {"segments": [{"words": (
            [{"word": " word", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(60)]
            + [{"word": " cut", "start": 31.0, "end": 31.3},
               {"word": " cut", "start": 31.3, "end": 31.6},
               {"word": " done.", "start": 32.0, "end": 32.5}]
        )}]}
        result = cutcut.cutcut(long_take, "cut cut", 0, 0)
        self.assertIn("Heads up", " ".join(cutcut.plain_summary(result)))


class TestAlternativeMarker(unittest.TestCase):
    def test_member_can_choose_their_own_marker(self):
        transcript = {
            "segments": [{
                "words": [
                    {"word": " First", "start": 0.0, "end": 0.4},
                    {"word": " attempt.", "start": 0.4, "end": 1.0},
                    {"word": " Snip", "start": 1.2, "end": 1.5},
                    {"word": " snip.", "start": 1.5, "end": 1.8},
                    {"word": " Second", "start": 2.0, "end": 2.4},
                    {"word": " attempt.", "start": 2.4, "end": 3.0},
                ]
            }]
        }
        result = cutcut.cutcut(transcript, marker="snip snip",
                               lead_pad_ms=0, tail_pad_ms=0)
        self.assertEqual(result["markers_found"], 1)
        self.assertEqual(len(result["keep_windows"]), 1)
        self.assertEqual(result["keep_windows"][0]["text"], "Second attempt.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
