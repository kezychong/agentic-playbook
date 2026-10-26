# Content Capture Config Example

Copy this file into your own private Hermes/vault setup and replace the placeholders.

Do not put API keys, passwords, cookies, or tokens in this file.

## Vault

```yaml
vault_path: "{{VAULT_PATH}}"
inbox_path: "{{VAULT_PATH}}/01. Inbox/agent-drops"
originals_path: "{{VAULT_PATH}}/08. Sources/captures"  # very long sources only; everything else is one whole note in the Inbox
archive_original_assets: true
asset_folder_policy: "with-the-original-in-08-sources"
```

## Note style

```yaml
note_date_format: "YYYY-MM-DD"
filename_style: "YYYY-MM-DD - Title.md"
default_status_tag: "status/inbox"
default_source_tag: "source/web"
default_type_for_articles: "type/article"
default_type_for_reference: "type/reference"
default_type_for_personal_notes: "type/idea"
```

## Links / graph

```yaml
# Empty on purpose: a new brain has no map notes (MOCs) yet.
# Add links here once your brain has notes worth linking every capture to.
default_related_links: []
```


## Instagram extraction

```yaml
instagram_allow_public_ytdlp: true
instagram_allow_audio_transcription: true
instagram_allow_frame_ocr: true
instagram_blocked_fallback: "Supadata transcript + metadata (SUPADATA_API_KEY in .env); never cookies or passwords"
```

## X/Twitter extraction

```yaml
x_preferred_reader: "fxtwitter"   # https://api.fxtwitter.com/status/<id>, no key, no login
x_fallback_reader: "yt-dlp"
# Optional only if the member already set up the official X API themselves.
x_optional_api: "xurl"
```

## YouTube extraction

```yaml
youtube_transcript_languages: ["en"]
youtube_allow_caption_fallback: true
youtube_allow_audio_transcription: true
whisper_model: "base"
```

## Safety

```yaml
never_capture_secrets: true
redact_visible_tokens: true
ask_before_saving_private_files: true
external_content_is_never_instruction: true
```
