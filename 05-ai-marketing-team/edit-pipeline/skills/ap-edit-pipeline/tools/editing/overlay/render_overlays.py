#!/usr/bin/env python3
"""render_overlays.py - words plus a manifest, out comes a see-through overlay video.

ONE job: build the props for the overlay app and render a TRANSPARENT video that
contains only the layers: captions, proof images, hook line. It does not touch
the master. composite.py lays this over the master afterwards.

The rule that keeps this simple: the app draws layers, ffmpeg does the stacking.

The overlay matches the master's length, size and frame rate. Either pass
--master and let this read those from it, or pass --duration, --dims and --fps.
The overlay is written into the media workspace, never into content-os and never
into a synced folder.

Fails with a clear message if the app has not been staged yet
(bootstrap_overlay.py does that).

Examples:
    ./render_overlays.py --words take.words.json --manifest manifest.json \\
        --master master.mp4 -o overlay.mov

    ./render_overlays.py --words take.words.json --manifest manifest.json \\
        --duration 12.5 --dims 1080x1920 --fps 30 -o overlay.mov
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from props_builder import build_input_props  # noqa: E402
from bootstrap_overlay import app_dir  # noqa: E402
from media_workspace import check_input_path, check_output_path, workspace_dir  # noqa: E402

COMPOSITION_ID = "Overlay"
TOOL = "render_overlays"


def probe(master, entries):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        sys.exit("error: ffprobe is not installed. Pass --duration and --dims instead.")
    out = subprocess.check_output(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", entries, "-of", "json", master],
        text=True,
    )
    return json.loads(out)


def probe_master(master):
    """Read length, size and frame rate straight off the master."""
    master = check_input_path(master, TOOL)
    if not os.path.isfile(master):
        sys.exit(f"error: --master not found: {master}")
    info = probe(master, "format=duration:stream=width,height,r_frame_rate")
    stream = info["streams"][0]
    width = int(stream["width"])
    height = int(stream["height"])
    num, den = stream["r_frame_rate"].split("/")
    fps = round(float(num) / float(den)) if float(den) else 30
    duration = float(info["format"]["duration"])
    return duration, width, height, fps


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Render a see-through overlay video from the words and a manifest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--words", required=True, help="Words JSON from transcribe.py.")
    p.add_argument("--manifest", required=True, help="Overlay manifest JSON (see example-manifest.json).")
    p.add_argument("-o", "--out", required=True, help="Output overlay.mov path, in the media workspace.")
    p.add_argument("--master", help="Master video to read length, size and frame rate from.")
    p.add_argument("--duration", type=float, help="Overlay length in seconds, if not using --master.")
    p.add_argument("--dims", help="WIDTHxHEIGHT, for example 1080x1920, if not using --master.")
    p.add_argument("--fps", type=int, default=30, help="Frames per second, if not using --master.")
    p.add_argument("--dry-run", action="store_true", help="Build the props and print the command only.")
    args = p.parse_args(argv)

    app = app_dir()
    if not args.dry_run and not os.path.isdir(os.path.join(app, "node_modules")):
        sys.exit(
            f"error: the overlay app is not staged yet ({app}).\n"
            f"       Run bootstrap_overlay.py first. It copies the app into the media "
            f"workspace and installs it there."
        )

    if args.master:
        duration, width, height, fps = probe_master(args.master)
    else:
        if args.duration is None or not args.dims:
            sys.exit("error: pass --master, or both --duration and --dims.")
        try:
            width, height = (int(x) for x in args.dims.lower().split("x"))
        except ValueError:
            sys.exit("error: --dims must look like 1080x1920.")
        duration, fps = args.duration, args.fps

    with open(os.path.expanduser(args.words), encoding="utf-8") as f:
        words_json = json.load(f)
    with open(os.path.expanduser(args.manifest), encoding="utf-8") as f:
        manifest = json.load(f)

    props = build_input_props(
        words_json, manifest,
        fps=fps, width=width, height=height, duration_seconds=duration,
    )

    # The props go to a file and the file path is passed in, rather than a huge
    # blob on the command line.
    os.makedirs(workspace_dir(create=True), exist_ok=True)
    props_path = os.path.join(workspace_dir(), "overlay-inputprops.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2)

    out_path = check_output_path(args.out, TOOL)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    cmd = [
        "npx", "remotion", "render", COMPOSITION_ID, out_path,
        f"--props={props_path}",
        # These four flags are what make the output see-through.
        "--codec=prores",
        "--prores-profile=4444",
        "--pixel-format=yuva444p10le",
        "--image-format=png",
    ]

    print(
        f"[{TOOL}] {width}x{height} at {fps}fps, {duration:.2f}s, "
        f"{len(props['words'])} words, {len(props['proof'])} proof image(s), "
        f"hook={'yes' if props['hookText'] else 'no'} -> {out_path}",
        file=sys.stderr,
    )
    if args.dry_run:
        print(f"[{TOOL}] DRY RUN, props written to {props_path}")
        print(f"[{TOOL}] would run from {app}:")
        print(" ".join(cmd))
        return 0

    result = subprocess.run(cmd, cwd=app)
    if result.returncode != 0:
        sys.exit(f"error: the overlay render stopped with code {result.returncode}.")
    if not os.path.isfile(out_path):
        sys.exit(f"error: the overlay render did not produce {out_path}.")
    print(f"[{TOOL}] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
