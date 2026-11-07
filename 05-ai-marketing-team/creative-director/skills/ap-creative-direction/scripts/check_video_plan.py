#!/usr/bin/env python3
"""Validate a Creative Director video plan without external calls."""

from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path
from typing import Any

MAX_BYTES = 1_000_000
ALLOWED_FORMATS = {
    "short-video",
    "motion-graphics",
    "narrated-video",
    "footage-assembly",
}
ALLOWED_PLAN_STATUS = {"draft", "review-ready"}
ALLOWED_CLAIM_STATUS = {"verified", "owner-statement", "constructed", "excluded"}
ALLOWED_PERMISSION = {"confirmed", "licensed", "not-applicable"}
ALLOWED_REVIEW_STATUS = {"pending", "passed", "failed", "not-applicable"}
REQUIRED_REVIEW_GATES = {
    "message",
    "claims",
    "rights_and_consent",
    "accessibility",
    "full_playback",
}
FORBIDDEN_KEY_PARTS = {
    "api_key",
    "apikey",
    "cookie",
    "credential",
    "password",
    "passwd",
    "secret",
    "session_token",
    "token",
}


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _find_sensitive_keys(value: Any, location: str = "root") -> list[str]:
    findings: list[str] = []
    pending: list[tuple[Any, str]] = [(value, location)]
    while pending:
        current, current_location = pending.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                normalized = str(key).lower().replace("-", "_")
                child_location = f"{current_location}.{key}"
                if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                    findings.append("root: credential-like fields are not allowed")
                pending.append((child, child_location))
        elif isinstance(current, list):
            for index, child in enumerate(current):
                pending.append((child, f"{current_location}[{index}]"))
    return findings


def validate_plan(plan: Any) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one decoded plan."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(plan, dict):
        return ["root: expected a JSON object"], []

    errors.extend(_find_sensitive_keys(plan))

    if plan.get("schema_version") != "1.0":
        errors.append('schema_version: expected "1.0"')
    if not _is_text(plan.get("project")):
        errors.append("project: expected a non-empty string")
    plan_status = plan.get("status")
    if not isinstance(plan_status, str) or plan_status not in ALLOWED_PLAN_STATUS:
        errors.append("status: expected draft or review-ready")
    plan_format = plan.get("format")
    if not isinstance(plan_format, str) or plan_format not in ALLOWED_FORMATS:
        errors.append("format: unsupported production route")

    sources = plan.get("sources")
    source_permissions: dict[str, str] = {}
    if not isinstance(sources, list):
        errors.append("sources: expected a list")
        sources = []
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        raw_source_id = source.get("id")
        if not isinstance(raw_source_id, str) or not raw_source_id.strip():
            errors.append(f"{prefix}.id: expected a non-empty string")
            continue
        source_id = raw_source_id.strip()
        if source_id in source_permissions:
            errors.append(f"{prefix}.id: duplicate source id")
        permission = source.get("permission")
        if not isinstance(permission, str) or permission not in ALLOWED_PERMISSION:
            errors.append(f"{prefix}.permission: expected confirmed, licensed or not-applicable")
        source_permissions[source_id] = str(permission)
        if not _is_text(source.get("kind")):
            errors.append(f"{prefix}.kind: expected a non-empty string")
        if not _is_text(source.get("description")):
            errors.append(f"{prefix}.description: expected a non-empty string")

    claims = plan.get("claims")
    if not isinstance(claims, list):
        errors.append("claims: expected a list")
        claims = []
    for index, claim in enumerate(claims):
        prefix = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        if not _is_text(claim.get("text")):
            errors.append(f"{prefix}.text: expected a non-empty string")
        status = claim.get("status")
        if not isinstance(status, str) or status not in ALLOWED_CLAIM_STATUS:
            errors.append(f"{prefix}.status: unsupported evidence status")
        source_ids = claim.get("source_ids")
        if not isinstance(source_ids, list) or not all(_is_text(item) for item in source_ids):
            errors.append(f"{prefix}.source_ids: expected a list of source ids")
            continue
        source_ids = [item.strip() for item in source_ids]
        if isinstance(status, str) and status in {"verified", "owner-statement"} and not source_ids:
            errors.append(f"{prefix}.source_ids: evidence-bearing claims need a source")
        for source_id in source_ids:
            if source_id not in source_permissions:
                errors.append(f"{prefix}.source_ids: references an undeclared source id")

    people = plan.get("people")
    if not isinstance(people, list):
        errors.append("people: expected a list")
        people = []
    seen_people: set[str] = set()
    for index, person in enumerate(people):
        prefix = f"people[{index}]"
        if not isinstance(person, dict):
            errors.append(f"{prefix}: expected an object")
            continue
        raw_person_id = person.get("id")
        if not isinstance(raw_person_id, str) or not raw_person_id.strip():
            errors.append(f"{prefix}.id: expected a non-empty string")
        elif raw_person_id.strip() in seen_people:
            errors.append(f"{prefix}.id: duplicate person id")
        else:
            person_id = raw_person_id.strip()
            seen_people.add(person_id)
        if not _is_text(person.get("role")):
            errors.append(f"{prefix}.role: expected a non-empty string")
        if person.get("consent") != "confirmed":
            errors.append(f"{prefix}.consent: confirmed consent is required")

    production = plan.get("production")
    if not isinstance(production, dict):
        errors.append("production: expected an object")
    else:
        if not _is_text(production.get("renderer")):
            errors.append("production.renderer: expected a non-empty string or manual")
        for field in ("paid_calls", "publish", "send"):
            value = production.get(field)
            if not isinstance(value, bool):
                errors.append(f"production.{field}: expected true or false")
            elif value:
                errors.append(f"production.{field}: must remain false in this draft package")

    review = plan.get("review")
    if not isinstance(review, dict):
        errors.append("review: expected an object")
    else:
        missing = sorted(REQUIRED_REVIEW_GATES - set(review))
        for field in missing:
            errors.append(f"review.{field}: required review gate is missing")
        for field in sorted(REQUIRED_REVIEW_GATES & set(review)):
            status = review[field]
            if not isinstance(status, str) or status not in ALLOWED_REVIEW_STATUS:
                errors.append(f"review.{field}: unsupported review status")
            elif status == "failed":
                errors.append(f"review.{field}: failed review blocks handoff")
            elif status == "pending":
                if plan.get("status") == "review-ready":
                    errors.append(f"review.{field}: cannot remain pending for review-ready status")
                else:
                    warnings.append(f"review.{field}: still pending")
            elif (
                field == "full_playback"
                and plan.get("status") == "review-ready"
                and status != "passed"
            ):
                errors.append("review.full_playback: must pass before review-ready status")

    return sorted(set(errors)), sorted(set(warnings))


def load_plan(path: Path) -> Any:
    flags = os.O_RDONLY | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        if path.is_symlink():
            raise ValueError("refusing a symbolic link") from error
        raise
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("expected a regular file")
        if file_stat.st_size > MAX_BYTES:
            raise ValueError(f"file exceeds {MAX_BYTES} bytes")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            payload = handle.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError(f"file exceeds {MAX_BYTES} bytes")
        return json.loads(payload.decode("utf-8"), object_pairs_hook=_object_without_duplicates)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Creative Director video plan")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args(argv)

    try:
        plan = load_plan(args.plan)
    except OSError:
        print(json.dumps({"valid": False, "errors": ["input: cannot open or read plan"], "warnings": []}))
        return 2
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        print(json.dumps({"valid": False, "errors": ["input: malformed JSON or unsupported text"], "warnings": []}))
        return 2
    except ValueError as error:
        print(json.dumps({"valid": False, "errors": [f"input: {error}"], "warnings": []}))
        return 2

    try:
        errors, warnings = validate_plan(plan)
    except (RecursionError, TypeError):
        print(json.dumps({"valid": False, "errors": ["input: unsupported value shape"], "warnings": []}))
        return 2
    print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
