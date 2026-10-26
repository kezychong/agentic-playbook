#!/usr/bin/env python3
"""Run the optional Talk presence patch only inside a marked staged tree.

The upstream helper is retained verbatim beside this wrapper. The wrapper
takes an on-disk byte backup first and restores it even when the builder leaves
a broken tree. It rejects symlinks and unrelated file changes.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "patch-talk-presence.py"
MARKER = ".jarvis-talk-staged-tree.json"
ALLOWED = {
    "ui/talk-surface.js",
    "ui/.hermes-jarvis-presence.orig.sha256",
    "desktop/plugin.js",
    "dashboard/dist/index.js",
}


class Refusal(Exception):
    pass


def scan(root: Path) -> dict[str, bytes]:
    if not root.is_dir() or root.is_symlink():
        raise Refusal("Talk staged root must be a real directory")
    files: dict[str, bytes] = {}
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            path = current_path / name
            if path.is_symlink():
                raise Refusal(f"symlinked directory refused: {path.relative_to(root)}")
        for name in names:
            path = current_path / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                raise Refusal(f"symlinked file refused: {relative}")
            files[relative] = path.read_bytes()
    marker = root / MARKER
    if not marker.is_file() or marker.is_symlink():
        raise Refusal(f"missing {MARKER}; create an explicit staged tree first")
    return files


def make_backup(backup_root: Path, snapshot: dict[str, bytes]) -> None:
    for relative, content in snapshot.items():
        path = backup_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def clear_and_restore(root: Path, snapshot: dict[str, bytes], backup_root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        raise Refusal("cannot restore: Talk staged root is no longer a real directory")
    present: set[str] = set()
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            path = current_path / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                path.unlink()
                dirs.remove(name)
            else:
                present.add(relative)
        for name in names:
            path = current_path / name
            relative = str(path.relative_to(root))
            present.add(relative)
            if path.is_symlink():
                path.unlink()
    for relative in present - set(snapshot):
        path = root / relative
        if path.is_file() or path.is_symlink():
            path.unlink()
    for relative in snapshot:
        path = root / relative
        if path.is_symlink():
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        backup = (backup_root / relative).read_bytes()
        if not path.is_file() or path.read_bytes() != backup:
            path.write_bytes(backup)


def restore_or_refuse(root: Path, snapshot: dict[str, bytes], backup_root: Path, reason: str) -> None:
    try:
        clear_and_restore(root, snapshot, backup_root)
    except (OSError, Refusal) as restore_error:
        raise Refusal(
            f"{reason}; ROLLBACK INCOMPLETE: {restore_error}; "
            f"durable backup retained at {backup_root}"
        ) from restore_error


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--talk-staged-root", required=True, type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--revert", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    requested = args.talk_staged_root.expanduser().absolute()
    try:
        root = requested.resolve(strict=True)
        if root != requested:
            raise Refusal("Talk staged root or one of its parent directories is symlinked")
    except (OSError, Refusal) as exc:
        print(f"unsupported/refused: cannot resolve Talk staged root: {exc}", file=sys.stderr)
        return 2
    backup_root = Path(tempfile.mkdtemp(prefix="jarvis-talk-backup-"))
    retain_backup = False
    try:
        before = scan(root)
        make_backup(backup_root, before)
        if not (root / "ui/talk-surface.js").is_file():
            raise Refusal("ui/talk-surface.js is missing")
        command = [sys.executable, str(SCRIPT), "--talk", str(root)]
        command.append("--apply" if args.apply else "--check" if args.check else "--revert")
        if args.no_build:
            command.append("--no-build")
        if args.dry_run:
            command.append("--dry-run")
        result = subprocess.run(command, capture_output=True, text=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        try:
            after = scan(root)
        except Refusal as scan_error:
            try:
                restore_or_refuse(
                    root, before, backup_root,
                    f"post-helper scan failed: {scan_error}; restoration attempted",
                )
            except Refusal as restore_error:
                if "ROLLBACK INCOMPLETE" in str(restore_error):
                    retain_backup = True
                raise
            raise Refusal(f"post-helper scan failed: {scan_error}; staged tree restored")
        changed = {
            path for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        }
        if not changed.issubset(ALLOWED):
            try:
                restore_or_refuse(
                    root, before, backup_root,
                    "unrelated Talk tree change detected; restoration attempted",
                )
            except Refusal as restore_error:
                if "ROLLBACK INCOMPLETE" in str(restore_error):
                    retain_backup = True
                raise
            raise Refusal("unrelated Talk tree change detected; staged tree restored")
        if args.check:
            if changed:
                try:
                    restore_or_refuse(
                        root, before, backup_root,
                        "Talk check changed the staged tree; restoration attempted",
                    )
                except Refusal as restore_error:
                    if "ROLLBACK INCOMPLETE" in str(restore_error):
                        retain_backup = True
                    raise
                raise Refusal("Talk check changed the staged tree; staged tree restored")
            return result.returncode
        if result.returncode:
            try:
                restore_or_refuse(
                    root, before, backup_root,
                    "Talk staged tree helper failed; restoration attempted",
                )
            except Refusal as restore_error:
                if "ROLLBACK INCOMPLETE" in str(restore_error):
                    retain_backup = True
                raise
            print("Talk staged tree restored after helper failure", file=sys.stderr)
            return result.returncode
        print("Talk staged tree change is reversible and limited to allowed files")
        return 0
    except Refusal as exc:
        print(f"unsupported/refused: {exc}", file=sys.stderr)
        return 2
    finally:
        if not retain_backup:
            shutil.rmtree(backup_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
