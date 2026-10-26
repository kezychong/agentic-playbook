"""Schema validation plus cross-record fail-closed invariants for the patterns feed.

Ported from the proven original with two changes and nothing else:

  1. No database. The original also cross-checked the feed against a long-lived
     database of scraped posts. This version reads a workspace of markdown
     files, so the database check has no counterpart and is dropped.
  2. The blank-angle field is named ``owner_angle``. It carries the same rule:
     the owner's angle is never written by a machine, so the field must stay
     an empty string in every generated card.

Everything else, the schema walk, the cross-record invariants, the monotone
selection funnel, the coverage arithmetic check, the evidence-must-match rule,
the visual-evidence rule, the five-item Rising cap, is the original logic.

Pure standard library. No network, no files written.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
from typing import Any


SCHEMA_PATH = pathlib.Path(__file__).with_name("schemas") / "patterns-feed.schema.json"

_COMPACT_UTC_OFFSET_RE = re.compile(r"([+-]\d{2})(\d{2})$")


class FeedValidationError(ValueError):
    pass


def parse_iso8601_datetime(value: str) -> dt.datetime:
    """Parse the timestamp forms this system writes, on any supported runtime.

    Older runtimes reject a trailing ``Z`` and compact offsets such as
    ``+0800``. Normalize only that syntax; keep the represented offset intact
    so callers retain exact timezone truth.
    """
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    normalized = _COMPACT_UTC_OFFSET_RE.sub(r"\1:\2", normalized)
    return dt.datetime.fromisoformat(normalized)


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }[expected]


def _schema_validate(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    expected = schema.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, choice) for choice in choices):
            raise FeedValidationError(f"{path}: expected {choices}, got {type(value).__name__}")
    if "enum" in schema and value not in schema["enum"]:
        raise FeedValidationError(f"{path}: value is outside enum")
    if "const" in schema and value != schema["const"]:
        raise FeedValidationError(f"{path}: value does not match const")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise FeedValidationError(f"{path}: missing required keys {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                raise FeedValidationError(f"{path}: unexpected keys {extras}")
        for key, child in properties.items():
            if key in value:
                _schema_validate(value[key], child, f"{path}.{key}")
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            raise FeedValidationError(f"{path}: too few items")
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            raise FeedValidationError(f"{path}: too many items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(encoded) != len(set(encoded)):
                raise FeedValidationError(f"{path}: duplicate items")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _schema_validate(item, item_schema, f"{path}[{index}]")
    if isinstance(value, str):
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise FeedValidationError(f"{path}: string does not match pattern")
        if schema.get("format") == "date":
            try:
                dt.date.fromisoformat(value)
            except ValueError as exc:
                raise FeedValidationError(f"{path}: invalid date") from exc
        if schema.get("format") == "date-time":
            try:
                parsed = parse_iso8601_datetime(value)
            except ValueError as exc:
                raise FeedValidationError(f"{path}: invalid timestamp") from exc
            if parsed.tzinfo is None:
                raise FeedValidationError(f"{path}: timestamp needs a timezone")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise FeedValidationError(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise FeedValidationError(f"{path}: above maximum")


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def validate_feed(feed: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    _schema_validate(feed, schema)
    records = feed["patterns"]
    record_ids = [record["record_id"] for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise FeedValidationError("duplicate (pattern, scope) record ID")
    valid_ids = set(record_ids)
    for view_name, ids in feed["views"].items():
        if len(ids) != len(set(ids)) or not set(ids) <= valid_ids:
            raise FeedValidationError(f"view {view_name} has duplicate or unknown IDs")
    collecting = feed["collecting_evidence"]
    if len(collecting) != len(set(collecting)) or not set(collecting) <= valid_ids:
        raise FeedValidationError("collecting_evidence has duplicate or unknown IDs")
    surfaced_ids = set(collecting)
    for ids in feed["views"].values():
        surfaced_ids.update(ids)
    if len(feed["views"]["rising"]) > 5:
        raise FeedValidationError("Rising display exceeds five")
    funnel = feed["corpus"]["selection_funnel"]
    values = [
        funnel["admitted_total"],
        funnel["admitted_fresh"],
        funnel["admitted_new_fresh"],
        funnel["transcript_available"],
        funnel["analyzed"],
    ]
    if values != sorted(values, reverse=True):
        raise FeedValidationError("selection funnel is not monotone")
    expected_coverage = (
        funnel["analyzed"] / funnel["admitted_new_fresh"]
        if funnel["admitted_new_fresh"]
        else 0.0
    )
    if abs(feed["corpus"]["analysis_coverage"] - expected_coverage) > 1e-12:
        raise FeedValidationError("analysis coverage disagrees with funnel")
    for record in records:
        evidence = record["evidence_refs"]
        shortcodes = [item["shortcode"] for item in evidence]
        if len(shortcodes) != len(set(shortcodes)):
            raise FeedValidationError(f"{record['record_id']}: duplicate evidence shortcode")
        if record["record_id"] in surfaced_ids:
            if not evidence:
                raise FeedValidationError(f"{record['record_id']}: surfaced pattern needs evidence refs")
            if set(shortcodes) != set(record["supporting_shortcodes"]):
                raise FeedValidationError(
                    f"{record['record_id']}: evidence refs do not exactly match supporting shortcodes"
                )
        if record["pattern"]["is_visual"]:
            if record["quality"]["visual_evidence_mode"] != "observed_frames_ocr":
                raise FeedValidationError("inferred visual observation entered pattern math")
    confirmed = feed["last_confirmed_snapshot"]
    for card in feed["test_next"]:
        if card["snapshot_date"] != confirmed:
            raise FeedValidationError("Test next is not pinned to latest confirmed snapshot")
        if card["owner_angle"] != "":
            raise FeedValidationError("Owner angle must remain blank")
        if not (2 <= len(card["evidence_refs"]) <= 5):
            raise FeedValidationError("Test next needs 2-5 evidence refs")
        if not set(card["source_record_ids"]) <= valid_ids:
            raise FeedValidationError("confirmed Test next refers to unknown record")
    banned = "satur" + "ated"
    if any(banned in text.lower() for text in _walk_strings(feed)):
        raise FeedValidationError("banned fatigue claim in generated feed")
