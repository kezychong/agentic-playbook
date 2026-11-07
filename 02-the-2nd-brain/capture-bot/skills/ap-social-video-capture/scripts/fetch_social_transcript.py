#!/usr/bin/env python3
"""Create a transcript draft for one public social-video URL.

The default action prints a result. Writing requires both --write and an explicit
--out directory. --dry-run performs no network or account access.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import yt_media as media

PLATFORMS = {
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "douyin": "Douyin",
    "xiaohongshu": "Xiaohongshu",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "twitter": "X",
    "bilibili": "Bilibili",
}


def platform_of(metadata: dict) -> str:
    extractor = metadata.get("extractor") or ""
    for key, label in PLATFORMS.items():
        if key in extractor:
            return label
    return extractor.split(":")[0].title() if extractor else "Web"


def yaml_string(value: object) -> str:
    """Return a JSON-quoted scalar, which is also valid YAML."""
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def build_note(metadata: dict, transcript: dict, platform: str) -> str:
    published = media.iso_date(metadata.get("upload_date"))
    source_url = media.validate_url(str(metadata.get("webpage_url") or ""))
    captured = dt.datetime.now().astimezone().isoformat(timespec="minutes")
    status = "complete" if transcript["text"] else ("partial" if transcript["caveat"] else "blocked")
    text = transcript["text"] or "_(no transcript — see extraction status)_"
    return f"""---
source: {yaml_string(source_url)}
author: {yaml_string(metadata.get('uploader'))}
published: {yaml_string(published)}
captured: {yaml_string(captured)}
content_type: "social-video"
platform: {yaml_string(platform)}
capture_status: {yaml_string(status)}
transcript_method: {yaml_string(transcript['method'])}
---

# {platform}: {metadata.get('title') or '(untitled)'}

**Source:** {source_url}
**Author / channel:** {metadata.get('uploader') or '(unknown)'}
**Published:** {published or '(unknown)'}
**Transcript via:** {transcript['method']} · **Language:** {transcript.get('language') or 'n/a'}

## Draft summary

_(complete after checking the transcript; do not invent missing context)_

## Extraction status

- Transcript available: {"yes" if transcript['text'] else "no"}
- Caveats: {transcript['caveat'] or "none"}

## Full transcript

{text}
"""


def note_filename(metadata: dict, platform: str) -> str:
    published = media.iso_date(metadata.get("upload_date")) or dt.date.today().isoformat()
    title = media.slugify(metadata.get("title"))
    identity = media.video_identity(metadata)
    return f"{published} - {platform} - {title} - {identity}.md"


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="Capture one public social video as a local transcript draft."
    )
    argument_parser.add_argument("url", help="HTTPS social-video URL on the fixed public-media allowlist.")
    argument_parser.add_argument("--lang", default=None, help="Local Whisper language; default auto.")
    argument_parser.add_argument("--model", default=media.DEFAULT_WHISPER_MODEL)
    argument_parser.add_argument("--sub-langs", default=media.DEFAULT_SUB_LANGS)
    argument_parser.add_argument("--max-seconds", type=int, default=media.DEFAULT_MAX_SECONDS)
    argument_parser.add_argument("--no-whisper", action="store_true", help="Use captions only.")
    argument_parser.add_argument("--json", action="store_true", help="Print structured output.")
    argument_parser.add_argument("--write", action="store_true", help="Write the draft note locally.")
    argument_parser.add_argument(
        "--out",
        type=Path,
        help="Approved, already-existing real output directory; required with --write.",
    )
    argument_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the bounded plan without network access.",
    )
    return argument_parser


def main() -> int:
    args = parser().parse_args()
    try:
        url = media.validate_url(args.url)
        media.validate_max_seconds(args.max_seconds)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.write and args.out is None:
        raise SystemExit("--write requires an explicit --out directory")
    if args.write and (args.out.is_symlink() or not args.out.exists() or not args.out.is_dir()):
        raise SystemExit("--out must be an already-existing real directory (not a symlink)")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "url": url,
                    "network_access": False,
                    "write": args.write,
                    "out": str(args.out) if args.out else None,
                    "caption_languages": args.sub_langs,
                    "local_whisper": not args.no_whisper,
                    "max_seconds": args.max_seconds,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    metadata = media.probe(url)
    platform = platform_of(metadata)
    transcript = media.get_transcript(
        url,
        metadata,
        languages=args.sub_langs,
        whisper_model=args.model,
        allow_whisper=not args.no_whisper,
        language=args.lang,
        max_seconds=args.max_seconds,
    )
    result = {
        "platform": platform,
        "title": metadata.get("title"),
        "author": metadata.get("uploader"),
        "url": metadata.get("webpage_url"),
        "published": media.iso_date(metadata.get("upload_date")),
        "duration_s": metadata.get("duration"),
        **transcript,
    }

    if args.write:
        filename = note_filename(metadata, platform)
        note_path = media.atomic_write_text(
            args.out,
            filename,
            build_note(metadata, transcript, platform),
        )
        result["note"] = str(note_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[{platform}] {metadata.get('title')}")
        print(f"transcript: {transcript['method']} ({len(transcript['text'])} chars)")
        if transcript["caveat"]:
            print(f"caveat: {transcript['caveat']}")
        if result.get("note"):
            print(f"draft note: {result['note']}")
    return 0 if transcript["text"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
