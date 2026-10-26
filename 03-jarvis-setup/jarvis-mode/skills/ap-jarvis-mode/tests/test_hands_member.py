"""Member-package checks for configurable hands and the optional driver helper.

These checks are local only. They inspect defaults and the dry-run paths; they
never contact a host, start a native driver, or change /Applications.
"""

import importlib.util
import json
import os
import subprocess
import tempfile
import shutil
import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader

import pytest

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[1]
HANDS = ROOT / "payload" / "hands" / "ap-macbook-hands"
INSTALL = ROOT / "payload" / "bin" / "install-hands.sh"
DRIVER_INSTALL = ROOT / "payload" / "hands" / "install-cua-driver.sh"
HANDS_TRANSACTION = ROOT / "payload" / "hands" / "install-hands-transaction.py"
MIRROR = ROOT / "payload" / "bin" / "jarvis-mirror"
TOGGLE = ROOT / "payload" / "bin" / "jarvis-toggle"


def load_hands():
    loader = SourceFileLoader("member_hands", str(HANDS))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def clean_env():
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("JARVIS_HANDS_")
        and not key.startswith("JARVIS_CUA_DRIVER_")
    }


def write_config(tmp_path, profile, hosts=None):
    profile_home = tmp_path / "profiles" / profile
    hands_dir = profile_home / "jarvis" / "hands"
    hands_dir.mkdir(parents=True)
    path = hands_dir / "config.json"
    path.write_text(json.dumps({
        "schema": 1,
        "profile": profile,
        "profile_home": str(profile_home),
        "hosts": hosts or ["main-host"],
        "driver": "/Applications/CuaDriver.app/Contents/MacOS/cua-driver",
        "state": str(hands_dir / "state"),
    }), encoding="utf-8")
    path.chmod(0o600)
    return path


def test_durable_configs_have_no_author_host_and_profile_scoped_state(tmp_path):
    module = load_hands()
    alpha = dict(JARVIS_HANDS_CONFIG=str(write_config(tmp_path, "alpha")))
    beta = dict(JARVIS_HANDS_CONFIG=str(write_config(tmp_path, "beta")))
    first = module.Hands(alpha)
    second = module.Hands(beta)
    assert first.hosts == ["main-host"]
    assert first.state != second.state
    assert first.state.endswith(os.path.join("alpha", "jarvis", "hands", "state"))
    assert second.state.endswith(os.path.join("beta", "jarvis", "hands", "state"))


def test_explicit_member_configuration_is_used(tmp_path):
    module = load_hands()
    state = tmp_path / "chosen-state"
    hands = module.Hands({
        "JARVIS_HANDS_HOSTS": "main-host,backup-host",
        "JARVIS_HANDS_DRIVER": "/custom/CuaDriver",
        "JARVIS_HANDS_STATE": str(state),
        "JARVIS_HANDS_PROFILE": "selected",
    })
    assert hands.hosts == ["main-host", "backup-host"]
    assert hands.driver == "/custom/CuaDriver"
    assert hands.state == str(state)
    assert hands.profile == "selected"


def test_invalid_profile_cannot_escape_state_root(tmp_path):
    module = load_hands()
    with pytest.raises(module.ConfigurationError):
        module.Hands({
            "JARVIS_HANDS_PROFILE": "../outside",
            "JARVIS_HANDS_HOSTS": "main-host",
            "JARVIS_HANDS_STATE": str(tmp_path / "state"),
        })


def test_invalid_profiles_do_not_collapse_to_one_identity(tmp_path):
    module = load_hands()
    for profile in ("../alpha", "../beta"):
        with pytest.raises(module.ConfigurationError):
            module.Hands({"JARVIS_HANDS_PROFILE": profile,
                          "JARVIS_HANDS_HOSTS": "main-host",
                          "JARVIS_HANDS_STATE": str(tmp_path / profile.replace("/", "_"))})


def test_status_without_durable_or_explicit_config_is_refused(tmp_path):
    env = clean_env()
    env.update({"JARVIS_HANDS_STATE": str(tmp_path / "state")})
    result = subprocess.run(
        [str(HANDS), "status", "--json"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert '"error": "configuration"' in result.stdout
    assert result.stderr == ""


def test_hands_installer_requires_selected_host_and_profile(tmp_path):
    env = clean_env()
    env.update({"JARVIS_HANDS_MINI": "", "JARVIS_HANDS_PROFILE": "",
                "JARVIS_HANDS_PROFILE_HOME": "", "JARVIS_HANDS_HOSTS": ""})
    result = subprocess.run(
        ["bash", str(INSTALL), "--dry-run"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "JARVIS_HANDS_MINI" in result.stderr


def test_hands_installer_dry_run_uses_selected_profile(tmp_path):
    env = clean_env()
    env.update({"JARVIS_HANDS_MINI": "member-agent-host", "JARVIS_HANDS_PROFILE": "selected",
                "JARVIS_HANDS_PROFILE_HOME": "/tmp/member/profiles/selected",
                "JARVIS_HANDS_HOSTS": "main-computer"})
    result = subprocess.run(
        ["bash", str(INSTALL), "--dry-run"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "/tmp/member/profiles/selected/skills/agents/ap-macbook-hands" in result.stdout
    assert "/tmp/member/profiles/selected/jarvis/hands/config.json" in result.stdout
    assert "StrictHostKeyChecking=yes" in result.stdout
    assert "DRY RUN" in result.stdout


def test_hands_installer_quotes_profile_home_with_spaces():
    env = clean_env()
    env.update({"JARVIS_HANDS_MINI": "member-agent-host", "JARVIS_HANDS_PROFILE": "selected",
                "JARVIS_HANDS_PROFILE_HOME": "/tmp/member root/profiles/selected",
                "JARVIS_HANDS_HOSTS": "main-computer"})
    result = subprocess.run(["bash", str(INSTALL), "--dry-run"], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "/tmp/member root/profiles/selected" in result.stdout
    assert "member\\ root" in result.stdout


def make_transaction_stage(profile_home, profile, stage, unsafe_skill_link=False):
    stage.mkdir(parents=True)
    (stage / "ap-macbook-hands").write_text("new command", encoding="utf-8")
    (stage / "install-hands-transaction.py").write_text("new helper", encoding="utf-8")
    (stage / "skill").mkdir()
    (stage / "skill" / "SKILL.md").write_text(
        "run %s/jarvis/hands/bin/ap-macbook-hands\n" % profile_home, encoding="utf-8")
    if unsafe_skill_link:
        (stage / "skill" / "escape").symlink_to("/tmp")
    hands = profile_home / "jarvis" / "hands"
    (stage / "config.json").write_text(json.dumps({
        "schema": 1, "profile": profile, "profile_home": str(profile_home),
        "hosts": ["main-computer"],
        "driver": "/Applications/CuaDriver.app/Contents/MacOS/cua-driver",
        "state": str(hands / "state"),
    }), encoding="utf-8")


def test_profile_transaction_supports_space_in_parent_and_undo(tmp_path):
    profile = "selected"
    profile_home = tmp_path / "parent with space" / profile
    profile_home.mkdir(parents=True)
    hands = profile_home / "jarvis" / "hands"
    old_command = hands / "bin" / "ap-macbook-hands"
    old_skill = profile_home / "skills" / "agents" / "ap-macbook-hands"
    old_command.parent.mkdir(parents=True)
    old_skill.mkdir(parents=True)
    old_command.write_text("old command", encoding="utf-8")
    (old_skill / "SKILL.md").write_text("old skill", encoding="utf-8")
    stage = profile_home / ".jarvis-hands-stage-test"
    make_transaction_stage(profile_home, profile, stage)
    sealed = subprocess.run([str(HANDS_TRANSACTION), "seal", str(profile_home), profile,
                             str(stage)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10)
    assert sealed.returncode == 0, sealed.stderr
    assert old_command.read_text(encoding="utf-8") == "new command"
    assert (hands / "config.json").stat().st_mode & 0o777 == 0o600
    assert (hands / "install-receipt.json").exists()
    rerun_stage = profile_home / ".jarvis-hands-stage-rerun"
    make_transaction_stage(profile_home, profile, rerun_stage)
    rerun = subprocess.run([str(HANDS_TRANSACTION), "seal", str(profile_home), profile,
                            str(rerun_stage)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, timeout=10)
    assert rerun.returncode == 1
    assert old_command.read_text(encoding="utf-8") == "new command"
    undone = subprocess.run([str(HANDS_TRANSACTION), "undo", str(profile_home), profile],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10)
    assert undone.returncode == 0, undone.stderr
    assert old_command.read_text(encoding="utf-8") == "old command"
    assert (old_skill / "SKILL.md").read_text(encoding="utf-8") == "old skill"
    assert not (hands / "install-receipt.json").exists()


def test_profile_transaction_rolls_back_when_staged_tree_is_unsafe(tmp_path):
    profile = "selected"
    profile_home = tmp_path / profile
    profile_home.mkdir()
    old = profile_home / "jarvis" / "hands" / "bin" / "ap-macbook-hands"
    old.parent.mkdir(parents=True)
    old.write_text("old command", encoding="utf-8")
    stage = profile_home / ".jarvis-hands-stage-test"
    make_transaction_stage(profile_home, profile, stage, unsafe_skill_link=True)
    result = subprocess.run([str(HANDS_TRANSACTION), "seal", str(profile_home), profile,
                             str(stage)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10)
    assert result.returncode == 1
    assert old.read_text(encoding="utf-8") == "old command"
    assert not (profile_home / "jarvis" / "hands" / "install-receipt.json").exists()


def test_profile_transaction_rejects_intermediate_profile_symlink(tmp_path):
    real_parent = tmp_path / "real"; real_parent.mkdir()
    (real_parent / "selected").mkdir()
    linked_parent = tmp_path / "linked"; linked_parent.symlink_to(real_parent, target_is_directory=True)
    result = subprocess.run([str(HANDS_TRANSACTION), "seal",
                             str(linked_parent / "selected"), "selected",
                             str(linked_parent / "selected" / "stage")],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10)
    assert result.returncode == 1
    assert "symlink" in result.stderr


@pytest.mark.parametrize("name,value", [
    ("JARVIS_HANDS_PROFILE", 'x"; false; #'),
    ("JARVIS_HANDS_MINI", "-oProxyCommand=none"),
])
def test_hands_installer_rejects_shell_and_ssh_option_inputs(tmp_path, name, value):
    env = clean_env()
    env.update({"JARVIS_HANDS_MINI": "agent-host", "JARVIS_HANDS_PROFILE": "selected",
                "JARVIS_HANDS_PROFILE_HOME": "/tmp/member/profiles/selected",
                "JARVIS_HANDS_HOSTS": "main-computer"})
    env[name] = value
    result = subprocess.run(["bash", str(INSTALL), "--dry-run"], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10)
    assert result.returncode == 2
    assert "DRY RUN" not in result.stdout


def test_state_symlink_is_refused_and_existing_modes_are_tightened(tmp_path):
    module = load_hands()
    outside = tmp_path / "outside"
    outside.mkdir()
    state = tmp_path / "state"
    state.symlink_to(outside, target_is_directory=True)
    hands = module.Hands({"JARVIS_HANDS_PROFILE": "selected",
                          "JARVIS_HANDS_HOSTS": "main-host",
                          "JARVIS_HANDS_STATE": str(state)})
    with pytest.raises(module.ConfigurationError):
        hands._dir()
    assert list(outside.iterdir()) == []

    state.unlink()
    state.mkdir(mode=0o755)
    hands._dir()
    assert state.stat().st_mode & 0o777 == 0o700
    hands.receipt("click", True, 1, "main-host", 0)
    assert (state / "calls.jsonl").stat().st_mode & 0o777 == 0o600
    assert (state / "last.json").stat().st_mode & 0o777 == 0o600


def test_mirror_requires_remote_https_and_profile_home(tmp_path):
    env = clean_env()
    env["HERMES_HOME"] = str(tmp_path / "main-profile")
    refused = subprocess.run(["bash", str(MIRROR), "--dry-run"], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, timeout=10)
    assert refused.returncode == 64
    env["JARVIS_MIRROR_URL"] = "https://127.0.0.1:9119/api/plugins/hermes-jarvis/mirror"
    env["JARVIS_MIRROR_TRANSPORT"] = "direct"
    loopback = subprocess.run(["bash", str(MIRROR), "--dry-run"], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=10)
    assert loopback.returncode == 64
    env["JARVIS_MIRROR_TRANSPORT"] = "ssh-forward"
    forwarded = subprocess.run(["bash", str(MIRROR), "--dry-run"], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, timeout=10)
    assert forwarded.returncode == 0, forwarded.stderr
    env["JARVIS_MIRROR_URL"] = "https://member-agent.example/api/plugins/hermes-jarvis/mirror"
    env["JARVIS_MIRROR_TRANSPORT"] = "direct"
    ok = subprocess.run(["bash", str(MIRROR), "--dry-run"], env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, timeout=10)
    assert ok.returncode == 0, ok.stderr
    assert "member-agent.example" in ok.stdout


def test_toggle_scope_matches_frontend_utf16_fnv_for_non_ascii_route(tmp_path):
    values = ["connection-1", "路由", "目标"]
    text = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    raw = text.encode("utf-16-le", "surrogatepass")
    value = 0x811C9DC5
    for offset in range(0, len(raw), 2):
        value ^= raw[offset] | (raw[offset + 1] << 8)
        value = (value * 0x01000193) & 0xFFFFFFFF
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    expected = "0" if value == 0 else ""
    while value:
        value, rem = divmod(value, 36)
        expected = digits[rem] + expected
    app = tmp_path / "Hermes.app"; app.mkdir()
    env = clean_env()
    env.update({"HERMES_HOME": str(tmp_path / "main-profile"),
                "JARVIS_HERMES_APP": str(app), "JARVIS_OPEN_BIN": "/usr/bin/true",
                "JARVIS_CONNECTION_ID": values[0], "JARVIS_ROUTE_PROFILE": values[1],
                "JARVIS_TARGET_PROFILE": values[2]})
    result = subprocess.run(["bash", str(TOGGLE)], env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "desktop-heartbeat-%s.json" % expected in result.stdout


def test_driver_helper_is_pinned_and_plan_is_side_effect_free(tmp_path):
    env = clean_env()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["bash", str(DRIVER_INSTALL), "--plan"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "0.23.2" in result.stdout
    assert "9e521b16c8606896f20003f4d20ae62070a1cb3c8d33152d9d0593f62234fbb0" in result.stdout
    assert "YCK386LBJ7" in result.stdout
    assert not (tmp_path / ".local").exists()


def test_driver_undo_without_previous_app_consumes_receipt_once(tmp_path):
    root = Path(tempfile.mkdtemp(prefix="jarvis-driver-test-", dir="/private/tmp"))
    target = root / "Applications" / "CuaDriver.app"
    target.mkdir(parents=True)
    (target / "driver").write_text("installed", encoding="utf-8")
    # Mirror the helper's deterministic tree hash for this isolated fixture.
    import hashlib, stat
    digest = hashlib.sha256()
    for path in sorted(target.rglob("*")):
        rel = str(path.relative_to(target)).encode()
        mode = os.lstat(path).st_mode
        digest.update(rel + b"\0" + str(stat.S_IMODE(mode)).encode() + b"\0")
        if path.is_file():
            digest.update(b"F" + path.read_bytes())
    backup_root = root / "state" / "driver-backups"
    backup_root.mkdir(parents=True)
    receipt = backup_root / "last-install.env"
    receipt.write_text(
        "target=%s\nbackup=%s\nbackup_kind=none\ninstalled_hash=%s\n" %
        (target, backup_root / "unused", digest.hexdigest()), encoding="utf-8")
    env = clean_env(); env["JARVIS_CUA_DRIVER_TEST_ROOT"] = str(root)
    first = subprocess.run(["bash", str(DRIVER_INSTALL), "--undo"], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert first.returncode == 0, first.stderr
    assert not target.exists() and not receipt.exists()
    target.mkdir(parents=True); (target / "driver").write_text("separate", encoding="utf-8")
    second = subprocess.run(["bash", str(DRIVER_INSTALL), "--undo"], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert second.returncode == 2
        assert (target / "driver").read_text(encoding="utf-8") == "separate"
    finally:
        shutil.rmtree(root)


def test_driver_receipt_commit_failure_restores_previous_app(tmp_path):
    root = Path(tempfile.mkdtemp(prefix="jarvis-driver-test-", dir="/private/tmp"))
    try:
        target = root / "Applications" / "CuaDriver.app"
        target.mkdir(parents=True)
        (target / "old-marker").write_text("old", encoding="utf-8")
        source_app = tmp_path / "archive" / "CuaDriver.app" / "Contents"
        source_app.mkdir(parents=True)
        (source_app / "new-marker").write_text("new", encoding="utf-8")
        archive = tmp_path / "driver.tar.gz"
        subprocess.run(["tar", "-czf", str(archive), "-C", str(tmp_path / "archive"),
                        "CuaDriver.app"], check=True)
        tools = tmp_path / "tools"; tools.mkdir()
        scripts = {
            "curl": '#!/bin/sh\nwhile [ "$1" != "--output" ]; do shift; done\ncp "$FAKE_DRIVER_ARCHIVE" "$2"\n',
            "shasum": '#!/bin/sh\necho "9e521b16c8606896f20003f4d20ae62070a1cb3c8d33152d9d0593f62234fbb0  $4"\n',
            "codesign": '#!/bin/sh\ncase "$1" in -dv) echo "TeamIdentifier=YCK386LBJ7" >&2;; esac\nexit 0\n',
            "spctl": '#!/bin/sh\nexit 0\n',
            "ditto": '#!/bin/sh\ncp -R "$1" "$2"\n',
            "mv": '#!/bin/sh\ncase "$1" in */.last-install.env.*) exit 77;; esac\nexec /bin/mv "$@"\n',
        }
        for name, body in scripts.items():
            path = tools / name; path.write_text(body, encoding="utf-8"); path.chmod(0o755)
        env = clean_env()
        env.update({"JARVIS_CUA_DRIVER_TEST_ROOT": str(root),
                    "FAKE_DRIVER_ARCHIVE": str(archive),
                    "PATH": str(tools) + os.pathsep + os.environ["PATH"]})
        result = subprocess.run(["bash", str(DRIVER_INSTALL), "--apply"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, timeout=20)
        assert result.returncode != 0
        assert (target / "old-marker").read_text(encoding="utf-8") == "old"
        assert not (target / "Contents" / "new-marker").exists()
        assert not (root / "state" / "driver-backups" / "last-install.env").exists()
    finally:
        shutil.rmtree(root)


def test_member_payload_has_no_machine_identity_or_private_host_defaults():
    roots = [ROOT / "payload" / "hands", ROOT / "payload" / "bin"]
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for base in roots
        for path in base.rglob("*")
        if path.is_file() and path.suffix != ".pyc"
    )
    assert "/" + "Users/" not in text
    assert "tail4" not in text
