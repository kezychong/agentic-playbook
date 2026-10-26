#!/usr/bin/env python3
"""Chain tests that need no video and no engine installed.

What this pins:
  * the media rules: video never lands in content-os, never in a synced folder,
    and a synced SOURCE file is a warning rather than a refusal,
  * the silence inversion maths, with the padding floor,
  * the cut-list clamping and the filter graph the render builds, including the
    optional audio levelling,
  * the export preset sizes and their crop rule,
  * the transcript normalising that lets three different engines feed one shape,
  * the setup report shape the agent reads before it promises anything.

Run:  python3 tests/test_chain.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EDITING = os.path.dirname(HERE)
sys.path.insert(0, EDITING)

TEMP_ROOT = tempfile.mkdtemp(prefix="content-os-edit-tests-")
os.environ["CONTENT_OS_MEDIA_DIR"] = os.path.join(TEMP_ROOT, "media")

import media_workspace  # noqa: E402
import silence_trim  # noqa: E402
import render_cuts  # noqa: E402
import export_presets  # noqa: E402
import setup_editing  # noqa: E402
import transcribe  # noqa: E402


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("not really a video")
    return path


class TestMediaRules(unittest.TestCase):
    def test_workspace_comes_from_the_environment(self):
        self.assertEqual(media_workspace.workspace_dir(),
                         media_workspace.real(os.path.join(TEMP_ROOT, "media")))

    def test_a_normal_local_path_is_fine(self):
        target = os.path.join(TEMP_ROOT, "media", "runs", "one", "master.mp4")
        self.assertEqual(media_workspace.check_output_path(target, "test"),
                         media_workspace.real(target))

    def test_synced_folder_names_are_caught(self):
        for folder in ("Dropbox", "OneDrive", "Google Drive", "OneDrive - Acme Ltd"):
            path = os.path.join(TEMP_ROOT, folder, "master.mp4")
            self.assertIsNotNone(media_workspace.synced_reason(path), folder)

    def test_icloud_fragment_is_caught(self):
        path = os.path.join(TEMP_ROOT, "Library", "Mobile Documents",
                            "com~apple~CloudDocs", "master.mp4")
        self.assertIsNotNone(media_workspace.synced_reason(path))

    def test_writing_media_into_a_synced_folder_is_refused(self):
        path = os.path.join(TEMP_ROOT, "Dropbox", "master.mp4")
        with self.assertRaises(SystemExit):
            media_workspace.check_output_path(path, "test")

    def test_writing_media_into_the_text_workspace_is_refused(self):
        path = os.path.join(TEMP_ROOT, "work", "content-os", "scripts", "master.mp4")
        self.assertTrue(media_workspace.inside_text_workspace(path))
        with self.assertRaises(SystemExit):
            media_workspace.check_output_path(path, "test")

    def test_reading_from_a_synced_folder_is_allowed_with_a_warning(self):
        path = touch(os.path.join(TEMP_ROOT, "Dropbox", "raw.mp4"))
        self.assertEqual(media_workspace.check_input_path(path, "test"),
                         media_workspace.real(path))

    def test_report_flags_safety(self):
        report = media_workspace.report(os.path.join(TEMP_ROOT, "Dropbox", "x.mp4"))
        self.assertFalse(report["safe_for_media_output"])


class TestSilenceMaths(unittest.TestCase):
    def test_padding_floor_is_enforced(self):
        self.assertEqual(silence_trim.MIN_PAD_MS, 150)

    def test_silences_invert_into_keep_windows(self):
        # one 2 second silence in the middle of a 10 second file, 150ms padding
        keep = silence_trim.silences_to_keep_windows([(4.0, 6.0)], 10.0, 0.15)
        self.assertEqual(keep, [(0.0, 4.15), (5.85, 10.0)])

    def test_short_gaps_survive_the_padding(self):
        # a 0.2 second gap shrinks to nothing once padded, so nothing is cut
        keep = silence_trim.silences_to_keep_windows([(4.0, 4.2)], 10.0, 0.15)
        self.assertEqual(keep, [(0.0, 10.0)])

    def test_trailing_silence_with_no_end_uses_the_duration(self):
        # A silence that runs to the end of the file still keeps its padding, so
        # the last sliver of room tone survives rather than the file ending on a
        # hard stop.
        keep = silence_trim.silences_to_keep_windows([(8.0, None)], 10.0, 0.15)
        self.assertEqual(keep, [(0.0, 8.15), (9.85, 10.0)])


class TestRenderPlanning(unittest.TestCase):
    def test_clamping_drops_slivers_and_merges_overlaps(self):
        windows = [
            {"start": -1.0, "end": 2.0},
            {"start": 1.9, "end": 3.0},     # overlaps the one before
            {"start": 5.0, "end": 5.005},   # a sliver, dropped
            {"start": 8.0, "end": 99.0},    # clamped to the real length
        ]
        merged = render_cuts.clamp_windows(windows, 10.0)
        self.assertEqual(merged, [(0.0, 3.0), (8.0, 10.0)])

    def test_filter_graph_trims_and_joins(self):
        graph, v, a = render_cuts.build_filter([(0.0, 2.0), (5.0, 7.5)])
        self.assertIn("trim=start=0.000:end=2.000", graph)
        self.assertIn("atrim=start=5.000:end=7.500", graph)
        self.assertIn("concat=n=2:v=1:a=1", graph)
        self.assertEqual((v, a), ("[outv]", "[outa]"))

    def test_join_inputs_are_interleaved(self):
        # Two surviving stretches happen whenever somebody fumbles twice with a
        # clean run in between. The joining filter refuses grouped labels, so
        # this pins the interleaving that makes that case work at all.
        graph, _, _ = render_cuts.build_filter([(0.0, 2.0), (5.0, 7.5)])
        self.assertIn("[v0][a0][v1][a1]concat=n=2", graph)
        self.assertNotIn("[v0][v1][a0][a1]", graph)

    def test_optional_audio_levelling_is_off_unless_asked(self):
        plain, _, plain_audio = render_cuts.build_filter([(0.0, 2.0)])
        self.assertNotIn("loudnorm", plain)
        self.assertEqual(plain_audio, "[outa]")
        levelled, _, levelled_audio = render_cuts.build_filter(
            [(0.0, 2.0)], normalize_audio=True)
        self.assertIn("loudnorm=I=-14:TP=-1.5:LRA=11", levelled)
        self.assertEqual(levelled_audio, "[outa_clean]")

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg for the dry run")
    def test_dry_run_builds_a_command_without_touching_media(self):
        source = touch(os.path.join(TEMP_ROOT, "media", "runs", "dry", "raw.mp4"))
        cuts = os.path.join(TEMP_ROOT, "media", "runs", "dry", "take.cuts.json")
        with open(cuts, "w", encoding="utf-8") as f:
            json.dump({"keep_windows": [{"start": 1.0, "end": 4.0}]}, f)
        out = os.path.join(TEMP_ROOT, "media", "runs", "dry", "master.mp4")
        render_cuts.render(cuts, source, out, dry_run=True)
        self.assertFalse(os.path.isfile(out), "a dry run must not write a file")

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg for the dry run")
    def test_render_refuses_a_synced_destination(self):
        source = touch(os.path.join(TEMP_ROOT, "media", "runs", "dry2", "raw.mp4"))
        cuts = os.path.join(TEMP_ROOT, "media", "runs", "dry2", "take.cuts.json")
        with open(cuts, "w", encoding="utf-8") as f:
            json.dump({"keep_windows": [{"start": 0.0, "end": 2.0}]}, f)
        with self.assertRaises(SystemExit):
            render_cuts.render(cuts, source,
                               os.path.join(TEMP_ROOT, "Dropbox", "master.mp4"),
                               dry_run=True)


class TestExportPresets(unittest.TestCase):
    def test_the_three_sizes_are_the_delivery_shapes(self):
        self.assertEqual(export_presets.PRESETS["9x16"][:2], (1080, 1920))
        self.assertEqual(export_presets.PRESETS["1x1"][:2], (1080, 1080))
        self.assertEqual(export_presets.PRESETS["16x9"][:2], (1920, 1080))

    def test_crop_rule_fills_and_centres_without_stretching(self):
        rule = export_presets.fill_crop(1080, 1920)
        self.assertIn("force_original_aspect_ratio=increase", rule)
        self.assertIn("crop=1080:1920", rule)

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg for the dry run")
    def test_dry_run_names_all_three_files(self):
        master = touch(os.path.join(TEMP_ROOT, "media", "runs", "x", "master.mp4"))
        written = export_presets.export(master, dry_run=True)
        self.assertEqual(
            [os.path.basename(p) for p in written],
            ["master-9x16.mp4", "master-1x1.mp4", "master-16x9.mp4"],
        )


class TestTranscriptNormalising(unittest.TestCase):
    def test_tokens_group_into_words(self):
        entry = {
            "tokens": [
                {"text": "[_BEG_]", "offsets": {"from": 0, "to": 0}, "p": 1.0},
                {"text": " Most", "offsets": {"from": 0, "to": 200}, "p": 0.9},
                {"text": " own", "offsets": {"from": 200, "to": 320}, "p": 0.8},
                {"text": "ers", "offsets": {"from": 320, "to": 400}, "p": 0.7},
                {"text": " post.", "offsets": {"from": 400, "to": 600}, "p": 0.95},
            ]
        }
        words = transcribe.tokens_to_words(entry)
        self.assertEqual([w["word"] for w in words], [" Most", " owners", " post."])
        self.assertAlmostEqual(words[1]["start"], 0.2)
        self.assertAlmostEqual(words[1]["end"], 0.4)
        self.assertAlmostEqual(words[1]["probability"], 0.7)

    def test_whispercpp_output_becomes_the_shared_shape(self):
        raw = {
            "transcription": [
                {
                    "offsets": {"from": 0, "to": 600},
                    "text": " Most owners post.",
                    "tokens": [
                        {"text": " Most", "offsets": {"from": 0, "to": 200}, "p": 0.9},
                        {"text": " owners", "offsets": {"from": 200, "to": 400}, "p": 0.9},
                        {"text": " post.", "offsets": {"from": 400, "to": 600}, "p": 0.9},
                    ],
                }
            ]
        }
        data = transcribe.normalise_whispercpp(raw, "en")
        self.assertEqual(data["language"], "en")
        self.assertEqual(len(data["segments"]), 1)
        words = data["segments"][0]["words"]
        self.assertEqual(len(words), 3)
        self.assertEqual(words[0]["word"], " Most")
        self.assertAlmostEqual(data["segments"][0]["end"], 0.6)

    def test_a_normalised_transcript_feeds_the_cut_step(self):
        import cutcut
        raw = {
            "transcription": [{
                "offsets": {"from": 0, "to": 3000},
                "text": " First go. Cut cut. Second go.",
                "tokens": [
                    {"text": " First", "offsets": {"from": 0, "to": 400}, "p": 0.9},
                    {"text": " go.", "offsets": {"from": 400, "to": 800}, "p": 0.9},
                    {"text": " Cut", "offsets": {"from": 1000, "to": 1200}, "p": 0.9},
                    {"text": " cut.", "offsets": {"from": 1200, "to": 1400}, "p": 0.9},
                    {"text": " Second", "offsets": {"from": 1800, "to": 2200}, "p": 0.9},
                    {"text": " go.", "offsets": {"from": 2200, "to": 2600}, "p": 0.9},
                ],
            }]
        }
        data = transcribe.normalise_whispercpp(raw, "en")
        result = cutcut.cutcut(data, "cut cut", 0, 0)
        self.assertEqual(result["markers_found"], 1)
        self.assertEqual(result["keep_windows"][0]["text"], "Second go.")


class TestSetupReport(unittest.TestCase):
    def test_report_has_the_keys_the_agent_reads(self):
        state = setup_editing.detect()
        for key in ("ffmpeg", "ffprobe", "engines_found", "preferred_engine",
                    "core_chain_ready", "overlay_layer_ready", "media_workspace",
                    "package_manager", "machine"):
            self.assertIn(key, state)

    def test_report_is_json_serializable(self):
        json.dumps(setup_editing.detect())

    def test_plain_summary_says_something_useful_either_way(self):
        lines = setup_editing.plain_summary(setup_editing.detect())
        self.assertTrue(lines)
        self.assertTrue(all(isinstance(line, str) and line for line in lines))

    def test_the_tools_environment_lives_in_the_media_workspace(self):
        self.assertTrue(
            setup_editing.venv_dir().startswith(media_workspace.workspace_dir())
        )


def tearDownModule():
    shutil.rmtree(TEMP_ROOT, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
