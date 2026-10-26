"""Defensive readers for the owner's content-os workspace.

Everything in the workspace is heading-structured markdown written by an agent
during ordinary work, not a database. So every reader here follows three rules:

  1. **Absence is normal.** A missing file returns an empty result, never an
     error. A missing field returns None, never a guess.
  2. **Never invent.** If a number is not written down, it stays None and the
     entry carries an honest flag saying which piece is missing.
  3. **Read, never write.** Nothing in this file changes the workspace.

Pure standard library.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import re
from pathlib import Path
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Closed vocabularies. A value outside these lists becomes "unknown", and an
# "unknown" value never enters pattern maths (same rule as the original).
# ---------------------------------------------------------------------------

UNKNOWN = "unknown"

FORMAT_RULES = (
    ("screen_recording", ("screen record", "screen capture", "screen share", "screenshare")),
    ("text_on_screen", ("text on screen only", "text only", "text card", "no voice", "silent")),
    ("voiceover", ("voiceover", "voice over", "narration", "narrated")),
    ("interview", ("interview", "two people", "guest", "conversation with")),
    ("demonstration", ("demonstration", "demonstrat", "walkthrough", "showing how", "hands on")),
    ("talking_to_camera", ("talking to camera", "talking head", "straight to camera",
                           "piece to camera", "to camera", "selfie")),
)

PROOF_RULES = (
    ("before_after", ("before and after", "before/after", "before after")),
    ("screen_evidence", ("screen recording", "screenshot", "dashboard", "receipt", "invoice")),
    ("client_conversation", ("client conversation", "client message", "message from a client",
                             "testimonial", "review from", "direct message", "email from")),
    ("named_failure", ("failure", "mistake i made", "went wrong", "i lost", "i got it wrong")),
    ("live_demonstration", ("live demonstration", "does it on camera", "shows it working",
                            "demonstrates it")),
    ("result_shown", ("result", "numbers", "revenue", "figures", "the outcome")),
    ("credential", ("years of", "trained", "certified", "worked with", "clients served")),
    ("none_shown", ("no proof", "none", "nothing shown")),
)

CTA_RULES = (
    ("comment_keyword", ("comment the word", "comment ", "type ", "drop a ")),
    ("link_in_bio", ("link in bio", "sign up", "download", "free guide", "join the list",
                     "newsletter", "opt in")),
    ("book_or_buy", ("book a call", "buy", "enrol", "enroll", "join the", "apply", "dm me to work")),
    ("save_it", ("save this", "save it", "bookmark")),
    ("share_it", ("share this", "send this to", "tag someone")),
    ("follow", ("follow", "more like this", "hit follow")),
    ("watch_next", ("watch the next", "part two", "part 2", "next video")),
    ("no_ask", ("no ask", "asks for nothing", "none", "no call to action")),
)

VISUAL_OPEN_RULES = (
    ("result_on_screen", ("result on screen", "a result", "dashboard", "screen showing", "numbers on screen")),
    ("movement_toward_camera", ("walks toward", "moves toward", "movement toward", "steps into")),
    ("unusual_place", ("unusual place", "on site", "in a warehouse", "in the car", "outdoors", "backstage")),
    ("demonstration", ("demonstrat", "doing the thing", "hands", "holding")),
    ("object", ("an object", "holds up", "prop", "product in shot")),
    ("text_card", ("text card", "words on a blank", "title card")),
    ("face", ("a face", "their face", "close up", "head and shoulders", "person talking")),
)

MECHANISM_RULES = (
    ("challenge_belief", ("challenge", "everyone thinks", "you think", "myth", "wrong about",
                          "diagnosis of their own", "believe")),
    ("named_enemy", ("enemy", "blames", "the industry", "gurus", "them versus")),
    ("confession", ("confess", "admits", "i was wrong", "embarrassing", "own mistake")),
    ("curiosity_gap", ("curiosity", "withholds", "does not say", "secret", "nobody tells you")),
    ("proof_first", ("opens with the result", "leads with proof", "shows the outcome first")),
    ("diagnosis", ("diagnos", "symptom", "root cause", "the real reason")),
    ("warning", ("warning", "stop doing", "avoid", "the mistake")),
    ("comparison", ("versus", " vs ", "compares", "instead of")),
    ("story_open", ("story", "the day ", "when i ", "a client came")),
    ("list_promise", ("three things", "five things", "steps", "ways to", "reasons")),
    ("number_claim", ("percent", "%", "out of ten", "in ten", "statistic")),
    ("promise_shortcut", ("faster", "in minutes", "without", "shortcut", "in one day")),
)

OWN_ACCOUNT_SLUGS = {"mine", "me", "my_own", "my_account", "own", "own_account", "myself", "my"}
OWN_TRUST_PREFIXES = ("my own", "own results", "own account", "own experiment")

WORDS_SOURCE_RULES = (
    ("transcript", ("transcript",)),
    ("caption_only", ("caption only", "caption-only", "no transcript", "caption alone")),
    ("description", ("description", "watched it", "what happens on screen")),
)


def _match_rules(text: str, rules: Iterable[tuple[str, tuple[str, ...]]]) -> str:
    lowered = f" {text.lower()} "
    for value, needles in rules:
        for needle in needles:
            if needle in lowered:
                return value
    return UNKNOWN


# ---------------------------------------------------------------------------
# Small parsing helpers
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
NUMBER_RE = re.compile(r"(\d[\d,\.]*)\s*([km])?\b", re.IGNORECASE)
MULTIPLE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*x\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+")


def parse_date(text: Optional[str]) -> Optional[dt.date]:
    if not text:
        return None
    found = DATE_RE.search(text)
    if not found:
        return None
    try:
        return dt.date(int(found.group(1)), int(found.group(2)), int(found.group(3)))
    except ValueError:
        return None


def parse_number(text: Optional[str]) -> Optional[float]:
    """Read the first number in a piece of text. Understands 12,000 / 12k / 1.2m."""
    if not text:
        return None
    found = NUMBER_RE.search(text)
    if not found:
        return None
    raw = found.group(1).replace(",", "")
    if raw.endswith("."):
        raw = raw[:-1]
    try:
        value = float(raw)
    except ValueError:
        return None
    suffix = (found.group(2) or "").lower()
    if suffix == "k":
        value *= 1000
    elif suffix == "m":
        value *= 1000000
    return value


def parse_multiple(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    found = MULTIPLE_RE.search(text)
    if not found:
        return None
    try:
        return float(found.group(1))
    except ValueError:
        return None


def slugify(text: str, limit: int = 40) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return (cleaned[:limit].strip("_") or UNKNOWN)


def stable_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def split_sections(text: str) -> dict[str, str]:
    """Split heading-structured markdown into {heading text: body}. Body of the
    part before the first heading is stored under an empty key."""
    sections: dict[str, list[str]] = {"": []}
    current = ""
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)$", line)
        if heading:
            current = heading.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def inline_fields(text: str) -> dict[str, str]:
    """Read 'Label: value' and '- Label: value' lines into a dict of lowered labels."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*").strip()
        match = re.match(r"^([A-Za-z][A-Za-z0-9 _/'’-]{0,48}):\s*(.*)$", stripped)
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        if key not in fields or (not fields[key] and value):
            fields[key] = value
    return fields


def header_block(text: str) -> str:
    """The lines above the first '## ' heading. Card fields live there."""
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        if re.match(r"^#{2,6}\s+", line):
            break
        kept.append(line)
    return "\n".join(kept)


def find_section(sections: dict[str, str], *needles: str) -> str:
    for heading, body in sections.items():
        for needle in needles:
            if needle in heading:
                return body
    return ""


# ---------------------------------------------------------------------------
# Library entries
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class LibraryEntry:
    path: str
    entry_id: str
    title: str
    filed_on: Optional[dt.date]
    posted_on: Optional[dt.date]
    account: str
    is_own: bool
    family_hint: str
    link: str
    trust_level: str
    account_normal: Optional[float]
    views: Optional[float]
    multiple: Optional[float]
    words_source: str
    first_frame_observed: bool
    flags: tuple[str, ...]
    dimensions: dict[str, str]

    @property
    def observed_on(self) -> Optional[dt.date]:
        """The date this post is placed on the timeline: when it went up if the
        entry records that, otherwise when it was filed."""
        return self.posted_on or self.filed_on


def _account_from_filename(name: str) -> str:
    # "YYYY-MM-DD - account-or-mine - mechanism-slug.md"
    parts = [part.strip() for part in name.rsplit(".", 1)[0].split(" - ")]
    if len(parts) >= 3:
        return parts[1]
    return ""


def read_library_entries(content_os: Path) -> list[LibraryEntry]:
    library = content_os / "library"
    if not library.is_dir():
        return []
    entries: list[LibraryEntry] = []
    for path in sorted(library.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        entries.append(_parse_library_entry(path, text, content_os))
    return entries


def _parse_library_entry(path: Path, text: str, content_os: Path) -> LibraryEntry:
    sections = split_sections(text)
    fields = inline_fields(header_block(text))
    for key, value in inline_fields(find_section(sections, "source and trust", "source")).items():
        fields.setdefault(key, value)
    flags: list[str] = []

    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    filed_on = parse_date(fields.get("filed")) or parse_date(path.name)
    posted_on = parse_date(fields.get("posted")) or parse_date(fields.get("published"))
    if filed_on is None:
        flags.append("undated")

    account = (
        fields.get("account and platform")
        or fields.get("account")
        or _account_from_filename(path.name)
    ).strip()
    account_slug = slugify(account.split(",")[0].lstrip("@") or UNKNOWN, limit=32)
    trust_level = fields.get("trust level", "").strip()
    is_own = account_slug in OWN_ACCOUNT_SLUGS or trust_level.lower().startswith(OWN_TRUST_PREFIXES)

    link_match = URL_RE.search(text)
    link = link_match.group(0).rstrip(").,") if link_match else ""

    account_normal = parse_number(fields.get("account normal") or fields.get("their normal"))
    views = parse_number(fields.get("this post") or fields.get("views"))
    multiple = parse_multiple(fields.get("multiple", ""))
    stood_out = find_section(sections, "why it stood out")
    if multiple is None:
        multiple = parse_multiple(stood_out)
    if multiple is None and views and account_normal:
        multiple = views / account_normal if account_normal > 0 else None
    if multiple is None:
        flags.append("no_multiple_recorded")

    words_source_text = fields.get("words captured", "")
    words_source = _match_rules(words_source_text or text, WORDS_SOURCE_RULES)
    if words_source == "caption_only":
        flags.append("caption_only")

    first_frame_text = fields.get("first frame") or find_section(sections, "first frame")
    lowered_frame = first_frame_text.lower()
    first_frame_observed = bool(first_frame_text) and (
        "watched" in lowered_frame or "observed" in lowered_frame
    )
    if first_frame_text and not first_frame_observed:
        flags.append("visual_not_marked_watched")

    dimensions = {
        "format": _match_rules(
            fields.get("format") or find_section(sections, "format"), FORMAT_RULES
        ),
        "proof": _match_rules(find_section(sections, "proof device", "proof"), PROOF_RULES),
        "cta": _match_rules(find_section(sections, "the ask", "ask at the end", "ask"), CTA_RULES),
        "visual_open": (
            _match_rules(first_frame_text, VISUAL_OPEN_RULES) if first_frame_observed else UNKNOWN
        ),
        "mechanism_class": (
            slugify(fields["mechanism family"], limit=32)
            if fields.get("mechanism family")
            else _match_rules(find_section(sections, "the mechanism", "mechanism"), MECHANISM_RULES)
        ),
    }

    try:
        relative = str(path.relative_to(content_os))
    except ValueError:
        relative = path.name

    return LibraryEntry(
        path=relative,
        entry_id=stable_id(relative),
        title=title or path.stem,
        filed_on=filed_on,
        posted_on=posted_on,
        account=account_slug,
        is_own=is_own,
        family_hint="own" if is_own else "",
        link=link,
        trust_level=trust_level,
        account_normal=account_normal,
        views=views,
        multiple=multiple,
        words_source=words_source,
        first_frame_observed=first_frame_observed,
        flags=tuple(flags),
        dimensions=dimensions,
    )


# ---------------------------------------------------------------------------
# research-state.md
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class AccountBaseline:
    handle: str
    median_views: Optional[float]
    sample_size: Optional[int]
    measured_on: Optional[dt.date]
    last_run: Optional[dt.date]


def _clean_handle(raw: str) -> str:
    return slugify(raw.strip().lstrip("@").split(",")[0], limit=32)


def read_research_state(content_os: Path) -> dict[str, AccountBaseline]:
    path = content_os / "research-state.md"
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    accounts: dict[str, AccountBaseline] = {}
    accounts.update(_research_state_from_table(text))
    for handle, baseline in _research_state_from_blocks(text).items():
        accounts.setdefault(handle, baseline)
    return accounts


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _research_state_from_table(text: str) -> dict[str, AccountBaseline]:
    lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return {}
    header = [cell.lower() for cell in _split_row(lines[0])]

    def column(*needles: str) -> Optional[int]:
        for index, cell in enumerate(header):
            if any(needle in cell for needle in needles):
                return index
        return None

    handle_col = column("handle", "account")
    if handle_col is None:
        return {}
    median_col = column("median", "normal")
    sample_col = column("sample")
    measured_col = column("measured", "baseline")
    run_col = column("last run", "last pull", "last checked")

    accounts: dict[str, AccountBaseline] = {}
    for line in lines[2:]:
        cells = _split_row(line)
        if len(cells) <= handle_col or not cells[handle_col]:
            continue
        handle = _clean_handle(cells[handle_col])
        if handle in (UNKNOWN, ""):
            continue

        def cell(index: Optional[int]) -> str:
            return cells[index] if index is not None and index < len(cells) else ""

        sample_value = parse_number(cell(sample_col))
        accounts[handle] = AccountBaseline(
            handle=handle,
            median_views=parse_number(cell(median_col)),
            sample_size=int(sample_value) if sample_value else None,
            measured_on=parse_date(cell(measured_col)),
            last_run=parse_date(cell(run_col)),
        )
    return accounts


def _research_state_from_blocks(text: str) -> dict[str, AccountBaseline]:
    accounts: dict[str, AccountBaseline] = {}
    blocks = re.split(r"^#{2,6}\s+", text, flags=re.MULTILINE)[1:]
    for block in blocks:
        head, _, body = block.partition("\n")
        handle = _clean_handle(head)
        if handle in (UNKNOWN, ""):
            continue
        fields = inline_fields(body)
        joined = f"{head}\n{body}"
        median = parse_number(
            fields.get("median_views") or fields.get("median views") or fields.get("median")
            or fields.get("normal") or ""
        )
        sample = parse_number(fields.get("sample size") or fields.get("sample") or "")
        measured = parse_date(
            fields.get("date measured") or fields.get("measured") or fields.get("baseline") or ""
        )
        last_run = parse_date(fields.get("last run") or fields.get("last run date") or "")
        if median is None and measured is None and last_run is None and "median" not in joined.lower():
            continue
        accounts[handle] = AccountBaseline(
            handle=handle,
            median_views=median,
            sample_size=int(sample) if sample else None,
            measured_on=measured,
            last_run=last_run,
        )

    # One-line-per-account bullets, e.g.
    # "- @handle, median 4,200 views, sample 30, measured 2026-08-01, last run 2026-08-22"
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-") or "median" not in stripped.lower():
            continue
        body = stripped.lstrip("-").strip()
        # The owner's agent may separate the handle from its numbers with a
        # dash, a long dash, a colon or a comma. All four are ordinary writing.
        handle_match = re.match(r"@?([A-Za-z0-9_.\- ]{2,40}?)\s*[\u2014:,-]", body)
        if not handle_match:
            continue
        handle = _clean_handle(handle_match.group(1))
        if handle in (UNKNOWN, "") or handle in accounts:
            continue
        median_part = re.search(r"median[^0-9]*([\d,\.]+\s*[km]?)", body, re.IGNORECASE)
        sample_part = re.search(r"sample[^0-9]*(\d+)", body, re.IGNORECASE)
        measured_part = re.search(r"measured[^0-9]*(\d{4}-\d{2}-\d{2})", body, re.IGNORECASE)
        run_part = re.search(r"last run[^0-9]*(\d{4}-\d{2}-\d{2})", body, re.IGNORECASE)
        accounts[handle] = AccountBaseline(
            handle=handle,
            median_views=parse_number(median_part.group(1)) if median_part else None,
            sample_size=int(sample_part.group(1)) if sample_part else None,
            measured_on=parse_date(measured_part.group(1)) if measured_part else None,
            last_run=parse_date(run_part.group(1)) if run_part else None,
        )
    return accounts


# ---------------------------------------------------------------------------
# MY-WATCHLIST.md: which lane each account sits in
# ---------------------------------------------------------------------------

FAMILY_RULES = (
    ("competitor", ("direct competitor", "competitor", "same thing as me")),
    ("authority", ("bigger authority", "authority", "big name", "leader")),
    ("underdog", ("smaller", "punching above", "small account", "up and coming")),
    ("outside_industry", ("outside my industry", "outside", "another industry",
                          "different industry", "great format")),
)


def read_watchlist_families(content_os: Path) -> dict[str, str]:
    path = content_os / "MY-WATCHLIST.md"
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    # Only the accounts table counts. The "Filed so far" table further down has
    # a Date column and would otherwise be read as an account.
    sections = split_sections(text)
    accounts_body = find_section(sections, "the accounts", "accounts") or text

    families: dict[str, str] = {}
    lines = [line for line in accounts_body.splitlines() if line.strip().startswith("|")]
    if len(lines) >= 3:
        header = [cell.lower() for cell in _split_row(lines[0])]
        account_col = next((i for i, cell in enumerate(header) if "account" in cell), 0)
        why_col = next((i for i, cell in enumerate(header) if "why" in cell), None)
        for line in lines[2:]:
            cells = _split_row(line)
            if len(cells) <= account_col or not cells[account_col].strip():
                continue
            handle = _clean_handle(cells[account_col])
            if handle in (UNKNOWN, ""):
                continue
            why = cells[why_col] if why_col is not None and why_col < len(cells) else ""
            family = _match_rules(why, FAMILY_RULES)
            families[handle] = "" if family == UNKNOWN else family
    return families


# ---------------------------------------------------------------------------
# posted.md: the posted-content ledger
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class StatsSnapshot:
    as_of: Optional[dt.date]
    metrics: dict[str, float]
    raw: str


@dataclasses.dataclass(frozen=True)
class PostedPiece:
    posted_on: Optional[dt.date]
    title: str
    fields: dict[str, str]
    stats: tuple[StatsSnapshot, ...]

    @property
    def platform(self) -> str:
        return self.fields.get("platform", "")

    @property
    def link(self) -> str:
        return self.fields.get("link", "")

    @property
    def job(self) -> str:
        return self.fields.get("job", "")

    @property
    def franchise(self) -> str:
        return self.fields.get("franchise", "")

    @property
    def multiple(self) -> Optional[float]:
        return parse_multiple(self.fields.get("multiple", ""))

    def latest_metric(self, name: str) -> Optional[float]:
        for snapshot in reversed(self.stats):
            if name in snapshot.metrics:
                return snapshot.metrics[name]
        return None


METRIC_TOKEN_RE = re.compile(
    r"([a-z][a-z \-]{2,28}?)\s*[:=]?\s*([\d,\.]+\s*[km%]?)", re.IGNORECASE
)


def parse_stats_line(raw: str) -> StatsSnapshot:
    as_of_match = re.search(r"as of\s*(\d{4}-\d{2}-\d{2})", raw, re.IGNORECASE)
    as_of = parse_date(as_of_match.group(1)) if as_of_match else None
    body = raw
    if as_of_match:
        body = raw[: as_of_match.start()].rstrip(" (")
    metrics: dict[str, float] = {}
    for chunk in re.split(r"[,;]", body):
        found = METRIC_TOKEN_RE.search(chunk)
        if not found:
            continue
        name = slugify(found.group(1), limit=28)
        if name in (UNKNOWN, "", "as_of"):
            continue
        value = parse_number(found.group(2))
        if value is None:
            continue
        metrics.setdefault(name, value)
    return StatsSnapshot(as_of=as_of, metrics=metrics, raw=raw.strip())


def read_posted_ledger(content_os: Path) -> list[PostedPiece]:
    path = content_os / "posted.md"
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    pieces: list[PostedPiece] = []
    blocks = re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]
    for block in blocks:
        head, _, body = block.partition("\n")
        head = head.strip()
        if head.lower().startswith("how this file works"):
            continue
        posted_on = parse_date(head)
        title = head
        if posted_on:
            title = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[-\u2014:]?\s*", "", head).strip()
        fields: dict[str, str] = {}
        stats: list[StatsSnapshot] = []
        for line in body.splitlines():
            stripped = line.strip().lstrip("-*").strip()
            match = re.match(r"^([A-Za-z][A-Za-z0-9 _/'’-]{0,32}):\s*(.*)$", stripped)
            if not match:
                continue
            key = match.group(1).strip().lower()
            value = match.group(2).strip()
            if key == "stats":
                stats.append(parse_stats_line(value))
            elif key not in fields:
                fields[key] = value
        stats.sort(key=lambda snapshot: (snapshot.as_of or dt.date.min))
        pieces.append(
            PostedPiece(posted_on=posted_on, title=title, fields=fields, stats=tuple(stats))
        )
    return pieces
