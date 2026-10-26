#!/usr/bin/env bash
set -euo pipefail
# Agentic Playbook — by Kezy. Optional, unexecuted installer.
# Run only after the owner reviews target paths and approves installation.
[ "${1:-}" = "--approved" ] || { echo "Review README.md; explicit --approved required." >&2; exit 2; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${2:?Provide an approved host skill-directory path}"
for name in ap-content-capture-core ap-document-capture ap-instagram-reel-capture ap-web-article-capture ap-x-twitter-capture ap-youtube-video-capture; do
  [ -d "$ROOT/../$name" ] || { echo "Missing required sibling: $name" >&2; exit 1; }
  [ ! -e "$DEST/$name" ] || { echo "Conflict: $DEST/$name; back up and resolve manually." >&2; exit 1; }
done
mkdir -p "$DEST"
for name in ap-content-capture-core ap-document-capture ap-instagram-reel-capture ap-web-article-capture ap-x-twitter-capture ap-youtube-video-capture; do
  cp -R "$ROOT/../$name" "$DEST/$name"
done
echo "Copied six complete skill folders. No scheduler or helper was executed. Verify host discovery manually."
