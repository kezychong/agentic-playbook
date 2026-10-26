#!/usr/bin/env python3
"""composite.py - lay the see-through overlay over the approved master.

ONE job: stack the transparent overlay on top of the master and write the
finished file. The picture is re-encoded, because the overlay has to be flattened
onto it. The audio is copied straight through from the master, untouched. The
overlay layer never changes how the member sounds.

The app draws layers, ffmpeg does the stacking. This is the stacking half.

The overlay is expected to match the master's size and length, because
render_overlays.py reads both from the master. If the overlay is shorter, it
simply stops drawing and the master plays on.

Example:
    ./composite.py --master master.mp4 --overlay overlay.mov -o master-captioned.mp4
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from media_workspace import check_input_path, check_output_path  # noqa: E402

TOOL = "composite"


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Stack a see-through overlay over the master with ffmpeg. Audio passes through.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--master", required=True, help="The approved master. It provides the audio.")
    p.add_argument("--overlay", required=True, help="The see-through overlay from render_overlays.py.")
    p.add_argument("-o", "--out", required=True, help="Output file.")
    p.add_argument("--crf", type=int, default=18, help="Quality setting. Lower is better quality.")
    p.add_argument("--dry-run", action="store_true", help="Print the command without running it.")
    args = p.parse_args(argv)

    if not shutil.which("ffmpeg"):
        sys.exit("error: ffmpeg is not installed. Run setup_editing.py --check.")

    master = check_input_path(args.master, TOOL)
    overlay = check_input_path(args.overlay, TOOL)
    for label, path in (("--master", master), ("--overlay", overlay)):
        if not os.path.isfile(path):
            sys.exit(f"error: {label} not found: {path}")

    out_path = check_output_path(args.out, TOOL)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # Input 0 is the master, which is the base picture and the audio.
    # Input 1 is the see-through overlay.
    cmd = [
        "ffmpeg", "-y",
        "-i", master,
        "-i", overlay,
        "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        out_path,
    ]

    print(f"[{TOOL}] {os.path.basename(overlay)} over {os.path.basename(master)} -> {out_path}",
          file=sys.stderr)
    if args.dry_run:
        print(f"[{TOOL}] DRY RUN, the command that would run:")
        print(" ".join(cmd))
        return 0

    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"error: the composite stopped with code {result.returncode}.")
    if not os.path.isfile(out_path):
        sys.exit(f"error: the composite did not produce {out_path}.")
    print(f"[{TOOL}] wrote {out_path}")
    print("Captions land on the wrong word sometimes, and an image can cover a face. "
          "Watch this one too before it goes anywhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
