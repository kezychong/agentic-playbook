#!/usr/bin/env python3
"""End-to-end test on media this test makes for itself.

It builds its own recording, no fixtures on disk, and drives the REAL tools:

    say  ->  ffmpeg (bad take + the marker + good take, into one video)
         ->  transcribe.py  (whichever engine this machine has)
         ->  cutcut.py       (the marker cut list)
         ->  render_cuts.py  (ffmpeg join, into a clean master)

What it proves:
  * the master is meaningfully shorter than the recording,
  * the marker word does not survive in the master (proved by transcribing the
    master again),
  * the bad take is gone and the good take is still there.

Best effort by design. It needs a voice generator, ffmpeg, and a transcription
engine. If any of those is missing it SKIPS with a clear message instead of
failing, because a member machine without them is a setup question, not a
broken chain. The voice generator here is the one built into macOS, so this
test skips entirely on other systems. The rest of the chain does not.

All media goes into a temporary folder. Nothing is written near the pack.

Run:  python3 tests/test_e2e_synthetic.py
Exit 0 means pass or skip. Anything else is a real regression.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EDITING = os.path.dirname(HERE)

TEMP_ROOT = tempfile.mkdtemp(prefix="content-os-edit-e2e-")
os.environ["CONTENT_OS_MEDIA_DIR"] = os.path.join(TEMP_ROOT, "media")
sys.path.insert(0, EDITING)
import setup_editing  # noqa: E402

BAD_TAKE = "Most owners post every single day by hand."
GOOD_TAKE = "The smartest owner builds machines that make content while they sleep."
MARKER = "cut cut"

BAD_DISTINCTIVE = "hand"        # only in the bad take
GOOD_DISTINCTIVE = "machines"   # only in the good take


def have_engine():
    return bool(setup_editing.detect()["engines_found"])


def have(*names):
    return all(shutil.which(n) for n in names)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path]).stdout.strip()
    return float(out)


@unittest.skipUnless(platform.system() == "Darwin", "the built-in voice generator is macOS only")
@unittest.skipUnless(have("say", "ffmpeg", "ffprobe"), "needs say, ffmpeg and ffprobe")
@unittest.skipUnless(have_engine(), "needs a transcription engine, run setup_editing.py --check")
class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = os.path.join(TEMP_ROOT, "media", "runs", "e2e")
        os.makedirs(cls.d, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if not getattr(cls, "_keep", False):
            shutil.rmtree(TEMP_ROOT, ignore_errors=True)

    def _say(self, text, out):
        r = run(["say", "-o", out, text])
        self.assertEqual(r.returncode, 0, r.stderr)

    def _tool(self, name, *args):
        r = run([sys.executable, os.path.join(EDITING, name), *args])
        self.assertEqual(r.returncode, 0, f"{name} failed:\n{r.stdout}\n{r.stderr}")
        return r

    def test_pipeline(self):
        d = self.d
        # 1. build the audio: bad take, marker, good take
        self._say(BAD_TAKE, f"{d}/t1.aiff")
        self._say(MARKER, f"{d}/m.aiff")
        self._say(GOOD_TAKE, f"{d}/t2.aiff")
        cat = run([
            "ffmpeg", "-y", "-i", f"{d}/t1.aiff", "-i", f"{d}/m.aiff",
            "-i", f"{d}/t2.aiff", "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]", "-map", "[a]",
            "-ar", "16000", "-ac", "1", f"{d}/audio.wav",
        ])
        self.assertEqual(cat.returncode, 0, cat.stderr)

        # 2. wrap a real video around that audio
        dur = duration(f"{d}/audio.wav")
        vid = run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=navy:s=640x1136:d={dur}",
            "-i", f"{d}/audio.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", f"{d}/raw.mp4",
        ])
        self.assertEqual(vid.returncode, 0, vid.stderr)
        in_dur = duration(f"{d}/raw.mp4")

        # 3. transcribe, cut, render
        self._tool("transcribe.py", f"{d}/raw.mp4", "-o", f"{d}/words.json")
        self._tool("cutcut.py", f"{d}/words.json", "-o", f"{d}/cuts.json",
                   "--marker", MARKER)
        self._tool("render_cuts.py", f"{d}/cuts.json", f"{d}/raw.mp4",
                   "-o", f"{d}/master.mp4")

        # ---- what has to be true ----
        out_dur = duration(f"{d}/master.mp4")
        self.assertLess(out_dur, in_dur * 0.8,
                        f"master ({out_dur:.2f}s) is not meaningfully shorter than "
                        f"the recording ({in_dur:.2f}s)")

        with open(f"{d}/cuts.json", encoding="utf-8") as f:
            cuts = json.load(f)
        self.assertGreaterEqual(cuts["markers_found"], 1)
        removed_text = " ".join(r["text"].lower() for r in cuts["removed_windows"])
        self.assertIn(BAD_DISTINCTIVE, removed_text,
                      "the bad take should be listed in what was removed")

        # transcribe the MASTER again: marker gone, good take there, bad take not
        self._tool("transcribe.py", f"{d}/master.mp4", "-o", f"{d}/master.words.json")
        with open(f"{d}/master.words.json", encoding="utf-8") as f:
            master = json.load(f)
        master_text = master["text"].lower()
        self.assertIn(GOOD_DISTINCTIVE, master_text,
                      f"the good take is missing from the master: {master_text!r}")
        self.assertNotIn(BAD_DISTINCTIVE, master_text,
                         f"the bad take survived in the master: {master_text!r}")
        self.assertNotIn("cut cut", master_text,
                         f"the marker survived in the master: {master_text!r}")

    def test_line_scope_keeps_the_clean_run(self):
        """The continuous-take case: good sentence, fumbled line, marker, retry.

        Line scope has to keep the good sentence AND the retry, which also means
        the render has to join two separate stretches. That join is where a
        grouped filter graph silently fails, so this is the case that guards it.
        """
        d = os.path.join(self.d, "line")
        os.makedirs(d, exist_ok=True)
        self._say("Margins are the whole game.", f"{d}/a.aiff")
        self._say("And the thing about", f"{d}/b.aiff")
        self._say(MARKER, f"{d}/m.aiff")
        self._say("And the fix is simple.", f"{d}/c.aiff")
        gap = run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                   "anullsrc=r=22050:cl=mono:d=1", f"{d}/gap.wav"])
        self.assertEqual(gap.returncode, 0, gap.stderr)
        cat = run([
            "ffmpeg", "-y",
            "-i", f"{d}/a.aiff", "-i", f"{d}/gap.wav", "-i", f"{d}/b.aiff",
            "-i", f"{d}/m.aiff", "-i", f"{d}/c.aiff", "-filter_complex",
            "[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[a]", "-map", "[a]",
            "-ar", "16000", "-ac", "1", f"{d}/audio.wav",
        ])
        self.assertEqual(cat.returncode, 0, cat.stderr)
        dur = duration(f"{d}/audio.wav")
        vid = run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=640x1136:d={dur}",
            "-i", f"{d}/audio.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", f"{d}/raw.mp4",
        ])
        self.assertEqual(vid.returncode, 0, vid.stderr)

        self._tool("transcribe.py", f"{d}/raw.mp4", "-o", f"{d}/words.json")
        self._tool("cutcut.py", f"{d}/words.json", "-o", f"{d}/cuts.json",
                   "--marker", MARKER, "--scope", "line")
        with open(f"{d}/cuts.json", encoding="utf-8") as f:
            cuts = json.load(f)
        self.assertEqual(cuts["scope"], "line")
        self.assertEqual(len(cuts["keep_windows"]), 2,
                         f"line scope should keep two stretches: {cuts['keep_windows']}")

        self._tool("render_cuts.py", f"{d}/cuts.json", f"{d}/raw.mp4",
                   "-o", f"{d}/master.mp4")
        self._tool("transcribe.py", f"{d}/master.mp4", "-o", f"{d}/master.words.json")
        with open(f"{d}/master.words.json", encoding="utf-8") as f:
            master_text = json.load(f)["text"].lower()
        self.assertIn("margins", master_text,
                      f"the clean sentence should survive line scope: {master_text!r}")
        self.assertIn("fix is simple", master_text)
        self.assertNotIn("cut cut", master_text)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if not result.wasSuccessful():
        TestEndToEnd._keep = True  # leave the media behind for a look
    sys.exit(0 if result.wasSuccessful() else 1)
