#!/usr/bin/env bash
set -euo pipefail

echo "Hermes Content Capture Pack — health check"
echo

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    local path
    path="$(command -v "$cmd")"
    echo "[ok] $cmd -> $path"
  else
    echo "[missing optional] $cmd"
  fi
}

check_cmd hermes
check_cmd python3
check_cmd curl
check_cmd jq
check_cmd yt-dlp
check_cmd ffmpeg
check_cmd ffprobe
check_cmd whisper-ctranslate2
check_cmd defuddle
check_cmd firecrawl
check_cmd tesseract


if command -v curl >/dev/null 2>&1 && curl -s -m 15 -A 'Mozilla/5.0' https://api.fxtwitter.com/status/20 | grep -q '"code":200'; then
  echo "[ok] X/Twitter reader (FxTwitter, no key)"
else
  echo "[retry later] X/Twitter reader (FxTwitter) did not answer; yt-dlp is the fallback"
fi

echo
# Hermes runs its own bundled Python, which does not see packages installed
# for the system Python. Check packages with Hermes's Python when it exists.
HERMES_PY="$(ls -d "${HERMES_HOME:-$HOME/.hermes}"/tools/python-3*/bin/python3 2>/dev/null | head -1 || true)"
PY_BIN="${HERMES_PY:-python3}"
echo "Python package checks (using $PY_BIN)"
"$PY_BIN" - <<'PY'
mods = [
    ('youtube_transcript_api', 'YouTube transcript extraction'),
    ('fitz', 'PyMuPDF PDF extraction'),
    ('docx', 'DOCX extraction'),
]
for mod, label in mods:
    try:
        __import__(mod)
        print(f"[ok] {mod} — {label}")
    except Exception:
        print(f"[missing optional] {mod} — {label}")
PY

echo
if [ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/fetch_youtube_transcript.py" ]; then
  echo "[ok] scripts/fetch_youtube_transcript.py"
else
  echo "[missing] scripts/fetch_youtube_transcript.py"
fi

echo "Done. Missing optional tools only matter for that source type."
