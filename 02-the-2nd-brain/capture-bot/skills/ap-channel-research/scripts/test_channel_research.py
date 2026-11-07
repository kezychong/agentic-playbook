#!/usr/bin/env python3
"""Deterministic offline regression tests for channel research."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import channel_research as channel  # noqa: E402


YTDLP_ISOLATION_PREFIX = [
    "--ignore-config",
    "--no-plugin-dirs",
    "--no-cookies",
    "--no-cookies-from-browser",
    "--no-cache-dir",
    "--no-exec",
]
YTDLP_OVERRIDE_FLAGS = {
    "--config-locations",
    "--plugin-dirs",
    "--cookies",
    "--cookies-from-browser",
    "-n",
    "--netrc",
    "--netrc-location",
    "--netrc-cmd",
    "--exec",
    "--cache-dir",
}


def fixture_args(**changes: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "keyword": "memory",
        "since": "2026-01-01",
        "until": None,
        "limit": 2,
        "scan": 10,
        "captions_only": True,
        "lang": None,
        "model": "base",
        "sub_langs": "en.*",
        "max_seconds": 300,
        "sleep": 1.0,
    }
    values.update(changes)
    return argparse.Namespace(**values)


def fixture_manifest(videos: list[dict] | None = None) -> dict:
    return channel.build_manifest(
        "https://www.youtube.com/@example/videos",
        fixture_args(),
        videos
        or [
            {
                "id": "fixture001",
                "title": "Memory fixture",
                "url": "https://youtube.com/watch?v=fixture001",
                "published": "2026-11-07",
            }
        ],
    )


class ExistingBehaviorTests(unittest.TestCase):
    def test_resolves_channel_and_filters(self) -> None:
        self.assertEqual(channel.resolve_channel("example"), "https://www.youtube.com/@example/videos")
        self.assertEqual(
            channel.resolve_channel("https://www.youtube.com/@example"),
            "https://www.youtube.com/@example/videos",
        )
        self.assertTrue(channel.keyword_match("Agent memory patterns", ["memory"]))
        self.assertFalse(channel.keyword_match("Cooking", ["memory"]))
        self.assertTrue(channel.in_date_range("2026-11-07", "2026-01-01", "2026-12-31"))

    def test_manifest_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "manifest.json"
            channel.write_manifest(path, fixture_manifest())
            loaded = channel.load_manifest(path)
            self.assertEqual(loaded["videos"][0]["id"], "fixture001")
            json.loads(path.read_text(encoding="utf-8"))

    def test_dry_run_is_offline(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HERE / "channel_research.py"), "@example", "--list-only", "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"network_access": false', result.stdout)


class ManifestApprovalTests(unittest.TestCase):
    def test_manifest_write_refuses_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            escaped = root / "escaped.json"
            path = root / "manifest.json"
            path.symlink_to(escaped)
            with self.assertRaises(FileExistsError):
                channel.write_manifest(path, fixture_manifest())
            self.assertTrue(path.is_symlink())
            self.assertFalse(escaped.exists())

    def test_mutated_manifest_fails_approved_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            original = json.dumps(fixture_manifest(), ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
            path.write_bytes(original)
            approved_digest = hashlib.sha256(original).hexdigest()
            path.write_bytes(original.replace(b"fixture001", b"fixture999"))
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                channel.load_manifest(path, approved_sha256=approved_digest)

    def test_build_requires_explicit_approved_sha256(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HERE / "channel_research.py"),
                "@example",
                "--build",
                "--approved",
                "--approved-manifest",
                "missing.json",
                "--out",
                "missing-output",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--approved-sha256", result.stderr)

    def test_manifest_rejects_duplicate_ids_and_urls(self) -> None:
        cases = (
            [
                {"id": "same", "title": "One", "url": "https://youtube.com/watch?v=one"},
                {"id": "same", "title": "Two", "url": "https://youtube.com/watch?v=two"},
            ],
            [
                {"id": "one", "title": "One", "url": "https://youtube.com/watch?v=same"},
                {"id": "two", "title": "Two", "url": "https://youtube.com/watch?v=same"},
            ],
        )
        for videos in cases:
            with self.subTest(videos=videos), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(fixture_manifest(videos)), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    channel.load_manifest(path)


class SafeCorpusWriteTests(unittest.TestCase):
    def test_index_write_refuses_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            escaped = root / "escaped.md"
            (root / "_INDEX.md").symlink_to(escaped)
            with self.assertRaises(FileExistsError):
                channel.write_index(root, "example", [], Path("manifest.json"))
            self.assertTrue((root / "_INDEX.md").is_symlink())
            self.assertFalse(escaped.exists())

    def test_corpus_note_write_refuses_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            escaped = root / "escaped.md"
            (root / "note.md").symlink_to(escaped)
            with self.assertRaises(FileExistsError):
                channel.write_corpus_note(root, "note", "private")
            self.assertTrue((root / "note.md").is_symlink())
            self.assertFalse(escaped.exists())

    def test_build_requires_preexisting_real_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            digest = channel.write_manifest(manifest_path, fixture_manifest())
            args = argparse.Namespace(
                approved=True,
                approved_manifest=manifest_path,
                approved_sha256=digest,
                out=root / "not-created",
            )
            with (
                mock.patch.object(channel.media, "probe") as probe,
                self.assertRaisesRegex(SystemExit, "already-existing"),
            ):
                channel.build_phase(args, "https://www.youtube.com/@example/videos")
            probe.assert_not_called()

    def test_corpus_filename_includes_video_identity(self) -> None:
        first = {"id": "video-A", "title": "Same title", "upload_date": "20261107"}
        second = {"id": "video-B", "title": "Same title", "upload_date": "20261107"}
        self.assertNotEqual(channel.corpus_stem(first, "2026-11-07"), channel.corpus_stem(second, "2026-11-07"))
        self.assertIn("video-a", channel.corpus_stem(first, "2026-11-07"))

    def test_corpus_note_rejects_secret_bearing_source_url(self) -> None:
        metadata = {"id": "fixture", "title": "Fixture", "webpage_url": "https://youtube.com/watch?v=x&token=secret"}
        transcript = {"method": "none", "language": "", "text": "", "caveat": "missing"}
        with self.assertRaises(ValueError):
            channel.corpus_note(metadata, transcript, "example")


class ListPhaseTests(unittest.TestCase):
    def test_channel_enumeration_uses_fail_closed_yt_dlp_prefix(self) -> None:
        completed = subprocess.CompletedProcess([], 0, '{"entries":[]}', "")
        with (
            mock.patch.object(channel.media, "YTDLP", "yt-dlp"),
            mock.patch.object(channel.media, "require_tools"),
            mock.patch.object(
                channel.media,
                "validate_public_resolution",
                return_value="https://www.youtube.com/@example/videos",
            ),
            mock.patch.object(channel.media, "_run", return_value=completed) as runner,
        ):
            self.assertEqual(
                channel.enumerate_videos("https://www.youtube.com/@example/videos", 1),
                [],
            )
        command = runner.call_args.args[0]
        self.assertEqual(command[0], "yt-dlp")
        self.assertEqual(command[1 : 1 + len(YTDLP_ISOLATION_PREFIX)], YTDLP_ISOLATION_PREFIX)
        self.assertEqual(command[1 + len(YTDLP_ISOLATION_PREFIX)], "--flat-playlist")
        self.assertTrue(YTDLP_OVERRIDE_FLAGS.isdisjoint(command))

    def test_enumeration_failure_sanitizes_subprocess_stderr(self) -> None:
        completed = subprocess.CompletedProcess(
            [],
            1,
            "",
            "request https://youtube.com/private Authorization: Bearer bearer-secret api_key=api-secret",
        )
        with (
            mock.patch.object(channel.media, "YTDLP", "yt-dlp"),
            mock.patch.object(channel.media, "require_tools"),
            mock.patch.object(
                channel.media,
                "validate_public_resolution",
                return_value="https://www.youtube.com/@example/videos",
            ),
            mock.patch.object(channel.media, "_run", return_value=completed),
            self.assertRaises(RuntimeError) as raised,
        ):
            channel.enumerate_videos("https://www.youtube.com/@example/videos", 1)
        message = str(raised.exception)
        self.assertNotIn("https://", message)
        self.assertNotIn("bearer-secret", message)
        self.assertNotIn("api-secret", message)
        self.assertIn("[redacted]", message)

    def test_enumeration_uses_bounded_runner_and_dns_preflight(self) -> None:
        payload = json.dumps({"entries": [{"id": "fixture", "title": "Memory", "url": "https://youtube.com/watch?v=fixture"}]})
        completed = subprocess.CompletedProcess([], 0, payload, "")
        with (
            mock.patch.object(channel.media, "YTDLP", "yt-dlp"),
            mock.patch.object(channel.media, "require_tools"),
            mock.patch.object(channel.media, "validate_public_resolution", return_value="https://www.youtube.com/@example/videos") as dns_check,
            mock.patch.object(channel.media, "_run", return_value=completed) as bounded,
        ):
            videos = channel.enumerate_videos("https://www.youtube.com/@example/videos", 1)
        self.assertEqual(videos[0]["id"], "fixture")
        dns_check.assert_called_once()
        bounded.assert_called_once()

    def test_scans_full_bounded_candidate_list_until_limit_matches(self) -> None:
        videos = [
            {"id": f"video{index}", "title": "Memory", "url": f"https://youtube.com/watch?v=video{index}"}
            for index in range(8)
        ]

        def probe(url: str) -> dict:
            index = int(url.rsplit("video", 1)[1])
            return {
                "id": f"video{index}",
                "title": "Memory",
                "webpage_url": url,
                "upload_date": "20260101" if index >= 6 else "20250101",
            }

        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            args = fixture_args(limit=2, scan=8, manifest=manifest_path)
            with (
                mock.patch.object(channel, "enumerate_videos", return_value=videos),
                mock.patch.object(channel.media, "probe", side_effect=probe),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = channel.list_phase(args, "https://www.youtube.com/@example/videos")
            self.assertEqual(result, 0)
            loaded = channel.load_manifest(manifest_path)
            self.assertEqual([video["id"] for video in loaded["videos"]], ["video6", "video7"])

    def test_probe_failures_are_reported_separately_from_zero_matches(self) -> None:
        videos = [{"id": "broken", "title": "Memory", "url": "https://youtube.com/watch?v=broken"}]
        with tempfile.TemporaryDirectory() as directory:
            args = fixture_args(limit=1, scan=1, manifest=Path(directory) / "manifest.json")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(channel, "enumerate_videos", return_value=videos),
                mock.patch.object(channel.media, "probe", side_effect=RuntimeError("fixture probe failed")),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                result = channel.list_phase(args, "https://www.youtube.com/@example/videos")
            self.assertEqual(result, 2)
            self.assertIn("metadata probe", stderr.getvalue().lower())
            self.assertIn("fixture probe failed", stderr.getvalue())
            self.assertNotIn("widen the filters", stdout.getvalue().lower())

    def test_list_prints_sha256_of_exact_manifest_bytes(self) -> None:
        video = {"id": "fixture001", "title": "Memory", "url": "https://youtube.com/watch?v=fixture001"}
        metadata = {**video, "webpage_url": video["url"], "upload_date": "20260101"}
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            args = fixture_args(limit=1, scan=1, manifest=manifest_path)
            stdout = io.StringIO()
            with (
                mock.patch.object(channel, "enumerate_videos", return_value=[video]),
                mock.patch.object(channel.media, "probe", return_value=metadata),
                contextlib.redirect_stdout(stdout),
            ):
                channel.list_phase(args, "https://www.youtube.com/@example/videos")
            digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            self.assertIn(digest, stdout.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
