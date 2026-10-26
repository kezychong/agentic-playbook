#!/usr/bin/env python3
"""
thumbs.py - small cover pictures for the Viral and Calendar cards.

Standard library only.

Two safety rules, both non-negotiable:

1. Every address fetched is built here, from a post code that already appears
   in the member's own library or their own posted record. A caller can never
   hand this file a web address. Nothing outside the member's own workspace
   can decide what gets downloaded.

2. Nothing is embedded from anyone else's site. The picture is cached once
   into content-os/cockpit/covers/ and served from the member's own machine,
   so no card ever loads a frame from a third party.

Guards on every download: an eight-second limit, a five-megabyte ceiling, a
response that must actually be an image, and an atomic write. A failure is
normal and shows as "no preview" on the card, never as an error.

Only one platform publishes a cover picture without a sign-in, and only its
codes are recognised here. A post on any other platform simply has no
preview, which the card says plainly.
"""

import http.client
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT = 8
MAX_BYTES = 5 * 1024 * 1024
COVER_SIZES = ("l", "m")
COVER_URL_TMPL = "https://www.instagram.com/p/{code}/media/?size={size}"

CODE_RE = re.compile(r"^[A-Za-z0-9_-]{5,40}$")
SERVED_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,40}\.jpg$")


def _fetch_image(url: str):
    """The bytes behind an address, only when it passes every guard. Returns
    None on any failure, and never raises."""
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"}
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "")
            if not content_type.lower().startswith("image/"):
                return None
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_BYTES:
                return None
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                return None
            return data
    except urllib.error.HTTPError as exc:
        exc.close()
        return None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, http.client.HTTPException):
        return None


def cached_name(thumbs_dir: Path, code):
    """The served filename when that cover is already on disk, else None. A
    pure existence check: no network, no folder creation. Cheap enough to run
    once per card while building a response."""
    if not code or not isinstance(code, str) or not CODE_RE.match(code):
        return None
    name = f"{code}.jpg"
    return name if (Path(thumbs_dir) / name).is_file() else None


def _download_cover(thumbs_dir: Path, code: str):
    data = None
    for size in COVER_SIZES:
        data = _fetch_image(COVER_URL_TMPL.format(code=code, size=size))
        if data is not None:
            break
    if data is None:
        return None
    target = Path(thumbs_dir) / f"{code}.jpg"
    try:
        tmp = Path(thumbs_dir) / f".{code}.jpg.tmp{os.getpid()}"
        tmp.write_bytes(data)
        tmp.replace(target)
    except OSError:
        return None
    return target


def warm(thumbs_dir: Path, known_codes, limit: int = 80) -> dict:
    """Cache covers for the codes the workspace already knows about.

    `limit` caps downloads, not list positions, so a library bigger than the
    limit still warms all the way through across a few runs.

    Returns {"cached": n, "failed": m}. Already-cached covers count as cached
    and cost nothing. Never raises.
    """
    thumbs_dir = Path(thumbs_dir)
    codes, seen = [], set()
    for code in known_codes or []:
        if not isinstance(code, str) or not CODE_RE.match(code) or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    if not codes:
        return {"cached": 0, "failed": 0}
    try:
        thumbs_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"cached": 0, "failed": 0}

    cached, missing = 0, []
    for code in codes:
        if (thumbs_dir / f"{code}.jpg").is_file():
            cached += 1
        else:
            missing.append(code)
    failed = 0
    for code in missing[:limit]:
        if _download_cover(thumbs_dir, code) is not None:
            cached += 1
        else:
            failed += 1
    return {"cached": cached, "failed": failed}
