#!/usr/bin/env python3
"""transcribe.py - a recording in, words with exact timings out.

ONE job: turn audio or video into a JSON file where every single word carries a
start time and an end time. Everything downstream snaps to those times: the
marker cut, the captions, the overlays.

THREE ENGINES, ONE OUTPUT SHAPE. The engine is picked automatically:

  mlx        mlx-whisper. Apple Silicon Macs only. Fast and local.
  whisper    openai-whisper. Works anywhere. Slower without a graphics chip.
  whispercpp whisper.cpp, if it is already installed. Fast on a plain
             processor. Needs a model file (--model or the WHISPER_CPP_MODEL
             environment variable). Word timings are grouped from its token
             output, so read the first result before trusting it on a long take.

Whichever engine runs, this writes the SAME shape, so nothing downstream ever
has to know which one was used:

  {
    "text": "...",
    "language": "en",
    "engine": "mlx",
    "segments": [
      {"id": 0, "start": 0.0, "end": 10.5, "text": "...",
       "words": [{"word": " Hello", "start": 0.0, "end": 0.2, "probability": 0.98}]}
    ]
  }

Word strings keep the leading space and trailing punctuation the engines add
(" Hello", " world,"). Everything downstream normalises before matching.

VOCAB PRIMING: pass --initial-prompt with the topic and any names the engine is
likely to mishear (your product name, your industry words). It measurably cuts
mishears, and a mishear becomes a typo burned into a caption later.

Nothing is uploaded. Every engine runs on this machine.

Examples:
    ./transcribe.py raw_take.mp4 -o take.words.json
    ./transcribe.py raw_take.mp4 -o take.words.json --initial-prompt "bookkeeping, Xero, month-end close"
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from media_workspace import check_input_path  # noqa: E402
from setup_editing import detect, find  # noqa: E402

MLX_DEFAULT_MODEL = "mlx-community/whisper-large-v3-mlx"
CROSS_PLATFORM_DEFAULT_MODEL = "small"
TOOL = "transcribe"


def die(message):
    sys.exit(f"error: {message}")


def choose_engine(requested):
    state = detect()
    available = state["engines_found"]
    if requested and requested != "auto":
        if requested not in available:
            die(
                f"engine '{requested}' is not installed. Found: {available or 'none'}. "
                f"Run setup_editing.py --check for the full picture."
            )
        return requested
    if not available:
        die(
            "no speech-to-text engine is installed yet. Run setup_editing.py --check, "
            "tell the member in plain words what is about to be set up, and on their yes "
            "run setup_editing.py --install engine."
        )
    return available[0]


def ffmpeg_or_die():
    if not find("ffmpeg"):
        die("ffmpeg is not installed. Run setup_editing.py --install ffmpeg first.")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _word_count(data):
    return sum(len(s.get("words", [])) for s in data.get("segments", []))


def run_mlx(audio, out_dir, model, language, initial_prompt, verbose):
    stem = "transcribe_out"
    cmd = [
        find("mlx_whisper") or "mlx_whisper",
        audio,
        "--model", model or MLX_DEFAULT_MODEL,
        # This flag takes a VALUE. A bare --word-timestamps silently gives no
        # per-word times, which breaks every step after this one.
        "--word-timestamps", "True",
        "--output-format", "json",
        "--output-dir", out_dir,
        # The engine truncates this name at the first dot, so it stays dot-free.
        "--output-name", stem,
        "--verbose", "True" if verbose else "False",
    ]
    if language:
        cmd += ["--language", language]
    if initial_prompt:
        cmd += ["--initial-prompt", initial_prompt]
    print(f"[{TOOL}] engine: mlx-whisper", file=sys.stderr)
    if subprocess.run(cmd).returncode != 0:
        die("the transcription engine stopped before it finished.")
    produced = os.path.join(out_dir, stem + ".json")
    if not os.path.isfile(produced):
        die(f"expected transcript not written: {produced}")
    return _load(produced), produced


def run_openai_whisper(audio, out_dir, model, language, initial_prompt, verbose):
    cmd = [
        find("whisper") or "whisper",
        audio,
        "--model", model or CROSS_PLATFORM_DEFAULT_MODEL,
        "--word_timestamps", "True",
        "--output_format", "json",
        "--output_dir", out_dir,
        "--verbose", "True" if verbose else "False",
    ]
    if language:
        cmd += ["--language", language]
    if initial_prompt:
        cmd += ["--initial_prompt", initial_prompt]
    print(f"[{TOOL}] engine: openai-whisper (this one is slower, be patient)", file=sys.stderr)
    if subprocess.run(cmd).returncode != 0:
        die("the transcription engine stopped before it finished.")
    stem = os.path.splitext(os.path.basename(audio))[0]
    produced = os.path.join(out_dir, stem + ".json")
    if not os.path.isfile(produced):
        die(f"expected transcript not written: {produced}")
    return _load(produced), produced


def to_wav_16k(audio, out_dir):
    """whisper.cpp only reads 16kHz mono wav, so convert first."""
    ffmpeg_or_die()
    wav = os.path.join(out_dir, "for-transcription.wav")
    cmd = [find("ffmpeg") or "ffmpeg", "-y", "-i", audio, "-ar", "16000", "-ac", "1", wav]
    if subprocess.run(cmd, capture_output=True).returncode != 0:
        die("could not prepare the audio for the transcription engine.")
    return wav


def whispercpp_binary():
    for name in ("whisper-cli", "whisper.cpp", "main-whisper"):
        path = shutil.which(name)
        if path:
            return path
    return None


def tokens_to_words(entry):
    """Group whisper.cpp tokens into words. A token that starts with a space
    begins a new word; special tokens are dropped."""
    words = []
    current = None
    for token in entry.get("tokens", []) or []:
        text = token.get("text", "")
        if not text or text.startswith("[_") or text.startswith("<|"):
            continue
        offsets = token.get("offsets", {}) or {}
        start = float(offsets.get("from", 0)) / 1000.0
        end = float(offsets.get("to", 0)) / 1000.0
        probability = float(token.get("p", 0.0) or 0.0)
        if current is None or text.startswith(" "):
            if current is not None:
                words.append(current)
            current = {"word": text, "start": start, "end": end, "probability": probability}
        else:
            current["word"] += text
            current["end"] = end
            current["probability"] = min(current["probability"], probability)
    if current is not None:
        words.append(current)
    return words


def run_whispercpp(audio, out_dir, model, language, initial_prompt, verbose):
    binary = whispercpp_binary()
    model_path = model or os.environ.get("WHISPER_CPP_MODEL")
    if not model_path or not os.path.isfile(os.path.expanduser(model_path)):
        die(
            "this engine needs a model file. Pass --model with the path to it, or set "
            "WHISPER_CPP_MODEL. If that is a hassle, run setup_editing.py --install engine "
            "and use the engine this pack installs instead."
        )
    wav = to_wav_16k(audio, out_dir)
    stem = os.path.join(out_dir, "transcribe_out")
    cmd = [binary, "-m", os.path.expanduser(model_path), "-f", wav,
           "--output-json-full", "-of", stem]
    if language:
        cmd += ["-l", language]
    if initial_prompt:
        cmd += ["--prompt", initial_prompt]
    print(f"[{TOOL}] engine: whisper.cpp (word timings grouped from tokens)", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=not verbose)
    if result.returncode != 0:
        die("the transcription engine stopped before it finished.")
    produced = stem + ".json"
    if not os.path.isfile(produced):
        die(f"expected transcript not written: {produced}")
    raw = _load(produced)
    return normalise_whispercpp(raw, language), produced


def normalise_whispercpp(raw, language):
    segments = []
    full_text = []
    for index, entry in enumerate(raw.get("transcription", []) or []):
        words = tokens_to_words(entry)
        offsets = entry.get("offsets", {}) or {}
        text = entry.get("text", "")
        full_text.append(text)
        segments.append({
            "id": index,
            "start": float(offsets.get("from", 0)) / 1000.0,
            "end": float(offsets.get("to", 0)) / 1000.0,
            "text": text,
            "words": words,
        })
    return {
        "text": "".join(full_text),
        "language": language or (raw.get("params", {}) or {}).get("language", ""),
        "segments": segments,
    }


ENGINE_RUNNERS = {
    "mlx": run_mlx,
    "whisper": run_openai_whisper,
    "whispercpp": run_whispercpp,
}


def transcribe(audio, out_json, engine="auto", model=None, language="en",
               initial_prompt=None, verbose=False):
    audio = check_input_path(audio, TOOL)
    if not os.path.isfile(audio):
        die(f"input file not found: {audio}")

    out_json = os.path.abspath(os.path.expanduser(out_json))
    out_dir = os.path.dirname(out_json) or "."
    os.makedirs(out_dir, exist_ok=True)

    picked = choose_engine(engine)
    ffmpeg_or_die()  # every engine decodes video through ffmpeg

    data, produced = ENGINE_RUNNERS[picked](
        audio, out_dir, model, language, initial_prompt, verbose
    )

    if "segments" not in data:
        die(f"the transcript came back without segments: {produced}")
    count = _word_count(data)
    if count == 0:
        die(
            "the transcript came back with no per-word timings, so no cut can be made "
            "from it. Check the recording actually has speech in it, then try again."
        )

    data["engine"] = picked
    data["model"] = model or (MLX_DEFAULT_MODEL if picked == "mlx" else CROSS_PLATFORM_DEFAULT_MODEL)
    data["source"] = os.path.basename(audio)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    if os.path.abspath(produced) != out_json and os.path.isfile(produced):
        os.remove(produced)

    print(f"[{TOOL}] wrote {out_json} ({count} words, engine {picked})")
    return out_json


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Turn a recording into a word-by-word transcript with exact timings.",
        epilog="Example: transcribe.py raw_take.mp4 -o take.words.json",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("audio", help="Input audio or video file (mp4/mov/m4a/wav/mp3).")
    p.add_argument("-o", "--out", required=True, help="Output words JSON path.")
    p.add_argument("--engine", default="auto", choices=["auto", "mlx", "whisper", "whispercpp"],
                   help="Force an engine. Leave on auto unless there is a reason.")
    p.add_argument("--model", default=None,
                   help="Model name, or a model file path for whisper.cpp.")
    p.add_argument("--language", default="en",
                   help="Spoken language code. Empty string lets the engine detect it.")
    p.add_argument("--initial-prompt", default=None,
                   help="Topic and proper nouns, to cut mishears before they happen.")
    p.add_argument("--verbose", action="store_true", help="Stream engine progress.")
    args = p.parse_args(argv)

    transcribe(args.audio, args.out, engine=args.engine, model=args.model,
               language=args.language, initial_prompt=args.initial_prompt,
               verbose=args.verbose)


if __name__ == "__main__":
    main()
