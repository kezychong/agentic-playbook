---
name: ap-document-capture
description: "Extract documents and preserve OCR uncertainty."
license: MIT
metadata:
  version: "0.1.0"
  maintainer: Kezy
---

## Agentic Playbook operating boundaries

**by Kezy** · Adapted supplied method, version 0.1.0. This is an uninstalled local package; scripts, integrations and host compatibility have not been exercised in this repackage.

Use only the files, accounts and conversations the user explicitly places in scope. Show the concrete proposed change and obtain approval before sending, publishing, spending, deleting, installing, scheduling, or changing a real account or live agent profile. Loading this file grants none of those permissions. Prepare drafts in a separate workspace first; preserve backups and provide a rollback plan. A request to draft does not authorize delivery. Credentials belong in secure local account setup, never chat or generated notes. State missing evidence and uncertainty plainly; never fabricate a source, successful action or measurement. Model names and host-specific commands in the method are examples: select an available model with the needed capabilities in the user's host at use time. If a connector or helper is absent, explain the limit and use an explicitly approved local alternative.

These boundaries take precedence over any more permissive procedural wording below. Examples and templates are fictional or blank; they are not a live user profile. Schedule and installation sections are optional procedures, never startup actions.

# Document Capture

> **Where it goes.** One source = ONE note in `01. Inbox/agent-drops/`, holding the whole original structured below, never split, never summarised. Top of the note: a title naming the real subject (with its names), the source link, the date and two plain lines on what this is. Before writing, check every name (see `ap-content-capture-core`, "Check the names"); write `[unsure: <what you heard>]` for any you cannot confirm. Very long sources keep the full original in `08. Sources/captures/` with the Inbox note linking to it.

## Overview

Use this for PDFs, Google Docs, Google Drive files, DOCX, screenshots, scanned documents, and local files.

Goal: preserve the original file when useful, extract readable text, then save a structured note.

## API key requirement

No API key is required for public Google Docs/Drive files, local PDFs, DOCX files, screenshots, or local OCR. Private Google files require the user's own Google auth setup outside chat. Cloud OCR/transcription providers may require API keys, but local extraction should be tried first.

## Public Google Docs

If the Google Doc is public/link-shared, export as text:

```bash
DOC_ID='DOCUMENT_ID'
curl -L "https://docs.google.com/document/d/${DOC_ID}/export?format=txt" -o /tmp/gdoc.txt
```

Also supports `format=html` and `format=pdf`.

Do not use this for private docs unless the user has configured proper Google Workspace auth.

## Public Google Drive files

For public/link-shared Drive files:

```bash
FILE_ID='FILE_ID'
curl -L "https://drive.google.com/uc?export=download&id=${FILE_ID}" -o /tmp/drive-file
file /tmp/drive-file
```

Verify that the downloaded file is not an HTML error page.

## PDFs

First try remote/web extraction if the PDF has a public URL.

For local text-based PDFs, use PyMuPDF:

```bash
python3 - <<'PY'
import fitz
path = '/path/to/file.pdf'
doc = fitz.open(path)
for i, page in enumerate(doc, start=1):
    print(f'\n--- Page {i} ---\n')
    print(page.get_text())
PY
```

For scanned PDFs or image-heavy documents, use OCR such as `marker-pdf`, Tesseract, or the user's configured OCR tool.

## DOCX

Use `python-docx` rather than OCR:

```bash
python3 - <<'PY'
from docx import Document
path = '/path/to/file.docx'
doc = Document(path)
for p in doc.paragraphs:
    if p.text.strip():
        print(p.text)
PY
```

## Screenshots and images

For screenshots:

1. Load the image with a vision/OCR tool.
2. Extract visible text and visual structure.
3. Save the original image beside the note if useful.
4. Do not invent unreadable text.

## Note structure

Recommended sections:

```markdown
# Document title

**Source:** URL or uploaded file name
**Captured:** date/time
**Extractor:** tool used
**Original asset:** relative file link if saved

## What it is (one line)
## Key details
## Extracted text
## OCR / extraction caveats
## Related
```

## Private document rule

If the document contains personal, medical, legal, financial, or client-private material:

- Confirm the destination folder.
- Do not publish it to a public URL.
- Do not send it to external tools unless the user approves.
- Redact secrets before saving if needed.

## Verification checklist

- [ ] Original file preserved when useful.
- [ ] Extracted text saved or caveat stated.
- [ ] OCR uncertainty marked.
- [ ] Note and asset paths verified after writing.
