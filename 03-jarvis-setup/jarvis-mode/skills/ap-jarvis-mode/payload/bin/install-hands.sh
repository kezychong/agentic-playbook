#!/usr/bin/env bash
# Mac main device only. Hands (CuaDriver) is an OPTIONAL extra: it is never
# required by, and never blocks, the core JARVIS Mode install. Windows members
# skip this script entirely.
#
# Install, check or undo one profile-scoped hands command and skill.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MINI="${JARVIS_HANDS_MINI:-}"
PROFILE="${JARVIS_HANDS_PROFILE:-}"
PROFILE_HOME="${JARVIS_HANDS_PROFILE_HOME:-}"
HOSTS="${JARVIS_HANDS_HOSTS:-}"
DRIVER="${JARVIS_HANDS_DRIVER:-/Applications/CuaDriver.app/Contents/MacOS/cua-driver}"
RSYNC="${JARVIS_HANDS_RSYNC:-rsync}"
SSH="${JARVIS_HANDS_SSH:-ssh}"
SRC_BIN="$REPO_ROOT/hands/ap-macbook-hands"
SRC_SKILL="$REPO_ROOT/hands/skill/ap-macbook-hands/skill-template.md"
SRC_TRANSACTION="$REPO_ROOT/hands/install-hands-transaction.py"
MODE="install"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check" ;;
    --dry-run) MODE="dry-run" ;;
    --undo) MODE="undo" ;;
    -h|--help) sed -n '1,4p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'install-hands.sh: unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

die() { printf 'install-hands.sh: %s\n' "$1" >&2; exit 2; }
valid_host() { [[ "$1" != -* && "$1" =~ ^([A-Za-z0-9._-]+@)?([A-Za-z0-9][A-Za-z0-9.-]*|\[[0-9A-Fa-f:]+\])$ ]]; }
[[ -f "$SRC_BIN" && -f "$SRC_SKILL" && -f "$SRC_TRANSACTION" ]] || die 'package hands payload is incomplete'
valid_host "$MINI" || die 'JARVIS_HANDS_MINI must be one host name, never an SSH option'
[[ "$PROFILE" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]] || die 'JARVIS_HANDS_PROFILE must be a safe selected profile id'
PROFILE_HOME="$(/usr/bin/python3 - "$PROFILE_HOME" "$PROFILE" <<'PY'
import os, sys
path, profile = sys.argv[1:]
if (not path or not os.path.isabs(path) or any(ord(ch) < 32 for ch in path)
        or ".." in path.split(os.sep) or os.path.basename(os.path.normpath(path)) != profile):
    raise SystemExit(2)
print(os.path.normpath(path))
PY
)" || die 'JARVIS_HANDS_PROFILE_HOME must be an absolute path ending in the selected profile id, without traversal or controls'
[[ "$DRIVER" == /* && "$DRIVER" != *$'\n'* ]] || die 'JARVIS_HANDS_DRIVER must be an absolute path'
IFS=',' read -r -a host_list <<< "$HOSTS"
[[ "$MODE" == undo || ( "${#host_list[@]}" -gt 0 && -n "$HOSTS" ) ]] || die 'JARVIS_HANDS_HOSTS needs the verified main computer host'
if [[ "$MODE" != undo ]]; then
  for host in "${host_list[@]}"; do
    [[ "$host" == "${host//[[:space:]]/}" ]] || die 'JARVIS_HANDS_HOSTS contains whitespace'
    valid_host "$host" || die 'JARVIS_HANDS_HOSTS contains an invalid or option-like host'
  done
fi

HANDS_DIR="$PROFILE_HOME/jarvis/hands"
BIN_PATH="$HANDS_DIR/bin/ap-macbook-hands"
TRANSACTION="$HANDS_DIR/bin/install-hands-transaction.py"
SKILL_DIR="$PROFILE_HOME/skills/agents/ap-macbook-hands"
LINK="$HANDS_DIR/ap-macbook-hands"
CONFIG="$HANDS_DIR/config.json"
STATE="$HANDS_DIR/state"
STAGE="$PROFILE_HOME/.jarvis-hands-stage.$$"
SSH_ARGS=(-T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8)
RSYNC_SHELL="$SSH -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8"
q() { printf '%q' "$1"; }
remote() { printf '%s:%s' "$MINI" "$(q "$1")"; }

tmp="$(mktemp -d "${TMPDIR:-/tmp}/jarvis-hands-install.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT
config_tmp="$tmp/config.json"; skill_tmp="$tmp/SKILL.md"
/usr/bin/python3 - "$config_tmp" "$skill_tmp" "$SRC_SKILL" "$PROFILE" "$PROFILE_HOME" "$HOSTS" "$DRIVER" "$STATE" "$BIN_PATH" <<'PY'
import json, os, sys
config, skill, source, profile, profile_home, hosts, driver, state, command = sys.argv[1:]
doc = {"schema": 1, "profile": profile, "profile_home": profile_home,
       "hosts": hosts.split(",") if hosts else [], "driver": driver, "state": state}
with open(config, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":")); fh.write("\n")
with open(source, "r", encoding="utf-8") as fh: text = fh.read()
token = "__JARVIS_HANDS_COMMAND__"
if token not in text: raise SystemExit("skill command token is missing")
with open(skill, "w", encoding="utf-8") as fh: fh.write(text.replace(token, command))
os.chmod(config, 0o600); os.chmod(skill, 0o644)
PY

# Read-only ancestry proof before any remote mkdir, copy or replacement.
PREFLIGHT_CODE='import os,stat,sys;p=os.path.normpath(sys.argv[1]);cur=os.sep
for part in [x for x in p.split(os.sep) if x]:
 cur=os.path.join(cur,part);m=os.lstat(cur).st_mode
 if stat.S_ISLNK(m) or not stat.S_ISDIR(m): raise SystemExit("unsafe profile ancestry")'
PREFLIGHT_CMD="/usr/bin/python3 -c $(q "$PREFLIGHT_CODE") $(q "$PROFILE_HOME")"
STAGE_CMD="mkdir -m 700 $(q "$STAGE") && mkdir -m 700 $(q "$STAGE/skill")"
SEAL_CMD="/usr/bin/python3 $(q "$STAGE/install-hands-transaction.py") seal $(q "$PROFILE_HOME") $(q "$PROFILE") $(q "$STAGE")"
UNDO_CMD="/usr/bin/python3 $(q "$TRANSACTION") undo $(q "$PROFILE_HOME") $(q "$PROFILE")"
STATUS_CMD="$(q "$BIN_PATH") status"
READ_CMD="printf '%s\\n%s\\n%s\\n%s\\n%s\\n%s\\n' \"\$(readlink $(q "$LINK") 2>/dev/null || true)\" $(q "$BIN_PATH") \"\$(stat -f %Lp $(q "$BIN_PATH") 2>/dev/null || true)\" \"\$(cksum < $(q "$BIN_PATH") 2>/dev/null || true)\" \"\$(stat -f %Lp $(q "$CONFIG") 2>/dev/null || true)\" \"\$(cksum < $(q "$CONFIG") 2>/dev/null || true)\""

echo "Main computer hands $MODE"
echo "  agent host   : $MINI"
echo "  profile home : $PROFILE_HOME"
[[ "$MODE" == undo ]] || echo "  main host    : $HOSTS"
echo "  command      : $BIN_PATH"
echo "  skill        : $SKILL_DIR/SKILL.md"
echo "  config       : $CONFIG"

if [[ "$MODE" == dry-run ]]; then
  echo 'DRY RUN - nothing ran.'
  printf '  %s %s %s %q\n' "$SSH" "${SSH_ARGS[*]}" "$MINI" "$PREFLIGHT_CMD"
  printf '  stage command, exact-path skill, durable config and transaction helper under %s\n' "$STAGE"
  printf '  seal transaction with rollback, then run: %s\n' "$STATUS_CMD"
  exit 0
fi

if [[ "$MODE" == undo ]]; then
  "$SSH" "${SSH_ARGS[@]}" "$MINI" "$PREFLIGHT_CMD"
  exec "$SSH" "${SSH_ARGS[@]}" "$MINI" "$UNDO_CMD"
fi

if [[ "$MODE" == check ]]; then
  bin_sum_here="$(cksum < "$SRC_BIN" | awk 'NF {print $1, $2}')"
  config_sum_here="$(cksum < "$config_tmp" | awk 'NF {print $1, $2}')"
  set +e
  read_out="$("$SSH" "${SSH_ARGS[@]}" "$MINI" "$PREFLIGHT_CMD" && "$SSH" "${SSH_ARGS[@]}" "$MINI" "$READ_CMD")"; read_rc=$?
  skill_diff="$("$RSYNC" -a -e "$RSYNC_SHELL" --dry-run --itemize-changes "$skill_tmp" "$(remote "$SKILL_DIR/SKILL.md")" 2>&1)"; skill_rc=$?
  set -e
  skill_real=""
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^[\<\>ch.][fdLDS]\.+\  ]] && continue
    skill_real="$skill_real$line"$'\n'
  done <<< "$skill_diff"
  link_now="$(printf '%s\n' "$read_out" | sed -n '1p')"; link_want="$(printf '%s\n' "$read_out" | sed -n '2p')"
  bin_mode="$(printf '%s\n' "$read_out" | sed -n '3p')"; bin_sum_there="$(printf '%s\n' "$read_out" | sed -n '4p' | awk 'NF {print $1, $2}')"
  config_mode="$(printf '%s\n' "$read_out" | sed -n '5p')"; config_sum_there="$(printf '%s\n' "$read_out" | sed -n '6p' | awk 'NF {print $1, $2}')"
  differs=0
  [[ "$read_rc" -eq 0 ]] || { echo 'differs: profile install could not be read safely'; differs=1; }
  [[ "$skill_rc" -eq 0 && -z "$skill_real" ]] || { echo "differs: the exact-path skill (rsync exit $skill_rc)"; differs=1; }
  [[ "$bin_sum_there" == "$bin_sum_here" ]] || { echo "differs: the command (there: ${bin_sum_there:-missing})"; differs=1; }
  [[ "$config_sum_there" == "$config_sum_here" ]] || { echo "differs: the durable config (there: ${config_sum_there:-missing})"; differs=1; }
  [[ "$link_now" == "$link_want" && -n "$link_want" ]] || { echo 'differs: the profile hands link'; differs=1; }
  [[ "$bin_mode" == 755 ]] || { echo "differs: command mode ${bin_mode:-missing}, expected 755"; differs=1; }
  [[ "$config_mode" == 600 ]] || { echo "differs: config mode ${config_mode:-missing}, expected 600"; differs=1; }
  [[ "$differs" -eq 0 ]] && { echo 'same: selected profile command, exact-path skill and config match'; exit 0; }
  exit 1
fi

step() { local what="$1"; shift; set +e; "$@"; local rc=$?; set -e; [[ "$rc" -eq 0 ]] || { printf 'install-hands.sh: the step "%s" failed (exit %s); no install was sealed.\n' "$what" "$rc" >&2; exit "$rc"; }; }
step 'validate every profile path component' "$SSH" "${SSH_ARGS[@]}" "$MINI" "$PREFLIGHT_CMD"
step 'create isolated remote stage' "$SSH" "${SSH_ARGS[@]}" "$MINI" "$STAGE_CMD"
step 'stage the command' "$RSYNC" -a -e "$RSYNC_SHELL" "$SRC_BIN" "$(remote "$STAGE/ap-macbook-hands")"
step 'stage the exact-path skill' "$RSYNC" -a -e "$RSYNC_SHELL" "$skill_tmp" "$(remote "$STAGE/skill/SKILL.md")"
step 'stage the durable config' "$RSYNC" -a -e "$RSYNC_SHELL" "$config_tmp" "$(remote "$STAGE/config.json")"
step 'stage the transaction helper' "$RSYNC" -a -e "$RSYNC_SHELL" "$SRC_TRANSACTION" "$(remote "$STAGE/install-hands-transaction.py")"
step 'seal the profile transaction' "$SSH" "${SSH_ARGS[@]}" "$MINI" "$SEAL_CMD"
echo "Installed with undo receipt. Run this installer with --undo to reverse it."
echo "ap-macbook-hands status (on $MINI):"
set +e
"$SSH" "${SSH_ARGS[@]}" "$MINI" "$STATUS_CMD" 2>&1 | sed 's/^/  /'; rc="${PIPESTATUS[0]}"
set -e
[[ "$rc" -eq 0 ]] || echo "  (status exit $rc - install is sealed; readiness still needs attention)"
exit 0
