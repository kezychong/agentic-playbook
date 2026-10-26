from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import types
from pathlib import Path

import pytest


PACKAGE_BACKEND = Path(__file__).resolve().parents[1] / "payload" / "backend" / "hermes-jarvis"


class ProfileVerifier:
    def __init__(self) -> None:
        self.roots: dict[str, Path] = {}

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = types.ModuleType("hermes_cli.profiles")
        module.profile_matches_home = lambda name, home=None: (
            name in self.roots and Path(home).resolve() == self.roots[name].resolve()
        )
        monkeypatch.setitem(sys.modules, "hermes_cli.profiles", module)


@pytest.fixture
def verifier(monkeypatch: pytest.MonkeyPatch) -> ProfileVerifier:
    result = ProfileVerifier()
    result.install(monkeypatch)
    return result


def _base_config(profile_id: str, enabled: list[str] | None = None, sources=None, brains=None):
    return {
        "schema_version": 1,
        "profile_id": profile_id,
        "agent_name": "Chief",
        "owner_label": "Member",
        "timezone": "America/New_York",
        "enabled_sources": enabled or [],
        "sources": sources or {},
        "brains": brains or [],
    }


def _install_profile(tmp_path: Path, verifier: ProfileVerifier, profile_id: str, document=None, default=False):
    profile = tmp_path / ("runtime-home" if default else "profiles" / Path(profile_id))
    plugin = profile / "plugins" / "hermes-jarvis"
    shutil.copytree(PACKAGE_BACKEND, plugin)
    state = profile / "jarvis"
    state.mkdir(mode=0o700)
    config = state / "config.json"
    config.write_text(json.dumps(document or _base_config(profile_id)), encoding="utf-8")
    config.chmod(0o600)
    verifier.roots[profile_id] = profile
    return profile, plugin


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _api(plugin: Path, suffix: str):
    return _load(plugin / "dashboard" / "plugin_api.py", f"fixture_api_{suffix}")


def _tools(plugin: Path, suffix: str):
    return _load(plugin / "__init__.py", f"fixture_tools_{suffix}")


def test_config_profile_modes_and_permissions(tmp_path, verifier):
    named_root, named_plugin = _install_profile(tmp_path, verifier, "member-one")
    named = _load(named_plugin / "config.py", "fixture_config_named")
    loaded = named.load_config(named_plugin)
    assert loaded.profile_root == named_root.resolve()
    assert loaded.profile_id == "member-one"
    assert named_root.joinpath("jarvis").stat().st_mode & 0o777 == 0o700
    assert loaded.config_path.stat().st_mode & 0o777 == 0o600

    default_root, default_plugin = _install_profile(
        tmp_path / "default-case", verifier, "default", _base_config("default"), default=True
    )
    default = _load(default_plugin / "config.py", "fixture_config_default")
    assert default.load_config(default_plugin).profile_root == default_root.resolve()


def test_config_rejects_malformed_timezone_bool_schema_and_symlinks(tmp_path, verifier):
    root, plugin = _install_profile(tmp_path, verifier, "member-two")
    config_module = _load(plugin / "config.py", "fixture_config_errors")
    config_path = root / "jarvis" / "config.json"
    document = _base_config("member-two")
    document["timezone"] = "Nowhere/Invalid"
    config_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(config_module.ConfigError, match="timezone"):
        config_module.load_config(plugin)

    document["timezone"] = "UTC"
    document["schema_version"] = True
    config_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(config_module.ConfigError, match="schema_version"):
        config_module.load_config(plugin)

    real = root / "real-config.json"
    real.write_text(json.dumps(_base_config("member-two")), encoding="utf-8")
    config_path.unlink()
    config_path.symlink_to(real)
    with pytest.raises(config_module.ConfigError, match="symlink"):
        config_module.load_config(plugin)


def test_tools_and_backend_share_only_their_profile_state(tmp_path, verifier, monkeypatch):
    root_a, plugin_a = _install_profile(tmp_path / "a", verifier, "member-a")
    root_b, plugin_b = _install_profile(tmp_path / "b", verifier, "member-b")
    api_a, api_b = _api(plugin_a, "a"), _api(plugin_b, "b")
    tools_a = _tools(plugin_a, "a")
    monkeypatch.delitem(sys.modules, "hermes_dashboard_plugin_hermes-jarvis", raising=False)
    receipt = tools_a.jarvis_show_panel({"title": "A only", "body": "fixture"})
    assert "panel up" in receipt
    assert api_a.current_panel()["title"] == "A only"
    assert api_b.current_panel() is None
    assert (root_a / "jarvis" / "panel.json").is_file()
    assert (root_a / "jarvis" / "panel.json").stat().st_mode & 0o777 == 0o600
    assert not (root_b / "jarvis" / "panel.json").exists()

    monkeypatch.setitem(sys.modules, "hermes_dashboard_plugin_hermes-jarvis", api_b)
    assert tools_a._dashboard_module() is None


def test_disabled_sources_do_not_touch_files_or_launch_calendar(tmp_path, verifier, monkeypatch):
    forbidden = tmp_path / "must-not-open"
    document = _base_config(
        "member-three",
        [],
        {
            "agent_state": {"path": str(forbidden)},
            "next_meeting": {"service_account_path": str(forbidden), "hours": 36},
        },
    )
    _, plugin = _install_profile(tmp_path, verifier, "member-three", document)
    api = _api(plugin, "disabled")
    monkeypatch.setattr(api, "_read_text", lambda *_: (_ for _ in ()).throw(AssertionError("file accessed")))
    monkeypatch.setattr(api.subprocess, "run", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("process launched")))
    state = api.read_state(force=True)
    assert state["agent_state"]["status"] == "disabled"
    assert state["next_meeting"]["status"] == "disabled"


def test_selected_missing_source_is_honest_not_zero(tmp_path, verifier):
    missing = tmp_path / "absent.json"
    document = _base_config(
        "member-four", ["overnight_jobs"], {"overnight_jobs": {"path": str(missing)}}
    )
    _, plugin = _install_profile(tmp_path, verifier, "member-four", document)
    block = _api(plugin, "missing").read_state(force=True)["overnight_jobs"]
    assert block["status"] == "missing"
    assert block["total"] is None
    assert block["ok"] is None

    document = _base_config("member-four", ["log"], {})
    (plugin.parents[1] / "jarvis" / "config.json").write_text(json.dumps(document), encoding="utf-8")
    unconfigured = _api(plugin, "unconfigured").read_state(force=True)
    assert unconfigured["log"] is None
    assert unconfigured["log_note"] == "unconfigured"


def _fixture_db(path: Path, current: float) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE async_delegations (
          delegation_id TEXT, origin_session TEXT, state TEXT, dispatched_at REAL,
          completed_at REAL, updated_at REAL, task_json TEXT, event_json TEXT,
          result_json TEXT, delivery_state TEXT
        );
        CREATE TABLE session_model_usage (
          model TEXT, api_call_count INTEGER, input_tokens INTEGER, output_tokens INTEGER,
          cache_read_tokens INTEGER, estimated_cost_usd REAL, actual_cost_usd REAL,
          cost_status TEXT, last_seen REAL
        );
        """
    )
    connection.execute(
        "INSERT INTO async_delegations VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("job-1", "chat", "completed", current - 2, current - 1, current - 1,
         '{"goal":"Check fixture"}', '{}', '{"summary":"Done"}', "delivered"),
    )
    connection.execute(
        "INSERT INTO async_delegations VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("job-stale", "chat", "running", current - 4000, None, current - 1900,
         '{"goal":"Old running fixture"}', '{}', '{}', "pending"),
    )
    connection.execute(
        "INSERT INTO session_model_usage VALUES (?,?,?,?,?,?,?,?,?)",
        ("model-fixture", 2, 10, 20, 3, 0.5, 0.0, "estimated", current),
    )
    connection.execute(
        "INSERT INTO session_model_usage VALUES (?,?,?,?,?,?,?,?,?)",
        ("model-unknown", 1, 4, 6, 1, 0.0, 0.0, "unknown", current),
    )
    connection.commit()
    connection.close()


def test_sqlite_sources_are_read_only_and_closed(tmp_path, verifier, monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    moment = datetime(2026, 9, 22, 12, 0, tzinfo=ZoneInfo("America/New_York"))
    database = tmp_path / "state.db"
    _fixture_db(database, moment.timestamp())
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    document = _base_config(
        "member-five",
        ["agent_helpers", "spend"],
        {"agent_helpers": {"path": str(database)}, "spend": {"path": str(database)}},
    )
    _, plugin = _install_profile(tmp_path, verifier, "member-five", document)
    api = _api(plugin, "database")
    monkeypatch.setattr(api, "_local_now", lambda: moment)
    monkeypatch.setattr(api, "_now_s", lambda: moment.timestamp())
    state = api.read_state(force=True)
    assert state["agent_helpers"]["recent"][0]["goal"] == "Check fixture"
    assert state["agent_helpers"]["recent"][0]["delivered"] is True
    assert state["agent_helpers"]["running"] == []
    assert state["agent_helpers"]["todayCount"] == 2
    assert state["spend"]["today"]["totalCalls"] == 3
    models = {item["model"]: item for item in state["spend"]["today"]["byModel"]}
    assert models["model-fixture"]["cacheReadTokens"] == 3
    assert models["model-fixture"]["costUsd"] == 0.5
    assert models["model-unknown"]["costUsd"] is None
    assert state["spend"]["today"]["costUsd"] is None
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    database.rename(tmp_path / "moved.db")


def test_source_parity_for_briefs_lever_scoreboard_and_today(tmp_path, verifier):
    state_file = tmp_path / "STATE.md"
    briefs = tmp_path / "BRIEFS.md"
    lever = tmp_path / "LEVER.md"
    scoreboard = tmp_path / "SCOREBOARD.md"
    today = tmp_path / "TODAY.md"
    state_file.write_text(
        "# State\n## In flight\n- [row-1] Shipping | next: Review | Member | 2099-01-01 | fresh\n"
        "## Recently closed\n- Finished one\n",
        encoding="utf-8",
    )
    briefs.write_text(
        "## [row-1] Review package\n- what: A portable display\n- why: Clear status\n- do: Read it\n",
        encoding="utf-8",
    )
    lever.write_text("---\npm_current_one_lever: Ship the member package\n---\n", encoding="utf-8")
    scoreboard.write_text("# Weekly Scoreboard\nCalls: 3\nReviews: 2\n", encoding="utf-8")
    today.write_text(
        "---\ndate: 2099-01-01\nbuild_task: Verify package\nbuild_status: active\nbuild_next_action: Run tests\n---\n"
        "## Today\nFinish the portable backend.\n",
        encoding="utf-8",
    )
    sources = {
        "agent_state": {"path": str(state_file), "briefs_path": str(briefs)},
        "lever": {"path": str(lever)},
        "scoreboard": {"path": str(scoreboard)},
        "today_plan": {"path": str(today)},
    }
    document = _base_config("member-six", list(sources), sources)
    _, plugin = _install_profile(tmp_path, verifier, "member-six", document)
    state = _api(plugin, "parity").read_state(force=True)
    row = state["agent_state"]["rows"][0]
    assert row["where"] == "Shipping"
    assert row["brief"]["what"] == "A portable display"
    assert state["agent_state"]["briefs"]["matched"] == 1
    assert state["lever"]["text"] == "Ship the member package"
    assert state["scoreboard"]["headline"] == "Weekly Scoreboard"
    assert state["scoreboard"]["lines"] == ["Calls: 3", "Reviews: 2"]
    assert state["today_plan"]["headline"] == "Finish the portable backend."
    assert state["today_plan"]["lever"]["text"] == "Ship the member package"


def test_spoken_hook_registers_once_and_fires_only_for_voice(tmp_path, verifier, monkeypatch):
    root, plugin = _install_profile(tmp_path, verifier, "member-seven")
    tools = _tools(plugin, "hook")

    class Context:
        def __init__(self):
            self.tools, self.hooks = [], []

        def register_tool(self, **kwargs):
            self.tools.append(kwargs)

        def register_hook(self, name, handler):
            self.hooks.append((name, handler))

    context = Context()
    tools.register(context)
    assert len(context.tools) == 2
    assert [name for name, _ in context.hooks] == ["pre_llm_call"]
    assert tools.jarvis_spoken_rule(user_message="typed") is None
    spoken = tools.jarvis_spoken_rule(user_message="delegation from a live spoken conversation")
    assert "delegate_task once" in spoken["context"]
    assert tools.jarvis_spoken_rule(
        user_message="delegation from a live spoken conversation", parent_session_id="child"
    ) is None
    receipt = json.loads((root / "jarvis" / "spoken-rule.json").read_text())
    assert receipt["fired"] == 1
    monkeypatch.setenv("JARVIS_SPOKEN_RULE", "off")
    assert tools.jarvis_spoken_rule(user_message="delegation from a live spoken conversation") is None
    monkeypatch.delenv("JARVIS_SPOKEN_RULE")
    (root / "jarvis" / "config.json").write_text("{broken", encoding="utf-8")
    assert tools.jarvis_spoken_rule(user_message="delegation from a live spoken conversation") is None


def test_status_does_not_claim_backend_without_state_files(tmp_path, verifier):
    _, plugin = _install_profile(tmp_path, verifier, "member-status")
    sentence = _tools(plugin, "status").jarvis_status()
    assert "no presence file yet" in sentence
    assert "backend v" not in sentence


def test_calendar_time_conversion_respects_daylight_saving():
    calendar = _load(PACKAGE_BACKEND / "dashboard" / "jarvis_calendar.py", "fixture_calendar")
    zone = calendar.ZoneInfo("America/New_York")
    assert calendar._iso("2026-07-01T12:00:00Z", False, zone).endswith("-04:00")
    assert calendar._iso("2026-12-01T12:00:00Z", False, zone).endswith("-05:00")


def test_websocket_auth_and_origin_fail_closed(tmp_path, verifier, monkeypatch):
    _, plugin = _install_profile(tmp_path, verifier, "member-eight")
    api = _api(plugin, "auth")
    checks = types.SimpleNamespace(
        _ws_auth_ok=lambda _ws: False,
        _ws_request_is_allowed=lambda _ws: True,
    )
    monkeypatch.setattr(api.importlib, "import_module", lambda _name: checks)
    assert api.ws_gate_reason(object()) == "credential"
    checks._ws_auth_ok = lambda _ws: True
    checks._ws_request_is_allowed = lambda _ws: False
    assert api.ws_gate_reason(object()) == "origin"
    monkeypatch.setattr(api.importlib, "import_module", lambda _name: (_ for _ in ()).throw(ImportError()))
    assert api.ws_gate_reason(object()) == "ws auth unavailable"


def test_watch_loop_broadcasts_tool_written_file_panel(tmp_path, verifier, monkeypatch):
    root, plugin = _install_profile(tmp_path, verifier, "member-nine")
    api = _api(plugin, "watch")
    panel = {
        "id": "file-panel-1",
        "title": "From tool",
        "body": "fixture",
        "ttl_s": 20,
        "at": api._now_ms(),
    }
    path = root / "jarvis" / "panel.json"
    path.write_text(json.dumps(panel), encoding="utf-8")
    path.chmod(0o600)
    sent = []

    class Client:
        async def send_json(self, frame):
            sent.append(frame)
            api.JARVIS_STATE.clients.clear()

    api.JARVIS_STATE.clients.add(Client())
    async def immediate(_seconds):
        return None

    monkeypatch.setattr(api.asyncio, "sleep", immediate)
    asyncio.run(api._watch_loop())
    assert any(frame["type"] == "panel" and frame["data"]["id"] == "file-panel-1" for frame in sent)


def test_mirror_route_reports_explicit_unavailable(tmp_path, verifier, monkeypatch):
    _, plugin = _install_profile(tmp_path, verifier, "member-ten")
    api = _api(plugin, "mirror")
    monkeypatch.setattr(api, "_MIRROR_HTML", tmp_path / "missing.html")
    response = api.get_mirror()
    assert response.status_code == 503
    assert b"unavailable" in response.body


def test_mirror_serves_packaged_html_and_refuses_symlink(tmp_path, verifier, monkeypatch):
    _, plugin = _install_profile(tmp_path, verifier, "member-mirror")
    api = _api(plugin, "mirror_present")
    mirror = tmp_path / "mirror.html"
    mirror.write_text("<!doctype html><title>Chief mirror</title>", encoding="utf-8")
    monkeypatch.setattr(api, "_MIRROR_HTML", mirror)
    response = api.get_mirror()
    assert response.status_code == 200
    assert response.media_type == "text/html"
    assert response.body == mirror.read_bytes()
    alias = tmp_path / "alias.html"
    alias.symlink_to(mirror)
    monkeypatch.setattr(api, "_MIRROR_HTML", alias)
    assert api.get_mirror().status_code == 503


def test_state_reader_rejects_cross_profile_symlink(tmp_path, verifier):
    root_a, plugin_a = _install_profile(tmp_path / "a", verifier, "member-link-a")
    root_b, _ = _install_profile(tmp_path / "b", verifier, "member-link-b")
    foreign = root_b / "jarvis" / "panel.json"
    foreign.write_text(
        json.dumps({"id": "private", "title": "Foreign", "body": "hidden", "ttl_s": 60, "at": 1}),
        encoding="utf-8",
    )
    foreign.chmod(0o600)
    (root_a / "jarvis" / "panel.json").symlink_to(foreign)
    assert _api(plugin_a, "state_symlink").current_panel() is None


def test_atomic_writer_ignores_predictable_temp_symlink(tmp_path, verifier):
    root, plugin = _install_profile(tmp_path, verifier, "member-atomic")
    config_module = _load(plugin / "config.py", "fixture_config_atomic")
    config = config_module.load_config(plugin)
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("keep", encoding="utf-8")
    guessed = root / "jarvis" / f".status.json.{os.getpid()}.tmp"
    guessed.symlink_to(sentinel)
    assert config_module.write_json_atomic(config, "status.json", {"ok": True})
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not (root / "jarvis" / "status.json").is_symlink()


def test_invalid_config_suppresses_cached_presence_and_panel(tmp_path, verifier):
    root, plugin = _install_profile(tmp_path, verifier, "member-invalid-cache")
    api = _api(plugin, "invalid_cache")
    api.store_presence({"mode": "ready"})
    api.push_panel("Private cached panel")
    (root / "jarvis" / "config.json").write_text("{broken", encoding="utf-8")
    assert api.read_state(force=True)["config"]["status"] == "invalid"
    assert api.read_presence()["presence"] is None
    assert api.current_panel() is None


def test_original_shaped_jobs_scoreboard_brains_calendar_and_secret_scrub(tmp_path, verifier):
    import time

    now = time.time()
    jobs = tmp_path / "jobs.json"
    jobs.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "night-1",
                        "name": "Night task",
                        "enabled": True,
                        "state": "paused",
                        "last_run_at": now,
                        "last_status": "failed",
                        "last_error": "Bearer hidden-value",
                        "next_run_at": now + 3600,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    streaks = tmp_path / "streaks.md"
    day = __import__("datetime").datetime.now().date().isoformat()
    streaks.write_text(
        "---\nbuild_streak: 4\ncontent_streak: 3\nbest_build_streak: 8\n"
        "lessons_shipped_since_start: 12\n---\n"
        f"- {day} · build ✅ · content ❌ · useful note\n",
        encoding="utf-8",
    )
    brain = tmp_path / "brain"
    nested = brain / "nested"
    nested.mkdir(parents=True)
    latest = nested / "note.md"
    latest.write_text("fixture", encoding="utf-8")
    sources = {
        "overnight_jobs": {"path": str(jobs)},
        "one_thing_scoreboard": {"path": str(streaks)},
    }
    document = _base_config(
        "member-parity",
        ["overnight_jobs", "one_thing_scoreboard", "brains"],
        sources,
        [{"id": "brain-one", "label": "Brain one", "path": str(brain)}],
    )
    _, plugin = _install_profile(tmp_path / "profile", verifier, "member-parity", document)
    api = _api(plugin, "full_parity")
    state = api.read_state(force=True)
    overnight = state["overnight_jobs"]
    assert overnight["pausedCount"] == 1
    assert overnight["failed"][0]["id"] == "night-1"
    assert overnight["failed"][0]["lastStatus"] == "failed"
    assert "hidden-value" not in overnight["failed"][0]["error"]
    score = state["one_thing_scoreboard"]
    assert score["buildStreak"] == 4
    assert score["bestBuildStreak"] == 8
    assert score["lessonsShipped"] == 12
    assert score["lastDays"][0]["build"] is True
    assert score["lastDays"][0]["content"] is False
    assert score["lastDays"][0]["note"] == "useful note"
    assert state["brains"][0]["mirror"] == str(brain.resolve())
    assert state["brains"][0]["mirror_updated"] is not None
    assert set(api.SOURCE_PARITY) == {
        "agent_state", "agent_helpers", "next_meeting", "today_plan", "overnight_jobs",
        "one_thing_scoreboard", "spend", "lever", "brains", "scoreboard", "log",
    }
    assert "•••" in api._strip_secrets("Basic a-long-secret-value --token other-hidden-value")

    timed = (api._local_now() + api.timedelta(minutes=30)).isoformat(timespec="seconds")
    all_day = api._local_now().date().isoformat()
    calendar = api._calendar_block_from(
        {"events": [
            {"title": "All day", "start": all_day, "end": all_day, "calendar": "A", "allDay": True},
            {"title": "Timed", "start": timed, "end": timed, "calendar": "B", "allDay": False},
        ]}
    )
    assert calendar["next"]["title"] == "Timed"
    assert calendar["next"]["calendar"] == "B"
    assert calendar["next"]["end"] == timed


def test_optional_http_fallback_binds_profile_before_sending_panel(tmp_path, verifier, monkeypatch):
    root, plugin = _install_profile(tmp_path, verifier, "member-http")
    tools = _tools(plugin, "http")
    monkeypatch.setenv("JARVIS_DASHBOARD_URL", "https://dashboard.example")
    monkeypatch.setenv("JARVIS_DASHBOARD_COOKIE", "session=fixture-secret")
    calls = []

    def mismatch(method, path, payload, base, cookie):
        calls.append((method, path, payload, base, cookie))
        return 200, {"profile_id": "different-profile"}

    monkeypatch.setattr(tools, "_raw_request", mismatch)
    refused = tools.jarvis_show_panel({"title": "Bound panel", "body": "fixture"})
    assert "does not match" in refused
    assert [(method, path) for method, path, *_ in calls] == [("GET", "/status")]
    assert calls[0][2] is None
    assert not (root / "jarvis" / "panel.json").exists()

    calls.clear()

    def matching(method, path, payload, base, cookie):
        calls.append((method, path, payload, base, cookie))
        if path == "/status":
            return 200, {"profile_id": "member-http", "version": "fixture"}
        return 200, {
            "panel": {"id": "remote-1", "title": payload["title"], "kind": "card", "ttl": 20},
            "clients": 1,
        }

    monkeypatch.setattr(tools, "_raw_request", matching)
    receipt = tools.jarvis_show_panel({"title": "Bound panel", "body": "fixture"})
    assert "remote-1" in receipt
    assert [(method, path) for method, path, *_ in calls] == [
        ("GET", "/status"), ("POST", "/panel")
    ]
    assert calls[1][2]["body"] == "fixture"

    calls.clear()
    monkeypatch.setenv("JARVIS_DASHBOARD_URL", "http://remote.example")
    refused = tools.jarvis_show_panel({"title": "No send", "body": "fixture"})
    assert "HTTPS" in refused
    assert calls == []


def test_invalid_config_websocket_sends_no_cached_frames_despite_status_cap(tmp_path, verifier, monkeypatch):
    root, plugin = _install_profile(tmp_path, verifier, "member-ws-cache")
    api = _api(plugin, "ws_cache")
    api.store_presence({"mode": "private"})
    api.push_panel("Private panel")
    assert api.write_status_file(force=True)
    assert api.write_status_file() is False
    (root / "jarvis" / "config.json").write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(api, "ws_gate_reason", lambda _ws: None)

    class Socket:
        def __init__(self):
            self.accepted = False
            self.sent = []
            self.closed = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, frame):
            self.sent.append(frame)

        async def close(self, **kwargs):
            self.closed.append(kwargs)

    socket = Socket()
    asyncio.run(api.events(socket))
    assert socket.accepted is False
    assert socket.sent == []
    assert socket.closed and socket.closed[0]["code"] == 1008
    assert api.JARVIS_STATE.presence is None
    assert api.JARVIS_STATE.panel is None


def test_config_change_invalidates_per_reader_cache(tmp_path, verifier):
    today = tmp_path / "today.md"
    lever = tmp_path / "lever.md"
    today.write_text("---\ndate: 2099-01-01\n---\n## Today\nFixture plan\n", encoding="utf-8")
    lever.write_text("---\npm_current_one_lever: Private lever\n---\n", encoding="utf-8")
    sources = {"today_plan": {"path": str(today)}, "lever": {"path": str(lever)}}
    document = _base_config("member-cache-change", ["today_plan", "lever"], sources)
    root, plugin = _install_profile(tmp_path / "profile", verifier, "member-cache-change", document)
    api = _api(plugin, "cache_change")
    assert api.read_state(force=True)["today_plan"]["lever"]["text"] == "Private lever"

    document["enabled_sources"] = ["today_plan"]
    config_path = root / "jarvis" / "config.json"
    config_path.write_text(json.dumps(document), encoding="utf-8")
    current = config_path.stat().st_mtime_ns
    os.utime(config_path, ns=(current + 1_000_000, current + 1_000_000))
    changed = api.read_state(force=True)
    assert changed["lever"] is None
    assert changed["today_plan"]["lever"] is None


def test_http_status_refuses_followup_auth_or_server_error(tmp_path, verifier, monkeypatch):
    _, plugin = _install_profile(tmp_path, verifier, "member-http-errors")
    tools = _tools(plugin, "http_errors")
    monkeypatch.setenv("JARVIS_DASHBOARD_URL", "https://dashboard.example")
    monkeypatch.setenv("JARVIS_DASHBOARD_COOKIE", "session=fixture-secret")
    replies = iter(
        [
            (200, {"profile_id": "member-http-errors"}),
            (401, None),
            (503, None),
        ]
    )
    monkeypatch.setattr(tools, "_raw_request", lambda *_args: next(replies))
    assert "auth refused" in tools.jarvis_status()

    replies = iter(
        [
            (200, {"profile_id": "member-http-errors"}),
            (200, {"presence": None}),
            (503, None),
        ]
    )
    monkeypatch.setattr(tools, "_raw_request", lambda *_args: next(replies))
    assert "state is unavailable" in tools.jarvis_status()


def test_public_settings_drive_member_choices_without_source_paths(tmp_path, verifier):
    document = _base_config("member-display", ["today_plan"],
        {"next_meeting": {"service_account_path": str(tmp_path / "private-credential.json")}},
        [{"id": "work", "label": "Work", "path": str(tmp_path / "private-brain")}])
    _, plugin = _install_profile(tmp_path, verifier, "member-display", document)
    api = _api(plugin, "display-settings")
    state = api.read_state(force=True)
    settings = state["settings"]
    assert settings == api.read_status()["settings"]
    assert settings["profile_id"] == "member-display"
    assert settings["enabled_sources"] == ["today_plan"]
    assert settings["brains"] == [{"id": "work", "label": "Work"}]
    encoded = json.dumps(settings)
    assert "private-credential" not in encoded and "private-brain" not in encoded
    assert "sources" not in settings and "path" not in settings["brains"][0]
    config_file = plugin.parent.parent / "jarvis" / "config.json"
    document["agent_name"] = "Nova"
    document["timezone"] = "Europe/London"
    document["enabled_sources"] = []
    config_file.write_text(json.dumps(document))
    refreshed = api.read_state()["settings"]
    assert refreshed["agent_name"] == "Nova"
    assert refreshed["timezone"] == "Europe/London"
    assert refreshed["enabled_sources"] == []
    config_file.write_text("{broken")
    assert "settings" not in api.read_state()
    assert "settings" not in api.read_status()


def test_explicit_foreign_profile_selector_denies_http_and_socket(tmp_path, verifier):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    _, plugin = _install_profile(tmp_path, verifier, "member-route")
    api = _api(plugin, "route-selector")
    app = FastAPI()
    app.include_router(api.router, prefix="/api/plugins/hermes-jarvis")
    with TestClient(app) as client:
        base = "/api/plugins/hermes-jarvis"
        assert client.get(base + "/status?profile=member-route").status_code == 200
        for query in ["profile=someone-else", "profile=member-route&profile=someone-else", "profile="]:
            assert client.get(base + "/state?" + query).status_code == 403
            assert client.post(base + "/presence?" + query, json={"private": "forbidden"}).status_code == 403
            with pytest.raises(WebSocketDisconnect) as err:
                with client.websocket_connect(base + "/events?" + query):
                    pass
            assert err.value.code == 1008
        assert api.read_presence()["presence"] is None


def test_prospective_config_and_independent_box_choices(tmp_path, verifier):
    root, plugin = _install_profile(tmp_path, verifier, "member-boxes")
    module = _load(plugin / "config.py", "fixture_config_boxes")
    document = _base_config("member-boxes", ["agent_state"])
    document["enabled_boxes"] = ["waiting_on_you"]
    parsed = module.validate_config_document(document, root)
    assert parsed.enabled_boxes == frozenset({"waiting_on_you"})
    config_file = root / "jarvis" / "config.json"
    config_file.write_text(json.dumps(document))
    api = _api(plugin, "boxes")
    assert api.read_state()["settings"]["enabled_boxes"] == ["waiting_on_you"]
    document["enabled_boxes"] = ["unknown"]
    with pytest.raises(module.ConfigError, match="enabled_boxes"):
        module.validate_config_document(document, root)
    clean = tmp_path / "clean-home"
    clean.mkdir()
    verifier.roots["default"] = clean
    base = _base_config("default")
    validated = module.validate_config_document(base, clean)
    assert validated.profile_id == "default"
    assert list(clean.iterdir()) == []


def test_http_origin_uses_host_policy_and_fails_closed(tmp_path, verifier, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    _, plugin = _install_profile(tmp_path, verifier, "member-origin")
    api = _api(plugin, "origin")
    app = FastAPI()
    app.include_router(api.router, prefix="/api/plugins/hermes-jarvis")
    host = types.ModuleType("fixture_host_origin")
    host._ws_host_origin_reason = lambda connection: None if connection.headers["origin"] == "https://allowed.example" else "origin_mismatch"
    monkeypatch.setitem(sys.modules, host.__name__, host)
    monkeypatch.setattr(api, "_HOST_WS_AUTH_MODULE", host.__name__)
    with TestClient(app) as client:
        route = "/api/plugins/hermes-jarvis/status"
        assert client.get(route).status_code == 200
        assert client.get(route, headers={"Origin": "https://allowed.example"}).status_code == 200
        assert client.get(route, headers={"Origin": "https://foreign.example"}).status_code == 403
        del host._ws_host_origin_reason
        assert client.get(route, headers={"Origin": "https://allowed.example"}).status_code == 403


def test_backend_version_is_the_released_v1_in_both_files():
    """plugin.yaml and the dashboard manifest ship the same released version."""
    import re

    raw = (PACKAGE_BACKEND / "plugin.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^version:\s*(\S+)\s*$", raw)
    assert match, "plugin.yaml must declare a version"
    yaml_version = match.group(1).strip('"\'')
    manifest = json.loads((PACKAGE_BACKEND / "dashboard" / "manifest.json").read_text(encoding="utf-8"))
    assert yaml_version == manifest["version"] == "1.0.0"
    # A released pack carries no pre-release or build suffix.
    assert re.fullmatch(r"\d+\.\d+\.\d+", yaml_version)
