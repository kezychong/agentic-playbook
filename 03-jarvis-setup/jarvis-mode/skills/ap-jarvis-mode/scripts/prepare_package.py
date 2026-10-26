#!/usr/bin/env python3
"""Deterministic preflight for the ap-jarvis-mode member package.

This repackage is not a verified release. The original release-only gate is
retained: a package is either independently verified or not installable.
No historical source verification is inherited by these adapted bytes.
Integrity, mapping and gate failures all block.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


MANIFEST_NAME = "package-manifest.json"
SCHEMA_VERSION = 1
RELEASE_STATE = "release"
REQUIRED_RELEASE_GATES = {
    "frontend_source_and_bundle",
    "host_patch_compatibility_proof",
    "licence_and_art_provenance",
    "two_device_install_proof",
    "linux_headless_proof",
}
FORBIDDEN_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".DS_Store",
    "node_modules",
    ".env",
    ".env.local",
}
FORBIDDEN_PARTS = {"private", "secrets", "credentials", "cache", "caches"}


class PreflightError(ValueError):
    """Raised when a package cannot be trusted or is incomplete."""


def _safe_relative(value: str, label: str = "path") -> Path:
    if not isinstance(value, str) or not value:
        raise PreflightError(f"{label} must be a non-empty relative path")
    relative = Path(value)
    if relative.is_absolute() or value.startswith(("/", "\\")):
        raise PreflightError(f"unsafe absolute {label}: {value}")
    if not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise PreflightError(f"unsafe traversal in {label}: {value}")
    if "\\" in value:
        raise PreflightError(f"unsafe separator in {label}: {value}")
    return relative


def _path_is_forbidden(path: Path) -> bool:
    return any(part in FORBIDDEN_NAMES or part.lower() in FORBIDDEN_PARTS for part in path.parts)


def _assert_safe_root(root: Path) -> None:
    """Reject package roots reached through user-controlled symlink ancestors."""
    current = root
    while current != current.parent:
        # macOS exposes temporary trees through these harmless aliases.
        if current.is_symlink() and str(current) not in {"/var", "/tmp"}:
            raise PreflightError(f"package root path contains a symlink: {current}")
        current = current.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(package_root: Path) -> dict[str, Any]:
    manifest_path = package_root / MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise PreflightError(f"missing manifest: {MANIFEST_NAME}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"cannot read manifest: {exc}") from exc
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != SCHEMA_VERSION:
        raise PreflightError("unsupported or missing manifest schema_version")
    if type(data.get("release_ready")) is not bool:
        raise PreflightError("manifest release_ready must be boolean")
    gates = data.get("release_gates")
    if not isinstance(gates, dict):
        raise PreflightError("manifest release_gates must be an object")
    missing_gates = sorted(REQUIRED_RELEASE_GATES - set(gates))
    if missing_gates:
        raise PreflightError("manifest missing release gates: " + ", ".join(missing_gates))
    invalid_gates = sorted(name for name in REQUIRED_RELEASE_GATES if type(gates[name]) is not bool)
    if invalid_gates:
        raise PreflightError("manifest release gates must be boolean: " + ", ".join(invalid_gates))
    if not isinstance(data.get("files"), list):
        raise PreflightError("manifest files must be a list")
    if not isinstance(data.get("install_mappings"), dict):
        raise PreflightError("manifest install_mappings must be an object")
    return data


def _manifest_entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for raw in manifest["files"]:
        if not isinstance(raw, dict):
            raise PreflightError("manifest file entry must be an object")
        rel = str(_safe_relative(raw.get("path"), "manifest file path"))
        if rel == MANIFEST_NAME or rel in entries:
            raise PreflightError(f"manifest cannot list duplicate or manifest path: {rel}")
        role = raw.get("role")
        if not isinstance(role, str) or not role:
            raise PreflightError(f"missing role for {rel}")
        status = raw.get("status", "present")
        if status not in {"present", "missing"}:
            raise PreflightError(f"invalid status for {rel}: {status}")
        if "required" in raw and type(raw["required"]) is not bool:
            raise PreflightError(f"required must be boolean for {rel}")
        expected_hash = raw.get("sha256")
        expected_size = raw.get("size")
        if status == "present":
            if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                raise PreflightError(f"present file lacks SHA-256: {rel}")
            if not isinstance(expected_size, int) or expected_size < 0:
                raise PreflightError(f"present file lacks size: {rel}")
        elif expected_hash is not None or expected_size is not None:
            raise PreflightError(f"missing file must not have hash or size: {rel}")
        entries[rel] = raw
    return entries


def _scan_files(package_root: Path) -> tuple[set[str], list[str]]:
    found: set[str] = set()
    errors: list[str] = []
    for root, dirs, files in os.walk(package_root, followlinks=False):
        root_path = Path(root)
        dirs[:] = sorted(dirs)
        files = sorted(files)
        for name in list(dirs):
            path = root_path / name
            rel = path.relative_to(package_root)
            if path.is_symlink():
                errors.append(f"symlink directory: {rel}")
                dirs.remove(name)
            elif _path_is_forbidden(rel):
                errors.append(f"forbidden directory: {rel}")
                dirs.remove(name)
        for name in files:
            path = root_path / name
            rel_path = path.relative_to(package_root)
            rel = str(rel_path)
            if path.is_symlink():
                errors.append(f"symlink file: {rel}")
                continue
            if not stat.S_ISREG(path.stat().st_mode):
                errors.append(f"non-regular file: {rel}")
                continue
            if _path_is_forbidden(rel_path):
                errors.append(f"forbidden file: {rel}")
                continue
            found.add(rel)
    return found, errors


def verify_install_mappings(manifest: dict[str, Any], entries: dict[str, dict[str, Any]]) -> None:
    for role, raw_mappings in manifest["install_mappings"].items():
        if role not in {"main", "headless"} or not isinstance(raw_mappings, list):
            raise PreflightError(f"invalid install mapping role: {role}")
        seen_targets: set[str] = set()
        for mapping in raw_mappings:
            if not isinstance(mapping, dict):
                raise PreflightError(f"{role} mapping must be an object")
            source = str(_safe_relative(mapping.get("package_path"), "package mapping"))
            target = str(_safe_relative(mapping.get("target_relative"), "target mapping"))
            if source not in entries or entries[source].get("status") != "present":
                raise PreflightError(f"{role} mapping references unavailable file: {source}")
            if target in seen_targets:
                raise PreflightError(f"duplicate {role} target: {target}")
            seen_targets.add(target)
            if mapping.get("role") != entries[source].get("role"):
                raise PreflightError(f"role mismatch for mapping: {source}")


def preflight(package_root: str | os.PathLike[str]) -> dict[str, Any]:
    # abspath normalises ``.`` without following symlinks.  Preserve that
    # distinction so a symlinked package root cannot evade the scan.
    root = Path(os.path.abspath(os.fspath(package_root)))
    _assert_safe_root(root)
    if not root.is_dir() or root.is_symlink():
        raise PreflightError(f"package root is not a directory: {package_root}")
    manifest = load_manifest(root)
    entries = _manifest_entries(manifest)
    found, scan_errors = _scan_files(root)
    integrity_errors = list(scan_errors)
    listed = set(entries)
    # The manifest is checked structurally by ``load_manifest``; it cannot
    # hash itself without a self-reference. Release authenticity is external.
    found.discard(MANIFEST_NAME)
    unknown = sorted(found - listed)
    missing_from_tree = sorted(listed - found)
    present_but_marked_missing = sorted(rel for rel in found & listed if entries[rel].get("status") == "missing")
    integrity_errors.extend(f"unlisted file: {path}" for path in unknown)
    integrity_errors.extend(f"missing file: {path}" for path in missing_from_tree if entries[path].get("status") == "present")
    integrity_errors.extend(f"file present but manifest marks missing: {path}" for path in present_but_marked_missing)
    for rel, entry in sorted(entries.items()):
        path = root / rel
        if entry.get("status") != "present" or not path.is_file() or path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
            continue
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        if actual_size != entry["size"]:
            integrity_errors.append(f"size mismatch: {rel}")
        if actual_hash != entry["sha256"]:
            integrity_errors.append(f"SHA-256 mismatch: {rel}")
    try:
        verify_install_mappings(manifest, entries)
    except PreflightError as exc:
        integrity_errors.append(str(exc))
    for rel, entry in sorted(entries.items()):
        if entry.get("status") == "missing" and entry.get("required", True):
            integrity_errors.append(f"required payload unavailable: {rel}")
    errors = list(integrity_errors)
    if manifest.get("release_state") != RELEASE_STATE:
        errors.append(f"manifest release_state must be {RELEASE_STATE!r}")
    if manifest.get("release_ready") is not True:
        errors.append("release_ready is false")
    for gate, passed in (manifest.get("release_gates") or {}).items():
        if passed is not True:
            errors.append(f"release gate incomplete: {gate}")
    release_ready = manifest.get("release_ready") is True and not errors
    return {
        "package_root": str(root),
        "release_ready": release_ready,
        "release_state": manifest.get("release_state"),
        "install_ready": release_ready,
        "files_scanned": len(found),
        "errors": sorted(set(errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a JARVIS member package before installation.")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    args = parser.parse_args()
    try:
        report = preflight(args.package_root)
    except PreflightError as exc:
        report = {"release_ready": False, "install_ready": False, "files_scanned": 0, "errors": [str(exc)]}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if report.get("release_ready"):
            print(f"PASS RELEASE: {report.get('files_scanned', 0)} files scanned")
        else:
            print(f"FAIL: {report.get('files_scanned', 0)} files scanned")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report.get("install_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
