#!/usr/bin/env python3
"""
review_numbers.py: the arithmetic behind the weekly review.

Reads content-os/posted.md and works out, for every piece in the review
window:

    * the baseline: the median views of the last twenty comparable pieces
      (same platform and format) posted before it, and how many were actually
      available to compare with
    * the multiple: this piece's views divided by that baseline
    * the band: weak below 0.7x, normal 0.7x to 1.5x, strong 1.5x to 3x,
      outlier above 3x
    * whether it clears the winner bar (3x, or a business signal recorded in
      the ledger even without the reach)
    * which numbers are missing, one list per piece, so the review asks for
      exactly those and nothing else

It never estimates a number that is not written down. A missing number comes
back as missing.

The multiple itself is worked out by outlier_math.py, the same maths the
research stage uses on watchlist accounts. It is not reimplemented here.

Usage:
    python3 review_numbers.py --workspace /folder/that/holds/content-os
    python3 review_numbers.py --workspace . --since 2026-08-17

Output: JSON to stdout.

Exit codes:
    0  read the ledger (even if it was empty)
    2  no workspace found
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from outlier_math import compute_median, evaluate_candidate  # noqa: E402
from workspace_read import PostedPiece, read_posted_ledger, slugify  # noqa: E402

BASELINE_SAMPLE = 20
BANDS = ((0.7, "weak"), (1.5, "normal"), (3.0, "strong"))

# What the owner's agent can read from a public post, and what only the owner
# can see inside the app. The split is not a preference, it is what is public.
PUBLIC_METRICS = ("views", "likes", "comments")
PRIVATE_METRICS = ("shares", "saves", "follows", "watch_time", "reach", "profile_visits")

BUSINESS_FIELDS = ("enquiries", "bookings", "sales", "sign_ups", "signups", "replies", "business")


def band_for(multiple: Optional[float]) -> str:
    if multiple is None:
        return "unknown"
    for edge, name in BANDS:
        if multiple < edge:
            return name
    return "outlier"


def _comparable_key(piece: PostedPiece) -> str:
    return f"{slugify(piece.platform)}|{slugify(piece.fields.get('format', ''))}"


def _views(piece: PostedPiece) -> Optional[float]:
    return piece.latest_metric("views") or piece.latest_metric("plays")


def _business_signal(piece: PostedPiece) -> str:
    for field in BUSINESS_FIELDS:
        if piece.fields.get(field):
            return f"{field}: {piece.fields[field]}"
    return ""


def _missing_numbers(piece: PostedPiece) -> dict[str, list[str]]:
    seen = set()
    for snapshot in piece.stats:
        seen.update(snapshot.metrics)
    return {
        "public": [name for name in PUBLIC_METRICS if name not in seen],
        "only_you_can_see": [name for name in PRIVATE_METRICS if name not in seen],
    }


def review(content_os: Path, since: Optional[dt.date], as_of: dt.date) -> dict[str, Any]:
    pieces = read_posted_ledger(content_os)
    pieces.sort(key=lambda piece: (piece.posted_on or dt.date.min))

    rows: list[dict[str, Any]] = []
    baselines: dict[str, dict[str, Any]] = {}

    for index, piece in enumerate(pieces):
        key = _comparable_key(piece)
        earlier = [
            other
            for other in pieces[:index]
            if _comparable_key(other) == key and _views(other) is not None
        ][-BASELINE_SAMPLE:]
        comparable_views = [_views(other) for other in earlier]
        baseline = compute_median(comparable_views) if comparable_views else None
        views = _views(piece)

        multiple = None
        band = "unknown"
        note = ""
        if views is None:
            note = "no view count recorded yet"
        elif baseline is None:
            note = "no comparable piece to measure against yet, so no multiple"
        else:
            age_days = (as_of - piece.posted_on).days if piece.posted_on else None
            result = evaluate_candidate(
                label=piece.title or "piece",
                views=views,
                creator_median=baseline,
                age_days=age_days,
            )
            multiple = result["outlier_multiple"]
            band = band_for(multiple)
            note = result["note"]

        business = _business_signal(piece)
        in_window = since is None or (piece.posted_on and piece.posted_on >= since)
        row = {
            "posted_on": piece.posted_on.isoformat() if piece.posted_on else None,
            "title": piece.title,
            "platform": piece.platform,
            "format": piece.fields.get("format", ""),
            "job": piece.job,
            "link": piece.link,
            "franchise": piece.franchise,
            "hook": piece.fields.get("hook", ""),
            "views": views,
            "baseline_median": baseline,
            "comparable_count": len(comparable_views),
            "comparable_note": (
                "fewer than twenty comparable pieces exist, so this baseline is thin"
                if 0 < len(comparable_views) < BASELINE_SAMPLE
                else ""
            ),
            "multiple": multiple,
            "band": band,
            "note": note,
            "ledger_multiple": piece.multiple,
            "business_signal": business,
            "winner": bool((multiple is not None and multiple >= 3.0) or business),
            "winner_reason": (
                "three times the baseline"
                if multiple is not None and multiple >= 3.0
                else ("business signal without the reach" if business else "")
            ),
            "stats_snapshots": [
                {
                    "as_of": snapshot.as_of.isoformat() if snapshot.as_of else None,
                    "metrics": snapshot.metrics,
                }
                for snapshot in piece.stats
            ],
            "missing": _missing_numbers(piece),
            "in_review_window": bool(in_window),
        }
        rows.append(row)
        if baseline is not None:
            baselines[key] = {
                "median_views": baseline,
                "comparable_count": len(comparable_views),
                "as_of": as_of.isoformat(),
            }

    window_rows = [row for row in rows if row["in_review_window"]]
    return {
        "as_of": as_of.isoformat(),
        "since": since.isoformat() if since else None,
        "pieces_in_ledger": len(rows),
        "pieces_in_window": len(window_rows),
        "baselines": baselines,
        "pieces": rows,
        "winners": [row for row in window_rows if row["winner"]],
        "needs_numbers": [
            {
                "title": row["title"],
                "posted_on": row["posted_on"],
                "missing": row["missing"],
            }
            for row in window_rows
            if row["missing"]["public"] or row["missing"]["only_you_can_see"]
        ],
        "notes": [
            "Nothing here is estimated. A number that is not in the ledger is reported as missing.",
            "Views, likes and comments are public. Watch time, reach, saves, follows and profile "
            "visits are only visible to the owner, so they have to be read off the owner's own screen.",
        ],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Work out the weekly review numbers from the ledger.")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--since", default=None, help="Only judge pieces posted on or after this date.")
    parser.add_argument("--as-of", default=None, help="Override today's date (YYYY-MM-DD).")
    args = parser.parse_args(argv)

    start = Path(args.workspace).expanduser().resolve()
    content_os = start if start.name == "content-os" and start.is_dir() else start / "content-os"
    if not content_os.is_dir():
        print(json.dumps({"error": "no content-os folder found at that location"}), file=sys.stderr)
        return 2

    try:
        as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
        since = dt.date.fromisoformat(args.since) if args.since else None
    except ValueError:
        print(json.dumps({"error": "dates must look like 2026-08-24"}), file=sys.stderr)
        return 2

    print(json.dumps(review(content_os, since, as_of), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
