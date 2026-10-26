#!/usr/bin/env python3
"""
static_pages.py - two pages that keep working when the cockpit is closed.

Standard library only. Nothing to install, nothing on the network, nothing
uploaded. It reads the member's own content-os/ folder and writes two plain
web pages into content-os/cockpit/:

  today.html   the day in one screen: the mechanism of the day, the idea on
               deck, what the research found lately, what is waiting on the
               owner, the outlier wall from their own library, and the news
               in their own topics.
  board.html   the same seven columns the cockpit shows, frozen to a page.

Why both exist
--------------
The cockpit is a window that has to be open. These two pages are files. They
open with a double click, they work on a machine that has nothing running,
they print, and they can be looked at on a phone over a shared folder. When
the cockpit IS open, board.html notices and offers a link across to it.

What it reads, and what it never does
-------------------------------------
Every number and every card here comes from the same readers the cockpit
uses: workspace.py, board_state.py, viral_data.py, news_data.py,
posted_ledger.py and library_data.py. Nothing is parsed twice and nothing is
invented. A workspace on day one produces two honest pages that say, panel by
panel, what is missing and what would fill it.

It writes exactly two files, both inside content-os/cockpit/. It never moves,
edits, or deletes anything else, and it never posts anything anywhere.

Deterministic: run it twice on the same day against the same workspace and
you get the same two files, byte for byte.
"""

import argparse
import datetime
import html
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import board_state  # noqa: E402
import library_data  # noqa: E402
import news_data  # noqa: E402
import posted_ledger  # noqa: E402
import thumbs  # noqa: E402
import viral_data  # noqa: E402
import workspace as ws  # noqa: E402

TODAY_FILENAME = "today.html"
BOARD_FILENAME = "board.html"

# Parity with the cockpit's own honesty rules.
FRESH_WINDOW_DAYS = 14          # what "lately" means for the research panel
OUTLIER_WALL_MAX = 30           # most cards the wall ever shows
OUTLIER_WALL_PER_ACCOUNT = 2    # so one loud account cannot fill the wall
ON_DECK_SHOWN = 3               # ideas named on the day page
WAITING_SHOWN = 5               # cards named as waiting on the owner
NEWS_ROWS_PER_TOPIC = 4
RECENT_LIBRARY_SHOWN = 5

COLUMNS = [
    ("inbox", "Inbox"),
    ("on_deck", "On deck"),
    ("interviewed", "Interviewed"),
    ("map_ready", "Map ready"),
    ("record_edit", "Record / Edit"),
    ("posted_learning", "Posted & learning"),
    ("parked", "Parked"),
]

# What the owner does next with a card in that column, in plain words.
NEXT_STEP = {
    "inbox": "Score it, then decide whether it is worth making.",
    "on_deck": "Pick it up and start the interview.",
    "interviewed": "Build the talking map.",
    "map_ready": "Film it, then edit it.",
    "record_edit": "Finish the edit, stage it to post, then log it once it is live.",
    "posted_learning": "Run the weekly review on it.",
    "parked": "Leave it, or move it back to On deck.",
}

# The words to hand an assistant for that column, and what each set of words
# does. Same sentences the cockpit's own buttons use, read from one place so
# the page and the window can never drift apart. A column with two steps
# offers both, in the same order the cockpit offers them.
STEP_WORDS = {
    "inbox": [("Score idea", board_state.prompt_score)],
    "on_deck": [("Start the interview", board_state.prompt_interview)],
    "interviewed": [("Build the talking map", board_state.prompt_talking_map)],
    "map_ready": [("Prep the recording", board_state.prompt_record_prep)],
    "record_edit": [
        ("Finish the edit and stage it to post", board_state.prompt_finish_and_publish),
        ("Multiply into platforms", board_state.prompt_multiply),
    ],
    "posted_learning": [("Run the weekly review", board_state.prompt_weekly_review)],
}

WHAT_FILLS_COLUMN = {
    "inbox": "Nothing captured yet. Say \"capture this idea\".",
    "on_deck": "Nothing scored past the line yet.",
    "interviewed": "Nothing interviewed yet.",
    "map_ready": "No talking map is finished yet.",
    "record_edit": "Nothing filmed yet.",
    "posted_learning": "Nothing logged as posted yet.",
    "parked": "Nothing parked. That is a good sign.",
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def rel_href(relative_path: str) -> str:
    """A link from content-os/cockpit/ to a file elsewhere in the workspace.

    Relative on purpose. The page carries no absolute location, so it still
    opens correctly after the whole folder is moved or synced to another
    machine.
    """
    if not relative_path:
        return ""
    return "../" + quote(relative_path)


def card_href(workspace, path) -> str:
    if not path:
        return ""
    return rel_href(workspace.relative(Path(path)))


def multiple_label(multiple) -> str:
    if multiple is None:
        return "no numbers recorded"
    return f"{multiple:.1f} times their normal"


def plural(count: int, word: str, many: str = "") -> str:
    if count == 1:
        return f"1 {word}"
    return f"{count} {many or word + 's'}"


def parse_day(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def within_days(day, reference: datetime.date, span: int) -> bool:
    if day is None:
        return False
    gap = (reference - day).days
    return 0 <= gap <= span


# --------------------------------------------------------------------------
# Reading the workspace
# --------------------------------------------------------------------------

def collect_today(workspace, config, today: datetime.date) -> dict:
    """Everything the day page shows, read once."""
    brief = viral_data.brief_data(workspace, config, today=today)
    entries = library_data.load_entries(workspace.library_dir)
    qualified = board_state.sort_by_score(board_state.load_idea_dir(workspace.qualified_dir))
    inbox = board_state.load_idea_dir(workspace.inbox_dir)
    ledger = posted_ledger.load_entries(workspace.posted_ledger)

    return {
        "date": today,
        "focus": brief["one_lever"],
        "counts": brief["counts"],
        "hook": _hook_panel(brief, entries, today),
        "on_deck": _on_deck_panel(qualified, inbox, today),
        "research": _research_panel(entries, today),
        "waiting": _waiting_panel(inbox, qualified),
        "wall": _wall_panel(workspace, config, today),
        "news": _news_panel(workspace),
        "posted_count": len(ledger),
    }


def _hook_panel(brief, entries, today: datetime.date) -> dict:
    hook = brief["hook_of_day"]
    recent = []
    for entry in entries:
        filed = parse_day(entry.get("filed"))
        if within_days(filed, today, FRESH_WINDOW_DAYS):
            recent.append(entry)
    recent.sort(key=lambda item: (item["multiple"] is None, -(item["multiple"] or 0)))
    return {
        "empty": not hook.get("title"),
        "title": hook.get("title", ""),
        "family": hook.get("family", ""),
        "line": hook.get("skeleton_line", ""),
        "card_path": hook.get("card_path", ""),
        "recent": recent[:RECENT_LIBRARY_SHOWN],
    }


def _on_deck_panel(qualified, inbox, today: datetime.date) -> dict:
    """Which ideas are ready to start, picked by the cockpit's own picker.

    board_state.rank_on_deck is the single decision. On a workspace still
    using the flat ideas folder there is no qualified folder, so the scored
    cards in the inbox are what is ready, and this page names the same one the
    live brief names.
    """
    ready = board_state.rank_on_deck(qualified, inbox)
    shown = []
    for card in ready[:ON_DECK_SHOWN]:
        shown.append({
            "title": card["title"],
            "score": card["score"],
            "age": ws.format_age(card["captured"], today),
            "needs_angle": not card["angle"],
            "path": card["path"],
        })
    return {
        "empty": not shown,
        "shown": shown,
        "qualified_total": len(ready),
        "inbox_total": len(inbox),
    }


def _research_panel(entries, today: datetime.date) -> dict:
    fresh = [e for e in entries if within_days(parse_day(e.get("filed")), today, FRESH_WINDOW_DAYS)]
    accounts = {e["creator"] for e in fresh if e.get("creator")}
    top = sorted(fresh, key=lambda item: (item["multiple"] is None, -(item["multiple"] or 0)))[:3]
    filed_days = [d for d in (parse_day(e.get("filed")) for e in entries) if d]
    return {
        "total_library": len(entries),
        "fresh_total": len(fresh),
        "accounts": len(accounts),
        "top": top,
        "last_filed": max(filed_days).isoformat() if filed_days else "",
    }


def _waiting_panel(inbox, qualified) -> dict:
    cards = list(qualified) + list(inbox)
    waiting = [card for card in cards if not card["angle"]]
    return {
        "any_cards": bool(cards),
        "total": len(waiting),
        "shown": waiting[:WAITING_SHOWN],
    }


def _wall_panel(workspace, config, today: datetime.date) -> dict:
    """The strongest finds in the member's own library. No third-party player
    is ever loaded: a card is their own filed entry, their own cached cover
    picture when one exists, and a plain link out."""
    rows = viral_data.build_entries(workspace, config, today=today)
    outliers = [
        row for row in rows
        if not row["own"]
        and row["multiple"] is not None
        and row["multiple"] >= viral_data.OUTLIER_GATE
    ]
    # "In the last fortnight" is decided by the same window rule the Viral tab
    # uses, so the two can never disagree about what counts as recent.
    fresh = [row for row in outliers if FRESH_WINDOW_DAYS in row["posted_windows"]]
    window = "fortnight" if fresh else "all"
    pool = fresh or outliers
    pool = sorted(pool, key=lambda row: -row["multiple"])

    selected, per_account = [], {}
    for row in pool:
        account = row.get("creator") or "unknown"
        if per_account.get(account, 0) >= OUTLIER_WALL_PER_ACCOUNT:
            continue
        selected.append(row)
        per_account[account] = per_account.get(account, 0) + 1
        if len(selected) >= OUTLIER_WALL_MAX:
            break

    for row in selected:
        row["cover"] = thumbs.cached_name(workspace.thumbs_dir, row.get("shortcode"))

    return {"empty": not selected, "window": window, "rows": selected}


def _news_panel(workspace) -> dict:
    settings = ws.load_news_pillars(workspace)
    payload = news_data.build_news_payload(workspace.news_archive)
    names = {p["id"]: p["name"] for p in settings.get("pillars", [])}

    rows = payload["buckets"]["24h"] + payload["buckets"]["3d"]
    grouped = {}
    for row in rows:
        grouped.setdefault(str(row.get("pillar") or "other"), []).append(row)

    order = [p["id"] for p in settings.get("pillars", [])]
    order += [key for key in grouped if key not in order]

    groups = []
    for key in order:
        found = grouped.get(key)
        if not found:
            continue
        groups.append({
            "name": names.get(key, key.replace("-", " ").strip() or "other"),
            "rows": found[:NEWS_ROWS_PER_TOPIC],
            "more": max(0, len(found) - NEWS_ROWS_PER_TOPIC),
        })

    return {
        "pillars_set": bool(settings.get("pillars")),
        "updated_at": payload.get("updated_at") or "",
        "groups": groups,
    }


def collect_board(workspace, today: datetime.date) -> list:
    """The same seven columns the cockpit shows, from the same reader."""
    raw = {
        "inbox": board_state.load_idea_dir(workspace.inbox_dir),
        "on_deck": board_state.load_idea_dir(workspace.qualified_dir),
        "parked": board_state.load_idea_dir(workspace.parked_dir),
    }
    raw.update(board_state.load_production(workspace))

    columns = []
    for key, title in COLUMNS:
        if key == "parked":
            entries = board_state.sort_by_captured(raw[key])
        elif key in ("inbox", "on_deck"):
            entries = board_state.sort_by_score(raw[key])
        else:
            entries = board_state.sort_by_age(raw[key])

        cards = []
        for item in entries:
            is_idea = "captured" in item
            card_id = workspace.relative(item["path"])
            steps = [
                {"label": label, "words": builder(card_id)}
                for label, builder in STEP_WORDS.get(key, [])
            ]
            cards.append({
                "title": item["title"],
                "score": item.get("score") if (is_idea and key != "parked") else None,
                "age": ws.format_age(item["captured"] if is_idea else item["date"], today),
                "needs_angle": bool(is_idea and not item["angle"]),
                "next_step": NEXT_STEP[key],
                "steps": steps,
                "href": card_href(workspace, item["path"]),
            })
        columns.append({"key": key, "title": title, "cards": cards})
    return columns


# --------------------------------------------------------------------------
# The look of both pages
# --------------------------------------------------------------------------

CSS = """
:root{
  --ink:#12141a; --muted:#5b6270; --line:#e3e6ec; --paper:#f6f7fa;
  --card:#ffffff; --accent:#2850e8; --accent-soft:#e8edff; --warn:#b64a2e;
}
*{box-sizing:border-box;}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  font-size:17px; line-height:1.55; overflow-wrap:break-word;
}
a{color:var(--accent); text-decoration:none;}
a:hover{text-decoration:underline;}
a:focus-visible{outline:2px solid var(--accent); outline-offset:2px; border-radius:4px;}
header.top{background:var(--ink); color:#fff; padding:34px 28px;}
header.top .stamp{font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:#aab1c2;}
header.top h1{margin:10px 0 6px; font-size:clamp(26px,5vw,36px); line-height:1.15;}
header.top p{margin:0; color:#c9cfdc; font-size:15px;}
header.top a{color:#c9cfdc; text-decoration:underline;}
.counts{display:flex; flex-wrap:wrap; gap:10px; margin-top:18px;}
.counts span{
  border:1px solid #333947; border-radius:999px; padding:6px 14px;
  font-size:13px; color:#c9cfdc;
}
.wrap{max-width:1180px; margin:0 auto; padding:26px;}
.grid{display:grid; grid-template-columns:1fr 1fr; gap:18px;}
.panel{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:22px;}
.panel.wide{grid-column:1 / -1;}
.panel h2{
  margin:0 0 14px; font-size:12.5px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--muted);
}
.lead{font-size:19px; font-weight:600; margin:0 0 8px;}
.quiet{color:var(--muted); font-size:14.5px; margin:6px 0 0;}
.empty{color:var(--muted); font-size:15px; margin:6px 0 0;}
.rows{list-style:none; margin:12px 0 0; padding:0;}
.rows li{
  display:flex; justify-content:space-between; gap:12px; align-items:baseline;
  padding:8px 0; border-top:1px solid var(--line); font-size:15px;
}
.rows li:first-child{border-top:none;}
.rows .num{color:var(--muted); font-size:13.5px; white-space:nowrap;}
.item{border-top:1px solid var(--line); padding:14px 0;}
.item:first-of-type{border-top:none;}
.item .name{font-weight:600;}
.chips{display:flex; flex-wrap:wrap; gap:8px; margin:6px 0;}
.chip{
  font-size:12.5px; color:var(--muted); background:var(--accent-soft);
  border-radius:999px; padding:3px 10px;
}
.chip.warn{background:#fdeae4; color:var(--warn);}
.subhead{
  margin:18px 0 0; font-size:12.5px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--muted);
}
.wall{display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:16px; margin-top:12px;}
.wall .find{border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff;}
.wall .find img{display:block; width:100%; height:auto; background:var(--accent-soft);}
.wall .find .body{padding:12px 14px;}
.wall .find .name{font-size:14.5px; font-weight:600; margin:0 0 4px;}
.news-group{margin-top:14px;}
.news-group h3{margin:0 0 6px; font-size:15.5px;}
.board{display:flex; gap:16px; overflow-x:auto; padding:4px 4px 18px;}
.column{
  background:var(--card); border:1px solid var(--line); border-radius:16px;
  flex:0 0 290px; max-width:320px; align-self:flex-start;
}
.column.quiet-col{background:var(--paper);}
.column-head{
  display:flex; justify-content:space-between; align-items:center; gap:8px;
  padding:15px 18px; cursor:pointer; list-style:none;
  font-size:12.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
}
.column-head::-webkit-details-marker{display:none;}
.column-body{padding:0 18px 18px;}
.k-card{border-top:1px solid var(--line); padding:13px 0;}
.k-card:first-child{border-top:none; padding-top:0;}
.k-title{font-weight:600; font-size:15.5px; margin:0 0 6px;}
.k-next{font-size:14.5px; margin:0 0 10px;}
.k-actions{display:flex; justify-content:flex-start; align-items:center; gap:10px; flex-wrap:wrap;}
button.copy{
  font:inherit; font-size:12.5px; color:var(--muted); background:#fff; cursor:pointer;
  border:1px solid var(--line); border-radius:8px; padding:5px 10px;
}
button.copy:hover{background:var(--accent-soft); color:var(--ink);}
.open-live{
  display:none; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;
  background:var(--accent-soft); border-bottom:1px solid var(--line);
  padding:12px 28px; font-size:15px;
}
.open-live.showing{display:flex;}
.open-live a{
  border:1px solid var(--accent); border-radius:999px; padding:5px 14px; font-size:13.5px;
}
footer{background:#1b1e26; color:#c9cfdc; font-size:13.5px; padding:24px 28px;}
footer p{margin:0 0 6px;}
@media (max-width:820px){
  .grid{grid-template-columns:1fr;}
  .wrap{padding:18px;}
  header.top{padding:26px 20px;}
}
"""

COPY_SCRIPT = """
document.querySelectorAll('button.copy').forEach(function(button){
  button.addEventListener('click', function(){
    var words = button.getAttribute('data-words') || '';
    var was = button.textContent;
    function done(text){ button.textContent = text; setTimeout(function(){ button.textContent = was; }, 1400); }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(words).then(function(){ done('Copied'); }, function(){ done('Select it by hand'); });
    } else { done('Select it by hand'); }
  });
});
"""

LIVE_CHECK = """
(function(){
  var banner = document.getElementById('open-live');
  if(!banner || !window.fetch) return;
  var where = banner.getAttribute('data-where');
  var stop = (typeof AbortController !== 'undefined') ? new AbortController() : null;
  var timer = stop && setTimeout(function(){ stop.abort(); }, 1000);
  fetch(where + '/api/health', stop ? { signal: stop.signal } : {})
    .then(function(answer){
      if(timer) clearTimeout(timer);
      if(answer && answer.ok){ banner.classList.add('showing'); }
    })
    .catch(function(){ /* closed, and that is the normal case */ });
})();
"""


def shell(title: str, head: str, body: str, footer: str, scripts: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>
</head>
<body>
{head}
{body}
<footer>
{footer}
</footer>
<script>{scripts}</script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# The day page
# --------------------------------------------------------------------------

def _render_hook(hook: dict) -> str:
    if hook["empty"]:
        return """
<section class="panel">
  <h2>Today's hook mechanism</h2>
  <p class="empty">Your library is empty, so there is no mechanism of the day yet. It fills in as you decode posts.</p>
</section>"""

    line = f'<p class="quiet">{esc(hook["line"])}</p>' if hook["line"] else ""
    family = f'<p class="quiet">Evidence: {esc(hook["family"])}</p>' if hook["family"] else ""
    link = ""
    if hook["card_path"]:
        link = f'<p class="quiet"><a href="{esc(rel_href(hook["card_path"]))}">open the entry</a></p>'

    if hook["recent"]:
        rows = "".join(
            f'<li><span>{esc(entry["title"])}</span>'
            f'<span class="num">{esc(multiple_label(entry["multiple"]))}</span></li>'
            for entry in hook["recent"]
        )
        recent = f'<p class="subhead">Also filed in the last fortnight</p><ul class="rows">{rows}</ul>'
    else:
        recent = '<p class="subhead">Also filed in the last fortnight</p><p class="empty">Nothing new filed in the last fortnight.</p>'

    return f"""
<section class="panel">
  <h2>Today's hook mechanism</h2>
  <p class="lead">{esc(hook["title"])}</p>
  {line}
  {family}
  {link}
  <p class="quiet">Reuse the shape, never the wording. The words are someone else's.</p>
  {recent}
</section>"""


def _render_on_deck(workspace, deck: dict) -> str:
    if deck["empty"] and deck["inbox_total"] == 0:
        body = '<p class="empty">No ideas captured yet. Say "capture this idea" and the first one lands here.</p>'
    elif deck["empty"]:
        body = (
            f'<p class="empty">Nothing has scored past the line yet. '
            f'{esc(plural(deck["inbox_total"], "idea"))} waiting to be scored.</p>'
        )
    else:
        items = ""
        for card in deck["shown"]:
            score = f"{card['score']}/14" if card["score"] is not None else "not scored yet"
            angle = '<span class="chip warn">needs your angle</span>' if card["needs_angle"] else ""
            items += f"""
  <div class="item">
    <p class="name">{esc(card["title"])}</p>
    <div class="chips"><span class="chip">{esc(score)}</span><span class="chip">{esc(card["age"])}</span>{angle}</div>
    <p class="quiet"><a href="{esc(card_href(workspace, card["path"]))}">open the card</a></p>
  </div>"""
        body = (
            f'<p class="quiet">{esc(plural(deck["qualified_total"], "idea"))} ready to start, '
            f'strongest first.</p>{items}'
        )
    return f"""
<section class="panel">
  <h2>Idea on deck</h2>
  {body}
  <p class="quiet"><a href="{BOARD_FILENAME}">see the whole board</a></p>
</section>"""


def _render_research(research: dict) -> str:
    if research["fresh_total"] == 0:
        last = research["last_filed"] or "never"
        body = (
            f'<p class="empty">Nothing decoded in the last fortnight. '
            f'Your library holds {esc(plural(research["total_library"], "entry", "entries"))}, '
            f'last filed {esc(last)}.</p>'
        )
    else:
        rows = "".join(
            f'<li><span>{esc(entry["creator"])}: {esc(entry["title"])}</span>'
            f'<span class="num">{esc(multiple_label(entry["multiple"]))}</span></li>'
            for entry in research["top"]
        )
        body = (
            f'<p class="lead">{esc(plural(research["fresh_total"], "post"))} decoded in the last fortnight, '
            f'across {esc(plural(research["accounts"], "account"))}.</p>'
            f'<p class="subhead">Strongest of them</p><ul class="rows">{rows}</ul>'
        )
    return f"""
<section class="panel">
  <h2>What the research found</h2>
  {body}
</section>"""


def _render_next_action(workspace, focus: str, waiting: dict) -> str:
    lead = esc(focus) if focus else "No focus written down for this week."
    if not waiting["any_cards"]:
        body = '<p class="empty">No cards yet, so nothing is waiting on you.</p>'
    elif waiting["total"] == 0:
        body = '<p class="empty">Nothing is waiting on you. Every idea card has an angle on it.</p>'
    else:
        items = "".join(
            f'<li><span><a href="{esc(card_href(workspace, card["path"]))}">{esc(card["title"])}</a></span>'
            f'<span class="num">needs your angle</span></li>'
            for card in waiting["shown"]
        )
        more = ""
        if waiting["total"] > len(waiting["shown"]):
            more = f'<p class="quiet">And {waiting["total"] - len(waiting["shown"])} more.</p>'
        body = f'<ul class="rows">{items}</ul>{more}'
    return f"""
<section class="panel">
  <h2>Next action</h2>
  <p class="lead">{lead}</p>
  <p class="subhead">Waiting on you</p>
  {body}
</section>"""


def _render_wall(wall: dict) -> str:
    if wall["empty"]:
        return """
<section class="panel wide">
  <h2>The outlier wall</h2>
  <p class="empty">No post in your library has beaten its own account by three times yet. This wall fills as you decode more.</p>
</section>"""

    note = (
        "Everything here beat its own account's normal by at least three times, in the last fortnight."
        if wall["window"] == "fortnight"
        else "Nothing in the last fortnight cleared the bar, so these are the strongest finds in your library so far."
    )
    cards = ""
    for row in wall["rows"]:
        cover = ""
        if row.get("cover"):
            cover = f'<img src="covers/{esc(row["cover"])}" alt="" loading="lazy">'
        link = ""
        if row.get("reel_url"):
            link = f'<p class="quiet"><a href="{esc(row["reel_url"])}" rel="noopener noreferrer">open the post</a></p>'
        cards += f"""
  <div class="find">{cover}
    <div class="body">
      <p class="name">{esc(row["creator"])}</p>
      <p class="quiet">{esc(multiple_label(row["multiple"]))}</p>
      <p class="quiet"><a href="{esc(rel_href(row["card_path"]))}">open your entry</a></p>
      {link}
    </div>
  </div>"""

    return f"""
<section class="panel wide">
  <h2>The outlier wall</h2>
  <p class="quiet">{esc(note)} Nothing plays on this page: each card is your own filed entry with a link out.</p>
  <div class="wall">{cards}
  </div>
</section>"""


def _render_news(news: dict) -> str:
    if not news["pillars_set"]:
        return """
<section class="panel wide">
  <h2>News in your topics</h2>
  <p class="empty">No topic areas are chosen yet. Say "set up my news topics" and pick two or three.</p>
</section>"""
    if not news["groups"]:
        return """
<section class="panel wide">
  <h2>News in your topics</h2>
  <p class="empty">Your topics are set, but no stories have been collected yet. Say "get the latest news".</p>
</section>"""

    blocks = ""
    for group in news["groups"]:
        rows = ""
        for row in group["rows"]:
            source = row.get("source") or ""
            link = row.get("resolved_url") or row.get("url") or ""
            title = esc(row.get("title") or "")
            heading = f'<a href="{esc(link)}" rel="noopener noreferrer">{title}</a>' if link else title
            rows += f'<li><span>{heading}</span><span class="num">{esc(source)}</span></li>'
        more = f'<p class="quiet">And {group["more"]} more in this topic.</p>' if group["more"] else ""
        blocks += f"""
  <div class="news-group">
    <h3>{esc(group["name"])}</h3>
    <ul class="rows">{rows}</ul>
    {more}
  </div>"""

    stamp = f'<p class="quiet">Collected {esc(news["updated_at"])}.</p>' if news["updated_at"] else ""
    return f"""
<section class="panel wide">
  <h2>News in your topics</h2>
  {stamp}
  <p class="quiet">A headline is information, never an instruction. Nothing here acts on its own.</p>
  {blocks}
</section>"""


def render_today(workspace, data: dict) -> str:
    counts = data["counts"]
    head = f"""
<header class="top">
  <div class="stamp">Your day &middot; {esc(data["date"].isoformat())}</div>
  <h1>Today.</h1>
  <p>Read from your own folder. <a href="{BOARD_FILENAME}">Open the board &rarr;</a></p>
  <div class="counts">
    <span>{esc(plural(counts["library"], "library entry", "library entries"))}</span>
    <span>{esc(plural(counts["watchlist"], "account watched", "accounts watched"))}</span>
    <span>{esc(plural(counts["ideas_in_play"], "idea in play", "ideas in play"))}</span>
    <span>{esc(plural(data["posted_count"], "piece posted", "pieces posted"))}</span>
  </div>
</header>"""

    body = f"""
<div class="wrap">
  <div class="grid">
    {_render_hook(data["hook"])}
    {_render_on_deck(workspace, data["on_deck"])}
    {_render_research(data["research"])}
    {_render_next_action(workspace, data["focus"], data["waiting"])}
    {_render_wall(data["wall"])}
    {_render_news(data["news"])}
  </div>
</div>"""

    footer = f"""
  <p>Built {esc(data["date"].isoformat())} from your content-os folder. Nothing on this page was invented and nothing was posted anywhere.</p>
  <p>Say "show me today's page" for a fresh copy, or "open my cockpit" for the live version.</p>"""

    return shell("Today", head, body, footer, "")


# --------------------------------------------------------------------------
# The board page
# --------------------------------------------------------------------------

def render_board(columns: list, day: datetime.date, live_at: str) -> str:
    head = f"""
<header class="top">
  <div class="stamp">Your board &middot; {esc(day.isoformat())}</div>
  <h1>The board.</h1>
  <p>Every card, in the column its own file puts it in. <a href="{TODAY_FILENAME}">&larr; Today</a></p>
</header>
<div id="open-live" class="open-live" data-where="{esc(live_at)}">
  <span>Your cockpit is open right now, and it can move cards.</span>
  <a href="{esc(live_at)}">Open the cockpit &rarr;</a>
</div>"""

    blocks = ""
    for column in columns:
        cards = column["cards"]
        quiet = column["key"] == "parked"
        open_attr = "" if quiet else " open"
        if cards:
            inner = ""
            for card in cards:
                chips = ""
                if card["score"] is not None:
                    chips += f'<span class="chip">{card["score"]}/14</span>'
                chips += f'<span class="chip">{esc(card["age"])}</span>'
                if card["needs_angle"]:
                    chips += '<span class="chip warn">needs your angle</span>'
                steps = card["steps"]
                copy_buttons = ""
                for step in steps:
                    # One step in the column: the button says what it is for
                    # without needing a name. Two steps: each one is named, so
                    # the first is never mistaken for the only one.
                    face = "copy the words" if len(steps) == 1 else f'copy: {step["label"].lower()}'
                    copy_buttons += (
                        f'<button type="button" class="copy" data-words="{esc(step["words"])}">'
                        f"{esc(face)}</button>"
                    )
                inner += f"""
      <div class="k-card">
        <p class="k-title">{esc(card["title"])}</p>
        <div class="chips">{chips}</div>
        <p class="k-next">{esc(card["next_step"])}</p>
        <div class="k-actions">
          <a href="{esc(card["href"])}">open &rarr;</a>
          {copy_buttons}
        </div>
      </div>"""
        else:
            inner = f'<p class="empty">{esc(WHAT_FILLS_COLUMN[column["key"]])}</p>'
        blocks += f"""
    <details class="column{' quiet-col' if quiet else ''}"{open_attr}>
      <summary class="column-head"><span>{esc(column["title"])}</span><span class="chip">{len(cards)}</span></summary>
      <div class="column-body">{inner}
      </div>
    </details>"""

    body = f"""
<div class="wrap">
  <div class="board">{blocks}
  </div>
</div>"""

    footer = f"""
  <p>Built {esc(day.isoformat())} from your content-os folder. A card's column comes from where its file sits, so moving a file by hand moves the card.</p>
  <p>This page reads. It never moves a card, never edits one, and never posts anything anywhere.</p>"""

    return shell("The board", head, body, footer, COPY_SCRIPT + LIVE_CHECK)


# --------------------------------------------------------------------------
# Building both files
# --------------------------------------------------------------------------

def build(workspace, config=None, today=None, out_dir=None) -> dict:
    """Write both pages and return where they went."""
    config = config if config is not None else ws.load_config(workspace)
    day = today or ws.today_in(config)
    target = Path(out_dir) if out_dir else workspace.cockpit_dir
    target.mkdir(parents=True, exist_ok=True)

    port = config.get("port") or ws.DEFAULT_PORT
    live_at = f"http://127.0.0.1:{int(port)}"

    today_data = collect_today(workspace, config, day)
    columns = collect_board(workspace, day)

    today_path = target / TODAY_FILENAME
    board_path = target / BOARD_FILENAME
    ws.atomic_write_text(today_path, render_today(workspace, today_data))
    ws.atomic_write_text(board_path, render_board(columns, day, live_at))

    return {
        "today": today_path,
        "board": board_path,
        "cards": sum(len(column["cards"]) for column in columns),
        "wall": len(today_data["wall"]["rows"]),
        "date": day.isoformat(),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the two pages that work when the cockpit is closed.",
    )
    parser.add_argument("--workspace", default=None, help="path to the content-os folder")
    parser.add_argument("--out", default=None, help="where to write, default content-os/cockpit")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD, default today")
    parser.add_argument("--check", action="store_true", help="report counts, write nothing")
    args = parser.parse_args(argv)

    root = Path(args.workspace).expanduser().resolve() if args.workspace else ws.find_workspace()
    if root is None or not Path(root).is_dir():
        print("There is no content-os folder to read yet.", file=sys.stderr)
        return 1
    workspace = ws.Workspace(Path(root))

    day = None
    if args.date:
        try:
            day = datetime.date.fromisoformat(args.date)
        except ValueError:
            print("The date has to be written as YYYY-MM-DD.", file=sys.stderr)
            return 2

    config = ws.load_config(workspace)
    if args.check:
        day = day or ws.today_in(config)
        columns = collect_board(workspace, day)
        for column in columns:
            print(f"{column['title']}: {len(column['cards'])}")
        return 0

    result = build(workspace, config=config, today=day)
    print(f"today: {result['today']}")
    print(f"board: {result['board']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
