#!/usr/bin/env python3
"""Transactionally stage a verified JARVIS package into an explicit directory.

The ``main`` role runs on macOS, Windows and Linux; the ``headless`` role runs
wherever the member's Hermes chief of staff runs (a Mac mini or a Linux VPS).
Hands and the call-survival voice patch are Mac-only extras that are reported,
never required: they never block a core install.

This module never guesses a profile or destination and never starts services.
The default action is a dry run; pass ``--apply`` only after the caller has
chosen the destination and profile.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import stat
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

# The package preflight rejects cache directories. Disable bytecode before
# importing the local preflight module so invoking this script normally cannot
# create scripts/__pycache__ inside the package being verified.
sys.dont_write_bytecode = True
from prepare_package import PreflightError, preflight, load_manifest, sha256_file


MAC_EXTRAS_AVAILABLE = "available: hands and the call-survival voice patch can be added on this Mac; neither is required"
MAC_EXTRAS_UNAVAILABLE = "unavailable: hands and the call-survival voice patch are Mac-only extras. Skip them here; JARVIS Mode does not need them."
STATE_NAME = ".jarvis-install-state.json"
RECOVERY_STATE_NAME = ".jarvis-install-recovery.json"
STATE_SCHEMA = 1
CONFIG_SCHEMA = 1
MAIN_STATE_DIR = Path("jarvis")
BOX_SOURCE_MAP: dict[str, tuple[str, ...]] = {
    "agent_helpers": ("agent_helpers",),
    "waiting_on_you": ("agent_state",),
    "agent_in_flight": ("agent_state",),
    "overnight_jobs": ("overnight_jobs",),
    "next_meeting": ("next_meeting",),
    "today": ("today_plan", "lever"),
    "spend": ("spend",),
    "scoreboard": ("one_thing_scoreboard",),
    "fleet": (),
}


class InstallError(ValueError):
    """Raised before or during an installation transaction."""


class SetupError(InstallError):
    """Raised when the host/profile setup gate cannot be proven."""


def _safe_rel(value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise InstallError("target path must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or value.startswith(("/", "\\")) or "\\" in value:
        raise InstallError(f"unsafe target path: {value}")
    if not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise InstallError(f"unsafe target path: {value}")
    return path


def _sha(path: Path) -> str | None:
    try:
        return sha256_file(path) if stat.S_ISREG(path.lstat().st_mode) else None
    except FileNotFoundError:
        return None


def _has_entry(path: Path) -> bool:
    """Whether a path exists, including a dangling symlink."""
    return path.is_symlink() or path.exists()


def _assert_safe_destination(destination: Path) -> None:
    if not destination.is_absolute():
        raise InstallError("destination must be an explicit absolute path")
    current = destination
    while current != current.parent:
        # macOS exposes its temporary tree through the harmless /var alias.
        # Inspect every user-controlled component while allowing that system
        # alias; a symlink below it still fails.
        if current.is_symlink() and str(current) not in {"/var", "/tmp"}:
            raise InstallError(f"destination path contains a symlink: {current}")
        current = current.parent
    if destination.exists() and not destination.is_dir():
        raise InstallError("destination must be a directory")
    if not destination.exists():
        raise InstallError("destination must already exist; choose the profile directory explicitly")


def _assert_safe_parent(destination: Path, relative: Path) -> Path:
    target = destination / relative
    parent = target.parent
    current = destination
    if current.is_symlink():
        raise InstallError(f"target parent is a symlink: {current}")
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise InstallError(f"target parent is a symlink: {current}")
    if target.is_symlink():
        raise InstallError(f"target is a symlink: {target}")
    return target


def _mapping(manifest: dict[str, Any], role: str) -> list[dict[str, Any]]:
    if role not in {"main", "headless"}:
        raise InstallError("role must be main or headless")
    values = manifest.get("install_mappings", {}).get(role)
    if not isinstance(values, list) or not values:
        raise InstallError(f"no install mapping for role: {role}")
    return values


def _verified_plan(package_root: Path, role: str, destination: Path, profile_id: str | None) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    try:
        report = preflight(package_root)
    except PreflightError as exc:
        raise InstallError(str(exc)) from exc
    if not report["install_ready"]:
        raise InstallError("package preflight failed: " + "; ".join(report["errors"]))
    _assert_safe_destination(destination)
    manifest = load_manifest(package_root)
    if role == "headless":
        if not profile_id:
            raise InstallError("headless installation requires the member-selected profile_id")
        if not _stager_profile_match(profile_id, destination):
            raise InstallError("profile_id does not match the selected Hermes profile root")
    plan: list[dict[str, Any]] = []
    for item in _mapping(manifest, role):
        source_rel = str(_safe_rel(item["package_path"]))
        target_rel = str(_safe_rel(item["target_relative"]))
        source = package_root / source_rel
        target = _assert_safe_parent(destination, Path(target_rel))
        if source.is_symlink() or not source.is_file() or not stat.S_ISREG(source.lstat().st_mode):
            raise InstallError(f"mapped source is unavailable: {source_rel}")
        plan.append({
            "source_rel": source_rel,
            "source": source,
            "target_rel": target_rel,
            "target": target,
            "installed_sha256": sha256_file(source),
        })
    return manifest, plan, report


def _plan_signature(plan: list[dict[str, Any]]) -> list[dict[str, str]]:
    return sorted(
        [{
            "source_rel": item["source_rel"],
            "target_relative": item["target_rel"],
            "installed_sha256": item["installed_sha256"],
        } for item in plan],
        key=lambda item: (item["target_relative"], item["source_rel"]),
    )


def _load_backend_validator(package_root: Path):
    config_path = package_root / "payload" / "backend" / "hermes-jarvis" / "config.py"
    if config_path.is_symlink() or not config_path.is_file() or not stat.S_ISREG(config_path.lstat().st_mode):
        raise SetupError("profile setup needs the packaged backend config validator")
    spec = importlib.util.spec_from_file_location("jarvis_member_config", config_path)
    if spec is None or spec.loader is None:
        raise SetupError("could not load the packaged backend config validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _host_profile_match(profile_id: str, profile_root: Path) -> bool | None:
    """Return the Hermes host answer, or None when that host is unavailable."""
    try:
        profiles = importlib.import_module("hermes_cli.profiles")
        matcher = getattr(profiles, "profile_matches_home")
        return bool(matcher(profile_id, profile_root))
    except Exception:
        return None


def _stager_profile_match(profile_id: str, profile_root: Path) -> bool:
    """Guard a low-level fixture stager; setup uses the host answer strictly."""
    host_answer = _host_profile_match(profile_id, profile_root)
    return profile_id == profile_root.name if host_answer is None else host_answer


def _resolve_box_sources(validator: Any, enabled_boxes: list[str] | None, enabled_sources: list[str] | None) -> tuple[list[str], list[str] | None]:
    if enabled_boxes is None:
        if enabled_sources is not None:
            return list(dict.fromkeys(enabled_sources)), None
        return sorted(getattr(validator, "SOURCE_IDS", ())), None
    unknown = sorted(set(enabled_boxes) - set(BOX_SOURCE_MAP))
    if unknown:
        raise SetupError(f"unknown enabled box: {unknown[0]}")
    sources = list(enabled_sources or [])
    for box in enabled_boxes:
        for source_id in BOX_SOURCE_MAP[box]:
            if source_id not in sources:
                sources.append(source_id)
    return sources, list(enabled_boxes)


def discover_profile(profile_root: str | os.PathLike[str], profile_id: str, *, validator_module=None) -> dict[str, Any]:
    """Discover host/profile capability without changing the profile."""
    root = Path(os.path.abspath(os.fspath(Path(profile_root).expanduser())))
    _assert_safe_destination(root)
    if not isinstance(profile_id, str) or not profile_id:
        raise SetupError("profile_id must be a non-empty member-selected profile id")
    plugin = root / "plugins" / "hermes-jarvis"
    report: dict[str, Any] = {
        "profile_root": str(root),
        "profile_id": profile_id,
        "platform": platform.system(),
        "python": platform.python_version(),
        "hermes_version": None,
        "plugin_path": str(plugin),
        "plugin_present": plugin.is_dir() and not plugin.is_symlink(),
        "host_profile_match": False,
        "config_validator": validator_module is not None,
        "reasons": [],
    }
    for distribution in ("hermes-agent", "hermes"):
        try:
            report["hermes_version"] = importlib.metadata.version(distribution)
            break
        except importlib.metadata.PackageNotFoundError:
            continue
    if validator_module is not None and report["plugin_present"]:
        try:
            derived = validator_module.profile_root_from_plugin(plugin)
            report["plugin_identity"] = os.path.realpath(os.fspath(derived)) == os.path.realpath(os.fspath(root))
        except Exception as exc:
            report["plugin_identity"] = False
            report["reasons"].append(f"plugin identity: {exc}")
    else:
        report["plugin_identity"] = False
        report["reasons"].append("JARVIS plugin is not installed in the selected profile")
    host_answer = _host_profile_match(profile_id, root)
    report["host_profile_match"] = bool(host_answer)
    if host_answer is None:
        report["reasons"].append("Hermes profile matcher unavailable")
    report["ready"] = bool(report["plugin_identity"] and report["host_profile_match"] and report["config_validator"])
    return report


def _atomic_json_document(path: Path, document: Mapping[str, Any]) -> None:
    if path.is_symlink():
        raise SetupError(f"refusing to replace symlink: {path.name}")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(raw_temp)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(dict(document), stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
    except Exception:
        try:
            temp.unlink()
        except OSError:
            pass
        raise


def _atomic_bytes(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise SetupError(f"refusing to replace symlink: {path.name}")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(raw_temp)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
    except Exception:
        try:
            temp.unlink()
        except OSError:
            pass
        raise


def _validate_prospective_document(validator: Any, document: Mapping[str, Any], profile_root: Path) -> None:
    """Use the backend schema helpers without touching a profile or host."""
    validate_document = getattr(validator, "validate_config_document", None)
    if callable(validate_document):
        try:
            validate_document(document, profile_root)
            return
        except Exception as exc:
            raise SetupError(f"prospective config validation failed: {exc}") from exc
    top_keys = getattr(validator, "_TOP_KEYS", frozenset(document))
    if set(document) != set(top_keys):
        raise SetupError("prospective config has unknown or missing keys")
    if isinstance(document["schema_version"], bool) or document["schema_version"] != CONFIG_SCHEMA:
        raise SetupError("prospective config has an unsupported schema version")
    profile_id = document["profile_id"]
    identifier = getattr(validator, "_ID_RE", None)
    if not isinstance(profile_id, str) or (identifier is not None and not identifier.fullmatch(profile_id)):
        raise SetupError("prospective profile_id is invalid")
    plain_label = getattr(validator, "_plain_label", None)
    if callable(plain_label):
        plain_label(document["agent_name"], "agent_name")
        plain_label(document["owner_label"], "owner_label")
    try:
        validator.ZoneInfo(document["timezone"])
    except Exception as exc:
        raise SetupError("prospective timezone is invalid") from exc
    enabled_raw = document["enabled_sources"]
    if not isinstance(enabled_raw, list) or any(not isinstance(item, str) for item in enabled_raw):
        raise SetupError("prospective enabled_sources must be a list of source ids")
    enabled = frozenset(enabled_raw)
    if len(enabled) != len(enabled_raw):
        raise SetupError("prospective enabled_sources contains a duplicate")
    validate_sources = getattr(validator, "_validate_sources", None)
    validate_brains = getattr(validator, "_validate_brains", None)
    if not callable(validate_sources) or not callable(validate_brains):
        raise SetupError("backend validator does not expose the schema validation helpers")
    validate_sources(document["sources"], enabled)
    validate_brains(document["brains"], enabled)


def _config_document(validator: Any, profile_id: str, *, agent_name: str, owner_label: str, timezone: str, enabled_sources: list[str] | None, enabled_boxes: list[str] | None, sources: Mapping[str, Any], brains: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Build the exact schema document used for provisioning and rerun checks."""
    resolved_sources, resolved_boxes = _resolve_box_sources(validator, enabled_boxes, enabled_sources)
    document: dict[str, Any] = {
        "schema_version": CONFIG_SCHEMA,
        "profile_id": profile_id,
        "agent_name": agent_name,
        "owner_label": owner_label,
        "timezone": timezone,
        "enabled_sources": resolved_sources,
        "sources": dict(sources),
        "brains": [dict(item) for item in brains],
    }
    if resolved_boxes is not None and "enabled_boxes" in getattr(validator, "_TOP_KEYS", ()):
        document["enabled_boxes"] = resolved_boxes
    return document


def provision_profile_config(package_root: str | os.PathLike[str], profile_root: str | os.PathLike[str], profile_id: str, *, agent_name: str, owner_label: str, timezone: str, enabled_sources: list[str] | None, sources: Mapping[str, Any], brains: list[Mapping[str, Any]], enabled_boxes: list[str] | None = None, apply: bool = False, validator_module=None, backup_dir: Path | None = None) -> dict[str, Any]:
    """Validate and atomically provision profile-local schema-1 config."""
    package = Path(os.path.abspath(os.fspath(Path(package_root).expanduser())))
    root = Path(os.path.abspath(os.fspath(Path(profile_root).expanduser())))
    validator = validator_module or _load_backend_validator(package)
    plugin = root / "plugins" / "hermes-jarvis"
    discovery = discover_profile(root, profile_id, validator_module=validator)
    if not discovery["host_profile_match"]:
        raise SetupError("selected profile was not confirmed by Hermes")
    document = _config_document(
        validator,
        profile_id,
        agent_name=agent_name,
        owner_label=owner_label,
        timezone=timezone,
        enabled_sources=enabled_sources,
        enabled_boxes=enabled_boxes,
        sources=sources,
        brains=brains,
    )
    state_dir = root / "jarvis"
    config_path = state_dir / "config.json"
    result = {"profile": discovery, "config_path": str(config_path), "mode": "apply" if apply else "dry-run"}
    if not apply:
        _validate_prospective_document(validator, document, root)
        result["prospective_validated"] = True
        result["requires_plugin_before_apply"] = not discovery["plugin_identity"]
        return result
    if not discovery["plugin_identity"]:
        raise SetupError("selected profile does not contain the verified JARVIS plugin")
    if state_dir.is_symlink():
        raise SetupError("profile-local Jarvis directory must not be a symlink")
    try:
        ensure_state_dir = getattr(validator, "ensure_state_dir", None)
        if callable(ensure_state_dir):
            state_dir = ensure_state_dir(root)
            config_path = state_dir / "config.json"
        else:
            state_dir.mkdir(mode=0o700, parents=False, exist_ok=True)
            os.chmod(state_dir, 0o700)
    except OSError as exc:
        raise SetupError("cannot create profile-local Jarvis directory") from exc
    if config_path.is_symlink() or (config_path.exists() and not stat.S_ISREG(config_path.lstat().st_mode)):
        raise SetupError("profile-local config must be a regular file")
    previous = config_path.read_bytes() if config_path.exists() else None
    config_record: dict[str, Any] | None = None
    if backup_dir is not None:
        if backup_dir.is_symlink() or not backup_dir.is_dir():
            raise SetupError("installation backup directory is unavailable")
        config_record = {"target_relative": "jarvis/config.json", "installed_sha256": "", "previous_sha256": None, "backup_relative": None}
    if previous is not None and backup_dir is not None:
        config_backup = backup_dir / "jarvis" / "config.json"
        config_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_path, config_backup)
        if _sha(config_backup) != hashlib.sha256(previous).hexdigest():
            raise SetupError("profile config backup verification failed")
        config_record["previous_sha256"] = hashlib.sha256(previous).hexdigest()
        config_record["backup_relative"] = str(config_backup.relative_to(backup_dir.parent))
    try:
        _atomic_json_document(config_path, document)
        validator.load_config(plugin)
    except Exception as exc:
        try:
            if previous is None:
                if config_path.exists() and not config_path.is_symlink():
                    config_path.unlink()
            else:
                _atomic_bytes(config_path, previous)
        except Exception as restore_error:
            raise SetupError(f"config validation failed and restore failed: {restore_error}") from exc
        raise SetupError(f"config validation failed; previous config restored: {exc}") from exc
    result["validated"] = True
    result["mode_bits"] = oct(config_path.stat().st_mode & 0o777)
    if config_record is not None:
        config_record["installed_sha256"] = _sha(config_path)
        result["receipt_record"] = config_record
    return result


def _restore_config_record(profile_root: Path, record: Mapping[str, Any]) -> None:
    """Restore config changed before its installation receipt was committed."""
    target_rel = _safe_rel(record.get("target_relative"))
    if str(target_rel) != "jarvis/config.json":
        raise SetupError("config recovery record has an unexpected target")
    target = _assert_safe_parent(profile_root, target_rel)
    installed_sha = record.get("installed_sha256")
    if not isinstance(installed_sha, str) or len(installed_sha) != 64:
        raise SetupError("config recovery record has an invalid installed hash")
    if target.is_symlink() or _sha(target) != installed_sha:
        raise SetupError("config changed before recovery")
    previous_sha = record.get("previous_sha256")
    if previous_sha is None:
        target.unlink()
        return
    if not isinstance(previous_sha, str) or len(previous_sha) != 64:
        raise SetupError("config recovery record has an invalid previous hash")
    backup_value = record.get("backup_relative")
    if not isinstance(backup_value, str):
        raise SetupError("config recovery record has no previous config backup")
    backup_rel = _safe_rel(backup_value)
    backup = _assert_safe_parent(profile_root, backup_rel)
    if backup.is_symlink() or not backup.is_file() or _sha(backup) != previous_sha:
        raise SetupError("config recovery backup is missing or changed")
    _atomic_copy(backup, target)


def _write_setup_recovery(profile_root: Path, record: Mapping[str, Any], error: Exception) -> None:
    recovery = {
        "schema_version": STATE_SCHEMA,
        "status": "config-recovery-incomplete",
        "destination": str(profile_root),
        "config_record": dict(record),
        "recovery_error": str(error),
    }
    _write_json_atomic(profile_root / RECOVERY_STATE_NAME, recovery)


def _append_receipt_record(state_path: Path, record: Mapping[str, Any]) -> None:
    if state_path.is_symlink() or not state_path.is_file():
        raise SetupError("headless installation receipt is unavailable")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SetupError("headless installation receipt is unreadable") from exc
    if state.get("status") != "installed" or not isinstance(state.get("files"), list):
        raise SetupError("headless installation receipt is not complete")
    if any(item.get("target_relative") == record.get("target_relative") for item in state["files"] if isinstance(item, dict)):
        raise SetupError("headless receipt already contains the profile config")
    state["files"].append(dict(record))
    _write_json_atomic(state_path, state)


def setup_package(package_root: str | os.PathLike[str], *, main_destination: str | os.PathLike[str] | None = None, headless_destination: str | os.PathLike[str] | None = None, profile_id: str | None = None, agent_name: str | None = None, owner_label: str | None = None, timezone: str | None = None, enabled_sources: list[str] | None = None, enabled_boxes: list[str] | None = None, sources: Mapping[str, Any] | None = None, brains: list[Mapping[str, Any]] | None = None, apply: bool = False) -> dict[str, Any]:
    """Run the agent-led two-device setup orchestration.

    The caller supplies destinations discovered from the member's own host.
    This function performs no SSH, shell evaluation, service restart or
    credential handling; a remote agent may provide a verified mounted/local
    destination before calling it.
    """
    if not main_destination and not headless_destination:
        raise SetupError("setup needs an explicit main or headless destination")
    package = Path(os.path.abspath(os.fspath(Path(package_root).expanduser())))
    result: dict[str, Any] = {"mode": "apply" if apply else "dry-run", "roles": []}
    if main_destination:
        # The main role installs on macOS, Windows and Linux. Only the two
        # optional extras are Mac-only, and neither blocks this install.
        result["optional_mac_extras"] = MAC_EXTRAS_AVAILABLE if platform.system() == "Darwin" else MAC_EXTRAS_UNAVAILABLE
    validator = None
    config_args = (agent_name, owner_label, timezone)
    applied_roles: list[dict[str, Any]] = []
    preserve_recovery = False
    try:
        # Preflight the complete package before importing any packaged module.
        # The validator is package code and must never execute before hashes,
        # sizes, paths and release gates have passed.
        try:
            package_report = preflight(package)
        except PreflightError as exc:
            raise SetupError(str(exc)) from exc
        if not package_report["install_ready"]:
            raise SetupError("package preflight failed: " + "; ".join(package_report["errors"]))
        result["package_state"] = "release"
        if headless_destination:
            if not profile_id:
                raise SetupError("headless setup requires the member-selected profile_id")
            validator = _load_backend_validator(package)
            # Verify the host owns this profile before staging any role.
            initial_profile = discover_profile(headless_destination, profile_id, validator_module=validator)
            if not initial_profile["host_profile_match"]:
                raise SetupError("selected profile was not confirmed by Hermes")
            if apply and not all(value is not None for value in config_args):
                plugin = Path(headless_destination) / "plugins" / "hermes-jarvis"
                existing_config = Path(headless_destination) / "jarvis" / "config.json"
                if not (plugin.is_dir() and existing_config.is_file() and not existing_config.is_symlink()):
                    raise SetupError("apply requires complete onboarding choices or an existing validated config")
                try:
                    validator.load_config(plugin)
                except Exception as exc:
                    raise SetupError(f"existing profile config is not valid: {exc}") from exc
        if main_destination:
            role_result = install_package(package, main_destination, "main", apply=apply)
            result["roles"].append(role_result)
            if apply and role_result.get("rerun") != "no-op" and role_result.get("state"):
                applied_roles.append(role_result)
        if headless_destination:
            role_result = install_package(package, headless_destination, "headless", apply=apply, profile_id=profile_id)
            result["roles"].append(role_result)
            if apply and role_result.get("rerun") != "no-op" and role_result.get("state"):
                applied_roles.append(role_result)
            if any(value is not None for value in config_args):
                if not all(value is not None for value in config_args):
                    raise SetupError("agent_name, owner_label and timezone must be supplied together")
                if apply and role_result.get("rerun") == "no-op":
                    # A repeated identical setup must leave the known-good
                    # receipt and config untouched. Validate the requested
                    # document against the existing config before returning a
                    # no-op; a changed request remains an explicit upgrade.
                    existing_config = Path(headless_destination) / "jarvis" / "config.json"
                    if existing_config.is_symlink() or not existing_config.is_file():
                        raise SetupError("existing setup receipt has no safe profile config")
                    try:
                        current_document = json.loads(existing_config.read_text(encoding="utf-8"))
                        validator.load_config(Path(headless_destination) / "plugins" / "hermes-jarvis")
                    except Exception as exc:
                        raise SetupError(f"existing profile config is not valid: {exc}") from exc
                    requested_document = _config_document(validator, profile_id, agent_name=agent_name, owner_label=owner_label, timezone=timezone, enabled_sources=enabled_sources, enabled_boxes=enabled_boxes, sources=sources or {}, brains=brains or [])
                    if current_document != requested_document:
                        raise SetupError("setup config changes require an explicit undo before reinstall")
                    result["config"] = {"mode": "existing-validated", "rerun": "no-op"}
                else:
                    backup_dir = None
                    if apply:
                        state_payload = json.loads(Path(role_result["state"]).read_text(encoding="utf-8"))
                        backup_dir = Path(headless_destination) / state_payload["backup_dir"]
                    result["config"] = provision_profile_config(package, headless_destination, profile_id, agent_name=agent_name, owner_label=owner_label, timezone=timezone, enabled_sources=enabled_sources, enabled_boxes=enabled_boxes, sources=sources or {}, brains=brains or [], apply=apply, validator_module=validator, backup_dir=backup_dir)
                    if apply and result["config"].get("receipt_record"):
                        try:
                            _append_receipt_record(Path(role_result["state"]), result["config"]["receipt_record"])
                        except Exception as receipt_error:
                            try:
                                _restore_config_record(Path(headless_destination), result["config"]["receipt_record"])
                            except Exception as restore_error:
                                preserve_recovery = True
                                try:
                                    _write_setup_recovery(Path(headless_destination), result["config"]["receipt_record"], restore_error)
                                except Exception as recovery_error:
                                    restore_error = SetupError(f"{restore_error}; could not write recovery receipt: {recovery_error}")
                                raise SetupError(f"config receipt write failed and restoration is incomplete: {restore_error}") from receipt_error
                            raise SetupError(f"config receipt write failed; previous config restored: {receipt_error}") from receipt_error
            else:
                result["profile_discovery"] = discover_profile(headless_destination, profile_id, validator_module=validator)
                if apply:
                    result["config"] = {"mode": "existing-validated"}
    except Exception as exc:
        if apply and not preserve_recovery:
            rollback_errors: list[str] = []
            for role_result in reversed(applied_roles):
                state = role_result.get("state")
                if state:
                    try:
                        undo_install(role_result["destination"])
                    except InstallError as rollback_error:
                        rollback_errors.append(str(rollback_error))
            if rollback_errors:
                raise SetupError("setup failed and rollback is incomplete: " + "; ".join(rollback_errors)) from exc
        if isinstance(exc, SetupError):
            raise
        raise SetupError(str(exc)) from exc
    return result


def _state_path(destination: Path) -> Path:
    return destination / STATE_NAME


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    if path.is_symlink():
        raise OSError(f"refusing to replace symlink receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as out, source.open("rb") as src:
            shutil.copyfileobj(src, out)
            out.flush()
            os.fsync(out.fileno())
        shutil.copymode(source, name)
        os.replace(name, target)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def _make_private(path: Path) -> None:
    """Ask for owner-only 0700.

    POSIX honours it. Windows ignores POSIX mode bits, so there the call is a
    no-op and the directory keeps whatever mode the filesystem reports. Never
    fail a Windows install over a mode the platform cannot express; the caller
    records the mode actually achieved instead.
    """
    try:
        os.chmod(path, 0o700)
    except (NotImplementedError, OSError):
        if os.name == "posix":
            raise


def _prepare_main_state_dir(destination: Path) -> dict[str, Any]:
    """Ensure the main Hermes home has a private, safe JARVIS state directory.

    The receipt records the mode the platform actually gave the directory, not
    the mode we asked for, so undo and rerun compare like with like on every
    operating system.
    """
    _assert_safe_parent(destination, MAIN_STATE_DIR / ".directory-check")
    state_dir = destination / MAIN_STATE_DIR
    if state_dir.is_symlink():
        raise InstallError("main JARVIS state directory is a symlink")
    if state_dir.exists() and not state_dir.is_dir():
        raise InstallError("main JARVIS state directory is not a directory")
    if not state_dir.exists():
        state_dir.mkdir(mode=0o700)
        try:
            _make_private(state_dir)
            installed_mode = stat.S_IMODE(state_dir.lstat().st_mode)
        except Exception:
            try:
                state_dir.rmdir()
            except OSError:
                pass
            raise
        return {"relative": str(MAIN_STATE_DIR), "created": True, "previous_mode": None, "installed_mode": installed_mode}
    previous_mode = stat.S_IMODE(state_dir.lstat().st_mode)
    if previous_mode != 0o700:
        _make_private(state_dir)
    return {"relative": str(MAIN_STATE_DIR), "created": False, "previous_mode": previous_mode, "installed_mode": stat.S_IMODE(state_dir.lstat().st_mode)}


def _rollback_state_dirs(destination: Path, changes: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for record in reversed(changes):
        target = destination / _safe_rel(record["relative"])
        try:
            if target.is_symlink() or not target.is_dir():
                raise OSError("state directory changed or is unavailable")
            if record["created"]:
                try:
                    target.rmdir()
                except OSError:
                    # A newly-created directory may have acquired a heartbeat
                    # or other member data; preserve it rather than deleting
                    # anything outside this transaction.
                    if any(target.iterdir()):
                        continue
                    raise
            elif record["previous_mode"] != record["installed_mode"]:
                if stat.S_IMODE(target.lstat().st_mode) != record["installed_mode"]:
                    raise OSError("state directory mode changed during rollback")
                os.chmod(target, record["previous_mode"])
        except OSError as exc:
            errors.append(f"{target}: {exc}")
    return errors


def install_package(package_root: str | os.PathLike[str], destination: str | os.PathLike[str], role: str, *, apply: bool = False, profile_id: str | None = None) -> dict[str, Any]:
    package = Path(os.path.abspath(os.fspath(Path(package_root).expanduser())))
    dest = Path(os.path.abspath(os.fspath(Path(destination).expanduser())))
    manifest, plan, package_report = _verified_plan(package, role, dest, profile_id)
    result = {"mode": "apply" if apply else "dry-run", "role": role, "destination": str(dest), "files": [p["target_rel"] for p in plan]}
    result["package_state"] = "release"
    if not apply:
        return result

    state_path = _state_path(dest)
    if state_path.is_symlink():
        raise InstallError("installation state is a symlink")
    recovery_path = dest / RECOVERY_STATE_NAME
    if recovery_path.is_symlink():
        raise InstallError("installation recovery receipt is a symlink")
    if recovery_path.exists():
        raise InstallError("pending installation recovery must be resolved before applying another plan")
    if state_path.exists():
        try:
            prior = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InstallError(f"cannot read existing installation receipt: {exc}") from exc
        if (prior.get("schema_version"), prior.get("role"), prior.get("destination"), prior.get("profile_id")) != (STATE_SCHEMA, role, str(dest), profile_id):
            raise InstallError("existing installation receipt does not match this plan")
        if prior.get("status", "installed") != "installed" or prior.get("plan") != _plan_signature(plan):
            raise InstallError("refusing changed installation plan; undo the existing install before applying an upgrade")
        prior_dirs = prior.get("directories", [])
        if not isinstance(prior_dirs, list):
            raise InstallError("existing installation receipt has invalid directory records")
        if role == "main" and not any(isinstance(directory, dict) and directory.get("relative") == str(MAIN_STATE_DIR) for directory in prior_dirs):
            raise InstallError("existing main receipt predates the Hermes state directory transaction; undo before reinstall")
        for directory in prior_dirs:
            if not isinstance(directory, dict):
                raise InstallError("existing installation receipt has invalid directory record")
            directory_target = _assert_safe_parent(dest, _safe_rel(directory.get("relative")) / ".directory-check")
            if directory_target.parent.is_symlink() or not directory_target.parent.is_dir():
                raise InstallError("refusing rerun: state directory changed")
            if stat.S_IMODE(directory_target.parent.lstat().st_mode) != directory.get("installed_mode"):
                raise InstallError("refusing rerun: state directory changed")
        for record in prior.get("files", []):
            target = _assert_safe_parent(dest, _safe_rel(record.get("target_relative")))
            if target.is_symlink() or _sha(target) != record.get("installed_sha256"):
                raise InstallError(f"refusing rerun: destination changed: {record.get('target_relative')}")
        rerun_result = {"mode": "apply", "role": role, "destination": str(dest), "files": [r["target_relative"] for r in prior.get("files", [])], "state": str(state_path), "rerun": "no-op"}
        rerun_result["package_state"] = "release"
        return rerun_result
    backup_dir = dest / f".jarvis-backup-{uuid.uuid4().hex}"
    records: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    directory_records: list[dict[str, Any]] = []
    try:
        backup_dir.mkdir(mode=0o700)
        if role == "main":
            directory_records.append(_prepare_main_state_dir(dest))
        for item in plan:
            target = item["target"]
            if target.is_symlink():
                raise InstallError(f"refusing to replace symlink: {item['target_rel']}")
            if target.exists() and not stat.S_ISREG(target.lstat().st_mode):
                raise InstallError(f"refusing to replace non-regular file: {item['target_rel']}")
            previous = _sha(target)
            backup_rel: str | None = None
            if target.exists():
                backup_path = backup_dir / Path(item["target_rel"])
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup_path)
                backup_rel = str(backup_path.relative_to(dest))
            changed.append({"target": target, "previous": previous, "backup": backup_rel})
            records.append({"target_relative": item["target_rel"], "installed_sha256": item["installed_sha256"], "previous_sha256": previous, "backup_relative": backup_rel})
            _atomic_copy(item["source"], target)
        state = {"schema_version": STATE_SCHEMA, "status": "installed", "role": role, "profile_id": profile_id, "destination": str(dest), "backup_dir": str(backup_dir.relative_to(dest)), "plan": _plan_signature(plan), "files": records, "directories": directory_records}
        _write_json_atomic(state_path, state)
    except Exception as exc:
        rollback_errors: list[str] = []
        for item in reversed(changed):
            target = item["target"]
            backup = dest / item["backup"] if item["backup"] else None
            try:
                if backup is not None:
                    if _sha(backup) != item["previous"]:
                        raise OSError("backup digest no longer matches")
                    _atomic_copy(backup, target)
                elif _has_entry(target) and not target.is_symlink():
                    target.unlink()
            except OSError as rollback_error:
                rollback_errors.append(f"{target}: {rollback_error}")
        rollback_errors.extend(_rollback_state_dirs(dest, directory_records))
        if rollback_errors:
            recovery = {
                "schema_version": STATE_SCHEMA,
                "status": "rollback-incomplete",
                "role": role,
                "profile_id": profile_id,
                "destination": str(dest),
                "backup_dir": str(backup_dir.relative_to(dest)),
                "plan": _plan_signature(plan),
                "files": records,
                "directories": directory_records,
                "recovery_errors": rollback_errors,
            }
            try:
                _write_json_atomic(dest / RECOVERY_STATE_NAME, recovery)
            except OSError as receipt_error:
                rollback_errors.append(f"recovery receipt: {receipt_error}")
            raise InstallError("installation failed; rollback incomplete; backup and recovery receipt retained") from exc
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise InstallError(f"installation rolled back: {exc}") from exc
    result["state"] = str(state_path)
    return result


def undo_install(destination: str | os.PathLike[str]) -> dict[str, Any]:
    dest = Path(os.path.abspath(os.fspath(Path(destination).expanduser())))
    _assert_safe_destination(dest)
    state_path = _state_path(dest)
    if not state_path.is_file() or state_path.is_symlink():
        raise InstallError("no safe installation receipt found")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"cannot read installation receipt: {exc}") from exc
    if type(state.get("schema_version")) is not int or state.get("schema_version") != STATE_SCHEMA or state.get("status") != "installed" or state.get("destination") != str(dest):
        raise InstallError("installation receipt does not match destination")
    try:
        backup_dir_rel = _safe_rel(state.get("backup_dir"))
    except (InstallError, TypeError) as exc:
        raise InstallError("installation backup path is invalid") from exc
    if not backup_dir_rel.name.startswith(".jarvis-backup-"):
        raise InstallError("installation backup path is invalid")
    # Validate the entire backup root and its ancestors before any write.
    _assert_safe_parent(dest, backup_dir_rel / ".receipt-check")
    backup_dir = dest / backup_dir_rel
    if backup_dir.is_symlink() or not backup_dir.is_dir():
        raise InstallError("installation backup is missing")
    records = state.get("files")
    if not isinstance(records, list) or not records:
        raise InstallError("installation receipt has no files")
    directory_records = state.get("directories", [])
    if not isinstance(directory_records, list):
        raise InstallError("installation receipt directory records are invalid")
    directory_checks: list[tuple[Path, dict[str, Any]]] = []
    for directory in directory_records:
        if not isinstance(directory, dict):
            raise InstallError("installation receipt directory record is invalid")
        try:
            directory_rel = _safe_rel(directory.get("relative"))
        except (InstallError, TypeError) as exc:
            raise InstallError("installation receipt directory path is invalid") from exc
        directory_target = _assert_safe_parent(dest, directory_rel / ".directory-check").parent
        if directory_target.is_symlink() or not directory_target.is_dir():
            raise InstallError(f"refusing undo: state directory changed: {directory_rel}")
        installed_mode = directory.get("installed_mode")
        if type(installed_mode) is not int or not 0 <= installed_mode <= 0o7777:
            raise InstallError(f"installation receipt directory mode is invalid: {directory_rel}")
        if stat.S_IMODE(directory_target.lstat().st_mode) != installed_mode:
            raise InstallError(f"refusing undo: state directory mode changed: {directory_rel}")
        created = directory.get("created")
        previous_mode = directory.get("previous_mode")
        if type(created) is not bool:
            raise InstallError(f"installation receipt directory ownership is invalid: {directory_rel}")
        if created:
            if previous_mode is not None:
                raise InstallError(f"installation receipt created directory has a previous mode: {directory_rel}")
        elif type(previous_mode) is not int or not 0 <= previous_mode <= 0o7777:
            raise InstallError(f"installation receipt previous directory mode is invalid: {directory_rel}")
        directory_checks.append((directory_target, directory))
    checks: list[tuple[Path, dict[str, Any], Path | None]] = []
    seen_targets: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise InstallError("installation receipt file entry is invalid")
        target_rel = str(_safe_rel(record.get("target_relative")))
        if target_rel in seen_targets:
            raise InstallError("installation receipt contains duplicate targets")
        seen_targets.add(target_rel)
        target = _assert_safe_parent(dest, Path(target_rel))
        installed_hash = record.get("installed_sha256")
        previous_hash = record.get("previous_sha256")
        if not isinstance(installed_hash, str) or len(installed_hash) != 64:
            raise InstallError(f"installation receipt hash is invalid: {target_rel}")
        if previous_hash is not None and (not isinstance(previous_hash, str) or len(previous_hash) != 64):
            raise InstallError(f"installation receipt previous hash is invalid: {target_rel}")
        if target.is_symlink() or _sha(target) != installed_hash:
            raise InstallError(f"refusing undo: destination changed: {target_rel}")
        backup_rel_value = record.get("backup_relative")
        backup: Path | None = None
        if previous_hash is None:
            if backup_rel_value is not None:
                raise InstallError(f"unexpected backup for new target: {target_rel}")
        else:
            if not isinstance(backup_rel_value, str):
                raise InstallError(f"missing backup for replaced target: {target_rel}")
            backup_rel = _safe_rel(backup_rel_value)
            expected_rel = backup_dir_rel / Path(target_rel)
            if backup_rel != expected_rel:
                raise InstallError(f"backup is outside its recorded root: {target_rel}")
            _assert_safe_parent(dest, backup_rel)
            backup = dest / backup_rel
            if backup.is_symlink() or not stat.S_ISREG(backup.lstat().st_mode):
                raise InstallError(f"installation backup is missing or non-regular: {target_rel}")
            if _sha(backup) != previous_hash:
                raise InstallError(f"installation backup digest mismatch: {target_rel}")
        checks.append((target, record, backup))

    # Snapshot the installed state outside the backup tree. If a later
    # restore fails, these snapshots let us return to the pre-undo state.
    undo_dir = backup_dir / f".undo-current-{uuid.uuid4().hex}"
    undo_dir.mkdir(mode=0o700)
    snapshots: list[tuple[Path, Path]] = []
    try:
        for target, record, _backup in checks:
            snapshot = undo_dir / Path(record["target_relative"])
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, snapshot)
            if _sha(snapshot) != record["installed_sha256"]:
                raise InstallError(f"could not snapshot installed target: {record['target_relative']}")
            snapshots.append((target, snapshot))
    except Exception as exc:
        shutil.rmtree(undo_dir, ignore_errors=True)
        raise InstallError(f"undo did not start: {exc}") from exc

    attempted: list[tuple[Path, Path]] = []
    removed_directories: list[Path] = []
    changed_directory_modes: list[tuple[Path, int]] = []
    preserved_directories: list[str] = []
    try:
        for target, record, backup in checks:
            snapshot = undo_dir / Path(record["target_relative"])
            attempted.append((target, snapshot))
            if backup is not None:
                _atomic_copy(backup, target)
            else:
                if target.is_symlink():
                    raise InstallError(f"target became a symlink during undo: {record['target_relative']}")
                target.unlink()
        for directory_target, directory in directory_checks:
            if directory["created"]:
                if any(directory_target.iterdir()):
                    preserved_directories.append(str(directory_target.relative_to(dest)))
                else:
                    directory_target.rmdir()
                    removed_directories.append(directory_target)
            elif directory["previous_mode"] != directory["installed_mode"]:
                os.chmod(directory_target, directory["previous_mode"])
                changed_directory_modes.append((directory_target, directory["installed_mode"]))
        state_path.unlink()
    except Exception as exc:
        recovery_errors: list[str] = []
        for target, snapshot in reversed(attempted):
            try:
                _atomic_copy(snapshot, target)
            except OSError as rollback_error:
                recovery_errors.append(f"{target}: {rollback_error}")
        for directory_target in reversed(removed_directories):
            try:
                directory_target.mkdir(mode=0o700)
            except OSError as rollback_error:
                recovery_errors.append(f"{directory_target}: {rollback_error}")
        for directory_target, installed_mode in reversed(changed_directory_modes):
            try:
                os.chmod(directory_target, installed_mode)
            except OSError as rollback_error:
                recovery_errors.append(f"{directory_target}: {rollback_error}")
        if recovery_errors:
            state["status"] = "undo-incomplete"
            state["undo_recovery_dir"] = str(undo_dir.relative_to(dest))
            state["recovery_errors"] = recovery_errors
            try:
                _write_json_atomic(state_path, state)
            except OSError as receipt_error:
                recovery_errors.append(f"recovery receipt: {receipt_error}")
            raise InstallError("undo failed; recovery state and backups retained") from exc
        shutil.rmtree(undo_dir, ignore_errors=True)
        raise InstallError("undo failed; original installation restored and receipt retained") from exc
    shutil.rmtree(undo_dir, ignore_errors=True)
    result = {"mode": "undo", "destination": str(dest), "files": [r["target_relative"] for r in records]}
    if preserved_directories:
        result["preserved_directories"] = preserved_directories
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage verified JARVIS files or run the agent-led setup gate.")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--role", choices=("main", "headless"))
    parser.add_argument("--profile-id")
    parser.add_argument("--apply", action="store_true", help="write files; otherwise perform a dry run")
    parser.add_argument("--undo", action="store_true", help="undo the prior receipt in --destination")
    parser.add_argument("--setup", action="store_true", help="run profile discovery, selected-box config and both install roles")
    parser.add_argument("--main-destination", type=Path)
    parser.add_argument("--headless-destination", type=Path)
    parser.add_argument("--agent-name")
    parser.add_argument("--owner-label")
    parser.add_argument("--timezone")
    parser.add_argument("--enabled-source", action="append", default=None)
    parser.add_argument("--enabled-box", action="append", default=None)
    parser.add_argument("--sources-json", default="{}")
    parser.add_argument("--brains-json", default="[]")
    args = parser.parse_args()
    try:
        if args.setup:
            sources = json.loads(args.sources_json)
            brains = json.loads(args.brains_json)
            if not isinstance(sources, dict) or not isinstance(brains, list):
                raise SetupError("sources-json must be an object and brains-json must be a list")
            result = setup_package(args.package_root, main_destination=args.main_destination, headless_destination=args.headless_destination, profile_id=args.profile_id, agent_name=args.agent_name, owner_label=args.owner_label, timezone=args.timezone, enabled_sources=args.enabled_source, enabled_boxes=args.enabled_box, sources=sources, brains=brains, apply=args.apply)
        elif args.undo:
            if args.destination is None:
                raise InstallError("--destination is required for undo")
            result = undo_install(args.destination)
        else:
            if args.destination is None or args.role is None:
                raise InstallError("--destination and --role are required unless --setup or --undo is used")
            result = install_package(args.package_root, args.destination, args.role, apply=args.apply, profile_id=args.profile_id)
    except (InstallError, PreflightError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
