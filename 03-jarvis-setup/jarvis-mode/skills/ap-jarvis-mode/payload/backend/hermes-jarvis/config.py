"""Profile-local configuration for the Hermes Jarvis plugin.

The plugin is installed at ``<profile>/plugins/hermes-jarvis``.  That location is
the authority for both identity and storage: configuration and runtime state live
in ``<profile>/jarvis``.  No environment variable or home-directory fallback is
used, so two profile processes cannot silently share data.
"""

from __future__ import annotations

import json
import importlib
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, FrozenSet, Mapping, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SCHEMA_VERSION = 1
PLUGIN_ID = "hermes-jarvis"
SOURCE_IDS: FrozenSet[str] = frozenset(
    {
        "agent_state",
        "agent_helpers",
        "next_meeting",
        "today_plan",
        "overnight_jobs",
        "one_thing_scoreboard",
        "spend",
        "lever",
        "brains",
        "scoreboard",
        "log",
    }
)

BOX_IDS: FrozenSet[str] = frozenset({
    "agent_helpers", "waiting_on_you", "agent_in_flight", "overnight_jobs",
    "next_meeting", "today", "spend", "scoreboard", "fleet",
})

_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "profile_id",
        "agent_name",
        "owner_label",
        "timezone",
        "enabled_sources",
        "sources",
        "brains",
    }
)
_TOP_KEYS = _REQUIRED_KEYS | {"enabled_boxes"}
_FILE_SOURCES = SOURCE_IDS - {"agent_state", "next_meeting", "brains"}
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class ConfigError(ValueError):
    """The selected profile or its versioned configuration is unsafe or invalid."""


@dataclass(frozen=True)
class BrainConfig:
    id: str
    label: str
    path: Path


@dataclass(frozen=True)
class JarvisConfig:
    schema_version: int
    profile_id: str
    agent_name: str
    owner_label: str
    timezone: str
    zone: ZoneInfo
    enabled_sources: FrozenSet[str]
    enabled_boxes: Optional[FrozenSet[str]]
    sources: Mapping[str, Mapping[str, Any]]
    brains: Tuple[BrainConfig, ...]
    profile_root: Path
    state_dir: Path
    config_path: Path

    def enabled(self, source_id: str) -> bool:
        return source_id in self.enabled_sources

    def source(self, source_id: str) -> Mapping[str, Any]:
        return self.sources[source_id]


def profile_root_from_plugin(plugin_location: Path | str) -> Path:
    """Derive and validate ``<profile>`` from the installed plugin path."""
    raw = Path(plugin_location).expanduser().absolute()
    if raw.is_file():
        raw = raw.parent
    if raw.name == "dashboard":
        raw = raw.parent
    # Resolve only after checking the structural path itself.  Otherwise a symlink
    # could erase the evidence that this plugin points into another profile.
    structural = (raw.parent.parent, raw.parent, raw)
    try:
        if any(part.is_symlink() for part in structural):
            raise ConfigError("profile and plugin directories must not be symlinks")
        plugin_root = raw.resolve(strict=True)
    except OSError as exc:
        raise ConfigError("plugin path does not exist") from exc
    if plugin_root.name != PLUGIN_ID or plugin_root.parent.name != "plugins":
        raise ConfigError("plugin must be installed at <profile>/plugins/hermes-jarvis")
    profile_root = plugin_root.parent.parent.resolve(strict=True)
    expected = profile_root / "plugins" / PLUGIN_ID
    if plugin_root != expected:
        raise ConfigError("plugin path does not match its canonical profile root")
    return profile_root


def _profile_matches_host(profile_id: str, profile_root: Path) -> bool:
    """Ask the running Hermes host whether this id owns this exact profile root."""
    try:
        profiles = importlib.import_module("hermes_cli.profiles")
        verifier = getattr(profiles, "profile_matches_home")
        return bool(verifier(profile_id, profile_root))
    except Exception:
        return False


def _tighten(path: Path, mode: int) -> None:
    """Create/tighten a member-owned path; reject a path owned by another user."""
    try:
        info = path.stat()
    except OSError as exc:
        raise ConfigError(f"cannot inspect {path.name}") from exc
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise ConfigError(f"{path.name} is not owned by the current user")
    if info.st_mode & 0o777 != mode:
        try:
            os.chmod(path, mode)
        except OSError as exc:
            raise ConfigError(f"cannot secure {path.name}") from exc


def ensure_state_dir(profile_root: Path) -> Path:
    state_dir = profile_root / "jarvis"
    if state_dir.is_symlink():
        raise ConfigError("profile-local Jarvis directory must not be a symlink")
    try:
        state_dir.mkdir(mode=0o700, parents=False, exist_ok=True)
    except OSError as exc:
        raise ConfigError("cannot create profile-local Jarvis directory") from exc
    _tighten(state_dir, 0o700)
    return state_dir


def _plain_label(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} must be a non-empty string")
    text = " ".join(value.split())
    if len(text) > 120:
        raise ConfigError(f"{field} is too long")
    return text


def _safe_absolute_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{field} must be an absolute path")
    raw = Path(value).expanduser()
    if not raw.is_absolute() or ".." in raw.parts:
        raise ConfigError(f"{field} must be an absolute path without traversal")
    return raw.resolve(strict=False)


def _mapping(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} must be an object")
    return dict(value)


def _validate_sources(raw: Any, enabled: FrozenSet[str]) -> Dict[str, Mapping[str, Any]]:
    document = _mapping(raw, "sources")
    unknown = set(document) - SOURCE_IDS
    if unknown:
        raise ConfigError(f"unknown source id: {sorted(unknown)[0]}")
    parsed: Dict[str, Mapping[str, Any]] = {}
    for source_id, value in document.items():
        spec = _mapping(value, f"sources.{source_id}")
        if source_id == "agent_state":
            allowed = {"path", "briefs_path"}
            if set(spec) - allowed or "path" not in spec:
                raise ConfigError("sources.agent_state requires path and accepts optional briefs_path")
            result: Dict[str, Any] = {
                "path": _safe_absolute_path(spec["path"], "sources.agent_state.path")
            }
            if "briefs_path" in spec:
                result["briefs_path"] = _safe_absolute_path(
                    spec["briefs_path"], "sources.agent_state.briefs_path"
                )
            parsed[source_id] = result
            continue
        if source_id in _FILE_SOURCES:
            if set(spec) != {"path"}:
                raise ConfigError(f"sources.{source_id} accepts only path")
            parsed[source_id] = {"path": _safe_absolute_path(spec["path"], f"sources.{source_id}.path")}
            continue
        if source_id == "next_meeting":
            allowed = {"service_account_path", "python_path", "hours"}
            unknown_fields = set(spec) - allowed
            if unknown_fields or "service_account_path" not in spec:
                raise ConfigError("sources.next_meeting has invalid fields")
            result: Dict[str, Any] = {
                "service_account_path": _safe_absolute_path(
                    spec["service_account_path"], "sources.next_meeting.service_account_path"
                )
            }
            if "python_path" in spec:
                result["python_path"] = _safe_absolute_path(
                    spec["python_path"], "sources.next_meeting.python_path"
                )
            hours = spec.get("hours", 36)
            if isinstance(hours, bool) or not isinstance(hours, int) or not 1 <= hours <= 168:
                raise ConfigError("sources.next_meeting.hours must be an integer from 1 to 168")
            result["hours"] = hours
            parsed[source_id] = result
    return parsed


def _validate_brains(raw: Any, enabled: FrozenSet[str]) -> Tuple[BrainConfig, ...]:
    if not isinstance(raw, list):
        raise ConfigError("brains must be a list")
    result = []
    seen = set()
    for index, item in enumerate(raw):
        entry = _mapping(item, f"brains[{index}]")
        if set(entry) != {"id", "label", "path"}:
            raise ConfigError(f"brains[{index}] requires only id, label, path")
        brain_id = entry["id"]
        if not isinstance(brain_id, str) or not _ID_RE.fullmatch(brain_id):
            raise ConfigError(f"brains[{index}].id is invalid")
        if brain_id in seen:
            raise ConfigError(f"duplicate brain id: {brain_id}")
        seen.add(brain_id)
        result.append(
            BrainConfig(
                brain_id,
                _plain_label(entry["label"], f"brains[{index}].label"),
                _safe_absolute_path(entry["path"], f"brains[{index}].path"),
            )
        )
    return tuple(result)


def load_config(plugin_location: Path | str) -> JarvisConfig:
    """Load schema v1 for exactly the profile containing ``plugin_location``."""
    profile_root = profile_root_from_plugin(plugin_location)
    state_dir = ensure_state_dir(profile_root)
    config_path = state_dir / "config.json"
    if config_path.is_symlink():
        raise ConfigError("Jarvis config must not be a symlink")
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError("Jarvis config is missing") from exc
    _tighten(config_path, 0o600)
    try:
        document = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError("Jarvis config is not valid JSON") from exc
    return validate_config_document(document, profile_root)


def validate_config_document(document: Any, profile_root: Path | str) -> JarvisConfig:
    """Validate prospective onboarding without writing config or creating a plugin."""
    raw_root = Path(profile_root).expanduser().absolute()
    if raw_root.is_symlink():
        raise ConfigError("profile root must not be a symlink")
    try:
        profile_root = raw_root.resolve(strict=True)
    except OSError as exc:
        raise ConfigError("profile root does not exist") from exc
    if not profile_root.is_dir():
        raise ConfigError("profile root must be a directory")
    state_dir = profile_root / "jarvis"
    config_path = state_dir / "config.json"
    if not isinstance(document, dict):
        raise ConfigError("Jarvis config must be an object")
    unknown = set(document) - _TOP_KEYS
    missing = _REQUIRED_KEYS - set(document)
    if unknown:
        raise ConfigError(f"unknown config key: {sorted(unknown)[0]}")
    if missing:
        raise ConfigError(f"missing config key: {sorted(missing)[0]}")
    if isinstance(document["schema_version"], bool) or document["schema_version"] != SCHEMA_VERSION:
        raise ConfigError("unsupported config schema_version; an explicit migration is required")
    profile_id = document["profile_id"]
    if not isinstance(profile_id, str) or not _ID_RE.fullmatch(profile_id):
        raise ConfigError("profile_id is invalid")
    if not _profile_matches_host(profile_id, profile_root):
        raise ConfigError("profile_id does not match this plugin root according to Hermes")
    try:
        zone = ZoneInfo(document["timezone"])
    except (KeyError, TypeError, ZoneInfoNotFoundError) as exc:
        raise ConfigError("timezone must be a valid IANA timezone") from exc

    enabled_raw = document["enabled_sources"]
    if not isinstance(enabled_raw, list) or any(not isinstance(item, str) for item in enabled_raw):
        raise ConfigError("enabled_sources must be a list of source ids")
    enabled = frozenset(enabled_raw)
    if len(enabled) != len(enabled_raw):
        raise ConfigError("enabled_sources contains a duplicate")
    unknown_sources = enabled - SOURCE_IDS
    if unknown_sources:
        raise ConfigError(f"unknown enabled source: {sorted(unknown_sources)[0]}")
    boxes_raw = document.get("enabled_boxes")
    boxes = None
    if "enabled_boxes" in document:
        if not isinstance(boxes_raw, list) or any(not isinstance(item, str) for item in boxes_raw):
            raise ConfigError("enabled_boxes must be a list of box ids")
        boxes = frozenset(boxes_raw)
        if len(boxes) != len(boxes_raw) or boxes - BOX_IDS:
            raise ConfigError("enabled_boxes contains duplicate or unknown box ids")
    sources = _validate_sources(document["sources"], enabled)
    brains = _validate_brains(document["brains"], enabled)
    return JarvisConfig(
        schema_version=SCHEMA_VERSION,
        profile_id=profile_id,
        agent_name=_plain_label(document["agent_name"], "agent_name"),
        owner_label=_plain_label(document["owner_label"], "owner_label"),
        timezone=document["timezone"],
        zone=zone,
        enabled_sources=enabled,
        enabled_boxes=boxes,
        sources=sources,
        brains=brains,
        profile_root=profile_root,
        state_dir=state_dir,
        config_path=config_path,
    )


def write_json_atomic(config: JarvisConfig, name: str, payload: Mapping[str, Any]) -> bool:
    """Write one profile-local state file atomically with mode 0600."""
    if not re.fullmatch(r"[a-z][a-z0-9-]*\.json", name):
        raise ValueError("invalid state file name")
    directory = ensure_state_dir(config.profile_root)
    target = directory / name
    try:
        if target.exists() or target.is_symlink():
            info = target.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                return False
    except OSError:
        return False
    temp: Path | None = None
    try:
        descriptor, raw_temp = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=directory)
        temp = Path(raw_temp)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(dict(payload), handle, separators=(",", ":"))
        os.replace(temp, target)
        os.chmod(target, 0o600)
        return True
    except (OSError, TypeError, ValueError):
        try:
            if temp is not None:
                temp.unlink()
        except OSError:
            pass
        return False


def read_json(config: JarvisConfig, name: str) -> Dict[str, Any] | None:
    if not re.fullmatch(r"[a-z][a-z0-9-]*\.json", name):
        return None
    try:
        directory_info = config.state_dir.lstat()
        if stat.S_ISLNK(directory_info.st_mode) or not stat.S_ISDIR(directory_info.st_mode):
            return None
        target = config.state_dir / name
        info = target.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return None
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None
