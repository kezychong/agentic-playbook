#!/usr/bin/env python3
"""setup_editing.py - find or install the two free tools the edit chain needs.

ONE job: tell the agent exactly what is present on this machine, and install
what is missing when the agent asks it to.

Two things are needed for the core chain:
  * ffmpeg (with ffprobe) - the free engine that cuts and re-renders video.
  * a speech-to-text engine with word-level timings - so the cut lands on the
    exact word instead of near it.

One more is needed only for the optional caption and overlay layer:
  * node (with npx) - installed later, the first time the member asks for
    burned-in captions. Never up front.

ENGINE CHOICE, in order of preference:
  1. mlx-whisper   Apple Silicon Macs only. Fast, local, best quality per minute.
  2. openai-whisper Works on any machine. Slower on a plain processor, same
                    output shape once normalised.
  3. whisper.cpp   Fast on plain processors, installed through the system
                   package manager, needs a model file. Detected and used if it
                   is already here, never auto-installed.

Everything installs into a private folder inside the media workspace
(<workspace>/tools-venv), never into the machine's shared setup. Nothing here
touches the member's system beyond ffmpeg and node, which are installed with the
machine's own package manager only when the agent passes --install.

USAGE (agent runs these, never the member):
    ./setup_editing.py --check
    ./setup_editing.py --check --json
    ./setup_editing.py --install engine
    ./setup_editing.py --install ffmpeg
    ./setup_editing.py --install overlay
    ./setup_editing.py --plan          # what WOULD be run, nothing executed

HONESTY: this reports what it finds. It never claims a tool is present without
running the check, and it never silently installs anything.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from media_workspace import workspace_dir  # noqa: E402

VENV_NAME = "tools-venv"
MLX_PACKAGE = "mlx-whisper"
CROSS_PLATFORM_PACKAGE = "openai-whisper"


def is_apple_silicon():
    return platform.system() == "Darwin" and platform.machine().lower() in ("arm64", "aarch64")


def venv_dir():
    return os.path.join(workspace_dir(), VENV_NAME)


def venv_bin(name):
    """Path to a binary inside the private tools environment, if it exists."""
    sub = "Scripts" if os.name == "nt" else "bin"
    suffix = ".exe" if os.name == "nt" else ""
    candidate = os.path.join(venv_dir(), sub, name + suffix)
    return candidate if os.path.isfile(candidate) else None


def find(name):
    """Private tools environment first, then the machine's own path."""
    return venv_bin(name) or shutil.which(name)


def package_manager():
    """The machine's own installer, and how to call it."""
    system = platform.system()
    if system == "Darwin":
        if shutil.which("brew"):
            return {"name": "brew", "install": ["brew", "install"]}
        return {"name": None, "install": None,
                "note": "Homebrew is not on this Mac. It is the usual way to add ffmpeg."}
    if system == "Windows":
        if shutil.which("winget"):
            return {"name": "winget", "install": ["winget", "install", "-e", "--id"]}
        return {"name": None, "install": None,
                "note": "winget was not found. It ships with current Windows versions."}
    for manager, args in (
        ("apt-get", ["sudo", "apt-get", "install", "-y"]),
        ("dnf", ["sudo", "dnf", "install", "-y"]),
        ("pacman", ["sudo", "pacman", "-S", "--noconfirm"]),
    ):
        if shutil.which(manager):
            return {"name": manager, "install": args}
    return {"name": None, "install": None, "note": "No known package manager was found."}


def ffmpeg_package_id():
    system = platform.system()
    if system == "Windows":
        return "Gyan.FFmpeg"
    return "ffmpeg"


def node_package_id():
    system = platform.system()
    if system == "Windows":
        return "OpenJS.NodeJS.LTS"
    return "node"


def detect():
    """What is actually on this machine right now."""
    engines = []
    if find("mlx_whisper"):
        engines.append("mlx")
    if find("whisper"):
        engines.append("whisper")
    for cpp in ("whisper-cli", "whisper.cpp", "main-whisper"):
        if shutil.which(cpp):
            engines.append("whispercpp")
            break

    return {
        "machine": {
            "system": platform.system(),
            "processor": platform.machine(),
            "apple_silicon": is_apple_silicon(),
        },
        "media_workspace": workspace_dir(),
        "tools_environment": venv_dir(),
        "tools_environment_exists": os.path.isdir(venv_dir()),
        "ffmpeg": find("ffmpeg"),
        "ffprobe": find("ffprobe"),
        "engines_found": engines,
        "preferred_engine": engines[0] if engines else None,
        "node": shutil.which("node"),
        "npx": shutil.which("npx"),
        "package_manager": package_manager().get("name"),
        "core_chain_ready": bool(find("ffmpeg") and find("ffprobe") and engines),
        "overlay_layer_ready": bool(shutil.which("node") and shutil.which("npx")),
    }


def plain_summary(state):
    """The sentences the agent can read out loud, with no machine words in them."""
    lines = []
    if state["core_chain_ready"]:
        lines.append("The editing tools are already on this machine. I can edit straight away.")
    else:
        missing = []
        if not (state["ffmpeg"] and state["ffprobe"]):
            missing.append("the one that cuts and re-renders video")
        if not state["engines_found"]:
            missing.append("the one that turns speech into words with exact timings")
        lines.append(
            "Before the first edit I need to set up "
            + " and ".join(missing)
            + ". Both are free, both run on this machine, and nothing is uploaded anywhere."
        )
        if not state["engines_found"]:
            if state["machine"]["apple_silicon"]:
                lines.append(
                    "On this Mac the fast local engine works, so a normal recording "
                    "is done in a few minutes. The first setup downloads about 3GB once."
                )
            else:
                lines.append(
                    "On this machine the slower engine is the one that works. A ten "
                    "minute recording can take a while the first time. I will tell you "
                    "before I start, and I can use a smaller, quicker model if you "
                    "would rather trade a little accuracy for speed."
                )
    if not state["overlay_layer_ready"]:
        lines.append(
            "Burned-in captions and on-screen overlays need one more free tool. "
            "I only set that up if and when you ask for captions."
        )
    if not state["package_manager"]:
        lines.append(
            "This machine has no installer I can drive, so I cannot add the missing "
            "pieces myself. The no-setup road still works: you record, you edit in "
            "whatever editor you already use, and I do everything either side of it."
        )
    return lines


def run(cmd, dry=False):
    print("[setup] " + " ".join(cmd), file=sys.stderr)
    if dry:
        return 0
    return subprocess.run(cmd).returncode


def ensure_venv(dry=False):
    if os.path.isdir(venv_dir()) and (venv_bin("pip") or venv_bin("pip3")):
        return 0
    os.makedirs(workspace_dir(), exist_ok=True)
    return run([sys.executable, "-m", "venv", venv_dir()], dry=dry)


def venv_installer():
    return venv_bin("pip") or venv_bin("pip3")


def install_engine(dry=False):
    """Install the right speech-to-text engine into the private tools environment."""
    code = ensure_venv(dry=dry)
    if code != 0:
        return code
    installer = venv_installer()
    if installer is None:
        if dry:
            installer = os.path.join(venv_dir(), "bin", "pip")
        else:
            print("error: could not create the private tools environment.", file=sys.stderr)
            return 1
    package = MLX_PACKAGE if is_apple_silicon() else CROSS_PLATFORM_PACKAGE
    return run([installer, "install", "--upgrade", package], dry=dry)


def install_with_manager(package_id, label, dry=False):
    manager = package_manager()
    if not manager.get("install"):
        print(
            f"error: cannot install {label} automatically. {manager.get('note', '')}".strip(),
            file=sys.stderr,
        )
        return 1
    return run(list(manager["install"]) + [package_id], dry=dry)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Check for, or install, the free tools the edit chain needs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--check", action="store_true", help="Report what is present. Installs nothing.")
    p.add_argument("--json", action="store_true", help="Print the report as JSON.")
    p.add_argument(
        "--install",
        choices=["ffmpeg", "engine", "overlay", "all"],
        help="Install a missing piece. Ask the member before running this.",
    )
    p.add_argument("--plan", action="store_true", help="Show the commands without running them.")
    args = p.parse_args(argv)

    state = detect()

    if args.install:
        dry = args.plan
        code = 0
        if args.install in ("ffmpeg", "all") and not (state["ffmpeg"] and state["ffprobe"]):
            code |= install_with_manager(ffmpeg_package_id(), "ffmpeg", dry=dry)
        if args.install in ("engine", "all") and not state["engines_found"]:
            code |= install_engine(dry=dry)
        if args.install in ("overlay", "all") and not state["overlay_layer_ready"]:
            code |= install_with_manager(node_package_id(), "node", dry=dry)
        state = detect()
        if args.json:
            print(json.dumps(state, indent=2))
        else:
            for line in plain_summary(state):
                print(line)
        return code

    if args.json:
        print(json.dumps(state, indent=2))
        return 0

    for line in plain_summary(state):
        print(line)
    print("")
    print("Detail for the agent:")
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
