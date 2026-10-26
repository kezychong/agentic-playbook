"""Jarvis mode — the backend half, mounted by the Hermes dashboard.

Routes land at ``/api/plugins/hermes-jarvis/`` via
``hermes_cli/web_server_dashboard.py::_mount_plugin_api_routes``, which imports
THIS FILE BY PATH (``importlib.util.spec_from_file_location``) under the module
name ``hermes_dashboard_plugin_hermes-jarvis`` and mounts the module-level
``router``. There is no parent package at that point, so nothing here uses a
relative import and the module carries no plugin-local imports at all.

What this layer is, and is not:

- **It stores and relays; it never decides.** The desktop half owns presence
  (§4.1 of SPEC.md) and posts it here at up to 10 Hz. This process keeps the
  last one in memory and pushes it to the mirror page over ``/events``. The
  only things it writes to disk are the three small file-seam files under the
  selected profile's ``jarvis`` directory; no route persists
  anything else, so a restart starts blank apart from those.
- **It mints nothing, and it gates the one route the host cannot.** The HTTP
  routes ride the host's own session auth (``web_server.py::auth_middleware``
  and the OAuth gate). HTTP middleware never runs for a WebSocket upgrade, so
  ``/events`` calls the host's own WS checks itself, before ``accept()``, and
  fails closed when they are missing. No credential is defined or stored here.
- **Every read of Member's vault is guarded.** ``/state`` reads four vault
  files, Agent's ``STATE.md``, and the six v3 readings of SPEC §8.3 (his briefs,
  his background helpers, his calendar, today's contract, the overnight cron
  file and today's model usage), all of which may be absent, on a machine that
  may not have a vault at all. A missing or unreadable file becomes ``null`` (or
  ``rows: []``, or a block with ``status`` and a ``note``) — never an exception,
  never a fabricated value (the honesty rule, SPEC §0). Every one of those reads
  is read-only: files are opened for reading and capped, Agent's ``state.db`` is
  opened through a ``file:…?mode=ro`` URI and closed before the reader returns,
  and the calendar is a read-only scope in a separate short-lived process.

Two seams reach Agent's tools (``__init__.py``), and neither one involves auth:

- **In process.** ``JARVIS_STATE``, :func:`push_panel`, :func:`read_presence`
  and :func:`read_status` are module-level on purpose. A tool running inside
  this process finds this module in ``sys.modules`` and calls them directly.
- **A file seam** in the selected profile's ``jarvis`` directory (0700).
  Agent's agent is a different process on the same computer, under the same user, so
  three small JSON files carry what the two halves need: the tool writes
  ``panel.json`` and this module picks it up; this module writes
  ``presence.json`` and ``status.json`` and the tool reads them. Every write is
  atomic (temp file plus ``os.replace``), so a reader never sees half a file,
  and nothing here needs the dashboard's session cookie. The tools see new
  presence the moment it lands; no gateway restart, no re-registration.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketException
from starlette.requests import HTTPConnection
from fastapi.responses import HTMLResponse, JSONResponse, Response

def assert_profile_scope(connection: HTTPConnection) -> None:
    """This plugin belongs to one dashboard process, never a profile multiplexer."""
    if connection.scope.get("type") == "http" and connection.headers.get("origin"):
        try:
            host_checks = importlib.import_module(_HOST_WS_AUTH_MODULE)
            reason = getattr(host_checks, "_ws_host_origin_reason")(connection)
        except Exception:
            reason = "origin check unavailable"
        if reason is not None:
            raise HTTPException(status_code=403, detail="Jarvis origin refused")
    selectors = connection.query_params.getlist("profile")
    if not selectors:
        return
    try:
        profile_id = get_config().profile_id
        matches = all(value == profile_id for value in selectors)
    except Exception:
        matches = False
    if not matches:
        if connection.scope.get("type") == "websocket":
            raise WebSocketException(code=1008, reason="jarvis: profile mismatch")
        raise HTTPException(status_code=403, detail="Jarvis belongs to a different profile")


router = APIRouter(dependencies=[Depends(assert_profile_scope)])

_DASHBOARD_DIR = Path(__file__).resolve().parent
_PLUGIN_ROOT = _DASHBOARD_DIR.parent
#: Written by ``scripts/build.py`` (another builder owns it); absent until a build has run.
_MIRROR_HTML = _DASHBOARD_DIR / "mirror.html"


def _load_config_module():
    path = _PLUGIN_ROOT / "config.py"
    name = "hermes_jarvis_config_" + str(abs(hash(str(_PLUGIN_ROOT))))
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Jarvis config support is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_CONFIG = _load_config_module()
_PROFILE_ROOT = _CONFIG.profile_root_from_plugin(_PLUGIN_ROOT)

#: How long a ``/state`` answer is reused before the files are read again.
_STATE_CACHE_S = 30.0
#: Server-side keepalive on ``/events``.
_PING_S = 15.0
#: The watch loop ticks every second (that is the panel-file poll) and does its
#: heavier work on these intervals.
_WATCH_TICK_S = 1.0
_STATE_PUSH_S = 15.0
#: Write caps on the file seam: presence changes fast, status does not.
_PRESENCE_FILE_S = 1.0
_STATUS_FILE_S = 5.0

#: The file seam. Same resolution in ``__init__.py``; keep the two in step.
_PANEL_FILE = "panel.json"
_PRESENCE_FILE = "presence.json"
_STATUS_FILE = "status.json"

_CALENDAR_HELPER = _DASHBOARD_DIR / "jarvis_calendar.py"

#: How long each v3 reading is reused. Each reader owns its own cache entry, so a slow
#: or broken one never delays or empties the others (SPEC §8.3).
_BRIEFS_CACHE_S = 30.0
_HELPERS_CACHE_S = 20.0
_JOBS_CACHE_S = 60.0
_TODAY_CACHE_S = 30.0
_ONE_THING_CACHE_S = 60.0
_SPEND_CACHE_S = 60.0
#: The calendar is the one network reading: 5 minutes, refreshed off the request path.
_CALENDAR_CACHE_S = 300.0
#: SPEC §8 amendments C4 — after a FAILED refresh, no new helper subprocess for five
#: minutes. Without this every ``/state`` rebuild started another one while the error
#: stood (a poll every few seconds, each one an 8 s-budget Python process), and the
#: last good value was already being served the whole time anyway.
_CALENDAR_FAIL_BACKOFF_S = 300.0
_CALENDAR_TIMEOUT_S = 8.0
_CALENDAR_WINDOW_H = 36

#: Agent's ``state.db`` is opened read-only, waits this long for a writer and no longer,
#: and the connection is closed before the reader returns.
_DB_BUSY_S = 2.0
_DB_ROW_CAP = 400
_USAGE_ROW_CAP = 5000
#: A helper counts as running while it has no end and was touched inside this window.
_HELPER_RUNNING_S = 30 * 60
_HELPER_RECENT_S = 24 * 60 * 60
_HELPER_RECENT_MAX = 5
#: Caps from SPEC §8.3.2 and §8.3.5.
_GOAL_MAX = 140
_SUMMARY_MAX = 200
_JOB_ERROR_MAX = 160
_HEADLINE_MAX = 240
_SCOREBOARD_DAYS = 7
_SCOREBOARD_STALE_DAYS = 3
_JOBS_NEXT_UP = 3
_MEETING_LATER = 3
#: Read caps, the way ``_AGENT_STATE_MAX_CHARS`` caps Agent's STATE.md.
_BRIEFS_MAX_CHARS = 64 * 1024
_TODAY_MAX_CHARS = 256 * 1024
_JOBS_MAX_CHARS = 4 * 1024 * 1024

#: Agent's STATE.md is read this far in and no further (SPEC §7.5). A runaway file is
#: truncated with a note, never refused, and the cut final line is dropped rather than
#: half-parsed.
_AGENT_STATE_MAX_CHARS = 64 * 1024
#: One field of one row, capped the way the lever and the log are capped above.
_AGENT_FIELD_MAX = 400

_KIND_RE = re.compile(r"[^a-z0-9_-]+")

# Stable source id -> preserved source-engine capability.  The member labels may
# change later; these ids and reader behaviors are the backend contract.
SOURCE_PARITY = {
    "agent_state": "in-flight rows, due state, and optional brief attachment",
    "agent_helpers": "24-hour delegation window, running/recent counts and delivery",
    "next_meeting": "read-only calendar, timed-event preference and later events",
    "today_plan": "dated contract, headline, three items and lever",
    "overnight_jobs": "overnight window, failures, paused count and next jobs",
    "one_thing_scoreboard": "streak metrics, seven structured days and staleness",
    "spend": "model calls, tokens, cache reads and honest cost availability",
    "lever": "frontmatter or section ONE lever",
    "brains": "configured mirrors with capped recursive freshness",
    "scoreboard": "headline and two detail lines",
    "log": "newest dated operations entry",
}

#: Agent's STATE.md grammar (SPEC §7.5): ``## In flight`` holds one row per line,
#: ``- [id] where it stands | next: action | owner | follow_up_at | last update``.
#: Every one of these is deliberately loose: the file is written by an agent in a hurry
#: and a row that does not fit must go null, never raise.
_AGENT_IN_FLIGHT_RE = re.compile(r"^#{1,6}\s*in\s+flight\b", re.I)
_AGENT_CLOSED_RE = re.compile(r"^#{1,6}\s*recently\s+closed\b", re.I)
#: A row starts at column 0. Anything indented is a note under a row, not a row.
_AGENT_BULLET_RE = re.compile(r"^[-*+]\s+(\S.*)$")
_AGENT_ID_RE = re.compile(r"^\[([^\]]{1,80})\]\s*(.*)$")
_AGENT_NEXT_RE = re.compile(r"^next\s*:\s*(.*)$", re.I)
#: ``2026-09-22T09:00+08:00``, ``2026-09-22 09:00``, ``2026-09-22`` and the Z form.
#: Anything else (Agent's own truncated ``2026-09-19T`` included) simply does not match.
_AGENT_STAMP_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})"
    r"(?:[T ](\d{1,2}):(\d{2})(?::(\d{2}))?)?"
    r"\s*(Z|[+-]\d{2}:?\d{2})?$",
    re.I,
)


#: A presence frame is a small object; anything larger is not one.
_PRESENCE_MAX_BYTES = 64 * 1024

#: Where the host defines the checks its own WebSocket routes run before ``accept()``
#: (``web_routers/chat_ws.py`` and ``web_routers/audio.py`` both call these two).
_HOST_WS_AUTH_MODULE = "hermes_cli.web_server_chat"


def _plugin_version() -> str:
    """Version from ``plugin.yaml`` without a YAML dependency (one flat key)."""
    try:
        text = (_PLUGIN_ROOT / "plugin.yaml").read_text(encoding="utf-8")
    except OSError:
        return "0.0.0"
    match = re.search(r"^version:\s*[\"']?([^\"'\s]+)", text, re.M)
    return match.group(1) if match else "0.0.0"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class _Reading:
    """One v3 reader's private cache (SPEC §8.3: "its own cache").

    ``value`` is the last block this reader built successfully, ``key`` the source paths
    it was built from, ``at`` when that happened. ``error`` remembers why the most recent
    refresh failed, so a stale value can say so. ``lock`` and ``refreshing`` belong to the
    calendar, the one reader that refreshes on a background thread.
    """

    value: Optional[Dict[str, Any]] = None
    at: float = 0.0
    key: Optional[str] = None
    error: Optional[str] = None
    refreshing: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class JarvisState:
    """Everything this plugin knows, in memory, for the life of the process."""

    version: str = field(default_factory=_plugin_version)
    presence: Optional[Dict[str, Any]] = None
    presence_at: float = 0.0
    panel: Optional[Dict[str, Any]] = None
    panel_expires_at: float = 0.0
    clients: Set[Any] = field(default_factory=set)
    #: The dashboard's event loop, captured when the first ws client connects, so a
    #: sync caller on another thread can still reach the broadcast.
    loop: Optional[asyncio.AbstractEventLoop] = None
    watch_task: Optional[Any] = None
    state_cache: Optional[Dict[str, Any]] = None
    state_cache_key: Optional[Tuple[str, ...]] = None
    state_cache_at: float = 0.0
    #: SPEC §8.3 — one cache entry per v3 reading, keyed by name. A reader that fails
    #: keeps its own last good value here and never touches anybody else's.
    readings: Dict[str, "_Reading"] = field(default_factory=dict)
    last_state_sent: Optional[Dict[str, Any]] = None
    #: The panel Agent's tool wrote to ``panel.json``, and what we know about that file.
    file_panel: Optional[Dict[str, Any]] = None
    file_panel_expires_at: float = 0.0
    panel_file_mtime: Optional[float] = None
    #: Id of the panel last pushed to the mirror clients (None once a clear was pushed);
    #: ``_UNSENT`` until the first push, so an empty start does not broadcast a clear.
    last_panel_sent_id: Any = "__unsent__"
    #: Last time each seam file was written, for the write caps above.
    presence_file_at: float = 0.0
    status_file_at: float = 0.0


JARVIS_STATE = JarvisState()
_CONFIG_SIGNATURE: Any = None


# -- paths ------------------------------------------------------------------


def _clear_private_state() -> None:
    JARVIS_STATE.presence = None
    JARVIS_STATE.presence_at = 0.0
    JARVIS_STATE.panel = None
    JARVIS_STATE.panel_expires_at = 0.0
    JARVIS_STATE.file_panel = None
    JARVIS_STATE.file_panel_expires_at = 0.0
    JARVIS_STATE.state_cache = None
    JARVIS_STATE.readings.clear()


def get_config():
    global _CONFIG_SIGNATURE
    try:
        config = _CONFIG.load_config(_PLUGIN_ROOT)
    except Exception:
        _CONFIG_SIGNATURE = None
        _clear_private_state()
        raise
    signature = (
        config.config_path.stat().st_mtime_ns,
        config.profile_id, config.agent_name, config.owner_label, config.timezone,
        None if config.enabled_boxes is None else tuple(sorted(config.enabled_boxes)),
        tuple(sorted(config.enabled_sources)),
        tuple(sorted((name, repr(dict(spec))) for name, spec in config.sources.items())),
        tuple((brain.id, brain.label, str(brain.path)) for brain in config.brains),
    )
    if _CONFIG_SIGNATURE is not None and signature != _CONFIG_SIGNATURE:
        JARVIS_STATE.state_cache = None
        JARVIS_STATE.state_cache_key = None
        JARVIS_STATE.readings.clear()
    _CONFIG_SIGNATURE = signature
    return config


def _zone() -> Any:
    return get_config().zone


def _source_spec(source_id: str) -> Optional[Dict[str, Any]]:
    value = get_config().sources.get(source_id)
    return dict(value) if value is not None else None


def _source_path(source_id: str, key: str = "path") -> Path:
    spec = _source_spec(source_id)
    if spec is None or key not in spec:
        raise _CONFIG.ConfigError(f"selected source is unconfigured: {source_id}")
    return Path(spec[key])


def _vault_root() -> Path:
    return get_config().profile_root


def _scoreboard_path() -> Path:
    return _source_path("scoreboard")


def _agent_state_path() -> Path:
    return _source_path("agent_state")


def _hermes_home() -> Path:
    return get_config().profile_root


def _state_dir() -> Path:
    return get_config().state_dir


def _ensure_state_dir() -> Optional[Path]:
    """The seam directory, created 0700 on first write. None when it cannot exist."""
    try:
        return _CONFIG.ensure_state_dir(get_config().profile_root)
    except Exception:
        return None


def _write_json_atomic(name: str, payload: Dict[str, Any]) -> bool:
    """Write one seam file so a reader in another process never sees it half-written."""
    try:
        return bool(_CONFIG.write_json_atomic(get_config(), name, payload))
    except Exception:
        return False


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    """Parse a seam file, or None for missing, unreadable or mid-write garbage."""
    try:
        if path.parent != _state_dir():
            return None
        return _CONFIG.read_json(get_config(), path.name)
    except Exception:
        return None


def _read_text(path: Path, limit: int = 2_000_000) -> Optional[str]:
    """File contents, or None for anything that is not a readable file."""
    try:
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except (OSError, ValueError):
        return None


def _mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _newest_mtime(folder: Path, cap: int = 4000) -> Optional[float]:
    """Newest mtime anywhere under *folder*, bounded so a huge mirror cannot stall a request."""
    newest = _mtime(folder)
    seen = 0
    try:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files:
                if name.startswith("."):
                    continue
                seen += 1
                ts = _mtime(Path(root) / name)
                if ts is not None and (newest is None or ts > newest):
                    newest = ts
                if seen >= cap:
                    return newest
    except OSError:
        return newest
    return newest


# -- /state readers ---------------------------------------------------------


def _read_lever(vault: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """The ONE lever: frontmatter key first, the ``## Current ONE Lever`` section second."""
    del vault
    path = _source_path("lever")
    text = _read_text(path)
    if text is None:
        return None, f"not found: {path}"

    scope = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            scope = text[:end]
    match = re.search(r"^pm_current_one_lever:\s*(.+)$", scope, re.M)
    value = match.group(1).strip().strip('"').strip("'").strip() if match else ""

    if not value:
        section = re.search(r"^##\s+Current ONE Lever\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if section:
            for line in section.group(1).splitlines():
                clean = line.strip().lstrip("->*").strip()
                if clean and not clean.startswith("#") and not clean.startswith("["):
                    value = clean
                    break

    if not value:
        return None, f"no ONE lever found in {path}"
    ts = _mtime(path)
    return {
        "text": value[:400],
        "source": str(path),
        "updatedAt": _iso(ts) if ts else None,
    }, None


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "brain"


def _read_brains(vault: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Configured brain mirrors, each with a capped recursive newest-file stamp."""
    del vault
    config = get_config()
    note: Optional[str] = None
    brains: List[Dict[str, Any]] = []
    for brain in config.brains:
        entry: Dict[str, Any] = {"id": brain.id, "label": brain.label, "mirror_updated": None, "mirror": None}
        if brain.path.is_dir():
            ts = _newest_mtime(brain.path)
            entry["mirror"] = str(brain.path)
            entry["mirror_updated"] = _iso(ts) if ts else None
        else:
            entry["note"] = f"not found: {brain.path}"
        brains.append(entry)
    return brains, note


def _read_scoreboard() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Agent's scoreboard: first heading, then the first two lines of substance."""
    path = _scoreboard_path()
    text = _read_text(path, limit=200_000)
    if text is None:
        return None, f"not found: {path}"

    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1:]
                break

    headline = ""
    start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            headline = stripped.lstrip("#").strip()
            start = index + 1
            break
        if stripped and not headline:
            headline = stripped
            start = index + 1
            break

    body: List[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            body.append(stripped[:200])
        if len(body) == 2:
            break

    if not headline and not body:
        return None, f"empty: {path}"
    ts = _mtime(path)
    return {
        "headline": headline[:200],
        "lines": body,
        "source": str(path),
        "updatedAt": _iso(ts) if ts else None,
    }, None


def _read_log(vault: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Newest dated bullet of the agent operations LOG (the file is append-only)."""
    del vault
    path = _source_path("log")
    text = _read_text(path)
    if text is None:
        return None, f"not found: {path}"
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if re.match(r"^- 20\d\d-", stripped):
            ts = _mtime(path)
            return {
                "text": stripped[:500],
                "source": str(path),
                "updatedAt": _iso(ts) if ts else None,
            }, None
    return None, f"no dated entry in {path}"


def _parse_follow_up(raw: str) -> Optional[datetime]:
    """Agent's follow-up stamp as an aware datetime, or None when it is not one.

    No offset means the selected member timezone. A bare date means "some time that
    day", so it counts as due at the end of that day: a row due today must not read as
    overdue at 00:01. Anything unparseable returns None, and the caller keeps the raw
    text and says the row is not overdue rather than guessing.
    """
    match = _AGENT_STAMP_RE.match(raw.strip())
    if not match:
        return None
    year, month, day, hour, minute, second, offset = match.groups()
    try:
        if hour is None:
            moment = datetime(int(year), int(month), int(day), 23, 59, 59)
        else:
            moment = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second or 0))
    except ValueError:
        return None
    if not offset:
        return moment.replace(tzinfo=_zone())
    if offset.upper() == "Z":
        return moment.replace(tzinfo=timezone.utc)
    digits = offset[1:].replace(":", "")
    try:
        delta = timedelta(hours=int(digits[:2]), minutes=int(digits[2:4] or 0))
        zone = timezone(-delta if offset[0] == "-" else delta)
    except ValueError:
        return None
    return moment.replace(tzinfo=zone)


def _parse_agent_row(body: str, now: datetime) -> Optional[Dict[str, Any]]:
    """One ``## In flight`` bullet as a row, or None when there is nothing in it.

    Tolerant on purpose. The id is optional; a missing field is ``null``; extra pipes
    inside the prose do not shift the meaning, because the row is read from BOTH ends:
    the ``next:`` marker opens the tail, and the last three fields of that tail are owner,
    follow_up_at and last update. Everything between them is the next action, pipes and
    all. A row that ran out mid-line (Agent truncates at 220 chars) simply has fewer
    fields, and they fill from the left.
    """
    stripped = body.strip()
    if not stripped:
        return None

    row_id: Optional[str] = None
    match = _AGENT_ID_RE.match(stripped)
    if match:
        row_id = match.group(1).strip() or None
        stripped = match.group(2).strip()

    parts = [part.strip() for part in stripped.split("|")]
    head: Optional[int] = None
    for index in range(1, len(parts)):
        if _AGENT_NEXT_RE.match(parts[index]):
            head = index
            break

    if head is None:
        where = parts[0]
        tail = parts[1:]
    else:
        where = " | ".join(part for part in parts[:head] if part)
        tail = parts[head:]
        tail[0] = _AGENT_NEXT_RE.match(tail[0]).group(1).strip()  # type: ignore[union-attr]

    owner_raw = follow_raw = updated_raw = ""
    if len(tail) >= 4:
        next_raw = " | ".join(part for part in tail[:-3] if part)
        owner_raw, follow_raw, updated_raw = tail[-3], tail[-2], tail[-1]
    elif len(tail) == 3:
        next_raw, owner_raw, follow_raw = tail
    elif len(tail) == 2:
        next_raw, owner_raw = tail
    elif tail:
        next_raw = tail[0]
    else:
        next_raw = ""

    where_text = where.strip()[:_AGENT_FIELD_MAX] or None
    next_text = next_raw.strip()[:_AGENT_FIELD_MAX] or None
    owner = owner_raw.strip()[:_AGENT_FIELD_MAX] or None
    follow_up = follow_raw.strip()[:_AGENT_FIELD_MAX] or None
    updated = updated_raw.strip()[:_AGENT_FIELD_MAX] or None
    if row_id is None and not any((where_text, next_text, owner, follow_up, updated)):
        return None

    due = _parse_follow_up(follow_up) if follow_up else None
    owner_label = get_config().owner_label.casefold()
    waiting = bool(owner and owner_label in owner.casefold()) or bool(
        next_text and owner_label in next_text.casefold())
    return {
        "id": row_id,
        "where": where_text,
        "next": next_text,
        "owner": owner,
        # Kept verbatim, parsed or not: a stamp this file cannot read is still what Agent wrote.
        "follow_up_at": follow_up,
        "updated": updated,
        "waiting_on_owner": waiting,
        "overdue": bool(due is not None and due < now),
    }


def _read_agent_state() -> Dict[str, Any]:
    """Agent's in-flight rows (SPEC §7.5). Read-only, size-capped, never written back.

    Rows live under ``## In flight``. Rows under a ``## Recently closed ...`` heading are a
    different shape and only ever count into ``closed_count``. Prose between the title and
    the first heading, blank lines and nested sub-bullets are skipped. A missing or
    unreadable file is ``rows: []`` plus a plain note, like every other reading here.
    """
    path = _agent_state_path()
    payload: Dict[str, Any] = {
        "rows": [],
        "closed_count": 0,
        "source": str(path),
        "updatedAt": None,
        "note": None,
    }
    text = _read_text(path, limit=_AGENT_STATE_MAX_CHARS)
    if text is None:
        payload["note"] = f"not found: {path}"
        return payload

    ts = _mtime(path)
    payload["updatedAt"] = int(ts * 1000) if ts else None

    if len(text) >= _AGENT_STATE_MAX_CHARS:
        cut = text.rfind("\n")
        text = text[:cut] if cut > 0 else ""
        payload["note"] = f"long file: read the first {_AGENT_STATE_MAX_CHARS // 1024} KB only"

    now = datetime.now(timezone.utc)
    section: Optional[str] = None
    rows: List[Dict[str, Any]] = []
    closed = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if _AGENT_IN_FLIGHT_RE.match(stripped):
                section = "flight"
            elif _AGENT_CLOSED_RE.match(stripped):
                section = "closed"
            else:
                section = None
            continue
        if section is None:
            continue
        bullet = _AGENT_BULLET_RE.match(line)
        if bullet is None:
            continue
        if section == "closed":
            closed += 1
            continue
        row = _parse_agent_row(bullet.group(1), now)
        if row is not None:
            rows.append(row)

    payload["rows"] = rows
    payload["closed_count"] = closed
    return payload


# -- /state · the v3 readings (SPEC §8.3) -----------------------------------
#
# Six more things Member can read off the glass without asking Agent: the plain-words
# brief behind each STATE row, the background helpers Agent spawned, his next meeting,
# today's contract, what ran overnight and what the models cost today.
#
# Four laws hold for every one of them, and the helpers in this section are what enforce
# them:
#
# 1. **Read-only.** Files are opened for reading and capped; Agent's ``state.db`` is
#    opened through a ``file:…?mode=ro`` URI with a short busy timeout and closed before
#    the reader returns, so no lock is ever held across a request.
# 2. **Nothing raises out of ``/state``.** Each reader runs inside
#    :func:`_cached_reading`, which owns the try/except and the cache entry. A reader
#    that throws serves its own last good value marked ``stale`` — or a plain
#    ``unreachable`` block — and leaves the other five untouched.
# 3. **Nothing blocks ``/state``.** The five local readings are file and small-table
#    reads. The calendar is a network call (measured at ~3 s live), so it refreshes on a
#    background thread and the request is answered from cache, always inside ~1 s.
# 4. **Nothing is invented.** A missing source is ``missing``, an unreadable one is
#    ``unreachable``, an old one is ``stale``, and the reason is in ``note``.


def _briefs_path() -> Path:
    return _source_path("agent_state", "briefs_path")


def _agent_db_path(source_id: str = "agent_helpers") -> Path:
    return _source_path(source_id)


def _jobs_path() -> Path:
    return _source_path("overnight_jobs")


def _today_path() -> Path:
    return _source_path("today_plan")


def _one_thing_scoreboard_path() -> Path:
    # This is distinct from the agent scoreboard source, with a different shape.
    return _source_path("one_thing_scoreboard")


def _calendar_mtw_path() -> Path:
    return _source_path("next_meeting", "service_account_path")


def _short_path(path: Any) -> str:
    """``/home/member/.hermes/…`` as ``~/.hermes/…`` — a source a person can read."""
    text = str(path)
    home = str(Path.home())
    return "~" + text[len(home):] if home and text.startswith(home) else text


def _now_s() -> float:
    """The wall clock, in seconds, as ONE seam.

    SPEC §8 amendments B2/C4: a window or a backoff is never tested against the real
    clock. Readers that measure one call this instead of ``time.time()`` directly, so a
    test can pin it here rather than patching ``datetime`` or ``time`` globally.
    """
    return time.time()


def _iso_local(ts: Optional[float]) -> Optional[str]:
    """A stamp in the selected member timezone with its offset on it (SPEC §8.3: "ISO, LOCAL offset")."""
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts, _zone()).isoformat(timespec="seconds")
    except (OSError, OverflowError, ValueError):
        return None


def _local_now() -> datetime:
    return datetime.now(_zone())


def _local_day_start(day_offset: int = 0, now: Optional[datetime] = None) -> datetime:
    """Midnight in the selected member timezone, *now* plus *day_offset* days (SPEC §8 amendment B.2).

    ``now`` is the seam the time-window tests pin: every window in this module is
    measured from the moment it is handed instead of from a wall clock nobody can
    hold still, so a test reads the same at 00:30 as it does at 20:59.
    """
    moment = (now or _local_now()) + timedelta(days=day_offset)
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_iso(raw: Any) -> Optional[datetime]:
    """Any stamp Hermes writes, as an aware datetime, or None.

    Covers the two shapes on disk — ``2026-09-19T22:15:03.123456+08:00`` from the cron
    file and epoch seconds from ``state.db`` — plus the bare and ``Z`` forms Agent's
    STATE.md uses. A stamp with no offset uses the selected member timezone.
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(float(raw), timezone.utc).astimezone(_zone())
        except (OSError, OverflowError, ValueError):
            return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return moment if moment.tzinfo else moment.replace(tzinfo=_zone())
    except ValueError:
        return _parse_follow_up(text)


# -- text hygiene (the same stripper the glass uses) ------------------------
#
# A straight port of ``src/30-data.js`` (``JARVIS_SECRET_*`` / ``jarvisSafeText``), which
# is the repo's stripper: same word list, same three passes, same ``•••``. Anything that
# looks like a credential is replaced before a goal, a summary or a job error is put on
# the wire — those strings come from prompts and shell output, so they can carry one.

_SECRET_WORD = r"(?:api[_.-]?key|key|token|secret|password|passwd|pwd|bearer|authorization|credential|cookie)"
_SECRET_SCHEME_RE = re.compile(r"\b(bearer|basic)\s+([^\s\"']+)", re.I)
_SECRET_FLAG_RE = re.compile(
    r"(--?[A-Za-z0-9_.-]*" + _SECRET_WORD + r"[A-Za-z0-9_.-]*)([\s:=]+)([\"']?)([^\s\"'&]+)\3", re.I)
_SECRET_PAIR_RE = re.compile(
    r"\b([A-Za-z0-9_.-]*" + _SECRET_WORD + r"[A-Za-z0-9_.-]*\s*[:=]\s*)([\"']?)([^\s\"'&]+)\2", re.I)
_SECRET_RUN_RE = re.compile(r"•••(?:[\s:=]+•••)+")

#: Markdown a goal or a summary arrives wrapped in. Stripped so the glass shows words.
_MD_LINK_RE = re.compile(r"\[([^\]]{1,120})\]\(([^)\s]{1,400})\)")
_MD_LEAD_RE = re.compile(r"^\s{0,3}(?:[-*+]\s+|#{1,6}\s+|>\s?|\d{1,2}[.)]\s+)")
_MD_MARK_RE = re.compile(r"(\*\*|__|`{1,3}|~~)")


def _strip_secrets(text: str) -> str:
    text = _SECRET_SCHEME_RE.sub(lambda m: m.group(1) + " •••", text)
    text = _SECRET_FLAG_RE.sub(
        lambda m: m.group(1) + ("=" if "=" in m.group(2) else " ") + m.group(3) + "•••" + m.group(3),
        text)
    text = _SECRET_PAIR_RE.sub(lambda m: m.group(1) + m.group(2) + "•••" + m.group(2), text)
    return _SECRET_RUN_RE.sub("•••", text)


def _clip(text: str, cap: int) -> str:
    if not cap or len(text) <= cap:
        return text
    return text[:max(1, cap - 1)] + "…"


def _first_line(text: Any) -> str:
    """The first line with something on it — a summary is a paragraph, the glass is a row."""
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _plain(text: Any, cap: int = 0, first_line: bool = False) -> str:
    """Plain words: one line, no markdown, no credential, cut to *cap*."""
    raw = _first_line(text) if first_line else str(text or "")
    raw = _MD_LINK_RE.sub(lambda m: m.group(1), raw)
    raw = _MD_LEAD_RE.sub("", raw)
    raw = _MD_MARK_RE.sub("", raw)
    raw = " ".join(raw.split())
    if not raw:
        return ""
    return _clip(_strip_secrets(raw), cap)


# -- block scaffolding + the per-reader cache ------------------------------


def _block(status: str, source: str, note: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
    """Every v3 reading on the wire: its own ``status``, ``updatedAt``, ``source``, ``note``."""
    payload: Dict[str, Any] = dict(fields)
    payload["status"] = status
    payload["updatedAt"] = _iso_local(time.time())
    payload["source"] = source
    payload["note"] = note
    return payload


def _stale(value: Dict[str, Any], note: str, status: str = "unreachable") -> Dict[str, Any]:
    """The last good value, honestly labelled: same numbers, new status, ``stale: True``."""
    copy = dict(value)
    copy["status"] = status
    copy["stale"] = True
    copy["note"] = note
    return copy


def _cached_reading(name: str, ttl: float, key: str, source: str,
                    build: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    """Run one reader behind its own cache, its own try/except and its own clock.

    This is the rule from SPEC §8.3 in one function: a reader that raises never reaches
    the route, and never empties the block either — the last good value comes back marked
    ``stale`` with the reason in ``note``. With nothing cached yet, the answer is a plain
    ``unreachable`` block. The other five readings are not affected either way.
    """
    entry = JARVIS_STATE.readings.setdefault(name, _Reading())
    now = time.time()
    if entry.value is not None and entry.key == key and now - entry.at < ttl:
        return entry.value
    try:
        value = build()
    except Exception as exc:  # noqa: BLE001 - a reader must never break /state
        note = f"could not be read: {type(exc).__name__}"
        if entry.value is not None and entry.key == key:
            return _stale(entry.value, note)
        return _block("unreachable", source, note)
    entry.value, entry.at, entry.key, entry.error = value, now, key, None
    return value


# -- 8.3.1 · the plain-words briefs behind Agent's STATE rows ----------------

#: ``## [row-id] Plain title`` — the id is what matches a brief to a STATE row.
_BRIEF_HEAD_RE = re.compile(r"^#{1,6}\s*\[([^\]]{1,80})\]\s*(.*)$")
#: ``- what: …`` — one known key per bullet; anything else is ignored, not an error.
_BRIEF_FIELD_RE = re.compile(r"^[-*+]\s*([A-Za-z][A-Za-z _-]{0,20})\s*:\s*(.*)$")
_BRIEF_KEYS = ("what", "why", "do", "takes", "where", "updated")
_BRIEF_FIELD_MAX = 400


def _parse_briefs(text: str) -> Dict[str, Dict[str, Any]]:
    """Agent's WAITING-ON-OWNER.md as ``{row id: brief}``. Tolerant on purpose.

    Unknown bullets are skipped, a brief with no bullets is still a title, a heading with
    no ``[id]`` cannot be matched to a row so it is dropped, and a repeated id keeps the
    first one. Nothing here can raise on a file written in a hurry.
    """
    briefs: Dict[str, Dict[str, Any]] = {}
    current: Optional[Dict[str, Any]] = None
    for line in text.splitlines():
        head = _BRIEF_HEAD_RE.match(line.strip())
        if head:
            row_id = head.group(1).strip()
            current = None
            if row_id and row_id not in briefs:
                current = {"title": _plain(head.group(2), _BRIEF_FIELD_MAX) or None}
                current.update({key: None for key in _BRIEF_KEYS})
                briefs[row_id] = current
            continue
        if current is None:
            continue
        field_match = _BRIEF_FIELD_RE.match(line.strip())
        if not field_match:
            continue
        key = field_match.group(1).strip().lower().replace(" ", "").replace("-", "")
        if key in _BRIEF_KEYS and current.get(key) is None:
            current[key] = _plain(field_match.group(2), _BRIEF_FIELD_MAX) or None
    return briefs


def _read_briefs() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """The briefs file, as a map and as its own ``agent_state.briefs`` block."""
    path = _briefs_path()
    source = _short_path(path)
    if not path.exists():
        return {}, _block("missing", source, f"not found: {source}", count=0, matched=0)
    text = _read_text(path, limit=_BRIEFS_MAX_CHARS)
    if text is None:
        return {}, _block("unreachable", source, f"unreadable: {source}", count=0, matched=0)
    note = None
    if len(text) >= _BRIEFS_MAX_CHARS:
        cut = text.rfind("\n")
        text = text[:cut] if cut > 0 else ""
        note = f"long file: read the first {_BRIEFS_MAX_CHARS // 1024} KB only"
    briefs = _parse_briefs(text)
    block = _block("ok", source, note, count=len(briefs), matched=0)
    block["fileUpdatedAt"] = _iso_local(_mtime(path))
    return briefs, block


def _attach_briefs(agent_state: Dict[str, Any]) -> None:
    """Hang each row's brief off the row, and the block off ``agent_state`` (SPEC §8.3.1).

    Additive: every existing key of ``agent_state`` and of every row keeps its shape. A row
    with no brief keeps ``brief: null`` — the glass says "ask Agent", it never invents one.
    """
    spec = _source_spec("agent_state") or {}
    if "briefs_path" not in spec:
        for row in agent_state.get("rows", []):
            row["brief"] = None
        agent_state["briefs"] = _block(
            "unconfigured", "agent_state.briefs_path", "briefs_path is not configured",
            count=None, matched=None)
        return
    try:
        briefs, block = _cached_briefs()
    except Exception as exc:  # noqa: BLE001 - the rows must survive a bad briefs file
        briefs, block = {}, _block(
            "unreachable", _short_path(_briefs_path()),
            f"could not be read: {type(exc).__name__}", count=0, matched=0)
    matched = 0
    for row in agent_state.get("rows", []):
        brief = briefs.get(row.get("id") or "")
        row["brief"] = dict(brief) if brief else None
        if brief:
            matched += 1
    block = dict(block)
    block["matched"] = matched
    agent_state["briefs"] = block


def _cached_briefs() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """``_read_briefs`` behind the same per-reader cache, holding both halves."""
    name, key = "briefs", str(_briefs_path())
    entry = JARVIS_STATE.readings.setdefault(name, _Reading())
    now = time.time()
    if entry.value is not None and entry.key == key and now - entry.at < _BRIEFS_CACHE_S:
        return entry.value["briefs"], entry.value["block"]
    briefs, block = _read_briefs()
    entry.value, entry.at, entry.key = {"briefs": briefs, "block": block}, now, key
    return briefs, block


# -- 8.3.2 · Agent's background helpers --------------------------------------


def _db_uri(path: Path) -> str:
    """``file:…?mode=ro`` — the only way this module ever opens Agent's database."""
    return path.resolve().as_uri() + "?mode=ro"


def _read_only_rows(path: Path, sql: str, params: Tuple[Any, ...]) -> List[Tuple[Any, ...]]:
    """One bounded query against Agent's ``state.db``, read-only, connection closed.

    ``mode=ro`` refuses every write at the SQLite level, ``PRAGMA query_only`` refuses it
    again, the busy timeout is 2 s so a writer can never park a request, and the
    connection is closed in ``finally`` — no lock is held across the request.
    """
    connection = sqlite3.connect(_db_uri(path), uri=True, timeout=_DB_BUSY_S)
    try:
        connection.execute("PRAGMA query_only = 1")
        return connection.execute(sql, params).fetchall()
    finally:
        connection.close()


def _json_or_empty(raw: Any) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _helper_origin(origin_session: Any) -> str:
    """Where the helper was asked for, in Member's words, from ``origin_session``.

    The live shapes are ``agent:main:telegram:…``, ``agent:main:whatsapp:…`` and a bare
    session id (a chat in the dashboard). Nothing in the row says whether that chat was
    spoken or typed, so a dashboard chat is called ``chat`` unless the id itself says
    voice — Jarvis does not guess that a call was running.
    """
    text = str(origin_session or "").lower()
    if not text:
        return "unknown"
    if "voice" in text:
        return "voice chat"
    if "telegram" in text:
        return "telegram"
    if "whatsapp" in text:
        return "whatsapp"
    if "cron" in text or "schedule" in text:
        return "cron"
    return "chat"


def _helper_summary(result: Dict[str, Any]) -> Optional[str]:
    """The first line of what the helper reported back, plain and capped."""
    results = result.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        text = results[0].get("summary") or results[0].get("error") or ""
    else:
        text = result.get("summary") or result.get("error") or ""
    return _plain(text, _SUMMARY_MAX, first_line=True) or None


def _read_agent_helpers(now: Optional[datetime] = None) -> Dict[str, Any]:
    """``async_delegations``: what Agent has running, and what came back today (SPEC §8.3.2).

    A background helper never reaches the window as a ``subagent.*`` event, which is why
    the v2 NOW box could not show one. This is where they actually live.
    """
    path = _agent_db_path()
    source = f"{_short_path(path)} · async_delegations"
    if not path.is_file():
        return _block("missing", source, f"not found: {_short_path(path)}",
                      running=[], recent=[], runningCount=0, todayCount=0)

    moment = now or _local_now()
    now = moment.timestamp()
    rows = _read_only_rows(
        path,
        "SELECT delegation_id, origin_session, state, dispatched_at, completed_at,"
        " updated_at, task_json, event_json, result_json, delivery_state"
        " FROM async_delegations"
        " WHERE COALESCE(completed_at, updated_at, dispatched_at, 0) >= ?"
        " ORDER BY COALESCE(completed_at, updated_at, dispatched_at, 0) DESC"
        " LIMIT ?",
        (now - _HELPER_RECENT_S, _DB_ROW_CAP),
    )

    day_start = _local_day_start(now=moment).timestamp()
    running: List[Dict[str, Any]] = []
    recent: List[Dict[str, Any]] = []
    today_count = 0
    for (identifier, origin_session, state, dispatched_at, completed_at, updated_at,
         task_json, event_json, result_json, delivery_state) in rows:
        task = _json_or_empty(task_json) or _json_or_empty(event_json)
        started = float(dispatched_at or 0)
        ended = float(completed_at or 0)
        touched = float(updated_at or 0) or ended or started
        if started and started >= day_start:
            today_count += 1
        goal = _plain(task.get("goal"), _GOAL_MAX, first_line=True) or None
        entry_id = str(identifier or "")[:80]
        finished = bool(ended) or str(state or "").lower() in (
            "completed", "complete", "error", "failed", "cancelled", "canceled", "timeout")
        if not finished:
            if now - touched > _HELPER_RUNNING_S:
                continue  # touched too long ago to call it running; nothing is guessed
            running.append({
                "id": entry_id,
                "goal": goal,
                "model": _plain(task.get("model"), 60) or None,
                "startedAt": _iso_local(started),
                "seconds": int(max(0.0, now - started)) if started else None,
                "origin": _helper_origin(origin_session),
            })
            continue
        if len(recent) >= _HELPER_RECENT_MAX:
            continue
        recent.append({
            "id": entry_id,
            "goal": goal,
            "state": _plain(state, 40) or "unknown",
            "startedAt": _iso_local(started),
            "endedAt": _iso_local(ended),
            "seconds": int(max(0.0, ended - started)) if (started and ended) else None,
            "summary": _helper_summary(_json_or_empty(result_json)),
            "delivered": str(delivery_state or "").lower() == "delivered",
            "origin": _helper_origin(origin_session),
        })

    running.sort(key=lambda item: item.get("startedAt") or "", reverse=True)
    return _block("ok", source, None, running=running, recent=recent,
                  runningCount=len(running), todayCount=today_count)


def _agent_helpers_block(now: Optional[datetime] = None) -> Dict[str, Any]:
    return _cached_reading("agent_helpers", _HELPERS_CACHE_S, str(_agent_db_path()),
                           f"{_short_path(_agent_db_path())} · async_delegations",
                           lambda: _read_agent_helpers(now))


# -- 8.3.3 · the next meeting (Google Calendar, read only) ------------------


def _calendar_source() -> str:
    return "Google Calendar (service account, read only)"


def _calendar_interpreters() -> List[str]:
    """Which Python runs the helper: the dashboard's own first, then the ladder."""
    spec = _source_spec("next_meeting") or {}
    return [str(spec.get("python_path") or sys.executable)]


def _calendar_fetch() -> Dict[str, Any]:
    """Run ``dashboard/jarvis_calendar.py`` and return its JSON, or raise.

    Never on the request path: this is the one reading that goes to the network (measured
    at about 3 s live), and it runs in a subprocess so a missing Google client cannot
    unmount the plugin and an 8 s wall clock can actually stop it.
    """
    if not _CALENDAR_HELPER.is_file():
        raise FileNotFoundError("jarvis_calendar.py is not in the dashboard folder")
    config = get_config()
    spec = config.sources["next_meeting"]
    last = "no interpreter could run the calendar helper"
    for interpreter in _calendar_interpreters():
        try:
            done = subprocess.run(  # noqa: S603 - our own file, our own interpreter list
                [interpreter, str(_CALENDAR_HELPER),
                 "--service-account", str(spec["service_account_path"]),
                 "--timezone", config.timezone,
                 "--hours", str(spec.get("hours", _CALENDAR_WINDOW_H))],
                capture_output=True, text=True, timeout=_CALENDAR_TIMEOUT_S,
                cwd=str(_DASHBOARD_DIR))
        except (OSError, subprocess.SubprocessError) as exc:
            last = f"{type(exc).__name__} running the calendar helper"
            continue
        payload = _json_or_empty(done.stdout.strip() or "{}")
        if done.returncode == 0 and isinstance(payload.get("events"), list):
            return payload
        last = _plain(payload.get("error") or f"helper exit {done.returncode}", 160) or "helper failed"
        if done.returncode != 3:
            break  # only a missing Google client is worth another interpreter
    raise RuntimeError(last)


def _calendar_block_from(payload: Dict[str, Any]) -> Dict[str, Any]:
    """The helper's events as ``next_meeting`` (SPEC §8.3.3)."""
    now = _local_now()
    events: List[Dict[str, Any]] = []
    for raw in payload.get("events") or []:
        if not isinstance(raw, dict):
            continue
        start = _parse_iso(raw.get("start"))
        if start is None:
            continue
        events.append({
            "title": _plain(raw.get("title"), 200) or "(untitled)",
            "start": start.isoformat(timespec="seconds"),
            "end": (_parse_iso(raw.get("end")) or start).isoformat(timespec="seconds"),
            "calendar": _plain(raw.get("calendar"), 120) or None,
            "allDay": bool(raw.get("allDay")),
            "minutesUntil": int((start - now).total_seconds() // 60),
        })
    events.sort(key=lambda item: (item["start"], item["allDay"]))

    # A timed event beats an all-day one for ``next``: "in 42 min" is a countdown, and an
    # all-day block has nothing to count down to.
    timed = [event for event in events if not event["allDay"]]
    ahead = [event for event in timed if event["minutesUntil"] >= 0] or timed
    upcoming = ahead or events
    nxt = upcoming[0] if upcoming else None
    later = [event for event in events if event is not nxt][:_MEETING_LATER]
    note = None if nxt else f"nothing in the next {_CALENDAR_WINDOW_H} h"
    return _block("ok", _calendar_source(), note, next=nxt, later=later,
                  windowHours=_CALENDAR_WINDOW_H)


def _calendar_refresh() -> None:
    """One refresh, on a background thread, never holding up a request."""
    entry = JARVIS_STATE.readings.setdefault("next_meeting", _Reading())
    try:
        block = _calendar_block_from(_calendar_fetch())
        entry.value, entry.at, entry.error = block, _now_s(), None
        entry.key = str(_calendar_mtw_path())
    except Exception as exc:  # noqa: BLE001 - a calendar that will not answer is a note
        entry.error = _plain(str(exc), 160) or type(exc).__name__
        # ``at`` is when this attempt finished either way, which is what both the
        # 5-minute cache and the 5-minute failure backoff below are measured from.
        entry.at = _now_s()
    finally:
        with entry.lock:
            entry.refreshing = False


def _calendar_configured() -> bool:
    """True when there is something to read a calendar with, without asking Google."""
    config = get_config()
    spec = config.sources.get("next_meeting")
    return bool(config.enabled("next_meeting") and spec and spec["service_account_path"].is_file())


def _next_meeting_block() -> Dict[str, Any]:
    """The calendar reading: cached 5 minutes, refreshed off the request path.

    Serve-stale-then-refresh, so ``/state`` never waits for Google: a fresh value is
    returned as it is, an ageing one is returned marked ``stale`` while a thread fetches
    the new one, and a refresh that failed says ``unreachable`` over the last good value.
    """
    source = _calendar_source()
    entry = JARVIS_STATE.readings.setdefault("next_meeting", _Reading())
    if not _calendar_configured():
        return _block("missing", source, "no calendar service account on this machine",
                      next=None, later=[], windowHours=_CALENDAR_WINDOW_H)

    now = _now_s()
    fresh = entry.value is not None and now - entry.at < _CALENDAR_CACHE_S and not entry.error
    if fresh:
        return entry.value

    # SPEC §8 amendments C4 — a FAILED refresh backs off for five minutes. The last
    # good value keeps being served as ``stale`` below, exactly as it was; the only
    # thing that stops is the spawning of another helper subprocess on every poll.
    backing_off = bool(entry.error) and now - entry.at < _CALENDAR_FAIL_BACKOFF_S

    start_refresh = False
    if not backing_off:
        with entry.lock:
            if not entry.refreshing:
                entry.refreshing = True
                start_refresh = True
    if start_refresh:
        try:
            threading.Thread(target=_calendar_refresh, name="jarvis-calendar", daemon=True).start()
        except RuntimeError:  # noqa: PERF203 - no thread available; try again next poll
            with entry.lock:
                entry.refreshing = False

    if entry.value is not None:
        if entry.error:
            return _stale(entry.value, f"calendar could not be read: {entry.error}")
        return _stale(entry.value, "refreshing", status="ok")
    note = f"calendar could not be read: {entry.error}" if entry.error else "first calendar read is running"
    return _block("unreachable", source, note, next=None, later=[],
                  windowHours=_CALENDAR_WINDOW_H)


# -- 8.3.4 · today's contract ----------------------------------------------

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.S)
_FRONT_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.*)$")
_TODAY_HEAD_RE = re.compile(r"^#{1,6}\s*Today\b", re.I)
_PLAN_KINDS = ("build", "content", "momentum")


def _front_matter(text: str) -> Tuple[Dict[str, str], str]:
    """The ``---`` block as flat ``key: value`` pairs, plus the body after it.

    No YAML dependency (the plugin ships none, by law): one key per line, quotes stripped,
    anything nested or multi-line simply does not become a key.
    """
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    values: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t", "#")):
            continue
        pair = _FRONT_KEY_RE.match(line.strip())
        if not pair:
            continue
        raw = pair.group(2).strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        values[pair.group(1).lower()] = raw.strip()
    return values, text[match.end():]


def _today_headline(body: str) -> Optional[str]:
    """The first real sentence under ``## Today`` — the plain-words ONE thing."""
    seen = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if _TODAY_HEAD_RE.match(stripped):
                seen = True
                continue
            if seen:
                break
            continue
        if not seen or not stripped or stripped.startswith(">"):
            continue
        return _plain(stripped, _HEADLINE_MAX) or None
    return None


def _read_today_plan(vault: Path) -> Dict[str, Any]:
    """TODAY.md: the date it was set, and the three contract items (SPEC §8.3.4)."""
    path = _today_path()
    source = _short_path(path)
    config = get_config()
    lever = _read_lever(vault)[0] if config.enabled("lever") and "lever" in config.sources else None
    if not path.exists():
        return _block("missing", source, f"not found: {source}", date=None, isToday=False,
                      headline=None, items=[], lever=lever, fileUpdatedAt=None)
    text = _read_text(path, limit=_TODAY_MAX_CHARS)
    if text is None:
        return _block("unreachable", source, f"unreadable: {source}", date=None, isToday=False,
                      headline=None, items=[], lever=lever, fileUpdatedAt=None)

    front, body = _front_matter(text)
    date = front.get("date") or None
    items: List[Dict[str, Any]] = []
    for kind in _PLAN_KINDS:
        task = _plain(front.get(f"{kind}_task"), 300, first_line=True) or None
        status = _plain(front.get(f"{kind}_status"), 40) or None
        following = _plain(front.get(f"{kind}_next_action"), 300, first_line=True) or None
        if task is None and status is None and following is None:
            continue
        items.append({"kind": kind, "task": task, "status": status, "next": following})

    today = _local_now().strftime("%Y-%m-%d")
    # Reported, never hidden: a card set two days ago still says which day it is for.
    note = None if date == today else (
        f"set {date}, not today" if date else "no date in the front matter")
    return _block("ok", source, note, date=date, isToday=date == today,
                  headline=_today_headline(body), items=items, lever=lever,
                  fileUpdatedAt=_iso_local(_mtime(path)))


def _today_plan_block(vault: Path) -> Dict[str, Any]:
    return _cached_reading("today_plan", _TODAY_CACHE_S, f"{vault}|{_today_path()}",
                           _short_path(_today_path()), lambda: _read_today_plan(vault))


# -- 8.3.5 · what ran overnight ---------------------------------------------


def _read_overnight_jobs(now: Optional[datetime] = None) -> Dict[str, Any]:
    """Agent's cron file since 21:00 yesterday: what ran, what failed, what is next.

    Only enabled jobs are counted — a disabled job that last ran a week ago is not news.
    ``state`` carries the pause, so paused jobs are counted separately.
    """
    path = _jobs_path()
    source = _short_path(path)
    now = now or _local_now()
    window_from = _local_day_start(-1, now=now).replace(hour=21)
    window = {"from": window_from.isoformat(timespec="seconds"),
              "to": now.isoformat(timespec="seconds")}
    empty = {"window": window, "total": 0, "ok": 0, "failed": [], "pausedCount": 0, "nextUp": []}
    unknown = {"window": window, "total": None, "ok": None, "failed": None,
               "pausedCount": None, "nextUp": None}

    if not path.exists():
        return _block("missing", source, f"not found: {source}", **unknown)
    text = _read_text(path, limit=_JOBS_MAX_CHARS)
    if text is None:
        return _block("unreachable", source, f"unreadable: {source}", **unknown)
    try:
        document = json.loads(text)
    except ValueError:
        return _block("unreachable", source, "the cron file is not readable JSON", **unknown)

    jobs = document.get("jobs") if isinstance(document, dict) else document
    if not isinstance(jobs, list):
        return _block("unreachable", source, "the cron file has no job list", **unknown)

    total = ok = paused = 0
    failed: List[Dict[str, Any]] = []
    next_up: List[Tuple[datetime, Dict[str, Any]]] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if str(job.get("state") or "").lower() == "paused":
            paused += 1
        if not job.get("enabled"):
            continue
        last_run = _parse_iso(job.get("last_run_at"))
        if last_run is not None and window_from <= last_run <= now:
            total += 1
            status = str(job.get("last_status") or "").lower()
            if status == "ok":
                ok += 1
            else:
                failed.append({
                    "id": _plain(job.get("id"), 80) or None,
                    "name": _plain(job.get("name"), 120) or None,
                    "lastRunAt": last_run.isoformat(timespec="seconds"),
                    "lastStatus": status or "unknown",
                    "error": _plain(job.get("last_error"), _JOB_ERROR_MAX, first_line=True) or None,
                })
        upcoming = _parse_iso(job.get("next_run_at"))
        if upcoming is not None and upcoming >= now:
            next_up.append((upcoming, {
                "name": _plain(job.get("name"), 120) or None,
                "nextRunAt": upcoming.isoformat(timespec="seconds"),
            }))

    next_up.sort(key=lambda pair: pair[0])
    failed.sort(key=lambda item: item["lastRunAt"], reverse=True)
    return _block("ok", source, None, window=window, total=total, ok=ok, failed=failed,
                  pausedCount=paused, nextUp=[entry for _, entry in next_up[:_JOBS_NEXT_UP]])


def _overnight_jobs_block(now: Optional[datetime] = None) -> Dict[str, Any]:
    return _cached_reading("overnight_jobs", _JOBS_CACHE_S, str(_jobs_path()),
                           _short_path(_jobs_path()),
                           lambda: _read_overnight_jobs(now))


# -- 8.3.6 · the streak scoreboard ------------------------------------------

#: ``- 2026-07-26 · build ✅ · content ❌ · one-line note`` (the file's own format line).
_SCORE_DAY_RE = re.compile(r"^[-*+]\s*(\d{4}-\d{2}-\d{2})\s*(?:·|\|)?\s*(.*)$")
_SCORE_NUMBER_KEYS = {
    "buildStreak": "build_streak",
    "contentStreak": "content_streak",
    "bestBuildStreak": "best_build_streak",
    "lessonsShipped": "lessons_shipped_since_start",
}


def _mark(segment: str) -> Optional[bool]:
    """A day's tick: ✅ true, ❌ false, anything else unknown — never guessed."""
    if "✅" in segment or "✔" in segment:
        return True
    if "❌" in segment or "✗" in segment or "❎" in segment:
        return False
    return None


def _score_int(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    match = re.search(r"-?\d+", raw)
    return int(match.group(0)) if match else None


def _read_one_thing_scoreboard(vault: Path) -> Dict[str, Any]:
    """The streaks file: the four numbers, the last 7 dated days, and how old it is."""
    path = _one_thing_scoreboard_path()
    source = _short_path(path)
    empty: Dict[str, Any] = {
        "buildStreak": None, "contentStreak": None, "bestBuildStreak": None,
        "lessonsShipped": None, "lastDays": [], "fileUpdatedAt": None, "staleDays": None,
    }
    if not path.exists():
        return _block("missing", source, f"not found: {source}", **empty)
    text = _read_text(path, limit=_TODAY_MAX_CHARS)
    if text is None:
        return _block("unreachable", source, f"unreadable: {source}", **empty)

    front, body = _front_matter(text)
    numbers = {name: _score_int(front.get(key)) for name, key in _SCORE_NUMBER_KEYS.items()}

    days: List[Dict[str, Any]] = []
    for line in body.splitlines():
        day = _SCORE_DAY_RE.match(line.strip())
        if not day:
            continue
        parts = [part.strip() for part in day.group(2).split("·")]
        build = content = None
        note_parts: List[str] = []
        for part in parts:
            lowered = part.lower()
            if lowered.startswith("build"):
                build = _mark(part)
            elif lowered.startswith("content"):
                content = _mark(part)
            elif part:
                note_parts.append(part)
        days.append({
            "date": day.group(1),
            "build": build,
            "content": content,
            "note": _plain(" · ".join(note_parts), 160) or None,
        })

    days.sort(key=lambda item: item["date"], reverse=True)
    last_days = days[:_SCOREBOARD_DAYS]
    mtime = _mtime(path)
    newest = _parse_iso(last_days[0]["date"]) if last_days else _parse_iso(mtime)
    stale_days = None
    if newest is not None:
        stale_days = max(0, (_local_day_start() - newest.astimezone(_zone()).replace(
            hour=0, minute=0, second=0, microsecond=0)).days)

    status = "ok"
    note = None
    if stale_days is None:
        status, note = "stale", "no dated line and no file date to go by"
    elif stale_days > _SCOREBOARD_STALE_DAYS:
        status = "stale"
        note = (f"no dated line since {last_days[0]['date']}" if last_days
                else f"the file itself is {stale_days} days old")
    return _block(status, source, note, lastDays=last_days,
                  fileUpdatedAt=_iso_local(mtime), staleDays=stale_days, **numbers)


def _one_thing_scoreboard_block(vault: Path) -> Dict[str, Any]:
    return _cached_reading(
        "one_thing_scoreboard", _ONE_THING_CACHE_S, f"{vault}|{_one_thing_scoreboard_path()}",
        _short_path(_one_thing_scoreboard_path()), lambda: _read_one_thing_scoreboard(vault))


# -- 8.3.7 · what the models cost today -------------------------------------

#: A cost this table does not actually know. Never printed as a dollar figure.
_COST_UNKNOWN = ("", "unknown", "none", "unavailable")


def _read_spend(now: Optional[datetime] = None) -> Dict[str, Any]:
    """``session_model_usage`` for today in the selected member timezone, grouped by model (SPEC §8.3.7).

    ``costKnown`` is false — and every dollar figure null — whenever the table's own cost
    columns are zero or its ``cost_status`` says unknown. A made-up number on this box
    would be worse than no number.
    """
    path = _agent_db_path("spend")
    source = f"{_short_path(path)} · session_model_usage"
    empty = {"today": {"byModel": [], "totalCalls": 0, "totalTokens": 0,
                       "costUsd": None, "costKnown": False}}
    if not path.is_file():
        return _block("missing", source, f"not found: {_short_path(path)}", **empty)

    day_start = _local_day_start(now=now).timestamp()
    day_end = _local_day_start(1, now=now).timestamp()
    rows = _read_only_rows(
        path,
        "SELECT model, api_call_count, input_tokens, output_tokens, cache_read_tokens,"
        " estimated_cost_usd, actual_cost_usd, cost_status"
        " FROM session_model_usage WHERE last_seen >= ? AND last_seen < ? LIMIT ?",
        (day_start, day_end, _USAGE_ROW_CAP),
    )

    by_model: Dict[str, Dict[str, Any]] = {}
    for (model, calls, input_tokens, output_tokens, cache_read, estimated, actual, cost_status) in rows:
        name = _plain(model, 60) or "unknown"
        entry = by_model.setdefault(name, {
            "model": name, "calls": 0, "inputTokens": 0, "outputTokens": 0,
            "cacheReadTokens": 0, "costUsd": 0.0, "costKnown": True,
        })
        entry["calls"] += int(calls or 0)
        entry["inputTokens"] += int(input_tokens or 0)
        entry["outputTokens"] += int(output_tokens or 0)
        entry["cacheReadTokens"] += int(cache_read or 0)
        cost = float(actual or 0.0) or float(estimated or 0.0)
        if not cost or str(cost_status or "").strip().lower() in _COST_UNKNOWN:
            entry["costKnown"] = False
        else:
            entry["costUsd"] += cost

    models: List[Dict[str, Any]] = []
    for entry in sorted(by_model.values(), key=lambda item: item["calls"], reverse=True):
        known = entry.pop("costKnown")
        entry["costUsd"] = round(entry["costUsd"], 4) if known and entry["costUsd"] else None
        models.append(entry)

    total_calls = sum(entry["calls"] for entry in models)
    total_tokens = sum(entry["inputTokens"] + entry["outputTokens"] for entry in models)
    costs = [entry["costUsd"] for entry in models]
    cost_known = bool(models) and all(cost is not None for cost in costs)
    note = None if cost_known or not models else "Hermes did not report a cost for today"
    return _block("ok", source, note, today={
        "byModel": models,
        "totalCalls": total_calls,
        "totalTokens": total_tokens,
        "costUsd": round(sum(costs), 4) if cost_known else None,
        "costKnown": cost_known,
    })


def _spend_block(now: Optional[datetime] = None) -> Dict[str, Any]:
    return _cached_reading("spend", _SPEND_CACHE_S, str(_agent_db_path("spend")),
                           f"{_short_path(_agent_db_path('spend'))} · session_model_usage",
                           lambda: _read_spend(now))


def public_settings(config) -> Dict[str, Any]:
    """Display choices only; source paths and credentials never leave this view."""
    settings = {
        "schema_version": config.schema_version,
        "profile_id": config.profile_id,
        "agent_name": config.agent_name,
        "owner_label": config.owner_label,
        "timezone": config.timezone,
        "enabled_sources": sorted(config.enabled_sources),
        "brains": [{"id": brain.id, "label": brain.label} for brain in config.brains],
    }

    if config.enabled_boxes is not None:
        settings["enabled_boxes"] = sorted(config.enabled_boxes)
    return settings


def read_state(force: bool = False) -> Dict[str, Any]:
    """The ``/state`` payload, recomputed at most every 30 s per set of source paths."""
    try:
        config = get_config()
    except Exception as exc:
        return {"config": {"status": "invalid", "note": str(exc)[:240]}, "updatedAt": _now_ms()}
    vault = _vault_root()
    key = (str(config.config_path.stat().st_mtime_ns), repr(sorted(config.enabled_sources)),
           repr(sorted((name, repr(dict(spec))) for name, spec in config.sources.items())),
           repr(tuple((brain.id, brain.label, str(brain.path)) for brain in config.brains)))
    now = time.time()
    cached = JARVIS_STATE.state_cache
    if (not force and cached is not None and JARVIS_STATE.state_cache_key == key
            and now - JARVIS_STATE.state_cache_at < _STATE_CACHE_S):
        return cached

    def available(source_id: str) -> Tuple[bool, str]:
        if not config.enabled(source_id):
            return False, "disabled"
        if source_id == "brains":
            return (bool(config.brains), "unconfigured" if not config.brains else "ok")
        return (source_id in config.sources, "unconfigured" if source_id not in config.sources else "ok")

    lever_ok, lever_reason = available("lever")
    lever, lever_note = _read_lever(vault) if lever_ok else (None, lever_reason)
    brains_ok, brains_reason = available("brains")
    brains, brains_note = _read_brains(vault) if brains_ok else ([], brains_reason)
    scoreboard_ok, scoreboard_reason = available("scoreboard")
    scoreboard, scoreboard_note = _read_scoreboard() if scoreboard_ok else (None, scoreboard_reason)
    log_ok, log_reason = available("log")
    log, log_note = _read_log(vault) if log_ok else (None, log_reason)
    state_ok, state_reason = available("agent_state")
    if state_ok:
        agent_state = _read_agent_state()
        _attach_briefs(agent_state)
    else:
        agent_state = {
            "rows": [], "closed_count": None, "source": None, "updatedAt": None,
            "status": state_reason, "note": state_reason,
            "briefs": _block(state_reason, "agent_state", state_reason, count=None, matched=None),
        }

    def gated(source_id: str, build: Callable[[], Dict[str, Any]], **empty: Any) -> Dict[str, Any]:
        ok, reason = available(source_id)
        return build() if ok else _block(reason, source_id, reason, **empty)

    payload: Dict[str, Any] = {
        "settings": public_settings(config),
        "vault": str(vault),
        "lever": lever,
        "brains": brains,
        "scoreboard": scoreboard,
        "log": log,
        # Agent's own file, not the vault's: it carries its own note and its own mtime, and
        # it stays out of ``notes`` below so the four vault readings keep their shape.
        "agent_state": agent_state,
        # SPEC §8.3 — the six v3 readings. Additive: every key above keeps its shape, and
        # each block below carries its own status, so one broken source dims one box.
        # ``one_thing_scoreboard`` is not ``scoreboard``: that name belongs to Agent's own
        # SCOREBOARD.md from v1, which is a different file. See docs/BACKEND.md.
        "agent_helpers": gated("agent_helpers", _agent_helpers_block,
                               running=None, recent=None, runningCount=None, todayCount=None),
        "next_meeting": gated("next_meeting", _next_meeting_block,
                              next=None, later=None, windowHours=None),
        "today_plan": gated("today_plan", lambda: _today_plan_block(vault),
                            date=None, isToday=None, headline=None, items=None, lever=None,
                            fileUpdatedAt=None),
        "overnight_jobs": gated("overnight_jobs", _overnight_jobs_block,
                                window=None, total=None, ok=None, failed=None,
                                pausedCount=None, nextUp=None),
        "one_thing_scoreboard": gated("one_thing_scoreboard",
                                      lambda: _one_thing_scoreboard_block(vault),
                                      buildStreak=None, contentStreak=None,
                                      bestBuildStreak=None, lessonsShipped=None,
                                      lastDays=None, fileUpdatedAt=None, staleDays=None),
        "spend": gated("spend", _spend_block,
                       today={"byModel": None, "totalCalls": None, "totalTokens": None,
                              "costUsd": None, "costKnown": False}),
        "updatedAt": _now_ms(),
    }
    notes = {
        "lever": lever_note,
        "brains": brains_note,
        "scoreboard": scoreboard_note,
        "log": log_note,
    }
    payload["notes"] = {k: v for k, v in notes.items() if v}
    if lever is None:
        payload["lever_note"] = lever_note
    if scoreboard is None:
        payload["scoreboard_note"] = scoreboard_note
    if log is None:
        payload["log_note"] = log_note

    JARVIS_STATE.state_cache = payload
    JARVIS_STATE.state_cache_key = key
    JARVIS_STATE.state_cache_at = now
    return payload


# -- in-memory presence + panel --------------------------------------------


def _write_presence_file(force: bool = False) -> bool:
    """Mirror the live presence into ``presence.json`` for Agent's tools, at most 1 Hz."""
    now = time.time()
    if not force and now - JARVIS_STATE.presence_file_at < _PRESENCE_FILE_S:
        return False
    JARVIS_STATE.presence_file_at = now
    return _write_json_atomic(_PRESENCE_FILE, {
        "presence": JARVIS_STATE.presence,
        "at": int(JARVIS_STATE.presence_at * 1000) if JARVIS_STATE.presence_at else None,
        "clients": len(JARVIS_STATE.clients),
        "version": JARVIS_STATE.version,
    })


def write_status_file(force: bool = False) -> bool:
    """Mirror the client count into ``status.json``, at most once every 5 s."""
    now = time.time()
    if not force and now - JARVIS_STATE.status_file_at < _STATUS_FILE_S:
        return False
    JARVIS_STATE.status_file_at = now
    return _write_json_atomic(_STATUS_FILE, {
        "clients": len(JARVIS_STATE.clients),
        "version": JARVIS_STATE.version,
        "presence_age_ms": presence_age_ms(),
        "at": _now_ms(),
    })


def store_presence(presence: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the desktop half's presence object verbatim; it owns that contract, not this file."""
    get_config()
    if not isinstance(presence, dict):
        raise ValueError("presence must be a JSON object")
    JARVIS_STATE.presence = dict(presence)
    JARVIS_STATE.presence_at = time.time()
    _write_presence_file()
    return JARVIS_STATE.presence


def presence_age_ms() -> Optional[int]:
    if JARVIS_STATE.presence is None or not JARVIS_STATE.presence_at:
        return None
    return int((time.time() - JARVIS_STATE.presence_at) * 1000)


def read_presence() -> Dict[str, Any]:
    """Last presence + how old it is + how many mirror clients are watching."""
    try:
        config = get_config()
    except Exception as exc:
        return {"presence": None, "age_ms": None, "clients": 0, "version": JARVIS_STATE.version,
                "profile_id": None, "config_note": str(exc)[:240]}
    return {
        "presence": JARVIS_STATE.presence,
        "age_ms": presence_age_ms(),
        "clients": len(JARVIS_STATE.clients),
        "version": JARVIS_STATE.version,
        "profile_id": config.profile_id,
    }


def read_status() -> Dict[str, Any]:
    try:
        config = get_config()
    except Exception as exc:
        return {"ok": False, "version": JARVIS_STATE.version, "profile_id": None,
                "presence_age_ms": None, "clients": 0, "config_note": str(exc)[:240],
                "host_auth": "unproven until installed preflight"}
    return {
        "ok": True,
        "version": JARVIS_STATE.version,
        "profile_id": config.profile_id,
        "settings": public_settings(config),
        "agent_name": config.agent_name,
        "hermes_home": str(config.profile_root),
        "vault": None,
        "presence_age_ms": presence_age_ms(),
        "clients": len(JARVIS_STATE.clients),
    }


def _normalize_panel(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Turn a ``panel.json`` payload into the wire shape, or None if it is not one."""
    if not isinstance(raw, dict):
        return None
    title = str(raw.get("title") or "").strip()[:200]
    body = str(raw.get("body") or "").strip()[:4000]
    if not title and not body:
        return None
    try:
        ttl = int(raw.get("ttl", raw.get("ttl_s", 20)))
    except (TypeError, ValueError):
        ttl = 20
    try:
        at = int(raw.get("at") or 0)
    except (TypeError, ValueError):
        at = 0
    kind = _KIND_RE.sub("-", str(raw.get("kind") or "card").strip().lower()).strip("-")[:24] or "card"
    return {
        "id": str(raw.get("id") or f"panel-{at or _now_ms()}")[:80],
        "title": title,
        "body": body,
        "kind": kind,
        "ttl": max(1, min(ttl, 600)),
        "at": at or _now_ms(),
        "source": "file",
    }


def refresh_file_panel() -> bool:
    """Re-read ``panel.json`` when its mtime moved. True when a NEW panel id appeared."""
    try:
        path = get_config().state_dir / _PANEL_FILE
    except Exception:
        return False
    try:
        mtime = path.stat().st_mtime
    except OSError:
        if JARVIS_STATE.panel_file_mtime is not None:
            JARVIS_STATE.panel_file_mtime = None
            JARVIS_STATE.file_panel = None
            JARVIS_STATE.file_panel_expires_at = 0.0
        return False
    if mtime == JARVIS_STATE.panel_file_mtime:
        return False
    JARVIS_STATE.panel_file_mtime = mtime
    panel = _normalize_panel(_read_json(path) or {})
    if panel is None:
        return False
    previous = JARVIS_STATE.file_panel
    if previous is not None and previous.get("id") == panel["id"]:
        return False
    JARVIS_STATE.file_panel = panel
    # The file's ``at`` is the writer's clock on this same computer; expire from it, so a
    # panel written 30 s ago with a 20 s ttl never flashes up late.
    JARVIS_STATE.file_panel_expires_at = (panel["at"] / 1000.0) + panel["ttl"]
    return True


def current_panel(check_file: bool = True) -> Optional[Dict[str, Any]]:
    """The live panel: newest of the in-memory one and ``panel.json``, ttl honoured."""
    try:
        get_config()
    except Exception:
        return None
    if check_file:
        refresh_file_panel()

    now = time.time()
    memory = JARVIS_STATE.panel
    if memory is not None and JARVIS_STATE.panel_expires_at and now >= JARVIS_STATE.panel_expires_at:
        JARVIS_STATE.panel = None
        JARVIS_STATE.panel_expires_at = 0.0
        memory = None

    from_file = JARVIS_STATE.file_panel
    if from_file is not None and JARVIS_STATE.file_panel_expires_at and now >= JARVIS_STATE.file_panel_expires_at:
        JARVIS_STATE.file_panel = None
        JARVIS_STATE.file_panel_expires_at = 0.0
        from_file = None

    if memory is None:
        return from_file
    if from_file is None:
        return memory
    return from_file if from_file.get("at", 0) > memory.get("at", 0) else memory


def clear_panel(broadcast: bool = True) -> None:
    """Drop both panels, and the file with them: a clear must not be undone by a stale file."""
    get_config()
    JARVIS_STATE.panel = None
    JARVIS_STATE.panel_expires_at = 0.0
    JARVIS_STATE.file_panel = None
    JARVIS_STATE.file_panel_expires_at = 0.0
    JARVIS_STATE.panel_file_mtime = None
    try:
        (_state_dir() / _PANEL_FILE).unlink()
    except OSError:
        pass
    JARVIS_STATE.last_panel_sent_id = None
    if broadcast:
        schedule_broadcast("panel", None)


def push_panel(
    title: str,
    body: str = "",
    kind: str = "card",
    ttl_s: int = 20,
    broadcast: bool = True,
) -> Dict[str, Any]:
    """Store an Agent-summoned card and (by default) push it to every mirror client.

    Called two ways: by ``POST /panel`` (which broadcasts itself, so it passes
    ``broadcast=False``) and directly by Agent's tool when the tool happens to run
    inside this process.
    """
    get_config()
    try:
        ttl = int(ttl_s)
    except (TypeError, ValueError):
        ttl = 20
    ttl = max(1, min(ttl, 600))
    clean_kind = _KIND_RE.sub("-", str(kind or "card").strip().lower()).strip("-")[:24] or "card"
    at = _now_ms()
    panel = {
        "id": f"panel-{at}",
        "title": str(title or "").strip()[:200],
        "body": str(body or "").strip()[:4000],
        "kind": clean_kind,
        "ttl": ttl,
        "at": at,
        "source": "memory",
    }
    JARVIS_STATE.panel = panel
    JARVIS_STATE.panel_expires_at = time.time() + ttl
    JARVIS_STATE.last_panel_sent_id = panel["id"]
    if broadcast:
        schedule_broadcast("panel", panel)
    return panel


# -- websocket fan-out ------------------------------------------------------


async def broadcast(kind: str, data: Any) -> None:
    """Send one frame to every mirror client, dropping the ones that have gone away."""
    if not JARVIS_STATE.clients:
        return
    frame = {"type": kind, "data": data}
    for client in list(JARVIS_STATE.clients):
        try:
            await client.send_json(frame)
        except Exception:  # noqa: BLE001 - a dead socket must never break the others
            JARVIS_STATE.clients.discard(client)


def schedule_broadcast(kind: str, data: Any) -> None:
    """Broadcast from a synchronous caller, on this loop or from another thread."""
    if not JARVIS_STATE.clients:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = JARVIS_STATE.loop
        if loop is None or loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(broadcast(kind, data), loop)
        except Exception:  # noqa: BLE001 - best effort; the mirror also polls on reconnect
            pass
        return
    try:
        loop.create_task(broadcast(kind, data))
    except Exception:  # noqa: BLE001
        pass


async def _ping_loop(client: WebSocket) -> None:
    while True:
        await asyncio.sleep(_PING_S)
        try:
            await client.send_json({"type": "ping", "data": {"at": _now_ms()}})
        except Exception:  # noqa: BLE001 - the receive loop owns the disconnect
            return


async def _watch_loop() -> None:
    """While anyone is watching: poll ``panel.json`` every second, keep ``status.json``
    warm, and push ``/state`` when it changes."""
    loop = asyncio.get_running_loop()
    last_state_push = time.monotonic()
    while JARVIS_STATE.clients:
        await asyncio.sleep(_WATCH_TICK_S)
        if not JARVIS_STATE.clients:
            break
        try:
            # 1 Hz: a new panel from Agent's tool, or one that just ran out of ttl.
            panel = await loop.run_in_executor(None, current_panel)
            panel_id = panel["id"] if panel else None
            if panel_id != JARVIS_STATE.last_panel_sent_id:
                JARVIS_STATE.last_panel_sent_id = panel_id
                await broadcast("panel", panel)

            # 5 s cap inside the writer.
            await loop.run_in_executor(None, write_status_file)

            now = time.monotonic()
            if now - last_state_push >= _STATE_PUSH_S:
                last_state_push = now
                state = await loop.run_in_executor(None, read_state)
                if state != JARVIS_STATE.last_state_sent:
                    JARVIS_STATE.last_state_sent = state
                    await broadcast("state", state)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - a bad tick must not end the watch
            continue
    JARVIS_STATE.watch_task = None


def _ensure_watch() -> None:
    task = JARVIS_STATE.watch_task
    if task is not None and not task.done():
        return
    try:
        JARVIS_STATE.watch_task = asyncio.get_running_loop().create_task(_watch_loop())
    except RuntimeError:
        JARVIS_STATE.watch_task = None


# -- routes -----------------------------------------------------------------


@router.get("/status")
def get_status() -> Dict[str, Any]:
    return read_status()


@router.get("/state")
def get_state() -> Dict[str, Any]:
    return read_state()


@router.post("/presence")
async def post_presence(request: Request) -> Response:
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > _PRESENCE_MAX_BYTES:
        return JSONResponse(status_code=413, content={"detail": "presence body too large"})
    try:
        raw = await request.body()
    except Exception:  # noqa: BLE001 - a dropped upload is a client problem, not a crash
        return JSONResponse(status_code=400, content={"detail": "presence body could not be read"})
    if len(raw) > _PRESENCE_MAX_BYTES:
        return JSONResponse(status_code=413, content={"detail": "presence body too large"})
    try:
        body = json.loads(raw)
    except Exception:  # noqa: BLE001 - a malformed frame is a client bug, not a crash
        return JSONResponse(status_code=400, content={"detail": "presence body must be JSON"})
    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"detail": "presence body must be a JSON object"})
    stored = store_presence(body)
    await broadcast("presence", stored)
    return Response(status_code=204)


@router.get("/presence")
def get_presence() -> Dict[str, Any]:
    return read_presence()


@router.post("/panel")
async def post_panel(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    panel = push_panel(
        title=body.get("title", ""),
        body=body.get("body", ""),
        kind=body.get("kind", "card"),
        ttl_s=body.get("ttl_s", 20),
        broadcast=False,
    )
    await broadcast("panel", panel)
    return {"ok": True, "panel": panel, "clients": len(JARVIS_STATE.clients)}


@router.get("/panel")
def get_panel() -> Dict[str, Any]:
    return {"panel": current_panel()}


@router.delete("/panel")
async def delete_panel() -> Dict[str, Any]:
    clear_panel(broadcast=False)
    await broadcast("panel", None)
    return {"ok": True, "panel": None}


@router.get("/mirror")
def get_mirror():
    """Serve the generated standalone mirror through the host's authenticated route."""
    try:
        if _MIRROR_HTML.is_symlink() or not _MIRROR_HTML.is_file():
            raise OSError("mirror is not a regular package file")
        html = _MIRROR_HTML.read_text(encoding="utf-8")
    except OSError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Mirror page is unavailable. Rebuild and reinstall the verified package."},
        )
    return HTMLResponse(content=html)


def ws_gate_reason(websocket: WebSocket) -> Optional[str]:
    """Why this upgrade must be refused, or None when the host's own checks pass.

    HTTP middleware does not run for a WebSocket upgrade
    (``web_server_chat.py::_ws_host_origin_reason`` says so in as many words), so the
    host's own WS routes gate themselves: ``web_routers/chat_ws.py`` and
    ``web_routers/audio.py`` both call ``_ws_auth_ok`` then ``_ws_request_is_allowed``
    before ``accept()``. This route runs exactly the same two, imported lazily so this
    module still imports in a bare test harness.

    Fail closed, without exception: if the helpers cannot be imported, or either one
    raises, the answer is "refuse". An unauthenticated peer must never reach ``accept()``.
    """
    try:
        module = importlib.import_module(_HOST_WS_AUTH_MODULE)
        ws_auth_ok = getattr(module, "_ws_auth_ok")
        ws_request_is_allowed = getattr(module, "_ws_request_is_allowed")
    except Exception:  # noqa: BLE001 - no host checks available means no admission
        return "ws auth unavailable"
    try:
        if not ws_auth_ok(websocket):
            return "credential"
        if not ws_request_is_allowed(websocket):
            return "origin"
    except Exception:  # noqa: BLE001 - an erroring check is a failing check
        return "ws auth error"
    return None


@router.websocket("/events")
async def events(websocket: WebSocket) -> None:
    # Before accept(), and before anything is sent: the host's own WS auth.
    refusal = ws_gate_reason(websocket)
    if refusal is not None:
        await websocket.close(code=1008, reason=f"jarvis: {refusal}")
        return
    # Host auth is necessary but profile identity is a separate gate.  Validate it
    # before accept so a recently rate-limited status write cannot leave cached data
    # available to a socket after config corruption or profile mismatch.
    try:
        get_config()
    except Exception:
        await websocket.close(code=1008, reason="jarvis: profile config")
        return

    await websocket.accept()
    JARVIS_STATE.clients.add(websocket)
    try:
        JARVIS_STATE.loop = asyncio.get_running_loop()
    except RuntimeError:
        JARVIS_STATE.loop = None
    ping = asyncio.create_task(_ping_loop(websocket))
    _ensure_watch()
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, write_status_file)
        get_config()
        await websocket.send_json({"type": "hello", "data": {"version": JARVIS_STATE.version}})
        presence = await loop.run_in_executor(None, read_presence)
        if presence.get("profile_id") is None:
            await websocket.close(code=1008, reason="jarvis: profile config")
            return
        await websocket.send_json({"type": "presence", "data": presence.get("presence")})
        get_config()
        panel = await loop.run_in_executor(None, current_panel)
        JARVIS_STATE.last_panel_sent_id = panel["id"] if panel else None
        await websocket.send_json({"type": "panel", "data": panel})
        state = await loop.run_in_executor(None, read_state)
        if isinstance(state.get("config"), dict) and state["config"].get("status") == "invalid":
            await websocket.close(code=1008, reason="jarvis: profile config")
            return
        JARVIS_STATE.last_state_sent = state
        await websocket.send_json({"type": "state", "data": state})
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
    except Exception:  # noqa: BLE001 - every disconnect path lands here and cleans up
        pass
    finally:
        ping.cancel()
        JARVIS_STATE.clients.discard(websocket)
        if not JARVIS_STATE.clients:
            task = JARVIS_STATE.watch_task
            if task is not None:
                task.cancel()
                JARVIS_STATE.watch_task = None
            # The watch loop is gone now, so this last write is forced: otherwise
            # status.json would keep claiming a mirror is connected.
            write_status_file(force=True)
        else:
            write_status_file()


__all__ = [
    "JARVIS_STATE",
    "SOURCE_PARITY",
    "broadcast",
    "clear_panel",
    "current_panel",
    "push_panel",
    "read_presence",
    "read_state",
    "read_status",
    "refresh_file_panel",
    "router",
    "schedule_broadcast",
    "store_presence",
    "write_status_file",
    "ws_gate_reason",
]
