#!/usr/bin/env python3
"""Apply, check or revert the hermes-jarvis presence-bus patch on a hermes-talk root.

The patch inserts one marker-delimited block into ``ui/talk-surface.js`` (inside
``TalkPage``, right after the state hooks) that:

  * dispatches a ``hermes-talk:presence`` CustomEvent on ``window`` whenever
    phase / live / audioActivity / transcript / muted / sleeping change, and
  * listens for ``hermes-talk:command`` and maps
    ``start|stop|mute|unmute|sleep|wake`` onto Talk's own
    ``startTalk`` / ``stopTalk`` / ``setMuted`` / ``setSleeping``.

Nothing else in the file changes. Talk behaves identically when nobody listens.

Usage
-----
    python3 scripts/patch-talk-presence.py --talk <hermes-talk root> --apply
    python3 scripts/patch-talk-presence.py --talk <hermes-talk root> --check
    python3 scripts/patch-talk-presence.py --talk <hermes-talk root> --revert
    ... plus --no-build (skip scripts/build_ui.py) and --dry-run (print the diff only)

Revert safety
-------------
The revert itself is deterministic: the block is marker-delimited, so removing
exactly those lines restores the file. ``--apply`` additionally records the
sha256 of the ORIGINAL ``ui/talk-surface.js`` in
``ui/.hermes-jarvis-presence.orig.sha256`` (shasum format) so the restore can be
PROVED rather than assumed:

* sidecar present and the hashes agree -> the file is written, the sidecar is
  deleted, exit 0;
* sidecar present and the hashes differ -> the file drifted while patched;
  nothing is written, exit 4;
* sidecar absent (someone deleted it, or the patch was applied by hand) -> the
  marked block is still removed and the bundles are still rebuilt, but the
  restore is NOT hash-verified: exit 0 with a notice saying so. Run ``--check``
  afterwards, and diff against upstream if the root is a git checkout.

The sidecar is local tooling state and is never part of the upstream PR.

The surface file is read and written as bytes (decoded/encoded UTF-8, no newline
translation), so a hash always describes what is on disk. Upstream pins these
sources to LF in .gitattributes; a CRLF copy fails the anchor match and exits 2
rather than being silently rewritten.

Exit codes
----------
0  success (patched / already patched / reverted, verified or not / not patched
   under --revert; and, for --check, the file IS patched)
1  --check only: anchors are present but the file is not patched
2  anchors missing, duplicated, or half-marked -> unknown Talk version, refuse
3  the build needs dashboard/dist/style.css and it is missing
4  --revert: a sidecar exists and the restored bytes do not match it, so nothing
   is written
5  scripts/build_ui.py failed
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

SURFACE = "ui/talk-surface.js"
SIDECAR = "ui/.hermes-jarvis-presence.orig.sha256"
BUILDER = "scripts/build_ui.py"
STYLE = "dashboard/dist/style.css"
DESKTOP_ENTRY = "ui/desktop-entry.js"
GENERATED = ("desktop/plugin.js", "dashboard/dist/index.js")

BEGIN = "    // hermes-jarvis presence-bus BEGIN\n"
END = "    // hermes-jarvis presence-bus END\n"

# The insertion point: the tail of TalkPage's state hooks. The block goes right
# after this, before `const transportRef = useRef(null);`.
ANCHOR_INSERT_AFTER = (
    '    const [audioActivity, setAudioActivity] = useState({ input: false, output: false });\n'
    '    const [appearance, updateAppearance] = useState({ skin: "system", animate: false,\n'
    "      collapseOnConnect: true, hoverExpand: true });\n"
)

# Every one of these must appear exactly once, or this is not a Talk version we
# know how to patch. They are the state the block reads and the functions the
# command listener calls.
ANCHORS_REQUIRED = (
    "  const { useState, useEffect, useRef, useCallback } = SDK.hooks;\n",
    '    const [phase, setPhase] = useState("idle");',
    '    const [live, setLive] = useState("");\n',
    "    const [transcript, setTranscript] = useState([]);\n",
    "    const [muted, updateMuted] = useState(false);\n",
    "    const [sleeping, updateSleeping] = useState(false);\n",
    "    async function startTalk() {\n",
    "    function stopTalk() {\n",
    "    function setMuted(value) {\n",
    "    function setSleeping(value) {\n",
)

BLOCK = """    // hermes-jarvis presence-bus BEGIN
    // Optional presence bus: other surfaces can mirror the live call without reading
    // Talk's DOM. Inert when nothing listens; commands call Talk's own functions.
    const presenceBusRef = useRef(null);
    useEffect(() => { presenceBusRef.current = { startTalk, stopTalk, setMuted, setSleeping }; },
      [startTalk, stopTalk, setMuted, setSleeping]);
    useEffect(() => {
      if (typeof window === "undefined") return;
      try {
        window.dispatchEvent(new CustomEvent("hermes-talk:presence", { detail: { phase, live,
          audioActivity, transcript: transcript.slice(-6), muted, sleeping, at: Date.now() } }));
      } catch (e) { /* the bus is optional */ }
    }, [phase, live, audioActivity, transcript, muted, sleeping]);
    useEffect(() => {
      if (typeof window === "undefined") return undefined;
      const onCommand = (event) => {
        const api = presenceBusRef.current || {}, action = event?.detail?.action;
        const call = (fn, value) => { if (typeof fn === "function") fn(value); };
        try {
          if (action === "start") call(api.startTalk);
          else if (action === "stop") call(api.stopTalk);
          else if (action === "mute" || action === "unmute") call(api.setMuted, action === "mute");
          else if (action === "sleep" || action === "wake") call(api.setSleeping, action === "sleep");
        } catch (e) { /* a command never breaks the call */ }
      };
      window.addEventListener("hermes-talk:command", onCommand);
      return () => window.removeEventListener("hermes-talk:command", onCommand);
    }, []);
    // hermes-jarvis presence-bus END
"""


BLOCK_LINES = BLOCK.count("\n")


class PatchError(Exception):
    """A refusal that carries the process exit code."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_surface(talk: Path) -> str:
    path = talk / SURFACE
    if not path.is_file():
        raise PatchError(2, f"Not a hermes-talk root: {path} is missing.")
    return path.read_bytes().decode("utf-8")


def marker_span(source: str) -> tuple[int, int] | None:
    """Return (begin, end) character offsets of the block, or None when absent."""
    begins, ends = source.count(BEGIN), source.count(END)
    if begins == 0 and ends == 0:
        return None
    if begins != 1 or ends != 1:
        raise PatchError(
            2,
            "Half-marked or doubly-marked file: found "
            f"{begins} BEGIN and {ends} END markers in {SURFACE}.",
        )
    start = source.index(BEGIN)
    stop = source.index(END) + len(END)
    if stop <= start:
        raise PatchError(2, f"END marker precedes BEGIN marker in {SURFACE}.")
    return start, stop


def require_anchors(source: str) -> int:
    """Validate every anchor and return the offset to insert at."""
    missing = [a for a in ANCHORS_REQUIRED if source.count(a) != 1]
    if source.count(ANCHOR_INSERT_AFTER) != 1:
        missing.append(ANCHOR_INSERT_AFTER)
    if missing:
        detail = "\n".join("  " + a.strip().splitlines()[0] for a in missing)
        raise PatchError(
            2,
            "Unknown hermes-talk version: these anchors are missing or not unique in "
            f"{SURFACE}:\n{detail}",
        )
    return source.index(ANCHOR_INSERT_AFTER) + len(ANCHOR_INSERT_AFTER)


def patched_source(source: str) -> str:
    at = require_anchors(source)
    return source[:at] + BLOCK + source[at:]


def reverted_source(source: str, span: tuple[int, int]) -> str:
    return source[: span[0]] + source[span[1] :]


def print_diff(before: str, after: str) -> None:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile="a/" + SURFACE,
        tofile="b/" + SURFACE,
        n=3,
    )
    sys.stdout.writelines(diff)


def hashes(talk: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in GENERATED:
        path = talk / name
        out[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return out


def preflight_build(talk: Path) -> None:
    """Refuse before writing anything if the rebuild cannot succeed."""
    if not (talk / BUILDER).is_file():
        raise PatchError(2, f"{BUILDER} is missing; cannot regenerate the Talk bundles.")
    if (talk / DESKTOP_ENTRY).is_file() and not (talk / STYLE).is_file():
        raise PatchError(
            3,
            f"{STYLE} is missing. scripts/build_ui.py inlines that stylesheet into the "
            "desktop bundle, so it cannot rebuild without it. Nothing was written. Restore "
            "the file (it ships with hermes-talk), or pass --no-build, and re-run.",
        )


def run_build(talk: Path) -> None:
    builder = talk / BUILDER
    preflight_build(talk)
    before = hashes(talk)
    result = subprocess.run(
        [sys.executable, str(builder)], cwd=str(talk), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise PatchError(
            5,
            f"{BUILDER} failed (exit {result.returncode}):\n"
            + (result.stdout + result.stderr).strip(),
        )
    after = hashes(talk)
    changed = [name for name in GENERATED if before[name] != after[name]]
    if changed:
        print("Rebuilt: " + ", ".join(changed))
    else:
        print("Rebuilt: no generated file changed.")


def do_check(talk: Path) -> int:
    source = read_surface(talk)
    span = marker_span(source)
    if span is not None:
        print(f"{SURFACE}: patched (presence bus present).")
        return 0
    require_anchors(source)
    print(f"{SURFACE}: not patched (anchors present, block absent).")
    return 1


def do_apply(talk: Path, *, build: bool, dry_run: bool) -> int:
    source = read_surface(talk)
    if marker_span(source) is not None:
        require_anchors(source)
        if dry_run:
            print(f"{SURFACE}: already patched; nothing to do.")
            return 0
        print(f"{SURFACE}: already patched; no change.")
        if build:
            run_build(talk)
        return 0
    after = patched_source(source)
    if dry_run:
        print_diff(source, after)
        return 0
    if build:
        preflight_build(talk)
    (talk / SIDECAR).write_text(f"{sha256(source)}  {SURFACE}\n", encoding="utf-8")
    (talk / SURFACE).write_bytes(after.encode("utf-8"))
    print(f"{SURFACE}: presence bus inserted ({BLOCK_LINES} lines).")
    print(f"Original sha256 recorded in {SIDECAR}.")
    if build:
        run_build(talk)
    return 0


def do_revert(talk: Path, *, build: bool, dry_run: bool) -> int:
    source = read_surface(talk)
    span = marker_span(source)
    if span is None:
        require_anchors(source)
        print(f"{SURFACE}: not patched; nothing to revert.")
        return 0
    after = reverted_source(source, span)
    if dry_run:
        print_diff(source, after)
        return 0
    if build:
        preflight_build(talk)
    sidecar = talk / SIDECAR
    recorded = None
    if sidecar.is_file():
        recorded = sidecar.read_text(encoding="utf-8").split()[0]
    if recorded is not None and sha256(after) != recorded:
        raise PatchError(
            4,
            f"Refusing to write: removing the block does not reproduce the original "
            f"{SURFACE} (recorded {recorded[:12]}…, got {sha256(after)[:12]}…). "
            "The file was edited while patched; restore it from hermes-talk and re-run.",
        )
    (talk / SURFACE).write_bytes(after.encode("utf-8"))
    if recorded is None:
        print(
            f"{SURFACE}: block removed, but there was no {SIDECAR} to verify against, "
            "so the restore is not hash-verified. Run --check to confirm."
        )
    else:
        print(f"{SURFACE}: block removed; bytes match the recorded original.")
        sidecar.unlink()
    if build:
        run_build(talk)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply/check/revert the hermes-jarvis presence-bus patch on hermes-talk.",
    )
    parser.add_argument(
        "--talk", required=True, metavar="PATH", help="path to a hermes-talk root"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="insert the presence-bus block")
    mode.add_argument("--check", action="store_true", help="report whether the block is present")
    mode.add_argument("--revert", action="store_true", help="remove the block")
    parser.add_argument(
        "--no-build", action="store_true", help="skip scripts/build_ui.py after a write"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print the unified diff and write nothing"
    )
    args = parser.parse_args(argv)

    talk = Path(args.talk).expanduser().resolve()
    if not talk.is_dir():
        print(f"error: --talk {talk} is not a directory", file=sys.stderr)
        return 2
    build = not args.no_build
    try:
        if args.check:
            return do_check(talk)
        if args.apply:
            return do_apply(talk, build=build, dry_run=args.dry_run)
        return do_revert(talk, build=build, dry_run=args.dry_run)
    except PatchError as err:
        print(f"error: {err}", file=sys.stderr)
        return err.code


if __name__ == "__main__":
    raise SystemExit(main())
