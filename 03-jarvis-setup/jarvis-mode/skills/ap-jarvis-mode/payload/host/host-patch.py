#!/usr/bin/env python3
"""Apply the packaged full voice chain to an explicitly staged Git tree."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any

HOST_DIR = Path(__file__).resolve().parent
MANIFEST = HOST_DIR / "voice-patch-compatibility.json"
PATCHES = (
    "voice-1-67601e80767.patch", "voice-2-d0903ea0486.patch",
    "voice-3-ccbf400b47d.patch", "voice-4-64f012ac0c.patch",
    "voice-5-ec5a0d4df4d.patch", "voice-6-cf0ecb16df7.patch",
)
MARKER = ".jarvis-staged-tree.json"
LEVEL_NAMES = ("base", "voice-1", "voice-2", "voice-3", "voice-4", "voice-5", "voice-6")

class Refusal(Exception):
    pass

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_manifest() -> dict[str, Any]:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal(f"invalid package manifest: {exc}") from exc

def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        detail = (result.stdout + result.stderr).strip()
        raise Refusal(f"git {' '.join(args)} failed: {detail}")
    return result

def manifest_files(manifest: dict[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for state in manifest["levels"].values():
        for path in (*state["files"], *state.get("absent", [])):
            if path not in paths:
                paths.append(path)
    return tuple(paths)

def assert_no_symlink_components(root: Path, relative: str) -> None:
    candidate = root
    for component in Path(relative).parts:
        candidate /= component
        if candidate.is_symlink():
            raise Refusal(f"symlinked staged path component refused: {relative}")

def validate_stage(root: Path, manifest: dict[str, Any]) -> None:
    if not root.exists() or not root.is_dir() or root.is_symlink():
        raise Refusal("staged root must be a real directory, not a symlink")
    marker = root / MARKER
    if marker.is_symlink() or not marker.is_file():
        raise Refusal(f"missing {MARKER}; create an explicit staging tree first")
    try:
        if json.loads(marker.read_text(encoding="utf-8")).get("kind") != "jarvis-host-staging":
            raise Refusal("staged root marker is not a Jarvis host staging tree")
    except (OSError, ValueError) as exc:
        raise Refusal(f"invalid {MARKER}: {exc}") from exc
    actual = Path(run_git(root, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if actual != root.resolve():
        raise Refusal(f"staged root is not the Git top-level directory: expected {root.resolve()}, got {actual}")
    for relative in manifest_files(manifest):
        assert_no_symlink_components(root, relative)

def changed_paths(root: Path) -> set[str]:
    unstaged = run_git(root, "diff", "--name-only").stdout.splitlines()
    cached = run_git(root, "diff", "--cached", "--name-only").stdout.splitlines()
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return set(unstaged + cached + untracked)

def ensure_only_chain_files_changed(root: Path, manifest: dict[str, Any]) -> None:
    changed = changed_paths(root)
    allowed = set(manifest_files(manifest))
    if not changed.issubset(allowed):
        raise Refusal("refusing unrelated staged-tree changes: " + ", ".join(sorted(changed - allowed)))

def level_files(manifest: dict[str, Any], number: int) -> dict[str, str]:
    return manifest["levels"][LEVEL_NAMES[number]]["files"]

def level(root: Path, manifest: dict[str, Any]) -> int:
    for number in range(len(LEVEL_NAMES) - 1, -1, -1):
        expected = level_files(manifest, number)
        if not all((root / p).is_file() and not (root / p).is_symlink() and digest(root / p) == s for p, s in expected.items()):
            continue
        if any((root / p).exists() for p in manifest["levels"][LEVEL_NAMES[number]].get("absent", [])):
            continue
        return number
    raise Refusal("unsupported host tree: exact source/capability hashes do not match")

def verify_level(root: Path, manifest: dict[str, Any], number: int) -> None:
    bad = []
    for path, expected in level_files(manifest, number).items():
        target = root / path
        if not target.is_file() or target.is_symlink() or digest(target) != expected:
            bad.append(path)
    for path in manifest["levels"][LEVEL_NAMES[number]].get("absent", []):
        if (root / path).exists():
            bad.append(path + " (expected absent)")
    if bad:
        raise Refusal("result did not match package level: " + ", ".join(bad))

def packaged_patch(manifest: dict[str, Any], number: int) -> Path:
    name = PATCHES[number - 1]
    entries = [x for x in manifest["patches"] if x.get("id") == f"voice-{number}"]
    if len(entries) != 1 or entries[0].get("file") != f"payload/host/{name}":
        raise Refusal(f"manifest does not name the packaged voice-{number} patch")
    patch = HOST_DIR / name
    if patch.is_symlink() or not patch.is_file() or patch.resolve().parent != HOST_DIR.resolve():
        raise Refusal(f"packaged voice-{number} patch is missing, symlinked, or misplaced")
    actual = digest(patch)
    expected = entries[0].get("package_sha256")
    if actual != expected:
        raise Refusal(f"packaged voice-{number} patch sha256 mismatch: expected {expected}, got {actual}")
    return patch

def apply_one(root: Path, manifest: dict[str, Any], number: int, reverse: bool = False) -> None:
    patch = packaged_patch(manifest, number)
    command = ["apply"] + (["--reverse"] if reverse else [])
    run_git(root, *command, "--check", str(patch))
    run_git(root, *command, str(patch))

def target_number(value: str, full: bool = False) -> int:
    aliases = {"base": 0, "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6}
    if full:
        aliases["full"] = 6
    if value in aliases:
        return aliases[value]
    try:
        number = int(value)
    except ValueError as exc:
        raise Refusal(f"invalid patch level: {value}") from exc
    if 0 <= number <= 6:
        return number
    raise Refusal(f"invalid patch level: {value}")

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-root", required=True, type=Path)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--revert", action="store_true")
    parser.add_argument("--through", choices=("1","2","3","4","5","6","first","second","third","fourth","fifth","sixth","full"), default="full")
    parser.add_argument("--to", choices=("0","1","2","3","4","5","base","first","second","third","fourth","fifth"), default="base")
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    requested = args.staged_root.expanduser().absolute()
    root: Path | None = None
    manifest: dict[str, Any] | None = None
    mutated: list[tuple[int, bool]] = []
    try:
        root = requested.resolve(strict=True)
        if root != requested:
            raise Refusal("staged root or one of its parent directories is symlinked")
        manifest = load_manifest()
        validate_stage(root, manifest)
        current = level(root, manifest)
        if args.check:
            ensure_only_chain_files_changed(root, manifest)
            print(f"host patch level: {LEVEL_NAMES[current]}")
            return 0
        if args.apply:
            target = target_number(args.through, True)
            if target < current:
                raise Refusal(
                    f"cannot apply down to {LEVEL_NAMES[target]} from {LEVEL_NAMES[current]}; "
                    "use --revert for a lower level"
                )
            if current == 0 and changed_paths(root):
                raise Refusal("staged tree must be clean before applying the first patch")
            if current > 0:
                ensure_only_chain_files_changed(root, manifest)
            for number in range(current + 1, target + 1):
                apply_one(root, manifest, number)
                mutated.append((number, False))
                verify_level(root, manifest, number)
            print(f"host patches applied through {LEVEL_NAMES[target]}")
            return 0
        target = target_number(args.to)
        if target > current:
            raise Refusal(
                f"cannot revert up to {LEVEL_NAMES[target]} from {LEVEL_NAMES[current]}; "
                "use --apply for a higher level"
            )
        ensure_only_chain_files_changed(root, manifest)
        for number in range(current, target, -1):
            apply_one(root, manifest, number, True)
            mutated.append((number, True))
            verify_level(root, manifest, number - 1)
        print(f"host patches reverted to {LEVEL_NAMES[target]}")
        return 0
    except Refusal as exc:
        rollback_errors: list[str] = []
        if root is not None and manifest is not None:
            for number, was_reversed in reversed(mutated):
                try:
                    apply_one(root, manifest, number, not was_reversed)
                except Refusal as rollback_error:
                    rollback_errors.append(f"voice-{number}: {rollback_error}")
        if root is not None and manifest is not None:
            try:
                state = LEVEL_NAMES[level(root, manifest)]
            except Refusal as state_error:
                state = f"unknown ({state_error})"
        else:
            state = "unknown (staged root was not accepted)"
        if rollback_errors:
            print(f"unsupported/refused: {exc}; ROLLBACK INCOMPLETE; current patch level: {state}; rollback errors: {' | '.join(rollback_errors)}", file=sys.stderr)
            return 3
        print(f"unsupported/refused: {exc}; rollback complete; current patch level: {state}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
