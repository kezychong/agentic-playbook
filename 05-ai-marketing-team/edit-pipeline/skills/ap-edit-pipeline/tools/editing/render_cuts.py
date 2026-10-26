#!/usr/bin/env python3
"""render_cuts.py - run a cut list against the recording and write the clean master.

ONE job: take the keep windows (from cutcut.py or silence_trim.py) and produce a
single clean video where every removed stretch is gone.

HOW: one ffmpeg pass using trim and concat. It re-encodes rather than copying
the stream, because a copy can only cut on the video's own keyframes and the
cuts here land on word boundaries. For a short piece the re-encode costs
seconds, and the cuts land exactly where the words said they should.

Keep windows are clamped to the real length of the file and merged where the
padding made two of them overlap, so the joins stay clean and in order.

Cut-list shape it reads (only keep_windows is required):
  {"keep_windows": [{"start": s, "end": e, ...}, ...], ...}

OPTIONAL --normalize-audio: gentle noise reduction, then loudness normalised to
-14 LUFS, which is the level short-form platforms expect. Clean, even audio is
half of what people mean when they say a video looks professional. Off by
default, because it changes the sound of the take and that is the member's call.

Media in, media out. Nothing is written into the content-os workspace and
nothing is written into a cloud-synced folder.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from media_workspace import check_input_path, check_output_path  # noqa: E402

TOOL = "render_cuts"
AUDIO_CLEANUP = "afftdn=nf=-25,loudnorm=I=-14:TP=-1.5:LRA=11"


def find_binary(name):
    path = shutil.which(name)
    if not path:
        sys.exit(f"error: '{name}' is not installed. Run setup_editing.py --check.")
    return path


def probe_duration(video_path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        out = subprocess.check_output(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            text=True,
        ).strip()
        return float(out)
    except (subprocess.CalledProcessError, ValueError):
        return None


def clamp_windows(windows, duration):
    """Clamp to the real length, drop slivers, sort, and merge overlaps so the
    joins stay clean and in order."""
    cleaned = []
    for w in windows:
        s = max(0.0, float(w["start"]))
        e = float(w["end"])
        if duration is not None:
            e = min(e, duration)
        if e - s > 0.01:  # ignore anything under 10ms
            cleaned.append((s, e))
    cleaned.sort()
    merged = []
    for s, e in cleaned:
        if merged and s <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def build_filter(windows, normalize_audio=False):
    """Build the ffmpeg filter graph that trims each window and joins them.

    The joining filter wants its inputs INTERLEAVED, one picture label then one
    sound label per piece: [v0][a0][v1][a1]. Listing all the pictures and then
    all the sound looks tidier and fails the moment there is more than one
    piece, which is exactly the case where somebody fumbled twice.
    """
    parts = []
    pairs = []
    for i, (s, e) in enumerate(windows):
        parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{i}]")
        pairs.append(f"[v{i}][a{i}]")
    n = len(windows)
    audio_out = "[outa]"
    parts.append("".join(pairs) + f"concat=n={n}:v=1:a=1[outv]{audio_out}")
    if normalize_audio:
        parts.append(f"{audio_out}{AUDIO_CLEANUP}[outa_clean]")
        audio_out = "[outa_clean]"
    return ";".join(parts), "[outv]", audio_out


def render(cut_list_path, source_video, out_path, dry_run=False, normalize_audio=False, crf=18):
    find_binary("ffmpeg")
    source_video = check_input_path(source_video, TOOL)
    if not os.path.isfile(source_video):
        sys.exit(f"error: source video not found: {source_video}")

    with open(cut_list_path, encoding="utf-8") as f:
        cut_list = json.load(f)
    windows = cut_list.get("keep_windows", [])
    if not windows:
        sys.exit("error: this cut list keeps nothing, so there is nothing to render.")

    duration = probe_duration(source_video)
    windows = clamp_windows(windows, duration)
    if not windows:
        sys.exit("error: every keep window collapsed once clamped to the real length.")

    filtergraph, vlabel, alabel = build_filter(windows, normalize_audio=normalize_audio)
    out_path = check_output_path(out_path, TOOL)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-i", source_video,
        "-filter_complex", filtergraph,
        "-map", vlabel, "-map", alabel,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-c:a", "aac", "-b:a", "192k",
        out_path,
    ]

    kept = sum(e - s for s, e in windows)
    total = f" (of {round(duration, 2)}s)" if duration else ""
    print(
        f"[{TOOL}] {len(windows)} stretch(es), about {kept:.2f}s{total} -> {out_path}",
        file=sys.stderr,
    )
    if dry_run:
        print(f"[{TOOL}] DRY RUN, the command that would run:")
        print(" ".join(cmd))
        return out_path

    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"error: the render stopped with code {result.returncode}.")
    if not os.path.isfile(out_path):
        sys.exit(f"error: the render did not produce {out_path}.")
    print(f"[{TOOL}] wrote {out_path}")
    print("Watch this once, all the way through, before anything is exported.")
    return out_path


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Render the clean master by joining the keep windows from a cut list.",
        epilog="Example: render_cuts.py take.cuts.json raw_take.mp4 -o master.mp4",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("cut_list", help="Cut-list JSON from cutcut.py or silence_trim.py.")
    p.add_argument("source_video", help="The recording to cut.")
    p.add_argument("-o", "--out", required=True, help="Output master path.")
    p.add_argument("--dry-run", action="store_true", help="Print the command without running it.")
    p.add_argument("--normalize-audio", action="store_true",
                   help="Gentle de-noise and level the audio to -14 LUFS. Off by default.")
    p.add_argument("--crf", type=int, default=18, help="Quality setting. Lower is better quality.")
    args = p.parse_args(argv)
    render(args.cut_list, args.source_video, args.out,
           dry_run=args.dry_run, normalize_audio=args.normalize_audio, crf=args.crf)


if __name__ == "__main__":
    main()
