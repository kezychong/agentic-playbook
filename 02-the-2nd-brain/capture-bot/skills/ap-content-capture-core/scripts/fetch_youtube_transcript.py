#!/usr/bin/env python3
"""Fetch a YouTube transcript as JSON or plain text.

Usage:
  python3 scripts/fetch_youtube_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
  python3 scripts/fetch_youtube_transcript.py "URL" --text-only --timestamps
  python3 scripts/fetch_youtube_transcript.py "URL" --language en,es
"""
import argparse
import json
import re
import sys
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if "youtu.be" in host:
        return path.split("/")[0]
    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        if qs.get("v"):
            return qs["v"][0]
        parts = path.split("/")
        for marker in ("shorts", "embed", "live"):
            if marker in parts:
                i = parts.index(marker)
                if i + 1 < len(parts):
                    return parts[i + 1]
    raise SystemExit(f"Could not extract YouTube video ID from: {value}")


def fetch_transcript(video_id: str, languages: list) -> list:
    """Work with old and new youtube-transcript-api versions.

    Newer versions removed get_transcript(); they use fetch() on an instance.
    """
    if hasattr(YouTubeTranscriptApi, "fetch"):
        return YouTubeTranscriptApi().fetch(video_id, languages=languages).to_raw_data()
    return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url_or_id")
    parser.add_argument("--language", default="en", help="Comma-separated language fallback list, e.g. en,es")
    parser.add_argument("--text-only", action="store_true")
    parser.add_argument("--timestamps", action="store_true")
    args = parser.parse_args()

    video_id = extract_video_id(args.url_or_id)
    languages = [x.strip() for x in args.language.split(",") if x.strip()]

    try:
        transcript = fetch_transcript(video_id, languages)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.text_only:
        for item in transcript:
            text = " ".join(item.get("text", "").split())
            if args.timestamps:
                seconds = int(item.get("start", 0))
                print(f"[{seconds//60:02d}:{seconds%60:02d}] {text}")
            else:
                print(text)
        return 0

    print(json.dumps({"video_id": video_id, "transcript": transcript}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
