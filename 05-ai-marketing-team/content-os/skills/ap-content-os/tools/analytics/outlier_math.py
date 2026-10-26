#!/usr/bin/env python3
"""
outlier_math.py: the outlier multiple calculator.

Job (one job):
    Given an account's recent view counts (the comparison baseline) and one or
    more candidate post view counts, compute the outlier multiple for each
    candidate: candidate_views / account_median_views.

    Flags candidates >= 3x the account's median as outliers. That is the
    working definition of a performance-backed hook used everywhere in this
    system: a post only counts as a standout when it clearly beat the normal
    of the account that published it.

    Also attaches a recency note: posts should be compared at roughly similar
    ages. This file has no clock of its own; if the caller supplies post ages
    in days, it flags any candidate older than --recency-window-days
    (default 90) as "STALE: compare with caution" rather than silently
    including it. A six-month-old post is history, not evidence.

Used for two jobs, same maths both times:
    1. Watchlist accounts. Did this post beat that account's normal by 3x?
       (the research stage's standout gate)
    2. The owner's own posts. Did this piece beat their own last-20 median?
       (the weekly review's band and winner test)

Pure standard library (statistics, json, argparse). No third-party packages,
no network calls, no keys, no files written.

USAGE

    1) Arguments (quick one-off):
        python3 outlier_math.py \\
            --recent-views 12000 15000 9000 20000 11000 \\
            --candidate "post_a:64000:5" \\
            --candidate "post_b:31000:120"

       Each --candidate is "label:views:age_days" (age_days optional).

    2) JSON on stdin (batch mode):
        echo '{
          "creator": "example_account",
          "recent_views": [12000, 15000, 9000, 20000, 11000],
          "candidates": [
            {"label": "post_a", "views": 64000, "age_days": 5},
            {"label": "post_b", "views": 31000, "age_days": 120}
          ]
        }' | python3 outlier_math.py --stdin

    Output: JSON to stdout, one object per candidate plus the median used, so
    the caller can consume it directly.

EXIT CODES
    0  ran successfully (even if zero candidates cleared the outlier bar ,
       that is a valid, reportable result, not an error)
    2  bad input (empty recent_views, malformed --candidate, invalid JSON)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from typing import Optional

OUTLIER_THRESHOLD = 3.0
DEFAULT_RECENCY_WINDOW_DAYS = 90


class InputError(ValueError):
    """Raised for malformed caller input, maps to exit code 2."""


def compute_median(recent_views: list[float]) -> float:
    if not recent_views:
        raise InputError("recent_views is empty, need at least one comparison view count")
    if any(v < 0 for v in recent_views):
        raise InputError("recent_views contains a negative value")
    return statistics.median(recent_views)


def evaluate_candidate(
    label: str,
    views: float,
    creator_median: float,
    age_days: Optional[float] = None,
    recency_window_days: float = DEFAULT_RECENCY_WINDOW_DAYS,
) -> dict:
    if views < 0:
        raise InputError(f"candidate '{label}' has negative views")
    if creator_median <= 0:
        # Median of zero means there is no real baseline, outlier maths is
        # meaningless. Report it plainly rather than dividing by zero or
        # silently returning infinity.
        return {
            "label": label,
            "views": views,
            "creator_median": creator_median,
            "outlier_multiple": None,
            "is_outlier": False,
            "note": "creator_median is 0, no valid baseline, cannot compute a multiple",
            "age_days": age_days,
            "recency_flag": _recency_flag(age_days, recency_window_days),
        }

    multiple = views / creator_median
    return {
        "label": label,
        "views": views,
        "creator_median": creator_median,
        "outlier_multiple": round(multiple, 2),
        "is_outlier": multiple >= OUTLIER_THRESHOLD,
        "note": (
            f">= {OUTLIER_THRESHOLD:g}x account median, flagged outlier"
            if multiple >= OUTLIER_THRESHOLD
            else f"< {OUTLIER_THRESHOLD:g}x account median, not flagged"
        ),
        "age_days": age_days,
        "recency_flag": _recency_flag(age_days, recency_window_days),
    }


def _recency_flag(age_days: Optional[float], recency_window_days: float) -> str:
    if age_days is None:
        return "UNKNOWN: no age_days supplied, compare with caution"
    if age_days < 0:
        return "INVALID: negative age_days supplied"
    if age_days > recency_window_days:
        return (
            f"STALE: {age_days:g}d old, outside the "
            f"{recency_window_days:g}d recency window (compare with caution; "
            "a six-month-old post should not be casually compared with a "
            "three-day-old one)"
        )
    return f"FRESH, {age_days:g}d old, within {recency_window_days:g}d window"


def parse_candidate_arg(raw: str) -> dict:
    """Parse 'label:views:age_days' or 'label:views' from a --candidate flag."""
    parts = raw.split(":")
    if len(parts) not in (2, 3):
        raise InputError(
            f"--candidate '{raw}' malformed, expected 'label:views' or 'label:views:age_days'"
        )
    label = parts[0]
    try:
        views = float(parts[1])
    except ValueError:
        raise InputError(f"--candidate '{raw}' has non-numeric views")
    age_days = None
    if len(parts) == 3 and parts[2] != "":
        try:
            age_days = float(parts[2])
        except ValueError:
            raise InputError(f"--candidate '{raw}' has non-numeric age_days")
    return {"label": label, "views": views, "age_days": age_days}


def run_from_stdin(recency_window_days: float) -> dict:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON on stdin: {exc}")

    creator = payload.get("creator", "unknown")
    recent_views = payload.get("recent_views")
    candidates = payload.get("candidates")

    if not isinstance(recent_views, list) or not recent_views:
        raise InputError("JSON input must include a non-empty 'recent_views' list")
    if not isinstance(candidates, list) or not candidates:
        raise InputError("JSON input must include a non-empty 'candidates' list")

    creator_median = compute_median([float(v) for v in recent_views])

    results = []
    for c in candidates:
        if "label" not in c or "views" not in c:
            raise InputError(f"candidate entry missing 'label' or 'views': {c}")
        results.append(
            evaluate_candidate(
                label=c["label"],
                views=float(c["views"]),
                creator_median=creator_median,
                age_days=c.get("age_days"),
                recency_window_days=recency_window_days,
            )
        )

    return {
        "creator": creator,
        "recent_views_count": len(recent_views),
        "creator_median": creator_median,
        "outlier_threshold": OUTLIER_THRESHOLD,
        "recency_window_days": recency_window_days,
        "results": results,
    }


def run_from_args(
    recent_views: list[float], candidate_raws: list[str], recency_window_days: float
) -> dict:
    creator_median = compute_median(recent_views)
    results = []
    for raw in candidate_raws:
        c = parse_candidate_arg(raw)
        results.append(
            evaluate_candidate(
                label=c["label"],
                views=c["views"],
                creator_median=creator_median,
                age_days=c["age_days"],
                recency_window_days=recency_window_days,
            )
        )
    return {
        "creator": "unspecified",
        "recent_views_count": len(recent_views),
        "creator_median": creator_median,
        "outlier_threshold": OUTLIER_THRESHOLD,
        "recency_window_days": recency_window_days,
        "results": results,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute outlier multiple (candidate views / account median) with a recency note.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read a JSON payload from stdin instead of --recent-views/--candidate args.",
    )
    parser.add_argument(
        "--recent-views",
        nargs="+",
        type=float,
        help="The account's recent view counts (the baseline set the median is computed from).",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        help="One candidate post as 'label:views' or 'label:views:age_days'. Repeatable.",
    )
    parser.add_argument(
        "--recency-window-days",
        type=float,
        default=DEFAULT_RECENCY_WINDOW_DAYS,
        help=f"Window in days for the recency flag (default {DEFAULT_RECENCY_WINDOW_DAYS}).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.stdin:
            output = run_from_stdin(args.recency_window_days)
        else:
            if not args.recent_views:
                raise InputError("--recent-views is required unless --stdin is used")
            if not args.candidate:
                raise InputError("at least one --candidate is required unless --stdin is used")
            output = run_from_args(args.recent_views, args.candidate, args.recency_window_days)
    except InputError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
