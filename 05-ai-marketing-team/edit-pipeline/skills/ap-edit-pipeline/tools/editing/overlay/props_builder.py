#!/usr/bin/env python3
"""props_builder.py - words plus a manifest, out comes the exact object the overlay app receives.

This is the one piece of the overlay layer with no extra tooling behind it, so it
can be tested on its own. render_overlays.py and the test both import
`build_input_props` from here, so there is one code path and no drift.

Contract, kept in lockstep with src/types.ts (OverlayProps):

    build_input_props(words_json, manifest, *, fps, width, height,
                      duration_seconds) -> dict

- words_json: the parsed output of transcribe.py (top level `segments`, each
  with a `words` list of {word, start, end, probability}). Word strings carry a
  leading space and trailing punctuation, so display text is stripped but the
  timings pass through untouched.
- manifest: the parsed overlay manifest (see example-manifest.json).
- Returns a plain dict, ready to be written as JSON.

No file reading happens here, which is what keeps it deterministic and easy to
test. Paths get expanded but do not have to exist yet.
"""

import os

# These mirror src/Root.tsx defaultProps.captionStyle exactly, so a manifest that
# leaves a field out renders the same on both sides. Colours are deliberately
# neutral: white for the word being spoken, dimmed grey for the rest. Set
# active_color in the manifest to the member's own accent colour when they gave one.
DEFAULT_CAPTION_STYLE = {
    "fontSizePx": 72,
    "activeColor": "#FFFFFF",
    "inactiveColor": "#B8B8B8",
    "bottomMarginPx": 320,
    "maxWordsPerGroup": 4,
}


def _clean_word(raw):
    """Drop the leading space the engines add. Inner text and trailing
    punctuation stay, because they belong on screen."""
    return raw.strip()


def extract_words(words_json):
    """Flatten every segment's words into [{text, start, end}] in seconds.

    Words with no usable timing, or that clean to nothing, are skipped. Timings
    are never altered.
    """
    out = []
    for seg in words_json.get("segments", []):
        for w in seg.get("words", []):
            text = _clean_word(w.get("word", ""))
            if not text:
                continue
            if "start" not in w or "end" not in w:
                continue
            out.append({
                "text": text,
                "start": float(w["start"]),
                "end": float(w["end"]),
            })
    return out


def _caption_style(manifest):
    cap = manifest.get("captions", {}) or {}
    style = dict(DEFAULT_CAPTION_STYLE)
    if "font_size_px" in cap:
        style["fontSizePx"] = int(cap["font_size_px"])
    if "active_color" in cap:
        style["activeColor"] = str(cap["active_color"])
    if "inactive_color" in cap:
        style["inactiveColor"] = str(cap["inactive_color"])
    if "bottom_margin_px" in cap:
        style["bottomMarginPx"] = int(cap["bottom_margin_px"])
    if "max_words_per_group" in cap:
        style["maxWordsPerGroup"] = int(cap["max_words_per_group"])
    return style


def _proof_windows(manifest):
    out = []
    for p in manifest.get("proof_assets", []) or []:
        path = os.path.expanduser(str(p.get("path", "")))
        out.append({
            "assetPath": path,
            "start": float(p.get("start", 0.0)),
            "end": float(p.get("end", 0.0)),
            "position": str(p.get("position", "center")),
            "label": str(p.get("caption", "")),
        })
    return out


def build_input_props(words_json, manifest, *, fps, width, height, duration_seconds):
    """Turn parsed words plus a manifest into the object the overlay app reads."""
    cap = manifest.get("captions", {}) or {}
    captions_enabled = bool(cap.get("enabled", True))

    return {
        "fps": int(fps),
        "width": int(width),
        "height": int(height),
        "durationInSeconds": float(duration_seconds),
        "hookText": str(manifest.get("hook_text", "") or ""),
        "hookDurationSeconds": float(manifest.get("hook_duration_seconds", 2.0)),
        "captionsEnabled": captions_enabled,
        "captionStyle": _caption_style(manifest),
        "words": extract_words(words_json) if captions_enabled else [],
        "proof": _proof_windows(manifest),
    }
