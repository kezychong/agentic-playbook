#!/usr/bin/env bash
# tests/test_bin_scripts.sh — the two OPTIONAL Mac helper scripts, proved
# without touching a screen, a browser or the running Hermes.app.
#
#   bash tests/test_bin_scripts.sh
#
# Everything here runs through --dry-run, so no window opens, no key is pressed
# and no Chrome profile is created. The one real side effect a failure can have
# is a non-zero exit code.
#
# Two facts about this machine are NOT assumed, because both change with a
# cable: which displays are connected, and whether displayplacer is installed.
# The display test accepts either the "placed" answer or the "that screen is
# not connected" answer — but it insists the script gives one of them clearly
# and never invents a position it did not apply.

set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
BIN="$ROOT/payload/bin"
TOGGLE="$BIN/jarvis-toggle"
MIRROR="$BIN/jarvis-mirror"
export HERMES_HOME="${TMPDIR:-/tmp}/jarvis-bin-test-profile-$$"
export JARVIS_MIRROR_URL="https://member-agent.example/api/plugins/hermes-jarvis/mirror"
export JARVIS_MIRROR_TRANSPORT="direct"

pass=0
fail=0

ok()   { pass=$((pass + 1)); printf '  ok   %s\n' "$1"; }
bad()  { fail=$((fail + 1)); printf '  FAIL %s\n' "$1"; [ $# -gt 1 ] && printf '       %s\n' "$2"; }

# assert_has <label> <haystack> <needle>
assert_has() {
    case "$2" in
        *"$3"*) ok "$1" ;;
        *) bad "$1" "expected to find: $3" ;;
    esac
}

# assert_lacks <label> <haystack> <needle>
assert_lacks() {
    case "$2" in
        *"$3"*) bad "$1" "did NOT expect to find: $3" ;;
        *) ok "$1" ;;
    esac
}

assert_rc() {
    if [ "$2" -eq "$3" ]; then ok "$1"; else bad "$1" "exit code was $2, expected $3"; fi
}

printf '== the scripts exist, parse and are executable ==\n'

for f in "$TOGGLE" "$MIRROR"; do
    name="$(basename "$f")"
    if [ -f "$f" ]; then ok "$name exists"; else bad "$name exists"; continue; fi
    if [ -x "$f" ]; then ok "$name is executable"; else bad "$name is executable" "chmod +x it"; fi
    if err="$(bash -n "$f" 2>&1)"; then ok "$name parses (bash -n)"; else bad "$name parses (bash -n)" "$err"; fi
done

printf '== jarvis-toggle ==\n'

out="$("$TOGGLE" --dry-run 2>&1)"; rc=$?
assert_rc "toggle --dry-run exits 0" "$rc" 0
assert_has "toggle --dry-run says it changed nothing" "$out" 'DRY RUN'
assert_has "toggle --dry-run defaults to the toggle deep link" "$out" 'hermes://jarvis/toggle'
assert_has "toggle --dry-run names the open binary" "$out" '/usr/bin/open'
assert_has "toggle --dry-run reports the keystroke leg as off by default" "$out" 'keystroke fallback: off'
assert_lacks "toggle --dry-run does not arm osascript unasked" "$out" 'osascript'

for action in open close demo; do
    out="$("$TOGGLE" "--$action" --dry-run 2>&1)"; rc=$?
    assert_rc "toggle --$action exits 0" "$rc" 0
    assert_has "toggle --$action uses hermes://jarvis/$action" "$out" "hermes://jarvis/$action"
done

out="$("$TOGGLE" --keystroke --dry-run 2>&1)"; rc=$?
assert_rc "toggle --keystroke --dry-run exits 0" "$rc" 0
assert_has "toggle --keystroke describes the osascript fallback" "$out" 'osascript'
assert_has "toggle --keystroke wraps osascript in a hard timeout" "$out" 'alarm 8'
assert_has "toggle --keystroke names the chord it would press" "$out" 'command down, option down'

# The deep link must be the FIRST door offered, every time: it needs no
# permission, and on this machine an ungranted osascript keystroke HANGS.
link_line="$(printf '%s\n' "$out" | grep -n 'hermes://jarvis' | head -1 | cut -d: -f1)"
osa_line="$(printf '%s\n' "$out" | grep -n 'osascript' | head -1 | cut -d: -f1)"
if [ -n "$link_line" ] && [ -n "$osa_line" ] && [ "$link_line" -lt "$osa_line" ]; then
    ok "toggle offers the deep link before the keystroke fallback"
else
    bad "toggle offers the deep link before the keystroke fallback" "link line=$link_line osascript line=$osa_line"
fi

out="$(JARVIS_HERMES_APP=/nope/Hermes.app "$TOGGLE" --dry-run 2>&1)"; rc=$?
assert_rc "toggle refuses when Hermes is not installed" "$rc" 1
assert_has "toggle says so in plain words" "$out" 'Hermes is not installed'

out="$("$TOGGLE" --nonsense 2>&1)"; rc=$?
assert_rc "toggle rejects an unknown option" "$rc" 64
assert_has "toggle prints usage on a bad option" "$out" 'usage: jarvis-toggle'

printf '== jarvis-mirror ==\n'

# A profile path that does not exist: a dry run must not create it.
probe_profile="${TMPDIR:-/tmp}/jarvis-mirror-test-profile-$$"
rm -rf "$probe_profile"

out="$(JARVIS_CHROME_PROFILE="$probe_profile" "$MIRROR" --dry-run 2>&1)"; rc=$?
assert_rc "mirror --dry-run exits 0" "$rc" 0
assert_has "mirror --dry-run says it changed nothing" "$out" 'DRY RUN'
assert_has "mirror --dry-run opens Chrome as an app window" "$out" '--app='
assert_has "mirror --dry-run uses the configured remote member route" "$out" 'member-agent.example/api/plugins/hermes-jarvis/mirror'
assert_has "mirror --dry-run reports direct transport" "$out" 'transport: direct'
assert_has "mirror --dry-run uses its own Chrome profile" "$out" "--user-data-dir=$probe_profile"
assert_lacks "mirror --dry-run does not position a window it was not told to" "$out" '--window-position'
if [ -d "$probe_profile" ]; then
    bad "mirror --dry-run does not create the profile directory" "$probe_profile was created"
    rm -rf "$probe_profile"
else
    ok "mirror --dry-run does not create the profile directory"
fi

out="$("$MIRROR" --dry-run --kiosk 2>&1)"; rc=$?
assert_rc "mirror --kiosk exits 0" "$rc" 0
assert_has "mirror --kiosk passes --kiosk to Chrome" "$out" '--kiosk'

out="$("$MIRROR" --dry-run --url 'https://example.invalid/mirror' 2>&1)"; rc=$?
assert_rc "mirror --url exits 0" "$rc" 0
assert_has "mirror --url overrides the page" "$out" '--app=https://example.invalid/mirror'

# A screen name that is not connected on this machine. The honest answer is
# "that screen is not connected" — never a made-up origin.
out="$("$MIRROR" --dry-run --display 'Not A Real Screen' 2>&1)"; rc=$?
assert_rc "mirror refuses a screen that is not connected" "$rc" 1
assert_has "mirror names the screens that ARE connected" "$out" 'is connected right now'

out="$("$MIRROR" --dry-run --display 'Second Display' 2>&1)"; rc=$?
if [ "$rc" -eq 0 ]; then
    assert_has "mirror --display Second Display reports a placement" "$out" 'placement:'
    assert_has "mirror --display Second Display still opens the app window" "$out" '--app='
    case "$out" in
        *'placed exactly'*)
            assert_has "an exact placement passes a window position to Chrome" "$out" '--window-position='
            assert_has "an exact placement passes a window size to Chrome" "$out" '--window-size='
            ;;
        *'COULD NOT PLACE'*)
            assert_lacks "an unplaced window is never given a made-up position" "$out" '--window-position='
            ;;
        *)
            bad "mirror --display Second Display says whether it placed the window" "placement line was: $(printf '%s\n' "$out" | grep placement:)"
            ;;
    esac
else
    assert_rc "Second Display is simply not connected right now" "$rc" 1
    assert_has "mirror says which screens are connected" "$out" 'is connected right now'
fi

out="$("$MIRROR" --nonsense 2>&1)"; rc=$?
assert_rc "mirror rejects an unknown option" "$rc" 64
assert_has "mirror prints usage on a bad option" "$out" 'usage: jarvis-mirror'

printf '== both helpers say they are optional Mac extras ==\n'

toggle_body="$(cat "$TOGGLE")"
mirror_body="$(cat "$MIRROR")"
assert_has "jarvis-toggle labels itself optional" "$toggle_body" 'OPTIONAL Mac helper'
assert_has "jarvis-mirror labels itself optional" "$mirror_body" 'OPTIONAL Mac helper'
assert_lacks "jarvis-toggle carries no private display-project path" "$toggle_body" 'build-profiles.py'
assert_lacks "jarvis-mirror carries no private display-project path" "$mirror_body" 'build-profiles.py'

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
