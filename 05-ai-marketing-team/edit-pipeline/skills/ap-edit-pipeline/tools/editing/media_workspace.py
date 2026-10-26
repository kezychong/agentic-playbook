#!/usr/bin/env python3
"""media_workspace.py - where video files are allowed to live, and where they are not.

ONE job: resolve the member's media workspace and refuse to write big media into
a cloud-synced folder or into the content-os workspace.

WHY THIS EXISTS (the law this pack carries from the system it was built from):
  1. Video files are huge. A sync service (iCloud, Dropbox, OneDrive, Google
     Drive, Box, and friends) will upload every intermediate render, eat the
     member's storage plan, and slow the machine to a crawl.
  2. The content-os workspace holds TEXT only: cards, scripts, rules. Media in
     there breaks that promise and can end up inside whatever the member syncs
     their notes with.

So: media lives in a plain local folder outside every synced location. The
default is ~/ContentStudio, overridable with the CONTENT_OS_MEDIA_DIR
environment variable.

Rules enforced here:
  * OUTPUT paths inside a synced folder or inside content-os  -> REFUSE.
  * INPUT paths inside a synced folder                        -> WARN, allow.
    (The member's raw recording often lands in a synced Desktop. Reading it is
    fine; the agent should copy it into the media workspace first.)

Every tool in this folder imports this module, so the law cannot be skipped by
running one step directly.

Checks from anywhere:
    ./media_workspace.py --workspace
    ./media_workspace.py --check "/some/path/master.mp4"
"""

import argparse
import json
import os
import sys

DEFAULT_WORKSPACE_NAME = "ContentStudio"
ENV_WORKSPACE = "CONTENT_OS_MEDIA_DIR"

# Folder names that mean "this is synced to somebody's cloud". Matched against
# each part of the resolved path, case-insensitively, exact or prefix where the
# service appends an account name (e.g. "OneDrive - Acme Ltd").
SYNCED_EXACT = {
    "dropbox",
    "onedrive",
    "google drive",
    "googledrive",
    "my drive",
    "icloud drive",
    "icloud~drive",
    "box",
    "box sync",
    "pcloud drive",
    "mega",
    "meganz",
    "nextcloud",
    "owncloud",
    "proton drive",
    "protondrive",
    "tresorit",
    "creative cloud files",
    "sync.com",
    "idrive-sync",
    "jottacloud",
    "koofr",
}
SYNCED_PREFIXES = (
    "onedrive -",
    "onedrive_",
    "dropbox (",
    "google drive (",
    "box-box",
)
# Path fragments that are always a synced location on macOS.
SYNCED_FRAGMENTS = (
    "/library/mobile documents",
    "/library/cloudstorage",
    "com~apple~clouddocs",
)
# Environment variables the sync clients themselves set.
SYNCED_ENV_VARS = ("OneDrive", "OneDriveCommercial", "OneDriveConsumer")

WORKSPACE_FOLDER_NAME = "content-os"


def home():
    return os.path.expanduser("~")


def real(path):
    """Absolute, symlink-resolved path. macOS turns a synced Desktop into a
    symlink into iCloud, so resolving is what catches it."""
    return os.path.realpath(os.path.abspath(os.path.expanduser(str(path))))


def _parts(path):
    return [p for p in real(path).split(os.sep) if p]


def synced_reason(path):
    """Return a plain-English reason string if this path is inside a cloud-synced
    location, else None. Never raises."""
    resolved = real(path)
    lowered = resolved.replace("\\", "/").lower()

    for fragment in SYNCED_FRAGMENTS:
        if fragment in lowered:
            return "it sits inside a folder that syncs to iCloud"

    for part in _parts(resolved):
        p = part.lower()
        if p in SYNCED_EXACT:
            return f"it sits inside a folder called '{part}', which syncs to the cloud"
        for prefix in SYNCED_PREFIXES:
            if p.startswith(prefix):
                return f"it sits inside a folder called '{part}', which syncs to the cloud"

    for var in SYNCED_ENV_VARS:
        root = os.environ.get(var)
        if root and lowered.startswith(real(root).replace("\\", "/").lower()):
            return "it sits inside a cloud-synced folder this machine has set up"

    return None


def inside_text_workspace(path):
    """True when the path is inside a content-os workspace (text only, no media)."""
    return any(part.lower() == WORKSPACE_FOLDER_NAME for part in _parts(path))


def workspace_dir(create=False):
    """The media workspace: env override, else ~/ContentStudio."""
    configured = os.environ.get(ENV_WORKSPACE)
    base = real(configured) if configured else os.path.join(home(), DEFAULT_WORKSPACE_NAME)
    if create:
        os.makedirs(base, exist_ok=True)
    return base


def run_dir(name, create=True):
    """A per-recording folder inside the media workspace, e.g. runs/2026-08-24-my-idea."""
    safe = "".join(c if (c.isalnum() or c in "-_.") else "-" for c in str(name)).strip("-")
    path = os.path.join(workspace_dir(create=create), "runs", safe or "untitled")
    if create:
        os.makedirs(path, exist_ok=True)
    return path


def check_output_path(path, tool="this step"):
    """Hard gate for anything that WRITES media. Exits with a plain message when
    the destination is synced or inside the text workspace."""
    if inside_text_workspace(path):
        sys.exit(
            f"error: {tool} will not write video into the content-os workspace.\n"
            f"       That folder holds text only: cards, scripts, rules.\n"
            f"       Write media into {workspace_dir()} instead."
        )
    reason = synced_reason(path)
    if reason:
        sys.exit(
            f"error: {tool} will not write video to {path},\n"
            f"       because {reason}.\n"
            f"       Big video files fill up a sync plan and slow the machine down.\n"
            f"       Write media into {workspace_dir()} instead, or set the\n"
            f"       {ENV_WORKSPACE} environment variable to a different local folder."
        )
    return real(path)


def check_input_path(path, tool="this step"):
    """Soft gate for anything that READS media. Warns, does not stop."""
    reason = synced_reason(path)
    if reason:
        print(
            f"[{tool}] note: the source file is in a synced folder ({reason}).\n"
            f"[{tool}] reading it is fine. Copy it into {workspace_dir()} before a long "
            f"job so the sync service does not fight the render.",
            file=sys.stderr,
        )
    return real(path)


def report(path=None):
    """Machine-readable status for the agent."""
    ws = workspace_dir()
    data = {
        "media_workspace": ws,
        "media_workspace_exists": os.path.isdir(ws),
        "media_workspace_is_synced": synced_reason(ws) is not None,
        "media_workspace_synced_reason": synced_reason(ws),
        "env_override": os.environ.get(ENV_WORKSPACE) or None,
    }
    if path:
        data["checked_path"] = real(path)
        data["checked_path_synced_reason"] = synced_reason(path)
        data["checked_path_in_text_workspace"] = inside_text_workspace(path)
        data["safe_for_media_output"] = (
            synced_reason(path) is None and not inside_text_workspace(path)
        )
    return data


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Resolve the media workspace and test whether a path is safe for video files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--workspace", action="store_true", help="Print the media workspace path.")
    p.add_argument("--check", metavar="PATH", help="Report whether PATH is safe for media.")
    p.add_argument("--create", action="store_true", help="Create the media workspace if missing.")
    args = p.parse_args(argv)

    if args.create:
        workspace_dir(create=True)
    if args.workspace and not args.check:
        print(workspace_dir())
        return 0
    print(json.dumps(report(args.check), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
