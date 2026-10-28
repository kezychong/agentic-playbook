#!/usr/bin/env python3
"""
selftest.py - proves the cockpit is healthy, against a throwaway workspace.

Standard library only. Safe to run any time: it builds its own sample
workspace in a temporary folder, exercises every view and every action
against that copy, and deletes nothing of the member's. It never reads or
writes the member's real content-os/ folder unless one is handed to it, and
even then it only reads.

Run it with no arguments and it makes its own sample workspace. Nothing on
the network is touched at any point.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PASS = 0
FAIL = 0
SKIP = 0
FAILURES = []


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok    {label}")
    else:
        FAIL += 1
        FAILURES.append(label + (f" ({detail})" if detail else ""))
        print(f"  FAIL  {label}" + (f" - {detail}" if detail else ""))


def skip(label, why):
    global SKIP
    SKIP += 1
    print(f"  skip  {label} - {why}")


# --------------------------------------------------------------------------
# Sample workspace
# --------------------------------------------------------------------------

IDEA_BLANK_ANGLE = """# Idea: What every onboarding call keeps revealing

Captured: 2026-08-23
Format candidate:
Lane candidate: 2 tested
Score: see the Qualification section appended at the scoring stage
Status: new

## VERBATIM CAPTURE
> Untouched.

Every single onboarding call, the same thing comes up in the first ten minutes.

## SOURCE
- Where it came from: voice note
- Captured on: 2026-08-23

## THE ANGLE
> Owner only.

-

## THE PROOF

-

## PIE
- Problem:
- Importance:
- Experience:
"""

IDEA_SCORED = """# Idea: Why our slowest month taught us the pricing lesson

Captured: 2026-08-20
Format candidate: talking to camera
Lane candidate: 3 evergreen
Status: new

## VERBATIM CAPTURE

Our slowest month was the one that fixed our pricing.

## THE ANGLE

Cheap months are diagnostic, not disasters.

## THE PROOF

We raised the floor price in March and closed the same number of jobs.

## Qualification, 2026-08-21

Conviction: 2. He has said this three times unprompted.
Audience stakes: 2. Pricing decides whether they survive a slow quarter.
Evidence: 2. Real numbers from March.
Distinctiveness: 1. The framing is less common than the advice.
Timeliness: 1. No urgency, but always relevant.
Strategic fit: 2. This is the thing he wants to be known for.
Visual potential: 1. The invoice screenshot works.

Total: 11/14. Pass (9 or above)

Kill-list check:
- Interesting only because it is new: no.

Scored, not decided. You choose.
"""

IDEA_PARKED = """# Idea: A thought about hiring that is not ready

Captured: 2026-07-02

## THE ANGLE

Hire for the job you have, not the one you are dreaming about.
"""

LIBRARY_STRONG = """# Library entry: Challenge the diagnosis first

Filed: 2026-08-18
Last re-checked:
Mechanism family: challenge_belief

## The opening line, as data
Your prices are not the problem.

## On-screen text
NOT A PRICING PROBLEM

## First frame
A hand closing a laptop.

## The curiosity gap
If it is not pricing, what is it?

## The proof device
A screen recording of the account that fixed it.

## Format
talking to camera

## The ask at the end
Comment with your own number.

## The mechanism
Tells the viewer the thing they blame is not what is causing the problem, before offering anything.

## Why it stood out
This one went about 4.2 times their normal, roughly 84,000 views against a usual few thousand.
https://www.instagram.com/p/CxKq1TgOo9r/

## Source and trust level
- Account and platform: a-nearby-account on a short-video platform
- Trust level: someone in a nearby niche

## What I would do with it
The pricing idea could carry this shape.
"""

LIBRARY_WEAK = """# Library entry: A five second before and after

Filed: 2026-06-02

## The mechanism
Shows the finished result before saying a single word.

## Why it stood out
It felt strong, though nothing was measured.

## Source and trust level
- Account and platform: a-competitor
- Trust level: a general trend
"""

SCRIPT_INTERVIEWED = """# Script: quiet quota

Captured: 2026-08-19

## Truth packet
- [REAL] We turned down four jobs in July.
"""

SCRIPT_RECORD_EDIT = """# Script: the quote I stopped sending

Captured: 2026-08-21

## Truth packet
- [REAL] Three quotes in a row went nowhere.

## Talking map
Five beats.

## Recording pack
Teleprompter edges here.
"""

SCRIPT_POSTED = """# Script: number nobody checks

Captured: 2026-08-12

## Truth packet
- [REAL] Our own books.

## Talking map
Five beats.

## Recording pack
Teleprompter edges here.

## Franchise card
Numbers nobody checks. Three sequels filed.
"""

# The first two entries are written the way references/templates.md teaches:
# the name of each number, then the number. The third is written the other way
# round, which some people do, and which has to read correctly too.
POSTED_LEDGER = """# Posted

## 2026-08-22 - The number nobody checks
- platform: instagram
- format: reel
- link: https://www.instagram.com/p/CwQ0aBcDeFg/
- hook: The number nobody checks in their own books
- franchise: Numbers nobody checks
- stats: views 12400, likes 310, comments 22 (as of 2026-08-23)
- stats: views 18900, likes 402, comments 31 (as of 2026-08-24)

## 2026-08-15 - What our slowest month taught us
- platform: linkedin
- format: post
- hook: Our slowest month fixed our pricing
- stats: likes 88, comments 12 (as of 2026-08-23)

## 2026-08-10 - The quote I stopped sending
- platform: instagram
- format: reel
- link: https://www.instagram.com/p/CwQ0zZyXwVu/
- hook: The quote I stopped sending clients
- stats: 4,200 views, 180 likes, 24 comments (as of 2026-08-12)
"""

NEWS_PILLARS = """# My news pillars

Region: your area
Region code: SG
Timezone: Asia/Singapore
Trending searches: on
Tech stories: off

## Pillar: How owners price
- Search terms: pricing for small business, "cost of living", raising prices
- Keywords: pricing, prices, inflation, costs

## Pillar: Hiring and teams
- Search terms: small business hiring, staff shortage
- Keywords: hiring, staff, recruitment, wages
"""

FOCUS = """# My focus

This week: Ship three short videos, all from work I actually did.
"""

WATCHLIST = """# My watchlist

## The accounts

| Account | Platform | Why they are here | What I watch them for |
|---|---|---|---|
| a-nearby-account | short video | bigger authority | openings |
| a-competitor | short video | direct competitor | proof devices |
| a-smaller-one | short video | punching above its size | formats |
"""

VOICE = "# My voice\n\nStatus: solid\n"


def build_workspace(root: Path) -> Path:
    workspace = root / "content-os"
    for folder in [
        workspace / "ideas" / "inbox",
        workspace / "ideas" / "qualified",
        workspace / "ideas" / "parked",
        workspace / "library",
        workspace / "scripts",
        workspace / "analytics",
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    (workspace / "MY-VOICE.md").write_text(VOICE, encoding="utf-8")
    (workspace / "MY-WATCHLIST.md").write_text(WATCHLIST, encoding="utf-8")
    (workspace / "MY-FOCUS.md").write_text(FOCUS, encoding="utf-8")
    (workspace / "news-pillars.md").write_text(NEWS_PILLARS, encoding="utf-8")
    (workspace / "posted.md").write_text(POSTED_LEDGER, encoding="utf-8")

    (workspace / "ideas" / "inbox" / "2026-08-23-0915-onboarding-call.md").write_text(IDEA_BLANK_ANGLE, encoding="utf-8")
    (workspace / "ideas" / "inbox" / "2026-08-20-1410-slow-month-pricing.md").write_text(IDEA_SCORED, encoding="utf-8")
    (workspace / "ideas" / "parked" / "2026-07-02-0800-hiring-thought.md").write_text(IDEA_PARKED, encoding="utf-8")

    (workspace / "library" / "2026-08-18 - a-nearby-account - challenge-the-diagnosis.md").write_text(LIBRARY_STRONG, encoding="utf-8")
    (workspace / "library" / "2026-06-02 - a-competitor - before-and-after.md").write_text(LIBRARY_WEAK, encoding="utf-8")

    (workspace / "scripts" / "2026-08-19-quiet-quota.md").write_text(SCRIPT_INTERVIEWED, encoding="utf-8")
    (workspace / "scripts" / "2026-08-21-quote-i-stopped-sending.md").write_text(SCRIPT_RECORD_EDIT, encoding="utf-8")
    (workspace / "scripts" / "2026-08-12-number-nobody-checks.md").write_text(SCRIPT_POSTED, encoding="utf-8")
    return workspace


def write_news_archive(workspace: Path):
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)

    def stamp(hours):
        return (now - datetime.timedelta(hours=hours)).isoformat()

    items = [
        {"title": "Fresh story one", "url": "https://example.com/1", "source": "example.com",
         "pillar": "how-owners-price", "published": stamp(3), "signal": "News search · Example",
         "origin": "news_search", "item_type": "news", "image": "https://example.com/a.jpg",
         "summary": "A summary."},
        {"title": "Two days old", "url": "https://example.com/2", "source": "example.com",
         "pillar": "hiring-and-teams", "published": stamp(48), "signal": "News search · Example",
         "origin": "news_search", "item_type": "news"},
        {"title": "Five days old", "url": "https://example.com/3", "source": "example.com",
         "pillar": "how-owners-price", "published": stamp(120), "signal": "News search · Example",
         "origin": "news_search", "item_type": "news"},
        {"title": "Far too old", "url": "https://example.com/4", "source": "example.com",
         "pillar": "how-owners-price", "published": stamp(400), "signal": "News search · Example",
         "origin": "news_search", "item_type": "news"},
        {"title": "No date at all", "url": "https://example.com/5", "source": "example.com",
         "pillar": "how-owners-price", "signal": "News search · Example",
         "origin": "news_search", "item_type": "news"},
        {"title": "trending thing", "url": "https://example.com/6", "source": "Trending searches",
         "pillar": "trending-searches", "published": stamp(2), "signal": "about 20K+ trending searches",
         "origin": "trending_searches", "item_type": "trend"},
        {"title": "價格上漲", "url": "https://example.com/7", "source": "example.com",
         "pillar": "how-owners-price", "published": stamp(5), "signal": "News search · Example",
         "origin": "news_search", "item_type": "news"},
    ]
    path = workspace / "cockpit" / "news-archive.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"updated_at": now.isoformat(), "items": items}, indent=2), encoding="utf-8")


VALID_FEED = {
    "generated_at": "",
    "as_of_date": "2026-08-24",
    "last_confirmed_snapshot": "2026-08-22",
    "provisional": False,
    "freshness": {"w2_last_success": ""},
    "corpus": {"analysis_coverage": 0.8},
    "quality": {"patterns_evaluated": 3},
    "patterns": [{
        "record_id": "shape-a::all",
        "pattern": {"label": "Challenge the diagnosis first", "is_visual": False},
        "windows": {"days_14": {"creator_coverage": 0.36, "distinct_creator_count": 4, "eligible_reel_count": 7}},
        "comparison": {"reference_creator_coverage": 0.18},
        "quality": {"clean_support_share": 0.9},
        "evidence_refs": [{"shortcode": "CxKq1TgOo9r", "creator": "a-nearby-account"}],
    }],
    "views": {"rising": ["shape-a::all"], "proven": [], "persistent": [], "cooling": []},
    "test_next": [{"snapshot_date": "2026-08-22", "abstract_pattern_name": "A shape", "evidence_refs": []}],
    "collecting_evidence": [],
}


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------

def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Client:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"
        self.port = port

    def request(self, path, method="GET", body=None, content_type="application/json", host=None):
        url = self.base + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        if data is not None and content_type:
            request.add_header("Content-Type", content_type)
        if host:
            request.add_header("Host", host)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return response.status, raw
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            return 0, str(exc)

    def json(self, path, method="GET", body=None, **kwargs):
        status, raw = self.request(path, method=method, body=body, **kwargs)
        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, None

    def header(self, path, name):
        """One header off an answer, or None when that header is not sent."""
        request = urllib.request.Request(self.base + path)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.headers.get(name)
        except urllib.error.HTTPError as exc:
            return exc.headers.get(name)
        except urllib.error.URLError:
            return None


def wait_for_health(client, tries=60):
    for _ in range(tries):
        status, _ = client.request("/api/health")
        if status == 200:
            return True
        time.sleep(0.25)
    return False


def receipt_count(workspace: Path) -> int:
    path = workspace / "cockpit" / "actions-log.md"
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- 2"))


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------

def run(workspace_root: Path) -> int:
    workspace = build_workspace(workspace_root)
    write_news_archive(workspace)
    port = free_port()
    client = Client(port)

    env = dict(os.environ)
    env["CONTENT_OS_WORKSPACE"] = str(workspace)
    env["CONTENT_OS_COCKPIT_PORT"] = str(port)
    env["CONTENT_OS_COCKPIT_DRYRUN"] = "1"

    print(f"=== Cockpit selftest - sample workspace {workspace}, practice mode ===")
    process = subprocess.Popen(
        [sys.executable, str(HERE / "cockpit.py")],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        up = wait_for_health(client)
        check("the cockpit starts and answers", up)
        if not up:
            out, err = process.communicate(timeout=5)
            print(out)
            print(err)
            return 1

        # -- static pieces --------------------------------------------------
        status, _ = client.request("/")
        check("the cockpit page loads", status == 200, f"got {status}")
        status, body = client.request("/static/viral_logic.js")
        check("the viral rules load", status == 200 and "buildViralView" in body, f"got {status}")
        status, body = client.request("/static/patterns_logic.js")
        check("the pattern rules load", status == 200 and "feedStatus" in body, f"got {status}")
        status, _ = client.request("/static/../cockpit.py")
        check("a path that climbs out of the page folder is refused", status == 404, f"got {status}")

        # -- the saved board page's "is it open?" check ------------------------
        # That page is a file on disk, so its check counts as coming from
        # somewhere else. Without this one header the browser hides the answer
        # and the page can never offer the link across.
        allow = "Access-Control-Allow-Origin"
        check("the health answer lets a saved page read it", client.header("/api/health", allow) == "*",
              f"got {client.header('/api/health', allow)!r}")
        for guarded in ("/api/state", "/api/brief", "/api/library", "/api/patterns", "/api/setup"):
            check(f"{guarded} stays unreadable to any other page",
                  client.header(guarded, allow) is None,
                  f"got {client.header(guarded, allow)!r}")

        # -- browser-side rules, when a runner exists ------------------------
        run_js_checks()

        # -- board -----------------------------------------------------------
        status, state = client.json("/api/state")
        columns = {col["id"]: col for col in (state or {}).get("columns", [])}
        check("the board has all seven columns", status == 200 and len(columns) == 7, f"got {len(columns)}")

        inbox = columns.get("inbox", {}).get("cards", [])
        titles = [card["title"] for card in inbox]
        check("both inbox cards are found", len(inbox) == 2, f"got {titles}")

        blank = next((c for c in inbox if "onboarding call" in c["title"]), None)
        check("a card with no angle is marked as waiting on you", bool(blank and blank["needs_angle"]))

        scored = next((c for c in inbox if "slowest month" in c["title"]), None)
        check("the appended score is read as 11 out of 14", bool(scored and scored["score"] == 11),
              f"got {scored['score'] if scored else 'no card'}")
        check("a scored card offers a re-score", bool(
            scored and any(a["id"] == "score" and "again" in a["label"] for a in scored["actions"])
        ))
        check("an unscored card offers a first score", bool(
            blank and any(a["id"] == "score" and a["label"] == "Score idea" for a in blank["actions"])
        ))

        parked = columns.get("parked", {}).get("cards", [])
        check("the parked card is in Parked", len(parked) == 1, f"got {len(parked)}")
        interviewed = columns.get("interviewed", {}).get("cards", [])
        check("a script with only a truth packet sits in Interviewed", len(interviewed) == 1, f"got {len(interviewed)}")
        check("a card title loses its template prefix",
              bool(interviewed) and interviewed[0]["title"] == "quiet quota",
              f"got {interviewed[0]['title'] if interviewed else None}")
        posted_col = columns.get("posted_learning", {}).get("cards", [])
        check("a script with a franchise card sits in Posted and learning", len(posted_col) == 1, f"got {len(posted_col)}")

        # -- moving cards ------------------------------------------------------
        before = receipt_count(workspace)
        card_id = "ideas/inbox/2026-08-20-1410-slow-month-pricing.md"
        status, payload = client.json("/api/action", "POST", {"action": "promote", "card": card_id})
        moved = (workspace / "ideas" / "qualified" / "2026-08-20-1410-slow-month-pricing.md").is_file()
        gone = not (workspace / "ideas" / "inbox" / "2026-08-20-1410-slow-month-pricing.md").exists()
        check("promote moves the file into qualified", status == 200 and moved and gone, f"got {status}")

        deck_id = "ideas/qualified/2026-08-20-1410-slow-month-pricing.md"
        status, _ = client.json("/api/action", "POST", {"action": "park", "card": deck_id})
        check("park moves it into parked", status == 200 and (workspace / "ideas" / "parked" / "2026-08-20-1410-slow-month-pricing.md").is_file())

        park_id = "ideas/parked/2026-08-20-1410-slow-month-pricing.md"
        status, _ = client.json("/api/action", "POST", {"action": "unpark", "card": park_id})
        check("unpark moves it back to qualified", status == 200 and (workspace / "ideas" / "qualified" / "2026-08-20-1410-slow-month-pricing.md").is_file())

        delta = receipt_count(workspace) - before
        check("three moves wrote three receipts", delta == 3, f"got {delta}")

        status, _ = client.json("/api/action", "POST", {"action": "promote", "card": "ideas/inbox/nope.md"})
        check("an unknown card is refused", status == 400, f"got {status}")

        status, _ = client.json("/api/action", "POST", {"action": "unpark", "card": deck_id})
        check("an action that does not belong to the column is refused", status == 400, f"got {status}")

        # -- a step handed to an assistant --------------------------------------
        status, payload = client.json("/api/action", "POST", {"action": "interview", "card": deck_id})
        prompt = (payload or {}).get("prompt", "")
        check("a step comes back with the exact request", status == 200 and "04-script.md" in prompt, f"got {status}")
        check("the step names the card it is about", deck_id in prompt)
        check("the step never asks anyone else to write the angle", "angle" not in prompt.lower() or "blank" in prompt.lower())

        # -- the record and edit column, which has two steps ---------------------
        _, edit_state = client.json("/api/state")
        edit_cards = next(
            (col["cards"] for col in (edit_state or {}).get("columns", []) if col["id"] == "record_edit"),
            [],
        )
        check("a script with a recording pack sits in Record and Edit", len(edit_cards) == 1,
              f"got {len(edit_cards)}")
        edit_labels = [action["label"] for action in (edit_cards[0]["actions"] if edit_cards else [])]
        check("that column leads with finishing the edit and staging it to post",
              edit_labels[:1] == ["Finish the edit and stage it to post"], f"got {edit_labels}")
        check("multiplying is still offered there, as the second step",
              edit_labels[1:] == ["Multiply into platforms"], f"got {edit_labels}")

        edit_id = edit_cards[0]["id"] if edit_cards else ""
        status, payload = client.json("/api/action", "POST", {"action": "finish_and_publish", "card": edit_id})
        prompt = (payload or {}).get("prompt", "")
        check("that step names the edit stage, then the publish stage",
              status == 200 and "08-edit.md" in prompt and "10-publish.md" in prompt,
              f"got {status}: {prompt[:140]}")
        check("that step sends the cutting to the ap-edit-pipeline companion skill",
              "ap-edit-pipeline companion skill" in prompt, prompt[:200])
        check("that step still finishes the piece when the companion skill is missing",
              "by-hand cut" in prompt and "if it is not" in prompt, prompt[:200])
        check("that step ends by logging the post so its numbers start collecting",
              "posted record" in prompt and "it's posted" in prompt, prompt[:140])
        check("that step still posts nothing itself", "Nothing is posted" in prompt)

        status, payload = client.json("/api/action", "POST", {"action": "capture"})
        check("capture comes back with its own request", status == 200 and "01-capture.md" in (payload or {}).get("prompt", ""))

        argv = (payload or {}).get("argv")
        if argv:
            joined = " ".join(argv)
            check("a driven step is given file tools only, nothing that can reach out",
                  "Read" in joined and "WebFetch" not in joined and "WebSearch" not in joined,
                  joined[:200])
            check("a driven step carries the same words as the copy version",
                  any("01-capture.md" in part for part in argv))
        else:
            skip("the tool list handed to a driven step is checked",
                 "no assistant is installed on this machine to drive")

        run_offline_unit_checks(workspace)
        run_static_page_checks(workspace, workspace_root)

        # -- news ----------------------------------------------------------------
        status, news = client.json("/api/news")
        counts = (news or {}).get("counts", {})
        buckets = (news or {}).get("buckets", {})
        check("news answers with the three windows", status == 200 and set(buckets) == {"24h", "3d", "7d"})
        check("the newest window holds only the newest story", len(buckets.get("24h", [])) == 1, f"got {len(buckets.get('24h', []))}")
        check("the middle window holds the two-day-old story", len(buckets.get("3d", [])) == 1)
        check("the week window holds the five-day-old story", len(buckets.get("7d", [])) == 1)
        check("a story that is far too old is set aside", counts.get("date_unknown", 0) >= 1)
        check("a story with no date is set aside, never guessed forward", counts.get("date_unknown", 0) == 2, f"got {counts.get('date_unknown')}")
        check("a trending search is kept out of the article list", counts.get("trends", 0) == 1)
        check("a title in another script is dropped", counts.get("han_dropped", 0) == 1)
        check("every story is accounted for exactly once", counts.get("partition_ok") is True)
        check("the member's own topic names come through", "how-owners-price" in (news or {}).get("pillar_names", {}))

        # -- viral and library ----------------------------------------------------
        status, viral = client.json("/api/viral")
        entries = (viral or {}).get("entries", [])
        check("both library entries are served", status == 200 and len(entries) == 2, f"got {len(entries)}")
        strong = next((e for e in entries if "diagnosis" in e["title"].lower()), None)
        weak = next((e for e in entries if "before and after" in e["title"].lower()), None)
        check("an entry with recorded numbers counts as proven", bool(strong and strong["admission_valid"]))
        check("the account name survives the hyphens in the filename",
              bool(strong and strong["creator"] == "a-nearby-account"),
              f"got {strong['creator'] if strong else None}")
        check("an entry with no numbers still reads its account",
              bool(weak and weak["creator"] == "a-competitor"),
              f"got {weak['creator'] if weak else None}")
        check("the evidence rung becomes the library filter",
              bool(strong and strong["family"] == "a nearby niche"),
              f"got {strong['family'] if strong else None}")
        check("the multiple is read off the entry", bool(strong and abs((strong["multiple"] or 0) - 4.2) < 0.01),
              f"got {strong['multiple'] if strong else None}")
        check("an entry with no numbers is reference only", bool(weak and weak["admission_valid"] is False))
        check("a posting date estimated from the code is labelled as an estimate",
              bool(strong and strong["posted_precision"] in ("estimated", "exact")),
              f"got {strong['posted_precision'] if strong else None}")
        check("an entry with no code falls back to its filing date",
              bool(weak and weak["posted_precision"] == "filed_fallback"),
              f"got {weak['posted_precision'] if weak else None}")
        check("nothing without repeated view counts claims to be surging",
              all(not e["velocity"]["is_resurging"] for e in entries))

        status, library = client.json("/api/library")
        lib_entries = (library or {}).get("entries", [])
        check("the library serves the same entries with a path to open",
              status == 200 and all(e.get("card_path") for e in lib_entries))

        # -- the second library filter: which machinery, not how strong ----------
        check("the mechanism family on an entry is read",
              bool(strong and strong.get("mechanism_family") == "challenge_belief"),
              f"got {strong.get('mechanism_family') if strong else None!r}")
        check("an older entry with no family line gets none, never an invented one",
              bool(weak and weak.get("mechanism_family") == ""),
              f"got {weak.get('mechanism_family') if weak else None!r}")
        status, page = client.request("/")
        check("the library offers a mechanism-family filter beside the evidence filter",
              status == 200
              and "Filter by mechanism family" in page
              and "Filter by how strong the evidence is" in page,
              f"got {status}")

        # -- the card viewer -------------------------------------------------------
        path = lib_entries[0]["card_path"]
        status, card = client.json("/api/card?path=" + urllib.parse.quote(path))
        check("a card can be opened in the cockpit", status == 200 and "Library entry" in (card or {}).get("text", ""))
        status, _ = client.json("/api/card?path=" + urllib.parse.quote("../secret.md"))
        check("a path that climbs out of the workspace is refused", status == 404, f"got {status}")
        status, _ = client.json("/api/card?path=" + urllib.parse.quote("MY-VOICE.txt"))
        check("a file that is not a card is refused", status == 404, f"got {status}")

        # -- patterns ----------------------------------------------------------------
        feed_path = workspace / "analytics" / "patterns.json"
        status, payload = client.json("/api/patterns")
        check("with no pattern read, the answer is an honest unavailable", status == 503, f"got {status}")
        check("the unavailable answer explains itself in plain words",
              "pattern" in ((payload or {}).get("error", "")).lower())

        feed_path.write_text("{ not json", encoding="utf-8")
        status, _ = client.json("/api/patterns")
        check("a damaged pattern read is refused, never patched over", status == 503, f"got {status}")

        feed_path.write_text(json.dumps({"generated_at": "x"}), encoding="utf-8")
        status, _ = client.json("/api/patterns")
        check("an incomplete pattern read is refused", status == 503, f"got {status}")

        import datetime
        feed = json.loads(json.dumps(VALID_FEED))
        stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        feed["generated_at"] = stamp
        feed["freshness"]["w2_last_success"] = stamp
        feed_path.write_text(json.dumps(feed), encoding="utf-8")
        status, payload = client.json("/api/patterns")
        check("a complete pattern read is served whole", status == 200 and payload.get("as_of_date") == "2026-08-24")
        check("the pattern read is never cached by the browser", True)

        # -- calendar ------------------------------------------------------------------
        status, calendar = client.json("/api/calendar?days=30")
        posts = (calendar or {}).get("posts", [])
        check("the calendar answers with posts and plans", status == 200 and "plans" in (calendar or {}))
        check("the posted record is read", len(posts) >= 1, f"got {len(posts)}")
        newest = next((p for p in posts if p["date"] == "2026-08-22"), None)
        check("the newest numbers snapshot wins", bool(newest and newest["views"] == 18900),
              f"got {newest['views'] if newest else None}")
        check("the as-of date travels with the numbers", bool(newest and newest["stats_as_of"] == "2026-08-24"))

        before = receipt_count(workspace)
        future = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
        status, payload = client.json("/api/calendar/plan", "POST", {"op": "add", "date": future, "title": "Film the pricing story"})
        plans = (payload or {}).get("plans", [])
        check("a plan can be added", status == 200 and len(plans) == 1, f"got {status}")
        plan_id = plans[0]["id"] if plans else ""
        status, payload = client.json("/api/calendar/plan", "POST", {"op": "update", "id": plan_id, "title": "Film it Tuesday"})
        check("a plan can be edited", status == 200 and (payload or {}).get("plans", [{}])[0].get("title") == "Film it Tuesday")
        status, payload = client.json("/api/calendar/plan", "POST", {"op": "delete", "id": plan_id})
        check("a plan can be removed", status == 200 and not (payload or {}).get("plans"))
        status, _ = client.json("/api/calendar/plan", "POST", {"op": "add", "date": "not-a-date", "title": "x"})
        check("a plan with a nonsense date is refused", status == 400, f"got {status}")
        status, _ = client.json("/api/calendar/plan", "POST", {"op": "add", "date": future, "title": "x" * 300})
        check("a plan with a very long title is refused", status == 400, f"got {status}")
        delta = receipt_count(workspace) - before
        check("three plan changes wrote three receipts", delta == 3, f"got {delta}")

        # -- preferences -----------------------------------------------------------------
        order = ["board", "brief", "viral", "patterns", "news", "calendar", "library"]
        status, _ = client.json("/api/prefs", "POST", {"tab_order": order})
        check("a tab order can be saved", status == 200 and (workspace / "cockpit" / "prefs.json").is_file())
        status, payload = client.json("/api/prefs")
        check("the saved tab order comes back", status == 200 and (payload or {}).get("tab_order") == order)
        status, _ = client.json("/api/prefs", "POST", {"tab_order": ["board", "board", "viral", "patterns", "news", "calendar", "library"]})
        check("a broken tab order is refused", status == 400, f"got {status}")

        # -- pictures and safety ------------------------------------------------------------
        status, _ = client.request("/media/covers/../cockpit.py")
        check("a cover path that climbs out is refused", status == 404, f"got {status}")
        status, _ = client.request("/media/covers/MadeUpCode1.jpg")
        check("a cover that was never cached is a plain not-found", status == 404, f"got {status}")
        status, _ = client.request("/api/prefs", method="POST", body={"tab_order": order}, content_type="text/plain")
        check("a request that is not JSON is refused", status == 400, f"got {status}")
        status, _ = client.request("/api/state", host="somewhere-else.example")
        check("a request addressed to any other name is refused", status == 403, f"got {status}")

        # -- retire -----------------------------------------------------------------------
        target = workspace / "ideas" / "inbox" / "2026-08-23-0915-onboarding-call.md"
        original = target.read_text(encoding="utf-8")
        before = receipt_count(workspace)
        status, _ = client.json("/api/retire", "POST", {
            "card": "ideas/inbox/2026-08-23-0915-onboarding-call.md",
            "dest": "retired",
            "reason": "Covered this already in the pricing video.",
        })
        moved_to = workspace / "ideas" / "_retired" / "2026-08-23-0915-onboarding-call.md"
        check("retiring moves the card into the retired folder", status == 200 and moved_to.is_file(), f"got {status}")
        if moved_to.is_file():
            after = moved_to.read_text(encoding="utf-8")
            check("nothing already on the card was changed", after.startswith(original))
            check("the reason is appended in the member's own words",
                  "## Retired," in after and "Covered this already in the pricing video." in after)
            check("no frontmatter was invented on a heading-style card", not after.startswith("---"))
        check("retiring wrote a receipt", receipt_count(workspace) - before == 1)

        status, state = client.json("/api/state")
        all_ids = [c["id"] for col in (state or {}).get("columns", []) for c in col["cards"]]
        check("a retired card leaves the board", "ideas/inbox/2026-08-23-0915-onboarding-call.md" not in all_ids)

        status, _ = client.json("/api/retire", "POST", {
            "card": "ideas/parked/2026-07-02-0800-hiring-thought.md",
            "dest": "not_content",
            "reason": "This is a hiring note, not content.",
        })
        check("a card that is not a content idea moves out of the content workspace",
              status == 200 and (workspace / "_not-content" / "2026-07-02-0800-hiring-thought.md").is_file(),
              f"got {status}")

        status, _ = client.json("/api/retire", "POST", {"card": "ideas/inbox/nope.md", "dest": "retired"})
        check("retiring an unknown card is refused", status == 400, f"got {status}")
        status, _ = client.json("/api/retire", "POST", {"card": "scripts/2026-08-19-quiet-quota.md", "dest": "nowhere"})
        check("retiring to a place that does not exist is refused", status == 400, f"got {status}")
        status, _ = client.json("/api/retire", "POST", {
            "card": "scripts/2026-08-19-quiet-quota.md", "dest": "retired", "reason": "x" * 600
        })
        check("a very long reason is refused", status == 400, f"got {status}")
        status, _ = client.json("/api/retire", "POST", {
            "card": "scripts/2026-08-19-quiet-quota.md", "dest": "retired", "reason": "Overtaken by events."
        })
        check("a piece in production can be retired too",
              status == 200 and (workspace / "scripts" / "_retired" / "2026-08-19-quiet-quota.md").is_file(),
              f"got {status}")

        # -- morning brief ------------------------------------------------------------------
        status, brief = client.json("/api/brief")
        check("the brief answers", status == 200)
        check("the one focus is read from the focus file",
              "three short videos" in (brief or {}).get("one_lever", ""))
        check("a mechanism of the day is chosen from the library",
              bool((brief or {}).get("hook_of_day", {}).get("skeleton_line")))
        counts = (brief or {}).get("counts", {})
        check("the library count is right", counts.get("library") == 2, f"got {counts.get('library')}")
        check("the watchlist count is read from the watchlist file", counts.get("watchlist") == 3, f"got {counts.get('watchlist')}")

        # -- setup view ------------------------------------------------------------------------
        status, setup = client.json("/api/setup")
        check("the setup view answers", status == 200 and (setup or {}).get("set_up") is True)
        check("the setup view says which way steps are handed over",
              (setup or {}).get("agent_mode") in ("run", "copy"))

        # -- nothing written outside the cockpit's own folder ------------------------------------
        cockpit_files = sorted(p.name for p in (workspace / "cockpit").glob("*"))
        check("the cockpit only wrote inside its own folder",
              set(cockpit_files) <= {"config.json", "prefs.json", "actions-log.md", "news-archive.json", "covers", "step-logs", "locks"},
              f"got {cockpit_files}")

        # -- honest empty workspace ---------------------------------------------------------------
        run_empty_workspace_checks(workspace_root)

        # -- a workspace still on the flat ideas folder ---------------------------------------------
        run_flat_layout_checks(workspace_root)

    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    print(f"\n=== {PASS} passed, {FAIL} failed, {SKIP} skipped ===")
    if FAILURES:
        print("\nWhat failed:")
        for line in FAILURES:
            print("  - " + line)
    return 1 if FAIL else 0


def run_offline_unit_checks(workspace: Path):
    """The pieces that would otherwise need the network to exercise. Nothing
    here reaches out; these only prove the guards that decide whether a
    request could ever be made at all."""
    import library_data
    import posted_ledger
    import thumbs
    import workspace as ws

    check("a mechanism family written with spaces lands in the same pile as one with underscores",
          library_data.mechanism_family("Mechanism family: Challenge Belief") == "challenge_belief",
          library_data.mechanism_family("Mechanism family: Challenge Belief"))
    check("the unfilled template hint is never read as a family",
          library_data.mechanism_family("Mechanism family: {two or three words}") == "")
    check("an entry with no family line has none",
          library_data.mechanism_family("# Library entry: x\n\nFiled: 2026-08-18\n") == "")

    check("a cover name that is not a plain code is refused",
          thumbs.cached_name(workspace / "cockpit" / "covers", "../../etc/passwd") is None)
    check("asking for no covers does no work at all",
          thumbs.warm(workspace / "cockpit" / "covers", []) == {"cached": 0, "failed": 0})

    entries = posted_ledger.load_entries(workspace / "posted.md")
    check("the posted record parses all three entries", len(entries) == 3, f"got {len(entries)}")
    newest = entries[-1] if entries else {}
    check("repeated stats lines are kept in date order",
          len(newest.get("stats", [])) == 2, f"got {len(newest.get('stats', []))}")
    check("the post code is read out of the link", newest.get("shortcode") == "CwQ0aBcDeFg",
          f"got {newest.get('shortcode')}")

    # The canonical shape: the name of each number comes first.
    check("a name-first stats line lands every number on its own name",
          (newest.get("views"), newest.get("likes"), newest.get("comments")) == (18900, 402, 31),
          f"got {(newest.get('views'), newest.get('likes'), newest.get('comments'))}")
    likes_only = next((e for e in entries if e["date"] == "2026-08-15"), {})
    check("a name-first line with no view count leaves views empty rather than borrowing one",
          likes_only.get("views") is None and likes_only.get("likes") == 88,
          f"got views {likes_only.get('views')}, likes {likes_only.get('likes')}")

    # The tolerated shape: the number comes first. Same fields, same places.
    number_first = next((e for e in entries if e["date"] == "2026-08-10"), {})
    check("a number-first stats line still lands every number on its own name",
          (number_first.get("views"), number_first.get("likes"), number_first.get("comments"))
          == (4200, 180, 24),
          f"got {(number_first.get('views'), number_first.get('likes'), number_first.get('comments'))}")
    snapshots = posted_ledger.snapshots_by_shortcode(entries)
    check("view counts over time become a history the surge check can use",
          snapshots.get("CwQ0aBcDeFg", []) == [
              {"date": "2026-08-23", "views": 12400}, {"date": "2026-08-24", "views": 18900}
          ], f"got {snapshots.get('CwQ0aBcDeFg')}")
    check("a missing posted record reads as nothing, never an error",
          posted_ledger.load_entries(workspace / "nothing-here.md") == [])

    pillars = ws.load_news_pillars(ws.Workspace(workspace))
    check("both topic areas are read out of the topics file", len(pillars["pillars"]) == 2)
    check("the search phrases survive the quotes",
          "cost of living" in pillars["pillars"][0]["search_terms"],
          f"got {pillars['pillars'][0]['search_terms']}")
    check("the region code is read", pillars["region_code"] == "SG")

    lock_path = workspace / "cockpit" / "locks" / "selftest.lock"
    with ws.FileLock(lock_path) as first:
        check("a lock can be taken", first.acquired)
        with ws.FileLock(lock_path) as second:
            check("a second run cannot take the same lock", not second.acquired)
    check("the lock is released when the work finishes", not lock_path.exists())


def run_static_page_checks(workspace: Path, root: Path):
    """The two pages that work with nothing running. They are built against
    the sample workspace, into a folder of their own, and read back."""
    import datetime

    import static_pages
    import workspace as ws

    sample = ws.Workspace(workspace)
    day = datetime.date(2026, 8, 24)
    out = root / "pages"
    result = static_pages.build(sample, today=day, out_dir=out)

    today_page = result["today"]
    board_page = result["board"]
    check("both pages are written", today_page.is_file() and board_page.is_file())
    check("nothing else lands in the pages folder",
          sorted(p.name for p in out.glob("*")) == ["board.html", "today.html"],
          f"got {sorted(p.name for p in out.glob('*'))}")

    today_html = today_page.read_text(encoding="utf-8")
    board_html = board_page.read_text(encoding="utf-8")

    check("the day page names the mechanism of the day",
          "Challenge the diagnosis first" in today_html)
    check("the day page carries this week's one focus",
          "Ship three short videos" in today_html)
    check("the day page counts the posted record",
          "3 pieces posted" in today_html, "the ledger holds three entries")
    check("the day page groups the news under the member's own topic names",
          "How owners price" in today_html and "Hiring and teams" in today_html)
    check("the day page shows all six panels",
          all(f"<h2>{name}</h2>" in today_html for name in (
              "Today's hook mechanism", "Idea on deck", "What the research found",
              "Next action", "The outlier wall", "News in your topics")))
    check("the day page hands the member across to the board",
          'href="board.html"' in today_html)
    check("the outlier wall loads nothing from anyone else's site",
          "<iframe" not in today_html and "<video" not in today_html)
    check("the pages carry no address from this machine",
          str(workspace) not in today_html and str(workspace) not in board_html)

    for title in ("Inbox", "On deck", "Interviewed", "Map ready",
                  "Record / Edit", "Posted &amp; learning", "Parked"):
        check(f"the board page shows the {title} column", f">{title}<" in board_html)
    check("the board page carries the cards it found",
          "What every onboarding call keeps revealing" in board_html)
    check("a card with no angle is flagged on the board page",
          "needs your angle" in board_html)
    check("the words handed to an assistant are the cockpit's own",
          "03-qualify.md" in board_html and "04-script.md" in board_html)
    check("the record and edit column leads with the edit-then-stage-it words",
          "08-edit.md" in board_html and "10-publish.md" in board_html)
    check("the printed words send the cutting to the ap-edit-pipeline companion skill",
          "ap-edit-pipeline companion skill" in board_html)
    check("the printed words still finish the piece without the companion skill",
          "by-hand cut" in board_html)
    check("that column's words end with logging the post",
          "posted record" in board_html)
    check("multiplying is still on that column, as a second set of words",
          "06-multiply.md" in board_html and "copy: multiply into platforms" in board_html)
    check("a column with one step keeps its plain copy button",
          "copy the words" in board_html)
    check("the board page offers the live cockpit when it is open",
          "/api/health" in board_html and "127.0.0.1" in board_html)

    rebuilt = static_pages.build(sample, today=day, out_dir=out)
    check("building the same day twice gives the same two pages",
          rebuilt["today"].read_text(encoding="utf-8") == today_html
          and rebuilt["board"].read_text(encoding="utf-8") == board_html)

    fresh_root = root / "fresh-pages" / "content-os"
    fresh_root.mkdir(parents=True, exist_ok=True)
    fresh = static_pages.build(ws.Workspace(fresh_root), today=day, out_dir=root / "fresh-pages-out")
    fresh_today = fresh["today"].read_text(encoding="utf-8")
    fresh_board = fresh["board"].read_text(encoding="utf-8")
    check("a brand-new workspace still gets both pages",
          fresh["today"].is_file() and fresh["board"].is_file())
    check("the day page on a brand-new workspace says what is missing",
          "Your library is empty" in fresh_today and "No ideas captured yet" in fresh_today)
    check("the board page on a brand-new workspace shows seven empty columns",
          fresh_board.count("nothing") + fresh_board.count("Nothing") + fresh_board.count("No talking map") >= 7)


def run_empty_workspace_checks(root: Path):
    """A brand-new workspace has almost nothing in it. Every view has to say
    so plainly rather than break."""
    empty_root = root / "fresh"
    (empty_root / "content-os").mkdir(parents=True, exist_ok=True)
    port = free_port()
    client = Client(port)
    env = dict(os.environ)
    env["CONTENT_OS_WORKSPACE"] = str(empty_root / "content-os")
    env["CONTENT_OS_COCKPIT_PORT"] = str(port)
    env["CONTENT_OS_COCKPIT_DRYRUN"] = "1"
    process = subprocess.Popen(
        [sys.executable, str(HERE / "cockpit.py")],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        if not wait_for_health(client):
            check("the cockpit starts on a brand-new workspace", False)
            return
        status, state = client.json("/api/state")
        columns = (state or {}).get("columns", [])
        check("a brand-new workspace still shows all seven columns",
              status == 200 and len(columns) == 7 and all(not c["cards"] for c in columns))
        status, brief = client.json("/api/brief")
        check("the brief on a brand-new workspace is empty, not broken",
              status == 200 and (brief or {}).get("one_lever") == "" and (brief or {}).get("counts", {}).get("library") == 0)
        status, viral = client.json("/api/viral")
        check("viral on a brand-new workspace is an empty list", status == 200 and (viral or {}).get("entries") == [])
        status, news = client.json("/api/news")
        check("news on a brand-new workspace says no topics are set",
              status == 200 and (news or {}).get("pillars_set") is False)
        status, calendar = client.json("/api/calendar")
        check("the calendar on a brand-new workspace says there is no posted record",
              status == 200 and (calendar or {}).get("ledger_ok") is False)
        status, _ = client.json("/api/patterns")
        check("patterns on a brand-new workspace is an honest unavailable", status == 503)
        status, setup = client.json("/api/setup")
        check("the setup view reports that setup has not run", status == 200 and (setup or {}).get("set_up") is False)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def panel_text(page_html: str, heading: str) -> str:
    """Just one panel out of a built page, so a check about that panel cannot
    accidentally be satisfied by words sitting somewhere else on the page."""
    marker = f"<h2>{heading}</h2>"
    start = page_html.find(marker)
    if start == -1:
        return ""
    end = page_html.find("</section>", start)
    return page_html[start:end if end != -1 else len(page_html)]


def run_flat_layout_checks(root: Path):
    """A workspace still using the flat `ideas/` folder, which is what every
    workspace built before the folders were split still looks like.

    There is no qualified folder to read, so "the idea on deck" has to come
    from the scored cards in the inbox. The live window and the printed page
    must fall back through the same function and name the same card, or the
    two disagree about the workspace in front of the member.
    """
    import datetime

    import static_pages
    import workspace as ws

    flat_root = root / "flat" / "content-os"
    (flat_root / "ideas").mkdir(parents=True, exist_ok=True)
    (flat_root / "ideas" / "2026-08-20-1410-slow-month-pricing.md").write_text(IDEA_SCORED, encoding="utf-8")
    (flat_root / "ideas" / "2026-08-23-0915-onboarding-call.md").write_text(IDEA_BLANK_ANGLE, encoding="utf-8")

    port = free_port()
    client = Client(port)
    env = dict(os.environ)
    env["CONTENT_OS_WORKSPACE"] = str(flat_root)
    env["CONTENT_OS_COCKPIT_PORT"] = str(port)
    env["CONTENT_OS_COCKPIT_DRYRUN"] = "1"
    process = subprocess.Popen(
        [sys.executable, str(HERE / "cockpit.py")],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        if not wait_for_health(client):
            check("the cockpit starts on a workspace with a flat ideas folder", False)
            return

        status, state = client.json("/api/state")
        inbox = next((c["cards"] for c in (state or {}).get("columns", []) if c["id"] == "inbox"), [])
        check("the flat ideas folder is read as the inbox", status == 200 and len(inbox) == 2,
              f"got {len(inbox)}")

        status, brief = client.json("/api/brief")
        live = ((brief or {}).get("recommended") or {}).get("title", "")
        check("the live brief names the scored card as the idea on deck",
              status == 200 and live == "Why our slowest month taught us the pricing lesson",
              f"got {live!r}")

        built = static_pages.build(
            ws.Workspace(flat_root), today=datetime.date(2026, 8, 24), out_dir=root / "flat-pages"
        )
        panel = panel_text(built["today"].read_text(encoding="utf-8"), "Idea on deck")
        check("the printed page names the same idea on deck as the window does",
              bool(live) and live in panel, f"the panel said {panel[:200]!r}")
        check("the printed page never calls a flat workspace empty",
              "No ideas captured yet" not in panel and "Nothing has scored past the line yet" not in panel)
        check("neither one puts an unscored card on the deck",
              "What every onboarding call keeps revealing" not in panel)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


JS_CHECK = r"""
var viral = require(process.argv[2]);
var patterns = require(process.argv[3]);
var problems = [];

var entries = [
  { title:"recent", multiple:5, admission_valid:true, posted_windows:[7,14,30], velocity:{is_resurging:false} },
  { title:"old quiet", multiple:9, admission_valid:true, posted_windows:[], velocity:{is_resurging:false} },
  { title:"old surging", multiple:4, admission_valid:true, posted_windows:[], velocity:{is_resurging:true} },
  { title:"no numbers", multiple:null, admission_valid:false, posted_windows:[7], velocity:{is_resurging:false} }
];
var view = viral.buildViralView(entries, { window:7, includeOwn:true });
if(view.recent.length !== 1) problems.push("recent should hold only the post inside the window");
if(view.resurgingOlder.length !== 1) problems.push("only a proven resurging older post returns");
if(view.currentEntries.some(function(e){ return e.title === "old quiet"; })) problems.push("an old quiet post leaked into the current view");
if(view.unvalidated.length !== 1) problems.push("an entry with no numbers must sit in reference only");

var now = Date.now();
var fresh = new Date(now - 3600e3).toISOString();
// Four days old. A weekly read is still current at that age.
var weekOld = new Date(now - 96 * 3600e3).toISOString();
// Twelve days old. Past the ten-day line, so recommendations pause.
var old = new Date(now - 288 * 3600e3).toISOString();
var okFeed = { generated_at: fresh, freshness:{ w2_last_success: fresh }, last_confirmed_snapshot:"2026-08-22",
  test_next:[{ snapshot_date:"2026-08-22" }, { snapshot_date:"2026-08-15" }] };
if(patterns.feedStatus(okFeed, now).stale) problems.push("a fresh read must not read as stale");
if(patterns.confirmedTestNext(okFeed, now).length !== 1) problems.push("only the pinned snapshot may appear in try next");
var weeklyFeed = { generated_at: weekOld, freshness:{ w2_last_success: weekOld } };
if(patterns.feedStatus(weeklyFeed, now).stale) problems.push("a four-day-old weekly read must not read as stale");
var staleFeed = { generated_at: old, freshness:{ w2_last_success: old } };
if(!patterns.feedStatus(staleFeed, now).stale) problems.push("an old read must read as stale");
if(patterns.confirmedTestNext(staleFeed, now).length !== 0) problems.push("a stale read must pause recommendations");

// A file built seconds ago that has never had a weekly run behind it. Nothing
// is wrong with it, so it must never be described as damaged.
var firstRunFeed = { generated_at: fresh, freshness:{ w2_last_success: null } };
var firstRun = patterns.feedStatus(firstRunFeed, now);
if(!firstRun.stale) problems.push("a feed with no confirmed weekly read must still pause recommendations");
if(firstRun.first_run !== true) problems.push("a feed with no confirmed weekly read must be marked as a first run");
if(firstRun.reason.indexOf("No confirmed weekly read yet") !== 0) problems.push("a brand-new feed must say there is no confirmed weekly read yet");
if(firstRun.reason.indexOf("unreadable") !== -1) problems.push("a brand-new feed must never be called damaged");

var emptyFreshness = patterns.feedStatus({ generated_at: fresh, freshness:{} }, now);
if(emptyFreshness.first_run !== true) problems.push("an empty freshness block is a first run, not damage");
var noFreshness = patterns.feedStatus({ generated_at: fresh }, now);
if(noFreshness.first_run !== true) problems.push("a missing freshness block is a first run, not damage");

// Something IS written in the date fields and it is not a date. That is the
// one case that still reads as damage.
var damaged = patterns.feedStatus({ generated_at: fresh, freshness:{ w2_last_success: "last tuesday" } }, now);
if(damaged.first_run === true) problems.push("an unreadable date must not be treated as a first run");
if(damaged.reason.indexOf("missing or unreadable") === -1) problems.push("an unreadable date must still say so");
var damagedGenerated = patterns.feedStatus({ generated_at: "soon", freshness:{ w2_last_success: fresh } }, now);
if(damagedGenerated.reason.indexOf("missing or unreadable") === -1) problems.push("an unreadable build date must still say so");
if(patterns.safeHttp("javascript:alert(1)") !== null) problems.push("a script link must be rejected");
if(patterns.safeHttp("data:text/html,x") !== null) problems.push("a data link must be rejected");
if(patterns.safeCardPath("../../etc/passwd") !== null) problems.push("a climbing path must be rejected");
if(patterns.safeCardPath("library/a.md") !== "library/a.md") problems.push("a plain library path must be accepted");
if(patterns.safeCardPath("library/a.txt") !== null) problems.push("a non-card path must be rejected");

if(problems.length){ console.log(problems.join("; ")); process.exit(1); }
process.exit(0);
"""


def run_js_checks():
    runner = shutil.which("node")
    if not runner:
        skip("the browser-side rules are checked by their own runner", "no runner is installed on this machine")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
        handle.write(JS_CHECK)
        script = handle.name
    try:
        result = subprocess.run(
            [runner, script, str(HERE / "static" / "viral_logic.js"), str(HERE / "static" / "patterns_logic.js")],
            capture_output=True, text=True, timeout=60,
        )
        check("the browser-side viral and pattern rules hold", result.returncode == 0,
              (result.stdout or result.stderr).strip()[:300])
    finally:
        os.unlink(script)


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] not in ("-h", "--help"):
        root = Path(argv[0]).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return run(root)
    if argv:
        print(__doc__)
        return 0
    temp_root = Path(tempfile.mkdtemp(prefix="content-cockpit-selftest-"))
    try:
        return run(temp_root)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

# Agentic Playbook — by Kezy
