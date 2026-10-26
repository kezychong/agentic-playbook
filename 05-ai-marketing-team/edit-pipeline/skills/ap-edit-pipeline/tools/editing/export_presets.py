#!/usr/bin/env python3
"""export_presets.py - the approved master out into the three delivery shapes.

ONE job: take the master the member has already watched and approved, and render
the three sizes every platform between them wants:

  9:16   1080x1920   vertical: Reels, Shorts, TikTok
  1:1    1080x1080   square: feed posts
  16:9   1920x1080   wide: YouTube, landscape players

Each export scales up to fill the target frame and then crops from the centre,
so nothing is squashed and no black bars appear.

These are RAW exports. No watermark, no logo, no intro bumper, ever. A rival
app's watermark burned into a video is one of the cheapest ways to get shown to
fewer people, and it is one of the ten laws of this pack.

This is a straight port of the same three presets the system this pack was built
from uses, rewritten so it runs the same way on any machine.

Examples:
    ./export_presets.py master.mp4
    ./export_presets.py master.mp4 --out-dir exports --formats 9x16,1x1
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from media_workspace import check_input_path, check_output_path  # noqa: E402

TOOL = "export_presets"

PRESETS = {
    "9x16": (1080, 1920, "vertical, for Reels, Shorts and TikTok"),
    "1x1": (1080, 1080, "square, for feed posts"),
    "16x9": (1920, 1080, "wide, for YouTube and landscape players"),
}
DEFAULT_ORDER = ["9x16", "1x1", "16x9"]


def fill_crop(width, height):
    """Scale up to fill, then crop from the centre. No stretch, no bars."""
    return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"


def export(master, out_dir=None, formats=None, dry_run=False, crf=18):
    if not shutil.which("ffmpeg"):
        sys.exit("error: ffmpeg is not installed. Run setup_editing.py --check.")

    master = check_input_path(master, TOOL)
    if not os.path.isfile(master):
        sys.exit(f"error: master not found: {master}")

    name = os.path.splitext(os.path.basename(master))[0]
    out_dir = out_dir or os.path.dirname(master)
    out_dir = check_output_path(out_dir, TOOL)
    os.makedirs(out_dir, exist_ok=True)

    wanted = formats or list(DEFAULT_ORDER)
    unknown = [f for f in wanted if f not in PRESETS]
    if unknown:
        sys.exit(f"error: unknown format(s): {', '.join(unknown)}. Choose from {', '.join(DEFAULT_ORDER)}.")

    written = []
    for key in wanted:
        width, height, human = PRESETS[key]
        out_path = os.path.join(out_dir, f"{name}-{key}.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", master,
            "-vf", fill_crop(width, height),
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-c:a", "aac", "-b:a", "192k",
            out_path,
        ]
        print(f"[{TOOL}] {key} ({width}x{height}) {human} -> {out_path}", file=sys.stderr)
        if dry_run:
            print(" ".join(cmd))
            written.append(out_path)
            continue
        if subprocess.run(cmd).returncode != 0:
            sys.exit(f"error: the {key} export stopped before it finished.")
        if not os.path.isfile(out_path):
            sys.exit(f"error: the {key} export did not produce {out_path}.")
        written.append(out_path)

    print(f"[{TOOL}] done, {len(written)} file(s) in {out_dir}", file=sys.stderr)
    return written


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Export an approved master to 9:16, 1:1 and 16:9. Clean, never watermarked.",
        epilog="Example: export_presets.py master.mp4 --out-dir exports",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("master", help="The approved master video.")
    p.add_argument("--out-dir", default=None, help="Where the exports go. Defaults beside the master.")
    p.add_argument("--formats", default=",".join(DEFAULT_ORDER),
                   help="Comma-separated list: 9x16, 1x1, 16x9.")
    p.add_argument("--dry-run", action="store_true", help="Print the commands without running them.")
    p.add_argument("--crf", type=int, default=18, help="Quality setting. Lower is better quality.")
    args = p.parse_args(argv)

    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    export(args.master, out_dir=args.out_dir, formats=formats,
           dry_run=args.dry_run, crf=args.crf)


if __name__ == "__main__":
    main()
