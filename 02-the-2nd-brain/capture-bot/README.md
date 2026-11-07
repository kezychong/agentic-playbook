# Capture Bot

**Agentic Playbook — by Kezy**

This is one package, retaining the supplied grouping and its supporting files. It is a local source draft, not an installed or runtime-tested system.

## Included skills
- [Content Capture Core](skills/ap-content-capture-core/README.md): Route full-source captures into a verified vault note.
- [Channel Research](skills/ap-channel-research/README.md): Build a bounded transcript corpus only after approval of the exact channel manifest.
- [Document Capture](skills/ap-document-capture/README.md): Extract documents and preserve OCR uncertainty.
- [Instagram Reel Capture](skills/ap-instagram-reel-capture/README.md): Capture Reel speech, captions and visible context.
- [Social Video Capture](skills/ap-social-video-capture/README.md): Capture one public social-video transcript into a reviewable local draft.
- [Web Article Capture](skills/ap-web-article-capture/README.md): Save a complete article with source and caveats.
- [X Twitter Capture](skills/ap-x-twitter-capture/README.md): Capture posts, threads and media with provenance.
- [Youtube Video Capture](skills/ap-youtube-video-capture/README.md): Capture a full video transcript with timestamps.

## Setup
1. Read each included skill README and its prerequisites.
2. Keep every skill folder and all its support files together.
3. Review the documented host setup before copying anything into an installation.
4. Use fictional inputs first. Loading a skill does not approve installation, external actions or spending.
5. For whole-channel research, review the generated bounded manifest and approve its exact SHA-256 before any transcript or audio downloads.

[Host setup guide](../../08-setup-guides-tools-connections/manual-setup.md)


## Limits and reuse
Content Capture Core, Channel Research and Social Video Capture have offline regression checks. The two new media helpers also have standalone offline dry-runs; the other five included skills are documentation source drafts and are not fixture-tested by this package. Live platform access, redirect behavior, account connections, installations and host compatibility remain untested. Some optional components need additional software, verified compatibility or paid access. Preserve required legal notices. The collection is maintained by Kezy; no new blanket redistribution licence is implied.
