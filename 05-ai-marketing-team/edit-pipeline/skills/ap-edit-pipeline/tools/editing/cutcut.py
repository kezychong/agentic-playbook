#!/usr/bin/env python3
"""cutcut.py - words with timings plus a marker word, out comes a cut list.

ONE job: work out which parts of a recording to keep, using the marker word the
member said every time they fumbled a line.

THE PROTOCOL (a proven creator filming protocol, taught in short-form filming
guides and used by the record stage of this pack):
  You film straight through. When you flub a line you SAY the marker word
  ("cut cut" by default) and keep rolling. In the edit, for EACH marker you
  delete the bad take BEFORE the marker word, plus the marker words themselves.
  So a marker means: "the take I just did was bad, keep what FOLLOWS."

HOW IT WORKS (keep the last take):
  Walk the words in order. A marker deletes the run of speech immediately before
  it, back to the previous marker or to the start, and the marker words too.
  Everything after the final marker survives. Three attempts at the same line
  collapse into the one that worked.

TWO SCOPES, because two filming styles exist:

  --scope full-take  (default, and the way the tested original works)
      A marker deletes everything back to the previous marker, or to the start
      of the recording. Right when the recording is a run of separate attempts
      at the same short line, which is how the method was first taught.

  --scope line
      A marker deletes back only as far as the fumbled line: the latest
      sentence ending or real pause before the marker. Right when somebody
      filmed one continuous take from bullet points and fumbled once in the
      middle of it, which is what the record stage of this pack teaches. Under
      full-take scope that member would lose every good minute before the
      fumble.

  Under line scope the answer is a LIST of keep windows, not one span, because
  clean stretches before a fumble survive.

CHOOSING: run the default, read the cut list, and look at what it removes. A
removed piece that is long and carries more than one finished sentence means
they filmed continuously, so run it again with line scope and show them both.
Recommend one, with the reason, in one sentence. Never show a member a menu.

WHAT IT WRITES:
  {
    "source_words": 29,
    "marker": "cut cut",
    "markers_found": 2,
    "scope": "full-take",
    "padding_ms": {"lead": 120, "tail": 120},
    "keep_windows":    [{"start": s, "end": e, "text": "..."}],
    "removed_windows": [{"start": s, "end": e, "reason": "...", "text": "..."}],
    "kept_seconds": 3.74, "removed_seconds": 4.75
  }

`removed_windows` is the evidence trail. The member sees it, in plain words,
BEFORE anything is rendered. That gate is not optional.

Padding: each kept window is nudged outward slightly (120ms by default) so the
render never clips the start or end of a word.

This touches no video at all. It only writes the list that render_cuts.py runs.
"""

import argparse
import json
import re
import sys

DEFAULT_MARKER = "cut cut"
DEFAULT_LEAD_PAD_MS = 120
DEFAULT_TAIL_PAD_MS = 120
SCOPE_FULL_TAKE = "full-take"
SCOPE_LINE = "line"
DEFAULT_SCOPE = SCOPE_FULL_TAKE
DEFAULT_PAUSE_S = 0.8  # a gap this long reads as the end of a thought

_PUNCT = re.compile(r"[^\w']+", re.UNICODE)
_SENTENCE_END = (".", "!", "?")


def normalize(word):
    """Lowercase, strip surrounding whitespace and punctuation.

    Engines emit words like ' Hello', ' world,', ' Cut.' so matching a marker
    means stripping the leading space and any trailing punctuation first.
    """
    return _PUNCT.sub("", word.strip().lower())


def flatten_words(transcript):
    """Flatten the transcript segments into one ordered list of words."""
    words = []
    for seg in transcript.get("segments", []):
        for w in seg.get("words", []):
            if "start" not in w or "end" not in w:
                continue
            words.append({
                "word": w["word"],
                "norm": normalize(w["word"]),
                "start": float(w["start"]),
                "end": float(w["end"]),
            })
    return words


def find_marker_spans(words, marker_tokens):
    """Index ranges where the marker phrase appears.

    Two shapes count, because the engines produce both. Said quickly, "cut cut"
    often comes back as ONE joined word ("CutCut", "cut-cut"), and a missed
    marker means the fumble stays in the video. So the phrase is matched as
    consecutive words, and also as a single word equal to the whole phrase run
    together.
    """
    n = len(words)
    m = len(marker_tokens)
    joined = "".join(marker_tokens)
    spans = []
    i = 0
    while i < n:
        if m > 1 and words[i]["norm"] == joined:
            spans.append((i, i + 1))
            i += 1
            continue
        if i <= n - m and all(words[i + k]["norm"] == marker_tokens[k] for k in range(m)):
            spans.append((i, i + m))
            i += m  # markers never overlap
            continue
        i += 1
    return spans


def line_start_index(words, lower_bound, marker_start, pause_s):
    """Where the fumbled line began: the latest sentence ending or real pause
    between lower_bound and the marker. Falls back to lower_bound when there is
    no boundary to find, which makes line scope match full-take scope."""
    boundary = lower_bound
    for i in range(lower_bound + 1, marker_start):
        prev = words[i - 1]
        if prev["norm"] and prev["word"].strip().endswith(_SENTENCE_END):
            boundary = i
        elif words[i]["start"] - prev["end"] >= pause_s:
            boundary = i
    return boundary


def build_cut_list(words, marker_spans, scope=DEFAULT_SCOPE, pause_s=DEFAULT_PAUSE_S):
    """Turn marker positions into keep windows and removed windows."""
    keep = []
    removed = []
    prev_boundary = 0

    for (ms, me) in marker_spans:
        # words[prev_boundary:ms] is the speech before this marker
        # words[ms:me]            is the marker itself
        cut_from = prev_boundary
        if scope == SCOPE_LINE:
            cut_from = line_start_index(words, prev_boundary, ms, pause_s)
            if cut_from > prev_boundary:
                keep.append((prev_boundary, cut_from))
        if ms > cut_from:
            reason = ("fumbled line before marker" if scope == SCOPE_LINE
                      else "bad take before marker")
            removed.append((cut_from, ms, reason))
        removed.append((ms, me, "marker words"))
        prev_boundary = me

    if prev_boundary < len(words):
        keep.append((prev_boundary, len(words)))

    keep.sort()
    return keep, removed


def window_from_indices(words, i_start, i_end):
    chunk = words[i_start:i_end]
    start = chunk[0]["start"]
    end = chunk[-1]["end"]
    text = "".join(w["word"] for w in chunk).strip()
    return start, end, text


def cutcut(transcript, marker, lead_pad_ms, tail_pad_ms,
           scope=DEFAULT_SCOPE, pause_s=DEFAULT_PAUSE_S):
    words = flatten_words(transcript)
    if not words:
        sys.exit("error: this transcript has no per-word timings, so no cut can be built.")

    if scope not in (SCOPE_FULL_TAKE, SCOPE_LINE):
        sys.exit(f"error: scope must be {SCOPE_FULL_TAKE} or {SCOPE_LINE}.")

    marker_tokens = [normalize(t) for t in marker.split() if normalize(t)]
    if not marker_tokens:
        sys.exit("error: that marker is empty once punctuation is stripped. Pick a real word.")

    marker_spans = find_marker_spans(words, marker_tokens)
    keep_idx, removed_idx = build_cut_list(words, marker_spans, scope=scope, pause_s=pause_s)

    lead = lead_pad_ms / 1000.0
    tail = tail_pad_ms / 1000.0

    keep_windows = []
    for (a, b) in keep_idx:
        s, e, text = window_from_indices(words, a, b)
        keep_windows.append({
            "start": round(max(0.0, s - lead), 3),
            "end": round(e + tail, 3),
            "text": text,
        })

    removed_windows = []
    for (a, b, reason) in removed_idx:
        s, e, text = window_from_indices(words, a, b)
        removed_windows.append({
            "start": round(s, 3), "end": round(e, 3),
            "reason": reason, "text": text,
        })

    kept_seconds = round(sum(w["end"] - w["start"] for w in keep_windows), 3)
    removed_seconds = round(sum(w["end"] - w["start"] for w in removed_windows), 3)

    return {
        "source_words": len(words),
        "marker": marker,
        "markers_found": len(marker_spans),
        "scope": scope,
        "padding_ms": {"lead": lead_pad_ms, "tail": tail_pad_ms},
        "keep_windows": keep_windows,
        "removed_windows": removed_windows,
        "kept_seconds": kept_seconds,
        "removed_seconds": removed_seconds,
    }


def plain_summary(cut_list):
    """The lines the agent shows the member before anything is rendered."""
    lines = []
    found = cut_list["markers_found"]
    bad_takes = [w for w in cut_list["removed_windows"]
                 if w["reason"] != "marker words"]
    if found == 0:
        lines.append(
            "You filmed clean. I found no marker word, so nothing gets cut and the "
            "whole recording is the master."
        )
        return lines
    lines.append(
        f"I found your marker {found} time(s). That means {len(bad_takes)} attempt(s) "
        f"to remove, {cut_list['removed_seconds']:.1f} seconds in total."
    )
    for i, w in enumerate(bad_takes, start=1):
        snippet = w["text"].strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        lines.append(f"  {i}. cutting {w['start']:.1f}s to {w['end']:.1f}s: \"{snippet}\"")
    lines.append(
        f"What survives: {len(cut_list['keep_windows'])} stretch(es), "
        f"{cut_list['kept_seconds']:.1f} seconds."
    )
    if len(cut_list["keep_windows"]) > 1:
        lines.append(
            "More than one stretch survives, which is normal when only the fumbled "
            "lines come out and the good runs between them stay. Read the list above "
            "before I cut."
        )
    longest = max((w["end"] - w["start"] for w in bad_takes), default=0.0)
    if cut_list.get("scope") == SCOPE_FULL_TAKE and longest > 15.0:
        lines.append(
            f"Heads up: one removed piece runs {longest:.0f} seconds, which is long for a "
            f"single fumbled line. If you filmed one continuous take and only redid the "
            f"line you tripped on, say so and I will rebuild the cut so everything good "
            f"before the fumble stays."
        )
    return lines


def main(argv=None):
    p = argparse.ArgumentParser(
        description='Turn a word-timing transcript plus a marker word ("cut cut") into a cut list.',
        epilog='Example: cutcut.py take.words.json -o take.cuts.json --marker "cut cut"',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("transcript", help="Words JSON from transcribe.py.")
    p.add_argument("-o", "--out", required=True, help="Output cut-list JSON path.")
    p.add_argument(
        "--marker", default=DEFAULT_MARKER,
        help="The marker phrase the member says on a fumbled take. Casing and punctuation do not matter.",
    )
    p.add_argument("--lead-pad-ms", type=int, default=DEFAULT_LEAD_PAD_MS,
                   help="Milliseconds kept before each surviving stretch.")
    p.add_argument("--tail-pad-ms", type=int, default=DEFAULT_TAIL_PAD_MS,
                   help="Milliseconds kept after each surviving stretch.")
    p.add_argument("--scope", default=DEFAULT_SCOPE,
                   choices=[SCOPE_FULL_TAKE, SCOPE_LINE],
                   help="How far back each marker deletes: the whole previous take, "
                        "or only the fumbled line.")
    p.add_argument("--pause-seconds", type=float, default=DEFAULT_PAUSE_S,
                   help="With line scope, a gap this long counts as the start of a line.")
    args = p.parse_args(argv)

    with open(args.transcript, encoding="utf-8") as f:
        transcript = json.load(f)

    cut_list = cutcut(transcript, args.marker, args.lead_pad_ms, args.tail_pad_ms,
                      scope=args.scope, pause_s=args.pause_seconds)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cut_list, f, indent=2)

    for line in plain_summary(cut_list):
        print(line)
    print(
        f"[cutcut] {cut_list['markers_found']} marker(s); "
        f"{len(cut_list['keep_windows'])} keep-window(s); "
        f"kept {cut_list['kept_seconds']}s / removed {cut_list['removed_seconds']}s "
        f"-> {args.out}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
