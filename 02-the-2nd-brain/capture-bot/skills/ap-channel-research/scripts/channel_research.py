#!/usr/bin/env python3
"""Build a bounded transcript corpus from an approved channel manifest.

Phase 1 lists and records matching videos. Phase 2 requires that exact manifest,
its approved SHA-256, an explicit approval flag, and an existing output directory. --dry-run performs
no network or account access.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import stat
import sys
import time
from pathlib import Path

SOCIAL_SCRIPTS = Path(__file__).resolve().parents[2] / "ap-social-video-capture" / "scripts"
sys.path.insert(0, str(SOCIAL_SCRIPTS))
import yt_media as media  # noqa: E402  # pyright: ignore[reportMissingImports]

ENUMERATION_TIMEOUT = 180
MAX_SCAN = 500
MAX_VIDEOS = 100
MIN_SLEEP_SECONDS = 1.0
MAX_SLEEP_SECONDS = 60.0
MANIFEST_SCHEMA = 1
MAX_MANIFEST_BYTES = 4 * 1024 * 1024


def resolve_channel(value: str) -> str:
    value = value.strip()
    if value.startswith(("http://", "https://")):
        url = media.validate_url(value).rstrip("/")
        if "youtube.com" in url and not re.search(
            r"/(videos|streams|shorts|playlists)$", url
        ) and "list=" not in url and "watch?" not in url:
            url += "/videos"
        return url
    if not re.fullmatch(r"@?[A-Za-z0-9._-]+", value):
        raise ValueError("a bare channel must be a handle; otherwise provide an HTTP(S) URL")
    handle = value if value.startswith("@") else f"@{value}"
    return f"https://www.youtube.com/{handle}/videos"


def enumerate_videos(channel_url: str, scan: int) -> list[dict]:
    """List a bounded prefix of a public channel without downloading media."""
    media.require_tools()
    result = media._run(
        media.ytdlp_argv(
            "--flat-playlist",
            "-J",
            "--no-warnings",
            "-I",
            f"1:{scan}",
            media.validate_public_resolution(channel_url),
        ),
        ENUMERATION_TIMEOUT,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = media.safe_error_message(
            RuntimeError(result.stderr or "no channel metadata returned")
        )
        raise RuntimeError(f"channel enumeration failed: {detail}")
    data = json.loads(result.stdout)
    output: list[dict] = []
    for entry in data.get("entries") or []:
        if not entry:
            continue
        video_id = entry.get("id")
        url = entry.get("webpage_url") or entry.get("url")
        if url and not str(url).startswith(("http://", "https://")):
            url = None
        if not url and video_id and "youtube.com" in channel_url:
            url = f"https://www.youtube.com/watch?v={video_id}"
        if not url:
            continue
        try:
            url = media.validate_url(url)
        except ValueError:
            continue
        output.append(
            {
                "id": video_id,
                "title": (entry.get("title") or "").strip(),
                "url": url,
            }
        )
    return output


def keyword_match(title: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lowered = title.lower()
    return any(keyword in lowered for keyword in keywords)


def in_date_range(date_value: str, since: str | None, until: str | None) -> bool:
    if not date_value:
        return not (since or until)
    if since and date_value < since:
        return False
    if until and date_value > until:
        return False
    return True


def validate_iso_date(value: str | None, label: str) -> None:
    if value is None:
        return
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must use YYYY-MM-DD") from exc


def validate_bounds(limit: int, scan: int, sleep_seconds: float, max_seconds: int) -> None:
    if not 1 <= limit <= MAX_VIDEOS:
        raise ValueError(f"limit must be between 1 and {MAX_VIDEOS}")
    if not limit <= scan <= MAX_SCAN:
        raise ValueError(f"scan must be between limit ({limit}) and {MAX_SCAN}")
    if not MIN_SLEEP_SECONDS <= sleep_seconds <= MAX_SLEEP_SECONDS:
        raise ValueError(
            f"sleep must be between {MIN_SLEEP_SECONDS:g} and {MAX_SLEEP_SECONDS:g} seconds"
        )
    media.validate_max_seconds(max_seconds)


def build_manifest(channel_url: str, args: argparse.Namespace, videos: list[dict]) -> dict:
    return {
        "schema": MANIFEST_SCHEMA,
        "generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "channel_url": channel_url,
        "filters": {
            "keywords": [value.strip().lower() for value in args.keyword.split(",") if value.strip()],
            "since": args.since,
            "until": args.until,
            "limit": args.limit,
            "scan": args.scan,
        },
        "extraction": {
            "captions_only": args.captions_only,
            "language": args.lang,
            "model": args.model,
            "sub_languages": args.sub_langs,
            "max_seconds": args.max_seconds,
            "sleep_seconds": args.sleep,
        },
        "videos": videos,
    }


def write_manifest(path: Path, manifest: dict) -> str:
    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    media.atomic_write_text(path.parent, path.name, payload)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_manifest(path: Path, *, approved_sha256: str | None = None) -> dict:
    if approved_sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", approved_sha256):
        raise ValueError("approved manifest SHA-256 must be exactly 64 hexadecimal characters")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise ValueError("approved manifest must be a regular non-symlink file")
        if details.st_size > MAX_MANIFEST_BYTES:
            raise ValueError(f"approved manifest exceeds {MAX_MANIFEST_BYTES} bytes")
        chunks: list[bytes] = []
        remaining = MAX_MANIFEST_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > MAX_MANIFEST_BYTES:
            raise ValueError(f"approved manifest exceeds {MAX_MANIFEST_BYTES} bytes")
    finally:
        os.close(descriptor)
    if approved_sha256 is not None:
        actual_sha256 = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(actual_sha256, approved_sha256.lower()):
            raise ValueError("approved manifest SHA-256 does not match the exact supplied bytes")
    data = json.loads(payload.decode("utf-8"))
    if data.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("unsupported manifest schema")
    channel_url = media.validate_url(data.get("channel_url", ""))
    videos = data.get("videos")
    if not isinstance(videos, list) or not 1 <= len(videos) <= MAX_VIDEOS:
        raise ValueError(f"manifest must contain 1 to {MAX_VIDEOS} videos")
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for video in videos:
        if not isinstance(video, dict):
            raise ValueError("manifest video entries must be objects")
        clean_url = media.validate_url(video.get("url", ""))
        video_id = video.get("id")
        if video_id is not None and not isinstance(video_id, str):
            raise ValueError("manifest video IDs must be strings when present")
        if video_id and video_id in seen_ids:
            raise ValueError(f"duplicate manifest video ID: {video_id}")
        if clean_url in seen_urls:
            raise ValueError("duplicate manifest video URL")
        if video_id:
            seen_ids.add(video_id)
        seen_urls.add(clean_url)
        video["url"] = clean_url
    extraction = data.get("extraction") or {}
    filters = data.get("filters") or {}
    validate_bounds(
        int(filters.get("limit", len(videos))),
        int(filters.get("scan", len(videos))),
        float(extraction.get("sleep_seconds", 2.0)),
        int(extraction.get("max_seconds", media.DEFAULT_MAX_SECONDS)),
    )
    data["channel_url"] = channel_url
    return data


def yaml_string(value: object) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def corpus_note(metadata: dict, transcript: dict, channel: str) -> str:
    published = media.iso_date(metadata.get("upload_date"))
    source_url = media.validate_url(str(metadata.get("webpage_url") or ""))
    text = transcript["text"] or "_(no transcript — see caveat)_"
    captured = dt.datetime.now().astimezone().isoformat(timespec="minutes")
    return f"""---
source: {yaml_string(source_url)}
channel: {yaml_string(channel)}
video_id: {yaml_string(metadata.get('id'))}
published: {yaml_string(published)}
captured: {yaml_string(captured)}
content_type: "channel-research"
transcript_method: {yaml_string(transcript['method'])}
capture_status: {yaml_string('complete' if transcript['text'] else 'blocked')}
---

# {metadata.get('title') or '(untitled)'}

**Channel:** {channel}
**Source:** {source_url}
**Published:** {published or '(unknown)'}
**Transcript via:** {transcript['method']} · **Language:** {transcript.get('language') or 'n/a'}
**Caveat:** {transcript['caveat'] or 'none'}

## Transcript

{text}
"""


def write_corpus_note(output_dir: Path, stem: str, text: str) -> Path:
    return media.atomic_write_text(output_dir, f"{stem}.md", text)


def corpus_stem(metadata: dict, published: str) -> str:
    title = media.slugify(str(metadata.get("title") or "untitled"))
    identity = media.video_identity(metadata)
    return f"{published or 'undated'} - {title} - {identity}"


def write_index(
    output_dir: Path,
    channel: str,
    rows: list[dict],
    manifest: Path,
    approved_sha256: str | None = None,
) -> Path:
    lines = [
        f"# Research corpus — {channel}",
        "",
        f"_Generated {dt.datetime.now().astimezone().isoformat(timespec='minutes')}._  ",
        f"_Approved manifest: `{manifest}`_",
        f"_Approved manifest SHA-256: `{approved_sha256 or 'not recorded'}`_",
        "",
        "| Date | Title | Transcript | Chars |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['date'] or '—'} | [[{row['stem']}]] | {row['method']} | {row['chars']} |"
        )
    lines.extend(["", f"**{len(rows)} videos processed.**", ""])
    path = media.atomic_write_text(output_dir, "_INDEX.md", "\n".join(lines))
    return path


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="List a channel, approve the manifest, then build a bounded transcript corpus."
    )
    argument_parser.add_argument("channel", help="Channel URL or YouTube handle.")
    mode = argument_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list-only", action="store_true", help="List matches and write a review manifest.")
    mode.add_argument("--build", action="store_true", help="Build only from an approved manifest.")
    argument_parser.add_argument(
        "--manifest",
        type=Path,
        help="New manifest path inside an already-existing real review directory.",
    )
    argument_parser.add_argument("--approved-manifest", type=Path, help="Reviewed manifest for --build.")
    argument_parser.add_argument("--approved", action="store_true", help="Confirm the listed downloads were approved.")
    argument_parser.add_argument(
        "--approved-sha256",
        help="SHA-256 of the exact approved manifest bytes; required for --build.",
    )
    argument_parser.add_argument(
        "--out",
        type=Path,
        help="Approved, already-existing empty real corpus directory for --build.",
    )
    argument_parser.add_argument("--keyword", default="", help="Comma-separated title filters.")
    argument_parser.add_argument("--since", default=None, help="Inclusive YYYY-MM-DD.")
    argument_parser.add_argument("--until", default=None, help="Inclusive YYYY-MM-DD.")
    argument_parser.add_argument("--limit", type=int, default=25, help=f"Maximum matches (1-{MAX_VIDEOS}).")
    argument_parser.add_argument("--scan", type=int, default=300, help=f"Recent entries to inspect (max {MAX_SCAN}).")
    argument_parser.add_argument("--captions-only", action="store_true", help="Disable local Whisper fallback.")
    argument_parser.add_argument("--lang", default=None, help="Local Whisper language; default auto.")
    argument_parser.add_argument("--model", default=media.DEFAULT_WHISPER_MODEL)
    argument_parser.add_argument("--sub-langs", default=media.DEFAULT_SUB_LANGS)
    argument_parser.add_argument("--max-seconds", type=int, default=media.DEFAULT_MAX_SECONDS)
    argument_parser.add_argument("--sleep", type=float, default=2.0)
    argument_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the plan without network or file writes.",
    )
    return argument_parser


def list_phase(args: argparse.Namespace, channel_url: str) -> int:
    if args.manifest is None:
        raise SystemExit("--list-only requires a new --manifest path")
    keywords = [value.strip().lower() for value in args.keyword.split(",") if value.strip()]
    enumerated = enumerate_videos(channel_url, args.scan)
    candidates = [video for video in enumerated if keyword_match(video["title"], keywords)]
    matched: list[dict] = []
    probe_failures: list[dict] = []
    for video in candidates:
        if len(matched) >= args.limit:
            break
        try:
            metadata = media.probe(video["url"])
        except Exception as exc:
            message = media.safe_error_message(exc)
            failure = {
                "id": video.get("id"),
                "title": video.get("title") or "(untitled)",
                "error": message or type(exc).__name__,
            }
            probe_failures.append(failure)
            print(
                f"Metadata probe failed [{failure['id'] or 'no id'}] {failure['title']}: {failure['error']}",
                file=sys.stderr,
            )
            continue
        published = media.iso_date(metadata.get("upload_date"))
        if not in_date_range(published, args.since, args.until):
            continue
        matched.append(
            {
                "id": metadata.get("id") or video.get("id"),
                "title": metadata.get("title") or video.get("title"),
                "url": metadata.get("webpage_url") or video.get("url"),
                "published": published,
            }
        )
    if not matched:
        if probe_failures:
            print(
                f"No matches could be confirmed because {len(probe_failures)} metadata probe(s) failed; no manifest was written.",
                file=sys.stderr,
            )
            return 2
        print("No matches; widen the filters or scan bound. No manifest was written.")
        return 0
    manifest = build_manifest(channel_url, args, matched)
    if probe_failures:
        manifest["probe_failures"] = probe_failures
    manifest_sha256 = write_manifest(args.manifest, manifest)
    print(f"Channel: {channel_url}")
    for index, video in enumerate(matched, 1):
        print(f"{index:>3}. {video['published'] or '—'}  {video['title']}  [{video['id'] or 'no id'}]")
    print(f"\nReview manifest: {args.manifest}")
    print(f"Approved bytes SHA-256: {manifest_sha256}")
    print("Do not build until the user approves this exact list, extraction plan, and SHA-256.")
    return 0


def build_phase(args: argparse.Namespace, channel_url: str) -> int:
    if not args.approved or args.approved_manifest is None or not args.approved_sha256:
        raise SystemExit("--build requires --approved, --approved-manifest, and --approved-sha256")
    if args.out is None:
        raise SystemExit("--build requires an explicit --out directory")
    manifest = load_manifest(args.approved_manifest, approved_sha256=args.approved_sha256)
    if manifest["channel_url"] != channel_url:
        raise SystemExit("channel argument does not match the approved manifest")
    if args.out.is_symlink() or not args.out.exists() or not args.out.is_dir():
        raise SystemExit("--out must be an already-existing real directory (not a symlink)")
    if any(args.out.iterdir()):
        raise SystemExit(f"refusing non-empty output directory: {args.out}")

    extraction = manifest["extraction"]
    channel_name = re.sub(r"^https?://[^/]+/", "", channel_url).split("/")[0] or channel_url
    rows: list[dict] = []
    for index, approved_video in enumerate(manifest["videos"], 1):
        metadata = media.probe(approved_video["url"])
        if approved_video.get("id") and metadata.get("id") != approved_video["id"]:
            raise RuntimeError(f"video identity changed for {approved_video['url']}")
        transcript = media.get_transcript(
            approved_video["url"],
            metadata,
            languages=extraction["sub_languages"],
            whisper_model=extraction["model"],
            allow_whisper=not extraction["captions_only"],
            language=extraction["language"],
            max_seconds=int(extraction["max_seconds"]),
        )
        published = media.iso_date(metadata.get("upload_date")) or approved_video.get("published") or ""
        stem = corpus_stem(metadata, published)
        write_corpus_note(args.out, stem, corpus_note(metadata, transcript, channel_name))
        rows.append(
            {
                "stem": stem,
                "date": published,
                "method": transcript["method"],
                "chars": len(transcript["text"]),
            }
        )
        print(f"[{index}/{len(manifest['videos'])}] {transcript['method']}: {metadata.get('title')}")
        if index < len(manifest["videos"]):
            time.sleep(float(extraction["sleep_seconds"]))
    index_path = write_index(
        args.out,
        channel_name,
        rows,
        args.approved_manifest,
        args.approved_sha256.lower(),
    )
    print(f"Corpus: {args.out}\nIndex: {index_path}\n{len(rows)} videos processed.")
    return 0


def main() -> int:
    args = parser().parse_args()
    try:
        channel_url = resolve_channel(args.channel)
        validate_iso_date(args.since, "--since")
        validate_iso_date(args.until, "--until")
        validate_bounds(args.limit, args.scan, args.sleep, args.max_seconds)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.since and args.until and args.since > args.until:
        raise SystemExit("--since must not be later than --until")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "mode": "list" if args.list_only else "build",
                    "channel_url": channel_url,
                    "network_access": False,
                    "file_writes": False,
                    "limit": args.limit,
                    "scan": args.scan,
                    "max_seconds": args.max_seconds,
                },
                indent=2,
            )
        )
        return 0
    return list_phase(args, channel_url) if args.list_only else build_phase(args, channel_url)


if __name__ == "__main__":
    raise SystemExit(main())
