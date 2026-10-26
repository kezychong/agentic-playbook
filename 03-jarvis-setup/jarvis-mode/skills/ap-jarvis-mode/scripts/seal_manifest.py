#!/usr/bin/env python3
"""Re-seal the JARVIS Mode package manifest, then verify it.

    python3 scripts/seal_manifest.py <package-root> [--json]

Hashes are never hand-edited. This walks the package, rebuilds the manifest's
``files`` list (path, role, size, SHA-256) and its ``install_mappings`` from
what is actually on disk, keeps every release field the manifest already
carries (name, version, state, gates, notes) exactly as it finds them, writes
the manifest atomically, and then runs the ordinary preflight so a seal that
would not install fails loudly instead of shipping.

Exit status is 0 only when the sealed package passes that preflight.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_package import MANIFEST_NAME, PreflightError, preflight  # noqa: E402

REFUSED_PARTS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".DS_Store"}
RELEASE_FIELDS = (
    "schema_version",
    "package_name",
    "package_version",
    "release_ready",
    "release_state",
    "release_gates",
    "verification_notes",
)
BACKEND_PREFIX = "payload/backend/hermes-jarvis/"
FRONTEND_PLUGIN = "payload/frontend/desktop/plugin.js"
BIN_PREFIX = "payload/bin/"
# The files a main device actually receives. Optional Mac extras (hands) ship
# in the pack but are installed by their own script, never by this mapping.
MAIN_ARTIFACTS = (
    FRONTEND_PLUGIN,
    "payload/bin/jarvis-toggle",
    "payload/bin/jarvis-mirror",
)
REQUIRED_BACKEND_ARTIFACTS = (
    BACKEND_PREFIX + "dashboard/mirror.html",
    BACKEND_PREFIX + "dashboard/mirror.template.html",
    BACKEND_PREFIX + "dashboard/dist/index.js",
)


class SealError(ValueError):
    """Raised when the package cannot be sealed as it stands."""


def _role(relative: Path) -> str:
    path = str(relative)
    if path.startswith(BACKEND_PREFIX):
        return "headless-backend"
    if path == FRONTEND_PLUGIN:
        return "main-frontend"
    if path.startswith(BIN_PREFIX):
        return "main-helper"
    if "tests" in relative.parts:
        return "qa"
    return "source-and-support"


def _collect(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in REFUSED_PARTS for part in relative.parts):
            raise SealError(f"refusing generated or private artifact: {relative} (delete it and seal again; pytest writes these unless it is run with -p no:cacheprovider)")
        if path.is_symlink():
            raise SealError(f"refusing symlink: {relative}")
        if not path.is_file() or str(relative) == MANIFEST_NAME:
            continue
        if not stat.S_ISREG(path.stat().st_mode):
            raise SealError(f"refusing special file: {relative}")
        payload = path.read_bytes()
        entries.append({
            "path": str(relative),
            "role": _role(relative),
            "status": "present",
            "required": True,
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
    return entries


def _mappings(entries: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    mappings: dict[str, list[dict[str, Any]]] = {"main": [], "headless": []}
    for path in MAIN_ARTIFACTS:
        if path not in entries:
            raise SealError(f"required main artifact is missing: {path}")
        target = "desktop-plugins/hermes-jarvis/plugin.js" if path == FRONTEND_PLUGIN else "jarvis/bin/" + Path(path).name
        mappings["main"].append({"package_path": path, "target_relative": target, "role": entries[path]["role"]})
    for path in REQUIRED_BACKEND_ARTIFACTS:
        if path not in entries:
            raise SealError(f"required backend artifact is missing: {path}")
    for path, entry in entries.items():
        if path.startswith(BACKEND_PREFIX):
            mappings["headless"].append({
                "package_path": path,
                "target_relative": "plugins/hermes-jarvis/" + path[len(BACKEND_PREFIX):],
                "role": entry["role"],
            })
    mappings["headless"].sort(key=lambda item: item["package_path"])
    return mappings


def _write_atomic(path: Path, text: str) -> None:
    if path.is_symlink():
        raise SealError("refusing to replace a symlinked manifest")
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(raw, path)
    except Exception:
        try:
            os.unlink(raw)
        except FileNotFoundError:
            pass
        raise


def seal(package_root: str | os.PathLike[str]) -> dict[str, Any]:
    root = Path(os.path.abspath(os.fspath(Path(package_root).expanduser())))
    if not root.is_dir() or root.is_symlink():
        raise SealError(f"package root is not a directory: {package_root}")
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise SealError(f"missing manifest: {MANIFEST_NAME}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SealError(f"cannot read manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise SealError("manifest must be an object")
    missing = [field for field in RELEASE_FIELDS if field not in manifest]
    if missing:
        raise SealError("manifest is missing release fields: " + ", ".join(missing))
    files = _collect(root)
    by_path = {entry["path"]: entry for entry in files}
    sealed = {field: manifest[field] for field in RELEASE_FIELDS}
    sealed["files"] = files
    sealed["install_mappings"] = _mappings(by_path)
    _write_atomic(manifest_path, json.dumps(sealed, indent=2) + "\n")
    return {
        "package_root": str(root),
        "package_name": sealed["package_name"],
        "files": len(files),
        "main_targets": len(sealed["install_mappings"]["main"]),
        "headless_targets": len(sealed["install_mappings"]["headless"]),
        "package_version": sealed["package_version"],
        "release_state": sealed["release_state"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-hash and verify the JARVIS Mode package manifest.")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    args = parser.parse_args()
    try:
        sealed = seal(args.package_root)
        report = preflight(args.package_root)
    except (SealError, PreflightError) as exc:
        print(f"FAIL: {exc}")
        return 1
    combined = {"sealed": sealed, "preflight": report}
    if args.json:
        print(json.dumps(combined, indent=2, sort_keys=True))
        return 0 if report.get("install_ready") else 1
    print(f"sealed {sealed['files']} files in {sealed['package_name']}")
    print(f"- version {sealed['package_version']} ({sealed['release_state']})")
    print(f"- {sealed['main_targets']} main targets, {sealed['headless_targets']} headless targets")
    if report.get("release_ready"):
        print(f"PASS RELEASE: {report.get('files_scanned', 0)} files scanned")
        return 0
    print(f"FAIL: {report.get('files_scanned', 0)} files scanned")
    for error in report.get("errors", []):
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
