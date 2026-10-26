#!/usr/bin/env python3
"""
Build a made-up content-os workspace so the analytics tools can be checked
without touching anyone's real work.

Nothing here is real data. It is a stand-in owner: a fictional bookkeeping
firm watching five accounts, six weeks of filed standouts, and three of their
own posted pieces.

Usage:

    python3 tests/make_synthetic_workspace.py /somewhere/outside/the/pack
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path


WATCHLIST = """# My watchlist

Built on: {built_on}

## The rules

- Research only. I never repost anyone's content.
- Public posts only.
- What I take is the mechanism, never the wording.

## The accounts

| Account | Platform | Why they are here | What I watch them for |
|---|---|---|---|
| @ledgerlane | Instagram | direct competitor | how they open |
| @taxtruths | Instagram | direct competitor | proof they show |
| @cfoclare | Instagram | bigger authority | depth |
| @smallbizsam | Instagram | smaller account punching above its size | pacing |
| @toolmaker_jo | Instagram | outside my industry, great format | format ideas |

## Filed so far

| Date | Account | What I pulled out |
|---|---|---|
|  |  |  |
"""

RESEARCH_STATE = """# Research state

| Handle | Median views | Sample | Date measured | Last run |
|---|---|---|---|---|
| @ledgerlane | 4,200 | 30 | {measured} | {last_run} |
| @taxtruths | 3,100 | 30 | {measured} | {last_run} |
| @cfoclare | 61,000 | 30 | {measured} | {last_run} |
| @smallbizsam | 900 | 24 | {measured} | {last_run} |
| @toolmaker_jo | 12,000 | 30 | {measured} | {last_run} |

## Links already filed

- Nothing skipped this week.
"""

ENTRY = """# Library entry: {mechanism_short}

Filed: {filed}
Posted: {posted}
Last re-checked:
Account normal: {normal} views
This post: {views} views
Multiple: {multiple}x
Words captured: {words}
Mechanism family: {mechanism_family}
First frame: {first_frame}

## The opening line, as data
{opening}

## On-screen text
{on_screen}

## First frame
{first_frame}

## The curiosity gap
Why the number they trust is the wrong number.

## The proof device
{proof}

## Format
{fmt}

## The ask at the end
{cta}

## The mechanism
{mechanism}

## Why it stood out
Clearly beat their usual run of posts, about {multiple}x their normal.

## Source and trust level
- Account and platform: {account}, Instagram
- Trust level: {trust}
- Link: https://example.test/p/{slug}

## What I would do with it
Could carry my quarterly clean-up idea.
"""

POSTED = """# Posted

Append only. One section per posted piece, newest at the bottom.

## {d1} - The receipt drawer test

- platform: instagram
- format: talking to camera
- link: https://example.test/p/own-receipt-drawer
- hook: Your bookkeeper is not the reason your books are late.
- job: reach
- franchise:
- script: {d1}-receipt-drawer.md
- stats: views 3100, likes 140, comments 11, shares 6, saves 22 (as of {d1b})
- stats: views 5200, likes 210, comments 18, shares 9, saves 41, follows 12 (as of {d1c})
- multiple: 1.4x vs median 3700 of last 12 comparable posts (as of {d1c})
- lesson: The open worked, the middle wandered.

## {d2} - The three numbers I check first

- platform: instagram
- format: screen recording
- link: https://example.test/p/own-three-numbers
- hook: I check three numbers before I look at anything else.
- job: authority
- franchise: The numbers-first franchise
- script: {d2}-three-numbers.md
- stats: views 14200, likes 620, comments 74, shares 88, saves 310 (as of {d2b})
- multiple: 3.8x vs median 3700 of last 12 comparable posts (as of {d2b})
- lesson: Saves were the story, not views.

## {d3} - What a clean set of books actually looks like

- platform: instagram
- format: screen recording
- link: https://example.test/p/own-clean-books
- hook: This is what a clean set of books looks like on screen.
- job: authority
- franchise: The numbers-first franchise
- script: {d3}-clean-books.md
- stats: views 2100, likes 90, comments 30 (as of {d3b})
- enquiries: 2 booked calls, both said they saw this one
- lesson: Small reach, real business signal.
"""


def _entry_text(**kwargs) -> str:
    return ENTRY.format(**kwargs)


def build(root: Path, today: dt.date | None = None) -> Path:
    today = today or dt.date.today()
    content_os = root / "content-os"
    library = content_os / "library"
    library.mkdir(parents=True, exist_ok=True)

    (content_os / "MY-WATCHLIST.md").write_text(
        WATCHLIST.format(built_on=(today - dt.timedelta(days=60)).isoformat()), encoding="utf-8"
    )
    (content_os / "research-state.md").write_text(
        RESEARCH_STATE.format(
            measured=(today - dt.timedelta(days=45)).isoformat(),
            last_run=(today - dt.timedelta(days=2)).isoformat(),
        ),
        encoding="utf-8",
    )

    normals = {
        "ledgerlane": 4200,
        "taxtruths": 3100,
        "cfoclare": 61000,
        "smallbizsam": 900,
        "toolmaker_jo": 12000,
    }

    # (days_ago, account, mechanism_family, format, proof, cta, first frame, multiple)
    #
    # Shape of the made-up history, ten weeks of it:
    #   * "diagnosis" is the steady old shape, present across most windows.
    #   * "challenge_belief" spreads across more accounts in the recent windows,
    #     so a trend has something real to be measured against.
    #   * two entries are deliberately imperfect, so the honesty counters fire.
    plan = [
        # last 14 days, the current window
        (1, "ledgerlane", "challenge_belief", "talking to camera", "a client conversation", "follow", "a face, watched", 4.1),
        (3, "taxtruths", "challenge_belief", "talking to camera", "a result on screen", "follow", "a face, watched", 3.6),
        (5, "cfoclare", "challenge_belief", "screen recording", "a screenshot of the dashboard", "link in bio", "a result on screen, watched", 3.2),
        (6, "smallbizsam", "challenge_belief", "talking to camera", "a named failure", "comment the word BOOKS", "a face, watched", 5.4),
        (8, "toolmaker_jo", "warning", "demonstration", "a live demonstration", "follow", "hands, watched", 3.9),
        (10, "ledgerlane", "diagnosis", "talking to camera", "a result on screen", "follow", "a face, watched", 3.3),
        (12, "taxtruths", "challenge_belief", "screen recording", "a screenshot of the dashboard", "link in bio", "a result on screen, watched", 4.8),
        # 14 to 27 days back, reference A
        (16, "cfoclare", "diagnosis", "talking to camera", "a client conversation", "follow", "a face, watched", 3.1),
        (18, "ledgerlane", "diagnosis", "talking to camera", "a result on screen", "follow", "a face, watched", 3.5),
        (20, "smallbizsam", "warning", "talking to camera", "a named failure", "save this", "a face, watched", 6.2),
        (22, "taxtruths", "diagnosis", "talking to camera", "a client conversation", "follow", "a face, watched", 3.4),
        (24, "toolmaker_jo", "story_open", "voiceover", "a before and after", "follow", "an object, watched", 4.4),
        (26, "cfoclare", "challenge_belief", "screen recording", "a screenshot of the dashboard", "link in bio", "a result on screen, watched", 3.7),
        # 28 to 41 days back, reference B
        (30, "ledgerlane", "diagnosis", "talking to camera", "a result on screen", "follow", "a face, watched", 3.8),
        (32, "cfoclare", "diagnosis", "screen recording", "a screenshot of the dashboard", "link in bio", "a result on screen, watched", 3.3),
        (34, "smallbizsam", "warning", "talking to camera", "a named failure", "save this", "a face, watched", 4.9),
        (36, "taxtruths", "diagnosis", "talking to camera", "a client conversation", "follow", "a face, watched", 3.2),
        (38, "toolmaker_jo", "story_open", "voiceover", "a before and after", "follow", "an object, watched", 3.9),
        # older still, so the thirty-day window and the streaks have depth
        (44, "ledgerlane", "diagnosis", "talking to camera", "a result on screen", "follow", "a face, watched", 3.6),
        (46, "cfoclare", "diagnosis", "screen recording", "a screenshot of the dashboard", "link in bio", "a result on screen, watched", 3.4),
        (48, "smallbizsam", "warning", "talking to camera", "a named failure", "save this", "a face, watched", 5.1),
        (50, "taxtruths", "diagnosis", "talking to camera", "a client conversation", "follow", "a face, watched", 3.9),
        (52, "toolmaker_jo", "story_open", "voiceover", "a before and after", "follow", "an object, watched", 4.2),
        (58, "ledgerlane", "diagnosis", "talking to camera", "a result on screen", "follow", "a face, watched", 3.1),
        (60, "cfoclare", "diagnosis", "screen recording", "a screenshot of the dashboard", "link in bio", "a result on screen, watched", 3.5),
        (62, "taxtruths", "diagnosis", "talking to camera", "a client conversation", "follow", "a face, watched", 4.0),
        (64, "smallbizsam", "warning", "talking to camera", "a named failure", "save this", "a face, watched", 4.5),
    ]

    for index, (days_ago, account, family, fmt, proof, cta, first_frame, multiple) in enumerate(plan):
        posted = today - dt.timedelta(days=days_ago)
        filed = posted + dt.timedelta(days=2)
        if filed > today:
            filed = today
        normal = normals[account]
        slug = f"{family}-{index}"
        text = _entry_text(
            mechanism_short=family.replace("_", " "),
            filed=filed.isoformat(),
            posted=posted.isoformat(),
            normal=f"{normal:,}",
            views=f"{int(normal * multiple):,}",
            multiple=multiple,
            words="transcript",
            mechanism_family=family,
            first_frame=first_frame,
            opening="Quoted for analysis only.",
            on_screen="Three words on a plain background.",
            proof=proof,
            fmt=fmt,
            cta=cta,
            mechanism=f"{family.replace('_', ' ')} before offering any answer.",
            account=f"@{account}",
            trust="someone in my niche",
            slug=slug,
        )
        (library / f"{filed.isoformat()} - {account} - {slug}.md").write_text(text, encoding="utf-8")

    # Two of the owner's own winners, filed as own-account entries.
    for index, (days_ago, family, fmt, multiple) in enumerate(
        [(8, "diagnosis", "screen recording", 3.8), (26, "challenge_belief", "talking to camera", 3.1)]
    ):
        posted = today - dt.timedelta(days=days_ago)
        filed = posted + dt.timedelta(days=3)
        if filed > today:
            filed = today
        text = _entry_text(
            mechanism_short=f"my own {family.replace('_', ' ')} winner",
            filed=filed.isoformat(),
            posted=posted.isoformat(),
            normal="3,700",
            views=f"{int(3700 * multiple):,}",
            multiple=multiple,
            words="transcript",
            mechanism_family=family,
            first_frame="a result on screen, watched",
            opening="My own words, kept for the record.",
            on_screen="Three numbers.",
            proof="a screenshot of the dashboard",
            fmt=fmt,
            cta="link in bio",
            mechanism=f"{family.replace('_', ' ')} using my own numbers.",
            account="mine",
            trust="my own results",
            slug=f"own-{index}",
        )
        (library / f"{filed.isoformat()} - mine - own-{index}.md").write_text(text, encoding="utf-8")

    # Two honestly imperfect entries. Neither may enter the maths.
    caption_only = today - dt.timedelta(days=4)
    (library / f"{caption_only.isoformat()} - ledgerlane - caption-only-read.md").write_text(
        _entry_text(
            mechanism_short="caption only read",
            filed=caption_only.isoformat(),
            posted=(caption_only - dt.timedelta(days=2)).isoformat(),
            normal="4,200",
            views="15,000",
            multiple=3.5,
            words="caption only, no transcript came back",
            mechanism_family="challenge_belief",
            first_frame="a face, inferred from the caption",
            opening="Quoted for analysis only.",
            on_screen="Unknown.",
            proof="a result on screen",
            fmt="talking to camera",
            cta="follow",
            mechanism="challenge belief before offering any answer.",
            account="@ledgerlane",
            trust="someone in my niche",
            slug="caption-only-read",
        ),
        encoding="utf-8",
    )
    no_numbers = today - dt.timedelta(days=7)
    (library / f"{no_numbers.isoformat()} - cfoclare - no-numbers.md").write_text(
        """# Library entry: no numbers on this one

Filed: {filed}

## Format
talking to camera

## The mechanism
Names the enemy before making any claim.

## Why it stood out
It felt like it did well. Nobody wrote down the numbers.

## Source and trust level
- Account and platform: @cfoclare, Instagram
- Trust level: someone in my niche
""".format(filed=no_numbers.isoformat()),
        encoding="utf-8",
    )

    (content_os / "posted.md").write_text(
        POSTED.format(
            d1=(today - dt.timedelta(days=26)).isoformat(),
            d1b=(today - dt.timedelta(days=25)).isoformat(),
            d1c=(today - dt.timedelta(days=23)).isoformat(),
            d2=(today - dt.timedelta(days=8)).isoformat(),
            d2b=(today - dt.timedelta(days=5)).isoformat(),
            d3=(today - dt.timedelta(days=3)).isoformat(),
            d3b=(today - dt.timedelta(days=2)).isoformat(),
        ),
        encoding="utf-8",
    )
    return content_os


if __name__ == "__main__":
    target = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd()
    created = build(target)
    print(f"synthetic workspace at {created}")
