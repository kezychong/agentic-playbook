# Skill Index

## Core skills in this pack

### 1. `ap-content-capture-core`

Use for all capture requests. It decides where a source goes, which extractor to use, how to write the note, and how to verify the save.

Triggers:

- "capture this"
- "save this to my vault"
- "add this to my second brain"
- "put this in my Obsidian inbox"

### 2. `ap-instagram-reel-capture`

Use for Instagram Reels that need metadata, caption extraction, audio transcription, or on-screen text extraction.

Preferred paths:

1. `yt-dlp` for public Reel metadata/video.
2. `ffmpeg` + Whisper/STT for audio transcript.
3. Frame/contact-sheet extraction + vision/OCR for on-screen text.
4. Supadata transcript + metadata API if yt-dlp is blocked (key in `.env`).

### 3. `ap-x-twitter-capture`

Use for X/Twitter posts, long posts, threads, quoted posts, screenshots, and X-hosted videos.

Works with nothing to set up: no X account, no developer keys, no cookies.

Preferred paths:

1. FxTwitter public reader (`https://api.fxtwitter.com/status/<id>`): text, author, quoted post, photos, videos, long-form X articles, thread links.
2. Videos in a post: fetch by link, `ffmpeg` frames + audio, `whisper-ctranslate2` (same route as Instagram).
3. `yt-dlp` if FxTwitter does not answer.
4. Official API via `xurl`, only if the member already set it up themselves.
5. Rare last resort: the member pastes the post's words.

### 4. `ap-youtube-video-capture`

Use for YouTube links, Shorts, transcripts, video notes, and summaries.

Preferred paths:

1. `youtube-transcript-api`.
2. `yt-dlp` subtitle/caption fallback.
3. `yt-dlp` video/audio download + `ffmpeg` + Whisper/STT.

### 5. `ap-web-article-capture`

Use for standard articles, blog posts, docs, newsletters, and webpages.

Preferred paths:

1. Hermes web extraction, if available.
2. Defuddle for clean markdown extraction.
3. Firecrawl for JS-heavy or cluttered pages.
4. Browser automation for blocked/interactive pages.

### 6. `ap-document-capture`

Use for PDFs, Google Docs, Google Drive files, DOCX, screenshots, and scanned documents.

Preferred paths:

1. Public URL extraction.
2. Google Docs export links when public.
3. Local PDF extraction with PyMuPDF.
4. OCR tools for scanned documents.

## API keys and alternatives

Read `API_KEYS_AND_ALTERNATIVES.md` before setup. Short version:

- No key needed for the pack itself.
- X/Twitter links need nothing: FxTwitter reads public posts with no key.
- Firecrawl may need an API key.
- Private Google files need Google auth outside chat.
- Cloud transcription/OCR may need keys.
- Local alternatives exist for most capture paths.

## Skills not included but useful

These are optional dependencies, not bundled secrets:

- `xurl`, official X/Twitter API CLI (optional; FxTwitter needs nothing).
- `yt-dlp`, media/caption downloader.
- `ffmpeg`, video/audio processing.
- `whisper`, local transcription.
- `defuddle`, clean web article extraction.
- `firecrawl`, web scraping/crawling.
- `pymupdf` / `marker-pdf`, PDF extraction/OCR.

## Installation model

These are product skill folders. They are safe to copy into:

```text
~/.hermes/skills/content-capture-pack/
```

Start a new Hermes session after installing skills so the skill loader can see them.
