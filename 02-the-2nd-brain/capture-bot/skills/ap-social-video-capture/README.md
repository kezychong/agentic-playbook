# Social Video Capture

Agentic Playbook public draft · 0.2.0

Capture one permitted public social-video transcript into a reviewable local draft.

## Before you start

You need an HTTPS URL on the helper's fixed public-media host allowlist and `yt-dlp`. The helper tries bounded platform captions first; local Whisper is the optional bounded fallback. No API key is required. Review [the full method](SKILL.md) before live use; loading this folder does not approve downloads, software installation, account access or writes to a real knowledge base.

## Try it safely

```bash
python3 scripts/fetch_social_transcript.py "https://example.com/video/123" --dry-run
python3 scripts/test_social_video_capture.py
```

Both commands avoid network and account access. The fixture check uses invented data.

## Live workflow

1. Run the helper with `--json` and no `--write`.
2. Review the source, transcript, method and caveats with the user.
3. Create and approve a real, empty local destination (not a symlink), then add `--write --out "./approved-capture-drafts"`.
4. Read the note back. The script refuses existing note paths.

## Limits and permissions

The default local-Whisper cap is 5,400 seconds and the hard cap is 21,600 seconds. Missing, zero or invalid duration metadata blocks audio download. Subprocess output, caption files, temporary download totals, audio and transcript reads have fixed byte ceilings; see `SKILL.md`. The helper rejects literal/private/internal hosts and secret-like query keys, strips common tracking keys, checks DNS immediately before each `yt-dlp` call, and only accepts listed platform domains. Because `yt-dlp` performs its own later DNS resolution and redirects, this reduces but cannot eliminate DNS-rebinding or redirect risk. The supplied route has no password, browser-cookie or session-file option.

## Included files

- [SKILL.md](SKILL.md) — method and boundaries.
- [scripts/fetch_social_transcript.py](scripts/fetch_social_transcript.py) — bounded CLI.
- [scripts/yt_media.py](scripts/yt_media.py) — shared local media helper used by this skill and `ap-channel-research`.
- [scripts/test_social_video_capture.py](scripts/test_social_video_capture.py) — offline fixture checks.

## Included dependencies

- [ap-content-capture-core](../ap-content-capture-core/README.md) — optional destination and note conventions.
- [ap-channel-research](../ap-channel-research/README.md) — uses the shared media helper for approved channel corpora.

## Setup, update and removal

Keep the complete folder with its scripts. Use the host's documented skill directory and check discovery in a fresh session. Back up an older version before updating. Remove only this installed skill folder after approval; preserve user-created notes and external tool configuration.
