#!/usr/bin/env python3
"""Remote, profile-scoped transaction for install-hands.sh."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import uuid


def fail(message):
    raise RuntimeError(message)


def validate_profile_home(raw, profile):
    if not raw or not os.path.isabs(raw) or any(ord(ch) < 32 for ch in raw):
        fail("profile home must be an absolute path without control characters")
    if ".." in raw.split(os.sep) or os.path.basename(os.path.normpath(raw)) != profile:
        fail("profile home does not match the selected profile")
    return os.path.normpath(raw)


def reject_symlink_components(path, allow_missing=True):
    path = os.path.abspath(path)
    current = os.path.sep
    for part in [part for part in path.split(os.sep) if part]:
        current = os.path.join(current, part)
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            if allow_missing:
                continue
            fail("required path is missing")
        if stat.S_ISLNK(mode):
            fail("path contains a symlink")
        if current != path and not stat.S_ISDIR(mode):
            fail("path contains a non-directory component")


def remove(path):
    if not os.path.lexists(path):
        return
    if os.path.islink(path) or not os.path.isdir(path):
        os.unlink(path)
    else:
        shutil.rmtree(path)


def digest(path):
    if not os.path.lexists(path):
        return None
    h = hashlib.sha256()
    if os.path.islink(path):
        h.update(b"L" + os.readlink(path).encode("utf-8", "surrogateescape"))
        return h.hexdigest()
    if os.path.isfile(path):
        h.update(b"F")
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    for base, dirs, files in os.walk(path, topdown=True, followlinks=False):
        dirs.sort(); files.sort()
        for name in dirs + files:
            item = os.path.join(base, name)
            rel = os.path.relpath(item, path).encode("utf-8", "surrogateescape")
            mode = os.lstat(item).st_mode
            h.update(rel + b"\0" + str(stat.S_IMODE(mode)).encode() + b"\0")
            if stat.S_ISLNK(mode):
                fail("staged or installed tree contains a symlink")
            if stat.S_ISREG(mode):
                h.update(b"F")
                with open(item, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                        h.update(chunk)
    return h.hexdigest()


def atomic_json(path, doc):
    parent = os.path.dirname(path)
    tmp = os.path.join(parent, ".%s.%s.tmp" % (os.path.basename(path), uuid.uuid4().hex))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
            fh.write("\n")
            fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def paths(profile_home):
    hands = os.path.join(profile_home, "jarvis", "hands")
    return {
        "command": os.path.join(hands, "bin", "ap-macbook-hands"),
        "transaction": os.path.join(hands, "bin", "install-hands-transaction.py"),
        "skill": os.path.join(profile_home, "skills", "agents", "ap-macbook-hands"),
        "config": os.path.join(hands, "config.json"),
        "link": os.path.join(hands, "ap-macbook-hands"),
    }


def seal(profile_home, profile, stage):
    target = paths(profile_home)
    hands = os.path.join(profile_home, "jarvis", "hands")
    backups = os.path.join(hands, "install-backups")
    receipt = os.path.join(hands, "install-receipt.json")
    reject_symlink_components(profile_home, allow_missing=False)
    reject_symlink_components(hands)
    reject_symlink_components(stage, allow_missing=False)
    if os.path.commonpath([profile_home, os.path.abspath(stage)]) != profile_home:
        fail("stage is outside the selected profile")
    staged = {"command": os.path.join(stage, "ap-macbook-hands"),
              "transaction": os.path.join(stage, "install-hands-transaction.py"),
              "skill": os.path.join(stage, "skill"),
              "config": os.path.join(stage, "config.json")}
    for item in staged.values():
        reject_symlink_components(item, allow_missing=False)
    with open(staged["config"], "r", encoding="utf-8") as fh:
        config = json.load(fh)
    if (config.get("profile") != profile or config.get("profile_home") != profile_home
            or config.get("state") != os.path.join(hands, "state")):
        fail("staged config does not match the selected profile")
    if os.path.lexists(receipt):
        fail("an install receipt already exists; check or undo it first")
    os.makedirs(backups, mode=0o700, exist_ok=True)
    reject_symlink_components(backups, allow_missing=False)
    os.chmod(hands, 0o700); os.chmod(backups, 0o700)
    backup = os.path.join(backups, uuid.uuid4().hex)
    os.mkdir(backup, 0o700)
    moved = []
    installed = []
    try:
        for name, dest in target.items():
            if os.path.lexists(dest):
                old = os.path.join(backup, name)
                os.makedirs(os.path.dirname(old), exist_ok=True)
                os.replace(dest, old)
                moved.append((dest, old))
        os.makedirs(os.path.dirname(target["command"]), mode=0o700, exist_ok=True)
        os.makedirs(os.path.dirname(target["skill"]), mode=0o755, exist_ok=True)
        os.replace(staged["command"], target["command"]); installed.append(target["command"])
        os.replace(staged["transaction"], target["transaction"]); installed.append(target["transaction"])
        os.replace(staged["skill"], target["skill"]); installed.append(target["skill"])
        os.replace(staged["config"], target["config"]); installed.append(target["config"])
        os.chmod(target["command"], 0o755); os.chmod(target["transaction"], 0o755)
        os.chmod(target["config"], 0o600)
        for base, dirs, files in os.walk(target["skill"]):
            os.chmod(base, 0o755)
            for name in files: os.chmod(os.path.join(base, name), 0o644)
        link_tmp = target["link"] + "." + uuid.uuid4().hex + ".tmp"
        os.symlink(target["command"], link_tmp)
        os.replace(link_tmp, target["link"]); installed.append(target["link"])
        doc = {"schema": 1, "profile": profile, "profile_home": profile_home,
               "backup": backup, "targets": {name: {"path": path, "hash": digest(path)}
                                                for name, path in target.items()}}
        atomic_json(receipt, doc)
    except Exception:
        for item in reversed(installed): remove(item)
        for dest, old in reversed(moved):
            if os.path.lexists(old): os.replace(old, dest)
        remove(backup)
        raise
    finally:
        remove(stage)


def undo(profile_home, profile):
    target = paths(profile_home)
    hands = os.path.join(profile_home, "jarvis", "hands")
    receipt = os.path.join(hands, "install-receipt.json")
    reject_symlink_components(receipt, allow_missing=False)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(receipt, flags), "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    backup = doc.get("backup", "")
    backup_root = os.path.join(hands, "install-backups")
    if (doc.get("schema") != 1 or doc.get("profile") != profile
            or doc.get("profile_home") != profile_home
            or os.path.commonpath([backup_root, os.path.abspath(backup)]) != backup_root):
        fail("install receipt is outside the selected profile")
    reject_symlink_components(backup, allow_missing=False)
    for name, entry in doc.get("targets", {}).items():
        if name not in target or entry.get("path") != target[name] or digest(target[name]) != entry.get("hash"):
            fail("installed hands files changed after this receipt")
    quarantine = os.path.join(backup_root, ".undo-" + uuid.uuid4().hex)
    os.mkdir(quarantine, 0o700)
    current = []
    restored = []
    try:
        for name, dest in target.items():
            if os.path.lexists(dest):
                held = os.path.join(quarantine, name)
                os.replace(dest, held); current.append((dest, held))
            old = os.path.join(backup, name)
            if os.path.lexists(old):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                os.replace(old, dest); restored.append((dest, old))
        os.unlink(receipt)
    except Exception:
        for dest, old in reversed(restored):
            if os.path.lexists(dest): os.replace(dest, old)
        for dest, held in reversed(current):
            if os.path.lexists(held): os.replace(held, dest)
        raise
    remove(quarantine); remove(backup)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seal", "undo"))
    parser.add_argument("profile_home")
    parser.add_argument("profile")
    parser.add_argument("stage", nargs="?")
    args = parser.parse_args()
    home = validate_profile_home(args.profile_home, args.profile)
    if args.action == "seal":
        if not args.stage: fail("seal needs a stage")
        seal(home, args.profile, args.stage)
    else:
        undo(home, args.profile)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("hands install transaction: %s" % exc, file=sys.stderr)
        raise SystemExit(1)
