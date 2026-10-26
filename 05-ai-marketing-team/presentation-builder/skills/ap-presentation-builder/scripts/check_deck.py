#!/usr/bin/env python3
"""Visual + behaviour check for a presentation-builder deck (Jarvis layer).

The Agentic Playbook method says "open the deck in a browser and inspect every slide at
1600x900 and 1280x720" — this does that headlessly so Jarvis can do it from Telegram:

  - screenshots every slide at both sizes (for the agent to look at)
  - flags: content overflowing / clipped by the slide, headlines over 3 lines,
    supporting copy over 3 lines, SVG labels under 18px, SVGs without aria-label,
    wrong slide counter, console/page errors, web fonts that failed to load,
    presenter/notes-window code (not allowed in this version)
  - tests navigation: Right/Space/Left/Home/End, URL hash, progress bar at 100% on the end
  - writes contact_sheet.png (1600x900 shots, numbered grid on graphite) for the preview
  - optionally writes a PDF of every slide (--pdf) so Kezy can flip through on his phone

Usage:
  check_deck.py --html <abs>/<slug>.html --out <abs>/check [--pdf <abs>/<slug>.pdf]
Exit: 0 clean (warnings allowed), 1 issues to fix, 2 could not run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZES = [(1600, 900), (1280, 720)]
BG = (14, 16, 19)          # graphite #0e1013
LABEL = (172, 180, 192)    # grey #ACB4C0
SHEET_W = 1240
GAP = 16
LABEL_H = 28

SLIDE_CHECK_JS = r"""
(idx) => {
  const slides = document.querySelectorAll('.slide');
  const s = slides[idx];
  const issues = [], warnings = [];
  if (!s) return {issues: ['slide missing'], warnings};
  if (!s.classList.contains('active')) issues.push('slide did not become active when navigated to');
  const r = s.getBoundingClientRect();
  if (s.scrollHeight > s.clientHeight + 2 || s.scrollWidth > s.clientWidth + 2)
    issues.push('content is taller/wider than the slide (overflow)');
  const short = el => (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40);
  s.querySelectorAll('h1,h2,h3,p,li,.eyebrow,.card,.big-number,svg,img,table').forEach(el => {
    const b = el.getBoundingClientRect();
    if (!b.width && !b.height) return;
    if (b.left < r.left - 1 || b.right > r.right + 1 || b.top < r.top - 1 || b.bottom > r.bottom + 1)
      issues.push(`cut off by the slide edge: <${el.tagName.toLowerCase()}> "${short(el)}"`);
  });
  const lines = el => {
    const cs = getComputedStyle(el);
    let lh = parseFloat(cs.lineHeight);
    if (!lh) lh = parseFloat(cs.fontSize) * 1.2;
    return Math.round(el.getBoundingClientRect().height / lh);
  };
  s.querySelectorAll('h1,h2').forEach(h => {
    const n = lines(h);
    if (n > 3) issues.push(`headline runs to ${n} lines — rewrite shorter: "${short(h)}"`);
  });
  s.querySelectorAll('.sub').forEach(p => {
    const n = lines(p);
    if (n > 3) warnings.push(`supporting copy runs to ${n} lines: "${short(p)}"`);
  });
  s.querySelectorAll('svg text').forEach(t => {
    const fs = parseFloat(getComputedStyle(t).fontSize);
    if (fs < 18) issues.push(`SVG label under 18px (${fs}px): "${short(t)}"`);
  });
  s.querySelectorAll('svg').forEach(svg => {
    if (svg.closest('[aria-hidden="true"]')) return;
    if (svg.getBoundingClientRect().width > 60 && !svg.getAttribute('aria-label'))
      warnings.push('diagram SVG has no aria-label');
  });
  const c = s.querySelector('.counter');
  if (c && parseInt(c.textContent, 10) !== idx + 1)
    issues.push(`slide counter says "${c.textContent.trim()}" but this is slide ${idx + 1}`);
  return {issues, warnings};
}
"""

FONTS_JS = r"""
() => {
  const failed = [...document.fonts].filter(f => f.status === 'error').map(f => f.family.replace(/"/g, ''));
  const loaded = new Set([...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/"/g, '')));
  const wanted = new Set();
  document.querySelectorAll('h1,h2,.sub,.eyebrow,body').forEach(el => {
    const first = getComputedStyle(el).fontFamily.split(',')[0].trim().replace(/["']/g, '');
    if (first && !/^(serif|sans-serif|monospace|system-ui)$/i.test(first)) wanted.add(first);
  });
  const missing = [...wanted].filter(f => !loaded.has(f));
  return {failed: [...new Set(failed)], missing};
}
"""


def load_font(size: int):
    for path in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNS.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(shots: list[Path], out: Path) -> None:
    n = len(shots)
    cols = n if n <= 3 else (3 if n <= 9 else 4)
    rows = math.ceil(n / cols)
    tw = (SHEET_W - (cols + 1) * GAP) // cols
    th = round(tw * 9 / 16)
    sheet = Image.new("RGB", (SHEET_W, rows * (th + LABEL_H) + (rows + 1) * GAP), BG)
    draw = ImageDraw.Draw(sheet)
    font = load_font(18)
    for i, p in enumerate(shots):
        r, c = divmod(i, cols)
        x, y = GAP + c * (tw + GAP), GAP + r * (th + LABEL_H + GAP)
        with Image.open(p) as im:
            sheet.paste(im.convert("RGB").resize((tw, th), Image.LANCZOS), (x, y + LABEL_H))
        draw.text((x, y + 4), f"{i + 1:02d}", fill=LABEL, font=font)
    sheet.save(out)


def write_pdf(shots: list[Path], out: Path) -> None:
    pages = [Image.open(p).convert("RGB") for p in shots]
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=200)
    for im in pages:
        im.close()


async def run(html: Path, out: Path, pdf: Path | None, wait_ms: int) -> int:
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError:
        print("could not run: Playwright missing for this Python")
        return 2

    source = html.read_text(encoding="utf-8")
    report: dict = {"deck": str(html), "issues": [], "warnings": []}
    if re.search(r"window\.open\(|BroadcastChannel|speaker-?notes|presenter", source, re.I):
        report["issues"].append("presenter/notes-window code found — this version is one clean audience deck only")

    shots_main: list[Path] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for w, h in SIZES:
            tag = f"{w}x{h}"
            scale = 2 if (w, h) == SIZES[0] else 1  # crisp shots for the PDF
            page = await browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale,
                                          reduced_motion="reduce")
            errors: list[str] = []
            page.on("console", lambda m, e=errors: m.type == "error" and e.append(m.text))
            page.on("pageerror", lambda exc, e=errors: e.append(str(exc)))
            await page.goto(html.as_uri() + "#1", wait_until="networkidle")
            await page.evaluate("document.fonts.ready.then(() => true)")
            await page.wait_for_timeout(wait_ms)

            n = await page.evaluate("document.querySelectorAll('.slide').length")
            if not n:
                print("could not run: no .slide elements found")
                await browser.close()
                return 2
            report["slides"] = n
            shot_dir = out / tag
            shot_dir.mkdir(parents=True, exist_ok=True)
            for i in range(n):
                await page.evaluate(f"location.hash = '#{i + 1}'")
                await page.wait_for_timeout(350)
                res = await page.evaluate(SLIDE_CHECK_JS, i)
                report["issues"] += [f"slide {i + 1} @ {tag}: {x}" for x in res["issues"]]
                report["warnings"] += [f"slide {i + 1} @ {tag}: {x}" for x in res["warnings"]]
                shot = shot_dir / f"slide_{i + 1:02d}.png"
                await page.screenshot(path=str(shot))
                if tag == "1600x900":
                    shots_main.append(shot)

            if tag == "1600x900":
                fonts = await page.evaluate(FONTS_JS)
                for f in fonts["failed"]:
                    report["warnings"].append(f"web font failed to load: {f} (offline? fallback font used)")
                for f in fonts["missing"]:
                    report["warnings"].append(f"font not loaded, fallback used: {f}")
                nav = []
                async def expect(key: str, want: int) -> None:
                    await page.keyboard.press(key)
                    await page.wait_for_timeout(150)
                    got = await page.evaluate("location.hash")
                    if got != f"#{want}":
                        nav.append(f"{key} should go to slide {want}, went to {got or 'nothing'}")
                await page.evaluate("location.hash = '#1'")
                await page.wait_for_timeout(200)
                await expect("End", n)
                width = await page.evaluate("(document.querySelector('.progress')||{style:{}}).style.width")
                if width != "100%":
                    nav.append(f"progress bar on last slide is {width or 'missing'}, not 100%")
                await expect("Home", 1)
                if n >= 3:
                    await expect("ArrowRight", 2)
                    await expect("Space", 3)
                    await expect("ArrowLeft", 2)
                report["issues"] += [f"navigation: {x}" for x in nav]
            report["issues"] += [f"browser error @ {tag}: {e}" for e in errors]
            await page.close()
        await browser.close()

    sheet = out / "contact_sheet.png"
    contact_sheet(shots_main, sheet)
    report["contact_sheet"] = str(sheet)
    if pdf:
        write_pdf(shots_main, pdf)
        report["pdf"] = str(pdf)
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    for line in report["issues"]:
        print(f"FIX   {line}")
    for line in report["warnings"]:
        print(f"WARN  {line}")
    print(f"checked {report['slides']} slides at {', '.join(f'{w}x{h}' for w, h in SIZES)} — "
          f"{len(report['issues'])} issue(s), {len(report['warnings'])} warning(s)")
    print(f"screenshots: {out}/1600x900 and {out}/1280x720 · contact sheet: {sheet}"
          + (f" · pdf: {pdf}" if pdf else ""))
    return 1 if report["issues"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Visual + behaviour check for an HTML deck.")
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True, help="Folder for screenshots, contact sheet, report")
    ap.add_argument("--pdf", help="Also write a PDF of every slide here")
    ap.add_argument("--wait-ms", type=int, default=1500, help="Extra wait for web fonts")
    args = ap.parse_args()
    html = Path(args.html).expanduser().resolve()
    if not html.exists():
        print(f"could not run: deck not found: {html}")
        return 2
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    pdf = Path(args.pdf).expanduser().resolve() if args.pdf else None
    return asyncio.run(run(html, out, pdf, args.wait_ms))


if __name__ == "__main__":
    sys.exit(main())
