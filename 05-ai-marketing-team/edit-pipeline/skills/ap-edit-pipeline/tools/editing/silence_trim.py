#!/usr/bin/env python3
"""silence_trim.py - OPTIONAL dead-air removal. Off unless the member asks.

ONE job: find the long silent gaps in a finished master and write a cut list
that render_cuts.py can run, so the pacing tightens.

*** THIS IS OFF BY DEFAULT AND IT STAYS OFF BY DEFAULT. ***

Why: automatic silence cutting is exactly how an edit gets that machine-gun,
choppy feel. Every breath disappears, the delivery loses its rhythm, and the
video reads as processed. The system this pack was built from tested that,
rejected it, and wrote the finding into the pipeline. Three consequences live in
this file:

  1. No third-party auto-cutting tool. Silence detection is ffmpeg's own
     silencedetect and nothing else.
  2. Careful defaults. Only gaps LONGER than --min-silence (0.7s) are touched,
     and the padding around every cut is floored at 150ms, so speech is never
     clipped for the sake of pace.
  3. This is polish, not the point. The marker cut (cutcut.py) is the value.
     Run this only when the member asks for tighter pacing, only on the master
     they already watched and approved, and watch the result again afterwards.

This touches no video. It writes the cut list; render_cuts.py runs it.

How: ffmpeg `-af silencedetect=noise=<dB>:d=<sec>` reports silence_start and
silence_end pairs. Those get inverted into keep windows, then each detected
silence is shrunk by the padding so the cut never eats into speech.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from media_workspace import check_input_path  # noqa: E402

DEFAULT_NOISE_DB = -30          # quieter than this counts as silence
DEFAULT_MIN_SILENCE = 0.7       # seconds; only trim gaps longer than this
MIN_PAD_MS = 150                # hard floor, so speech is never clipped
DEFAULT_PAD_MS = 150

_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
_END = re.compile(r"silence_end:\s*(-?[\d.]+)")


def find_binary(name):
    path = shutil.which(name)
    if not path:
        sys.exit(f"error: '{name}' is not installed. Run setup_editing.py --check.")
    return path


def probe_duration(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        out = subprocess.check_output(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            text=True,
        ).strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError):
        return None


def detect_silences(path, noise_db, min_silence):
    """Return the (start, end) silence spans in seconds."""
    find_binary("ffmpeg")
    cmd = [
        "ffmpeg", "-i", path, "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence}",
        "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log = proc.stderr  # silencedetect reports on the error stream
    starts = [float(m) for m in _START.findall(log)]
    ends = [float(m) for m in _END.findall(log)]
    spans = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        spans.append((s, e))
    return spans


def silences_to_keep_windows(silences, duration, pad_s):
    """Invert silence spans into keep windows, shrinking each silence by the
    padding on both sides so speech beside the gap is never clipped."""
    cuts = []
    for (s, e) in silences:
        if e is None:
            e = duration if duration is not None else s
        cs = s + pad_s
        ce = e - pad_s
        if ce - cs > 0.01:
            cuts.append((cs, ce))
    cuts.sort()

    end_bound = duration if duration is not None else (cuts[-1][1] if cuts else 0.0)
    keep = []
    cursor = 0.0
    for (cs, ce) in cuts:
        if cs > cursor:
            keep.append((cursor, cs))
        cursor = max(cursor, ce)
    if duration is None or cursor < end_bound:
        keep.append((cursor, end_bound))
    return [(round(s, 3), round(e, 3)) for s, e in keep if e - s > 0.01]


def silence_trim(path, noise_db, min_silence, pad_ms):
    path = check_input_path(path, "silence_trim")
    if not os.path.isfile(path):
        sys.exit(f"error: input not found: {path}")
    pad_ms = max(MIN_PAD_MS, pad_ms)  # the floor is not negotiable
    pad_s = pad_ms / 1000.0

    duration = probe_duration(path)
    silences = detect_silences(path, noise_db, min_silence)
    keep = silences_to_keep_windows(silences, duration, pad_s)

    keep_windows = [{"start": s, "end": e} for s, e in keep]
    return {
        "mode": "silence_trim",
        "noise_db": noise_db,
        "min_silence_s": min_silence,
        "padding_ms": {"lead": pad_ms, "tail": pad_ms},
        "silences_detected": len(silences),
        "keep_windows": keep_windows,
        "note": "Optional polish. Off by default. Watch the result: this is how edits get choppy.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(
        description="OPTIONAL: find long silences and write a cut list. Off by default in the chain.",
        epilog="Example: silence_trim.py master.mp4 -o silence.cuts.json --min-silence 0.8",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("input", help="The approved master to analyse.")
    p.add_argument("-o", "--out", required=True, help="Output cut-list JSON path.")
    p.add_argument("--noise-db", type=int, default=DEFAULT_NOISE_DB,
                   help="How quiet counts as silence, in dB.")
    p.add_argument("--min-silence", type=float, default=DEFAULT_MIN_SILENCE,
                   help="Only trim gaps longer than this, in seconds.")
    p.add_argument("--pad-ms", type=int, default=DEFAULT_PAD_MS,
                   help=f"Room tone kept beside speech. Floored at {MIN_PAD_MS}ms.")
    args = p.parse_args(argv)

    cut_list = silence_trim(args.input, args.noise_db, args.min_silence, args.pad_ms)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cut_list, f, indent=2)
    print(
        f"[silence_trim] {cut_list['silences_detected']} silence(s) found; "
        f"{len(cut_list['keep_windows'])} stretch(es) kept -> {args.out}",
        file=sys.stderr,
    )
    print(
        "Tighter pacing is a taste call. Watch this render before it goes anywhere: "
        "silence cutting is what makes an edit feel choppy."
    )


if __name__ == "__main__":
    main()
