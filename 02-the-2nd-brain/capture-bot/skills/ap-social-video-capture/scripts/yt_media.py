#!/usr/bin/env python3
"""Bounded local media helpers for the Capture Bot package.

Metadata and captions are fetched with yt-dlp. Audio is downloaded only when
captions are unavailable and local Whisper is enabled. Commands use argument
lists, temporary files, fixed timeouts, and no browser-cookie or password path.
"""
from __future__ import annotations

import hashlib
import json
import ipaddress
import math
import os
import re
import shutil
import signal
import socket
import stat
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

YTDLP = shutil.which("yt-dlp")
WHISPER = shutil.which("whisper")

YTDLP_ISOLATION_PREFIX = (
    "--ignore-config",
    "--no-plugin-dirs",
    "--no-cookies",
    "--no-cookies-from-browser",
    "--no-cache-dir",
    "--no-exec",
)

PROBE_TIMEOUT = 90
CAPTION_TIMEOUT = 120
AUDIO_TIMEOUT = 600
WHISPER_TIMEOUT = 3600
DEFAULT_MAX_SECONDS = 5400
HARD_MAX_SECONDS = 21600
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_SUB_LANGS = "en.*,zh.*,zh-Hans,zh-Hant,ms,id"
MAX_PROCESS_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_SUBTITLE_BYTES = 16 * 1024 * 1024
MAX_CAPTION_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_TRANSCRIPT_BYTES = 32 * 1024 * 1024
MAX_AUDIO_BYTES = 256 * 1024 * 1024

ALLOWED_MEDIA_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "douyin.com",
    "xiaohongshu.com",
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "bilibili.com",
    "vimeo.com",
)
RESERVED_FIXTURE_HOSTS = {"example.com"}
SECRET_QUERY_KEYS = {
    "apikey",
    "accesstoken",
    "authtoken",
    "authorization",
    "cookie",
    "credential",
    "jwt",
    "key",
    "password",
    "passwd",
    "secret",
    "session",
    "sessionid",
    "sig",
    "signature",
    "token",
}
SECRET_QUERY_SUFFIXES = (
    "authorization",
    "cookie",
    "credential",
    "jwt",
    "password",
    "passwd",
    "secret",
    "session",
    "signature",
    "token",
)
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "igshid", "si"}


def _run(
    cmd: list[str],
    timeout: int,
    *,
    max_output_bytes: int = MAX_PROCESS_OUTPUT_BYTES,
    watch_dir: Path | None = None,
    max_download_bytes: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run without a shell while retaining at most a fixed amount per stream."""
    if max_output_bytes < 1:
        raise ValueError("subprocess output limit must be positive")
    if (watch_dir is None) != (max_download_bytes is None):
        raise ValueError("download monitoring requires both a directory and byte limit")
    if max_download_bytes is not None and max_download_bytes < 1:
        raise ValueError("download size limit must be positive")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=(os.name == "posix"),
    )
    stdout = bytearray()
    stderr = bytearray()
    exceeded = threading.Event()
    download_exceeded = False

    def collect(stream: Any, destination: bytearray) -> None:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            remaining = max_output_bytes - len(destination)
            if remaining > 0:
                destination.extend(chunk[:remaining])
            if len(chunk) > remaining:
                exceeded.set()

    assert process.stdout is not None and process.stderr is not None
    readers = [
        threading.Thread(target=collect, args=(process.stdout, stdout), daemon=True),
        threading.Thread(target=collect, args=(process.stderr, stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()

    def kill_process_tree() -> None:
        if process.poll() is not None:
            return
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()

    deadline = time.monotonic() + timeout
    while process.poll() is None:
        if exceeded.is_set():
            kill_process_tree()
            break
        if watch_dir is not None and max_download_bytes is not None:
            total = 0
            for child in watch_dir.iterdir():
                details = child.lstat()
                if not stat.S_ISREG(details.st_mode):
                    kill_process_tree()
                    download_exceeded = True
                    break
                total += details.st_size
                if total > max_download_bytes:
                    kill_process_tree()
                    download_exceeded = True
                    break
            if download_exceeded:
                break
        if time.monotonic() >= deadline:
            kill_process_tree()
            process.wait()
            for reader in readers:
                reader.join()
            process.stdout.close()
            process.stderr.close()
            raise subprocess.TimeoutExpired(cmd, timeout)
        time.sleep(0.01)
    process.wait()
    for reader in readers:
        reader.join()
    process.stdout.close()
    process.stderr.close()
    if exceeded.is_set():
        raise RuntimeError(f"subprocess output limit exceeded ({max_output_bytes} bytes per stream)")
    if watch_dir is not None and max_download_bytes is not None:
        total = sum(child.lstat().st_size for child in watch_dir.iterdir())
        if download_exceeded or total > max_download_bytes:
            raise RuntimeError(f"download size limit exceeded ({max_download_bytes} bytes)")
    return subprocess.CompletedProcess(
        cmd,
        process.returncode,
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
    )


def require_tools(*, need_whisper: bool = False) -> None:
    if not YTDLP:
        raise RuntimeError("yt-dlp was not found on PATH")
    if need_whisper and not WHISPER:
        raise RuntimeError("the local whisper CLI was not found on PATH")


def ytdlp_argv(*arguments: str) -> list[str]:
    """Build an isolated yt-dlp command before any operation-specific flags."""
    ytdlp = YTDLP
    if not ytdlp:
        raise RuntimeError("yt-dlp was not found on PATH")
    return [ytdlp, *YTDLP_ISOLATION_PREFIX, *arguments]


def validate_url(url: str) -> str:
    """Return a secret-free URL on the fixed public-media host allowlist."""
    value = (url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("URL must use https:// and include an approved public-media host")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not allowed")
    try:
        hostname = (parsed.hostname or "").encode("idna").decode("ascii").lower().rstrip(".")
        port = parsed.port
    except (UnicodeError, ValueError) as exc:
        raise ValueError("URL host or port is invalid") from exc
    if not hostname or port not in {None, 443}:
        raise ValueError("URL must use an approved host without a custom port")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError("literal IP addresses are not allowed")
    allowed = hostname in RESERVED_FIXTURE_HOSTS or any(
        hostname == domain or hostname.endswith(f".{domain}") for domain in ALLOWED_MEDIA_DOMAINS
    )
    if not allowed:
        raise ValueError("URL host is not on the approved public-media allowlist")

    kept_query: list[tuple[str, str]] = []
    for key, item_value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized_key = re.sub(r"[^a-z0-9]", "", key.lower())
        if normalized_key in SECRET_QUERY_KEYS or normalized_key.endswith(SECRET_QUERY_SUFFIXES):
            raise ValueError("URL query contains a secret-bearing parameter")
        if key.lower().startswith("utm_") or normalized_key in TRACKING_QUERY_KEYS:
            continue
        kept_query.append((key, item_value))
    clean_netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunparse(("https", clean_netloc, parsed.path or "/", "", urlencode(kept_query), ""))


def validate_public_resolution(url: str, *, resolver: Any = socket.getaddrinfo) -> str:
    """Fail closed unless the approved hostname currently resolves only globally."""
    clean_url = validate_url(url)
    parsed = urlparse(clean_url)
    try:
        answers = resolver(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("approved media host could not be resolved") from exc
    addresses = {answer[4][0].split("%", 1)[0] for answer in answers if answer[4]}
    if not addresses:
        raise ValueError("approved media host returned no addresses")
    if any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("approved media host resolved to a non-public address")
    return clean_url


def validate_max_seconds(value: int) -> int:
    if value < 1 or value > HARD_MAX_SECONDS:
        raise ValueError(f"max seconds must be between 1 and {HARD_MAX_SECONDS}")
    return value


def _sensitive_assignment_start(message: str) -> int | None:
    """Find the first sensitive assignment in one linear pass."""
    suffixes = (
        "api_key",
        "apikey",
        "secret",
        "token",
        "authorization",
        "cookie",
        "credential",
        "password",
        "passwd",
        "session",
        "session_id",
        "sessionid",
        "signature",
    )
    for separator, character in enumerate(message):
        if character not in "=:":
            continue
        end = separator - 1
        while end >= 0 and message[end].isspace():
            end -= 1
        if end >= 0 and message[end] in "\"'":
            end -= 1
        key_end = end + 1
        while end >= 0:
            candidate = message[end]
            if not (candidate.isascii() and (candidate.isalnum() or candidate in "_-")):
                break
            end -= 1
        key_start = end + 1
        if key_start == key_end:
            continue
        normalized = message[key_start:key_end].lower().replace("-", "_")
        if any(normalized.endswith(suffix) for suffix in suffixes):
            if key_start > 0 and message[key_start - 1] in "\"'":
                key_start -= 1
            return key_start
    return None


def safe_error_message(error: BaseException, *, max_length: int = 200) -> str:
    """Return a bounded diagnostic without URLs or common secret assignments."""
    marker = "[redacted]"
    if max_length < len(marker):
        raise ValueError(f"error message limit must be at least {len(marker)} characters")
    raw = str(error)
    newline = raw.find("\n")
    first_line_end = len(raw) if newline < 0 else newline
    line_was_truncated = first_line_end > MAX_PROCESS_OUTPUT_BYTES
    scan_end = min(first_line_end, MAX_PROCESS_OUTPUT_BYTES)
    message = raw[:scan_end].rstrip("\r")
    assignment_start = _sensitive_assignment_start(message)
    if assignment_start is not None or line_was_truncated:
        safe_prefix_end = len(message) if assignment_start is None else assignment_start
        safe_prefix = re.sub(
            r"https?://\S+",
            "[URL removed]",
            message[:safe_prefix_end],
            flags=re.IGNORECASE,
        )
        return f"{safe_prefix[: max_length - len(marker)]}{marker}"
    message = re.sub(r"https?://\S+", "[URL removed]", message, flags=re.IGNORECASE)
    return (message or type(error).__name__)[:max_length]


def atomic_write_text(output_dir: Path, filename: str, text: str) -> Path:
    """Create one file exclusively beneath an existing, non-symlink directory."""
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise ValueError("output filename must be one plain relative name")
    if output_dir.is_symlink():
        raise ValueError("approved output directory must not be a symbolic link")
    try:
        expected = output_dir.lstat()
        real_dir = output_dir.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("approved output directory must already exist") from exc
    if not stat.S_ISDIR(expected.st_mode):
        raise ValueError("approved output directory is not a directory")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(output_dir, directory_flags)
    actual = os.fstat(directory_fd)
    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
        os.close(directory_fd)
        raise RuntimeError("approved output directory changed during secure open")
    file_fd: int | None = None
    created = False
    try:
        file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(filename, file_flags, 0o600, dir_fd=directory_fd)
        created = True
        with os.fdopen(file_fd, "w", encoding="utf-8", newline="") as handle:
            file_fd = None
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        if file_fd is not None:
            os.close(file_fd)
        if created:
            try:
                os.unlink(filename, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(directory_fd)
    return real_dir / filename


def bounded_read_text(path: Path, *, max_bytes: int) -> str:
    """Read a regular non-symlink file without crossing a byte ceiling."""
    if max_bytes < 1:
        raise ValueError("file size limit must be positive")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise RuntimeError("bounded read requires a regular file")
        if details.st_size > max_bytes:
            raise RuntimeError(f"file size limit exceeded ({max_bytes} bytes)")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > max_bytes:
            raise RuntimeError(f"file size limit exceeded ({max_bytes} bytes)")
        return payload.decode("utf-8", errors="replace")
    finally:
        os.close(descriptor)


def validate_file_size(path: Path, *, max_bytes: int) -> None:
    """Reject non-regular, symlinked, or oversized downloaded files."""
    details = path.lstat()
    if not stat.S_ISREG(details.st_mode):
        raise RuntimeError("downloaded output must be a regular file")
    if details.st_size > max_bytes:
        raise RuntimeError(f"file size limit exceeded ({max_bytes} bytes)")


def probe(url: str) -> dict:
    """Fetch metadata for one video without downloading media."""
    require_tools()
    result = _run(
        ytdlp_argv("-J", "--no-warnings", "--skip-download", validate_public_resolution(url)),
        PROBE_TIMEOUT,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = safe_error_message(RuntimeError(result.stderr or "no metadata returned"))
        raise RuntimeError(f"metadata fetch failed: {detail}")
    data = json.loads(result.stdout)
    canonical_url = validate_url(data.get("webpage_url") or url)
    return {
        "id": data.get("id"),
        "title": (data.get("title") or "").strip() or "(untitled)",
        "uploader": data.get("uploader") or data.get("channel") or data.get("uploader_id"),
        "channel": data.get("channel") or data.get("uploader"),
        "upload_date": data.get("upload_date"),
        "webpage_url": canonical_url,
        "duration": data.get("duration"),
        "extractor": (data.get("extractor_key") or data.get("extractor") or "").lower(),
        "description": (data.get("description") or "").strip(),
    }


def iso_date(yyyymmdd: str | None) -> str:
    if yyyymmdd and re.fullmatch(r"\d{8}", yyyymmdd):
        return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
    return ""


def parse_vtt(text: str) -> str:
    """Convert VTT/SRT text to plain text and collapse duplicate cues."""
    output: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.isdigit() or "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"^\d+:\d\d:\d\d[.,]\d+\s*", "", line)
        if line and (not output or output[-1] != line):
            output.append(line)
    return "\n".join(output).strip()


def fetch_captions(url: str, languages: str, scratch: Path) -> tuple[str, str] | None:
    """Fetch public platform captions without downloading the video."""
    require_tools()
    result = _run(
        ytdlp_argv(
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            languages,
            "--sub-format",
            "vtt/srt/best",
            "--max-filesize",
            str(MAX_SUBTITLE_BYTES),
            "--no-warnings",
            "-o",
            str(scratch / "%(id)s.%(ext)s"),
            validate_public_resolution(url),
        ),
        CAPTION_TIMEOUT,
        watch_dir=scratch,
        max_download_bytes=MAX_CAPTION_DOWNLOAD_BYTES,
    )
    if result.returncode != 0:
        detail = safe_error_message(RuntimeError(result.stderr or "caption command failed"))
        raise RuntimeError(f"caption fetch failed: {detail}")
    subtitle_files = sorted(
        path for path in scratch.iterdir() if path.suffix.lower() in {".vtt", ".srt"}
    )
    if not subtitle_files:
        return None
    text = parse_vtt(bounded_read_text(subtitle_files[0], max_bytes=MAX_SUBTITLE_BYTES))
    match = re.search(r"\.([A-Za-z-]+)\.(vtt|srt)$", subtitle_files[0].name)
    return (text, match.group(1) if match else "und") if text else None


def download_audio(
    url: str,
    scratch: Path,
    *,
    duration: object,
    max_seconds: int,
) -> Path:
    """Download one audio track for local transcription."""
    max_seconds = validate_max_seconds(max_seconds)
    try:
        duration_seconds = float(str(duration))
    except (TypeError, ValueError) as exc:
        raise ValueError("positive finite duration metadata is required before audio download") from exc
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("positive finite duration metadata is required before audio download")
    if duration_seconds > max_seconds:
        raise ValueError(f"duration exceeds the {max_seconds}s audio-download limit")
    require_tools()
    result = _run(
        ytdlp_argv(
            "-f",
            "bestaudio/best",
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--max-filesize",
            str(MAX_AUDIO_BYTES),
            "--no-warnings",
            "-o",
            str(scratch / "%(id)s.%(ext)s"),
            validate_public_resolution(url),
        ),
        AUDIO_TIMEOUT,
        watch_dir=scratch,
        max_download_bytes=MAX_AUDIO_BYTES,
    )
    if result.returncode != 0:
        detail = safe_error_message(RuntimeError(result.stderr or "audio command failed"))
        raise RuntimeError(f"audio download failed: {detail}")
    audio_files = sorted(
        path for path in scratch.iterdir() if path.suffix.lower() in {".mp3", ".m4a", ".wav", ".webm"}
    )
    if not audio_files:
        detail = safe_error_message(RuntimeError(result.stderr or "no audio file returned"))
        raise RuntimeError(f"audio download failed: {detail}")
    validate_file_size(audio_files[0], max_bytes=MAX_AUDIO_BYTES)
    return audio_files[0]


def whisper_transcribe(audio: Path, model: str, language: str | None, scratch: Path) -> str:
    """Transcribe a local audio file with the local Whisper CLI."""
    require_tools(need_whisper=True)
    whisper = WHISPER
    assert whisper is not None
    command = [
        whisper,
        str(audio),
        "--model",
        model,
        "--output_format",
        "txt",
        "--output_dir",
        str(scratch),
        "--fp16",
        "False",
        "--verbose",
        "False",
    ]
    if language and language.lower() not in {"", "auto", "und"}:
        command.extend(["--language", language])
    result = _run(
        command,
        WHISPER_TIMEOUT,
        watch_dir=scratch,
        max_download_bytes=MAX_AUDIO_BYTES + MAX_TRANSCRIPT_BYTES,
    )
    if result.returncode != 0:
        detail = safe_error_message(RuntimeError(result.stderr or "Whisper command failed"))
        raise RuntimeError(f"Whisper transcription failed: {detail}")
    output = scratch / f"{audio.stem}.txt"
    if not output.is_file():
        detail = safe_error_message(RuntimeError(result.stderr or "no transcript file returned"))
        raise RuntimeError(f"Whisper produced no transcript: {detail}")
    return bounded_read_text(output, max_bytes=MAX_TRANSCRIPT_BYTES).strip()


def get_transcript(
    url: str,
    metadata: dict,
    *,
    languages: str = DEFAULT_SUB_LANGS,
    whisper_model: str = DEFAULT_WHISPER_MODEL,
    allow_whisper: bool = True,
    language: str | None = None,
    max_seconds: int = DEFAULT_MAX_SECONDS,
) -> dict:
    """Get captions or a bounded local transcript for one public video."""
    max_seconds = validate_max_seconds(max_seconds)
    with tempfile.TemporaryDirectory(prefix="capture-video-") as directory:
        scratch = Path(directory)
        caption_failure = ""
        try:
            transcript = fetch_captions(url, languages, scratch)
            if transcript:
                return {
                    "method": "captions",
                    "language": transcript[1],
                    "text": transcript[0],
                    "caveat": "",
                }
        except Exception as exc:
            caption_failure = f"Caption extraction failed: {safe_error_message(exc)}"
        raw_duration = metadata.get("duration")
        try:
            duration = float(str(raw_duration))
        except (TypeError, ValueError):
            duration = 0.0
        if not math.isfinite(duration):
            duration = 0.0
        if not allow_whisper:
            return {
                "method": "failed" if caption_failure else "none",
                "language": "",
                "text": "",
                "caveat": (
                    f"{caption_failure}; local Whisper fallback was disabled."
                    if caption_failure
                    else "No captions; local Whisper fallback was disabled."
                ),
            }
        if duration <= 0:
            return {
                "method": "failed" if caption_failure else "none",
                "language": "",
                "text": "",
                "caveat": (
                    f"{caption_failure}; a positive metadata duration is required before audio download."
                    if caption_failure
                    else "No captions; a positive metadata duration is required before audio download."
                ),
            }
        if duration > max_seconds:
            return {
                "method": "failed" if caption_failure else "none",
                "language": "",
                "text": "",
                "caveat": (
                    f"{caption_failure}; clip duration {int(duration)}s exceeds the {max_seconds}s limit."
                    if caption_failure
                    else f"No captions; clip duration {int(duration)}s exceeds the {max_seconds}s limit."
                ),
            }
        try:
            audio = download_audio(
                url,
                scratch,
                duration=duration,
                max_seconds=max_seconds,
            )
            text = whisper_transcribe(audio, whisper_model, language, scratch)
            return {
                "method": f"whisper:{whisper_model}",
                "language": language or "auto",
                "text": text,
                "caveat": caption_failure,
            }
        except Exception as exc:
            transcription_failure = f"Transcription failed: {safe_error_message(exc)}"
            return {
                "method": "failed",
                "language": "",
                "text": "",
                "caveat": (
                    f"{caption_failure}; {transcription_failure}"
                    if caption_failure
                    else transcription_failure
                ),
            }


def slugify(text: object, max_length: int = 60) -> str:
    value = re.sub(r"[^\w\s-]", "", str(text or "").lower(), flags=re.UNICODE)
    value = re.sub(r"[\s_-]+", "-", value).strip("-")
    return (value[:max_length].rstrip("-")) or "untitled"


def video_identity(metadata: dict) -> str:
    """Return a filesystem-safe public video identity, falling back to URL hash."""
    if metadata.get("id"):
        return slugify(metadata["id"], max_length=40)
    clean_url = validate_url(str(metadata.get("webpage_url") or ""))
    return hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:16]
