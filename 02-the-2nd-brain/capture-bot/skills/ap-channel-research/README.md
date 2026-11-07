# Channel Research

Agentic Playbook public draft · 0.2.0

Build a filtered transcript corpus only after the user approves the exact bounded channel manifest.

## Before you start

You need a public channel, `yt-dlp`, and the sibling `ap-social-video-capture` folder. The helper fetches bounded platform captions first; local Whisper is the optional bounded fallback. Review [the full method](SKILL.md) before live use. A general research request is not approval to fetch a whole channel.

## Try it safely

```bash
python3 scripts/channel_research.py "@example" --list-only --dry-run
python3 scripts/test_channel_research.py
```

Both commands avoid network and account access. The fixture check uses invented data.

## Required two-phase gate

1. Run `--list-only --manifest "./review/channel.json"` with bounded filters.
2. Show the exact manifest, extraction plan and printed SHA-256 to the user.
3. Stop until the user explicitly approves those exact bytes and SHA-256.
4. Create an empty real output directory, then run `--build --approved --approved-manifest "./review/channel.json" --approved-sha256 "PRINTED_SHA256" --out "./corpus"`.
5. Compare `_INDEX.md` with the approved manifest and report missing transcripts.

Changing even one manifest byte requires a new SHA-256 and new approval.

## Limits and permissions

The helper caps matches at 100, scans the full selected prefix of at most 500 until the match limit is met or the prefix is exhausted, caps per-video local transcription at 21,600 seconds, and pauses at least one second between videos. Probe failures are reported separately from a clean zero-match result. It inherits the social helper's host, DNS, byte and positive-duration limits. There is no unbounded or force mode.

## Included files

- [SKILL.md](SKILL.md) — method, approval gate and bounds.
- [scripts/channel_research.py](scripts/channel_research.py) — manifest-gated CLI.
- [scripts/test_channel_research.py](scripts/test_channel_research.py) — offline fixture checks.

## Included dependencies

- [ap-social-video-capture](../ap-social-video-capture/README.md) — required shared media helper.
- [ap-content-capture-core](../ap-content-capture-core/README.md) — optional destination and note conventions.

## Setup, update and removal

Keep this folder beside `ap-social-video-capture`. Use the host's documented skill directory and check discovery in a fresh session. Back up an older version before updating. Remove only this installed skill folder after approval; preserve corpora, approved manifests and external tool configuration.
