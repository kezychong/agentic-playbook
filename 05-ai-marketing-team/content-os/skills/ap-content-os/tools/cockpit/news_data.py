#!/usr/bin/env python3
"""
news_data.py - how the News tab decides what goes in which time window and
which stories make the page.

Standard library only. Reads one file and returns data; it never fetches
anything and never renders anything.

Every string in the archive is untrusted text pulled off the open internet.
This module sorts and returns it. It never treats a headline as an
instruction, and the page that shows it only ever puts it on screen as text.

The rules that make the windows trustworthy:

- The three windows do not overlap. 24h means the newest day. 3d means older
  than 24 and up to 72 hours. 7d means older than 72 and up to 168 hours.
- A story with a missing, unreadable, future, or too-old date is quarantined,
  never guessed into the newest window.
- Trending searches are separated from articles, because a search term is
  not a story.
- Ranking prefers stories that have both a picture and a summary, then a
  stronger signal, then recency, and rotates across the member's own topics
  so one topic cannot eat the whole page.
"""

import datetime
import json
import re
from pathlib import Path

PAGE_CAP = 30
MAX_AGE_SECONDS = 168 * 3600
HAN_SHARE_THRESHOLD = 0.0
HAN_MIN_COUNT = 1

_HAN_RANGES = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
)


def _parse_iso_dt(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def _han_count(text):
    return sum(
        1
        for char in str(text or "")
        if any(start <= ord(char) <= end for start, end in _HAN_RANGES)
    )


def has_display_han(text):
    """Drop a title that is materially in a script the member did not ask
    for, rather than one stray glyph. Applied after the publisher suffix has
    been stripped, so a publisher name never triggers it."""
    text = str(text or "")
    han = _han_count(text)
    alnum = sum(1 for char in text if char.isalnum())
    return han >= HAN_MIN_COUNT and (han / max(1, alnum)) >= HAN_SHARE_THRESHOLD


def _row_origin(row):
    """The source family a row came from. Rows written by an older run may
    not carry it, so it is worked out from what they do carry. `signal` never
    changes after first capture, which makes it safe to read here."""
    if row.get("origin"):
        return str(row["origin"])
    signal = str(row.get("signal") or "").lower()
    if "trending" in signal and "search" in signal:
        return "trending_searches"
    source = str(row.get("source") or "").lower()
    if source == "trending searches":
        return "trending_searches"
    return "archive_news"


def _item_type(row, origin):
    if row.get("item_type"):
        return str(row["item_type"])
    if origin == "trending_searches":
        return "trend"
    return "news"


def strip_publisher_suffix(title, row):
    """Remove a trailing " - Publisher" only when it matches metadata this
    row already carries. Never a blind trim."""
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    candidates = set()
    for raw in (row.get("source"), row.get("origin")):
        if isinstance(raw, str) and raw:
            normalized = raw.casefold().replace("www.", "")
            candidates.add(normalized)
            candidates.update(part for part in normalized.split(".") if len(part) > 2)
    signal = str(row.get("signal") or "")
    if "·" in signal:
        candidates.add(signal.rsplit("·", 1)[-1].strip().casefold())
    parts = re.split(r"\s+[-–—]\s+", title)
    for index, part in enumerate(parts[1:], start=1):
        if part.strip().casefold() in candidates:
            return " - ".join(parts[:index]).strip()
    return title


def _bucket_for(ref, now_utc):
    if ref is None:
        return None, None
    age_seconds = (now_utc - ref).total_seconds()
    if age_seconds < 0 or age_seconds > MAX_AGE_SECONDS:
        return None, age_seconds
    if age_seconds <= 24 * 3600:
        return "24h", age_seconds
    if age_seconds <= 72 * 3600:
        return "3d", age_seconds
    return "7d", age_seconds


def _signal_strength(row):
    match = re.search(r"[0-9](?:[0-9,]*[0-9])?", str(row.get("signal") or ""))
    if not match:
        return 0
    value = 0
    for char in match.group(0):
        if char != ",":
            value = value * 10 + (ord(char) - ord("0"))
    return value


def _rank_key(row):
    if row.get("image") and row.get("summary"):
        quality_missing = 0
    elif row.get("image") or row.get("summary"):
        quality_missing = 1
    else:
        quality_missing = 2
    return (quality_missing, -_signal_strength(row), float(row.get("age_seconds", 10**12)))


def _round_robin_page(rows, cap=PAGE_CAP):
    by_pillar = {}
    for row in rows:
        by_pillar.setdefault(str(row.get("pillar") or "other"), []).append(row)
    for pool in by_pillar.values():
        pool.sort(key=_rank_key)
    pillars = sorted(by_pillar)
    page = []
    offset = 0
    while len(page) < cap:
        added = False
        for pillar in pillars:
            pool = by_pillar[pillar]
            if offset < len(pool):
                page.append(pool[offset])
                added = True
                if len(page) >= cap:
                    break
        if not added:
            break
        offset += 1
    return page


def empty_payload(updated_at=None):
    return {
        "updated_at": updated_at,
        "items": [],
        "buckets": {"24h": [], "3d": [], "7d": []},
        "trends": [],
        "counts": {
            "archive_total": 0,
            "24h": 0,
            "3d": 0,
            "7d": 0,
            "han_dropped": 0,
            "trends": 0,
            "date_unknown": 0,
            "partition_ok": True,
        },
        "policy": {
            "exclusive_windows": True,
            "page_cap": PAGE_CAP,
            "han_min_count": HAN_MIN_COUNT,
            "han_share_threshold": HAN_SHARE_THRESHOLD,
        },
    }


def build_news_payload(archive_path: Path, now=None):
    try:
        data = json.loads(Path(archive_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return empty_payload()
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return empty_payload()
    now_utc = now or datetime.datetime.now(datetime.timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=datetime.timezone.utc)
    now_utc = now_utc.astimezone(datetime.timezone.utc)

    output = empty_payload(data.get("updated_at"))
    output["counts"]["archive_total"] = len(data["items"])
    regular = {"24h": [], "3d": [], "7d": []}
    trends = []

    for item in data["items"]:
        if not isinstance(item, dict):
            output["counts"]["date_unknown"] += 1
            continue
        row = dict(item)
        ref = _parse_iso_dt(row.get("published")) or _parse_iso_dt(row.get("first_seen"))
        bucket, age_seconds = _bucket_for(ref, now_utc)
        if bucket is None:
            output["counts"]["date_unknown"] += 1
            continue
        row["age_seconds"] = age_seconds
        row["age_hours"] = round(age_seconds / 3600, 2)
        row["bucket"] = bucket
        row["origin"] = _row_origin(row)
        row["item_type"] = _item_type(row, row["origin"])
        row["title"] = strip_publisher_suffix(row.get("title"), row)

        if has_display_han(row["title"]):
            output["counts"]["han_dropped"] += 1
            continue
        if row["item_type"] == "trend":
            output["counts"]["trends"] += 1
            if bucket == "24h":
                trends.append(row)
            continue
        regular[bucket].append(row)
        output["counts"][bucket] += 1

    output["buckets"] = {key: _round_robin_page(rows) for key, rows in regular.items()}
    output["items"] = [row for key in ("24h", "3d", "7d") for row in output["buckets"][key]]
    output["trends"] = sorted(trends, key=_rank_key)[:PAGE_CAP]
    partitioned = sum(
        output["counts"][key]
        for key in ("24h", "3d", "7d", "han_dropped", "trends", "date_unknown")
    )
    output["counts"]["partition_ok"] = partitioned == output["counts"]["archive_total"]
    return output
