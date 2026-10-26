#!/usr/bin/env python3
"""
library_data.py - reads the member's decoded-post library.

Standard library only. Read only; nothing here writes anything.

One file per decoded post in content-os/library/, filed as
`YYYY-MM-DD - account-or-mine - mechanism-slug.md`, in the heading-structured
shape the templates define. No frontmatter, and this parser never adds any.

What comes out of each entry:

  title        the mechanism in a few words (the H1)
  creator      the account it came from, or "mine" for the member's own post
  filed        the date it entered the library (freshness; undated is unusable)
  mechanism    the reusable skeleton, one line
  family       the mechanism family: a short repeatable tag, so the same
               machinery filed twice lands in the same pile. Blank on older
               entries filed before that line existed, and blank is fine.
  trust        the evidence rung, in the member's own words
  multiple     how many times over that account's normal it went, when the
               entry recorded the numbers
  link         the post it was decoded from
  shortcode    the code inside that link, when the link carries one

An entry that never recorded numbers is not thrown away and is not promoted
either. It is carried as a reference, labelled as one. That honesty is the
whole point of the evidence rungs.
"""

import datetime
import re
from pathlib import Path

# Filename: 2026-08-24 - someaccount - the-mechanism-slug.md
# The separator is a spaced hyphen, so a hyphen inside an account name or a
# slug never splits the name in the wrong place.
_FNAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+[-–]\s+(.+?)\s+[-–]\s+(.+)$")
# A file saved without the spaces still parses, just less precisely.
_FNAME_LOOSE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[-\s]+(.+)$")
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_H1_PREFIX_RE = re.compile(r"^Library entry\s*[:—-]\s*", re.IGNORECASE)
_FILED_RE = re.compile(r"^\s*Filed\s*:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE | re.IGNORECASE)
# One of the seven lines under the title. Two or three words, lower case,
# joined by underscores, written by whoever decoded the post.
_FAMILY_RE = re.compile(r"^\s*Mechanism family\s*:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_RECHECK_RE = re.compile(r"^\s*Last re-?checked\s*:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE | re.IGNORECASE)
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_FIELD_RE = re.compile(r"^\s*[-*]\s*([A-Za-z][A-Za-z /]{1,40}?)\s*:\s*(.*)$", re.MULTILINE)
_URL_RE = re.compile(r"https?://[^\s)>\]]+")
_IG_SHORTCODE_RE = re.compile(r"instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]{5,})")
_MULTIPLE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:×|x|times)\b", re.IGNORECASE)
_VIEWS_RE = re.compile(r"([\d][\d,]*)\s*(?:views|plays)", re.IGNORECASE)

OWN_ACCOUNT_WORDS = {"mine", "me", "my", "own", "myself", "my-account", "self"}

# The evidence rungs, strongest first. Used as the Library tab's filter so a
# member can pull up only what their own audience has already proved.
TRUST_RUNGS = [
    ("my own results", ("my own result", "my own results", "own results", "my results")),
    ("my own experiment", ("my own experiment", "own experiment", "my experiment")),
    ("someone in my niche", ("in my niche", "my niche", "same niche")),
    ("a nearby niche", ("nearby niche", "adjacent niche", "near niche")),
    ("a general trend", ("general trend", "a trend", "trend")),
    ("a generic list", ("generic list", "a list", "generic")),
]


def _section_text(text: str, wanted: str) -> str:
    """The body under a `## heading` whose name contains `wanted`."""
    wanted = wanted.lower()
    matches = list(_SECTION_RE.finditer(text or ""))
    for index, match in enumerate(matches):
        if wanted in match.group(1).strip().lower():
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


def _first_line(block: str) -> str:
    for raw_line in (block or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(">") or line in ("-", "*"):
            continue
        if line.startswith("- ") or line.startswith("* "):
            line = line[2:].strip()
        if line.startswith("{") and line.endswith("}"):
            continue  # an unfilled template hint, not real content
        if line:
            return line
    return ""


def _bullet_fields(block: str) -> dict:
    out = {}
    for key, value in _FIELD_RE.findall(block or ""):
        out[key.strip().lower()] = value.strip()
    return out


def _trust_label(raw: str) -> str:
    lowered = (raw or "").lower()
    for label, needles in TRUST_RUNGS:
        if any(needle in lowered for needle in needles):
            return label
    return "unrecorded"


def _clean(text: str) -> str:
    text = re.sub(r"[*_`]", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def mechanism_family(text: str) -> str:
    """The mechanism family tag on an entry, tidied into one plain word group.

    An entry filed before that line existed simply has none, and an empty
    answer means the entry sits out of the family filter rather than landing
    in a made-up pile. The template hint in curly braces is not a real answer
    either.
    """
    match = _FAMILY_RE.search(text or "")
    if not match:
        return ""
    raw = match.group(1).strip()
    if not raw or (raw.startswith("{") and raw.endswith("}")):
        return ""
    # Underscores are how the templates teach it, but people type spaces and
    # hyphens too, and the same machinery must land in the same pile either way.
    raw = re.sub(r"[*_`]", " ", raw)
    raw = re.sub(r"[^0-9A-Za-z]+", " ", raw).strip().lower()
    return re.sub(r"\s+", "_", raw)[:40]


def parse_entry(path: Path) -> dict:
    try:
        body = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        body = ""

    stem = path.stem
    name_match = _FNAME_RE.match(stem)
    loose_match = None if name_match else _FNAME_LOOSE_RE.match(stem)
    if name_match:
        date_str, account, slug = name_match.groups()
    elif loose_match:
        date_str, account, slug = loose_match.group(1), "", loose_match.group(2)
    else:
        date_str, account, slug = "", "", stem
    try:
        filename_date = datetime.date.fromisoformat(date_str) if date_str else None
    except ValueError:
        filename_date = None

    filed_match = _FILED_RE.search(body)
    if filed_match:
        try:
            filed = datetime.date.fromisoformat(filed_match.group(1))
        except ValueError:
            filed = filename_date
    else:
        filed = filename_date

    title_match = _H1_RE.search(body)
    title = _H1_PREFIX_RE.sub("", title_match.group(1).strip()).strip() if title_match else ""
    if not title:
        title = slug.replace("-", " ").strip() or stem

    source_block = _section_text(body, "source and trust")
    source_fields = _bullet_fields(source_block)
    account_field = source_fields.get("account and platform") or source_fields.get("account") or ""
    trust_raw = source_fields.get("trust level") or _first_line(source_block)

    creator = (account or "").strip()
    if not creator:
        creator = _clean(account_field).split(",")[0].split(" on ")[0].strip()
    creator = creator or "unknown"
    own = creator.lower() in OWN_ACCOUNT_WORDS or _trust_label(trust_raw).startswith("my own")
    if own:
        creator = "mine"

    stood_out = _section_text(body, "why it stood out")
    mechanism = _first_line(_section_text(body, "the mechanism")) or _first_line(_section_text(body, "mechanism"))
    opening = _first_line(_section_text(body, "opening line"))
    curiosity = _first_line(_section_text(body, "curiosity gap"))
    proof = _first_line(_section_text(body, "proof device"))
    fmt = _first_line(_section_text(body, "format"))
    ask = _first_line(_section_text(body, "ask at the end"))

    multiple = None
    numbers_source = " ".join([stood_out, source_block, body[:4000]])
    multiple_match = _MULTIPLE_RE.search(stood_out) or _MULTIPLE_RE.search(numbers_source)
    if multiple_match:
        try:
            multiple = float(multiple_match.group(1))
        except ValueError:
            multiple = None

    views = None
    views_match = _VIEWS_RE.search(stood_out) or _VIEWS_RE.search(numbers_source)
    if views_match:
        try:
            views = int(views_match.group(1).replace(",", ""))
        except ValueError:
            views = None

    url_match = _URL_RE.search(body)
    link = url_match.group(0).rstrip(".,);") if url_match else None
    shortcode_match = _IG_SHORTCODE_RE.search(body)
    shortcode = shortcode_match.group(1) if shortcode_match else None

    trust = _trust_label(trust_raw)
    return {
        "path": path,
        "title": _clean(title),
        "creator": creator,
        "own": own,
        "filed": filed.isoformat() if filed else None,
        "rechecked": (_RECHECK_RE.search(body).group(1) if _RECHECK_RE.search(body) else None),
        "mechanism": _clean(mechanism),
        "mechanism_family": mechanism_family(body),
        "opening_line": _clean(opening),
        "curiosity_gap": _clean(curiosity),
        "proof_device": _clean(proof),
        "format": _clean(fmt),
        "ask": _clean(ask),
        "stood_out": _clean(stood_out)[:400],
        "trust": trust,
        "trust_raw": _clean(trust_raw),
        "multiple": multiple,
        "views": views,
        "link": link,
        "shortcode": shortcode,
        "slug": slug,
    }


def load_entries(library_dir: Path) -> list:
    """Every entry in the library folder, newest filing first. Sub-folders
    beginning with an underscore (retired, superseded) stay invisible, and a
    missing library folder reads as an empty list."""
    if not library_dir or not Path(library_dir).is_dir():
        return []
    out = []
    for path in sorted(Path(library_dir).glob("*.md")):
        if path.name.startswith("_") or path.name.upper().startswith(("README", "INDEX")):
            continue
        out.append(parse_entry(path))
    out.sort(key=lambda entry: entry["filed"] or "", reverse=True)
    return out


def featured_entry(entries, reference_date: datetime.date):
    """The mechanism of the day: rotated by date across the strongest recent
    entries, so the same one does not sit there all week. Recent means filed
    in the last thirty days; when nothing is that recent, the whole library
    is the pool. Returns None for an empty library."""
    if not entries:
        return None
    recent = []
    for entry in entries:
        if not entry["filed"]:
            continue
        try:
            filed = datetime.date.fromisoformat(entry["filed"])
        except ValueError:
            continue
        if abs((reference_date - filed).days) <= 30:
            recent.append(entry)
    pool = recent or list(entries)
    pool = sorted(pool, key=lambda e: (e["multiple"] is None, -(e["multiple"] or 0)))
    top = pool[:15]
    if not top:
        return None
    return top[reference_date.toordinal() % len(top)]


def watchlist_account_count(watchlist_text: str) -> int:
    """How many accounts the member listed in their watchlist file. The table
    in the template ships with empty rows; those never count."""
    count = 0
    for raw_line in (watchlist_text or "").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.count("|") < 3:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        first = cells[0].lower()
        if first in ("account", "date") or set(first) <= set("-: "):
            continue
        count += 1
    return count
