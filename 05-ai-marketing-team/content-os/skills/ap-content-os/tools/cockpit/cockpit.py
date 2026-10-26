#!/usr/bin/env python3
"""
cockpit.py - the member's content cockpit.

Standard library only. Nothing to install.

It answers on this machine and this machine only. The address it binds to is
127.0.0.1, which means the loopback address: the computer talking to itself.
Nothing on the member's network, and nothing on the internet, can reach it.
That is a rule of this file, not a setting: the bind address is a constant and
there is no way to change it.

What it does
------------
It reads the member's own content-os/ folder and shows it as seven views:
morning brief, board, viral now, patterns, news, calendar, library. It never
invents data. Every view has an honest empty state for a workspace that has
not been filled in yet.

What it is allowed to change
----------------------------
Very little, and only when the member clicks something:

  - it moves a whole card file between folders (promote, park, unpark, retire),
  - it appends a Retired section to a card that is being retired, and only
    when the member typed a reason,
  - it writes the planned-posts file and its own settings and receipts.

It never rewrites the body of a card, never reorders one, never edits what a
stage wrote, and never deletes anything. A move is a move: the file is renamed
into its new folder, never copied and then removed.

Every action is receipted to content-os/cockpit/actions-log.md.
"""

import datetime
import errno
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import agent_runtime  # noqa: E402
import board_state  # noqa: E402
import calendar_data  # noqa: E402
import library_data  # noqa: E402
import news_data  # noqa: E402
import posted_ledger  # noqa: E402
import thumbs  # noqa: E402
import viral_data  # noqa: E402
import workspace as ws  # noqa: E402

STATIC_DIR = HERE / "static"
RADAR_ENTRY = HERE / "news_radar.py"

# Loopback only. This is a rule of the file, not an option.
HOST = "127.0.0.1"
PORT = int(os.environ.get(ws.ENV_PORT, str(ws.DEFAULT_PORT)) or ws.DEFAULT_PORT)
DRYRUN = os.environ.get(ws.ENV_DRYRUN) == "1"

CARD_MAX_BYTES = 400_000

TAB_IDS = ["brief", "board", "viral", "patterns", "news", "calendar", "library"]
VALID_TAB_IDS = set(TAB_IDS)

COLUMN_TITLES = [
    ("inbox", "Inbox"),
    ("on_deck", "On deck"),
    ("interviewed", "Interviewed"),
    ("map_ready", "Map ready"),
    ("record_edit", "Record / Edit"),
    ("posted_learning", "Posted & learning"),
    ("parked", "Parked"),
]

# Which actions a card can offer, decided by the column it is actually in.
# A request naming an action that is not on this list for the card's current
# column is refused, whatever the browser asked for.
ACTIONS_BY_STAGE = {
    "inbox": [
        {"id": "score", "label": "Score idea", "kind": "agent"},
        {"id": "promote", "label": "Move to On deck", "kind": "instant"},
        {"id": "park", "label": "Park for later", "kind": "instant"},
    ],
    "on_deck": [
        {"id": "interview", "label": "Start the interview", "kind": "agent"},
        {"id": "park", "label": "Park for later", "kind": "instant"},
    ],
    "interviewed": [
        {"id": "talking_map", "label": "Build the talking map", "kind": "agent"},
    ],
    "map_ready": [
        {"id": "record_prep", "label": "Prep the recording", "kind": "agent"},
    ],
    # First the step that actually moves the piece out of the door: finish the
    # edit, stage it for posting, and log it once the owner says it is live.
    # Multiplying it into every other place is the second step, not the first.
    "record_edit": [
        {"id": "finish_and_publish", "label": "Finish the edit and stage it to post", "kind": "agent"},
        {"id": "multiply", "label": "Multiply into platforms", "kind": "agent"},
    ],
    "posted_learning": [
        {"id": "weekly_review", "label": "Run the weekly review", "kind": "agent"},
    ],
    "parked": [
        {"id": "unpark", "label": "Move back to On deck", "kind": "instant"},
    ],
}

AGENT_PROMPTS = {
    "score": board_state.prompt_score,
    "interview": board_state.prompt_interview,
    "talking_map": board_state.prompt_talking_map,
    "record_prep": board_state.prompt_record_prep,
    "finish_and_publish": board_state.prompt_finish_and_publish,
    "multiply": board_state.prompt_multiply,
    "weekly_review": board_state.prompt_weekly_review,
}

INSTANT_DEST = {
    ("inbox", "promote"): ("ideas", "qualified"),
    ("inbox", "park"): ("ideas", "parked"),
    ("on_deck", "park"): ("ideas", "parked"),
    ("parked", "unpark"): ("ideas", "qualified"),
}

IDEA_STAGES = ("inbox", "on_deck", "parked")

_SERVED_NAME_RE = thumbs.SERVED_NAME_RE

# --------------------------------------------------------------------------
# Workspace, resolved once at start
# --------------------------------------------------------------------------

WORKSPACE_ROOT = ws.find_workspace()
WORKSPACE = ws.Workspace(WORKSPACE_ROOT) if WORKSPACE_ROOT else None


def config():
    if WORKSPACE is None:
        return dict(ws.DEFAULT_CONFIG)
    return ws.load_config(WORKSPACE)


# --------------------------------------------------------------------------
# Background jobs
# --------------------------------------------------------------------------

JOBS = {}
JOBS_LOCK = threading.Lock()
_job_counter = 0


def _new_job(kind, **extra):
    global _job_counter
    with JOBS_LOCK:
        _job_counter += 1
        job_id = f"job-{int(time.time())}-{_job_counter}"
        JOBS[job_id] = {
            "id": job_id,
            "kind": kind,
            "status": "running",
            "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "finished_at": None,
            "error": None,
            **extra,
        }
        return job_id, dict(JOBS[job_id])


def _finish_job(job_id, status, error=None, **extra):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return
        job["status"] = status
        job["error"] = error
        job["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        job.update(extra)


def get_job(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        return dict(job) if job else None


def list_jobs():
    with JOBS_LOCK:
        return [dict(job) for job in JOBS.values()]


def _running(kind, **match):
    with JOBS_LOCK:
        for job in JOBS.values():
            if job.get("kind") != kind or job.get("status") != "running":
                continue
            if all(job.get(key) == value for key, value in match.items()):
                return True
    return False


def start_news_refresh():
    if _running("refresh_news"):
        return None
    job_id, snapshot = _new_job("refresh_news", label="Refreshing your industry news")

    def worker():
        try:
            result = subprocess.run(
                [sys.executable, str(RADAR_ENTRY), "--workspace", str(WORKSPACE.root)],
                cwd=str(HERE),
                capture_output=True,
                text=True,
                timeout=600,
            )
        except Exception as exc:
            _finish_job(job_id, "error", str(exc))
            return
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "").strip()[-500:]
            _finish_job(job_id, "error", message or "the news refresh did not finish")
            return
        _finish_job(job_id, "done")

    threading.Thread(target=worker, daemon=True).start()
    return snapshot


def known_post_codes():
    """Every post code the workspace itself knows about. Nothing else is ever
    fetchable, so no caller can point the cover cache at an arbitrary page."""
    codes = []
    for entry in library_data.load_entries(WORKSPACE.library_dir):
        if entry.get("shortcode"):
            codes.append(entry["shortcode"])
    for entry in posted_ledger.load_entries(WORKSPACE.posted_ledger):
        if entry.get("shortcode"):
            codes.append(entry["shortcode"])
    return codes


def start_cover_warm():
    if _running("warm_covers"):
        return None
    job_id, snapshot = _new_job("warm_covers", label="Fetching cover pictures", cached=None, failed=None)

    def worker():
        try:
            result = thumbs.warm(WORKSPACE.thumbs_dir, known_post_codes())
        except Exception as exc:
            _finish_job(job_id, "error", str(exc))
            return
        _finish_job(job_id, "done", cached=result["cached"], failed=result["failed"])

    threading.Thread(target=worker, daemon=True).start()
    return snapshot


def start_agent_step(action_id, card_id, prompt, label):
    """Hand one step to an assistant this machine can drive. A second click on
    the same step for the same card is refused rather than stacking two
    invisible runs."""
    if _running("step", action=action_id, card=card_id):
        return None
    job_id, snapshot = _new_job("step", action=action_id, card=card_id, label=label)
    log_path = WORKSPACE.step_logs_dir / f"{job_id}-{action_id}.log"
    with JOBS_LOCK:
        JOBS[job_id]["log"] = log_path.name

    def worker():
        try:
            agent_runtime.run_step(prompt, WORKSPACE.root.parent, log_path)
        except Exception as exc:
            _finish_job(job_id, "error", str(exc))
            return
        _finish_job(job_id, "done")

    threading.Thread(target=worker, daemon=True).start()
    with JOBS_LOCK:
        return dict(JOBS[job_id])


# --------------------------------------------------------------------------
# Board state
# --------------------------------------------------------------------------

def scan_raw():
    raw = {
        "inbox": board_state.load_idea_dir(WORKSPACE.inbox_dir),
        "on_deck": board_state.load_idea_dir(WORKSPACE.qualified_dir),
        "parked": board_state.load_idea_dir(WORKSPACE.parked_dir),
    }
    raw.update(board_state.load_production(WORKSPACE))
    return raw


def find_card(raw, card_id, stages=None):
    """Look a card id up in a fresh scan. A path from the browser is never
    used against the filesystem directly."""
    for stage in (stages or list(raw.keys())):
        for entry in raw.get(stage, []):
            if WORKSPACE.relative(entry["path"]) == card_id:
                return stage, entry
    return None, None


def _card_actions(stage, card):
    actions = ACTIONS_BY_STAGE.get(stage, [])
    if stage != "inbox":
        return [dict(action) for action in actions]
    out = []
    for action in actions:
        action = dict(action)
        if action["id"] == "score" and card.get("score") is not None:
            action["label"] = "Score it again"
        out.append(action)
    return out


def _idea_cards_json(entries, stage, today, show_score):
    out = []
    for card in entries:
        out.append({
            "id": WORKSPACE.relative(card["path"]),
            "title": card["title"],
            "score": card["score"] if show_score else None,
            "score_max": board_state.SCORE_MAX if show_score else None,
            "age": ws.format_age(card["captured"], today),
            "needs_angle": not card["angle"],
            "card_path": WORKSPACE.relative(card["path"]),
            "kind": "idea",
            "actions": _card_actions(stage, card),
        })
    return out


def _production_cards_json(entries, stage, today):
    out = []
    for item in entries:
        is_folder = item.get("kind") == "run"
        out.append({
            "id": WORKSPACE.relative(item["path"]),
            "title": item["title"],
            "score": None,
            "score_max": None,
            "age": ws.format_age(item["date"], today),
            "needs_angle": False,
            "card_path": None if is_folder else WORKSPACE.relative(item["path"]),
            "kind": item.get("kind", "script"),
            "actions": [dict(action) for action in ACTIONS_BY_STAGE.get(stage, [])],
        })
    return out


def build_state_json():
    today = ws.today_in(config())
    raw = scan_raw()
    sorters = {
        "inbox": board_state.sort_by_score,
        "on_deck": board_state.sort_by_score,
        "parked": board_state.sort_by_captured,
    }
    columns = []
    for key, title in COLUMN_TITLES:
        if key in sorters:
            entries = sorters[key](raw[key])
            cards = _idea_cards_json(entries, key, today, show_score=(key != "parked"))
        else:
            entries = board_state.sort_by_age(raw[key])
            cards = _production_cards_json(entries, key, today)
        columns.append({"id": key, "title": title, "cards": cards})
    return {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "columns": columns,
        "jobs": list_jobs(),
        "agent_mode": agent_runtime.detect()["mode"],
    }


# --------------------------------------------------------------------------
# Patterns feed - read the generated file, never anything else
# --------------------------------------------------------------------------

REQUIRED_FEED_SHAPES = {
    "generated_at": str,
    "as_of_date": str,
    "provisional": bool,
    "freshness": dict,
    "patterns": list,
    "views": dict,
    "test_next": list,
    "collecting_evidence": list,
}


def load_pattern_feed():
    """The generated patterns file, or an honest reason it cannot be shown.

    The analytics side owns every number and every state in that file. This
    only checks that the file has the shape it promises, so a half-written or
    older file is never presented as a real read. Missing or malformed gets a
    plain "unavailable" answer, never a made-up stand-in.
    """
    path = WORKSPACE.patterns_feed
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, (
            "No pattern read yet. Patterns appear once the weekly review has "
            "enough of your own numbers to compare."
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "The last pattern read cannot be shown because the file is damaged."
    if not isinstance(data, dict) or any(
        key not in data or not isinstance(data[key], expected)
        for key, expected in REQUIRED_FEED_SHAPES.items()
    ):
        return None, "The last pattern read is incomplete, so nothing is being shown."
    return data, None


# --------------------------------------------------------------------------
# Preferences
# --------------------------------------------------------------------------

def load_prefs():
    data = ws.read_json(WORKSPACE.prefs_path, default=None)
    if not isinstance(data, dict):
        return {"tab_order": None}
    order = data.get("tab_order")
    if (
        isinstance(order, list)
        and all(isinstance(item, str) for item in order)
        and set(order) == VALID_TAB_IDS
        and len(order) == len(TAB_IDS)
    ):
        return {"tab_order": order}
    return {"tab_order": None}


# --------------------------------------------------------------------------
# Retire - move the file, and append the reason without touching anything
# already on the card
# --------------------------------------------------------------------------

_RETIRE_REASON_MAX = 500


def append_retired_section(path: Path, today_str: str, reason: str) -> None:
    """Add a Retired section to the very bottom of a card.

    Append only. Nothing already on the card is read back out, rewritten,
    reordered, or removed, and no frontmatter is ever added: these cards are
    heading-structured markdown and stay that way. The reason is written
    exactly as the member typed it.
    """
    if not reason:
        return
    block = f"\n## Retired, {today_str}\n\n{reason}\n"
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(block)
    except OSError:
        pass


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ContentCockpit/1"

    # -- helpers -----------------------------------------------------------

    def _send_json(self, status, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type=None, cache=None):
        try:
            data = path.read_bytes()
        except OSError:
            return self._send_json(404, {"ok": False, "error": "not found"})
        guessed = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", guessed)
        if cache:
            self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _safe_static(root: Path, relative: str):
        candidate = (root / relative.lstrip("/")).resolve()
        root_resolved = root.resolve()
        if candidate != root_resolved and root_resolved not in candidate.parents:
            return None
        return candidate

    def _valid_host(self) -> bool:
        """Only this machine, addressed as itself. Anything else is refused,
        which stops a page on the open web from pointing a browser here."""
        host = self.headers.get("Host", "")
        return host in (f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"[::1]:{PORT}")

    def _valid_json_type(self) -> bool:
        return self.headers.get("Content-Type", "").lower().startswith("application/json")

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 1_000_000:
            return {} if length <= 0 else None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _no_workspace(self):
        return self._send_json(200, {
            "ok": False,
            "error": "no-workspace",
            "message": (
                "No content workspace found on this machine yet. Ask your "
                "assistant to set up your content system first."
            ),
        })

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # -- GET ---------------------------------------------------------------

    def do_GET(self):
        if not self._valid_host():
            return self._send_json(403, {"ok": False, "error": "this address is not allowed"})
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/health":
            # The saved board page is a file on disk, so its "is the cockpit
            # open?" check counts as coming from somewhere else and a browser
            # hides the answer unless the answer says it may be read. This one
            # line is what lets that page offer the link across. It is on this
            # answer and no other: health says only yes-I-am-here, and every
            # answer that carries the member's own work stays unreadable to any
            # page but this one's own.
            return self._send_json(200, {
                "ok": True,
                "version": "1",
                "workspace": bool(WORKSPACE and WORKSPACE.exists()),
            }, {"Access-Control-Allow-Origin": "*"})

        if path in ("/", ""):
            index = STATIC_DIR / "index.html"
            if not index.is_file():
                return self._send_json(404, {"ok": False, "error": "the cockpit page is missing"})
            return self._send_file(index, "text/html; charset=utf-8")

        if path.startswith("/static/"):
            target = self._safe_static(STATIC_DIR, path[len("/static/"):])
            if target is None or not target.is_file():
                return self._send_json(404, {"ok": False, "error": "not found"})
            return self._send_file(target)

        if WORKSPACE is None or not WORKSPACE.exists():
            if path.startswith("/api/"):
                return self._no_workspace()
            return self._send_json(404, {"ok": False, "error": "not found"})

        if path == "/api/setup":
            detected = agent_runtime.detect()
            settings = ws.load_news_pillars(WORKSPACE)
            current = config()
            return self._send_json(200, {
                "ok": True,
                "set_up": WORKSPACE.is_set_up(),
                "agent_mode": detected["mode"],
                "timezone": current.get("timezone", ""),
                "region_name": current.get("region_name", ""),
                "pillars_set": bool(settings.get("pillars")),
                "posted_ledger": WORKSPACE.posted_ledger.is_file(),
                "patterns_feed": WORKSPACE.patterns_feed.is_file(),
            })

        if path == "/api/state":
            return self._send_json(200, build_state_json())

        if path == "/api/brief":
            return self._send_json(200, self._brief_payload())

        if path == "/api/viral":
            return self._send_json(200, {
                "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "entries": self._viral_entries(),
            })

        if path == "/api/library":
            return self._send_json(200, {
                "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "entries": self._viral_entries(),
            })

        if path == "/api/patterns":
            payload, error = load_pattern_feed()
            if error:
                return self._send_json(
                    503, {"ok": False, "error": error}, {"Cache-Control": "no-store"}
                )
            return self._send_json(200, payload, {"Cache-Control": "no-store"})

        if path == "/api/news":
            payload = news_data.build_news_payload(WORKSPACE.news_archive)
            settings = ws.load_news_pillars(WORKSPACE)
            payload["pillars_set"] = bool(settings.get("pillars"))
            payload["pillar_names"] = {p["id"]: p["name"] for p in settings.get("pillars", [])}
            payload["region_name"] = config().get("region_name", "")
            return self._send_json(200, payload)

        if path == "/api/calendar":
            query = parse_qs(parsed.query)
            try:
                days = int(query["days"][0])
            except (KeyError, IndexError, ValueError):
                days = 30
            days = max(1, min(days, 366))
            current = config()
            result = calendar_data.past_posts(WORKSPACE, current, days=days)
            result["plans"] = calendar_data.plans_list(WORKSPACE)
            return self._send_json(200, result)

        if path == "/api/prefs":
            return self._send_json(200, load_prefs())

        if path == "/api/card":
            query = parse_qs(parsed.query)
            return self._send_card(query.get("path", [""])[0])

        if path.startswith("/api/job/"):
            job = get_job(path[len("/api/job/"):])
            if job is None:
                return self._send_json(404, {"ok": False, "error": "unknown job"})
            return self._send_json(200, {"ok": True, "job": job})

        if path.startswith("/media/covers/"):
            name = path[len("/media/covers/"):]
            if not _SERVED_NAME_RE.match(name):
                return self._send_json(404, {"ok": False, "error": "not found"})
            target = self._safe_static(WORKSPACE.thumbs_dir, name)
            if target is None or not target.is_file():
                return self._send_json(404, {"ok": False, "error": "not found"})
            return self._send_file(target, "image/jpeg", cache="max-age=86400")

        return self._send_json(404, {"ok": False, "error": "not found"})

    # -- payload builders ---------------------------------------------------

    def _brief_payload(self):
        current = config()
        data = dict(viral_data.brief_data(WORKSPACE, current))
        raw = scan_raw()
        # The same picker the printed day page uses, so the window and the
        # page can never name a different idea on deck.
        ranked = board_state.rank_on_deck(raw.get("on_deck", []), raw.get("inbox", []))
        if ranked:
            top = ranked[0]
            data["recommended"] = {
                "title": top["title"],
                "card_id": WORKSPACE.relative(top["path"]),
                "score": top["score"],
            }
        else:
            data["recommended"] = None
        return data

    def _viral_entries(self):
        current = config()
        entries = viral_data.build_entries(WORKSPACE, current)
        for entry in entries:
            entry["thumb"] = thumbs.cached_name(WORKSPACE.thumbs_dir, entry.get("shortcode"))
        return entries

    def _send_card(self, relative_path):
        """One card's text, for the in-app viewer. Only markdown files inside
        the workspace can be read, and the text goes out as data for the page
        to show as plain text."""
        target = WORKSPACE.resolve_inside(relative_path)
        if target is None or not target.is_file() or target.suffix.lower() != ".md":
            return self._send_json(404, {"ok": False, "error": "that card is not here"})
        try:
            if target.stat().st_size > CARD_MAX_BYTES:
                return self._send_json(413, {"ok": False, "error": "that card is too big to show"})
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return self._send_json(404, {"ok": False, "error": "that card could not be read"})
        return self._send_json(200, {
            "ok": True,
            "path": WORKSPACE.relative(target),
            "name": target.name,
            "text": text,
        })

    # -- POST --------------------------------------------------------------

    def do_POST(self):
        if not self._valid_host():
            return self._send_json(403, {"ok": False, "error": "this address is not allowed"})
        path = urlparse(self.path).path

        # Requiring JSON forces the browser to ask permission first, which
        # blocks a plain form on any other page from posting here.
        if not self._valid_json_type():
            return self._send_json(400, {"ok": False, "error": "this request needs to be JSON"})
        body = self._read_json_body()
        if body is None or not isinstance(body, dict):
            return self._send_json(400, {"ok": False, "error": "that request could not be read"})

        if WORKSPACE is None or not WORKSPACE.exists():
            return self._no_workspace()

        if path == "/api/action":
            return self._handle_action(body)
        if path == "/api/retire":
            return self._handle_retire(body)
        if path == "/api/job":
            return self._handle_job(body)
        if path == "/api/calendar/plan":
            return self._handle_plan(body)
        if path == "/api/prefs":
            return self._handle_prefs(body)
        return self._send_json(404, {"ok": False, "error": "not found"})

    def _handle_job(self, body):
        kind = body.get("kind")
        if kind == "warm_covers":
            job = start_cover_warm()
            if job is None:
                return self._send_json(409, {"ok": False, "error": "that is already running"})
            return self._send_json(200, {"ok": True, "job": job})
        if kind == "refresh_news":
            settings = ws.load_news_pillars(WORKSPACE)
            if not settings.get("pillars"):
                return self._send_json(400, {
                    "ok": False,
                    "error": (
                        "No topic areas are set yet. Ask your assistant to set up "
                        "your industry news topics first."
                    ),
                })
            job = start_news_refresh()
            if job is None:
                return self._send_json(409, {"ok": False, "error": "a news refresh is already running"})
            return self._send_json(200, {"ok": True, "job": job})
        return self._send_json(400, {"ok": False, "error": f"unknown job: {kind!r}"})

    def _handle_prefs(self, body):
        order = body.get("tab_order")
        valid = (
            isinstance(order, list)
            and all(isinstance(item, str) for item in order)
            and len(order) == len(TAB_IDS)
            and set(order) == VALID_TAB_IDS
        )
        if not valid:
            return self._send_json(400, {
                "ok": False,
                "error": "the tab order has to list every tab exactly once",
            })
        ws.atomic_write_json(WORKSPACE.prefs_path, {
            "tab_order": order,
            "updated": datetime.datetime.now().isoformat(timespec="seconds"),
        })
        return self._send_json(200, {"ok": True})

    def _handle_plan(self, body):
        operation = body.get("op")
        try:
            if operation == "add":
                plan = calendar_data.plan_add(
                    WORKSPACE, body.get("date"), body.get("title"), body.get("note", "")
                )
                subject = f"{plan['date']} {plan['title']}"[:60]
                action = "plan-add"
            elif operation == "update":
                plan_id = body.get("id")
                fields = {k: v for k, v in body.items() if k in calendar_data.PLAN_FIELDS}
                calendar_data.plan_update(WORKSPACE, plan_id, **fields)
                subject = str(plan_id)[:60]
                action = "plan-update"
            elif operation == "delete":
                plan_id = body.get("id")
                if not calendar_data.plan_delete(WORKSPACE, plan_id):
                    return self._send_json(400, {"ok": False, "error": "there is no plan with that id"})
                subject = str(plan_id)[:60]
                action = "plan-delete"
            else:
                return self._send_json(400, {"ok": False, "error": f"unknown request: {operation!r}"})
        except ValueError as exc:
            return self._send_json(400, {"ok": False, "error": str(exc)})
        ws.append_receipt(WORKSPACE, action, subject, "saved")
        return self._send_json(200, {"ok": True, "plans": calendar_data.plans_list(WORKSPACE)})

    def _handle_action(self, body):
        action_id = body.get("action")
        card_id = body.get("card")
        if not action_id or not isinstance(action_id, str):
            return self._send_json(400, {"ok": False, "error": "no action was named"})

        if action_id == "capture":
            return self._run_agent_step(board_state.prompt_capture(), "capture", None, "Capture a new idea")

        if not card_id or not isinstance(card_id, str):
            return self._send_json(400, {"ok": False, "error": "no card was named"})

        raw = scan_raw()
        stage, entry = find_card(raw, card_id)
        if stage is None:
            return self._send_json(400, {"ok": False, "error": "that card is no longer on the board"})

        allowed = ACTIONS_BY_STAGE.get(stage, [])
        definition = next((a for a in allowed if a["id"] == action_id), None)
        if definition is None:
            return self._send_json(400, {
                "ok": False,
                "error": f"'{action_id}' is not something a card in {stage} can do",
            })

        if definition["kind"] == "instant":
            return self._run_instant(stage, action_id, card_id, entry)
        prompt = AGENT_PROMPTS[action_id](card_id)
        return self._run_agent_step(prompt, action_id, card_id, definition["label"])

    def _run_instant(self, stage, action_id, card_id, entry):
        destination = INSTANT_DEST.get((stage, action_id))
        if destination is None:
            return self._send_json(400, {"ok": False, "error": "nothing to do for that action"})
        dest_dir = WORKSPACE.root.joinpath(*destination)
        source = entry["path"]
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            target = ws.unique_destination(dest_dir, source.name)
            source.rename(target)  # a move, never a copy and delete
        except OSError as exc:
            return self._send_json(500, {"ok": False, "error": f"that move did not work: {exc}"})
        result = f"moved to {'/'.join(destination)}/"
        ws.append_receipt(WORKSPACE, action_id, card_id, result)
        return self._send_json(200, {"ok": True, "result": result, "state": build_state_json()})

    def _run_agent_step(self, prompt, action_id, card_id, label):
        """Either hand the step to an assistant on this machine, or hand the
        exact same words back for the member to paste into their app."""
        detected = agent_runtime.detect()
        if DRYRUN:
            ws.append_receipt(WORKSPACE, action_id, card_id or "-", "practice run, nothing was run")
            return self._send_json(200, {
                "ok": True,
                "mode": "dryrun",
                "prompt": prompt,
                "argv": agent_runtime.build_argv(prompt),
            })
        if detected["mode"] != "run":
            ws.append_receipt(WORKSPACE, action_id, card_id or "-", "handed over to copy")
            return self._send_json(200, {
                "ok": True,
                "mode": "copy",
                "prompt": prompt,
                "label": label,
            })
        job = start_agent_step(action_id, card_id, prompt, label)
        if job is None:
            return self._send_json(409, {
                "ok": False,
                "error": "That step is already running. Give it a couple of minutes.",
            })
        ws.append_receipt(WORKSPACE, action_id, card_id or "-", f"started in the background ({job['id']})")
        return self._send_json(200, {"ok": True, "mode": "run", "job": job})

    def _handle_retire(self, body):
        card_id = body.get("card")
        destination = body.get("dest")
        reason = body.get("reason", "")

        if not card_id or not isinstance(card_id, str):
            return self._send_json(400, {"ok": False, "error": "no card was named"})
        if destination not in ("retired", "not_content"):
            return self._send_json(400, {"ok": False, "error": "that is not a place to retire to"})
        if reason is None:
            reason = ""
        if not isinstance(reason, str):
            return self._send_json(400, {"ok": False, "error": "the reason has to be text"})
        if len(reason) > _RETIRE_REASON_MAX:
            return self._send_json(400, {
                "ok": False,
                "error": f"the reason has to be {_RETIRE_REASON_MAX} characters or fewer",
            })
        reason = reason.strip()

        raw = scan_raw()
        today_str = ws.today_in(config()).isoformat()
        stage, entry = find_card(raw, card_id, stages=IDEA_STAGES)
        if stage is not None:
            return self._retire_idea(entry, card_id, destination, reason, today_str)

        stage, entry = find_card(raw, card_id, stages=board_state.STAGE_ORDER)
        if stage is None:
            return self._send_json(400, {"ok": False, "error": "that card is no longer on the board"})
        if destination != "retired":
            return self._send_json(400, {
                "ok": False,
                "error": "work in production can only be retired, not sent back to the inbox",
            })
        return self._retire_production(stage, entry, card_id, reason, today_str)

    def _retire_idea(self, entry, card_id, destination, reason, today_str):
        source = entry["path"]
        # Append only. Nothing already on the card is touched.
        append_retired_section(source, today_str, reason)
        dest_dir = WORKSPACE.retired_ideas_dir if destination == "retired" else WORKSPACE.not_content_dir
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            target = ws.unique_destination(dest_dir, source.name)
            source.rename(target)
        except OSError as exc:
            return self._send_json(500, {"ok": False, "error": f"that move did not work: {exc}"})
        where = WORKSPACE.relative(target)
        ws.append_receipt(
            WORKSPACE,
            "retire" if destination == "retired" else "retire-not-content",
            card_id,
            f"moved to {where}" + (f" | reason: {reason}" if reason else ""),
        )
        return self._send_json(200, {"ok": True, "state": build_state_json()})

    def _retire_production(self, stage, entry, card_id, reason, today_str):
        source = entry["path"]
        if entry.get("kind") == "run":
            note = source / "retired.md"
            block = (
                f"# Retired\n\n"
                f"- retired on: {today_str}\n"
                f"- left from: {stage}\n"
                f"- reason: {reason or '(none given)'}\n"
            )
            try:
                existing = note.read_text(encoding="utf-8") if note.exists() else ""
                note.write_text(existing + block if existing else block, encoding="utf-8")
            except OSError as exc:
                return self._send_json(500, {"ok": False, "error": f"the note did not save: {exc}"})
            dest_dir = WORKSPACE.retired_runs_dir
        else:
            append_retired_section(source, today_str, reason)
            dest_dir = WORKSPACE.retired_scripts_dir
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            target = ws.unique_destination(dest_dir, source.name)
            source.rename(target)
        except OSError as exc:
            return self._send_json(500, {"ok": False, "error": f"that move did not work: {exc}"})
        ws.append_receipt(
            WORKSPACE, "retire", card_id,
            f"moved to {WORKSPACE.relative(target)}" + (f" | reason: {reason}" if reason else ""),
        )
        return self._send_json(200, {"ok": True, "state": build_state_json()})


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------

def main():
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        if exc.errno in (errno.EADDRINUSE, errno.EACCES):
            print(f"The cockpit is already open at http://{HOST}:{PORT}")
            return 0
        raise
    if WORKSPACE is None:
        print("No content workspace found. The cockpit will show an empty state.")
    else:
        print(f"Reading {WORKSPACE.root}")
    print(f"Cockpit ready at http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
