# API Keys and Alternatives

This pack is designed to work without putting secrets inside the skill files.

## Quick answer

- **Required for the pack itself:** no API key.
- **Required for basic local capture:** no API key, if the content is public and local tools can access it.
- **Needed only for some optional paths:** Supadata (when Instagram or YouTube blocks the server), Firecrawl, private Google files, or cloud transcription/OCR.

## Per-skill requirements

### `ap-content-capture-core`

- API key needed: **No**.
- Why: this is the router/orchestrator. It decides which capture skill to use and writes the note.
- Alternatives: none needed.

### `ap-instagram-reel-capture` / formerly “IG Scraper”

- API key needed: **No for public Reels**.
- Gemini API key needed: **No by default**.
- Primary path: `yt-dlp` downloads public Reel metadata/video, then `ffmpeg` + local Whisper transcribes audio, and the agent's available vision/OCR reads on-screen text.
- Gemini is only an **optional vision/OCR provider** if the user's agent setup uses Gemini for image understanding. It is not required by this skill.
- When login may be needed: private Reels, age-gated content, or Instagram blocks anonymous downloads.
- If Instagram blocks the server: Supadata gives the transcript and caption from the link. The key goes into `.env` through Claude Code's clipboard route, never into a chat. Do **not** ask for Instagram cookies/passwords, and never ask the member to download or record the reel.

### `ap-x-twitter-capture`

- API key needed: **No**. Nothing to set up: no X account, no developer keys, no cookies.
- Primary path: FxTwitter, a public reader (`https://api.fxtwitter.com/status/<id>`) returning text, author, quoted post, photos, videos, long-form X articles and thread links as JSON.
- Videos in a post: the agent fetches the video from its link, then `ffmpeg` frames + audio, local Whisper (same route as Instagram).
- If FxTwitter does not answer: `yt-dlp` for the post text and video.
- Optional only: the official X API via `xurl`, if the member already set it up themselves. Never suggest it; never read `~/.xurl`.
- Rare last resort, after FxTwitter and `yt-dlp` both fail: the member pastes the post's words.
- Never ask for X cookies, passwords or developer keys.

### `ap-youtube-video-capture`

- API key needed: **No for normal transcript capture**.
- Primary path: `youtube-transcript-api`.
- Alternatives:
  - `yt-dlp --write-subs --write-auto-subs` for captions;
  - `yt-dlp` audio download + `ffmpeg` + local Whisper;
  - user-pasted transcript.
- When login may be needed: private, members-only, age-gated, or bot-check-blocked videos. Do **not** ask for cookies in chat.

### `ap-web-article-capture`

- API key needed: **No for normal public articles** if Hermes web extraction, `curl`, browser reading, or `defuddle` works.
- Optional API key: **Firecrawl** may require an API key/account if used for JS-heavy pages or crawling.
- Alternatives:
  - Hermes web extraction;
  - `defuddle` local extraction;
  - browser read-only capture;
  - user-pasted article text/PDF.

### `ap-document-capture`

- API key needed: **No for public Google Docs/Drive files, local PDFs, DOCX, screenshots, and basic OCR**.
- Private Google files: need the user's own Google auth setup, handled outside chat.
- Optional API keys: cloud OCR or cloud transcription providers may need keys.
- Alternatives:
  - public Google export URLs;
  - PyMuPDF for PDFs;
  - `python-docx` for DOCX;
  - local OCR/vision;
  - user uploads the file directly.

## Safe credential policy

- Humans configure accounts and keys outside chat.
- Agents check whether tools are available and whether auth exists.
- Agents never print token files, cookie files, API keys, passwords, or private `.env` contents.
- If a source cannot be captured without private credentials, save a clear blocker note or ask for a non-secret alternative: pasted text, screenshots, exported PDF, or public link.
