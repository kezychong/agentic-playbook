#!/usr/bin/env python3
"""Deterministic gate for a book-a-call VSL script. Run BEFORE the fresh-context judge.

Usage:
  vsl_gate.py <script.md> [--ledger proof-ledger.md] [--offer offer.md]
              [--min-minutes 15] [--max-minutes 20] [--wpm 150]
              [--mechanism-words "Your Method Name"] [--allow "Your Brand"]

Exit 0 = all gates pass. Exit 1 = at least one FAIL. Prints one line per gate.
The script body is everything between the first two `---` horizontal rules if present,
otherwise the whole file. `## Writer notes` and anything after it is never graded.
"""
import argparse
import re
import sys
from pathlib import Path

BRITISH = [
    r"\bcolour", r"\bfavour", r"\bbehaviour", r"\borganis", r"\brealis", r"\boptimis",
    r"\bcentre\b", r"\bprogramme\b", r"\bcatalogue\b", r"\blicence\b", r"\bdefence\b",
    r"\banalys(e|ed|ing)\b", r"\bpractis", r"\btravell", r"\bcancell", r"\bmodell",
]
BANNED_PHRASES = [
    "game-changer", "game changer", "unlock", "supercharge", "10x", "skyrocket",
    "limited spots", "only a few spots", "spots are filling", "act now", "don't miss out",
    "in today's fast-paced", "at the end of the day", "revolutionary", "cutting-edge",
    "leverage the power", "take your business to the next level", "no-brainer",
]
CALL_WORDS = re.compile(r"\b(book|schedule|apply for|claim)\b.{0,40}\b(call|session|conversation|slot)\b", re.I)
PRICE = re.compile(r"(\$|SGD|USD|S\$)\s?\d[\d,]*")
LEDGER_TAG = re.compile(r"<!--\s*(P-\d+)\s*-->")
LEDGER_ROW = re.compile(r"\b(P-\d{2,})\b")
MARKER = re.compile(r"^\s*\[(\d{1,2}):(\d{2})\]", re.M)


def body_of(text: str) -> str:
    text = re.split(r"^##\s+Writer notes", text, flags=re.I | re.M)[0]
    parts = re.split(r"^---\s*$", text, flags=re.M)
    if len(parts) >= 3:
        # frontmatter? if first part is empty and second looks like yaml, body is after 2nd rule
        if parts[0].strip() == "" and re.search(r"^\w+:", parts[1], re.M):
            rest = "---".join(parts[2:])
            sub = re.split(r"^---\s*$", rest, flags=re.M)
            return sub[1] if len(sub) >= 3 else rest
        return parts[1]
    return text


def spoken_words(body: str) -> str:
    # strip stage directions [B-ROLL: ...], (pause), markers, html comments, headings
    b = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    b = re.sub(r"\[(B-ROLL|SCREEN|CUT|SHOW|TITLE|CARD|PROOF|VIDEO|STRIPE LINK|BOOK LINK)[^\]]*\]", "", b, flags=re.I)
    b = MARKER.sub("", b)
    b = re.sub(r"^\s*#.*$", "", b, flags=re.M)
    b = re.sub(r"\((pause|beat|breath)[^)]*\)", "", b, flags=re.I)
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--ledger")
    ap.add_argument("--offer")
    ap.add_argument("--min-minutes", type=float, default=15)
    ap.add_argument("--max-minutes", type=float, default=20)
    ap.add_argument("--wpm", type=int, default=150)
    ap.add_argument("--mechanism-words", default="")
    ap.add_argument("--allow", default="", help="comma list of allowed CEO/COO strings")
    ap.add_argument("--early-words", type=int, default=250)
    ap.add_argument("--forbidden-role-words", default="", help="comma-separated role labels forbidden by this project")
    ap.add_argument("--price-allowed", action="store_true", help="offer.md permits price on video")
    a = ap.parse_args()

    raw = Path(a.script).read_text(encoding="utf-8")
    body = body_of(raw)
    spoken = spoken_words(body)
    words = re.findall(r"[A-Za-z0-9'’$%-]+", spoken)
    n = len(words)
    fails = 0

    def gate(gid, ok, detail):
        nonlocal fails
        print(f"{'PASS' if ok else 'FAIL'}  {gid:<6} {detail}")
        if not ok:
            fails += 1

    # G1 dashes
    dashes = len(re.findall(r"[ - –]", body))
    gate("G1", dashes == 0, f"em/en dashes: {dashes} (must be 0)")

    # G2 spelling
    brit = [p for p in BRITISH if re.search(p, body, re.I)]
    gate("G2", not brit, f"British spellings: {brit or 'none'}")

    # G3 length by wpm
    lo, hi = a.min_minutes * a.wpm, a.max_minutes * a.wpm
    est = n / a.wpm
    gate("G3", lo <= n <= hi, f"spoken words {n} ≈ {est:.1f} min at {a.wpm} wpm (window {int(lo)}-{int(hi)})")

    # G4 minute markers present and monotonic
    marks = [(int(m.group(1)), int(m.group(2))) for m in MARKER.finditer(body)]
    secs = [m * 60 + s for m, s in marks]
    mono = all(x < y for x, y in zip(secs, secs[1:]))
    gate("G4", len(marks) >= 6 and mono, f"[mm:ss] markers: {len(marks)} (need ≥6, monotonic={mono})")

    # G5 last marker within window
    last = secs[-1] / 60 if secs else 0
    gate("G5", secs and a.min_minutes - 3 <= last <= a.max_minutes, f"last marker at {last:.1f} min")

    # G6 no mechanism words early
    early = " ".join(words[: a.early_words]).lower()
    mech = [w.strip() for w in a.mechanism_words.split(",") if w.strip()]
    hits = [w for w in mech if w.lower() in early]
    gate("G6", not hits, f"mechanism words in first {a.early_words} words: {hits or 'none'}")

    # G7 no price unless allowed
    prices = PRICE.findall(spoken)
    gate("G7", a.price_allowed or not prices, f"price strings on video: {len(prices)} {'(allowed)' if a.price_allowed else '(must be 0; price lives on the call)'}")

    # G8 call CTA present, and not before 60% of the script
    cta = list(CALL_WORDS.finditer(spoken))
    first_pos = (spoken.find(cta[0].group(0)) / max(len(spoken), 1)) if cta else None
    gate("G8", bool(cta) and first_pos >= 0.6, f"call CTA occurrences: {len(cta)}; first at {f'{first_pos:.0%}' if cta else 'n/a'} of script (must be ≥60%)")

    # G9 for / not-for present
    notfor = re.search(r"\b(this is not for|not for you|don't book|do not book|please don't)\b", spoken, re.I)
    gate("G9", bool(notfor), "explicit not-for / disqualifier line present")

    # G10 what happens on the call described
    what = re.search(r"\b(on the call|on that call|during the call|the call is|the call isn't|the call is not)\b", spoken, re.I)
    gate("G10", bool(what), "describes what the call is / is not")

    # G11 banned phrases
    bp = [p for p in BANNED_PHRASES if p in spoken.lower()]
    gate("G11", not bp, f"banned phrases: {bp or 'none'}")

    # G12 ledger ids all exist
    tags = set(LEDGER_TAG.findall(body))
    if a.ledger:
        ledger_ids = set(LEDGER_ROW.findall(Path(a.ledger).read_text(encoding="utf-8")))
        missing = sorted(tags - ledger_ids)
        gate("G12", bool(tags) and not missing, f"ledger tags {len(tags)}; missing from ledger: {missing or 'none'}")
    else:
        gate("G12", len(tags) > 0, f"ledger tags present: {len(tags)} (no --ledger given, existence only)")

    # G13 CEO/COO outside allowlist
    allow = [w.strip() for w in a.allow.split(",") if w.strip()]
    scrub = spoken
    for w in allow:
        scrub = scrub.replace(w, "")
    role_words = [w.strip() for w in a.forbidden_role_words.split(",") if w.strip()]
    ceo = [w for w in role_words if re.search(r"\b" + re.escape(w) + r"\b", scrub)]
    gate("G13", not ceo, f"project-forbidden role words outside allowlist: {len(ceo)}")

    # G14 Writer notes present
    gate("G14", bool(re.search(r"^##\s+Writer notes", raw, re.I | re.M)), "## Writer notes section present")

    # G15 honesty disclosure does not open the proof section (heuristic: a 'I have not / first time / never run' line must not be first line after a PROOF marker)
    m = re.search(r"\[(?:PROOF|SHOW)[^\]]*\]\s*\n\s*([^\n]+)", body, re.I)
    opens = bool(m and re.search(r"\b(I have not|I haven't|first time|never run|never done)\b", m.group(1), re.I))
    gate("G15", not opens, "honesty disclosure does not open a proof block")

    print(f"\n{'ALL GATES PASS' if fails == 0 else f'{fails} GATE(S) FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
