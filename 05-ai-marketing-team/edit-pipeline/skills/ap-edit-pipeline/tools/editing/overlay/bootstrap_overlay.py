#!/usr/bin/env python3
"""bootstrap_overlay.py - stage the caption and overlay app outside the pack, and install it there.

ONE job: copy this folder's app source into the member's media workspace and
install its parts THERE, once.

WHY: the installed parts of a node app are tens of thousands of small files.
They must never land inside the pack folder and never inside a cloud-synced
folder, or the sync service will grind for hours. The pack holds the app SOURCE,
which is text. The working copy lives at <media workspace>/overlay-app.

Safe to run again. The source is re-copied every time, so edits are picked up,
and the install only runs when it is missing or the app's parts list changed.

Usage:
    ./bootstrap_overlay.py
    ./bootstrap_overlay.py --check     # report readiness, install nothing
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from media_workspace import check_output_path, workspace_dir  # noqa: E402

APP_FOLDER_NAME = "overlay-app"
SOURCE_FILES = ("package.json", "tsconfig.json", "remotion.config.ts")
INSTALL_MARKER = ".overlay-install-marker"


def app_dir():
    path = os.path.join(workspace_dir(), APP_FOLDER_NAME)
    return check_output_path(path, "the overlay layer")


def copy_source(target):
    os.makedirs(os.path.join(target, "public"), exist_ok=True)
    src_src = os.path.join(HERE, "src")
    dst_src = os.path.join(target, "src")
    if os.path.isdir(dst_src):
        shutil.rmtree(dst_src)
    shutil.copytree(src_src, dst_src)
    for name in SOURCE_FILES:
        shutil.copy2(os.path.join(HERE, name), os.path.join(target, name))


def needs_install(target):
    modules = os.path.join(target, "node_modules")
    if not os.path.isdir(modules):
        return True
    marker = os.path.join(modules, INSTALL_MARKER)
    if not os.path.isfile(marker):
        return True
    return os.path.getmtime(os.path.join(target, "package.json")) > os.path.getmtime(marker)


def status():
    target = app_dir()
    return {
        "app_folder": target,
        "source_staged": os.path.isdir(os.path.join(target, "src")),
        "parts_installed": os.path.isdir(os.path.join(target, "node_modules")),
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "npx": shutil.which("npx"),
        "ready": bool(
            shutil.which("npx")
            and os.path.isdir(os.path.join(target, "node_modules"))
        ),
    }


def bootstrap():
    if not shutil.which("npm"):
        sys.exit(
            "error: the overlay layer needs node, which is not installed yet.\n"
            "       Ask the member first, then run setup_editing.py --install overlay.\n"
            "       Everything else in the edit chain works without it."
        )
    target = app_dir()
    print(f"[overlay] source : {HERE}")
    print(f"[overlay] working copy : {target}")
    os.makedirs(target, exist_ok=True)
    copy_source(target)

    if needs_install(target):
        print("[overlay] installing the app parts, this takes a few minutes the first time.")
        result = subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=target)
        if result.returncode != 0:
            sys.exit("error: the overlay app parts did not install. Check the connection and try again.")
        modules = os.path.join(target, "node_modules")
        os.makedirs(modules, exist_ok=True)
        with open(os.path.join(modules, INSTALL_MARKER), "w", encoding="utf-8") as f:
            f.write("installed\n")
    else:
        print("[overlay] parts already installed and up to date.")

    print(f"[overlay] ready at {target}")
    print(f"[overlay] proof images go in {os.path.join(target, 'public')} before a render.")
    return target


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Stage the caption and overlay app in the media workspace and install it there.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--check", action="store_true", help="Report readiness. Installs nothing.")
    args = p.parse_args(argv)
    if args.check:
        print(json.dumps(status(), indent=2))
        return 0
    bootstrap()
    return 0


if __name__ == "__main__":
    sys.exit(main())
