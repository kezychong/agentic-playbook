#!/usr/bin/env python3
"""Validate a portable Base Schema build manifest.

Usage:
    python scripts/check_manifest.py MANIFEST [--for-build] [--previous PREVIOUS]

Exit 0 means the manifest is valid (warnings may remain), exit 1 means validation
errors, and exit 2 means the checker could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_DIR / "templates" / "build-manifest.schema.json"
META_TABLES = {"settings", "record_home", "import_guard", "import_log", "period"}


def ensure_jsonschema(_script: Path, _argv: list[str]) -> None:
    """Fail with a portable install hint when jsonschema is unavailable."""
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print("could not run: install the 'jsonschema' package in this Python environment")
        raise SystemExit(2)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_portable_relative(value: str) -> bool:
    """Accept a project-relative POSIX-style path with no traversal."""
    if not value or value.startswith(("/", "~", "\\")) or re.match(r"^[A-Za-z]:", value):
        return False
    path = PurePosixPath(value.replace("\\", "/"))
    return ".." not in path.parts and "." not in path.parts


def check(manifest_path: Path, for_build: bool = False, previous: Path | None = None, _unused: Path | None = None):
    """Return (manifest, errors, warnings, notes)."""
    from jsonschema import Draft202012Validator, FormatChecker

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"can't read JSON: {exc}"], warnings, notes

    validation_errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
        key=lambda exc: list(exc.absolute_path),
    )
    for exc in validation_errors:
        where = "/".join(str(part) for part in exc.absolute_path) or "(top)"
        errors.append(f"schema: {where}: {exc.message[:200]}")
    if errors:
        return manifest, errors, warnings, notes

    base = manifest_path.resolve().parent
    checkpoints = manifest["checkpoints"]
    checkpoint_ids = [checkpoint["id"] for checkpoint in checkpoints]
    lines = manifest["record_home_map"]
    tables = {line["table"]: line for line in lines if line["table"]}
    metric_ids = [metric["id"] for metric in manifest["acceptance"]["metrics"]]

    for field in (manifest["blueprint"], manifest["target"]["db_path"], manifest["rollback"]["backup_dir"]):
        if not is_portable_relative(field):
            errors.append(f"path must be project-relative with no traversal: {field!r}")

    for label, identifiers in (
        ("checkpoint", checkpoint_ids),
        ("blocker", [item["id"] for item in manifest["blockers"]]),
        ("fixture", [item["id"] for item in manifest["acceptance"]["fixtures"]]),
        ("metric", metric_ids),
        ("migration", [item["id"] for item in manifest["migrations"]]),
        ("record kind", [item["kind"] for item in lines]),
        ("table", [item["table"] for item in lines if item["table"]]),
    ):
        duplicates = sorted({value for value in identifiers if identifiers.count(value) > 1})
        if duplicates:
            errors.append(f"{label} used twice: {', '.join(duplicates)}")

    expected_from = 0
    for migration in manifest["migrations"]:
        if migration["from_version"] != expected_from or migration["to_version"] != migration["from_version"] + 1:
            errors.append(
                f"{migration['id']}: goes {migration['from_version']}→{migration['to_version']}, "
                f"expected {expected_from}→{expected_from + 1}"
            )
        expected_from = migration["to_version"]
        for direction in ("up", "down"):
            relative = migration[f"{direction}_file"]
            path = (base / relative).resolve()
            if base not in path.parents:
                errors.append(f"{migration['id']} {direction}: path escapes the manifest folder")
                continue
            digest = migration[f"{direction}_sha256"]
            if digest is None:
                message = f"{migration['id']} {direction}: not written or fingerprinted ({relative})"
                if path.is_file():
                    message += f"; current sha256 {sha256_file(path)}"
                (errors if for_build else warnings).append(message)
            elif not path.is_file():
                errors.append(f"{migration['id']} {direction}: {relative} is missing")
            elif sha256_file(path) != digest:
                errors.append(f"{migration['id']} {direction}: {relative} changed since fingerprinting")
    if expected_from != manifest["target"]["user_version_after_build"]:
        errors.append(
            f"migrations end at version {expected_from}, target says "
            f"{manifest['target']['user_version_after_build']}"
        )

    if checkpoints[0]["kind"] != "preflight":
        errors.append("the first checkpoint must be preflight")
    kinds = [checkpoint["kind"] for checkpoint in checkpoints]
    if "migrate" in kinds and (
        "rehearse_on_copy" not in kinds or kinds.index("rehearse_on_copy") > kinds.index("migrate")
    ):
        errors.append("rehearse_on_copy must come before the first migrate checkpoint")
    used_migrations = [checkpoint.get("migration") for checkpoint in checkpoints if checkpoint["kind"] == "migrate"]
    migration_ids = {migration["id"] for migration in manifest["migrations"]}
    for migration in manifest["migrations"]:
        count = used_migrations.count(migration["id"])
        if count != 1:
            errors.append(f"{migration['id']} must have exactly one migrate checkpoint (found {count})")
    for checkpoint in checkpoints:
        if checkpoint.get("migration") and checkpoint["migration"] not in migration_ids:
            errors.append(f"{checkpoint['id']}: migration {checkpoint['migration']} does not exist")
    for blocker in manifest["blockers"]:
        for checkpoint_id in blocker["blocks"]:
            if checkpoint_id not in checkpoint_ids:
                errors.append(f"{blocker['id']}: blocks missing checkpoint {checkpoint_id}")
        if blocker["status"] == "open":
            message = (
                f"open blocker {blocker['id']} stops {', '.join(blocker['blocks'])} "
                f"until answered ({blocker['ask_who']}): {blocker['ask']}"
            )
            if for_build:
                errors.append(message)
            else:
                notes.append(f"build stops at {', '.join(blocker['blocks'])} until {blocker['id']} is answered "
                             f"({blocker['ask_who']}): {blocker['ask']}")

    built: set[str] = set()
    for checkpoint in checkpoints:
        if checkpoint["kind"] != "migrate":
            continue
        for readback in checkpoint["readback"]:
            if readback["check"] in ("tables_exist", "views_exist"):
                target = readback["target"]
                built.update([target] if isinstance(target, str) else target)
    for table in tables:
        if table not in built:
            errors.append(f"table {table} is in the map but no migrate checkpoint reads it back")
    for metric in manifest["acceptance"]["metrics"]:
        if metric["answered_by"] not in built:
            warnings.append(f"{metric['id']}: view {metric['answered_by']} is absent from migrate readbacks")
    for line in lines:
        for metric_id in line["freshness"]["read_by"]:
            if metric_id not in metric_ids:
                errors.append(f"{line['kind']}: freshness references missing metric {metric_id}")
        if line["role"] == "mirror" and line["freshness"]["max_age_days"] is None:
            warnings.append(f"{line['kind']}: copy freshness is not set")

    rows_by_table: dict[str, list[dict]] = {}
    for fixture in manifest["acceptance"]["fixtures"]:
        for table, rows in fixture["rows"].items():
            if table not in tables and table not in META_TABLES:
                errors.append(f"{fixture['id']}: rows target {table}, which is absent from the map")
            rows_by_table.setdefault(table, []).extend(rows)
    for table, line in tables.items():
        rows = rows_by_table.get(table, [])
        if line["role"] == "mirror":
            if not rows:
                errors.append(f"copy table {table} has no fictional fixture rows")
            if any("source_ref" not in row for row in rows):
                errors.append(f"copy table {table}: every fixture row needs source_ref")
        if line["role"] == "intake" and not any(row.get("handed_over_on") for row in rows):
            warnings.append(f"request table {table}: no handed-over fixture row")
        if line["role"] == "snapshot" and not rows:
            warnings.append(f"frozen-figure table {table}: no fixture row")

    if previous is not None:
        try:
            prior = json.loads(previous.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"can't read previous manifest: {exc}")
        else:
            if prior.get("build_id") != manifest["build_id"]:
                errors.append("previous manifest is for a different build")
            if prior.get("revision") != manifest["revision"] - 1:
                errors.append(
                    f"previous manifest is revision {prior.get('revision')}, expected {manifest['revision'] - 1}"
                )
            if manifest["supersedes_sha256"] != sha256_file(previous):
                errors.append("supersedes_sha256 does not match the previous manifest")
    elif manifest["revision"] > 1:
        message = f"revision {manifest['revision']} requires --previous to prove the exact revision chain"
        (errors if for_build else warnings).append(message)

    if for_build and manifest["approval"]["state"] != "approved_for_build":
        errors.append("not approved for build: record explicit owner approval first")
    return manifest, errors, warnings, notes


def main(argv: list[str]) -> int:
    ensure_jsonschema(Path(__file__).resolve(), argv)
    parser = argparse.ArgumentParser(description="Check a Base Schema build manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--for-build", action="store_true")
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args(argv)
    manifest, errors, warnings, notes = check(args.manifest, args.for_build, args.previous)
    for item in errors:
        print(f"ERROR  {item}")
    for item in warnings:
        print(f"WARN   {item}")
    for item in notes:
        print(f"NOTE   {item}")
    label = manifest["build_id"] if isinstance(manifest, dict) and "build_id" in manifest else args.manifest.name
    print(f"{label}: {len(errors)} error(s), {len(warnings)} warning(s){' — for build' if args.for_build else ''}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
