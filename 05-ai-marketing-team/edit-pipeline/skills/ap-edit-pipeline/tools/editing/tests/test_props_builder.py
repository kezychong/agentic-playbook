#!/usr/bin/env python3
"""Unit test for the overlay props builder. Needs nothing installed.

Feeds the shared fixture plus a made-up manifest through build_input_props and
pins exactly what the overlay app will receive: word count, specific words and
timings, the hook window, the caption style merge, and the proof windows.

This proves the contract between the two halves of the overlay layer without
ever starting a render.

Run:  python3 tests/test_props_builder.py
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EDITING = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EDITING, "overlay"))
from props_builder import build_input_props, extract_words  # noqa: E402

# The same fixture the cut test uses: 3 takes and 2 markers, 29 timed words.
# Note the props builder does NOT apply any cut logic, that is cutcut.py's job.
# The overlay captions every word of whatever master it is given, so all 29
# words are expected here (8 + 2 + 6 + 2 + 11).
FIXTURE = os.path.join(HERE, "fixture_three_takes.json")

MANIFEST = {
    "hook_text": "The mistake I see in eight out of ten of these",
    "hook_duration_seconds": 2.0,
    "captions": {
        "enabled": True,
        "font_size_px": 80,
        "active_color": "#00FF88",
        "max_words_per_group": 3,
    },
    "proof_assets": [
        {
            "path": "~/ContentStudio/proof/shot.png",
            "start": 4.4,
            "end": 6.6,
            "position": "top",
            "caption": "the actual report",
        }
    ],
}


class TestPropsBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, encoding="utf-8") as f:
            cls.words_json = json.load(f)
        cls.props = build_input_props(
            cls.words_json, MANIFEST,
            fps=30, width=1080, height=1920, duration_seconds=10.5,
        )

    def test_dimensions_and_timing(self):
        self.assertEqual(self.props["fps"], 30)
        self.assertEqual(self.props["width"], 1080)
        self.assertEqual(self.props["height"], 1920)
        self.assertEqual(self.props["durationInSeconds"], 10.5)

    def test_word_count(self):
        self.assertEqual(len(self.props["words"]), 29)
        self.assertEqual(len(extract_words(self.words_json)), 29)

    def test_first_and_last_word(self):
        first = self.props["words"][0]
        # leading space stripped, timing untouched
        self.assertEqual(first, {"text": "Most", "start": 0.0, "end": 0.2})
        last = self.props["words"][-1]
        self.assertEqual(last["text"], "sleep.")
        self.assertAlmostEqual(last["start"], 10.10)
        self.assertAlmostEqual(last["end"], 10.50)

    def test_marker_words_are_present_uncut(self):
        # The overlay does not cut, so the marker words are still in the stream.
        texts = [w["text"] for w in self.props["words"]]
        self.assertIn("cut", texts)
        self.assertIn("Cut,", texts)

    def test_hook_window(self):
        self.assertEqual(self.props["hookText"],
                         "The mistake I see in eight out of ten of these")
        self.assertEqual(self.props["hookDurationSeconds"], 2.0)

    def test_caption_style_merges_manifest_over_defaults(self):
        style = self.props["captionStyle"]
        self.assertEqual(style["fontSizePx"], 80)           # from the manifest
        self.assertEqual(style["activeColor"], "#00FF88")   # from the manifest
        self.assertEqual(style["maxWordsPerGroup"], 3)      # from the manifest
        self.assertEqual(style["inactiveColor"], "#B8B8B8")  # default kept
        self.assertEqual(style["bottomMarginPx"], 320)      # default kept

    def test_captions_enabled_flag(self):
        self.assertTrue(self.props["captionsEnabled"])

    def test_proof_windows(self):
        self.assertEqual(len(self.props["proof"]), 1)
        proof = self.props["proof"][0]
        self.assertEqual(proof["assetPath"],
                         os.path.expanduser("~/ContentStudio/proof/shot.png"))
        self.assertEqual(proof["start"], 4.4)
        self.assertEqual(proof["end"], 6.6)
        self.assertEqual(proof["position"], "top")
        self.assertEqual(proof["label"], "the actual report")

    def test_disabling_captions_drops_words(self):
        m = dict(MANIFEST)
        m["captions"] = {"enabled": False}
        props = build_input_props(
            self.words_json, m,
            fps=30, width=1080, height=1920, duration_seconds=10.5,
        )
        self.assertFalse(props["captionsEnabled"])
        self.assertEqual(props["words"], [])

    def test_output_is_json_serializable(self):
        json.dumps(self.props)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False, verbosity=2).result.wasSuccessful() else 1)
