"""Isolated host/Talk patch package checks.

All mutations happen in temporary fixture trees. These tests do not build a
desktop app, restart a process, install a plugin, call a model, or touch a live
checkout.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import types
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[1]
HOST = PACK / "payload/host"
HELPER = HOST / "host-patch.py"
TALK_WRAPPER = HOST / "talk-presence/talk-presence-safe.py"
MANIFEST_PATH = HOST / "voice-patch-compatibility.json"
HERMES_SOURCE = Path(
    os.environ.get("JARVIS_HERMES_REFERENCE", Path.home() / ".hermes/hermes-agent")
).expanduser()
VOICE_FILES = (
    "apps/desktop/src/app/chat/composer/hooks/use-composer-voice.ts",
    "apps/desktop/src/app/chat/composer/hooks/use-composer-voice.test.ts",
    "apps/desktop/src/app/chat/composer/index.tsx",
    "apps/desktop/src/sdk/index.ts",
    "apps/desktop/electron/main.ts",
    "apps/desktop/electron/talk-auth.test.ts",
    "apps/desktop/electron/talk-auth.ts",
    "apps/desktop/src/api/plugins.test.ts",
    "apps/desktop/src/api/plugins.ts",
    "apps/desktop/src/app/chat/composer/types.ts",
    "apps/desktop/src/app/chat/index.tsx",
    "apps/desktop/src/app/contrib/latest-actions.ts",
    "apps/desktop/src/app/contrib/types.ts",
    "apps/desktop/src/app/contrib/wiring.tsx",
    "hermes_cli/dashboard_task_context.py",
    "tests/hermes_cli/test_dashboard_task_context.py",
)
BASE_COMMIT = "e83b1d51f13a08b424636f0b519db86a35aa7bd7"
TALK_REFERENCE = Path(
    os.environ.get("JARVIS_TALK_REFERENCE", Path.home() / ".hermes/plugins/hermes-talk")
).expanduser()
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def helper(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(HELPER), "--staged-root", str(root), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.fixture
def staged_root(tmp_path: Path) -> Path:
    if not (HERMES_SOURCE / ".git").exists():
        pytest.skip("Hermes source checkout is not available for isolated replay")
    root = tmp_path / "hermes-staged"
    for relative in VOICE_FILES:
        exists = subprocess.run(
            ["git", "-C", str(HERMES_SOURCE), "cat-file", "-e", BASE_COMMIT + ":" + relative],
            capture_output=True,
        )
        if exists.returncode:
            continue
        source = subprocess.check_output(
            ["git", "-C", str(HERMES_SOURCE), "show", BASE_COMMIT + ":" + relative]
        )
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source)
    (root / ".jarvis-staged-tree.json").write_text(
        '{"kind":"jarvis-host-staging"}\n', encoding="utf-8"
    )
    git(root, "init", "-q")
    git(root, "config", "user.email", "staged@example.invalid")
    git(root, "config", "user.name", "staged")
    git(root, "add", ".")
    git(root, "commit", "-qm", "base")
    return root


def test_manifest_and_package_are_metadata_free() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["public_base"]["commit"] == BASE_COMMIT
    assert manifest["privacy"]["sanitized_comments_and_test_fixtures"] is True
    for patch in manifest["patches"]:
        path = PACK / patch["file"]
        assert sha(path) == patch["package_sha256"]
        assert "index " not in path.read_text(encoding="utf-8")


def test_apply_check_and_revert_exact_sequence(staged_root: Path) -> None:
    assert helper(staged_root, "--check").returncode == 0
    first = helper(staged_root, "--apply", "--through", "first")
    assert first.returncode == 0, first.stdout + first.stderr
    applied = helper(staged_root, "--apply", "--through", "second")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert "through voice-2" in applied.stdout
    checked = helper(staged_root, "--check")
    assert checked.returncode == 0
    assert "voice-2" in checked.stdout
    reverted = helper(staged_root, "--revert", "--to", "base")
    assert reverted.returncode == 0, reverted.stdout + reverted.stderr
    assert "reverted to base" in reverted.stdout
    assert helper(staged_root, "--check").returncode == 0
    assert git(staged_root, "status", "--porcelain").stdout == ""


def test_revert_to_first_reverses_only_the_second_patch(staged_root: Path) -> None:
    applied = helper(staged_root, "--apply", "--through", "full")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    partial = helper(staged_root, "--revert", "--to", "first")
    assert partial.returncode == 0, partial.stdout + partial.stderr
    checked = helper(staged_root, "--check")
    assert checked.returncode == 0
    assert "voice-1" in checked.stdout
    restored = helper(staged_root, "--revert", "--to", "base")
    assert restored.returncode == 0, restored.stdout + restored.stderr
    assert helper(staged_root, "--check").returncode == 0


def test_wrong_direction_is_refused_without_claiming_a_level_change(staged_root: Path) -> None:
    assert helper(staged_root, "--apply", "--through", "full").returncode == 0
    lower_apply = helper(staged_root, "--apply", "--through", "first")
    assert lower_apply.returncode == 2
    assert "use --revert" in lower_apply.stderr
    assert "voice-6" in helper(staged_root, "--check").stdout
    assert helper(staged_root, "--revert", "--to", "base").returncode == 0
    higher_revert = helper(staged_root, "--revert", "--to", "second")
    assert higher_revert.returncode == 2
    assert "use --apply" in higher_revert.stderr
    assert "base" in helper(staged_root, "--check").stdout


def test_unsupported_source_fails_before_patch(staged_root: Path) -> None:
    target = staged_root / VOICE_FILES[0]
    target.write_bytes(target.read_bytes() + b"\n")
    result = helper(staged_root, "--apply", "--through", "second")
    assert result.returncode == 2
    assert "unsupported" in result.stderr
    assert git(staged_root, "status", "--porcelain").stdout


def test_unrelated_change_and_symlink_are_refused(staged_root: Path) -> None:
    extra = staged_root / "unrelated.txt"
    extra.write_text("outside the patch\n", encoding="utf-8")
    result = helper(staged_root, "--check")
    assert result.returncode == 2
    extra.unlink()
    target = staged_root / VOICE_FILES[0]
    target.unlink()
    target.symlink_to(staged_root / VOICE_FILES[1])
    result = helper(staged_root, "--check")
    assert result.returncode == 2


def test_cached_unrelated_change_is_refused(staged_root: Path) -> None:
    extra = staged_root / "cached-unrelated.txt"
    extra.write_text("outside the patch\n", encoding="utf-8")
    git(staged_root, "add", "cached-unrelated.txt")
    result = helper(staged_root, "--check")
    assert result.returncode == 2
    assert "cached-unrelated.txt" in result.stderr


def test_nested_fake_stage_root_and_symlinked_parent_are_refused(staged_root: Path) -> None:
    nested = staged_root / "nested"
    nested.mkdir()
    (nested / ".jarvis-staged-tree.json").write_text(
        '{"kind":"jarvis-host-staging"}\n', encoding="utf-8"
    )
    result = helper(nested, "--check")
    assert result.returncode == 2
    assert "Git top-level" in result.stderr

    hooks = staged_root / "apps/desktop/src/app/chat/composer/hooks"
    real_hooks = staged_root / "apps/desktop/src/app/chat/composer/hooks-real"
    hooks.rename(real_hooks)
    hooks.symlink_to(real_hooks)
    result = helper(staged_root, "--check")
    assert result.returncode == 2
    assert "symlinked staged path component" in result.stderr


def test_packaged_patch_hash_is_checked_without_mutating_package(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("jarvis_host_patch", HELPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    temp_patch = tmp_path / "voice-1-67601e80767.patch"
    temp_patch.write_text("fixture\n", encoding="utf-8")
    try:
        module.HOST_DIR = tmp_path
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        with pytest.raises(module.Refusal, match="sha256 mismatch"):
            module.packaged_patch(manifest, 1)
    finally:
        temp_patch.unlink(missing_ok=True)


PRESENCE_MARKER = "ui/.hermes-jarvis-presence.orig.sha256"


def presence_marker(root: Path) -> bytes | None:
    """What the presence marker holds right now, or None when it is absent.

    The reference tree is whatever this machine has: a clean Talk checkout has
    no marker, a Mac that already carries the presence patch has one. Either is
    a valid starting point, so the tests assert the marker is UNCHANGED rather
    than absent.
    """
    marker = root / PRESENCE_MARKER
    return marker.read_bytes() if marker.is_file() else None


def talk_fixture(tmp_path: Path) -> Path:
    if not (TALK_REFERENCE / "ui/talk-surface.js").is_file():
        pytest.skip("Talk reference is not available for wrapper replay")
    root = tmp_path / "talk-staged"
    shutil.copytree(TALK_REFERENCE, root, symlinks=False)
    (root / ".jarvis-talk-staged-tree.json").write_text(
        '{"kind":"jarvis-talk-staging"}\n', encoding="utf-8"
    )
    return root


def test_talk_wrapper_rejects_a_symlinked_ancestor(tmp_path: Path) -> None:
    root = talk_fixture(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    result = subprocess.run(
        ["python3", str(TALK_WRAPPER), "--talk-staged-root", str(alias), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "parent directories is symlinked" in result.stderr


def test_talk_wrapper_restores_when_builder_deletes_marker(tmp_path: Path) -> None:
    root = talk_fixture(tmp_path)
    surface = root / "ui/talk-surface.js"
    original = surface.read_bytes()
    presence_before = presence_marker(root)
    (root / "scripts/build_ui.py").write_text(
        "from pathlib import Path\n"
        "Path('ui/talk-surface.js').write_bytes(Path('ui/talk-surface.js').read_bytes() + b'\\n')\n"
        "Path('.jarvis-talk-staged-tree.json').unlink()\n"
        "raise SystemExit(23)\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["python3", str(TALK_WRAPPER), "--talk-staged-root", str(root), "--apply"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "post-helper scan failed" in result.stderr
    assert surface.read_bytes() == original
    assert (root / ".jarvis-talk-staged-tree.json").is_file()
    assert presence_marker(root) == presence_before


def test_talk_wrapper_restores_when_builder_adds_a_symlink(tmp_path: Path) -> None:
    root = talk_fixture(tmp_path)
    surface = root / "ui/talk-surface.js"
    original = surface.read_bytes()
    (root / "scripts/build_ui.py").write_text(
        "from pathlib import Path\n"
        "Path('generated-bad').symlink_to('ui/talk-surface.js')\n"
        "raise SystemExit(23)\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["python3", str(TALK_WRAPPER), "--talk-staged-root", str(root), "--apply"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "post-helper scan failed" in result.stderr
    assert surface.read_bytes() == original
    assert not (root / "generated-bad").exists()


def test_talk_wrapper_retains_backup_when_restore_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = talk_fixture(tmp_path)
    surface = root / "ui/talk-surface.js"
    original = surface.read_bytes()
    spec = importlib.util.spec_from_file_location("talk_presence_safe", TALK_WRAPPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def failed_helper(*_args: object, **_kwargs: object) -> types.SimpleNamespace:
        surface.write_bytes(original + b"\nchanged")
        return types.SimpleNamespace(returncode=23, stdout="", stderr="builder failed")

    def failed_restore(*_args: object, **_kwargs: object) -> None:
        raise OSError("synthetic restore permission failure")

    real_run = module.subprocess.run
    real_restore = module.clear_and_restore
    module.subprocess.run = failed_helper
    module.clear_and_restore = failed_restore
    try:
        assert module.main(["--talk-staged-root", str(root), "--apply", "--no-build"]) == 2
    finally:
        module.subprocess.run = real_run
        module.clear_and_restore = real_restore

    error = capsys.readouterr().err
    assert "ROLLBACK INCOMPLETE" in error
    marker = "durable backup retained at "
    assert marker in error
    backup = Path(error.split(marker, 1)[1].strip())
    try:
        assert backup.is_dir()
        assert (backup / "ui/talk-surface.js").read_bytes() == original
        assert surface.read_bytes() != original
    finally:
        shutil.rmtree(backup, ignore_errors=True)
