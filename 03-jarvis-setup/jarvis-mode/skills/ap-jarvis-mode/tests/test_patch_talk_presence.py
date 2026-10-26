"""WP-C: scripts/patch-talk-presence.py against a throwaway copy of hermes-talk.

Every test runs on a fixture copy in pytest's tmp_path. The reference install
(``~/.hermes/plugins/hermes-talk``) is only ever READ.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "payload/host/talk-presence/patch-talk-presence.py"
REFERENCE = Path(
    os.environ.get("JARVIS_TALK_REFERENCE", Path.home() / ".hermes/plugins/hermes-talk")
).expanduser()
SURFACE = "ui/talk-surface.js"
SIDECAR = "ui/.hermes-jarvis-presence.orig.sha256"
BUILDER = "scripts/build_ui.py"
STYLE = "dashboard/dist/style.css"
GENERATED = ("desktop/plugin.js", "dashboard/dist/index.js")
NODE_TIMEOUT_S = 60

# A fake React/SDK runtime just big enough to render TalkPage once per call and
# run its effects, so the bus can be observed end to end: the presence event and
# a command actually reaching Talk's own start/stop/mute/sleep functions.
BUS_HARNESS = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
process.on('unhandledRejection', () => {});
const busEvents = [], listeners = {};
class CustomEvent { constructor(type, init) { this.type = type; this.detail = (init || {}).detail; } }
const slots = [];
let cursor = 0, effects = [];
const window = {
  __HERMES_TALK_TEST_HOOK__: true,
  __HERMES_PLUGINS__: { register() {} },
  location: { href: 'https://dashboard.example/plugins/hermes-talk' },
  crypto: { randomUUID: () => 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee' },
  sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  addEventListener(name, cb) { (listeners[name] = listeners[name] || []).push(cb); },
  removeEventListener(name, cb) {
    listeners[name] = (listeners[name] || []).filter((fn) => fn !== cb);
  },
  dispatchEvent(event) {
    if (event.type === 'hermes-talk:presence') busEvents.push(event.detail);
    (listeners[event.type] || []).slice().forEach((fn) => fn(event));
    return true;
  },
  __HERMES_PLUGIN_SDK__: {
    React: { createElement: (tag, props, ...children) => ({ tag, props: props || {}, children }) },
    components: { Button: 'button', Input: 'input' },
    hooks: {
      useState(initial) {
        const index = cursor++;
        if (!(index in slots)) slots[index] = initial;
        return [slots[index], (value) => {
          slots[index] = typeof value === 'function' ? value(slots[index]) : value;
        }];
      },
      useRef(initial) {
        const index = cursor++;
        if (!(index in slots)) slots[index] = { current: initial };
        return slots[index];
      },
      useCallback(callback, deps) {
        const index = cursor++, previous = slots[index];
        if (!previous || deps.some((d, at) => d !== previous.deps[at])) {
          slots[index] = { deps, callback };
        }
        return slots[index].callback;
      },
      useEffect(effect, deps) {
        const index = cursor++, previous = slots[index];
        if (!previous || deps.some((d, at) => d !== previous.deps[at])) {
          effects.push(() => {
            if (previous && previous.cleanup) previous.cleanup();
            slots[index] = { deps, cleanup: effect() };
          });
        }
      },
    },
    async fetchJSON(url) {
      if (url.endsWith('/status')) return { configured: true, voices: ['marin'], voice: 'marin' };
      if (url.endsWith('/targets')) return { ok: true, targets: [], peers: [], unavailable: [] };
      return {};
    },
  },
};
vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), {
  window, CustomEvent, setTimeout, clearTimeout, setInterval, clearInterval,
  AbortController, console, btoa, document: { title: 'bus harness' },
  navigator: { mediaDevices: {} }, RTCPeerConnection: function () {},
}, { filename: 'index.js' });

const Page = window.__HERMES_TALK_TEST__.TalkPage;
const render = () => {
  cursor = 0; effects = []; const tree = Page(); effects.forEach((f) => f()); return tree;
};
const send = (action) =>
  window.dispatchEvent(new CustomEvent('hermes-talk:command', { detail: { action } }));
const last = () => busEvents[busEvents.length - 1];

render();
assert.ok(busEvents.length >= 1, 'no presence event on first render');
const first = last();
assert.deepStrictEqual(Object.keys(first).sort(),
  ['at', 'audioActivity', 'live', 'muted', 'phase', 'sleeping', 'transcript'].sort());
assert.equal(first.phase, 'idle');
assert.equal(first.live, '');
assert.equal(JSON.stringify(first.audioActivity), '{"input":false,"output":false}');
assert.equal(first.transcript.length, 0);
assert.equal(first.muted, false);
assert.equal(first.sleeping, false);
assert.equal(typeof first.at, 'number');
assert.ok(listeners['hermes-talk:command'] && listeners['hermes-talk:command'].length === 1,
  'command listener not registered exactly once');

send('mute'); render();
assert.equal(last().muted, true, 'mute command did not reach setMuted');
send('unmute'); render();
assert.equal(last().muted, false, 'unmute command did not reach setMuted');
send('sleep'); render();
assert.equal(last().sleeping, true, 'sleep command did not reach setSleeping');
send('wake'); render();
assert.equal(last().sleeping, false, 'wake command did not reach setSleeping');

const before = busEvents.length;
send('frobnicate'); send(undefined);
window.dispatchEvent(new CustomEvent('hermes-talk:command', {}));
render();
assert.equal(busEvents.length, before,
  'an unknown action changed state, or the bus fired with no state change');

send('start'); render();
assert.equal(last().phase, 'starting', 'start command did not reach startTalk');
send('stop'); render();
assert.equal(last().phase, 'idle', 'stop command did not reach stopTalk');

render(); render();
assert.equal(listeners['hermes-talk:command'].length, 1, 'listener leaked across renders');
console.log('presence-bus behaviour OK (' + busEvents.length + ' presence events)');
process.exit(0);
"""


def node_binary() -> str:
    found = shutil.which("node") or str(Path.home() / ".local/bin/node")
    if not Path(found).exists():
        pytest.skip("node is not on PATH; the generated bundles cannot be parsed or driven")
    return found


@pytest.fixture
def talk(tmp_path: Path) -> Path:
    """A throwaway hermes-talk root: ui/ + scripts/ + the stylesheet the build needs.

    The reference install may itself be patched — on this MacBook the presence bus
    is applied for real — so the copy is healed back to stock before any test sees
    it. The sidecar is copied along with the sources, so that revert is verified.
    """
    if not (REFERENCE / SURFACE).is_file():
        pytest.skip(
            f"no hermes-talk reference copy at {REFERENCE} "
            "(set JARVIS_TALK_REFERENCE to a hermes-talk root to run these tests)"
        )
    root = tmp_path / "hermes-talk"
    (root / "ui").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / "dashboard/dist").mkdir(parents=True)
    for source in (REFERENCE / "ui").glob("*.js"):
        shutil.copy2(source, root / "ui" / source.name)
    for extra in (SIDECAR, BUILDER, STYLE):
        if (REFERENCE / extra).is_file():
            shutil.copy2(REFERENCE / extra, root / extra)
    unpatch(root)
    return root


def unpatch(root: Path) -> None:
    """Heal the copy to stock, whatever state the reference install is in."""
    if patch(root, "--check").returncode == 0:
        verifiable = (root / SIDECAR).is_file()
        reverted = patch(root, "--revert", "--no-build")
        assert reverted.returncode == 0, (
            "could not unpatch the fixture copy:\n" + reverted.stdout + reverted.stderr
        )
        if verifiable:
            assert "bytes match the recorded original" in reverted.stdout, reverted.stdout
    # Every test starts from stock: no block, and no sidecar left lying about.
    (root / SIDECAR).unlink(missing_ok=True)
    state = patch(root, "--check")
    assert state.returncode == 1, (
        "the fixture copy is not unpatched stock:\n" + state.stdout + state.stderr
    )


def patch(talk: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--talk", str(talk), *args],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_S,
    )


def build_ui(talk: Path) -> subprocess.CompletedProcess[str]:
    """Run the copy's own scripts/build_ui.py, exactly as the patch script does."""
    return subprocess.run(
        [sys.executable, str(talk / BUILDER)],
        cwd=str(talk),
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_S,
    )


def test_apply_check_reapply_build_and_revert(talk: Path) -> None:
    original = (talk / SURFACE).read_bytes()

    assert patch(talk, "--check").returncode == 1

    applied = patch(talk, "--apply")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert "presence bus inserted" in applied.stdout
    assert "Rebuilt: desktop/plugin.js, dashboard/dist/index.js" in applied.stdout
    assert (talk / SIDECAR).is_file()

    assert patch(talk, "--check").returncode == 0

    patched = (talk / SURFACE).read_bytes()
    again = patch(talk, "--apply")
    assert again.returncode == 0, again.stdout + again.stderr
    assert "already patched" in again.stdout
    assert (talk / SURFACE).read_bytes() == patched, "a second --apply changed the source"

    # The inserted block is small, marker-delimited and carries no console noise.
    text = (talk / SURFACE).read_text(encoding="utf-8")
    block = text.split("// hermes-jarvis presence-bus BEGIN")[1]
    block = block.split("// hermes-jarvis presence-bus END")[0]
    assert len(block.splitlines()) <= 30
    assert "console." not in block

    bundle = talk / "desktop/plugin.js"
    generated = bundle.read_text(encoding="utf-8")
    assert "hermes-talk:presence" in generated
    assert "hermes-talk:command" in generated
    assert "hermes-talk:presence" in (talk / "dashboard/dist/index.js").read_text(encoding="utf-8")

    esm = talk / "plugin-check.mjs"
    esm.write_bytes(bundle.read_bytes())
    parsed = subprocess.run(
        [node_binary(), "--check", str(esm)], capture_output=True, text=True, timeout=NODE_TIMEOUT_S
    )
    assert parsed.returncode == 0, parsed.stdout + parsed.stderr

    reverted = patch(talk, "--revert")
    assert reverted.returncode == 0, reverted.stdout + reverted.stderr
    assert "bytes match the recorded original" in reverted.stdout
    assert (talk / SURFACE).read_bytes() == original
    assert not (talk / SIDECAR).exists()
    assert patch(talk, "--check").returncode == 1


def test_generated_bundles_return_to_stock_on_revert(talk: Path) -> None:
    if not (talk / BUILDER).is_file():
        pytest.skip(f"the copy has no {BUILDER}; there are no bundles to compare")
    if (talk / "ui/desktop-entry.js").is_file() and not (talk / STYLE).is_file():
        pytest.skip(f"the copy has no {STYLE}; the desktop bundle cannot be built")

    # Stock = what the copy's own builder makes from the unpatched sources. The
    # reference install's bundles are not the yardstick: it may itself be patched.
    built = build_ui(talk)
    assert built.returncode == 0, built.stdout + built.stderr
    stock_before = {name: (talk / name).read_bytes() for name in GENERATED if (talk / name).is_file()}
    missing = [name for name in GENERATED if name not in stock_before]
    if missing:
        pytest.skip("the copy builds no " + ", ".join(missing) + "; nothing to compare")

    assert patch(talk, "--apply").returncode == 0
    patched_bundle = (talk / "desktop/plugin.js").read_bytes()
    assert patched_bundle != stock_before["desktop/plugin.js"], "--apply left the bundle alone"

    assert patch(talk, "--revert").returncode == 0
    for name, stock in stock_before.items():
        assert (talk / name).read_bytes() == stock, f"{name} did not return to stock on revert"


def test_unknown_talk_version_exits_two(talk: Path) -> None:
    surface = talk / SURFACE
    surface.write_text(
        surface.read_text(encoding="utf-8").replace(
            "const [audioActivity, setAudioActivity] = useState({ input: false, output: false });",
            "const [audioActivity, setAudioActivity] = useState({ input: 0, output: 0 });",
        ),
        encoding="utf-8",
        newline="",
    )
    for mode in ("--check", "--apply"):
        result = patch(talk, mode)
        assert result.returncode == 2, mode
        assert "Unknown hermes-talk version" in result.stderr
    assert not (talk / SIDECAR).exists()


def test_missing_root_exits_two(tmp_path: Path) -> None:
    empty = tmp_path / "not-talk"
    empty.mkdir()
    result = patch(empty, "--check")
    assert result.returncode == 2
    assert "Not a hermes-talk root" in result.stderr


def test_dry_run_writes_nothing_and_prints_the_diff(talk: Path) -> None:
    before = {p: p.read_bytes() for p in talk.rglob("*") if p.is_file()}
    result = patch(talk, "--apply", "--dry-run")
    assert result.returncode == 0
    assert "hermes-talk:presence" in result.stdout
    assert result.stdout.startswith("--- a/ui/talk-surface.js")
    assert "+++ b/ui/talk-surface.js" in result.stdout
    after = {p: p.read_bytes() for p in talk.rglob("*") if p.is_file()}
    assert after == before, "--dry-run wrote to disk"


def test_missing_stylesheet_refuses_before_writing(talk: Path) -> None:
    (talk / STYLE).unlink(missing_ok=True)
    result = patch(talk, "--apply")
    assert result.returncode == 3
    assert "style.css is missing" in result.stderr
    assert patch(talk, "--check").returncode == 1, "the source was written despite the refusal"
    assert patch(talk, "--apply", "--no-build").returncode == 0
    assert patch(talk, "--check").returncode == 0


def test_revert_on_an_unpatched_root_is_a_no_op(talk: Path) -> None:
    original = (talk / SURFACE).read_bytes()
    result = patch(talk, "--revert", "--no-build")
    assert result.returncode == 0
    assert "nothing to revert" in result.stdout
    assert (talk / SURFACE).read_bytes() == original


def test_revert_without_the_sidecar_restores_but_says_it_is_unverified(talk: Path) -> None:
    original = (talk / SURFACE).read_bytes()
    assert patch(talk, "--apply", "--no-build").returncode == 0
    (talk / SIDECAR).unlink()
    result = patch(talk, "--revert", "--no-build")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "not hash-verified" in result.stdout
    assert (talk / SURFACE).read_bytes() == original
    assert patch(talk, "--check").returncode == 1


def test_revert_refuses_when_the_file_drifted_while_patched(talk: Path) -> None:
    assert patch(talk, "--apply", "--no-build").returncode == 0
    surface = talk / SURFACE
    surface.write_text(
        surface.read_text(encoding="utf-8").replace(
            'const IDLE_POLL_MS = 20000;', 'const IDLE_POLL_MS = 20001;'
        ),
        encoding="utf-8",
        newline="",
    )
    drifted = surface.read_bytes()
    result = patch(talk, "--revert", "--no-build")
    assert result.returncode == 4
    assert "does not reproduce the original" in result.stderr
    assert surface.read_bytes() == drifted, "a refused revert still wrote"


def test_presence_and_commands_work_in_a_rendered_page(talk: Path, tmp_path: Path) -> None:
    node = node_binary()
    assert patch(talk, "--apply").returncode == 0
    harness = tmp_path / "bus-harness.js"
    harness.write_text(BUS_HARNESS, encoding="utf-8")
    result = subprocess.run(
        [node, str(harness), str(talk / "dashboard/dist/index.js")],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_S,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "presence-bus behaviour OK" in result.stdout

    # Negative control: the same harness must fail against the unpatched bundle.
    assert patch(talk, "--revert").returncode == 0
    stock = subprocess.run(
        [node, str(harness), str(talk / "dashboard/dist/index.js")],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_S,
    )
    assert stock.returncode != 0
    assert "no presence event on first render" in stock.stderr
