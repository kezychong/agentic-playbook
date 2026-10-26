#!/usr/bin/env python3
"""
build_patterns.py: turn the owner's own workspace into content-os/analytics/patterns.json.

What it reads (all read-only, all optional):
    content-os/library/*.md        the decoded standouts (Library Entries)
    content-os/research-state.md   each watched account's normal, and when it was last measured
    content-os/MY-WATCHLIST.md     which lane each watched account sits in
    content-os/posted.md           the owner's own posted pieces and their numbers

What it writes:
    content-os/analytics/patterns.json         the feed (validated before it replaces the old one)
    content-os/analytics/pattern-history.json  weekly snapshots, so streaks and cooling are real

The gates are the proven ones, ported: momentum, evidence, persistence and
confidence are decided in that order, every gate result is written into the
record's gate_receipt, and a pattern that has not earned a state says
"collecting evidence" instead of pretending.

Two scale profiles exist because one owner watching five accounts is not the
same corpus as a large watchlist:

    --profile member   (default) the same gates, thresholds sized for one owner
    --profile full     the original thresholds, unchanged

The profile in force is named in the feed's scope_note, so nobody can mistake
one for the other.

Honesty rules that are enforced in code, not in prose:
    * A post with no recorded multiple never enters the maths. It is counted
      as unusable and the count is published.
    * A first frame that was not marked as watched never enters visual pattern
      maths. Inferred visuals are excluded by the contract check.
    * Until three weekly snapshots exist, no pattern may be called rising or
      cooling. There is no history to compare against, and the feed says so.
    * If the feed fails its own contract check, the old file is left alone.

Pure standard library. No network. No keys. Nothing is posted anywhere.

Exit codes:
    0  wrote a valid feed
    2  bad arguments or no workspace found
    3  the generated feed failed the contract check (old file left untouched)
    4  another build is already running on this workspace
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from feed_contract import FeedValidationError, validate_feed  # noqa: E402
from workspace_read import (  # noqa: E402
    UNKNOWN,
    LibraryEntry,
    read_library_entries,
    read_posted_ledger,
    read_research_state,
    read_watchlist_families,
)

SCHEMA_VERSION = "patterns-feed-v1"
HISTORY_SCHEMA_VERSION = "patterns-history-v1"
HISTORY_LIMIT = 13
OUTLIER_THRESHOLD = 3.0
MATURATION_DAYS = 2
CONFIDENCE_RANK = {"Low": 0, "Medium": 1, "High": 2}


# ---------------------------------------------------------------------------
# Pattern expansion: the closed set of dimensions and pairs
# ---------------------------------------------------------------------------

ATOMIC_DIMENSIONS = ("mechanism_class", "format", "proof", "cta", "visual_open", "topic")

COMPOSITE_DIMENSIONS = (
    ("mechanism_class", "format"),
    ("mechanism_class", "proof"),
    ("mechanism_class", "cta"),
    ("topic", "mechanism_class"),
    ("topic", "format"),
    ("visual_open", "format"),
)

EXCLUDED_VALUES = {UNKNOWN, "unassigned", ""}
VISUAL_DIMENSION = "visual_open"


@dataclasses.dataclass(frozen=True, order=True)
class PatternDefinition:
    pattern_id: str
    pattern_kind: str
    dimension_a: str
    value_a: str
    dimension_b: Optional[str] = None
    value_b: Optional[str] = None
    eligible_visual: bool = False

    @property
    def dimensions(self) -> tuple[str, ...]:
        return (self.dimension_a,) if self.dimension_b is None else (self.dimension_a, self.dimension_b)

    @property
    def is_visual(self) -> bool:
        return VISUAL_DIMENSION in self.dimensions

    @property
    def label(self) -> str:
        first = f"{self.dimension_a.replace('_', ' ')}: {self.value_a.replace('_', ' ')}"
        if self.dimension_b is None or self.value_b is None:
            return first
        second = f"{self.dimension_b.replace('_', ' ')}: {self.value_b.replace('_', ' ')}"
        return f"{first} x {second}"


def make_pattern_id(
    kind: str,
    dimension_a: str,
    value_a: str,
    dimension_b: Optional[str] = None,
    value_b: Optional[str] = None,
) -> str:
    parts = [f"{dimension_a}={value_a}"]
    if dimension_b is not None and value_b is not None:
        parts.append(f"{dimension_b}={value_b}")
    return f"{kind}:" + "|".join(parts)


def make_record_id(pattern_id: str, scope: str) -> str:
    digest = hashlib.sha256(f"{pattern_id}\n{scope}".encode("utf-8")).hexdigest()[:20]
    return f"pattern-{digest}"


def expand_dimensions(values: dict[str, str], *, visual_observed: bool) -> tuple[PatternDefinition, ...]:
    usable = {}
    for dimension in ATOMIC_DIMENSIONS:
        value = values.get(dimension, UNKNOWN)
        ok = isinstance(value, str) and value not in EXCLUDED_VALUES
        if dimension == VISUAL_DIMENSION and not visual_observed:
            ok = False
        usable[dimension] = ok

    definitions: list[PatternDefinition] = []
    for dimension in ATOMIC_DIMENSIONS:
        if not usable[dimension]:
            continue
        definitions.append(
            PatternDefinition(
                pattern_id=make_pattern_id("atomic", dimension, values[dimension]),
                pattern_kind="atomic",
                dimension_a=dimension,
                value_a=values[dimension],
                eligible_visual=dimension == VISUAL_DIMENSION,
            )
        )
    for dimension_a, dimension_b in COMPOSITE_DIMENSIONS:
        if not (usable[dimension_a] and usable[dimension_b]):
            continue
        definitions.append(
            PatternDefinition(
                pattern_id=make_pattern_id(
                    "composite", dimension_a, values[dimension_a], dimension_b, values[dimension_b]
                ),
                pattern_kind="composite",
                dimension_a=dimension_a,
                value_a=values[dimension_a],
                dimension_b=dimension_b,
                value_b=values[dimension_b],
                eligible_visual=VISUAL_DIMENSION in {dimension_a, dimension_b},
            )
        )
    return tuple(sorted(definitions))


# ---------------------------------------------------------------------------
# Scale profiles: same gates, thresholds sized to the corpus
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class ScaleProfile:
    name: str
    all_scope_floor: int
    family_floor_cap: int
    family_floor_min: int
    family_floor_share: float
    rising_creators_atomic: int
    rising_creators_composite: int
    rising_posts_atomic: int
    rising_posts_composite: int
    scope_spread_creators: int
    emerging_creators: int
    emerging_posts: int
    proven_creators: int
    proven_posts: int
    proven_families: int
    proven_presence: int
    recurring_creators: int
    recurring_posts: int
    high_creators: int
    high_posts: int
    medium_creators: int
    medium_posts: int
    persistence_creators: int
    cooling_returning_supporters: int
    own_proven_posts: int


PROFILES = {
    # The original thresholds, unchanged.
    "full": ScaleProfile(
        name="full",
        all_scope_floor=8,
        family_floor_cap=5,
        family_floor_min=3,
        family_floor_share=0.40,
        rising_creators_atomic=3,
        rising_creators_composite=4,
        rising_posts_atomic=4,
        rising_posts_composite=6,
        scope_spread_creators=3,
        emerging_creators=2,
        emerging_posts=3,
        proven_creators=5,
        proven_posts=8,
        proven_families=2,
        proven_presence=2,
        recurring_creators=3,
        recurring_posts=4,
        high_creators=5,
        high_posts=8,
        medium_creators=3,
        medium_posts=4,
        persistence_creators=3,
        cooling_returning_supporters=3,
        own_proven_posts=1,
    ),
    # One owner, a handful of watched accounts, weeks of data rather than years.
    "member": ScaleProfile(
        name="member",
        all_scope_floor=3,
        family_floor_cap=3,
        family_floor_min=1,
        family_floor_share=0.40,
        rising_creators_atomic=2,
        rising_creators_composite=3,
        rising_posts_atomic=3,
        rising_posts_composite=4,
        scope_spread_creators=2,
        emerging_creators=2,
        emerging_posts=2,
        proven_creators=3,
        proven_posts=5,
        proven_families=2,
        proven_presence=2,
        recurring_creators=2,
        recurring_posts=3,
        high_creators=3,
        high_posts=5,
        medium_creators=2,
        medium_posts=3,
        persistence_creators=2,
        cooling_returning_supporters=2,
        # One of the owner's own winners is a real signal, but it is one post.
        # Two of their own posts carrying the same shape is what "proven" means
        # at this size, so a single win cannot flood the feed.
        own_proven_posts=2,
    ),
}


def family_floor(profile: ScaleProfile, active_creator_count: int) -> int:
    return min(
        profile.family_floor_cap,
        max(profile.family_floor_min, math.ceil(profile.family_floor_share * active_creator_count)),
    )


# ---------------------------------------------------------------------------
# Facts: one per decoded post
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class PostFact:
    shortcode: str
    canonical_url: str
    creator_id: str
    family: str
    published_at: Optional[dt.date]
    published_precision: str
    first_seen_at: Optional[dt.date]
    is_own: bool
    analyzed: bool
    mechanism_entry_path: Optional[str]
    source_extraction_path: Optional[str]
    analysis_flags: tuple[str, ...]
    visual_evidence_mode: str
    patterns: frozenset
    admitted: bool
    fresh: bool
    scanner_gap_exception: bool
    pending_maturation: bool
    best_valid_multiple: Optional[float]
    performance_signal: Optional[float]
    performance_flags: tuple[str, ...]
    source_run_id: Optional[str]
    unusable_reason: str

    @property
    def transcript_available(self) -> bool:
        return bool(self.source_extraction_path) or self.is_own

    @property
    def momentum_eligible(self) -> bool:
        return (
            not self.is_own
            and self.analyzed
            and self.published_at is not None
            and self.published_precision in {"exact", "estimated"}
            and self.fresh
            and self.admitted
            and not self.pending_maturation
            and self.performance_signal is not None
        )

    @property
    def own_qualifying(self) -> bool:
        return self.is_own and self.analyzed and self.admitted and self.performance_signal is not None

    @property
    def clean(self) -> bool:
        return not self.analysis_flags and not self.performance_flags

    def evidence_ref(self) -> dict[str, Any]:
        return {
            "shortcode": self.shortcode,
            "reel_url": self.canonical_url,
            "creator_id": self.creator_id,
            "family": self.family,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "mechanism_entry_path": self.mechanism_entry_path,
            "source_extraction_path": self.source_extraction_path,
            "source_run_id": self.source_run_id,
            "scanner_gap_exception": self.scanner_gap_exception,
        }


def build_facts(
    entries: Iterable[LibraryEntry],
    families: dict[str, str],
    ledger_multiples: dict[str, float],
) -> list[PostFact]:
    facts: list[PostFact] = []
    for entry in entries:
        multiple = entry.multiple
        if multiple is None and entry.is_own and entry.link:
            multiple = ledger_multiples.get(entry.link.rstrip("/"))

        analysis_flags: list[str] = []
        if "caption_only" in entry.flags:
            analysis_flags.append("caption_only")
        if "visual_not_marked_watched" in entry.flags:
            analysis_flags.append("visual_not_marked_watched")

        published = entry.posted_on or entry.filed_on
        precision = "exact" if entry.posted_on else ("estimated" if entry.filed_on else "unknown")
        first_seen = entry.filed_on or entry.posted_on

        if precision == "estimated":
            analysis_flags.append("post_date_unknown")

        age_at_capture: Optional[int] = None
        if entry.posted_on and first_seen:
            age_at_capture = (first_seen - entry.posted_on).days

        fresh = False
        if published is not None and first_seen is not None and precision in {"exact", "estimated"}:
            delay = (first_seen - published).days
            fresh = 0 <= delay <= 7

        pending = False
        valid_multiple = multiple
        if multiple is not None and age_at_capture is not None and age_at_capture < MATURATION_DAYS:
            pending = True
            valid_multiple = None

        admitted = valid_multiple is not None and valid_multiple >= OUTLIER_THRESHOLD
        unusable_reason = ""
        if multiple is None:
            unusable_reason = "no multiple recorded on the entry"
        elif pending:
            unusable_reason = "measured before the post was two days old"
        elif not admitted:
            unusable_reason = "did not beat the account's normal by three times"

        signal = (
            math.log2(1.0 + min(float(valid_multiple), 20.0)) if valid_multiple is not None else None
        )

        definitions = expand_dimensions(
            entry.dimensions, visual_observed=entry.first_frame_observed
        )
        analyzed = bool(definitions)
        if not analyzed and not unusable_reason:
            unusable_reason = "nothing in the entry could be classified"

        facts.append(
            PostFact(
                shortcode=entry.entry_id,
                canonical_url=entry.link,
                creator_id=entry.account,
                family=("own" if entry.is_own else families.get(entry.account, "")),
                published_at=published,
                published_precision=precision,
                first_seen_at=first_seen,
                is_own=entry.is_own,
                analyzed=analyzed,
                mechanism_entry_path=entry.path,
                source_extraction_path=(entry.path if entry.words_source == "transcript" else None),
                analysis_flags=tuple(sorted(set(analysis_flags))),
                visual_evidence_mode=(
                    "observed_frames_ocr" if entry.first_frame_observed else "not_applicable"
                ),
                patterns=frozenset(definition.pattern_id for definition in definitions),
                admitted=admitted,
                fresh=fresh,
                scanner_gap_exception=False,
                pending_maturation=pending,
                best_valid_multiple=valid_multiple,
                performance_signal=signal,
                performance_flags=(),
                source_run_id=None,
                unusable_reason=unusable_reason,
            )
        )
    return facts


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class WindowMetrics:
    start: str
    end: str
    window_days: int
    denominator_creators: int
    eligible_creators: tuple[str, ...]
    denominator_posts: int
    eligible_reel_count: int
    distinct_creator_count: int
    distinct_family_count: int
    creator_coverage: float
    analyzed_winner_share: float
    valid_performance_count: int
    performance_signal: Optional[float]
    clean_support_share: float
    supporting_shortcodes: tuple[str, ...]
    supporting_creators: tuple[str, ...]
    supporting_families: tuple[str, ...]
    evidence_refs: tuple[dict[str, Any], ...]
    newest_bucket_shortcodes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(dataclasses.asdict(self), sort_keys=True))


Interval = tuple[dt.date, dt.date]


def in_window(fact: PostFact, interval: Interval) -> bool:
    return fact.published_at is not None and interval[0] <= fact.published_at < interval[1]


def window_metrics(
    facts: list[PostFact], pattern_id: str, scope: str, interval: Interval, window_days: int
) -> WindowMetrics:
    eligible = [
        fact
        for fact in facts
        if fact.momentum_eligible and in_window(fact, interval) and (scope == "all" or fact.family == scope)
    ]
    support = [fact for fact in eligible if pattern_id in fact.patterns]
    denom_creators = {fact.creator_id for fact in eligible}
    support_creators = {fact.creator_id for fact in support}
    support_families = {fact.family for fact in support if fact.family}
    signals = [fact.performance_signal for fact in support if fact.performance_signal is not None]
    newest_start = interval[1] - dt.timedelta(days=7)
    newest = tuple(
        sorted(fact.shortcode for fact in support if fact.published_at and fact.published_at >= newest_start)
    )
    refs = tuple(fact.evidence_ref() for fact in sorted(support, key=lambda item: item.shortcode))
    return WindowMetrics(
        start=interval[0].isoformat(),
        end=interval[1].isoformat(),
        window_days=window_days,
        denominator_creators=len(denom_creators),
        eligible_creators=tuple(sorted(denom_creators)),
        denominator_posts=len(eligible),
        eligible_reel_count=len(support),
        distinct_creator_count=len(support_creators),
        distinct_family_count=len(support_families),
        creator_coverage=(len(support_creators) / len(denom_creators)) if denom_creators else 0.0,
        analyzed_winner_share=(len(support) / len(eligible)) if eligible else 0.0,
        valid_performance_count=len(signals),
        performance_signal=statistics.median(signals) if signals else None,
        clean_support_share=(sum(fact.clean for fact in support) / len(support)) if support else 0.0,
        supporting_shortcodes=tuple(sorted(fact.shortcode for fact in support)),
        supporting_creators=tuple(sorted(support_creators)),
        supporting_families=tuple(sorted(support_families)),
        evidence_refs=refs,
        newest_bucket_shortcodes=newest,
    )


# ---------------------------------------------------------------------------
# The gates
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class HistoryPoint:
    snapshot_date: dt.date
    momentum_state: str
    evidence_state: str
    persistent: bool
    supporting_creators: tuple[str, ...]
    newest_bucket_shortcodes: tuple[str, ...]
    presence: bool
    cooling_candidate: bool


@dataclasses.dataclass(frozen=True)
class StateResult:
    momentum_state: str
    evidence_state: str
    persistent: bool
    confidence: str
    confidence_ingredients: dict[str, Any]
    gate_receipt: dict[str, Any]


def reference_mean(a: Optional[float], b: Optional[float]) -> Optional[float]:
    values = [value for value in (a, b) if value is not None]
    return (sum(values) / 2.0) if len(values) == 2 else None


def _contiguous_tail(points: list[HistoryPoint], ending: dt.date) -> list[HistoryPoint]:
    by_date = {point.snapshot_date: point for point in points}
    result: list[HistoryPoint] = []
    cursor = ending
    while cursor in by_date:
        result.append(by_date[cursor])
        cursor -= dt.timedelta(days=7)
    return result


def _confidence(
    definition: PatternDefinition,
    current: WindowMetrics,
    reference_a: WindowMetrics,
    reference_b: WindowMetrics,
    profile: ScaleProfile,
    *,
    own_proven: bool,
    analysis_coverage: float,
    momentum_state: str,
) -> tuple[str, dict[str, Any]]:
    creator_post_counts = (
        current.distinct_creator_count >= profile.medium_creators
        and current.eligible_reel_count >= profile.medium_posts
    )
    creator_counts: dict[str, int] = {}
    for ref in current.evidence_refs:
        creator = str(ref["creator_id"])
        creator_counts[creator] = creator_counts.get(creator, 0) + 1
    dominant_share = (
        max(creator_counts.values()) / current.eligible_reel_count
        if creator_counts and current.eligible_reel_count
        else 0.0
    )
    no_creator_dominates = dominant_share <= 0.50
    repeated = reference_a.eligible_reel_count > 0 or reference_b.eligible_reel_count > 0
    material_quality_limit = current.clean_support_share < 0.60 and current.eligible_reel_count > 0
    selection_downgrade = analysis_coverage < 0.50 and bool(
        {definition.dimension_a, definition.dimension_b} & {"format", "visual_open"}
    )
    if (
        current.distinct_creator_count >= profile.high_creators
        and current.eligible_reel_count >= profile.high_posts
        and repeated
        and (current.distinct_family_count >= 2 or own_proven)
        and not material_quality_limit
        and no_creator_dominates
    ):
        confidence = "High"
    elif creator_post_counts and no_creator_dominates and not material_quality_limit:
        confidence = "Medium"
    else:
        confidence = "Low"
    if selection_downgrade:
        confidence = {"High": "Medium", "Medium": "Low", "Low": "Low"}[confidence]
    if momentum_state == "emerging":
        confidence = "Low"
    return confidence, {
        "current_creators": current.distinct_creator_count,
        "current_posts": current.eligible_reel_count,
        "current_families": current.distinct_family_count,
        "clean_support_share": current.clean_support_share,
        "dominant_creator_post_share": dominant_share,
        "no_creator_dominates": no_creator_dominates,
        "repeated_across_windows": repeated,
        "analysis_coverage": analysis_coverage,
        "selection_downgrade": selection_downgrade,
        "own_validation": own_proven,
        "profile": profile.name,
    }


def classify(
    definition: PatternDefinition,
    scope: str,
    snapshot_date: dt.date,
    current: WindowMetrics,
    reference_a: WindowMetrics,
    reference_b: WindowMetrics,
    scans: dict[str, dict[str, Any]],
    profile: ScaleProfile,
    *,
    active_scope_creators: int,
    analysis_coverage: float,
    own_proven: bool,
    weekly_confirmed: bool,
    history: list[HistoryPoint],
    scan_history_measured: bool,
) -> StateResult:
    reference_coverage = (reference_a.creator_coverage + reference_b.creator_coverage) / 2.0
    coverage_delta = current.creator_coverage - reference_coverage
    coverage_ratio = current.creator_coverage / reference_coverage if reference_coverage > 0 else None
    reference_performance = reference_mean(reference_a.performance_signal, reference_b.performance_signal)
    performance_ok = current.performance_signal is not None and (
        reference_performance is None or current.performance_signal >= 0.80 * reference_performance
    )
    floor = profile.all_scope_floor if scope == "all" else family_floor(profile, active_scope_creators)
    denominator_ok = all(
        metric.denominator_creators >= floor for metric in (current, reference_a, reference_b)
    )
    current_scan = float(scans["current"]["coverage"])
    reference_scan = (
        float(scans["reference_a"]["coverage"]) + float(scans["reference_b"]["coverage"])
    ) / 2.0
    scans_present = all(
        int(scans[name]["expected_account_checks"]) > 0
        and int(scans[name]["successful_account_checks"]) > 0
        for name in ("current", "reference_a", "reference_b")
    )
    if scan_history_measured:
        scan_ok = scans_present and reference_scan > 0 and current_scan >= 0.70 * reference_scan
        scan_collapse = reference_scan > 0 and current_scan < 0.70 * reference_scan
    else:
        # No weekly history to compare research runs against yet. Saying "the
        # scan collapsed" would be a guess and saying "the scan is fine" would
        # be a claim. So the gate stays open, the receipt says it is unmeasured,
        # and rising and cooling are withheld below.
        scan_ok = True
        scan_collapse = False

    composite = definition.pattern_kind == "composite"
    rising_count_ok = current.distinct_creator_count >= (
        profile.rising_creators_composite if composite else profile.rising_creators_atomic
    ) and current.eligible_reel_count >= (
        profile.rising_posts_composite if composite else profile.rising_posts_atomic
    )
    scope_spread_ok = (
        current.distinct_family_count >= 2
        if scope == "all"
        else current.distinct_creator_count >= profile.scope_spread_creators
    )
    rising_candidate = (
        rising_count_ok
        and coverage_delta >= 0.10
        and (coverage_ratio is None or coverage_ratio >= 1.50)
        and current.clean_support_share >= 0.60
        and performance_ok
        and scope_spread_ok
    )
    emerging_candidate = (
        current.distinct_creator_count >= profile.emerging_creators
        and current.eligible_reel_count >= profile.emerging_posts
        and (coverage_ratio is None or coverage_ratio >= 1.25)
    )

    prior_strong = any(
        point.momentum_state == "rising" or point.evidence_state == "proven" or point.persistent
        for point in history
    )
    reference_supporters = set(reference_a.supporting_creators) | set(reference_b.supporting_creators)
    current_winner_creators = set(current.eligible_creators)
    returning_supporters = len(reference_supporters & current_winner_creators)
    cooling_candidate = (
        prior_strong
        and reference_coverage > 0
        and current.creator_coverage <= 0.60 * reference_coverage
        and returning_supporters >= profile.cooling_returning_supporters
    )

    virtual = HistoryPoint(
        snapshot_date=snapshot_date,
        momentum_state="stable",
        evidence_state="observed",
        persistent=False,
        supporting_creators=current.supporting_creators,
        newest_bucket_shortcodes=current.newest_bucket_shortcodes,
        presence=current.eligible_reel_count > 0,
        cooling_candidate=cooling_candidate,
    )
    history_for_streak = list(history)
    if weekly_confirmed:
        history_for_streak.append(virtual)
        streak_end = snapshot_date
    elif history:
        streak_end = max(point.snapshot_date for point in history)
    else:
        streak_end = snapshot_date
    streak = _contiguous_tail(history_for_streak, streak_end)
    prior_week = next(
        (point for point in history if point.snapshot_date == snapshot_date - dt.timedelta(days=7)),
        None,
    )
    cooling_confirmed = (
        weekly_confirmed and cooling_candidate and prior_week is not None and prior_week.cooling_candidate
    )

    gate_ok = denominator_ok and scan_ok
    if not gate_ok:
        momentum = "insufficient_data"
    elif cooling_confirmed and scan_history_measured:
        momentum = "cooling"
    elif rising_candidate and scan_history_measured:
        momentum = "rising"
    elif emerging_candidate:
        momentum = "emerging"
    else:
        momentum = "stable"

    presence_count = sum(point.presence for point in streak[:3])
    external_proven = (
        current.distinct_creator_count >= profile.proven_creators
        and current.eligible_reel_count >= profile.proven_posts
        and current.distinct_family_count >= profile.proven_families
        and presence_count >= profile.proven_presence
    )
    if own_proven or external_proven:
        evidence = "proven"
    elif (
        current.distinct_creator_count >= profile.recurring_creators
        and current.eligible_reel_count >= profile.recurring_posts
    ):
        evidence = "recurring"
    else:
        evidence = "observed"

    if weekly_confirmed:
        persistence_points = streak[:3]
        persistent = (
            len(persistence_points) == 3
            and all(point.presence and point.newest_bucket_shortcodes for point in persistence_points)
            and len({creator for point in persistence_points for creator in point.supporting_creators})
            >= profile.persistence_creators
        )
    else:
        persistent = bool(streak and streak[0].persistent)
    if momentum == "cooling":
        persistent = False

    confidence, ingredients = _confidence(
        definition,
        current,
        reference_a,
        reference_b,
        profile,
        own_proven=own_proven,
        analysis_coverage=analysis_coverage,
        momentum_state=momentum,
    )
    return StateResult(
        momentum_state=momentum,
        evidence_state=evidence,
        persistent=persistent,
        confidence=confidence,
        confidence_ingredients=ingredients,
        gate_receipt={
            "profile": profile.name,
            "denominator_floor": floor,
            "denominator_ok": denominator_ok,
            "scan_ok": scan_ok,
            "scan_state": "measured" if scan_history_measured else "unmeasured",
            "scan_collapse": scan_collapse,
            "current_scan_coverage": current_scan,
            "reference_scan_coverage": reference_scan,
            "coverage_delta": coverage_delta,
            "coverage_ratio": coverage_ratio,
            "coverage_ratio_state": "new_in_sample" if coverage_ratio is None else "comparable",
            "reference_performance_signal": reference_performance,
            "performance_ok": performance_ok,
            "rising_count_ok": rising_count_ok,
            "scope_spread_ok": scope_spread_ok,
            "rising_candidate": rising_candidate,
            "rising_withheld_no_history": bool(rising_candidate and not scan_history_measured),
            "emerging_candidate": emerging_candidate,
            "prior_strong": prior_strong,
            "returning_reference_supporters": returning_supporters,
            "cooling_candidate": cooling_candidate,
            "weekly_streak_length": len(streak),
            "external_proven": external_proven,
            "own_proven": own_proven,
        },
    )


# ---------------------------------------------------------------------------
# History file
# ---------------------------------------------------------------------------

def load_history(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    snapshots = payload.get("snapshots")
    return snapshots if isinstance(snapshots, list) else []


def history_points(snapshots: list[dict[str, Any]], record_id: str) -> list[HistoryPoint]:
    points: list[HistoryPoint] = []
    for snapshot in snapshots:
        record = (snapshot.get("records") or {}).get(record_id)
        if not isinstance(record, dict):
            continue
        snapshot_date = None
        try:
            snapshot_date = dt.date.fromisoformat(str(snapshot.get("snapshot_date")))
        except ValueError:
            continue
        points.append(
            HistoryPoint(
                snapshot_date=snapshot_date,
                momentum_state=str(record.get("momentum_state", "insufficient_data")),
                evidence_state=str(record.get("evidence_state", "observed")),
                persistent=bool(record.get("persistent", False)),
                supporting_creators=tuple(record.get("supporting_creators", []) or []),
                newest_bucket_shortcodes=tuple(record.get("newest_bucket_shortcodes", []) or []),
                presence=bool(record.get("presence", False)),
                cooling_candidate=bool(record.get("cooling_candidate", False)),
            )
        )
    return points


def snapshot_near(snapshots: list[dict[str, Any]], target: dt.date, tolerance_days: int = 5):
    best = None
    best_gap = tolerance_days + 1
    for snapshot in snapshots:
        try:
            snapshot_date = dt.date.fromisoformat(str(snapshot.get("snapshot_date")))
        except ValueError:
            continue
        gap = abs((snapshot_date - target).days)
        if gap <= tolerance_days and gap < best_gap:
            best = snapshot
            best_gap = gap
    return best


# ---------------------------------------------------------------------------
# Feed assembly
# ---------------------------------------------------------------------------

def _record_sort_key(record: dict[str, Any]) -> tuple:
    return (
        -CONFIDENCE_RANK[record["confidence"]],
        -record["windows"]["days_14"]["distinct_creator_count"],
        -record["windows"]["days_14"]["eligible_reel_count"],
        record["record_id"],
    )


def _merge_refs(*groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in groups:
        for ref in group:
            merged.setdefault(str(ref["shortcode"]), ref)
    return [merged[key] for key in sorted(merged)]


def _scope_label(scope: str) -> str:
    if scope == "all":
        return "every account you watch"
    return scope.replace("_", " ")


def _collecting_record_ids(records: list[dict[str, Any]]) -> list[str]:
    return [
        record["record_id"]
        for record in records
        if record["momentum_state"] in {"insufficient_data", "emerging"} and bool(record["evidence_refs"])
    ]


def _make_test_next(records: list[dict[str, Any]], snapshot_date: Optional[str]) -> list[dict[str, Any]]:
    if snapshot_date is None:
        return []
    candidates = [
        record
        for record in records
        if (
            record["momentum_state"] == "rising"
            or record["evidence_state"] == "proven"
            or record["persistent"]
        )
        and (CONFIDENCE_RANK[record["confidence"]] >= CONFIDENCE_RANK["Medium"] or record["own_proven"])
        and len(record["evidence_refs"]) >= 2
    ]
    cards: list[dict[str, Any]] = []
    for record in sorted(candidates, key=_record_sort_key)[:5]:
        dimensions = record["pattern"]["dimensions"]
        formats = [item["value"] for item in dimensions if item["dimension"] == "format"]
        cards.append(
            {
                "experiment_id": f"experiment-{record['record_id']}",
                "snapshot_date": snapshot_date,
                "abstract_pattern_name": record["pattern"]["label"],
                "state": {
                    "momentum": record["momentum_state"],
                    "evidence": record["evidence_state"],
                    "persistent": record["persistent"],
                    "confidence": record["confidence"],
                    "scope": record["scope"],
                },
                "why_worth_testing": (
                    f"Confirmed {record['momentum_state']} / {record['evidence_state']} container "
                    f"with {record['windows']['days_14']['distinct_creator_count']} accounts and "
                    f"{record['windows']['days_14']['eligible_reel_count']} posts behind it."
                ),
                "compatible_content_jobs": ["hook", "proof", "retention", "call_to_action"],
                "compatible_formats": formats or ["format_chosen_at_scripting"],
                "evidence_refs": record["evidence_refs"][:5],
                "evidence_counts": {
                    "creators": record["windows"]["days_14"]["distinct_creator_count"],
                    "reels": record["windows"]["days_14"]["eligible_reel_count"],
                    "families": record["windows"]["days_14"]["distinct_family_count"],
                },
                "freshness": record["windows"]["days_14"]["end"],
                "observed_vs_inferred": (
                    "observed_frames_ocr"
                    if record["pattern"]["is_visual"]
                    else "canonical_non_visual_analysis"
                ),
                "do_not_copy_warning": "Use the shape only. Never copy the wording.",
                "source_record_ids": [record["record_id"]],
                "owner_angle": "",
            }
        )
    return cards


def _funnel(facts: list[PostFact], current_interval: Interval) -> tuple[dict[str, int], float]:
    admitted = [fact for fact in facts if fact.admitted]
    admitted_fresh = [fact for fact in admitted if fact.fresh]
    admitted_new_fresh = [fact for fact in admitted_fresh if in_window(fact, current_interval)]
    with_words = [fact for fact in admitted_new_fresh if fact.transcript_available or fact.analyzed]
    analyzed = [fact for fact in with_words if fact.analyzed]
    funnel = {
        "admitted_total": len(admitted),
        "admitted_fresh": len(admitted_fresh),
        "admitted_new_fresh": len(admitted_new_fresh),
        "transcript_available": len(with_words),
        "analyzed": len(analyzed),
    }
    coverage = (len(analyzed) / len(admitted_new_fresh)) if admitted_new_fresh else 0.0
    return funnel, coverage


def build_feed(
    content_os: Path,
    *,
    as_of: dt.date,
    weekly_confirmed: bool,
    profile: ScaleProfile,
    history_path: Path,
    generated_at: Optional[dt.datetime] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    generated_at = generated_at or dt.datetime.now().astimezone()
    entries = read_library_entries(content_os)
    baselines = read_research_state(content_os)
    families = read_watchlist_families(content_os)
    ledger = read_posted_ledger(content_os)

    ledger_multiples = {
        piece.link.rstrip("/"): piece.multiple
        for piece in ledger
        if piece.link and piece.multiple is not None
    }
    facts = build_facts(entries, families, ledger_multiples)

    current_interval = (as_of - dt.timedelta(days=13), as_of + dt.timedelta(days=1))
    days_7_interval = (as_of - dt.timedelta(days=6), as_of + dt.timedelta(days=1))
    days_30_interval = (as_of - dt.timedelta(days=29), as_of + dt.timedelta(days=1))
    reference_a_interval = (as_of - dt.timedelta(days=27), as_of - dt.timedelta(days=13))
    reference_b_interval = (as_of - dt.timedelta(days=41), as_of - dt.timedelta(days=27))

    snapshots = load_history(history_path)
    accounts_total = len(families) or len(baselines) or len({fact.creator_id for fact in facts if not fact.is_own})
    accounts_measured = sum(
        1 for baseline in baselines.values() if baseline.median_views and baseline.measured_on
    )
    current_scan_coverage = (accounts_measured / accounts_total) if accounts_total else 0.0

    def scan_entry(snapshot: Optional[dict[str, Any]]) -> dict[str, Any]:
        if not snapshot:
            return {"expected_account_checks": 0, "successful_account_checks": 0, "coverage": 0.0}
        expected = int(snapshot.get("accounts_total", 0) or 0)
        successful = int(snapshot.get("accounts_measured", 0) or 0)
        coverage = float(snapshot.get("scan_coverage", 0.0) or 0.0)
        return {
            "expected_account_checks": expected,
            "successful_account_checks": successful,
            "coverage": coverage,
        }

    reference_a_snapshot = snapshot_near(snapshots, as_of - dt.timedelta(days=14))
    reference_b_snapshot = snapshot_near(snapshots, as_of - dt.timedelta(days=28))
    scans = {
        "current": {
            "expected_account_checks": accounts_total,
            "successful_account_checks": accounts_measured,
            "coverage": current_scan_coverage,
        },
        "reference_a": scan_entry(reference_a_snapshot),
        "reference_b": scan_entry(reference_b_snapshot),
    }
    scan_history_measured = bool(reference_a_snapshot and reference_b_snapshot)

    scan_exceptions: list[str] = []
    if not scan_history_measured:
        scan_exceptions.append(
            "Fewer than three weekly snapshots exist, so trend comparisons are withheld. "
            "Nothing here can be called rising or cooling yet."
        )
    if accounts_total and accounts_measured < accounts_total:
        scan_exceptions.append(
            f"{accounts_total - accounts_measured} of {accounts_total} watched accounts have no measured normal."
        )
    if not entries:
        scan_exceptions.append("The library is empty, so there is nothing to find patterns in.")

    funnel, analysis_coverage = _funnel(facts, current_interval)

    scopes = ["all"] + sorted({fact.family for fact in facts if fact.family and fact.family != "own"})
    definitions_by_id: dict[str, PatternDefinition] = {}
    for entry in entries:
        for definition in expand_dimensions(
            entry.dimensions, visual_observed=entry.first_frame_observed
        ):
            definitions_by_id.setdefault(definition.pattern_id, definition)

    own_facts = [fact for fact in facts if fact.own_qualifying]
    records: list[dict[str, Any]] = []

    for scope in scopes:
        scope_facts = [fact for fact in facts if scope == "all" or fact.family == scope]
        scope_funnel, scope_coverage = _funnel(scope_facts, current_interval)
        active_scope_creators = len(
            {fact.creator_id for fact in scope_facts if not fact.is_own}
        )
        for pattern_id, definition in sorted(definitions_by_id.items()):
            current = window_metrics(facts, pattern_id, scope, current_interval, 14)
            days_7 = window_metrics(facts, pattern_id, scope, days_7_interval, 7)
            days_30 = window_metrics(facts, pattern_id, scope, days_30_interval, 30)
            reference_a = window_metrics(facts, pattern_id, scope, reference_a_interval, 14)
            reference_b = window_metrics(facts, pattern_id, scope, reference_b_interval, 14)
            own_refs = [fact.evidence_ref() for fact in own_facts if pattern_id in fact.patterns]

            if not (
                current.eligible_reel_count
                or days_30.eligible_reel_count
                or reference_a.eligible_reel_count
                or reference_b.eligible_reel_count
                or own_refs
            ):
                continue

            record_id = make_record_id(pattern_id, scope)
            state = classify(
                definition,
                scope,
                as_of,
                current,
                reference_a,
                reference_b,
                scans,
                profile,
                active_scope_creators=active_scope_creators,
                analysis_coverage=scope_coverage,
                own_proven=len(own_refs) >= profile.own_proven_posts,
                weekly_confirmed=weekly_confirmed,
                history=history_points(snapshots, record_id),
                scan_history_measured=scan_history_measured,
            )
            evidence_refs = _merge_refs(
                current.evidence_refs,
                reference_a.evidence_refs,
                reference_b.evidence_refs,
                days_30.evidence_refs,
                own_refs,
            )
            dimensions = [{"dimension": definition.dimension_a, "value": definition.value_a}]
            if definition.dimension_b and definition.value_b:
                dimensions.append({"dimension": definition.dimension_b, "value": definition.value_b})
            reference_coverage = (reference_a.creator_coverage + reference_b.creator_coverage) / 2.0
            records.append(
                {
                    "record_id": record_id,
                    "pattern_id": pattern_id,
                    "pattern": {
                        "kind": definition.pattern_kind,
                        "label": definition.label,
                        "dimensions": dimensions,
                        "is_visual": definition.is_visual,
                    },
                    "scope": scope,
                    "scope_label": _scope_label(scope),
                    "snapshot_date": as_of.isoformat(),
                    "provisional": not weekly_confirmed,
                    "windows": {
                        "days_7": days_7.as_dict(),
                        "days_14": current.as_dict(),
                        "days_30": days_30.as_dict(),
                    },
                    "references": {
                        "reference_a": reference_a.as_dict(),
                        "reference_b": reference_b.as_dict(),
                    },
                    "comparison": {
                        "reference_creator_coverage": reference_coverage,
                        "creator_coverage_delta": current.creator_coverage - reference_coverage,
                        "coverage_ratio": (
                            current.creator_coverage / reference_coverage if reference_coverage > 0 else None
                        ),
                        "coverage_ratio_state": "comparable" if reference_coverage > 0 else "new_in_sample",
                        "reference_analyzed_winner_share": (
                            reference_a.analyzed_winner_share + reference_b.analyzed_winner_share
                        )
                        / 2.0,
                        "reference_performance_signal": state.gate_receipt["reference_performance_signal"],
                    },
                    "momentum_state": state.momentum_state,
                    "evidence_state": state.evidence_state,
                    "persistent": state.persistent,
                    "confidence": state.confidence,
                    "confidence_ingredients": state.confidence_ingredients,
                    "gate_receipt": state.gate_receipt,
                    "scan_coverage": scans,
                    "selection_funnel": scope_funnel,
                    "analysis_coverage": scope_coverage,
                    "quality": {
                        "clean_support_share": current.clean_support_share,
                        "visual_evidence_mode": (
                            "observed_frames_ocr" if definition.is_visual else "not_applicable"
                        ),
                        "pending_maturation_excluded": sum(
                            fact.pending_maturation and in_window(fact, current_interval) for fact in facts
                        ),
                    },
                    "supporting_shortcodes": sorted({ref["shortcode"] for ref in evidence_refs}),
                    "evidence_refs": evidence_refs,
                    "own_proven": len(own_refs) >= profile.own_proven_posts,
                    "own_evidence_shortcodes": sorted(ref["shortcode"] for ref in own_refs),
                }
            )

    records.sort(key=lambda item: item["record_id"])
    rising_candidates = sorted(
        (record for record in records if record["momentum_state"] == "rising"), key=_record_sort_key
    )
    deduped_rising: list[dict[str, Any]] = []
    seen_patterns: set[str] = set()
    for record in rising_candidates:
        if record["pattern_id"] in seen_patterns:
            continue
        seen_patterns.add(record["pattern_id"])
        deduped_rising.append(record)
    shown_rising = deduped_rising[:5]
    ordered = sorted(records, key=_record_sort_key)
    views = {
        "emerging": [r["record_id"] for r in ordered if r["momentum_state"] == "emerging"],
        "rising": [r["record_id"] for r in shown_rising],
        "proven": [r["record_id"] for r in ordered if r["evidence_state"] == "proven"],
        "persistent": [r["record_id"] for r in ordered if r["persistent"]],
        "cooling": [r["record_id"] for r in ordered if r["momentum_state"] == "cooling"],
    }
    collecting = _collecting_record_ids(records)

    previous_confirmed = None
    for snapshot in snapshots:
        date_text = str(snapshot.get("snapshot_date", ""))
        if date_text and (previous_confirmed is None or date_text > previous_confirmed):
            previous_confirmed = date_text
    last_confirmed = as_of.isoformat() if weekly_confirmed else previous_confirmed
    test_source = records if weekly_confirmed else []

    last_run_dates = [b.last_run for b in baselines.values() if b.last_run]
    measured_dates = [b.measured_on for b in baselines.values() if b.measured_on]
    last_run = max(last_run_dates) if last_run_dates else None
    baseline_as_of = max(measured_dates) if measured_dates else None
    baseline_age_days = (as_of - baseline_as_of).days if baseline_as_of else None

    current_facts = [fact for fact in facts if in_window(fact, current_interval)]
    watched_accounts = len({fact.creator_id for fact in facts if not fact.is_own}) or accounts_total

    scope_note = (
        f"Your own watchlist of {watched_accounts} accounts and your own posts, nothing wider. "
        f"Scale profile: {profile.name}. Research runs weekly, so this feed moves weekly, not hourly."
    )

    feed = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at.isoformat(),
        "as_of_date": as_of.isoformat(),
        "provisional": not weekly_confirmed,
        "last_confirmed_snapshot": last_confirmed,
        "scope_note": scope_note,
        "freshness": {
            # The research run is recorded as a date, not a clock time, so the
            # stamp is that date at the start of the day in local time. The
            # field name is the one the board was written against; it means
            # "the last successful research run".
            "w2_last_success": (
                dt.datetime.combine(last_run, dt.time(0, 0), tzinfo=generated_at.tzinfo).isoformat()
                if last_run
                else None
            ),
            "baseline_as_of": baseline_as_of.isoformat() if baseline_as_of else None,
        },
        "corpus": {
            "eligible_recent": sum(fact.momentum_eligible for fact in current_facts),
            "active_entries": sum(fact.analyzed for fact in facts),
            "creators": watched_accounts,
            "selection_funnel": funnel,
            "analysis_coverage": analysis_coverage,
        },
        "patterns": records,
        "views": views,
        "test_next": _make_test_next(test_source, last_confirmed),
        "collecting_evidence": collecting,
        "quality": {
            "quarantined": sum(1 for fact in facts if fact.unusable_reason),
            "pending_maturation": sum(
                fact.pending_maturation and not fact.is_own for fact in current_facts
            ),
            "visual_observed": sum(
                fact.visual_evidence_mode == "observed_frames_ocr" for fact in facts if fact.analyzed
            ),
            "patterns_evaluated": len(records),
            "atomic_patterns_evaluated": sum(r["pattern"]["kind"] == "atomic" for r in records),
            "composite_patterns_evaluated": sum(r["pattern"]["kind"] == "composite" for r in records),
            "rising_overflow": max(0, len(deduped_rising) - 5),
            "scan_coverage": {
                "current": scans["current"]["coverage"],
                "reference_a": scans["reference_a"]["coverage"],
                "reference_b": scans["reference_b"]["coverage"],
                "state": "measured" if scan_history_measured else "unmeasured",
            },
            "scan_exceptions": scan_exceptions,
            "selection_funnel": funnel,
            "analysis_coverage": analysis_coverage,
            "baseline_age_days": baseline_age_days,
            "current_window_cost_usd": None,
            "expansion": {
                "entries_read": len(entries),
                "entries_usable": sum(1 for fact in facts if not fact.unusable_reason),
                "unusable_reasons": _reason_counts(facts),
                "atomic_patterns": len(
                    [d for d in definitions_by_id.values() if d.pattern_kind == "atomic"]
                ),
                "composite_patterns": len(
                    [d for d in definitions_by_id.values() if d.pattern_kind == "composite"]
                ),
                "own_posts_in_ledger": len(ledger),
            },
        },
    }

    snapshot_record = {
        "snapshot_date": as_of.isoformat(),
        "accounts_total": accounts_total,
        "accounts_measured": accounts_measured,
        "scan_coverage": current_scan_coverage,
        "records": {
            record["record_id"]: {
                "momentum_state": record["momentum_state"],
                "evidence_state": record["evidence_state"],
                "persistent": record["persistent"],
                "supporting_creators": list(record["windows"]["days_14"]["supporting_creators"]),
                "newest_bucket_shortcodes": list(
                    record["windows"]["days_14"]["newest_bucket_shortcodes"]
                ),
                "presence": record["windows"]["days_14"]["eligible_reel_count"] > 0,
                "cooling_candidate": bool(record["gate_receipt"]["cooling_candidate"]),
            }
            for record in records
        },
    }
    return feed, snapshot_record


def _reason_counts(facts: list[PostFact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        if fact.unusable_reason:
            counts[fact.unusable_reason] = counts.get(fact.unusable_reason, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Writing, with a lock and an all-or-nothing replace
# ---------------------------------------------------------------------------

LOCK_STALE_SECONDS = 900


class LockBusy(RuntimeError):
    pass


def acquire_lock(lock_path: Path) -> int:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            age = time.time() - lock_path.stat().st_mtime
        except OSError:
            age = 0.0
        if age > LOCK_STALE_SECONDS:
            try:
                lock_path.unlink()
            except OSError:
                pass
            return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        raise LockBusy(f"another build holds {lock_path}")


def release_lock(handle: int, lock_path: Path) -> None:
    try:
        os.close(handle)
    except OSError:
        pass
    try:
        lock_path.unlink()
    except OSError:
        pass


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".partial")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def append_history(history_path: Path, snapshot_record: dict[str, Any]) -> None:
    snapshots = load_history(history_path)
    snapshots = [
        snapshot
        for snapshot in snapshots
        if str(snapshot.get("snapshot_date")) != snapshot_record["snapshot_date"]
    ]
    snapshots.append(snapshot_record)
    snapshots.sort(key=lambda snapshot: str(snapshot.get("snapshot_date")))
    snapshots = snapshots[-HISTORY_LIMIT:]
    write_json_atomic(
        history_path, {"schema_version": HISTORY_SCHEMA_VERSION, "snapshots": snapshots}
    )


def summarize(feed: dict[str, Any]) -> dict[str, Any]:
    return {
        "as_of_date": feed["as_of_date"],
        "provisional": feed["provisional"],
        "entries_read": feed["quality"]["expansion"]["entries_read"],
        "entries_usable": feed["quality"]["expansion"]["entries_usable"],
        "patterns_evaluated": feed["quality"]["patterns_evaluated"],
        "rising": len(feed["views"]["rising"]),
        "emerging": len(feed["views"]["emerging"]),
        "proven": len(feed["views"]["proven"]),
        "persistent": len(feed["views"]["persistent"]),
        "cooling": len(feed["views"]["cooling"]),
        "collecting_evidence": len(feed["collecting_evidence"]),
        "test_next": len(feed["test_next"]),
        "unusable_reasons": feed["quality"]["expansion"]["unusable_reasons"],
        "honesty_notes": feed["quality"]["scan_exceptions"],
    }


def find_content_os(start: Path) -> Optional[Path]:
    if start.name == "content-os" and start.is_dir():
        return start
    candidate = start / "content-os"
    return candidate if candidate.is_dir() else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the patterns feed from the owner's content-os workspace."
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Folder that contains content-os/ (or the content-os folder itself). Default: here.",
    )
    parser.add_argument("--out", default=None, help="Where to write the feed.")
    parser.add_argument("--history", default=None, help="Where to keep weekly snapshots.")
    parser.add_argument(
        "--confirmed",
        action="store_true",
        help="Mark this as the weekly confirmed build (records a snapshot, unlocks Test next).",
    )
    parser.add_argument("--as-of", default=None, help="Override today's date (YYYY-MM-DD).")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="member")
    parser.add_argument(
        "--dry-run", action="store_true", help="Build and check, write nothing."
    )
    args = parser.parse_args(argv)

    content_os = find_content_os(Path(args.workspace).expanduser().resolve())
    if content_os is None:
        print(
            json.dumps({"error": "no content-os folder found at that location"}),
            file=sys.stderr,
        )
        return 2

    try:
        as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    except ValueError:
        print(json.dumps({"error": "--as-of must look like 2026-08-24"}), file=sys.stderr)
        return 2

    out_path = Path(args.out).expanduser() if args.out else content_os / "analytics" / "patterns.json"
    history_path = (
        Path(args.history).expanduser()
        if args.history
        else content_os / "analytics" / "pattern-history.json"
    )
    profile = PROFILES[args.profile]

    lock_path = out_path.with_suffix(out_path.suffix + ".lock")
    try:
        handle = acquire_lock(lock_path)
    except LockBusy as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 4

    try:
        feed, snapshot_record = build_feed(
            content_os,
            as_of=as_of,
            weekly_confirmed=args.confirmed,
            profile=profile,
            history_path=history_path,
        )
        try:
            validate_feed(feed)
        except FeedValidationError as exc:
            print(
                json.dumps({"error": f"feed failed its own contract check: {exc}"}),
                file=sys.stderr,
            )
            return 3
        if not args.dry_run:
            write_json_atomic(out_path, feed)
            if args.confirmed:
                append_history(history_path, snapshot_record)
    finally:
        release_lock(handle, lock_path)

    print(json.dumps(summarize(feed), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
