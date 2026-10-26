#!/usr/bin/env python3
"""Export Instagram carousel slides from a 420px HTML preview to 1080x1350 PNGs.

Expected HTML selectors:
- .ig-frame
- .carousel-viewport
- .carousel-track
- optional .ig-header, .ig-dots, .ig-actions, .ig-caption

Usage:
  python3 export_carousel_slides.py --html carousel.html --out slides --slides 7
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Iterable

from PIL import Image

VIEW_W = 420
VIEW_H = 525
TARGET_W = 1080
TARGET_H = 1350
SCALE = TARGET_W / VIEW_W


async def export_slides(html_path: Path, output_dir: Path, total_slides: int, wait_ms: int = 3000) -> None:
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing Playwright Python package. Install with: python3 -m pip install playwright && python3 -m playwright install chromium"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    html_content = html_path.read_text(encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": VIEW_W, "height": VIEW_H},
            device_scale_factor=SCALE,
        )
        await page.set_content(html_content, wait_until="networkidle")
        await page.wait_for_timeout(wait_ms)

        await page.evaluate(
            """() => {
                document.querySelectorAll('.ig-header,.ig-dots,.ig-actions,.ig-caption')
                    .forEach(el => el.style.display='none');
                const frame = document.querySelector('.ig-frame');
                if (!frame) throw new Error('Missing .ig-frame');
                frame.style.cssText = 'width:420px;height:525px;max-width:none;border-radius:0;box-shadow:none;overflow:hidden;margin:0;';
                const viewport = document.querySelector('.carousel-viewport');
                if (!viewport) throw new Error('Missing .carousel-viewport');
                viewport.style.cssText = 'width:420px;height:525px;aspect-ratio:unset;overflow:hidden;cursor:default;';
                document.body.style.cssText = 'padding:0;margin:0;display:block;overflow:hidden;background:transparent;';
            }"""
        )
        await page.wait_for_timeout(500)

        for i in range(total_slides):
            await page.evaluate(
                """(idx) => {
                    const track = document.querySelector('.carousel-track');
                    if (!track) throw new Error('Missing .carousel-track');
                    track.style.transition = 'none';
                    track.style.transform = 'translateX(' + (-idx * 420) + 'px)';
                }""",
                i,
            )
            await page.wait_for_timeout(400)
            out = output_dir / f"slide_{i + 1:02d}.png"
            await page.screenshot(
                path=str(out),
                clip={"x": 0, "y": 0, "width": VIEW_W, "height": VIEW_H},
            )
            print(f"exported {out}")
        await browser.close()


def verify_dimensions(paths: Iterable[Path]) -> None:
    bad = []
    for p in paths:
        with Image.open(p) as im:
            if im.size != (TARGET_W, TARGET_H):
                bad.append((str(p), im.size))
    if bad:
        details = "; ".join(f"{p}={size}" for p, size in bad)
        raise SystemExit(f"Dimension verification failed: {details}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a 420px Instagram carousel HTML preview to 1080x1350 PNG slides.")
    parser.add_argument("--html", required=True, help="Path to carousel.html")
    parser.add_argument("--out", required=True, help="Output slide directory")
    parser.add_argument("--slides", type=int, required=True, help="Total number of slides")
    parser.add_argument("--wait-ms", type=int, default=3000, help="Initial wait for fonts/assets")
    args = parser.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    output_dir = Path(args.out).expanduser().resolve()
    if not html_path.exists():
        raise SystemExit(f"HTML file not found: {html_path}")
    if args.slides < 1:
        raise SystemExit("--slides must be >= 1")

    asyncio.run(export_slides(html_path, output_dir, args.slides, wait_ms=args.wait_ms))
    exported = [output_dir / f"slide_{i + 1:02d}.png" for i in range(args.slides)]
    verify_dimensions(exported)
    print(f"verified {len(exported)} slides at {TARGET_W}x{TARGET_H}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
