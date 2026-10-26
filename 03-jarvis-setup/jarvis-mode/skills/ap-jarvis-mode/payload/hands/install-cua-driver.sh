#!/usr/bin/env bash
# Optional CuaDriver installer for the member's main computer.
# The default is a plan. Network access and /Applications changes require
# --apply. No package install is run by the member package tests.
set -euo pipefail

# These three values are intentionally immutable pins. A future release gets
# a reviewed package change rather than an environment override.
URL="https://github.com/trycua/cua/releases/download/cua-driver-rs-v0.23.2/cua-driver-rs-0.23.2-darwin-universal.tar.gz"
SHA256="9e521b16c8606896f20003f4d20ae62070a1cb3c8d33152d9d0593f62234fbb0"
TEAM_ID="YCK386LBJ7"
TEST_ROOT="${JARVIS_CUA_DRIVER_TEST_ROOT:-}"
if [[ -n "$TEST_ROOT" ]]; then
  canonical_test_root="$(cd "$TEST_ROOT" 2>/dev/null && pwd -P)" || canonical_test_root=""
  [[ "$canonical_test_root" == /private/tmp/jarvis-driver-test-* && "$TEST_ROOT" == "$canonical_test_root" && ! -L "$TEST_ROOT" ]] || {
    printf '%s\n' 'install-cua-driver.sh: test root must be a canonical /private/tmp/jarvis-driver-test-* directory' >&2
    exit 2
  }
  TARGET="$TEST_ROOT/Applications/CuaDriver.app"
  BACKUP_ROOT="$TEST_ROOT/state/driver-backups"
else
  TARGET="/Applications/CuaDriver.app"
  BACKUP_ROOT="${JARVIS_CUA_DRIVER_BACKUP_DIR:-$HOME/.local/state/jarvis-hands/driver-backups}"
fi
MODE="plan"

usage() {
  sed -n '1,8p' "$0"
  printf '%s\n' "  --apply  download, verify, back up and install" \
                "  --undo   restore the last backed-up app" \
                "  --plan   print the pinned plan (default)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) MODE="apply" ;;
    --undo) MODE="undo" ;;
    --plan|--dry-run) MODE="plan" ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'install-cua-driver.sh: unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

case "$TARGET" in
  /Applications/CuaDriver.app|"$TEST_ROOT"/Applications/CuaDriver.app) ;;
  *) printf '%s\n' 'install-cua-driver.sh: target is outside the safe install scope' >&2; exit 2 ;;
esac
[[ "$SHA256" =~ ^[0-9a-fA-F]{64}$ ]] || {
  printf '%s\n' 'install-cua-driver.sh: the pinned SHA-256 must be 64 hex characters' >&2
  exit 2
}
[[ "$TEAM_ID" =~ ^[A-Za-z0-9]+$ ]] || {
  printf '%s\n' 'install-cua-driver.sh: the pinned team id is invalid' >&2
  exit 2
}

RECEIPT="$BACKUP_ROOT/last-install.env"

tree_hash() {
  /usr/bin/python3 - "$1" <<'PY'
import hashlib, os, stat, sys
root = os.path.abspath(sys.argv[1])
h = hashlib.sha256()
for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
    dirs.sort(); files.sort()
    for name in dirs + files:
        path = os.path.join(base, name)
        rel = os.path.relpath(path, root).encode("utf-8", "surrogateescape")
        mode = os.lstat(path).st_mode
        h.update(rel + b"\0" + str(stat.S_IMODE(mode)).encode() + b"\0")
        if stat.S_ISLNK(mode):
            target = os.readlink(path)
            resolved = os.path.realpath(path)
            if os.path.commonpath([root, resolved]) != root:
                raise SystemExit("unsafe symlink: " + target)
            h.update(b"L" + target.encode("utf-8", "surrogateescape") + b"\0")
        elif stat.S_ISREG(mode):
            h.update(b"F")
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
print(h.hexdigest())
PY
}

safe_backup_root() {
  if ! /usr/bin/python3 - "$BACKUP_ROOT" <<'PY'
import os, stat, sys
path = os.path.abspath(sys.argv[1])
current = os.path.sep
for part in [part for part in path.split(os.path.sep) if part]:
    current = os.path.join(current, part)
    try:
        mode = os.lstat(current).st_mode
    except FileNotFoundError:
        continue
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise SystemExit(1)
PY
  then
    printf '%s\n' 'install-cua-driver.sh: backup path contains a symlink' >&2
    exit 2
  fi
  mkdir -p "$BACKUP_ROOT"
  chmod 700 "$BACKUP_ROOT"
}

if [[ "$MODE" == "plan" ]]; then
  printf '%s\n' 'CuaDriver plan (nothing downloaded or changed)' \
    "  url: $URL" \
    "  sha256: $SHA256" \
    "  team: $TEAM_ID" \
    "  target: $TARGET" \
    "  backups: $BACKUP_ROOT" \
    '  apply: run this script with --apply after reviewing the pin'
  exit 0
fi

if [[ "$MODE" == "undo" ]]; then
  safe_backup_root
  [[ -f "$RECEIPT" && ! -L "$RECEIPT" ]] || {
    printf '%s\n' 'install-cua-driver.sh: no driver install receipt exists to undo' >&2
    exit 2
  }
  receipt_target="$(sed -n 's/^target=//p' "$RECEIPT" | head -1)"
  receipt_backup="$(sed -n 's/^backup=//p' "$RECEIPT" | head -1)"
  receipt_kind="$(sed -n 's/^backup_kind=//p' "$RECEIPT" | head -1)"
  receipt_hash="$(sed -n 's/^installed_hash=//p' "$RECEIPT" | head -1)"
  [[ "$receipt_target" == "$TARGET" ]] || {
    printf '%s\n' 'install-cua-driver.sh: the receipt target is not within the safe install scope' >&2
    exit 2
  }
  [[ "$receipt_hash" =~ ^[0-9a-f]{64}$ ]] || {
    printf '%s\n' 'install-cua-driver.sh: the receipt has no valid installed-app hash' >&2
    exit 2
  }
  [[ -d "$TARGET" && ! -L "$TARGET" ]] || {
    printf '%s\n' 'install-cua-driver.sh: the installed app is missing or unsafe; nothing was changed' >&2
    exit 2
  }
  current_hash="$(tree_hash "$TARGET")" || {
    printf '%s\n' 'install-cua-driver.sh: the installed app could not be verified; nothing was changed' >&2
    exit 2
  }
  [[ "$current_hash" == "$receipt_hash" ]] || {
    printf '%s\n' 'install-cua-driver.sh: the installed app changed after this receipt; nothing was changed' >&2
    exit 2
  }
  claim="$BACKUP_ROOT/.last-install.undo.$$"
  mv "$RECEIPT" "$claim"
  restore_claim() { [[ -e "$claim" && ! -e "$RECEIPT" ]] && mv "$claim" "$RECEIPT" || true; }
  trap restore_claim ERR
  if [[ "$receipt_kind" == "none" ]]; then
    removed="$BACKUP_ROOT/.undo-removed-$(/usr/bin/python3 -c 'import uuid; print(uuid.uuid4().hex)')-CuaDriver.app"
    mv "$TARGET" "$removed"
    if ! rm -f "$claim"; then
      mv "$removed" "$TARGET"
      restore_claim
      printf '%s\n' 'install-cua-driver.sh: undo receipt could not be consumed; the app was restored' >&2
      exit 1
    fi
    rm -rf "$removed"
    trap - ERR
    printf '%s\n' "removed installed app: $TARGET" "no previous app was recorded"
    exit 0
  fi
  [[ "$receipt_backup" == "$BACKUP_ROOT"/* ]] || {
    printf '%s\n' 'install-cua-driver.sh: the receipt backup is not within the safe backup scope' >&2
    exit 2
  }
  [[ -d "$receipt_backup" && ! -L "$receipt_backup" ]] || {
    printf '%s\n' 'install-cua-driver.sh: the recorded backup is missing; nothing was changed' >&2
    exit 2
  }
  rollback="$BACKUP_ROOT/rollback-$(/usr/bin/python3 -c 'import uuid; print(uuid.uuid4().hex)')-CuaDriver.app"
  mv "$TARGET" "$rollback"
  if ! mv "$receipt_backup" "$TARGET"; then
    mv "$rollback" "$TARGET"
    restore_claim
    printf '%s\n' 'install-cua-driver.sh: restore failed; the installed app and receipt were put back' >&2
    exit 1
  fi
  if ! rm -f "$claim"; then
    mv "$TARGET" "$receipt_backup"
    mv "$rollback" "$TARGET"
    restore_claim
    printf '%s\n' 'install-cua-driver.sh: undo receipt could not be consumed; the installed app was restored' >&2
    exit 1
  fi
  trap - ERR
  printf '%s\n' "restored: $TARGET" "saved current app: $rollback"
  exit 0
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/cua-driver.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT
archive="$tmp/driver.tar.gz"

curl --fail --location --proto '=https' --tlsv1.2 --output "$archive" "$URL"
actual="$(shasum -a 256 "$archive" | awk '{print $1}')"
[[ "$actual" == "$SHA256" ]] || {
  printf 'install-cua-driver.sh: SHA-256 mismatch (got %s)\n' "$actual" >&2
  exit 1
}

while IFS= read -r item; do
  case "$item" in
    /*|../*|*/../*|*'/..')
      printf 'install-cua-driver.sh: unsafe archive entry: %s\n' "$item" >&2
      exit 1
      ;;
  esac
done < <(tar -tzf "$archive")

app_entry="$(tar -tzf "$archive" | awk '/(^|\/)CuaDriver\.app\/$/ {print; exit}')"
[[ -n "$app_entry" ]] || {
  printf '%s\n' 'install-cua-driver.sh: archive does not contain a CuaDriver.app directory' >&2
  exit 1
}
mkdir "$tmp/extracted"
# Extract exactly the signed app subtree after validating member and link paths.
/usr/bin/python3 - "$archive" "$tmp/extracted" <<'PY'
import os, posixpath, sys, tarfile
archive, out = sys.argv[1:]
with tarfile.open(archive, "r:gz") as tf:
    members = []
    app_root = None
    for item in tf.getmembers():
        name = item.name
        norm = posixpath.normpath(name)
        if name.startswith("/") or norm == ".." or norm.startswith("../"):
            raise SystemExit("unsafe archive path")
        parts = norm.split("/")
        try:
            index = parts.index("CuaDriver.app")
        except ValueError:
            continue
        root = "/".join(parts[:index + 1])
        if app_root is None:
            app_root = root
        if root != app_root:
            raise SystemExit("more than one app root")
        if item.issym() or item.islnk():
            raise SystemExit("archive links are not allowed")
        if not (item.isdir() or item.isfile()):
            raise SystemExit("archive special files are not allowed")
        members.append(item)
    if not app_root or not members:
        raise SystemExit("missing app")
    tf.extractall(out, members=members)
PY
app="$(find "$tmp/extracted" -type d -name CuaDriver.app -print -quit)"
[[ -n "$app" && -d "$app" ]] || {
  printf '%s\n' 'install-cua-driver.sh: archive does not contain CuaDriver.app' >&2
  exit 1
}
# Recheck the extracted tree before any signature or target operation.
tree_hash "$app" >/dev/null || {
  printf '%s\n' 'install-cua-driver.sh: extracted app contains an unsafe link' >&2
  exit 1
}

codesign --verify --deep --strict "$app"
team="$(codesign -dv --verbose=4 "$app" 2>&1 | awk -F= '$1 == "TeamIdentifier" {print $2; exit}')"
[[ "$team" == "$TEAM_ID" ]] || {
  printf 'install-cua-driver.sh: signing team mismatch (got %s)\n' "${team:-missing}" >&2
  exit 1
}
spctl --assess --type execute --verbose "$app" >/dev/null

safe_backup_root
backup="$BACKUP_ROOT/$(/usr/bin/python3 -c 'import uuid; print(uuid.uuid4().hex)')-CuaDriver.app"
target_parent="${TARGET%/*}"
mkdir -p "$target_parent"
[[ ! -L "$target_parent" && ! -L "$TARGET" ]] || {
  printf '%s\n' 'install-cua-driver.sh: target path contains a symlink' >&2
  exit 2
}
if [[ -e "$RECEIPT" && ( ! -f "$RECEIPT" || -L "$RECEIPT" ) ]]; then
  printf '%s\n' 'install-cua-driver.sh: install receipt path is unsafe' >&2
  exit 2
fi
target_tmp="$target_parent/.CuaDriver.app.install.$$"
old_target="$target_parent/.CuaDriver.app.previous.$$"
receipt_tmp="$BACKUP_ROOT/.last-install.env.$$"
ditto "$app" "$target_tmp"
backup_kind="app"
if [[ -d "$TARGET" ]]; then
  tree_hash "$TARGET" >/dev/null || {
    printf '%s\n' 'install-cua-driver.sh: existing app contains an unsafe link' >&2
    exit 2
  }
  ditto "$TARGET" "$backup"
else
  backup_kind="none"
fi
restore_on_error() {
  rm -rf "$target_tmp"
  rm -f "$receipt_tmp"
  if [[ "${receipt_committed:-0}" -eq 1 ]]; then rm -f "$RECEIPT"; fi
  if [[ -d "$old_target" ]]; then
    rm -rf "$TARGET"
    mv "$old_target" "$TARGET"
  elif [[ "$backup_kind" == "none" ]]; then
    rm -rf "$TARGET"
  fi
}
receipt_committed=0
trap restore_on_error ERR
if [[ -d "$TARGET" ]]; then mv "$TARGET" "$old_target"; fi
mv "$target_tmp" "$TARGET"
installed_hash="$(tree_hash "$TARGET")"
printf 'target=%s\nbackup=%s\nbackup_kind=%s\ninstalled_hash=%s\ninstalled_at=%s\n' \
  "$TARGET" "$backup" "$backup_kind" "$installed_hash" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$receipt_tmp"
chmod 600 "$receipt_tmp"
mv "$receipt_tmp" "$RECEIPT"
receipt_committed=1
rm -rf "$old_target"
trap - ERR
printf '%s\n' "installed: $TARGET" "backup: $backup" "undo: $0 --undo"
