#!/usr/bin/env python3
"""Deterministic offline regression tests for social-video capture."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fetch_social_transcript as capture  # noqa: E402
import yt_media as media  # noqa: E402


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


def assert_isolated_ytdlp(test: unittest.TestCase, command: list[str], first_argument: str) -> None:
    test.assertEqual(command[0], "yt-dlp")
    test.assertEqual(command[1 : 1 + len(YTDLP_ISOLATION_PREFIX)], YTDLP_ISOLATION_PREFIX)
    test.assertEqual(command[1 + len(YTDLP_ISOLATION_PREFIX)], first_argument)
    test.assertTrue(YTDLP_OVERRIDE_FLAGS.isdisjoint(command))


class YtDlpIsolationTests(unittest.TestCase):
    def test_metadata_probe_uses_fail_closed_yt_dlp_prefix(self) -> None:
        payload = '{"id":"fixture","title":"Fixture","webpage_url":"https://youtube.com/watch?v=fixture","duration":10}'
        completed = subprocess.CompletedProcess([], 0, payload, "")
        with (
            mock.patch.object(media, "YTDLP", "yt-dlp"),
            mock.patch.object(media, "require_tools"),
            mock.patch.object(media, "validate_public_resolution", return_value="https://youtube.com/watch?v=fixture"),
            mock.patch.object(media, "_run", return_value=completed) as runner,
        ):
            media.probe("https://youtube.com/watch?v=fixture")
        command = runner.call_args.args[0]
        assert_isolated_ytdlp(self, command, "-J")

    def test_caption_fetch_uses_fail_closed_yt_dlp_prefix(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "", "")
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "validate_public_resolution", return_value="https://youtube.com/watch?v=fixture"),
                mock.patch.object(media, "_run", return_value=completed) as runner,
            ):
                self.assertIsNone(media.fetch_captions("https://youtube.com/watch?v=fixture", "en", Path(directory)))
        command = runner.call_args.args[0]
        assert_isolated_ytdlp(self, command, "--skip-download")

    def test_audio_download_uses_fail_closed_yt_dlp_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)

            def successful_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                (scratch / "fixture.mp3").write_bytes(b"audio")
                return subprocess.CompletedProcess([], 0, "", "")

            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "validate_public_resolution", return_value="https://youtube.com/watch?v=fixture"),
                mock.patch.object(media, "_run", side_effect=successful_run) as runner,
            ):
                media.download_audio(
                    "https://youtube.com/watch?v=fixture",
                    scratch,
                    duration=10,
                    max_seconds=300,
                )
        command = runner.call_args.args[0]
        assert_isolated_ytdlp(self, command, "-f")


class UrlValidationTests(unittest.TestCase):
    def test_accepts_reserved_public_fixture_url(self) -> None:
        self.assertEqual(
            media.validate_url("https://example.com/video/123"),
            "https://example.com/video/123",
        )

    def test_rejects_non_public_literal_and_internal_hosts(self) -> None:
        invalid = (
            "https://localhost/video",
            "https://127.0.0.1/video",
            "https://[::1]/video",
            "https://169.254.169.254/latest/meta-data",
            "https://10.0.0.1/video",
            "https://service.internal/video",
            "https://printer.local/video",
        )
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValueError):
                media.validate_url(url)

    def test_rejects_secret_bearing_query_keys(self) -> None:
        for key in ("token", "access_token", "api_key", "password", "cookie", "signature"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                media.validate_url(f"https://example.com/video?{key}=secret")

    def test_rejects_host_when_dns_returns_non_global_address(self) -> None:
        def private_resolution(
            *_args: object, **_kwargs: object
        ) -> list[tuple[object, object, object, object, tuple[str, int]]]:
            return [(None, None, None, None, ("192.168.1.20", 443))]

        with self.assertRaises(ValueError):
            media.validate_public_resolution("https://youtube.com/watch?v=fixture", resolver=private_resolution)

    def test_probe_rejects_secret_bearing_canonical_url(self) -> None:
        payload = '{"id":"fixture","title":"Fixture","webpage_url":"https://youtube.com/watch?v=fixture&token=secret","duration":10}'
        completed = subprocess.CompletedProcess([], 0, payload, "")
        with (
            mock.patch.object(media, "YTDLP", "yt-dlp"),
            mock.patch.object(media, "require_tools"),
            mock.patch.object(media, "validate_public_resolution", return_value="https://youtube.com/watch?v=fixture") as dns_check,
            mock.patch.object(media, "_run", return_value=completed),
            self.assertRaises(ValueError),
        ):
            media.probe("https://youtube.com/watch?v=fixture")
        dns_check.assert_called_once()

    def test_caption_fetch_preflights_dns(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "", "")
        with tempfile.TemporaryDirectory() as directory:
            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "validate_public_resolution", return_value="https://youtube.com/watch?v=fixture") as dns_check,
                mock.patch.object(media, "_run", return_value=completed),
            ):
                self.assertIsNone(media.fetch_captions("https://youtube.com/watch?v=fixture", "en", Path(directory)))
        dns_check.assert_called_once()


class ExistingBehaviorTests(unittest.TestCase):
    def test_parses_vtt_and_collapses_duplicate_cues(self) -> None:
        fixture = (
            "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello <c>world</c>\n\n"
            "00:00:02.000 --> 00:00:03.000\nHello world\n"
        )
        self.assertEqual(media.parse_vtt(fixture), "Hello world")

    def test_formats_dates_and_slugs(self) -> None:
        self.assertEqual(media.iso_date("20261107"), "2026-11-07")
        self.assertEqual(media.slugify("A/B: Test!"), "ab-test")

    def test_builds_fixture_note(self) -> None:
        note = capture.build_note(
            {
                "title": "Fixture clip",
                "uploader": "Example Creator",
                "upload_date": "20261107",
                "webpage_url": "https://example.com/video/123",
            },
            {"method": "captions", "language": "en", "text": "Fixture words.", "caveat": ""},
            "Web",
        )
        self.assertIn("Fixture words.", note)
        self.assertIn("https://example.com/video/123", note)

    def test_note_builder_rejects_secret_bearing_source_url(self) -> None:
        metadata = {
            "title": "Fixture",
            "webpage_url": "https://example.com/video?token=secret",
        }
        transcript = {"method": "none", "language": "", "text": "", "caveat": "missing"}
        with self.assertRaises(ValueError):
            capture.build_note(metadata, transcript, "Web")

    def test_dry_run_is_offline(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HERE / "fetch_social_transcript.py"), "https://example.com/video/123", "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"network_access": false', result.stdout)


class TranscriptBoundTests(unittest.TestCase):
    def test_caption_failure_is_reported_when_whisper_is_disabled(self) -> None:
        with mock.patch.object(
            media,
            "fetch_captions",
            side_effect=RuntimeError("caption request failed https://example.com/private api_key=caption-secret"),
        ):
            result = media.get_transcript(
                "https://example.com/video/123",
                {"duration": 10},
                allow_whisper=False,
            )
        self.assertEqual(result["method"], "failed")
        self.assertIn("Caption extraction failed", result["caveat"])
        self.assertIn("Whisper fallback was disabled", result["caveat"])
        self.assertNotIn("https://", result["caveat"])
        self.assertNotIn("caption-secret", result["caveat"])

    def test_caption_and_whisper_failures_are_both_reported(self) -> None:
        with (
            mock.patch.object(
                media,
                "fetch_captions",
                side_effect=RuntimeError("caption request failed access_token=caption-secret"),
            ),
            mock.patch.object(
                media,
                "download_audio",
                side_effect=RuntimeError("audio request failed auth_token=audio-secret"),
            ),
        ):
            result = media.get_transcript(
                "https://example.com/video/123",
                {"duration": 10},
            )
        self.assertEqual(result["method"], "failed")
        self.assertIn("Caption extraction failed", result["caveat"])
        self.assertIn("Transcription failed", result["caveat"])
        self.assertNotIn("caption-secret", result["caveat"])
        self.assertNotIn("audio-secret", result["caveat"])

    def test_successful_whisper_fallback_preserves_caption_failure_caveat(self) -> None:
        with (
            mock.patch.object(
                media,
                "fetch_captions",
                side_effect=RuntimeError("caption request failed session_id=caption-secret"),
            ),
            mock.patch.object(media, "download_audio", return_value=Path("fixture.mp3")),
            mock.patch.object(media, "whisper_transcribe", return_value="Recovered locally."),
        ):
            result = media.get_transcript(
                "https://example.com/video/123",
                {"duration": 10},
            )
        self.assertEqual(result["method"], "whisper:base")
        self.assertEqual(result["text"], "Recovered locally.")
        self.assertIn("Caption extraction failed", result["caveat"])
        self.assertNotIn("caption-secret", result["caveat"])

    def test_safe_error_message_redacts_authorization_scheme_values(self) -> None:
        cases = (
            ("Authorization", "Bearer", "bearer-secret"),
            ("Authorization", "Basic", "basic-secret"),
            ("proxy_authorization", "Bearer", "proxy-secret"),
        )
        for key, scheme, secret in cases:
            with self.subTest(key=key, scheme=scheme):
                message = media.safe_error_message(
                    RuntimeError(f"request failed; {key}: {scheme} {secret} retry refused")
                )
                self.assertNotIn(secret, message)
                self.assertNotIn(scheme, message)
                self.assertIn("[redacted]", message)

    def test_safe_error_message_redacts_secret_key_variants_and_stays_bounded(self) -> None:
        variants = (
            "api_key",
            "apikey",
            "access_token",
            "auth_token",
            "session_id",
            "sessionid",
            "client-secret",
            "client_secret",
            "refresh_token",
            "id_token",
            "x_api_key",
        )
        for key in variants:
            secret = f"hostile-{key}-value"
            with self.subTest(key=key):
                message = media.safe_error_message(
                    RuntimeError(f"failure {key}={secret} " + ("x" * 500)),
                    max_length=96,
                )
                self.assertNotIn(secret, message)
                self.assertIn("[redacted]", message)
                self.assertLessEqual(len(message), 96)

    def test_safe_error_message_redacts_quoted_keys_and_malformed_values(self) -> None:
        secret_key = "client_" + "secret"
        authorization_key = "proxy_" + "authorization"
        long_secret_key = ("x" * 100) + "_" + "secret"
        cases = (
            (f'failure "{secret_key}": "alpha beta gamma" retry refused', ("alpha", "beta", "gamma")),
            (f"failure '{secret_key}': 'delta epsilon' retry refused", ("delta", "epsilon")),
            (f'failure "{authorization_key}": "Bearer zeta-value" retry refused', ("Bearer", "zeta-value")),
            (f'failure "{secret_key}": "eta \\"theta\\" iota" retry refused', ("eta", "theta", "iota")),
            (f'failure "{secret_key}": "kappa lambda', ("kappa", "lambda")),
            (f'failure "{long_secret_key}": "omicron-value"', ("omicron-value",)),
        )
        for diagnostic, fragments in cases:
            with self.subTest(diagnostic=diagnostic):
                message = media.safe_error_message(RuntimeError(diagnostic))
                for fragment in fragments:
                    self.assertNotIn(fragment, message)
                self.assertIn("[redacted]", message)

    def test_quoted_key_secret_does_not_reach_transcript_caveat(self) -> None:
        key = "client_" + "secret"
        with mock.patch.object(
            media,
            "fetch_captions",
            side_effect=RuntimeError(f'caption failure "{key}": "mu nu"'),
        ):
            result = media.get_transcript(
                "https://example.com/video/123",
                {"duration": 10},
                allow_whisper=False,
            )
        self.assertEqual(result["method"], "failed")
        self.assertNotIn("mu", result["caveat"])
        self.assertNotIn("nu", result["caveat"])
        self.assertIn("[redacted]", result["caveat"])

    def test_safe_error_message_reserves_room_for_marker_after_long_key(self) -> None:
        key = ("x" * 100_000) + "_" + "secret"
        sensitive_sample = "boundary-value"
        message = media.safe_error_message(
            RuntimeError(f"safe prefix {key}={sensitive_sample}"),
            max_length=64,
        )
        self.assertNotIn(sensitive_sample, message)
        self.assertTrue(message.endswith("[redacted]"), message)
        self.assertLessEqual(len(message), 64)

    def test_safe_error_message_marks_lines_truncated_before_assignment(self) -> None:
        key = ("x" * media.MAX_PROCESS_OUTPUT_BYTES) + "_secret"
        sensitive_sample = "edge-value"
        diagnostic = f"{key}={sensitive_sample}"
        for max_length in (10, 64, 200, media.MAX_PROCESS_OUTPUT_BYTES + 128):
            with self.subTest(max_length=max_length):
                message = media.safe_error_message(
                    RuntimeError(diagnostic),
                    max_length=max_length,
                )
                self.assertNotIn(sensitive_sample, message)
                self.assertTrue(message.endswith("[redacted]"))
                self.assertLessEqual(len(message), max_length)

    def test_safe_error_message_handles_large_nonmatching_input_linearly(self) -> None:
        diagnostic = ("-" * 10_000) + " harmless"
        started = time.monotonic()
        message = media.safe_error_message(RuntimeError(diagnostic))
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 1.0)
        self.assertLessEqual(len(message), 200)

    def test_subprocess_output_is_bounded(self) -> None:
        command = [sys.executable, "-c", "import sys; sys.stdout.write('x' * 8192)"]
        with self.assertRaisesRegex(RuntimeError, "output limit"):
            media._run(command, timeout=10, max_output_bytes=1024)

    def test_subprocess_download_directory_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; import sys, time; Path(sys.argv[1]).write_bytes(b'x' * 8192); time.sleep(1)",
                str(output / "media.bin"),
            ]
            with self.assertRaisesRegex(RuntimeError, "download size limit"):
                media._run(command, timeout=10, watch_dir=output, max_download_bytes=1024)

    def test_bounded_text_read_rejects_oversized_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.txt"
            path.write_bytes(b"x" * 1025)
            with self.assertRaisesRegex(RuntimeError, "size limit"):
                media.bounded_read_text(path, max_bytes=1024)

    def test_caption_fetch_rejects_partial_output_from_failed_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)

            def failed_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                (scratch / "fixture.en.vtt").write_text("WEBVTT\n\npartial secret text", encoding="utf-8")
                return subprocess.CompletedProcess(
                    [],
                    1,
                    "",
                    "failed https://captions.example/private Authorization: Bearer bearer-secret",
                )

            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "_run", side_effect=failed_run),
                self.assertRaises(RuntimeError) as raised,
            ):
                media.fetch_captions("https://example.com/video/123", "en", scratch)
        message = str(raised.exception)
        self.assertNotIn("https://", message)
        self.assertNotIn("bearer-secret", message)
        self.assertIn("[redacted]", message)

    def test_caption_reader_rejects_oversized_subtitle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)

            def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                (scratch / "fixture.en.vtt").write_bytes(b"x" * 1025)
                return subprocess.CompletedProcess([], 0, "", "")

            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "_run", side_effect=fake_run),
                mock.patch.object(media, "MAX_SUBTITLE_BYTES", 1024),
                self.assertRaisesRegex(RuntimeError, "size limit"),
            ):
                media.fetch_captions("https://example.com/video/123", "en", scratch)

    def test_audio_download_rejects_partial_output_from_failed_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)

            def failed_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                (scratch / "fixture.mp3").write_bytes(b"partial audio")
                return subprocess.CompletedProcess(
                    [],
                    1,
                    "",
                    "failed https://audio.example/private access_token=audio-secret",
                )

            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "_run", side_effect=failed_run),
                self.assertRaises(RuntimeError) as raised,
            ):
                media.download_audio(
                    "https://example.com/video/123",
                    scratch,
                    duration=10,
                    max_seconds=300,
                )
        message = str(raised.exception)
        self.assertNotIn("https://", message)
        self.assertNotIn("audio-secret", message)
        self.assertIn("[redacted]", message)

    def test_audio_download_requires_positive_bounded_duration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(media, "_run") as runner:
                for duration in (None, 0, 301):
                    with self.subTest(duration=duration), self.assertRaises(ValueError):
                        media.download_audio(
                            "https://example.com/video/123",
                            Path(directory),
                            duration=duration,
                            max_seconds=300,
                        )
                runner.assert_not_called()

    def test_audio_download_rejects_oversized_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)

            def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                (scratch / "fixture.mp3").write_bytes(b"x" * 1025)
                return subprocess.CompletedProcess([], 0, "", "")

            with (
                mock.patch.object(media, "YTDLP", "yt-dlp"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "_run", side_effect=fake_run),
                mock.patch.object(media, "MAX_AUDIO_BYTES", 1024),
                self.assertRaisesRegex(RuntimeError, "size limit"),
            ):
                media.download_audio(
                    "https://example.com/video/123",
                    scratch,
                    duration=10,
                    max_seconds=300,
                )

    def test_whisper_rejects_partial_output_from_failed_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scratch = Path(directory)
            audio = scratch / "fixture.mp3"
            audio.write_bytes(b"audio")

            def failed_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
                (scratch / "fixture.txt").write_text("partial transcript", encoding="utf-8")
                return subprocess.CompletedProcess(
                    [],
                    1,
                    "",
                    "failed https://whisper.example/private auth_token=whisper-secret",
                )

            with (
                mock.patch.object(media, "WHISPER", "whisper"),
                mock.patch.object(media, "require_tools"),
                mock.patch.object(media, "_run", side_effect=failed_run),
                self.assertRaises(RuntimeError) as raised,
            ):
                media.whisper_transcribe(audio, "base", None, scratch)
        message = str(raised.exception)
        self.assertNotIn("https://", message)
        self.assertNotIn("whisper-secret", message)
        self.assertIn("[redacted]", message)

    def test_youtube_metadata_uses_bounded_captions_without_transcript_package(self) -> None:
        package_called = False

        class InstalledTranscriptApi:
            @staticmethod
            def get_transcript(*_args: object, **_kwargs: object) -> list[dict[str, str]]:
                nonlocal package_called
                package_called = True
                return [{"text": "unbounded package transcript"}]

        installed_package = types.ModuleType("youtube_transcript_api")
        installed_package.YouTubeTranscriptApi = InstalledTranscriptApi  # type: ignore[attr-defined]
        metadata = {"id": "fixture", "extractor": "youtube", "duration": 10}
        with (
            mock.patch.dict(sys.modules, {"youtube_transcript_api": installed_package}),
            mock.patch.object(media, "fetch_captions", return_value=("bounded captions", "en")) as captions,
        ):
            result = media.get_transcript("https://youtube.com/watch?v=fixture", metadata)
        self.assertFalse(package_called)
        captions.assert_called_once()
        self.assertEqual(result["method"], "captions")
        self.assertEqual(result["text"], "bounded captions")

    def test_missing_duration_blocks_audio_download(self) -> None:
        for duration in (None, 0, "nan"):
            with self.subTest(duration=duration):
                metadata = {"id": "fixture", "extractor": "web", "duration": duration}
                with (
                    mock.patch.object(media, "fetch_captions", return_value=None),
                    mock.patch.object(media, "download_audio") as download,
                ):
                    result = media.get_transcript("https://example.com/video/123", metadata)
                download.assert_not_called()
                self.assertEqual(result["method"], "none")
                self.assertIn("duration", result["caveat"].lower())

    def test_failure_caveat_does_not_leak_urls_or_secret_values(self) -> None:
        metadata = {"id": "fixture", "extractor": "web", "duration": 10}
        failure = RuntimeError("download failed https://cdn.example/file?token=topsecret")
        with (
            mock.patch.object(media, "fetch_captions", return_value=None),
            mock.patch.object(media, "download_audio", side_effect=failure),
        ):
            result = media.get_transcript("https://example.com/video/123", metadata)
        self.assertNotIn("https://", result["caveat"])
        self.assertNotIn("topsecret", result["caveat"])
        self.assertIn("failed", result["caveat"].lower())


class SafeWriteTests(unittest.TestCase):
    def test_atomic_write_refuses_dangling_target_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "approved"
            root.mkdir()
            escaped = Path(directory) / "escaped.md"
            (root / "note.md").symlink_to(escaped)
            with self.assertRaises(FileExistsError):
                media.atomic_write_text(root, "note.md", "private")
            self.assertTrue((root / "note.md").is_symlink())
            self.assertFalse(escaped.exists())

    def test_cli_write_does_not_follow_dangling_note_symlink(self) -> None:
        metadata = {
            "id": "fixture-id",
            "title": "Fixture",
            "uploader": "Creator",
            "upload_date": "20261107",
            "webpage_url": "https://example.com/video/123",
            "extractor": "web",
            "duration": 10,
        }
        transcript = {"method": "captions", "language": "en", "text": "words", "caveat": ""}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "approved"
            root.mkdir()
            escaped = Path(directory) / "escaped.md"
            (root / "2026-11-07 - Web - fixture - fixture-id.md").symlink_to(escaped)
            argv = ["fetch_social_transcript.py", "https://example.com/video/123", "--write", "--out", str(root)]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(media, "probe", return_value=metadata),
                mock.patch.object(media, "get_transcript", return_value=transcript),
                self.assertRaises(FileExistsError),
            ):
                capture.main()
            self.assertFalse(escaped.exists())

    def test_note_filename_includes_video_identity(self) -> None:
        first = {"id": "video-A", "title": "Same title", "upload_date": "20261107"}
        second = {"id": "video-B", "title": "Same title", "upload_date": "20261107"}
        self.assertNotEqual(capture.note_filename(first, "Web"), capture.note_filename(second, "Web"))
        self.assertIn("video-a", capture.note_filename(first, "Web"))

    def test_cli_rejects_missing_output_directory_before_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            argv = ["fetch_social_transcript.py", "https://example.com/video/123", "--write", "--out", str(missing)]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(media, "probe") as probe,
                self.assertRaisesRegex(SystemExit, "already-existing"),
            ):
                capture.main()
            probe.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
