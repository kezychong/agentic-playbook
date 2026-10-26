"""Isolated tests for the package preflight and transactional installer."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import types
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import install  # noqa: E402
import prepare_package  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_package(root: Path, *, release_ready: bool = True) -> Path:
    (root / "payload").mkdir(parents=True)
    (root / "payload/main.txt").write_text("main-v1\n", encoding="utf-8")
    (root / "payload/headless.txt").write_text("headless-v1\n", encoding="utf-8")
    files = []
    for rel, role in (("payload/main.txt", "main"), ("payload/headless.txt", "headless")):
        path = root / rel
        files.append({"path": rel, "role": role, "status": "present", "required": True, "size": path.stat().st_size, "sha256": digest(path)})
    manifest = {
        "schema_version": 1,
        "package_name": "fixture",
        "package_version": "1.0.0",
        "release_ready": release_ready,
        "release_state": "release",
        "release_gates": {
            "frontend_source_and_bundle": release_ready,
            "host_patch_compatibility_proof": release_ready,
            "licence_and_art_provenance": release_ready,
            "two_device_install_proof": release_ready,
            "linux_headless_proof": release_ready,
        },
        "files": files,
        "install_mappings": {
            "main": [{"package_path": "payload/main.txt", "target_relative": "installed/main.txt", "role": "main"}],
            "headless": [{"package_path": "payload/headless.txt", "target_relative": "installed/headless.txt", "role": "headless"}],
        },
    }
    (root / "package-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root


def add_second_main_mapping(package: Path) -> None:
    manifest_path = package / "package-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["install_mappings"]["main"].append({"package_path": "payload/headless.txt", "target_relative": "installed/second.txt", "role": "headless"})
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


class PackageInstallTests(unittest.TestCase):
    def test_plain_python_entrypoint_does_not_create_package_bytecode_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = base / "package"
            (package / "payload").mkdir(parents=True)
            (package / "scripts").mkdir()
            (package / "payload" / "main.txt").write_text("main-v1\n", encoding="utf-8")
            source_scripts = Path(__file__).resolve().parents[1] / "scripts"
            shutil.copy2(source_scripts / "install.py", package / "scripts" / "install.py")
            shutil.copy2(source_scripts / "prepare_package.py", package / "scripts" / "prepare_package.py")
            files = []
            for relative in ("payload/main.txt", "scripts/install.py", "scripts/prepare_package.py"):
                path = package / relative
                files.append({"path": relative, "role": "fixture", "status": "present", "required": True, "size": path.stat().st_size, "sha256": digest(path)})
            manifest = {
                "schema_version": 1,
                "package_name": "fixture-entrypoint",
                "package_version": "1.0.0",
                "release_ready": True,
                "release_state": "release",
                "release_gates": {
                    "frontend_source_and_bundle": True,
                    "host_patch_compatibility_proof": True,
                    "licence_and_art_provenance": True,
                    "two_device_install_proof": True,
                    "linux_headless_proof": True,
                },
                "files": files,
                "install_mappings": {"main": [{"package_path": "payload/main.txt", "target_relative": "installed/main.txt", "role": "fixture"}]},
            }
            (package / "package-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            destination = base / "main-home"
            destination.mkdir()
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            completed = subprocess.run(
                [sys.executable, str(package / "scripts" / "install.py"), str(package), "--destination", str(destination), "--role", "main", "--apply"],
                cwd=package,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertFalse((package / "scripts" / "__pycache__").exists())
            self.assertEqual((destination / "installed" / "main.txt").read_text(encoding="utf-8"), "main-v1\n")

    def test_release_package_installs_and_prints_pass_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package", release_ready=True)
            report = prepare_package.preflight(package)
            self.assertTrue(report["release_ready"])
            self.assertTrue(report["install_ready"])
            self.assertEqual(report["release_state"], "release")
            with mock.patch.object(sys, "argv", ["prepare_package.py", str(package)]), mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(prepare_package.main(), 0)
            self.assertIn(f"PASS RELEASE: {report['files_scanned']} files scanned", stdout.getvalue())
            destination = base / "main-home"
            destination.mkdir()
            result = install.install_package(package, destination, "main", apply=True)
            self.assertEqual(result["package_state"], "release")
            self.assertEqual(install.undo_install(destination)["mode"], "undo")

    def test_a_package_that_is_not_a_release_is_never_installable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package", release_ready=True)
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["release_state"] = "staging"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = prepare_package.preflight(package)
            self.assertFalse(report["release_ready"])
            self.assertFalse(report["install_ready"])
            self.assertTrue(any("release_state must be 'release'" in error for error in report["errors"]))
            with mock.patch.object(sys, "argv", ["prepare_package.py", str(package)]), mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(prepare_package.main(), 1)
            self.assertIn("FAIL:", stdout.getvalue())
            destination = base / "main-home"
            destination.mkdir()
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "main", apply=True)
            self.assertEqual(list(destination.iterdir()), [])

    def test_a_single_false_release_gate_blocks_the_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package", release_ready=True)
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["release_gates"]["linux_headless_proof"] = False
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = prepare_package.preflight(package)
            self.assertFalse(report["release_ready"])
            self.assertFalse(report["install_ready"])
            self.assertTrue(any("release gate incomplete: linux_headless_proof" in error for error in report["errors"]))

    def test_retired_gate_names_no_longer_satisfy_the_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = make_package(Path(tmp) / "package", release_ready=True)
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["release_gates"] = {
                "frontend_source_and_bundle": True,
                "host_patch_compatibility_proof": True,
                "hands_driver_and_hardware_proof": True,
                "licence_and_art_provenance": True,
                "real_two_device_qa": True,
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(prepare_package.PreflightError):
                prepare_package.preflight(package)

    def test_tampered_payload_rejects_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = make_package(Path(tmp) / "package", release_ready=True)
            (package / "payload" / "main.txt").write_text("tampered\n", encoding="utf-8")
            report = prepare_package.preflight(package)
            self.assertFalse(report["release_ready"])
            self.assertFalse(report["install_ready"])
            self.assertTrue(any("SHA-256 mismatch" in error for error in report["errors"]))

    def test_incomplete_package_aborts_before_any_destination_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package", release_ready=False)
            destination = base / "profile"
            destination.mkdir()
            sentinel = destination / "untouched.txt"
            sentinel.write_text("keep\n", encoding="utf-8")
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "main", apply=True)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(list(destination.iterdir()), [sentinel])

    def test_manifest_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = make_package(Path(tmp) / "package")
            (package / "payload/main.txt").write_text("changed\n", encoding="utf-8")
            report = prepare_package.preflight(package)
            self.assertFalse(report["release_ready"])
            self.assertTrue(any("SHA-256 mismatch" in item for item in report["errors"]))

    def test_optional_missing_entry_cannot_hide_a_present_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            optional = package / "optional.txt"
            optional.write_text("unhashed\n", encoding="utf-8")
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"].append({"path": "optional.txt", "role": "optional", "status": "missing", "required": False})
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = prepare_package.preflight(package)
            self.assertFalse(report["release_ready"])
            self.assertTrue(any("manifest marks missing" in item for item in report["errors"]))

    def test_non_regular_fifo_is_rejected_before_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            fifo = package / "pipe"
            os.mkfifo(fifo)
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"].append({"path": "pipe", "role": "pipe", "status": "present", "required": True, "size": 0, "sha256": "0" * 64})
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = prepare_package.preflight(package)
            self.assertFalse(report["release_ready"])
            self.assertTrue(any("non-regular file" in item for item in report["errors"]))

    def test_required_gate_schema_and_strict_schema_version_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("release_gates")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(prepare_package.PreflightError):
                prepare_package.preflight(package)
            manifest["release_gates"] = {
                "frontend_source_and_bundle": True,
                "host_patch_compatibility_proof": True,
                "licence_and_art_provenance": True,
                "two_device_install_proof": True,
                "linux_headless_proof": True,
            }
            manifest["schema_version"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(prepare_package.PreflightError):
                prepare_package.preflight(package)

    def test_symlink_and_unsafe_manifest_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            outside = base / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            os.symlink(outside, package / "payload/link.txt")
            report = prepare_package.preflight(package)
            self.assertTrue(any("symlink file" in item for item in report["errors"]))
            manifest = json.loads((package / "package-manifest.json").read_text(encoding="utf-8"))
            manifest["files"][0]["path"] = "../outside.txt"
            (package / "package-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(prepare_package.PreflightError):
                prepare_package.preflight(package)

    def test_apply_rerun_is_a_no_op_and_undo_restores_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            target = destination / "installed/main.txt"
            target.parent.mkdir()
            target.write_text("original\n", encoding="utf-8")
            first = install.install_package(package, destination, "main", apply=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "main-v1\n")
            second = install.install_package(package, destination, "main", apply=True)
            self.assertEqual(second["rerun"], "no-op")
            self.assertEqual(install.undo_install(destination)["mode"], "undo")
            self.assertEqual(target.read_text(encoding="utf-8"), "original\n")
            self.assertFalse(Path(first["state"]).exists())

    def test_main_install_creates_private_jarvis_dir_and_undo_removes_empty_owned_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            result = install.install_package(package, destination, "main", apply=True)
            jarvis_dir = destination / "jarvis"
            self.assertTrue(jarvis_dir.is_dir())
            self.assertEqual(jarvis_dir.stat().st_mode & 0o777, 0o700)
            receipt = json.loads(Path(result["state"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["directories"], [{"relative": "jarvis", "created": True, "previous_mode": None, "installed_mode": 0o700}])
            undone = install.undo_install(destination)
            self.assertEqual(undone["mode"], "undo")
            self.assertFalse(jarvis_dir.exists())

    def test_main_install_preserves_preexisting_jarvis_dir_data_and_mode_on_undo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            jarvis_dir = destination / "jarvis"
            jarvis_dir.mkdir(mode=0o1700)
            os.chmod(jarvis_dir, 0o1700)
            sentinel = jarvis_dir / "member-data.json"
            sentinel.write_text("keep\n", encoding="utf-8")
            install.install_package(package, destination, "main", apply=True)
            self.assertEqual(jarvis_dir.stat().st_mode & 0o7777, 0o0700)
            undone = install.undo_install(destination)
            self.assertEqual(undone["mode"], "undo")
            self.assertTrue(jarvis_dir.is_dir())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(jarvis_dir.stat().st_mode & 0o7777, 0o1700)

    def test_main_role_installs_on_a_non_mac_and_labels_the_mac_only_extras(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            with mock.patch.object(install.platform, "system", return_value="Windows"):
                result = install.setup_package(package, main_destination=destination, apply=True)
            self.assertEqual([role["role"] for role in result["roles"]], ["main"])
            self.assertTrue(result["optional_mac_extras"].startswith("unavailable:"))
            self.assertIn("Mac-only extras", result["optional_mac_extras"])
            self.assertEqual((destination / "installed/main.txt").read_text(encoding="utf-8"), "main-v1\n")
            self.assertEqual(install.undo_install(destination)["mode"], "undo")

    def test_main_role_on_a_mac_offers_the_optional_extras_without_requiring_them(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            with mock.patch.object(install.platform, "system", return_value="Darwin"):
                result = install.setup_package(package, main_destination=destination, apply=False)
            self.assertTrue(result["optional_mac_extras"].startswith("available:"))
            self.assertEqual(list(destination.iterdir()), [])

    def test_state_dir_receipt_records_the_mode_the_platform_actually_gave(self) -> None:
        # Windows ignores POSIX mode bits, so chmod cannot reach 0700 there.
        # The install must still succeed and the receipt must record the mode
        # that was really achieved rather than the one that was requested.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            jarvis_dir = destination / "jarvis"
            jarvis_dir.mkdir(mode=0o755)
            os.chmod(jarvis_dir, 0o755)
            with mock.patch.object(install, "_make_private", lambda path: None):
                result = install.install_package(package, destination, "main", apply=True)
            receipt = json.loads(Path(result["state"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["directories"], [{"relative": "jarvis", "created": False, "previous_mode": 0o755, "installed_mode": 0o755}])
            self.assertEqual(install.undo_install(destination)["mode"], "undo")
            self.assertEqual(jarvis_dir.stat().st_mode & 0o7777, 0o755)

    def test_main_install_preserves_owned_jarvis_dir_after_member_writes_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            install.install_package(package, destination, "main", apply=True)
            (destination / "jarvis" / "desktop-heartbeat.json").write_text("live\n", encoding="utf-8")
            undone = install.undo_install(destination)
            self.assertEqual(undone["preserved_directories"], ["jarvis"])
            self.assertEqual((destination / "jarvis" / "desktop-heartbeat.json").read_text(encoding="utf-8"), "live\n")

    def test_main_install_rejects_jarvis_symlink_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "main-home"
            destination.mkdir()
            outside = base / "outside"
            outside.mkdir()
            os.symlink(outside, destination / "jarvis")
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "main", apply=True)
            self.assertTrue((destination / "jarvis").is_symlink())
            self.assertEqual(list(outside.iterdir()), [])

    def test_changed_plan_is_refused_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            target = destination / "installed/main.txt"
            install.install_package(package, destination, "main", apply=True)
            (package / "payload/main.txt").write_text("main-v2\n", encoding="utf-8")
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entry = next(item for item in manifest["files"] if item["path"] == "payload/main.txt")
            entry["size"] = (package / "payload/main.txt").stat().st_size
            entry["sha256"] = digest(package / "payload/main.txt")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "main", apply=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "main-v1\n")

    def test_dangling_target_symlink_is_rejected_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            target = destination / "installed/main.txt"
            target.parent.mkdir()
            os.symlink(base / "does-not-exist", target)
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "main", apply=True)
            self.assertTrue(target.is_symlink())

    def test_edited_destination_blocks_undo_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            target = destination / "installed/main.txt"
            install.install_package(package, destination, "main", apply=True)
            target.write_text("member edit\n", encoding="utf-8")
            state = destination / install.STATE_NAME
            before = state.read_bytes()
            with self.assertRaises(install.InstallError):
                install.undo_install(destination)
            self.assertEqual(state.read_bytes(), before)
            self.assertEqual(target.read_text(encoding="utf-8"), "member edit\n")

    def test_corrupt_or_redirected_backup_blocks_undo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            target = destination / "installed/main.txt"
            target.parent.mkdir()
            target.write_text("original\n", encoding="utf-8")
            install.install_package(package, destination, "main", apply=True)
            state = json.loads((destination / install.STATE_NAME).read_text(encoding="utf-8"))
            backup = destination / state["files"][0]["backup_relative"]
            backup.write_text("corrupted\n", encoding="utf-8")
            with self.assertRaises(install.InstallError):
                install.undo_install(destination)
            self.assertEqual(target.read_text(encoding="utf-8"), "main-v1\n")
            self.assertTrue((destination / install.STATE_NAME).exists())

            shutil.rmtree(backup.parent)
            external = base / "external"
            external.mkdir()
            (external / "main.txt").write_text("outside\n", encoding="utf-8")
            os.symlink(external, backup.parent)
            with self.assertRaises(install.InstallError):
                install.undo_install(destination)
            self.assertEqual(target.read_text(encoding="utf-8"), "main-v1\n")

    def test_failed_second_copy_rolls_back_first_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            # Add a second mapping so a failure can occur after one replacement.
            manifest_path = package / "package-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["install_mappings"]["main"].append({"package_path": "payload/headless.txt", "target_relative": "installed/second.txt", "role": "headless"})
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            destination = base / "member-profile"
            destination.mkdir()
            first = destination / "installed/main.txt"
            first.parent.mkdir()
            first.write_text("original\n", encoding="utf-8")
            real_copy = install._atomic_copy
            calls = {"count": 0}

            def fail_on_second(source: Path, target: Path) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("fixture failure")
                real_copy(source, target)

            with mock.patch.object(install, "_atomic_copy", side_effect=fail_on_second):
                with self.assertRaises(install.InstallError):
                    install.install_package(package, destination, "main", apply=True)
            self.assertEqual(first.read_text(encoding="utf-8"), "original\n")
            self.assertFalse((destination / "installed/second.txt").exists())
            self.assertFalse((destination / install.STATE_NAME).exists())

    def test_persistent_rollback_failure_retains_recovery_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            add_second_main_mapping(package)
            destination = base / "member-profile"
            destination.mkdir()
            first = destination / "installed/main.txt"
            second = destination / "installed/second.txt"
            first.parent.mkdir()
            first.write_text("original-main\n", encoding="utf-8")
            second.write_text("original-second\n", encoding="utf-8")
            real_copy = install._atomic_copy
            calls = {"count": 0}

            def fail_after_first(source: Path, target: Path) -> None:
                calls["count"] += 1
                if calls["count"] > 1:
                    raise OSError("persistent synthetic write failure")
                real_copy(source, target)

            with mock.patch.object(install, "_atomic_copy", side_effect=fail_after_first):
                with self.assertRaises(install.InstallError) as raised:
                    install.install_package(package, destination, "main", apply=True)
            self.assertIn("rollback incomplete", str(raised.exception))
            self.assertEqual(first.read_text(encoding="utf-8"), "main-v1\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "original-second\n")
            self.assertTrue((destination / install.RECOVERY_STATE_NAME).exists())
            self.assertTrue(any(path.name.startswith(".jarvis-backup-") for path in destination.iterdir()))

    def test_undo_restore_failure_is_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            add_second_main_mapping(package)
            destination = base / "member-profile"
            destination.mkdir()
            first = destination / "installed/main.txt"
            second = destination / "installed/second.txt"
            first.parent.mkdir()
            first.write_text("original-main\n", encoding="utf-8")
            second.write_text("original-second\n", encoding="utf-8")
            install.install_package(package, destination, "main", apply=True)
            real_copy = install._atomic_copy
            calls = {"count": 0}

            def fail_second_restore(source: Path, target: Path) -> None:
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("synthetic undo failure")
                real_copy(source, target)

            with mock.patch.object(install, "_atomic_copy", side_effect=fail_second_restore):
                with self.assertRaises(install.InstallError):
                    install.undo_install(destination)
            self.assertEqual(first.read_text(encoding="utf-8"), "main-v1\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "headless-v1\n")
            self.assertTrue((destination / install.STATE_NAME).exists())
            self.assertEqual(install.undo_install(destination)["mode"], "undo")
            self.assertEqual(first.read_text(encoding="utf-8"), "original-main\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "original-second\n")

    def test_profile_discovery_uses_host_matcher_and_plugin_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "member-profile"
            plugin = root / "plugins" / "hermes-jarvis"
            plugin.mkdir(parents=True)
            validator = types.SimpleNamespace(profile_root_from_plugin=lambda value: root)
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == home.name
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                report = install.discover_profile(root, "member-profile", validator_module=validator)
            self.assertTrue(report["plugin_identity"])
            self.assertTrue(report["host_profile_match"])
            self.assertTrue(report["ready"])

    def test_profile_config_uses_selected_boxes_and_restores_an_invalid_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "member-profile"
            plugin = root / "plugins" / "hermes-jarvis"
            plugin.mkdir(parents=True)

            class Validator:
                @staticmethod
                def profile_root_from_plugin(value: Path) -> Path:
                    return root

                @staticmethod
                def load_config(value: Path) -> object:
                    raw = json.loads((root / "jarvis" / "config.json").read_text(encoding="utf-8"))
                    if raw["profile_id"] != "member-profile":
                        raise ValueError("profile mismatch")
                    return raw

            selected = ["today_plan", "brains"]
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "member-profile" and home.resolve() == root.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                first = install.provision_profile_config(
                    Path(tmp), root, "member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore",
                    enabled_sources=selected, sources={"today_plan": {"path": str(Path(tmp) / "today.md")}}, brains=[{"id": "work", "label": "Work", "path": str(Path(tmp) / "work")}], apply=True, validator_module=Validator,
                )
            config_path = root / "jarvis" / "config.json"
            document = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(document["enabled_sources"], selected)
            self.assertEqual(first["mode_bits"], "0o600")
            self.assertEqual(oct((root / "jarvis").stat().st_mode & 0o777), "0o700")
            previous = config_path.read_bytes()

            class RejectingValidator(Validator):
                @staticmethod
                def load_config(value: Path) -> object:
                    raise ValueError("synthetic validator rejection")

            with self.assertRaises(install.SetupError):
                with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                    install.provision_profile_config(
                        Path(tmp), root, "member-profile", agent_name="Changed", owner_label="Member", timezone="Asia/Singapore",
                        enabled_sources=selected, sources={}, brains=[], apply=True, validator_module=RejectingValidator,
                    )
            self.assertEqual(config_path.read_bytes(), previous)

    def test_setup_rolls_back_staged_roles_when_config_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            main = base / "main-profile"
            headless = base / "member-profile"
            main.mkdir()
            headless.mkdir()
            staged = {
                "main": {"destination": str(main), "state": str(main / install.STATE_NAME), "role": "main"},
                "headless": {"destination": str(headless), "state": str(headless / install.STATE_NAME), "role": "headless"},
            }

            def fake_install(_package: Path, destination: Path, role: str, **_kwargs: object) -> dict[str, str]:
                return staged[role]

            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "member-profile" and home.resolve() == headless.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                with mock.patch.object(install, "install_package", side_effect=fake_install), mock.patch.object(install, "_load_backend_validator", return_value=object()), mock.patch.object(install, "provision_profile_config", side_effect=install.SetupError("synthetic config failure")), mock.patch.object(install, "undo_install") as undo:
                    with self.assertRaises(install.SetupError):
                        install.setup_package(package, main_destination=main, headless_destination=headless, profile_id="member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)
            self.assertEqual([call.args[0] for call in undo.call_args_list], [str(headless), str(main)])

    def test_setup_reports_rollback_failure_instead_of_swallowing_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            main = base / "main-profile"
            headless = base / "member-profile"
            main.mkdir()
            headless.mkdir()
            staged = {
                "main": {"destination": str(main), "state": str(main / install.STATE_NAME), "role": "main"},
                "headless": {"destination": str(headless), "state": str(headless / install.STATE_NAME), "role": "headless"},
            }
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "member-profile" and home.resolve() == headless.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                with mock.patch.object(install, "install_package", side_effect=lambda _package, _destination, role, **_kwargs: staged[role]), mock.patch.object(install, "_load_backend_validator", return_value=object()), mock.patch.object(install, "provision_profile_config", side_effect=install.SetupError("synthetic config failure")), mock.patch.object(install, "undo_install", side_effect=install.InstallError("persistent undo failure")):
                    with self.assertRaisesRegex(install.SetupError, "rollback is incomplete"):
                        install.setup_package(package, main_destination=main, headless_destination=headless, profile_id="member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)

    def test_identical_setup_rerun_preserves_existing_install_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            plugin = destination / "plugins" / "hermes-jarvis"
            plugin.mkdir(parents=True)

            class Validator:
                _TOP_KEYS = {"schema_version", "profile_id", "agent_name", "owner_label", "timezone", "enabled_sources", "sources", "brains"}
                SOURCE_IDS = frozenset()

                @staticmethod
                def profile_root_from_plugin(value: Path) -> Path:
                    return destination

                @staticmethod
                def load_config(value: Path) -> object:
                    document = json.loads((destination / "jarvis" / "config.json").read_text(encoding="utf-8"))
                    if document["profile_id"] != "member-profile":
                        raise ValueError("profile mismatch")
                    return document

                @staticmethod
                def ensure_state_dir(value: Path) -> Path:
                    state = value / "jarvis"
                    state.mkdir(mode=0o700, exist_ok=True)
                    return state

                @staticmethod
                def validate_config_document(document: dict[str, object], value: Path) -> None:
                    if document["profile_id"] != "member-profile":
                        raise ValueError("profile mismatch")

            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "member-profile" and home.resolve() == destination.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}), mock.patch.object(install, "_load_backend_validator", return_value=Validator):
                first = install.setup_package(package, headless_destination=destination, profile_id="member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)
                config_before = (destination / "jarvis" / "config.json").read_bytes()
                state_before = (destination / install.STATE_NAME).read_bytes()
                second = install.setup_package(package, headless_destination=destination, profile_id="member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)
            self.assertEqual(first["config"]["mode"], "apply")
            self.assertEqual(second["config"], {"mode": "existing-validated", "rerun": "no-op"})
            self.assertEqual((destination / "jarvis" / "config.json").read_bytes(), config_before)
            self.assertEqual((destination / install.STATE_NAME).read_bytes(), state_before)
            self.assertTrue(Path(first["roles"][0]["state"]).exists())

    def test_receipt_append_failure_restores_new_config_before_role_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            plugin = destination / "plugins" / "hermes-jarvis"
            plugin.mkdir(parents=True)

            class Validator:
                _TOP_KEYS = {"schema_version", "profile_id", "agent_name", "owner_label", "timezone", "enabled_sources", "sources", "brains"}
                SOURCE_IDS = frozenset()

                @staticmethod
                def profile_root_from_plugin(value: Path) -> Path:
                    return destination

                @staticmethod
                def load_config(value: Path) -> object:
                    return json.loads((destination / "jarvis" / "config.json").read_text(encoding="utf-8"))

                @staticmethod
                def ensure_state_dir(value: Path) -> Path:
                    state = value / "jarvis"
                    state.mkdir(mode=0o700, exist_ok=True)
                    return state

            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "member-profile" and home.resolve() == destination.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}), mock.patch.object(install, "_load_backend_validator", return_value=Validator), mock.patch.object(install, "_append_receipt_record", side_effect=install.SetupError("synthetic receipt write failure")):
                with self.assertRaisesRegex(install.SetupError, "previous config restored"):
                    install.setup_package(package, headless_destination=destination, profile_id="member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)
            self.assertFalse((destination / "jarvis" / "config.json").exists())
            self.assertFalse((destination / "installed" / "headless.txt").exists())
            self.assertFalse((destination / install.STATE_NAME).exists())
            backups = [path for path in destination.iterdir() if path.name.startswith(".jarvis-backup-")]
            self.assertTrue(backups)
            self.assertFalse(any((path / "jarvis" / "config.json").exists() for path in backups))

    def test_setup_preflights_before_loading_packaged_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            (package / "payload" / "headless.txt").write_text("tampered\n", encoding="utf-8")
            destination = base / "member-profile"
            destination.mkdir()
            loader = mock.Mock(side_effect=AssertionError("packaged validator imported before preflight"))
            with mock.patch.object(install, "_load_backend_validator", loader):
                with self.assertRaises(install.SetupError):
                    install.setup_package(package, headless_destination=destination, profile_id="member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)
            loader.assert_not_called()
            self.assertEqual(list(destination.iterdir()), [])

    def test_config_is_in_headless_receipt_and_undo_restores_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            plugin = destination / "plugins" / "hermes-jarvis"
            plugin.mkdir(parents=True)
            validator = install._load_backend_validator(Path(__file__).resolve().parents[1])
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "member-profile" and home.resolve() == destination.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                install_result = install.install_package(package, destination, "headless", apply=True, profile_id="member-profile")
                config_result = install.provision_profile_config(
                    package, destination, "member-profile", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore",
                    enabled_sources=None, enabled_boxes=["today"], sources={}, brains=[], apply=True, validator_module=validator,
                    backup_dir=destination / json.loads(Path(install_result["state"]).read_text(encoding="utf-8"))["backup_dir"],
                )
                install._append_receipt_record(Path(install_result["state"]), config_result["receipt_record"])
            config_path = destination / "jarvis" / "config.json"
            self.assertTrue(config_path.exists())
            self.assertEqual(install.undo_install(destination)["mode"], "undo")
            self.assertFalse(config_path.exists())

    def test_headless_profile_identity_must_match_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "headless", apply=True, profile_id="another-profile")
            self.assertEqual(list(destination.iterdir()), [])

    def test_default_profile_id_can_map_to_custom_profile_home_through_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "custom-home"
            destination.mkdir()
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "default" and home.resolve() == destination.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                result = install.install_package(package, destination, "headless", apply=True, profile_id="default")
            self.assertEqual(result["role"], "headless")
            self.assertEqual(install.undo_install(destination)["mode"], "undo")

    def test_dry_run_validates_first_install_config_without_plugin_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "custom-home"
            root.mkdir()
            package = Path(__file__).resolve().parents[1]
            validator = install._load_backend_validator(package)
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda profile_id, home: profile_id == "default" and home.resolve() == root.resolve()
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                result = install.provision_profile_config(
                    package, root, "default", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore",
                    enabled_sources=None, enabled_boxes=None, sources={}, brains=[], apply=False, validator_module=validator,
                )
            self.assertTrue(result["prospective_validated"])
            self.assertTrue(result["requires_plugin_before_apply"])
            self.assertFalse((root / "jarvis").exists())

    def test_unknown_host_profile_stops_setup_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "custom-home"
            root.mkdir()
            package = Path(__file__).resolve().parents[1]
            profiles = types.ModuleType("hermes_cli.profiles")
            profiles.profile_matches_home = lambda _profile_id, _home: False
            hermes_cli = types.ModuleType("hermes_cli")
            with mock.patch.dict(sys.modules, {"hermes_cli": hermes_cli, "hermes_cli.profiles": profiles}):
                with self.assertRaises(install.SetupError):
                    install.setup_package(package, headless_destination=root, profile_id="unknown", agent_name="Chief", owner_label="Member", timezone="Asia/Singapore", apply=True)
            self.assertEqual(list(root.iterdir()), [])

    def test_box_selection_maps_to_read_sources_and_optional_public_setting(self) -> None:
        validator = types.SimpleNamespace(SOURCE_IDS=frozenset({"agent_state", "agent_helpers", "today_plan", "lever", "one_thing_scoreboard"}))
        sources, boxes = install._resolve_box_sources(validator, ["waiting_on_you", "today", "scoreboard"], None)
        self.assertEqual(sources, ["agent_state", "today_plan", "lever", "one_thing_scoreboard"])
        self.assertEqual(boxes, ["waiting_on_you", "today", "scoreboard"])
        self.assertEqual(install._resolve_box_sources(validator, None, None), (sorted(validator.SOURCE_IDS), None))
        with self.assertRaises(install.SetupError):
            install._resolve_box_sources(validator, ["unknown-box"], None)

    def test_symlinked_package_or_destination_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            package_link = base / "package-link"
            os.symlink(package, package_link)
            with self.assertRaises(prepare_package.PreflightError):
                prepare_package.preflight(package_link)
            destination = base / "member-profile"
            destination.mkdir()
            destination_link = base / "member-profile-link"
            os.symlink(destination, destination_link)
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination_link, "main", apply=True)

    def test_symlinked_package_ancestor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_parent = base / "real-parent"
            package = make_package(real_parent / "package")
            alias_parent = base / "alias-parent"
            os.symlink(real_parent, alias_parent)
            with self.assertRaises(prepare_package.PreflightError):
                prepare_package.preflight(alias_parent / "package")

    def test_dangling_install_receipt_symlink_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            package = make_package(base / "package")
            destination = base / "member-profile"
            destination.mkdir()
            external = base / "external-receipt"
            external.write_text("do not replace\n", encoding="utf-8")
            receipt = destination / install.STATE_NAME
            os.symlink(external, receipt)
            with self.assertRaises(install.InstallError):
                install.install_package(package, destination, "main", apply=True)
            self.assertTrue(receipt.is_symlink())
            self.assertEqual(external.read_text(encoding="utf-8"), "do not replace\n")


if __name__ == "__main__":
    unittest.main()
