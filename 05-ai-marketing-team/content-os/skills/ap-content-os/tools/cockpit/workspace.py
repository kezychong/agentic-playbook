#!/usr/bin/env python3
"""
workspace.py - where the member's content-os/ workspace lives, and the small
safe-write helpers everything else in the cockpit shares.

Standard library only. Nothing here installs anything, downloads anything, or
reaches the network. Every write is atomic (temp file, then rename) so a
reader never sees a half-written file, and every cross-process lock is a
plain lock file created with O_EXCL, so this works the same on macOS,
Windows, and Linux.

The cockpit owns exactly one folder inside the workspace: content-os/cockpit/.
Its own settings, its click receipts, its cached cover images, and its step
logs live there and nowhere else. Everything outside that folder is read, and
only ever moved as a whole file when the member clicks an action.
"""

import datetime
import json
import os
import re
import tempfile
import time
from pathlib import Path

try:  # zoneinfo ships with Python 3.9+; a missing tz database is survivable
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - very old runtimes
    ZoneInfo = None

WORKSPACE_DIR_NAME = "content-os"
COCKPIT_DIR_NAME = "cockpit"

# The cockpit's own files, all inside content-os/cockpit/
CONFIG_FILENAME = "config.json"
PREFS_FILENAME = "prefs.json"
ACTIONS_LOG_FILENAME = "actions-log.md"
NEWS_ARCHIVE_FILENAME = "news-archive.json"
THUMBS_DIR_NAME = "covers"
STEP_LOGS_DIR_NAME = "step-logs"
LOCKS_DIR_NAME = "locks"

# Shared interfaces owned by other parts of the system. Read defensively:
# every one of these may be absent on a brand-new workspace.
POSTED_LEDGER_NAME = "posted.md"                       # append-only posted log
CALENDAR_PLAN_NAME = "calendar-plan.json"              # planned posts
NEWS_PILLARS_NAME = "news-pillars.md"                  # written at setup
PATTERNS_FEED_REL = ("analytics", "patterns.json")     # written by the analytics loop
FOCUS_FILE_NAME = "MY-FOCUS.md"                        # one line: this week's focus
WATCHLIST_FILE_NAME = "MY-WATCHLIST.md"
VOICE_FILE_NAME = "MY-VOICE.md"

DEFAULT_PORT = 8791
ENV_WORKSPACE = "CONTENT_OS_WORKSPACE"
ENV_PORT = "CONTENT_OS_COCKPIT_PORT"
ENV_DRYRUN = "CONTENT_OS_COCKPIT_DRYRUN"
ENV_AGENT = "CONTENT_OS_COCKPIT_AGENT"


# --------------------------------------------------------------------------
# Finding the workspace
# --------------------------------------------------------------------------

def find_workspace(start=None):
    """Return the content-os/ folder this cockpit should read.

    Order of preference:
      1. the CONTENT_OS_WORKSPACE value, when it points at a real folder
         (either the content-os folder itself or its parent),
      2. the nearest content-os/ folder at or above the current directory,
      3. the nearest content-os/ folder at or above this file's own folder.

    Returns None when no workspace exists yet. Callers must handle that as an
    honest empty state, never as a crash.
    """
    override = os.environ.get(ENV_WORKSPACE, "").strip()
    if override:
        candidate = Path(override).expanduser()
        if candidate.name == WORKSPACE_DIR_NAME and candidate.is_dir():
            return candidate.resolve()
        nested = candidate / WORKSPACE_DIR_NAME
        if nested.is_dir():
            return nested.resolve()
        if candidate.is_dir():
            return (candidate / WORKSPACE_DIR_NAME).resolve()

    roots = []
    if start is not None:
        roots.append(Path(start))
    roots.append(Path.cwd())
    roots.append(Path(__file__).resolve().parent)

    for root in roots:
        try:
            root = root.resolve()
        except OSError:
            continue
        for parent in [root] + list(root.parents):
            if parent.name == WORKSPACE_DIR_NAME and parent.is_dir():
                return parent
            candidate = parent / WORKSPACE_DIR_NAME
            if candidate.is_dir():
                return candidate.resolve()
    return None


class Workspace:
    """Every path the cockpit touches, resolved once from the workspace root."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    # -- read-only member content -----------------------------------------
    @property
    def ideas_dir(self):
        return self.root / "ideas"

    @property
    def inbox_dir(self):
        """ideas/inbox/ once the workspace has been split into stages, else
        the flat ideas/ folder a first-version workspace still uses."""
        split = self.ideas_dir / "inbox"
        return split if split.is_dir() else self.ideas_dir

    @property
    def qualified_dir(self):
        return self.ideas_dir / "qualified"

    @property
    def parked_dir(self):
        return self.ideas_dir / "parked"

    @property
    def retired_ideas_dir(self):
        return self.ideas_dir / "_retired"

    @property
    def not_content_dir(self):
        return self.root / "_not-content"

    @property
    def library_dir(self):
        return self.root / "library"

    @property
    def scripts_dir(self):
        return self.root / "scripts"

    @property
    def retired_scripts_dir(self):
        return self.scripts_dir / "_retired"

    @property
    def runs_dir(self):
        return self.root / "runs"

    @property
    def retired_runs_dir(self):
        return self.runs_dir / "_retired"

    @property
    def story_bank_dir(self):
        return self.root / "story-bank"

    @property
    def posted_ledger(self):
        return self.root / POSTED_LEDGER_NAME

    @property
    def calendar_plan(self):
        return self.root / CALENDAR_PLAN_NAME

    @property
    def news_pillars(self):
        return self.root / NEWS_PILLARS_NAME

    @property
    def patterns_feed(self):
        return self.root.joinpath(*PATTERNS_FEED_REL)

    @property
    def focus_file(self):
        return self.root / FOCUS_FILE_NAME

    @property
    def watchlist_file(self):
        return self.root / WATCHLIST_FILE_NAME

    @property
    def voice_file(self):
        return self.root / VOICE_FILE_NAME

    @property
    def view_snapshots(self):
        return self.library_dir / "view-snapshots.json"

    # -- the cockpit's own folder ------------------------------------------
    @property
    def cockpit_dir(self):
        return self.root / COCKPIT_DIR_NAME

    @property
    def config_path(self):
        return self.cockpit_dir / CONFIG_FILENAME

    @property
    def prefs_path(self):
        return self.cockpit_dir / PREFS_FILENAME

    @property
    def actions_log(self):
        return self.cockpit_dir / ACTIONS_LOG_FILENAME

    @property
    def news_archive(self):
        return self.cockpit_dir / NEWS_ARCHIVE_FILENAME

    @property
    def thumbs_dir(self):
        return self.cockpit_dir / THUMBS_DIR_NAME

    @property
    def step_logs_dir(self):
        return self.cockpit_dir / STEP_LOGS_DIR_NAME

    @property
    def locks_dir(self):
        return self.cockpit_dir / LOCKS_DIR_NAME

    # -- helpers ------------------------------------------------------------
    def relative(self, path: Path) -> str:
        """A workspace-relative posix id for a file, used as a card id."""
        try:
            return Path(path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return Path(path).name

    def resolve_inside(self, relative_path: str):
        """Resolve a workspace-relative path, or None if it escapes the
        workspace. Every path that arrives from the browser goes through
        this before anything on disk is touched."""
        if not isinstance(relative_path, str) or not relative_path:
            return None
        cleaned = relative_path.replace("\\", "/").lstrip("/")
        if not cleaned:
            return None
        candidate = (self.root / cleaned).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            return None
        return candidate

    def exists(self) -> bool:
        return self.root.is_dir()

    def is_set_up(self) -> bool:
        """A workspace counts as set up once the voice file exists - the same
        check the rest of the system uses."""
        return self.voice_file.is_file()


# --------------------------------------------------------------------------
# Atomic writes
# --------------------------------------------------------------------------

def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def atomic_write_json(path: Path, data) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def atomic_write_bytes(path: Path, blob: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_bytes(blob)
    tmp.replace(path)


def read_json(path: Path, default=None):
    """Read JSON, or return `default` for every failure mode: missing file,
    unreadable file, invalid JSON. Never raises."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def read_text(path: Path, default="") -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return default


# --------------------------------------------------------------------------
# Cross-process lock - a lock file, created with O_EXCL. Works everywhere,
# including Windows, which is why this is not built on Unix file locking.
# --------------------------------------------------------------------------

class FileLock:
    """Non-blocking lock. `acquired` is False when someone else holds it.

    A lock older than `stale_after` seconds is assumed to belong to a process
    that died and is taken over, so a crash can never wedge a feature shut.
    """

    def __init__(self, path: Path, stale_after: int = 900):
        self.path = Path(path)
        self.stale_after = stale_after
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._try_acquire()
        if not self.acquired:
            self._break_if_stale()
            self._try_acquire()
        return self

    def _try_acquire(self):
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return
        except OSError:
            return
        try:
            os.write(fd, f"{os.getpid()} {int(time.time())}".encode("utf-8"))
        finally:
            os.close(fd)
        self.acquired = True

    def _break_if_stale(self):
        try:
            age = time.time() - self.path.stat().st_mtime
        except OSError:
            return
        if age > self.stale_after:
            try:
                self.path.unlink()
            except OSError:
                pass

    def __exit__(self, exc_type, exc, tb):
        if self.acquired:
            try:
                self.path.unlink()
            except OSError:
                pass
            self.acquired = False
        return False


# --------------------------------------------------------------------------
# Receipts - one line per action, append only
# --------------------------------------------------------------------------

_RECEIPT_HEADER = (
    "# Cockpit receipts\n\n"
    "One line per action taken from the cockpit. Written by the cockpit, "
    "never edited by hand.\n\n"
)


def append_receipt(workspace: Workspace, action: str, subject: str, result: str) -> None:
    """Append one receipt line. Best effort: a receipt that cannot be written
    never fails the action the member just took."""
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    safe_subject = (subject or "-").replace("\n", " ").strip() or "-"
    safe_result = (result or "").replace("\n", " ").strip()
    line = f"- {stamp} | {action} | {safe_subject} | {safe_result}\n"
    try:
        path = workspace.actions_log
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(_RECEIPT_HEADER, encoding="utf-8")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        pass


def unique_destination(dest_dir: Path, filename: str) -> Path:
    """dest_dir/filename, or the same name with -2, -3 ... appended. An
    existing file is never overwritten and never deleted."""
    dest_dir = Path(dest_dir)
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 2
    while True:
        candidate = dest_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# --------------------------------------------------------------------------
# Settings - content-os/cockpit/config.json
# --------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "timezone": "",          # blank means "use whatever this machine is set to"
    "region_name": "",       # plain name, e.g. the member's country
    "region_code": "",       # two-letter code used by the trending-search feed
    "port": DEFAULT_PORT,
    "agent_runtime": "auto",  # auto | off | a named runtime
}

_TZ_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_+\-]*(?:/[A-Za-z0-9_+\-.]+)*$")


def local_timezone_name() -> str:
    """The machine's own timezone name, or an empty string when it cannot be
    determined. Never guesses a city."""
    try:
        name = datetime.datetime.now().astimezone().tzname() or ""
    except (OSError, ValueError):
        name = ""
    link = Path("/etc/localtime")
    try:
        if link.is_symlink():
            target = os.readlink(str(link))
            marker = "/zoneinfo/"
            if marker in target:
                candidate = target.split(marker, 1)[1]
                if _TZ_NAME_RE.match(candidate):
                    return candidate
    except OSError:
        pass
    return name


def load_config(workspace: Workspace) -> dict:
    """Settings, with sane fallbacks. Missing or damaged settings never stop
    the cockpit; they just fall back to the machine's own values."""
    config = dict(DEFAULT_CONFIG)
    stored = read_json(workspace.config_path, default=None)
    if isinstance(stored, dict):
        for key in DEFAULT_CONFIG:
            if key in stored and isinstance(stored[key], type(DEFAULT_CONFIG[key])):
                config[key] = stored[key]
    pillars = load_news_pillars(workspace)
    if not config["timezone"] and pillars.get("timezone"):
        config["timezone"] = pillars["timezone"]
    if not config["region_name"] and pillars.get("region_name"):
        config["region_name"] = pillars["region_name"]
    if not config["region_code"] and pillars.get("region_code"):
        config["region_code"] = pillars["region_code"]
    if not config["timezone"]:
        config["timezone"] = local_timezone_name()
    return config


def tzinfo_for(config: dict):
    """A timezone object for the configured zone, falling back to whatever
    this machine is set to. Never raises on a bad zone name."""
    name = (config or {}).get("timezone") or ""
    if name and ZoneInfo is not None and _TZ_NAME_RE.match(name):
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    return datetime.datetime.now().astimezone().tzinfo


def today_in(config: dict) -> datetime.date:
    return datetime.datetime.now(tz=tzinfo_for(config)).date()


# --------------------------------------------------------------------------
# News pillars - content-os/news-pillars.md, written at setup
#
# Heading-structured markdown, the same shape as every other card in this
# system. No frontmatter anywhere. The file is optional: with no file, the
# News tab says plainly that no topics have been chosen yet.
#
# Shape this parser accepts:
#
#   # My news pillars
#
#   Region: <plain country or area name>
#   Region code: <two letters>
#   Timezone: <zone name>
#   Trending searches: on | off
#   Tech stories: on | off
#
#   ## Pillar: <name>
#   - Search terms: term one, "an exact phrase", term three
#   - Keywords: word, word, word
# --------------------------------------------------------------------------

_PILLAR_HEADING_RE = re.compile(r"^##\s+Pillar\s*[:\-]\s*(.+?)\s*$", re.IGNORECASE)
_FIELD_RE = re.compile(r"^\s*[-*]?\s*([A-Za-z][A-Za-z ]{1,30}?)\s*:\s*(.*)$")
_REGION_CODE_RE = re.compile(r"^[A-Za-z]{2}$")


def _split_terms(value: str):
    parts = [part.strip().strip('"').strip() for part in re.split(r",|;", value or "")]
    return [part for part in parts if part]


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return slug or "pillar"


def _truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"on", "yes", "true", "1"}


def load_news_pillars(workspace: Workspace) -> dict:
    """Parse the member's chosen news topics. Always returns a dict; an
    absent or unreadable file returns empty pillars, never an error."""
    result = {
        "present": False,
        "region_name": "",
        "region_code": "",
        "timezone": "",
        "trending_searches": True,
        "tech_stories": False,
        "pillars": [],
    }
    text = read_text(workspace.news_pillars, default="")
    if not text.strip():
        return result
    result["present"] = True

    current = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading = _PILLAR_HEADING_RE.match(line)
        if heading:
            current = {
                "name": heading.group(1).strip(),
                "id": _slugify(heading.group(1)),
                "search_terms": [],
                "keywords": [],
            }
            result["pillars"].append(current)
            continue
        if line.startswith("#"):
            if line.startswith("## "):
                current = None
            continue
        field = _FIELD_RE.match(line)
        if not field:
            continue
        key = field.group(1).strip().lower()
        value = field.group(2).strip()
        if current is not None:
            if key in ("search terms", "searches", "queries"):
                current["search_terms"] = _split_terms(value)
            elif key in ("keywords", "words"):
                current["keywords"] = _split_terms(value)
            continue
        if key in ("region", "country", "area"):
            result["region_name"] = value
        elif key in ("region code", "country code"):
            if _REGION_CODE_RE.match(value):
                result["region_code"] = value.upper()
        elif key == "timezone":
            if _TZ_NAME_RE.match(value):
                result["timezone"] = value
        elif key in ("trending searches", "trends"):
            result["trending_searches"] = _truthy(value)
        elif key in ("tech stories", "tech and startup stories", "tech"):
            result["tech_stories"] = _truthy(value)

    # A pillar with no search terms falls back to its own name, so a
    # half-filled file still produces something honest rather than nothing.
    for pillar in result["pillars"]:
        if not pillar["search_terms"] and pillar["name"]:
            pillar["search_terms"] = [pillar["name"]]
        if not pillar["keywords"]:
            pillar["keywords"] = [word.lower() for word in _split_terms(pillar["name"]) if word]
    return result


# --------------------------------------------------------------------------
# Small shared helpers
# --------------------------------------------------------------------------

def scratch_dir() -> Path:
    return Path(tempfile.gettempdir())


def format_age(day, today: datetime.date) -> str:
    if day is None:
        return "age unknown"
    days = (today - day).days
    if days < 0:
        return "dated in the future"
    if days == 0:
        return "today"
    if days == 1:
        return "1 day old"
    return f"{days} days old"
