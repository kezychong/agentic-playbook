"""Hermes Jarvis tools and the live spoken-call hook.

The tools share profile-local state with the backend.  The in-process shortcut is
used only when the mounted backend proves it belongs to the same profile root.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("hermes_jarvis")
_PLUGIN_ROOT = Path(__file__).absolute().parent
_DASHBOARD_MODULE = "hermes_dashboard_plugin_hermes-jarvis"
_PANEL_FILE = "panel.json"
_PRESENCE_FILE = "presence.json"
_STATUS_FILE = "status.json"
_SPOKEN_RULE_FILE = "spoken-rule.json"
_API_PREFIX = "/api/plugins/hermes-jarvis"
_HTTP_TIMEOUT_S = 3.0


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


def _config():
    return _CONFIG.load_config(_PLUGIN_ROOT)


def _write(name: str, payload: Dict[str, Any]) -> bool:
    try:
        return bool(_CONFIG.write_json_atomic(_config(), name, payload))
    except Exception:
        return False


def _read(name: str) -> Optional[Dict[str, Any]]:
    try:
        return _CONFIG.read_json(_config(), name)
    except Exception:
        return None


def _dashboard_module():
    module = sys.modules.get(_DASHBOARD_MODULE)
    if module is None:
        return None
    try:
        module_root = Path(getattr(module, "_PROFILE_ROOT")).resolve(strict=True)
    except (OSError, TypeError, ValueError):
        return None
    if module_root != _PROFILE_ROOT:
        return None
    if callable(getattr(module, "push_panel", None)) and callable(getattr(module, "read_presence", None)):
        return module
    return None


def _panel_id() -> str:
    return f"{int(time.time() * 1000)}-{os.getpid()}"


def _panel_receipt(panel: Dict[str, Any], clients: Optional[int] = None) -> str:
    title = str(panel.get("title") or panel.get("body") or "panel").strip()
    if len(title) > 60:
        title = title[:57] + "..."
    suffix = "" if clients is None else f", {clients} mirror client{'s' if clients != 1 else ''}"
    return f'Jarvis panel up: "{title}" ({panel.get("kind", "card")}, {panel.get("ttl", panel.get("ttl_s", 20))}s, id {panel.get("id")}){suffix}.'


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward the member-supplied session cookie to another location."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _http_requested() -> bool:
    return bool(os.environ.get("JARVIS_DASHBOARD_URL") or os.environ.get("JARVIS_DASHBOARD_COOKIE"))


def _http_settings() -> Tuple[str, str]:
    base = (os.environ.get("JARVIS_DASHBOARD_URL") or "").strip().rstrip("/")
    cookie = (os.environ.get("JARVIS_DASHBOARD_COOKIE") or "").strip()
    if not base or not cookie:
        raise ValueError("dashboard URL and cookie must both be configured")
    parsed = urllib.parse.urlsplit(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("dashboard URL contains unsupported credentials or suffixes")
    if parsed.path not in ("", "/"):
        raise ValueError("dashboard URL must not contain a path")
    loopback = parsed.hostname == "localhost"
    if parsed.hostname:
        try:
            loopback = loopback or ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            pass
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise ValueError("dashboard URL must use HTTPS, except for loopback HTTP")
    return base, cookie


def _raw_request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]],
    base: str,
    cookie: str,
) -> Tuple[int, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "Cookie": cookie}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{_API_PREFIX}{path}", data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=_HTTP_TIMEOUT_S) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        return exc.code, None


def _http_binding(base: str, cookie: str) -> Tuple[bool, str]:
    """Prove the remote host serves this configured profile before sending data."""
    try:
        status, body = _raw_request("GET", "/status", None, base, cookie)
    except (urllib.error.URLError, OSError, ValueError):
        return False, "dashboard did not answer"
    if status in (401, 403):
        return False, "dashboard auth refused"
    if status >= 400 or not isinstance(body, dict):
        return False, "dashboard profile binding is unavailable"
    try:
        expected = _config().profile_id
    except Exception:
        return False, "local profile config is invalid"
    if body.get("profile_id") != expected:
        return False, "dashboard profile binding does not match"
    return True, ""


def jarvis_show_panel(args: Optional[Dict[str, Any]] = None, **_: Any) -> str:
    args = args or {}
    title, body = str(args.get("title") or "").strip(), str(args.get("body") or "").strip()
    kind = str(args.get("kind") or "card").strip() or "card"
    try:
        ttl = max(1, min(int(args.get("ttl_s", 20)), 600))
    except (TypeError, ValueError):
        ttl = 20
    if not title and not body:
        return "Jarvis panel needs a title or a body."
    try:
        _config()
    except Exception as exc:
        return f"Jarvis panel refused: {str(exc)[:160]}."
    module = _dashboard_module()
    if module is not None:
        try:
            panel = module.push_panel(title=title, body=body, kind=kind, ttl_s=ttl)
            state = getattr(module, "JARVIS_STATE", None)
            clients = len(state.clients) if state is not None else None
            return _panel_receipt(panel, clients)
        except Exception as exc:
            logger.debug("Jarvis in-process panel failed (%s); using file state", type(exc).__name__)
    if _http_requested():
        try:
            base, cookie = _http_settings()
        except ValueError as exc:
            return f"Jarvis panel refused: {exc}."
        bound, reason = _http_binding(base, cookie)
        if not bound:
            return f"Jarvis panel refused: {reason}."
        try:
            status, data = _raw_request(
                "POST", "/panel", {"title": title, "body": body, "kind": kind, "ttl_s": ttl},
                base, cookie)
        except (urllib.error.URLError, OSError, ValueError):
            return "Jarvis panel refused: dashboard did not answer."
        if status >= 400 or not isinstance(data, dict) or not isinstance(data.get("panel"), dict):
            return f"Jarvis panel refused: dashboard answered {status}."
        clients = data.get("clients")
        return _panel_receipt(data["panel"], clients if isinstance(clients, int) else None)
    panel = {"id": _panel_id(), "title": title[:200], "body": body[:4000], "kind": kind[:24], "ttl_s": ttl, "at": int(time.time() * 1000)}
    if not _write(_PANEL_FILE, panel):
        return "Jarvis panel could not be written to this profile."
    return _panel_receipt(panel)


def _status_sentence(status: Optional[Dict[str, Any]], presence: Optional[Dict[str, Any]]) -> str:
    status, presence = status or {}, presence or {}
    body = presence.get("presence")
    clients = status.get("clients", presence.get("clients", 0))
    version = status.get("version", presence.get("version", "?"))
    if not isinstance(body, dict):
        return f"Jarvis backend v{version} is up, {clients} mirror client(s), but no presence yet."
    source = body.get("source") if isinstance(body.get("source"), dict) else {}
    age = presence.get("age_ms")
    age_text = "unknown age" if age is None else f"{max(0, int(age)) / 1000:.1f}s old"
    return f"Jarvis: call {body.get('call', 'off')}, mode {body.get('mode', 'unknown')}, source {source.get('status', 'none')}, presence {age_text}, {clients} mirror client(s), backend v{version}."


def jarvis_status(args: Optional[Dict[str, Any]] = None, **_: Any) -> str:
    del args
    try:
        _config()
    except Exception as exc:
        return f"Jarvis config is invalid: {str(exc)[:160]}."
    module = _dashboard_module()
    if module is not None:
        try:
            return _status_sentence(module.read_status(), module.read_presence())
        except Exception as exc:
            logger.debug("Jarvis in-process status failed (%s); using file state", type(exc).__name__)
    if _http_requested():
        try:
            base, cookie = _http_settings()
        except ValueError as exc:
            return f"Jarvis status refused: {exc}."
        bound, reason = _http_binding(base, cookie)
        if not bound:
            return f"Jarvis status refused: {reason}."
        try:
            presence_code, presence = _raw_request("GET", "/presence", None, base, cookie)
            status_code, status = _raw_request("GET", "/status", None, base, cookie)
        except (urllib.error.URLError, OSError, ValueError):
            return "Jarvis status refused: dashboard did not answer."
        if presence_code in (401, 403) or status_code in (401, 403):
            return "Jarvis status refused: dashboard auth refused."
        if (presence_code >= 400 or status_code >= 400
                or not isinstance(presence, dict) or not isinstance(status, dict)):
            return "Jarvis status refused: dashboard state is unavailable."
        if status.get("profile_id") != _config().profile_id:
            return "Jarvis status refused: dashboard profile binding does not match."
        return _status_sentence(status, presence)
    presence, status = _read(_PRESENCE_FILE), _read(_STATUS_FILE)
    if presence is None:
        if status is None:
            return "Jarvis has no presence file yet. Is the Jarvis display open?"
        return _status_sentence(status, None)
    envelope = dict(presence)
    written = envelope.get("at")
    envelope["age_ms"] = max(0, int(time.time() * 1000) - int(written)) if isinstance(written, (int, float)) else None
    return _status_sentence(status, envelope)


_SPOKEN_MARKER = "delegation from a live spoken conversation"
SPOKEN_RULE = (
    "[Jarvis spoken-call rule. The person is waiting in silence on a live call, and a new spoken "
    "turn interrupts work in progress. If you can answer from what you know or with at most two "
    "quick tool calls, answer now in one or two sentences. For anything longer, call delegate_task "
    "once with a complete brief, say in one sentence what the helper is doing, and end the turn. "
    "When asked whether it is done, check the helper result; if it is not back, say so in one "
    "sentence and end the turn. Never claim progress that the helper did not report.]"
)
_spoken_fired = 0


def _message_text(message: Any) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, (list, tuple)):
        return "\n".join(
            block if isinstance(block, str) else str(block.get("text") or "")
            for block in message
            if isinstance(block, (str, dict))
        )
    return ""


def _last_user_text(history: Any) -> str:
    if not isinstance(history, (list, tuple)):
        return ""
    for entry in reversed(history):
        if isinstance(entry, dict) and entry.get("role") == "user":
            return _message_text(entry.get("content"))
    return ""


def jarvis_spoken_rule(**kwargs: Any) -> Optional[Dict[str, str]]:
    global _spoken_fired
    try:
        if (os.environ.get("JARVIS_SPOKEN_RULE") or "").strip().lower() == "off":
            return None
        # A profile mismatch or malformed config must never inject operating words
        # into an unrelated persona.
        _config()
        if str(kwargs.get("parent_session_id") or "").strip():
            return None
        if _SPOKEN_MARKER not in _message_text(kwargs.get("user_message")) and _SPOKEN_MARKER not in _last_user_text(kwargs.get("conversation_history")):
            return None
        _spoken_fired += 1
        _write(_SPOKEN_RULE_FILE, {"at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "fired": _spoken_fired})
        return {"context": SPOKEN_RULE}
    except Exception as exc:
        logger.debug("Jarvis spoken-call rule skipped (%s)", type(exc).__name__)
        return None


_TOOLS: Tuple[Tuple[str, Callable, str, Dict[str, Any], List[str]], ...] = (
    (
        "jarvis_show_panel",
        jarvis_show_panel,
        "Show a short card on the Jarvis display during a conversation.",
        {
            "title": {"type": "string", "description": "Short card title."},
            "body": {"type": "string", "description": "Screen-sized plain text."},
            "kind": {"type": "string", "default": "card"},
            "ttl_s": {"type": "integer", "default": 20},
        },
        ["title", "body"],
    ),
    ("jarvis_status", jarvis_status, "Report the current Jarvis display state.", {}, []),
)


def register(ctx) -> None:
    register_tool = getattr(ctx, "register_tool", None)
    if callable(register_tool):
        for name, handler, description, properties, required in _TOOLS:
            parameters: Dict[str, Any] = {"type": "object", "properties": properties}
            if required:
                parameters["required"] = required
            try:
                register_tool(name=name, toolset="jarvis", schema={"name": name, "description": description, "parameters": parameters}, handler=handler, description=description, emoji="\U0001f4e1")
            except Exception as exc:
                logger.warning("Jarvis tool %s was not registered (%s)", name, type(exc).__name__)
    register_hook = getattr(ctx, "register_hook", None)
    if callable(register_hook):
        try:
            register_hook("pre_llm_call", jarvis_spoken_rule)
        except Exception as exc:
            logger.warning("Jarvis spoken-call hook was not registered (%s)", type(exc).__name__)


__all__ = ["SPOKEN_RULE", "jarvis_show_panel", "jarvis_spoken_rule", "jarvis_status", "register"]
