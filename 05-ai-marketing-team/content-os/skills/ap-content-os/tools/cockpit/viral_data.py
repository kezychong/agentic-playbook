#!/usr/bin/env python3
"""
viral_data.py - what the Viral now, Library, and Morning brief tabs read.

Standard library only. No network calls anywhere in this file, so it is safe
to call while answering a browser request. Read only.

Three honest rules carried over unchanged, because they are what stop this
tab from lying:

1. A post's date is either exact, clearly labelled as an estimate, or absent.
   Exact dates come from the member's own posted record. Estimates are
   decoded from the post code itself and are always labelled. When neither
   works, the card says the posting date is unavailable and shows the filing
   date instead.

2. "Viral now" contains only posts actually published inside the chosen
   window. An older post can re-enter only when repeated view counts prove a
   genuinely new burst. Everything else lives in All-time winners, which
   never claims anything is viral today.

3. An entry that never recorded the numbers behind it is a reference, not
   proof, and is labelled that way.
"""

import datetime
import re
import statistics
from pathlib import Path

import library_data
import posted_ledger
import workspace as ws

# Post codes on the short-video platform this decoder understands use a
# URL-safe base-64 alphabet, and the code itself carries the posting time.
_CODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
_EPOCH_MS = 1_314_220_021_721
_EARLIEST_DATE = datetime.date(2010, 10, 1)

# An entry counts as proven when it clearly beat that account's normal by
# this much, which is the same three-times gate the research stage uses.
OUTLIER_GATE = 3.0

# A burst counts as a real resurgence only above all three of these.
RESURGE_MIN_DAYS = 2
RESURGE_MIN_GAIN = 1000
RESURGE_PACE_MULTIPLE = 3


def _decode_code(code: str):
    if not isinstance(code, str) or len(code) != 11:
        return None
    value = 0
    for char in code:
        try:
            digit = _CODE_ALPHABET.index(char)
        except ValueError:
            return None
        value = (value * 64) + digit
    return value or None


def estimated_post_date(code: str, tzinfo, now=None):
    """The posting date the post code itself implies, in the member's own
    timezone. The decode is exact; the packed timestamp is only ever a good
    estimate, so every caller must label it as one."""
    media_id = _decode_code(code)
    if media_id is None:
        return None
    timestamp_ms = (media_id >> 23) + _EPOCH_MS
    try:
        estimated = datetime.datetime.fromtimestamp(
            timestamp_ms / 1000, tz=datetime.timezone.utc
        ).astimezone(tzinfo)
    except (OverflowError, OSError, ValueError):
        return None
    if now is None:
        now_dt = datetime.datetime.now(tz=tzinfo)
    elif isinstance(now, datetime.datetime):
        now_dt = now.astimezone(tzinfo) if now.tzinfo else now.replace(tzinfo=tzinfo)
    else:
        now_dt = datetime.datetime.combine(now, datetime.time.max, tzinfo=tzinfo)
    if estimated.date() < _EARLIEST_DATE:
        return None
    if estimated > now_dt:
        return None
    return estimated


def load_view_snapshots(path: Path) -> dict:
    """An optional compact history of view counts, written by the research
    engine when it re-checks a post. Absent, unreadable, or malformed all
    read as no history at all."""
    payload = ws.read_json(path, default=None)
    if not isinstance(payload, dict):
        return {}
    clean = {}
    for code, rows in payload.items():
        if not isinstance(code, str) or not isinstance(rows, list):
            continue
        by_date = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                day = datetime.date.fromisoformat(str(row.get("date", "")))
                views = int(row.get("views"))
            except (TypeError, ValueError):
                continue
            if views < 0:
                continue
            by_date[day.isoformat()] = {"date": day.isoformat(), "views": views}
        if by_date:
            clean[code] = [by_date[key] for key in sorted(by_date)][-13:]
    return clean


def velocity(snapshots, posted: datetime.date, today: datetime.date) -> dict:
    """Is this post surging again right now? Only repeated view counts can
    answer that, so with fewer than two the answer is "still collecting"."""
    rows = []
    for row in snapshots or []:
        try:
            day = datetime.date.fromisoformat(str(row["date"]))
            views = int(row["views"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append((day, views))
    rows = sorted(rows)[-13:]
    empty = {
        "method": "collecting",
        "is_resurging": False,
        "snapshot_count": len(rows),
        "view_gain": None,
        "interval_days": None,
        "recent_views_per_day": None,
        "baseline_views_per_day": None,
    }
    if len(rows) < 2:
        return empty
    latest_date, latest_views = rows[-1]
    prior_date, prior_views = rows[-2]
    interval_days = (latest_date - prior_date).days
    view_gain = latest_views - prior_views
    if interval_days <= 0 or view_gain < 0:
        return empty
    recent_pace = view_gain / interval_days
    method = "lifetime_average"
    age_days = max(1, (latest_date - posted).days)
    baseline_pace = latest_views / age_days
    if len(rows) >= 4:
        prior_paces = []
        for (start_day, start_views), (end_day, end_views) in zip(rows[:-2], rows[1:-1]):
            days = (end_day - start_day).days
            gain = end_views - start_views
            if days > 0 and gain >= 0:
                prior_paces.append(gain / days)
        if prior_paces:
            method = "interval_median"
            baseline_pace = statistics.median(prior_paces)
    if baseline_pace > 0:
        threshold_met = recent_pace >= (RESURGE_PACE_MULTIPLE * baseline_pace)
    else:
        threshold_met = view_gain >= RESURGE_MIN_GAIN
    return {
        "method": method,
        "is_resurging": (
            interval_days >= RESURGE_MIN_DAYS
            and view_gain >= RESURGE_MIN_GAIN
            and threshold_met
        ),
        "snapshot_count": len(rows),
        "view_gain": view_gain,
        "interval_days": interval_days,
        "recent_views_per_day": round(recent_pace, 1),
        "baseline_views_per_day": round(baseline_pace, 1),
    }


def _admission(entry: dict) -> dict:
    """Why this entry earned a place, in plain words.

    Only two things earn one: the member's own audience already proved it, or
    the entry recorded numbers showing it clearly beat that account's normal.
    Everything else is a reference, and is labelled as one rather than quietly
    counted as evidence.

    The labels only ever add something the card does not already show. The
    multiple has its own badge and the evidence rung has its own chip, so
    neither is repeated here.
    """
    own = bool(entry.get("own")) or str(entry.get("trust", "")).startswith("my own")
    multiple = entry.get("multiple")
    beat_normal = multiple is not None and multiple >= OUTLIER_GATE

    labels = []
    if own:
        labels.append("proved with your audience")
    if multiple is not None and not beat_normal:
        labels.append("under the 3 times mark")

    return {
        "valid": own or beat_normal,
        "labels": labels,
        "raw": entry.get("trust_raw", ""),
    }


def _posted_fields(entry, exact_dates, tzinfo, today):
    code = entry.get("shortcode")
    filed = entry.get("filed")
    if code and code in exact_dates:
        posted = datetime.date.fromisoformat(exact_dates[code])
        precision, flag = "exact", ""
    else:
        estimated = estimated_post_date(code, tzinfo, now=today) if code else None
        if estimated is None:
            if not filed:
                return {
                    "posted": None,
                    "posted_precision": "unknown",
                    "posted_flag": "No posting date and no filing date on this entry.",
                    "posted_windows": [],
                    "posted_boundary_uncertain": [],
                }
            posted = datetime.date.fromisoformat(filed)
            precision = "filed_fallback"
            flag = "Posting date unavailable, so this shows the date it was filed."
        else:
            posted = estimated.date()
            precision = "estimated"
            flag = "Estimated from the post's own code."
    age_days = (today - posted).days
    windows, uncertain = [], []
    if precision != "filed_fallback" and age_days >= 0:
        for window in (7, 14, 30):
            if precision == "estimated" and age_days == window:
                uncertain.append(window)
            elif age_days <= window:
                windows.append(window)
    return {
        "posted": posted.isoformat(),
        "posted_precision": precision,
        "posted_flag": flag,
        "posted_windows": windows,
        "posted_boundary_uncertain": uncertain,
    }


def build_entries(workspace, config, today=None) -> list:
    """Every library entry, decorated with dates, admission, and velocity."""
    tzinfo = ws.tzinfo_for(config)
    today = today or ws.today_in(config)
    entries = library_data.load_entries(workspace.library_dir)

    ledger = posted_ledger.load_entries(workspace.posted_ledger)
    exact_dates = posted_ledger.exact_dates_by_shortcode(ledger)
    snapshots = load_view_snapshots(workspace.view_snapshots)
    for code, rows in posted_ledger.snapshots_by_shortcode(ledger).items():
        snapshots.setdefault(code, rows)

    out = []
    for entry in entries:
        dates = _posted_fields(entry, exact_dates, tzinfo, today)
        admission = _admission(entry)
        posted_day = None
        if dates["posted"]:
            try:
                posted_day = datetime.date.fromisoformat(dates["posted"])
            except ValueError:
                posted_day = None
        speed = velocity(
            snapshots.get(entry.get("shortcode") or "", []),
            posted_day or today,
            today,
        )
        row = {
            "title": entry["title"],
            "creator": entry["creator"],
            "family": entry["trust"],
            "mechanism_family": entry["mechanism_family"],
            "cls": entry["mechanism"] or entry["opening_line"],
            "multiple": entry["multiple"],
            "views": entry["views"],
            "reel_url": entry["link"],
            "shortcode": entry["shortcode"],
            "filed": entry["filed"],
            "own": entry["own"],
            "card_path": workspace.relative(entry["path"]),
            "admission_valid": admission["valid"],
            "admission_labels": admission["labels"],
            "admission_raw": admission["raw"],
            "velocity": speed,
        }
        row.update(dates)
        out.append(row)
    return out


def brief_data(workspace, config, today=None) -> dict:
    """What the Morning brief tab shows: this week's one focus, the mechanism
    of the day, and three counts. Every one of them has an honest empty
    state, because a workspace on day one has none of them."""
    today = today or ws.today_in(config)
    entries = library_data.load_entries(workspace.library_dir)

    focus = read_focus(workspace)
    featured = library_data.featured_entry(entries, today)
    if featured is None:
        hook_of_day = {"title": "", "family": "", "skeleton_line": "", "card_path": ""}
    else:
        hook_of_day = {
            "title": featured["title"],
            "family": featured["trust"],
            "skeleton_line": featured["mechanism"] or featured["opening_line"] or featured["title"],
            "card_path": workspace.relative(featured["path"]),
        }

    inbox = _count_cards(workspace.inbox_dir)
    qualified = _count_cards(workspace.qualified_dir)
    watchlist = library_data.watchlist_account_count(ws.read_text(workspace.watchlist_file))
    ledger = posted_ledger.load_entries(workspace.posted_ledger)

    return {
        "one_lever": focus,
        "hook_of_day": hook_of_day,
        "counts": {
            "library": len(entries),
            "watchlist": watchlist,
            "ideas_in_play": inbox + qualified,
            "posted": len(ledger),
        },
    }


_FOCUS_LINE_RE = re.compile(r"^\s*(?:This week|Focus|One lever|One thing)\s*:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def read_focus(workspace) -> str:
    """This week's single focus, from MY-FOCUS.md. That file is optional, so
    an empty answer is normal and the tab says so plainly."""
    text = ws.read_text(workspace.focus_file)
    if not text.strip():
        return ""
    match = _FOCUS_LINE_RE.search(text)
    if match:
        return match.group(1).strip()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        if line.startswith("- ") or line.startswith("* "):
            line = line[2:].strip()
        if line and not line.startswith("{"):
            return line
    return ""


def _count_cards(dir_path: Path) -> int:
    if not dir_path or not Path(dir_path).is_dir():
        return 0
    return sum(
        1
        for path in Path(dir_path).glob("*.md")
        if not path.name.startswith("_") and not path.name.upper().startswith("README")
    )
