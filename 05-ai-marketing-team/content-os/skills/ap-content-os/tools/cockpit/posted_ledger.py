#!/usr/bin/env python3
"""
posted_ledger.py - reads content-os/posted.md, the append-only record of what
the member has actually published.

Standard library only. Read only: nothing in this file ever writes to the
ledger. The ledger has one writer, and it is not the cockpit.

The file may not exist at all. That is the normal state of a workspace on day
one and it is never an error. Every caller gets an empty list and the tabs
that use it say plainly that nothing has been posted yet.

Shape read (heading-structured markdown, no frontmatter):

    ## 2026-08-24 - The thing I stopped doing
    - platform: instagram
    - format: reel
    - link: https://www.instagram.com/reel/ABCdefGHijk/
    - hook: the line that opened it
    - franchise: the recurring series it belongs to
    - stats: views 12400, likes 310, comments 22 (as of 2026-08-25)
    - stats: views 18900, likes 402, comments 31 (as of 2026-09-01)

Everything is optional except the heading. Repeated stats lines are kept in
date order and are the raw material for the resurging check on the Viral tab.
An unknown field name is preserved in `fields` rather than dropped, so a
ledger that grows a new field later still reads cleanly here.

Stats lines are written name first, then the number: `views 12400, likes 310`.
That is the shape `references/templates.md` teaches and the shape the numbers
side of the system writes. A line written the other way round, `12,400 views,
310 likes`, still reads correctly, because the labels are looked for first and
a number is only ever read by its position when the piece it sits in carries
no label at all. A canonical line can never come out with its fields swapped.
"""

import datetime
import re
from pathlib import Path

_ENTRY_HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*[-–—]\s*(.*?)\s*$")
_BULLET_FIELD_RE = re.compile(r"^\s*[-*]\s*([A-Za-z][A-Za-z0-9 _-]{0,30}?)\s*:\s*(.*)$")
_AS_OF_RE = re.compile(r"\(?\s*as of\s+(\d{4}-\d{2}-\d{2})\s*\)?", re.IGNORECASE)

# A stats line is a list of measurements separated by commas. A comma that
# sits inside a number ("12,400") is part of the number, not a separator.
_MEASUREMENT_SPLIT_RE = re.compile(r"[,;](?!\d)")

# Canonical: the name, then the number. "views 4200", "likes: 180".
_LABEL_FIRST_RE = re.compile(
    r"([A-Za-z][A-Za-z \-]{0,28}?)\s*[:=]?\s*([\d][\d,\.]*)\s*([KkMm]?)(?![\d,\.])"
)
# Tolerated fallback: the number, then the name. "4,200 views".
_NUMBER_FIRST_RE = re.compile(
    r"([\d][\d,\.]*)\s*([KkMm]?)\s+([A-Za-z][A-Za-z \-]{0,28}?)(?![A-Za-z])"
)
_SHORTCODE_RE = re.compile(
    r"(?:instagram\.com|youtube\.com|youtu\.be|tiktok\.com)/(?:p|reel|reels|shorts|video|watch)?/?([A-Za-z0-9_-]{6,})"
)
_IG_SHORTCODE_RE = re.compile(r"instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]{5,})")
_URL_RE = re.compile(r"https?://\S+")


_MULTIPLIERS = {"": 1, "k": 1_000, "m": 1_000_000}


def _to_int(raw: str, suffix: str = ""):
    cleaned = (raw or "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return int(value * _MULTIPLIERS.get((suffix or "").lower(), 1))


def _metric_key(label: str) -> str:
    key = (label or "").strip().lower().rstrip(".")
    return re.sub(r"\s+", "_", key)


def _measurements(chunk: str):
    """Every (name, number) pair in one comma-separated piece of a stats line.

    Labels win. Only a piece that carries no name in front of any of its
    numbers is read the other way round, so the two shapes can never be
    mixed up inside the same measurement.
    """
    pairs = []
    for label, number, suffix in _LABEL_FIRST_RE.findall(chunk):
        key = _metric_key(label)
        parsed = _to_int(number, suffix)
        if key and parsed is not None:
            pairs.append((key, parsed))
    if pairs:
        return pairs
    for number, suffix, label in _NUMBER_FIRST_RE.findall(chunk):
        key = _metric_key(label)
        parsed = _to_int(number, suffix)
        if key and parsed is not None:
            pairs.append((key, parsed))
    return pairs


def _parse_stats_line(value: str) -> dict:
    """One stats snapshot. Numbers are pulled by their own label, so the
    order they were written in does not matter and an unlabelled number is
    ignored rather than guessed at."""
    as_of = None
    match = _AS_OF_RE.search(value or "")
    if match:
        try:
            as_of = datetime.date.fromisoformat(match.group(1))
        except ValueError:
            as_of = None
    body = _AS_OF_RE.sub(" ", value or "")
    metrics = {}
    for chunk in _MEASUREMENT_SPLIT_RE.split(body):
        if not chunk.strip():
            continue
        for key, parsed in _measurements(chunk):
            metrics.setdefault(key, parsed)
    return {
        "as_of": as_of.isoformat() if as_of else None,
        "raw": (value or "").strip(),
        "metrics": metrics,
        "views": metrics.get("views") or metrics.get("plays") or metrics.get("impressions"),
        "likes": metrics.get("likes"),
        "comments": metrics.get("comments"),
    }


def _shortcode_from(link: str):
    if not link:
        return None
    match = _IG_SHORTCODE_RE.search(link)
    if match:
        return match.group(1)
    match = _SHORTCODE_RE.search(link)
    return match.group(1) if match else None


def load_entries(path: Path) -> list:
    """Every posted entry, oldest first. Never raises; an absent or damaged
    ledger reads as an empty list."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    entries = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading = _ENTRY_HEADING_RE.match(line)
        if heading:
            try:
                posted_on = datetime.date.fromisoformat(heading.group(1))
            except ValueError:
                current = None
                continue
            current = {
                "date": posted_on.isoformat(),
                "title": heading.group(2).strip(),
                "platform": "",
                "format": "",
                "link": "",
                "hook": "",
                "franchise": "",
                "fields": {},
                "stats": [],
                "shortcode": None,
            }
            entries.append(current)
            continue
        if line.startswith("#"):
            if line.startswith("## "):
                current = None
            continue
        if current is None:
            continue
        field = _BULLET_FIELD_RE.match(line)
        if not field:
            continue
        key = field.group(1).strip().lower().replace(" ", "_")
        value = field.group(2).strip()
        if key == "stats":
            current["stats"].append(_parse_stats_line(value))
        elif key in ("platform", "format", "link", "hook", "franchise"):
            current[key] = value
        else:
            current["fields"][key] = value

    for entry in entries:
        link = entry["link"] or ""
        if not link:
            url = _URL_RE.search(entry["fields"].get("url", "") or "")
            link = url.group(0) if url else ""
            entry["link"] = link
        entry["shortcode"] = _shortcode_from(link)
        entry["stats"].sort(key=lambda snapshot: snapshot["as_of"] or "")
        latest = entry["stats"][-1] if entry["stats"] else None
        entry["latest_stats"] = latest
        entry["views"] = latest["views"] if latest else None
        entry["likes"] = latest["likes"] if latest else None
        entry["comments"] = latest["comments"] if latest else None
        entry["stats_as_of"] = latest["as_of"] if latest else None
    entries.sort(key=lambda item: item["date"])
    return entries


def exact_dates_by_shortcode(entries) -> dict:
    """shortcode -> the date it actually went out, for entries that carry a
    link the cockpit can read a code out of."""
    out = {}
    for entry in entries:
        if entry.get("shortcode"):
            out[entry["shortcode"]] = entry["date"]
    return out


def snapshots_by_shortcode(entries) -> dict:
    """shortcode -> [{date, views}, ...], built from the repeated stats lines.

    This is what lets the Viral tab tell a genuinely resurging post from an
    old winner. A post with one snapshot cannot prove anything yet, and the
    tab says so rather than inventing a trend.
    """
    out = {}
    for entry in entries:
        shortcode = entry.get("shortcode")
        if not shortcode:
            continue
        rows = []
        for snapshot in entry.get("stats", []):
            if snapshot.get("as_of") and snapshot.get("views") is not None:
                rows.append({"date": snapshot["as_of"], "views": snapshot["views"]})
        if rows:
            out[shortcode] = rows[-13:]
    return out


def median_views(entries, last_n: int = 20):
    """The middle view count of the most recent `last_n` posts that carry a
    view number, or None when there are not enough numbers yet."""
    numbers = [entry["views"] for entry in entries if entry.get("views") is not None]
    numbers = numbers[-last_n:]
    if not numbers:
        return None
    ordered = sorted(numbers)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) // 2
