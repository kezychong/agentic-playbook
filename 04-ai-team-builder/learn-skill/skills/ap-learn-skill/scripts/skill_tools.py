#!/usr/bin/env python3
"""Agentic Playbook skill helpers — by Kezy.

Source-adapted, unexecuted helper. Requires an explicit --workspace path; it never
searches operator profiles or credential files. Operates on workspace/skills and
workspace/exports, inbox and backups. Read every file before approved installation.
Commands: list, zip NAME [--for-others], check-zip FILE,
install FOLDER --category CATEGORY --approve-install.
--for-others requires --reviewed-for-sharing, a human review acknowledgment.
Pattern screening is limited and cannot prove a package contains no private data.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

# Assigned only from the caller's explicit workspace in main().
WORKSPACE = SKILLS = ZIPS = HOLD = BACKUPS = None

SKIP_PARTS = {"__pycache__", "backups", ".git", "node_modules"}
SKIP_NAMES = {".env", "credentials", ".DS_Store"}
KEY_SHAPES = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|hnk_[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,}"
    r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\b\d{8,10}:[A-Za-z0-9_-]{30,}\b)")
TEXT_EXT = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css", ".toml", ".csv"}


def frontmatter_name(skill_md: Path) -> str:
    try:
        head = skill_md.read_text(encoding="utf-8", errors="ignore").split("---")[1]
    except (IndexError, OSError):
        return skill_md.parent.name
    m = re.search(r"^name:\s*['\"]?([^'\"\n]+)", head, re.M)
    return m.group(1).strip() if m else skill_md.parent.name


def all_skills() -> dict[str, Path]:
    found = {}
    for md in SKILLS.rglob("SKILL.md"):
        rel = md.relative_to(SKILLS).parts
        if any(p.startswith(".") for p in rel) or any(p in SKIP_PARTS for p in rel):
            continue
        found.setdefault(frontmatter_name(md), md.parent)
    return found


def cmd_list(_args) -> int:
    skills = all_skills()
    builtin = set()
    try:
        for line in (SKILLS / ".bundled_manifest").read_text().splitlines():
            if ":" in line:
                builtin.add(line.split(":", 1)[0].strip())
    except OSError:
        pass
    hub = set()
    try:
        hub = set(json.loads((SKILLS / ".hub" / "lock.json").read_text()).get("installed", {}))
    except (OSError, ValueError):
        pass
    agent = set()
    try:
        for name, rec in json.loads((SKILLS / ".usage.json").read_text()).items():
            if isinstance(rec, dict) and rec.get("created_by") == "agent":
                agent.add(name)
    except (OSError, ValueError):
        pass
    groups = {"Agent-created": [], "Local or adapted (provenance not verified)": [],
              "Recorded as bundled or hub-installed": []}
    for name, folder in sorted(skills.items()):
        if name in agent:
            groups["Agent-created"].append(name)
        elif name in builtin or name in hub:
            groups["Recorded as bundled or hub-installed"].append(name)
        else:
            tag = " (adapted source copy)" if (folder / "_ORIGINAL-SKILL.md").exists() else ""
            groups["Local or adapted (provenance not verified)"].append(name + tag)
    for title, names in groups.items():
        print(f"{title}: {len(names)}")
        print("  " + ", ".join(names) if names else "  none")
    return 0


def files_to_pack(folder: Path) -> list[Path]:
    out = []
    for f in sorted(folder.rglob("*")):
        rel = f.relative_to(folder).parts
        if f.is_symlink() or not f.is_file() or any(p in SKIP_PARTS or p.startswith(".") for p in rel):
            continue
        if f.name in SKIP_NAMES or ".bak" in f.name or f.suffix == ".pyc" or f.stat().st_size > 20_000_000:
            continue
        out.append(f)
    return out


def secrets_in(files: list[Path]) -> list[str]:
    hits = []
    for f in files:
        if f.suffix.lower() not in TEXT_EXT and f.stat().st_size > 2_000_000:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if KEY_SHAPES.search(text):
            hits.append(f"{f.name}: holds something shaped like a key or token")
    return hits


def cmd_zip(args) -> int:
    skills = all_skills()
    folder = skills.get(args.name)
    if folder is None:
        close = [n for n in skills if args.name.lower() in n.lower()]
        print(f"No skill named {args.name}." + (f" Close matches: {', '.join(close[:8])}" if close else ""))
        return 2
    files = files_to_pack(folder)
    hits = secrets_in(files)
    if hits:
        print("REFUSED: this skill holds a secret, so it was not zipped.")
        print("\n".join(hits))
        return 1
    if args.for_others and not args.reviewed_for_sharing:
        print("REFUSED: human privacy and rights review acknowledgment required.")
        return 1
    ZIPS.mkdir(parents=True, exist_ok=True)
    dest = ZIPS / f"{args.name}-{dt.date.today().isoformat()}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, Path(args.name) / f.relative_to(folder))
    print(f"zipped {len(files)} files: {dest}")
    return 0


def cmd_check_zip(args) -> int:
    src = Path(args.zip).expanduser()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    hold = HOLD / f"{src.stem}-{stamp}"
    hold.mkdir(parents=True)
    with zipfile.ZipFile(src) as z:
        if len(z.infolist()) > 10000 or sum(i.file_size for i in z.infolist()) > 100_000_000:
            print("REFUSED: archive exceeds review limits; no extraction performed.")
            return 1
        for info in z.infolist():
            target = (hold / info.filename).resolve()
            if not target.is_relative_to(hold.resolve()) or info.filename.startswith("/"):
                print(f"REFUSED: unsafe path inside the zip: {info.filename}")
                shutil.rmtree(hold)
                return 1
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                print(f"REFUSED: the zip holds a link: {info.filename}")
                shutil.rmtree(hold)
                return 1
        z.extractall(hold)
    mds = [m for m in hold.rglob("SKILL.md") if "__MACOSX" not in m.parts]
    if len(mds) != 1:
        print(f"Found {len(mds)} SKILL.md files, need exactly 1. Holding folder: {hold}")
        return 2
    skill_dir = mds[0].parent
    name = frontmatter_name(mds[0])
    print(f"skill name: {name}")
    print(f"holding folder: {skill_dir}")
    print(f"already installed: {'yes, at ' + str(all_skills()[name]) if name in all_skills() else 'no'}")
    flags = {"runs code": [], "reaches the internet": [], "reads keys or secrets": [],
             "sets a timer": [], "talks to Claude Code, not Hermes": []}
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file() or "__MACOSX" in f.parts:
            continue
        rel = f.relative_to(skill_dir)
        print(f"  {rel} ({f.stat().st_size} bytes)")
        if f.suffix in {".py", ".sh", ".js", ".ts", ".rb"}:
            flags["runs code"].append(str(rel))
        text = f.read_text(encoding="utf-8", errors="ignore") if f.stat().st_size < 2_000_000 else ""
        if re.search(r"curl |wget |requests\.|urllib|fetch\(|https?://", text):
            flags["reaches the internet"].append(str(rel))
        is_code = f.suffix in {".py", ".sh", ".js", ".ts", ".rb"}
        secret_pat = (r"\.env\b|[A-Z_]*API_KEY|[A-Z_]+_TOKEN\b|credentials|password|secret_key" if is_code
                      else r"(^|[\s`'\"/])\.env\b|/credentials\b|[A-Z_]+_API_KEY=")
        if re.search(secret_pat, text):
            flags["reads keys or secrets"].append(str(rel))
        if re.search(r"\bcrontab\b|\bcron (create|add|edit)\b|launchd|launchctl|\.plist\b", text, re.I):
            flags["sets a timer"].append(str(rel))
        if re.search(r"If you are Claude Code|~/\.claude/skills|~/\.codex/skills", text):
            flags["talks to Claude Code, not Hermes"].append(str(rel))
    for k, v in flags.items():
        if v:
            print(f"FLAG {k}: {', '.join(v[:6])}")
    print("Nothing is installed yet. Read every file, then ask the owner if anything is flagged.")
    return 0


def cmd_install(args) -> int:
    if not args.approve_install:
        print("REFUSED: explicit --approve-install acknowledgment required.")
        return 1
    src = Path(args.folder).expanduser().resolve()
    if not src.is_relative_to(HOLD.resolve()) or not (src / "SKILL.md").exists():
        print("Install only from a holding folder made by check-zip (one with a SKILL.md).")
        return 2
    name = frontmatter_name(src / "SKILL.md")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", name) or not re.fullmatch(r"[a-z0-9-]{1,40}", args.category):
        print(f"Unsafe skill or category name: {name} / {args.category}")
        return 2
    if any(p.is_symlink() for p in src.rglob("*")):
        print("REFUSED: installation source contains symbolic links.")
        return 1
    hits = secrets_in(files_to_pack(src))
    if hits:
        print("REFUSED: potential credential material found; review locally.")
        return 1
    existing = all_skills().get(name)
    dest = SKILLS / args.category / name
    if existing:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        BACKUPS.mkdir(parents=True, exist_ok=True)
        shutil.move(str(existing), str(BACKUPS / f"{name}-{stamp}"))
        print(f"old copy moved to {BACKUPS / f'{name}-{stamp}'}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__MACOSX", "INSTALL.md", ".DS_Store"))
    print(f"installed {name} at {dest}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True, help="Explicit approved local staging workspace")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    z = sub.add_parser("zip"); z.add_argument("name"); z.add_argument("--for-others", action="store_true"); z.add_argument("--reviewed-for-sharing", action="store_true"); z.set_defaults(fn=cmd_zip)
    c = sub.add_parser("check-zip"); c.add_argument("zip"); c.set_defaults(fn=cmd_check_zip)
    i = sub.add_parser("install"); i.add_argument("folder"); i.add_argument("--category", required=True); i.add_argument("--approve-install", action="store_true"); i.set_defaults(fn=cmd_install)
    args = ap.parse_args()
    global WORKSPACE, SKILLS, ZIPS, HOLD, BACKUPS
    WORKSPACE = Path(args.workspace).expanduser().resolve()
    SKILLS = WORKSPACE / "skills"
    ZIPS = WORKSPACE / "exports" / "skill-zips"
    HOLD = WORKSPACE / "inbox"
    BACKUPS = WORKSPACE / "backups" / "skills"
    for path in (SKILLS, ZIPS, HOLD, BACKUPS):
        if not path.resolve().is_relative_to(WORKSPACE):
            print("REFUSED: workspace paths must not escape through symbolic links.")
            return 1
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
