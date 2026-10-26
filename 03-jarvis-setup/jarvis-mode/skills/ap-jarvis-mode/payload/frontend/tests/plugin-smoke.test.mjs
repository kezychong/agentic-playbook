// tests/plugin-smoke.test.mjs — node --test tests/plugin-smoke.test.mjs
//
// Loads the BUILT desktop/plugin.js (the exact bytes Hermes.app loads), strips
// the two bare imports Node cannot resolve, injects a fake SDK + React, and
// registers it against a fake PluginContext. Proves: the default export's
// shape, every contribution, the deep-link subscription, and the heartbeat
// receipt under the active Desktop Hermes root.
//
// The same stub window/document also drive the overlay's voice cluster
// (SPEC §4.6) straight from src/, where the button labels and the T/M/Z keys
// can be read without a browser.
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const BUILT = fileURLToPath(new URL('../desktop/plugin.js', import.meta.url))
const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const THEME_SRC = fileURLToPath(new URL('../src/10-theme.js', import.meta.url))
const OVERLAY_SRC = fileURLToPath(new URL('../src/50-overlay.js', import.meta.url))

function fakeReact() {
  return {
    createElement: (type, props, ...kids) => ({
      type: typeof type === 'function' ? type.name || 'component' : type,
      props: props || {},
      kids
    }),
    useState: initial => [initial, () => {}],
    useEffect: () => {}
  }
}

function atomOf(value) {
  return { get: () => value, listen: () => () => {} }
}

function scopeId() {
  const text = JSON.stringify(['local', 'agent', 'agent'])
  let hash = 2166136261
  for (let i = 0; i < text.length; i += 1) { hash ^= text.charCodeAt(i); hash = Math.imul(hash, 16777619) }
  return (hash >>> 0).toString(36)
}
const PLUGIN_SCOPE_ID = scopeId()
const pluginStorageKey = name => `hermes-jarvis:${PLUGIN_SCOPE_ID}:${name}`
const pluginReceipt = stem => `/tmp/hermes-test/jarvis/${stem}-${PLUGIN_SCOPE_ID}.json`

/** The host exposes its composer voice controller through a hook (§4.10
 *  ruling 1). `useController` is what that hook returns; `null` here means a
 *  host that HAS the hook but no composer mounted, and `undefined` (pass
 *  `{ hook: false }`) means an older shell with no hook at all. */
function fakeSDK(options = {}) {
  const sdk = {
    PALETTE_AREA: 'palette',
    KEYBINDS_AREA: 'keybinds',
    STATUSBAR_AREAS: { left: 'statusBar.left', right: 'statusBar.right' },
    Codicon: function Codicon() {},
    Button: function Button() {},
    host: {
      state: {
        profile: atomOf('agent'),
        gateway: atomOf('open'),
        model: atomOf('grok-4.6'),
        connectionId: atomOf('local'),
        focusedSessionProfile: atomOf('agent')
      },
      request: async () => ({}),
      profileRoutes: async () => [{ connectionId: 'local', profile: 'agent', targetProfile: 'agent' }],
      notify: () => {}
    }
  }
  if (options.hook !== false) {
    sdk.useComposerVoiceController = () => (options.controller === undefined ? null : options.controller)
  }
  return sdk
}

// A canvas 2D context that swallows everything — enough for the real scene to
// paint into without a browser.
const ctx2d = new Proxy({}, {
  get: (t, k) => {
    if (k === 'canvas') return { width: 100, height: 100 }
    if (k === 'createLinearGradient' || k === 'createRadialGradient') return () => ({ addColorStop() {} })
    if (k === 'measureText') return () => ({ width: 40 })
    return typeof k === 'string' ? () => undefined : t[k]
  },
  set: () => true
})

function domNode(tag) {
  const n = {
    tagName: String(tag).toUpperCase(), className: '', _text: '', children: [], childNodes: [],
    style: { setProperty() {}, removeProperty() {} }, attributes: {}, parentNode: null,
    get textContent() { return this._text },
    set textContent(v) { this._text = String(v); this.children.length = 0; this.childNodes.length = 0 },
    classList: { _s: new Set(), add(...c) { c.forEach(x => this._s.add(x)) }, remove(...c) { c.forEach(x => this._s.delete(x)) }, toggle(c, on) { on ? this._s.add(c) : this._s.delete(c) }, contains(c) { return this._s.has(c) } },
    appendChild(c) { c.parentNode = this; this.children.push(c); this.childNodes.push(c); return c },
    removeChild(c) { this.children = this.children.filter(x => x !== c); this.childNodes = this.childNodes.filter(x => x !== c); c.parentNode = null },
    setAttribute(k, v) { this.attributes[k] = v }, getAttribute(k) { return this.attributes[k] ?? null },
    querySelector: () => null, querySelectorAll: () => [],
    _on: {},
    addEventListener(type, fn) { (this._on[type] || (this._on[type] = [])).push(fn) },
    removeEventListener(type, fn) { this._on[type] = (this._on[type] || []).filter(x => x !== fn) },
    dispatch(type, event) {
      const ev = event || { type, preventDefault() {}, stopPropagation() {} }
      ;(this._on[type] || []).slice().forEach(fn => fn(ev))
    },
    click() { this.dispatch('click') },
    focus() {}, blur() {},
    getContext: () => ctx2d, clientWidth: 1440, clientHeight: 900, width: 0, height: 0
  }
  n.classList = { ...n.classList, _s: new Set() }
  n._on = {}
  return n
}

/** Depth-first hunt for a node carrying `attr="value"` (the overlay tags its
 *  voice buttons with data-jv). */
function findByAttr(node, attr, value) {
  if (!node) return null
  if (node.attributes && node.attributes[attr] === value) return node
  const kids = node.childNodes || []
  for (const kid of kids) {
    const hit = findByAttr(kid, attr, value)
    if (hit) return hit
  }
  return null
}

function findByClass(node, cls) {
  if (!node) return null
  if (typeof node.className === 'string' && node.className.split(' ').includes(cls)) return node
  const kids = node.childNodes || []
  for (const kid of kids) {
    const hit = findByClass(kid, cls)
    if (hit) return hit
  }
  return null
}

/** The button's own label node — `kbd` holds the key hint, so textContent alone
 *  would read "START TALKT". */
function labelOf(button) {
  const label = findByClass(button, 'jv-vbtn-l')
  return label ? label.textContent : null
}

function install(live, search = '') {
  const writes = []
  let deepLinkHandler = null
  // The host composer with its real Talk trigger inside it: exactly one
  // talk-named clickable, so probeTalkDom() (20-presence.js) has one candidate
  // to find and the heartbeat has something to carry.
  const composer = domNode('div')
  composer.className = 'ht-composer-row'
  const talkBtn = domNode('button')
  talkBtn.setAttribute('aria-label', 'Open Hermes Talk')
  talkBtn.setAttribute('data-testid', 'composer-talk')
  talkBtn.textContent = 'Talk'
  composer.appendChild(talkBtn)
  // SPEC §4.9 ruling 2: the constructor the main instance wraps — and the HUD
  // instance must not. Kept by identity so a test can say which one is in place.
  class FakeHTMLAudioElement { constructor() { this.srcObject = null } }
  class FakeAudio extends FakeHTMLAudioElement {}
  const win = {
    // Which window the plugin thinks it is in (SPEC §4.7): the HUD instance is
    // the relay and registers nothing at all.
    location: { search: search, href: 'app://hermes/index.html' + search },
    Audio: FakeAudio,
    HTMLAudioElement: FakeHTMLAudioElement,
    WeakRef: typeof WeakRef === 'function' ? WeakRef : undefined,
    localStorage: (() => {
      const cells = new Map()
      return {
        getItem: k => (cells.has(k) ? cells.get(k) : null),
        setItem: (k, v) => { cells.set(k, String(v)) },
        removeItem: k => { cells.delete(k) }
      }
    })(),
    hermesDesktop: {
      onDeepLink: cb => { deepLinkHandler = cb; return () => { deepLinkHandler = null } },
      logsRoot: async () => '/tmp/hermes-test/logs',
      writeTextFile: async (path, content) => { writes.push({ path, content }); return { path } }
    },
    requestAnimationFrame: () => 1,
    cancelAnimationFrame: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    matchMedia: () => ({ matches: false }),
    setTimeout, clearTimeout, setInterval, clearInterval
  }
  const docFake = {
    body: live ? domNode('body') : null,
    head: live ? domNode('head') : null,
    documentElement: live ? domNode('html') : null,
    activeElement: null,
    createElement: domNode, createTextNode: t => ({ nodeValue: String(t) }),
    querySelector: sel => (sel === 'button[aria-label="Open Hermes Talk"]' ? talkBtn : null),
    querySelectorAll: sel => (sel !== 'audio' && /button/.test(sel) ? [talkBtn] : []),
    getElementById: () => null,
    _on: {},
    addEventListener(type, fn) { (this._on[type] || (this._on[type] = [])).push(fn) },
    removeEventListener(type, fn) { this._on[type] = (this._on[type] || []).filter(x => x !== fn) },
    fire(type, event) { (this._on[type] || []).slice().forEach(fn => fn(event)) }
  }
  globalThis.window = win
  globalThis.document = docFake
  Object.defineProperty(globalThis, 'navigator', { value: {}, configurable: true })
  return { writes, deepLink: () => deepLinkHandler, win, doc: docFake, talkBtn, OriginalAudio: FakeAudio }
}

// 10-theme.js + 50-overlay.js as text: the overlay is vanilla DOM, so the stub
// document above is all it needs.
function loadOverlay(env) {
  const source = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n' + fs.readFileSync(THEME_SRC, 'utf8') + '\n' + fs.readFileSync(OVERLAY_SRC, 'utf8')
  return new Function('window', 'document', `${source}\nreturn createOverlay;`)(env.win, env.doc)
}

function presenceStub(initial, budget = null, canCommand = null) {
  const subscribers = new Set()
  const asked = []
  let snap = initial
  const store = {
    get: () => snap,
    subscribe(fn) { subscribers.add(fn); return () => subscribers.delete(fn) },
    isDemo: () => false,
    command(action) {
      asked.push(action)
      return Promise.resolve({ ok: true, via: 'bus', reason: '' })
    }
  }
  // A real store publishes the longest it will make command() wait; the overlay
  // adds its half second to that (§4.7 amendment). `budget: null` is the older
  // store that does not, so the overlay falls back to its own constant.
  if (budget !== null) store.waitBudgetMs = action => (String(action) === 'start' ? budget : 0)
  // §4.8 ruling 6: the real store tells the overlay whether a press can be
  // DELIVERED, whatever the snapshot's `call` happens to read at that instant.
  if (canCommand !== null) store.canCommand = () => canCommand
  return {
    asked,
    push(patch) {
      snap = { ...snap, ...patch }
      subscribers.forEach(fn => fn(snap))
    },
    store
  }
}

const QUIET_DATA = {
  connection: { profile: 'agent', gateway: 'open', model: 'grok-4.6', backend: 'ok' },
  brains: [], senses: [], fleet: [], jobs: [], lever: null, events: [], panel: null,
  health: {}, updatedAt: 0
}

const dataStub = { get: () => QUIET_DATA, subscribe: () => () => {} }
const sleep = ms => new Promise(r => setTimeout(r, ms))
const OFF = {
  call: 'off', mode: 'idle', live: '', levels: { voice: 0, mic: 0 }, captions: [],
  source: { status: 'none', voice: 'none', mic: 'none' }, demo: false, updatedAt: 0
}

function loadPlugin(sdk, react) {
  const raw = fs.readFileSync(BUILT, 'utf8')
    .replace(/^import .*$/gm, '')
    .replace(/^export default /m, 'const JARVIS_PLUGIN = ')
  return new Function('HermesSDK', 'React', `${raw}\nreturn JARVIS_PLUGIN;`)(sdk || fakeSDK(), react || fakeReact())
}

function fakeCtx() {
  const registered = []
  const disposers = []
  const events = []
  return {
    registered, disposers, events,
    ctx: {
      register: c => { registered.push(c); return () => {} },
      registerMany: cs => { cs.forEach(c => registered.push(c)); return () => {} },
      onDispose: fn => { disposers.push(fn) },
      onEvent: (type, fn) => { events.push(type); return () => {} },
      rest: async () => { throw new Error('backend offline') },
      socket: () => () => {},
      storage: { get: (k, fallback) => fallback, set() {}, remove() {} },
      os: {}
    }
  }
}

// §4.10 ruling 1 adds an EIGHTH registration — the invisible composer
// contribution — and no eighth door: it draws nothing and nobody can press it.
// Eight registrations, seven ways in.
test('the built plugin registers every door and writes a heartbeat', async () => {
  const env = install()
  const plugin = loadPlugin()

  assert.equal(plugin.id, 'hermes-jarvis')
  // SPEC §7.6: the display name is "Jarvis mode"; the id never moved.
  assert.equal(plugin.name, 'Jarvis mode')
  assert.equal(plugin.defaultEnabled, true)
  assert.equal(typeof plugin.register, 'function')

  const harness = fakeCtx()
  plugin.register(harness.ctx)

  const ids = harness.registered.map(c => c.id)
  assert.deepEqual(ids.sort(), [
    'jarvis-composer-voice', 'jarvis-keybind', 'jarvis-palette-demo', 'jarvis-palette-toggle',
    'jarvis-palette-window', 'jarvis-room-nav', 'jarvis-room-page', 'jarvis-statusbar', 'jarvis-topbar'
  ], 'title bar, statusbar, three palette rows (§7.2 adds the window one), the keybind, WP-D room page + sidebar row, and the invisible composer bridge')

  const areas = {}
  harness.registered.forEach(c => { areas[c.id] = c.area })
  assert.equal(areas['jarvis-topbar'], 'titleBar.tools.right')
  assert.equal(areas['jarvis-statusbar'], 'statusBar.right')
  assert.equal(areas['jarvis-keybind'], 'keybinds')

  const keybind = harness.registered.find(c => c.id === 'jarvis-keybind')
  assert.deepEqual(keybind.data.defaults, ['mod+alt+j'])
  assert.equal(keybind.data.id, 'jarvis.toggle')

  const topbar = harness.registered.find(c => c.id === 'jarvis-topbar')
  assert.equal(topbar.data.label, 'Jarvis mode', 'titleBar.tools.* reads `data`, not `render`')
  assert.equal(topbar.data.icon.props.name, 'radio-tower')

  assert.deepEqual(harness.events, ['*'], 'the gateway event tap is registered')
  assert.ok(harness.disposers.length >= 1, 'teardown goes through ctx.onDispose')
  assert.equal(typeof env.deepLink(), 'function', 'the deep-link bridge is subscribed')

  // The heartbeat is written with `await` inside the bridge stub, so give the
  // microtask queue a turn before reading it.
  await new Promise(r => setImmediate(r))

  assert.ok(env.writes.length >= 1, 'a heartbeat was written on register')
  const beat = env.writes[env.writes.length - 1]
  assert.equal(beat.path, pluginReceipt('desktop-heartbeat'))

  const body = JSON.parse(beat.content)
  assert.ok(Array.isArray(body.contributions) && body.contributions.length === 9,
    'every registration listed: the room, the invisible composer bridge and the §7.2 palette row included')
  // §7.2 ruling 5: which window wrote this, and whether it was sent here.
  assert.equal(body.window, 'primary', 'no ?peer=1 and no ?win= flag: this is the primary window')
  assert.equal(body.bootOpen, false, 'nobody asked this window to open itself')
  assert.equal(body.deepLink, true)
  assert.equal(body.overlay, 'closed')
  assert.equal(body.lastError, null)
  assert.equal(body.demo, false)
  assert.equal(typeof body.pluginVersion, 'string')
  assert.ok(Date.parse(body.loadedAt) > 0, 'loadedAt is an ISO stamp')
  assert.ok(Date.parse(body.at) > 0, 'at is an ISO stamp')
  assert.ok(body.source && typeof body.source.status === 'string', 'presence source rides along')

  // The Talk DOM probe: the heartbeat is the only window into why START TALK
  // found nothing, so it must carry the live reading, not a guess.
  const probe = body.talkProbe
  assert.ok(probe && typeof probe === 'object', 'the heartbeat carries talkProbe')
  assert.equal(probe.trigger, 'button[aria-label="Open Hermes Talk"]', 'the selector command() clicks')
  assert.equal(probe.hud, false, 'no Talk HUD in this stub window')
  assert.equal(probe.view, false, 'and no desktop view')
  assert.equal(probe.audio, 0, 'no <audio> elements either')
  assert.equal(probe.buttons, 1, 'one button in the whole stub document')
  assert.equal(probe.candidates.length, 1, 'exactly one talk-named clickable')
  assert.deepEqual(probe.candidates[0], {
    tag: 'button',
    text: 'Talk',
    ariaLabel: 'Open Hermes Talk',
    title: '',
    dataTestId: 'composer-talk',
    inComposer: true
  }, 'and it is described in plain fields, composer flag included')

  // SPEC §4.9 ruling 5: the probe also says which voice system was on screen
  // and whether the window.Audio tap is in place. Nothing native in this stub
  // window, so every flag is false — and says so rather than going missing.
  assert.deepEqual(probe.native, { start: false, end: false, mute: false, pill: '' },
    'the built-in voice rides along, blank when it is not there')
  assert.equal(probe.audioTap.wrapped, true, 'the main window wrapped window.Audio')
  assert.equal(probe.audioTap.seen, 0, 'nothing has constructed an element yet')
  assert.equal(probe.audioTap.metering, false, 'and nothing is being metered')

  // The wrapper is real, and it comes off again on dispose (§4.9 ruling 2).
  assert.notEqual(env.win.Audio, env.OriginalAudio, 'window.Audio is wrapped while we are loaded')
  harness.disposers.forEach(fn => fn()) // no stray timers left behind
  assert.equal(env.win.Audio, env.OriginalAudio, 'and the original is back after dispose')
})

test('the heartbeat follows the overlay open and closed', async () => {
  const env = install(true)
  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const beat = () => JSON.parse(env.writes[env.writes.length - 1].content)
  assert.equal(beat().overlay, 'closed', 'nothing open at load')

  const toggleRow = harness.registered.find(c => c.id === 'jarvis-palette-toggle')
  toggleRow.data.run()
  assert.equal(toggleRow.data.detail(), 'open', 'the palette row reports the live state')
  await new Promise(r => setTimeout(r, 700)) // past the write throttle
  assert.equal(beat().overlay, 'open', 'the heartbeat records the open overlay')

  toggleRow.data.run()
  await new Promise(r => setTimeout(r, 700))
  assert.equal(beat().overlay, 'closed', 'and records it closing again')

  harness.disposers.forEach(fn => fn())
})

// ---- SPEC §4.7: the HUD instance is the relay and nothing else -------------

test('in the floating HUD window the plugin registers nothing and relays instead', async () => {
  const env = install(false, '?win=hud')
  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  assert.equal(harness.registered.length, 0,
    'no title-bar tool, no statusbar chip, no palette rows, no keybind, no room')
  assert.deepEqual(harness.events, [], 'and no gateway polling from the HUD window')
  assert.equal(env.deepLink(), null, 'the deep link belongs to the main window')
  assert.ok(harness.disposers.length >= 1, 'the relay is torn down through ctx.onDispose')

  const paths = env.writes.map(w => w.path)
  assert.ok(!paths.includes(pluginReceipt('desktop-heartbeat')),
    'the HUD never writes the main window’s receipt')
  assert.ok(paths.includes(pluginReceipt('hud-heartbeat')),
    'it writes its own scoped HUD receipt')

  const body = JSON.parse(env.writes.find(w => w.path === pluginReceipt('hud-heartbeat')).content)
  assert.equal(typeof body.pluginVersion, 'string')
  assert.ok(Date.parse(body.loadedAt) > 0, 'loadedAt is an ISO stamp')
  assert.equal(typeof body.relaySeq, 'number')
  assert.ok(body.talkProbe && typeof body.talkProbe === 'object', 'with a probe of the HUD DOM')
  assert.equal(body.lastError, null)

  // SPEC §4.9 ruling 2: the audio tap is the MAIN window's, once. The HUD
  // instance is the relay and nothing else — a second wrapper in a second
  // window would double-count Agent's elements for no reading anyone reads.
  assert.equal(env.win.Audio, env.OriginalAudio, 'the HUD instance never wraps window.Audio')

  harness.disposers.forEach(fn => fn())        // no stray relay timers left behind
})

// ---- SPEC §4.6: the voice cluster ----------------------------------------

test('the voice buttons follow the presence snapshot, never the last click', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF)
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const talk = findByAttr(root, 'data-jv', 'talk')
  const mute = findByAttr(root, 'data-jv', 'mute')
  const sleepBtn = findByAttr(root, 'data-jv', 'sleep')
  assert.ok(talk && mute && sleepBtn, 'three buttons live in the overlay')

  assert.equal(labelOf(talk), 'START TALK', 'call off → START TALK')
  assert.equal(labelOf(mute), 'MUTE')
  assert.equal(labelOf(sleepBtn), 'SLEEP')
  assert.equal(mute.disabled, true, 'nothing to mute without a live call')
  assert.equal(mute.attributes.title, 'no live call · start Talk first', 'and it says why')
  assert.equal(talk.disabled, false, 'START TALK stays live — that is the whole point')

  // The overlay paints text at 10 Hz, so each state needs its own beat before
  // the store pushes it (the real store emits ~30 times a second).
  const beat = async patch => { await sleep(120); presence.push(patch) }

  await beat({ call: 'on', mode: 'speaking' })
  assert.equal(labelOf(talk), 'END TALK', 'a live call → END TALK')
  assert.equal(talk.classList.contains('jv-live'), true, 'coral for the live call')
  assert.equal(mute.disabled, false)

  await beat({ mode: 'muted' })
  assert.equal(labelOf(mute), 'UNMUTE', 'the bus says muted → UNMUTE')
  assert.equal(labelOf(sleepBtn), 'SLEEP')

  await beat({ mode: 'sleeping' })
  assert.equal(labelOf(sleepBtn), 'WAKE', 'the bus says sleeping → WAKE')
  assert.equal(labelOf(mute), 'MUTE', 'and mute follows the same reading back')

  overlay.destroy()
})

// ---- SPEC §8.1: keys need a chord ------------------------------------------
//
// A BARE letter does nothing, in every state (Owner hit T while typing on
// another screen on 2026-09-19 and his call ended). The chord is exactly
// ctrl+alt, matched on `event.code` because Option rewrites `event.key` on
// macOS — ⌃⌥T arrives with `key: '†'` and `code: 'KeyT'`, which is what these
// fakes carry.

/** The keydown a real ⌃⌥<letter> produces on macOS: the code is the physical
 *  key, the `key` is the dead-key character Option made of it. */
function chord(letter, extra = {}) {
  const OPTION_KEY = { t: '†', m: 'µ', z: 'Ω', w: '∑', f: 'ƒ', d: '∂' }
  return {
    key: OPTION_KEY[letter.toLowerCase()] || letter,
    code: 'Key' + letter.toUpperCase(),
    ctrlKey: true, altKey: true, metaKey: false, shiftKey: false,
    ...extra
  }
}

/** The same key with nothing held down. */
function bare(letter, extra = {}) {
  return { key: letter, code: 'Key' + letter.toUpperCase(), ...extra }
}

test('⌃⌥T / ⌃⌥M / ⌃⌥Z drive the voice commands, and no other key is swallowed', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub({ ...OFF, call: 'on', mode: 'listening' })
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const swallowed = []
  const key = (spec) => {
    let stopped = false
    env.doc.fire('keydown', {
      target: { tagName: 'DIV' },
      preventDefault() { stopped = true }, stopPropagation() {}, ...spec
    })
    swallowed.push(stopped)
    return stopped
  }

  key(chord('m'))
  assert.deepEqual(presence.asked, ['mute'], '⌃⌥M on a live unmuted call asks to mute')
  key(chord('z'))
  assert.deepEqual(presence.asked, ['mute', 'sleep'], '⌃⌥Z asks Agent to sleep')
  key(chord('t'))
  assert.deepEqual(presence.asked, ['mute', 'sleep', 'stop'], '⌃⌥T on a live call ends it')

  const before = presence.asked.length
  key(bare('a'))
  key({ key: 'Enter', code: 'Enter' })
  key({ key: ' ', code: 'Space' })
  key(chord('t', { metaKey: true }))
  assert.equal(presence.asked.length, before, 'no other key reaches the voice door')
  assert.deepEqual(swallowed.slice(3), [false, false, false, false], 'and none of them is swallowed')

  // The pressed button says what it is waiting for until the bus reports.
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const talk = findByAttr(root, 'data-jv', 'talk')
  assert.equal(labelOf(talk), 'ending…', 'pressed → ending… while the bus is silent')
  await sleep(120)
  presence.push({ call: 'off', mode: 'idle' })
  assert.equal(labelOf(talk), 'START TALK', 'the bus reported: the pending state clears')

  overlay.destroy()
})


test('a silent wait puts the honest "No answer" line in the VOICE pod', async () => {
  const env = install(true)
  // Fake timers on the overlay's own seam: timerSet/timerClear read win.setTimeout
  // at call time, so swapping it here lets the 6 s wait be fired by hand instead
  // of by the clock (the same trick the presence tests play with commandWaitMs).
  const timers = []
  env.win.setTimeout = (fn, ms) => { timers.push({ fn, ms, live: true }); return timers.length }
  env.win.clearTimeout = id => { const t = timers[id - 1]; if (t) t.live = false }

  const createOverlay = loadOverlay(env)
  // Call off → START TALK is the one live seat. The stub bus takes the ask
  // (ok:true) and then never reports a new state: exactly the Talk-not-loaded case.
  const presence = presenceStub(OFF)
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const talk = findByAttr(root, 'data-jv', 'talk')
  const msg = findByClass(root, 'jv-cmdmsg')
  assert.ok(talk && msg, 'the button and the honest line both exist')
  assert.equal(msg.textContent, '', 'nothing to say before a press')

  talk.click()
  await null; await null                       // let the command promise settle
  assert.deepEqual(presence.asked, ['start'], 'the ask left the building')
  assert.equal(labelOf(talk), 'starting…', 'and the label waits on the bus')

  // START TALK presses the host's own voice button first and waits for its pill
  // (SPEC §4.9: 4 s, plus 0.8 s for a folded Voice hub's rows and 0.3 s for the
  // hub itself to open — §4.9 amendment 2), may have to bring a chat forward and
  // watch 4 s for the composer (§4.8), then open the floating HUD and wait for
  // its relay (8 s), then re-send `start` up to three times 1.5 s apart (§4.7
  // amendment). The overlay's generic line always sits half a second past all of
  // that, so command()'s own named reason lands first.
  // §4.10 adds the draft-chat save (TWENTY s — amendment 3 waits a slow one out
  // instead of racing it), its settle (4 s) and the 90 s START will stand and
  // wait while Agent finishes an answer (ruling 2).
  const wait = timers.find(t => t.ms === 4000 + 800 + 300 + 4000 + 8000 + 3 * 1500 +
    20000 + 4000 + 90000 + 500 && t.live)
  assert.ok(wait, 'the press armed the 136.1 s wait — command()\'s budget plus the grace')
  wait.fn()                                    // the wait is over, nothing reported

  // §4.9 amendment 6: the generic last-resort line names the door that works
  // on this host — the round button beside the message box, not Talk.
  assert.equal(msg.textContent, 'No answer · press the round voice button beside the message box once',
    'the VOICE pod says the honest thing')
  assert.equal(msg.style.display, '', 'and the line is shown, not hidden')
  assert.equal(labelOf(talk), 'START TALK', 'the label drops back to the live reading')

  overlay.destroy()
})

// §4.7 amendment — TIMEOUT ORDER. The generic "Talk did not answer" line is the
// last resort. If it fired first it would overwrite the real reason command()
// was about to give ("no Talk button in this window (1 talk-named button…)"),
// which is the one sentence that tells Owner what to do next. So the overlay
// reads the store's own budget and always waits half a second longer than it.
test('the overlay always waits half a second longer than command() does', async () => {
  const env = install(true)
  const timers = []
  env.win.setTimeout = (fn, ms) => { timers.push({ fn, ms, live: true }); return timers.length }
  env.win.clearTimeout = id => { const t = timers[id - 1]; if (t) t.live = false }

  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF, 4200)     // a store with a shorter wait
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  findByAttr(root, 'data-jv', 'talk').click()
  await null; await null

  assert.ok(timers.find(t => t.ms === 4700 && t.live),
    'the pending timeout followed the store down to its budget + 500 ms')
  assert.ok(!timers.find(t => t.ms === 4200 && t.live),
    'and never fires at the same moment command() answers')

  overlay.destroy()
})

// §4.10 ruling 2 — the same rule against the REAL budget, which now carries the
// 90 s START will stand and wait while Agent finishes (plus the draft-chat
// prepare and its settle). The pod must never time out in the middle of that.
test('the pending timeout is the store\'s own budget + 500 ms, 90 s wait included', async () => {
  const env = install(true)
  const timers = []
  env.win.setTimeout = (fn, ms) => { timers.push({ fn, ms, live: true }); return timers.length }
  env.win.clearTimeout = id => { const t = timers[id - 1]; if (t) t.live = false }

  const createOverlay = loadOverlay(env)
  // 20-presence.js's own arithmetic: 4000 native + 800 hub + 300 menu + 4000
  // nav + 8000 doors + 3 x 1500 retries + 20000 save + 4000 settle + 90000
  // while Agent answers.
  const budget = 4000 + 800 + 300 + 4000 + 8000 + 3 * 1500 + 20000 + 4000 + 90000
  const presence = presenceStub(OFF, budget)
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  findByAttr(root, 'data-jv', 'talk').click()
  await null; await null

  assert.ok(timers.find(t => t.ms === budget + 500 && t.live),
    'the overlay waits out the whole 90 s wait, and half a second more')

  overlay.destroy()
})

// ---- SPEC §4.10 ruling 1: the invisible composer contribution --------------

test('the composer bridge renders null, hands the controller over, and clears it on unmount', async () => {
  const env = install(true)
  const controller = {
    capabilities: { prepareSession: 1 },
    owner: { connectionId: 'local', profile: 'agent', sessionId: null, storedSessionId: null },
    prepareSession: async () => ({ sessionId: 's1', storedSessionId: 'stored-1' })
  }
  // A React whose effects actually run, so the bridge's one effect can be
  // driven by hand: mount, then unmount.
  const effects = []
  const react = {
    createElement: (type, props, ...kids) => ({ type, props: props || {}, kids }),
    useState: initial => [initial, () => {}],
    useEffect: fn => { effects.push(fn) }
  }
  const plugin = loadPlugin(fakeSDK({ controller }), react)
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const bridge = harness.registered.find(c => c.id === 'jarvis-composer-voice')
  assert.ok(bridge, 'the invisible contribution is registered in the main window')
  assert.equal(bridge.area, 'composer.actions', 'it sits beside the message box')
  assert.equal(typeof bridge.render, 'function', 'and it is a render contribution, not data')

  const element = bridge.render()
  assert.equal(typeof element.type, 'function', 'the render returns the bridge component')
  assert.equal(element.type(), null, 'which draws nothing at all — no layout change')
  assert.equal(effects.length, 1, 'and registers the controller in one effect')

  const beat = () => JSON.parse(env.writes[env.writes.length - 1].content)
  const toggleRow = harness.registered.find(c => c.id === 'jarvis-palette-toggle')
  assert.deepEqual(beat().talkProbe.controller, { present: false, stored: '', canPrepare: false },
    'nothing is claimed before the effect has run')

  const cleanup = effects[0]()
  toggleRow.data.run()                       // opening the overlay stamps a beat
  await new Promise(r => setTimeout(r, 700))
  assert.deepEqual(beat().talkProbe.controller, { present: true, stored: '', canPrepare: true },
    'the mounted composer\'s controller reached the plugin: a draft chat it can prepare')

  cleanup()                                   // the composer unmounts
  toggleRow.data.run()
  await new Promise(r => setTimeout(r, 700))
  assert.deepEqual(beat().talkProbe.controller, { present: false, stored: '', canPrepare: false },
    'and the reference is dropped again, never left dangling')

  harness.disposers.forEach(fn => fn())
})

test('a host without the controller hook simply does not get the bridge', async () => {
  install(true)
  const plugin = loadPlugin(fakeSDK({ hook: false }))
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const ids = harness.registered.map(c => c.id)
  assert.ok(!ids.includes('jarvis-composer-voice'),
    'no hook, no contribution — and START behaves exactly as it did before §4.10')
  assert.equal(ids.length, 8, 'every door is untouched (§7.2 added the window palette row)')

  harness.disposers.forEach(fn => fn())
})

test('the HUD window registers no composer bridge either', async () => {
  install(false, '?win=hud')
  const controller = { capabilities: { prepareSession: 1 }, owner: {}, prepareSession: async () => ({}) }
  const plugin = loadPlugin(fakeSDK({ controller }))
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  assert.equal(harness.registered.length, 0,
    'the relay window registers nothing at all — the composer bridge included')

  harness.disposers.forEach(fn => fn())
})

// §4.8 ruling 6 — MUTE and SLEEP follow the DOOR, not only the snapshot. Talk
// in the floating HUD reports on changes only, so between frames this window's
// snapshot can read `call off` during a perfectly live call. Greying MUTE then
// is the drift the judge caught at 50-overlay.js:509.
test('MUTE and SLEEP stay live while the store says a command can be delivered', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF, null, true)   // snapshot off, door open
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const mute = findByAttr(root, 'data-jv', 'mute')
  const sleepBtn = findByAttr(root, 'data-jv', 'sleep')

  assert.equal(mute.disabled, false, 'the door is open, so MUTE is pressable')
  assert.equal(sleepBtn.disabled, false, 'and so is SLEEP')
  assert.equal(mute.attributes.title, 'mute  (⌃⌥M)', 'no "no live call" excuse in the tooltip, and the hint is the chord')

  mute.click()
  await null; await null
  assert.deepEqual(presence.asked, ['mute'], 'and the press actually reaches the store')

  overlay.destroy()
})

test('MUTE is greyed with a reason when no door is open at all', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF, null, false)
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const mute = findByAttr(root, 'data-jv', 'mute')
  assert.equal(mute.disabled, true)
  assert.equal(mute.attributes.title, 'no live call · start Talk first')

  overlay.destroy()
})

// SPEC §4.9 ruling 3 — the built-in voice has no sleep. Greying the button and
// saying why is the honest move: offering a press that lands nowhere is not.
test('with the built-in voice as the source, SLEEP is greyed and says why', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const NATIVE_ON = {
    ...OFF,
    call: 'on',
    mode: 'listening',
    source: { status: 'native', voice: 'native-analyser', mic: 'tap' }
  }
  const presence = presenceStub(NATIVE_ON, null, true)
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const sleepBtn = findByAttr(root, 'data-jv', 'sleep')
  const mute = findByAttr(root, 'data-jv', 'mute')
  const talk = findByAttr(root, 'data-jv', 'talk')

  assert.equal(sleepBtn.disabled, true, 'SLEEP is not offered')
  assert.equal(sleepBtn.attributes.title, 'built-in voice has no sleep', 'and the title says exactly why')
  assert.equal(mute.disabled, false, 'MUTE still works — the host has a mute button')
  assert.equal(labelOf(talk), 'END TALK', 'and the call can still be ended')

  // The VOICE pod names the source word, so which voice system is feeding the
  // orb is readable off the glass (§4.9 ruling 6).
  const notes = []
  const collect = node => {
    if (!node) return
    if (typeof node.className === 'string' && node.className.split(' ').includes('jv-pod-n')) notes.push(node.textContent)
    ;(node.childNodes || []).forEach(collect)
  }
  collect(root)
  assert.ok(notes.includes('source native / native-analyser / tap'),
    'the VOICE pod says which voice system fed this reading')

  // §4.9 amendment 1 — a muted built-in call reads UNMUTE, and that is the
  // press that lands on the "Unmute microphone" button the host has up.
  await sleep(120)
  presence.push({ mode: 'muted' })
  assert.equal(labelOf(mute), 'UNMUTE', 'muted → the button offers the way out of it')
  assert.equal(mute.disabled, false, 'and it can be pressed')
  await sleep(120)
  presence.push({ mode: 'listening' })

  // Back to Talk: the same seat is live again. (The overlay paints text at
  // 10 Hz, so the next reading needs its own beat — as everywhere else here.)
  await sleep(120)
  presence.push({ source: { status: 'bus', voice: 'analyser', mic: 'tap' } })
  assert.equal(sleepBtn.disabled, false, 'with Talk on the line SLEEP comes back')

  overlay.destroy()
})

// §4.10 rulings 2 and 3 — the pod carries the store's own line, and the START
// button becomes the way out of a wait.
test('the VOICE pod shows the store\'s notice, and CANCEL calls off the wait', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const state = { notice: '', waiting: false, cancels: 0 }
  const presence = presenceStub(OFF)
  presence.store.notice = () => state.notice
  presence.store.startWaiting = () => state.waiting
  presence.store.cancelStart = () => { state.cancels += 1; state.waiting = false; return true }
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const talk = findByAttr(root, 'data-jv', 'talk')
  const msg = findByClass(root, 'jv-cmdmsg')
  assert.equal(msg.textContent, '', 'nothing to say yet')

  // §8 amendment A ruling 5, finished by C1 — a call the host dropped is said
  // ONCE, under the orb, by the black box (§8.2). The store no longer publishes
  // a pod copy of it at all (the constant is gone from 20-presence.js), so the
  // pod's line for an ended call is simply the empty one it always was before
  // something happened.
  state.notice = ''
  await sleep(120)
  presence.push({ updatedAt: 1 })
  assert.equal(msg.textContent, '', 'the dropped-call line is the under-orb line\'s to say, not the pod\'s')
  assert.equal(msg.style.display, 'none', 'and the pod shows nothing at all')

  // every OTHER line the store publishes still reaches the pod, unchanged
  state.notice = 'New chat · the call may drop when Agent\'s first answer starts'
  await sleep(120)
  presence.push({ updatedAt: 2 })
  assert.equal(msg.textContent, 'New chat · the call may drop when Agent\'s first answer starts',
    'the store\'s line reaches the glass')
  assert.equal(msg.style.display, '', 'and it is shown')

  // START, and the store stands by for Agent to finish.
  state.notice = 'Agent is answering · voice starts when he finishes'
  state.waiting = true
  talk.click()
  await null; await null
  assert.deepEqual(presence.asked, ['start'], 'the ask went out')
  await sleep(120)
  presence.push({ updatedAt: 3 })
  assert.equal(labelOf(talk), 'CANCEL', 'the button offers the way out while it waits')
  assert.equal(msg.textContent, 'Agent is answering · voice starts when he finishes',
    'and the pod says what it is waiting for')

  // The same button — and the T key — now cancels instead of asking again.
  talk.click()
  await null; await null
  assert.equal(state.cancels, 1, 'the wait was called off')
  assert.deepEqual(presence.asked, ['start'], 'and no second start was ever sent')

  state.notice = ''
  await sleep(120)
  presence.push({ updatedAt: 3 })
  assert.equal(msg.textContent, '', 'the line goes when the store stops publishing it')

  overlay.destroy()
})

// ---- SPEC §4.10 amendment 2: closing the dashboard calls START off ---------

test('closing the dashboard cancels a waiting START', async () => {
  const env = install(true)
  const presence = presenceStub(OFF, 1000)
  let cancels = 0
  presence.store.cancelStart = () => { cancels += 1; return true }
  presence.store.startWaiting = () => true

  const createOverlay = loadOverlay(env)
  const overlay = createOverlay({ presence: presence.store, data: dataStub, log: () => {} })
  overlay.open()
  assert.equal(cancels, 0, 'opening calls nothing off')

  overlay.close()
  assert.equal(cancels, 1, 'a per-minute call never starts behind a closed dashboard')

  overlay.close()
  assert.equal(cancels, 1, 'and a second close is not a second cancel')

  overlay.destroy()
})

// ---- SPEC §4.10 amendment 7: two tiles, two controllers -------------------

test('two composers mounted: the focused chat\'s controller is the one Jarvis uses', async () => {
  const env = install(true)
  const draft = {
    capabilities: { prepareSession: 1 },
    owner: { storedSessionId: null },                 // a brand-new chat
    prepareSession: async () => ({ storedSessionId: 's-draft' })
  }
  const saved = {
    capabilities: { prepareSession: 1 },
    owner: { storedSessionId: 'stored-9' },
    prepareSession: async () => ({ storedSessionId: 'stored-9' })
  }
  const effects = []
  const react = {
    createElement: (type, props, ...kids) => ({ type, props: props || {}, kids }),
    useState: initial => [initial, () => {}],
    useEffect: fn => { effects.push(fn) }
  }
  const sdk = fakeSDK({ controller: null })
  let focusedStored = 'stored-9'
  sdk.host.state.focusedStoredSessionId = { get: () => focusedStored, listen: () => () => {} }
  const queue = [draft, saved]
  sdk.useComposerVoiceController = () => queue.shift() || null

  const plugin = loadPlugin(sdk, react)
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const bridge = harness.registered.find(c => c.id === 'jarvis-composer-voice')
  bridge.render().type()                       // the draft tile mounts
  bridge.render().type()                       // the saved tile mounts
  const cleanups = effects.map(fn => fn())
  assert.equal(cleanups.length, 2, 'both composers registered')

  const beat = () => JSON.parse(env.writes[env.writes.length - 1].content)
  const toggleRow = harness.registered.find(c => c.id === 'jarvis-palette-toggle')
  toggleRow.data.run()
  await new Promise(r => setTimeout(r, 700))
  assert.deepEqual(beat().talkProbe.controller, { present: true, stored: 'stored-9', canPrepare: true },
    'the focused chat is the saved one, so its composer is the one Jarvis reads')

  focusedStored = ''                           // Owner clicks into the draft tile
  toggleRow.data.run()
  await new Promise(r => setTimeout(r, 700))
  assert.deepEqual(beat().talkProbe.controller, { present: true, stored: '', canPrepare: true },
    'a draft\'s empty id matches the host\'s null — that tile is the one to prepare')

  cleanups[0]()                                // the draft tile closes
  toggleRow.data.run()
  await new Promise(r => setTimeout(r, 700))
  assert.deepEqual(beat().talkProbe.controller, { present: true, stored: 'stored-9', canPrepare: true },
    'an unmount falls back to the composer that is still there, never to nothing')

  harness.disposers.forEach(fn => fn())
})

// ===========================================================================
// SPEC §7 — Jarvis mode v2: the right rail, the NOW box, its own window
// ===========================================================================

/** The overlay file exports more than the factory now: §7.3 / §7.4 readers are
 *  pure functions, so their words can be pinned without a browser. */
function loadKit(env) {
  const source = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n' +
    fs.readFileSync(THEME_SRC, 'utf8') + '\n' + fs.readFileSync(OVERLAY_SRC, 'utf8')
  return new Function('window', 'document', `${source}
    return { createOverlay, jarvisNowLines, jarvisStateRows, jarvisAgentLines,
             jarvisSystemDots, jarvisWorkingPresence, jarvisSpan, jarvisRailCaps }`)(env.win, env.doc)
}

const T0 = 1789800000000          // a fixed clock, so every word below is exact

function textsOf(node, cls, out = []) {
  if (!node) return out
  if (typeof node.className === 'string' && node.className.split(' ').includes(cls)) out.push(node.textContent)
  ;(node.childNodes || []).forEach(kid => textsOf(kid, cls, out))
  return out
}

function countOf(node, cls) {
  return textsOf(node, cls).length
}

const RUNNING = {
  source: 'events', session: 's-1', focused: true, running: true,
  startedAt: T0 - 100000, lastEventAt: T0 - 4000, endedAt: 0, steps: 12, modelCalls: 31,
  tool: { name: 'terminal', label: 'running a command', detail: 'git status', startedAt: T0 - 4000 },
  lastTool: null, thought: 'checking which file writes the receipt', saying: '',
  subagents: [{ id: 'sub-1', label: 'reader', status: 'running', tool: 'read_file' }],
  needsYou: null,
  recent: [
    { at: T0 - 9000, label: 'reading a file', detail: 'SPEC.md', ms: 420, ok: true },
    { at: T0 - 14000, label: 'searching the web', detail: 'hermes plugin sdk', ms: 1900, ok: false }
  ],
  lastTurn: null
}

// ---- §7.3 ruling 5: the NOW box -------------------------------------------

test('the NOW box prints the facts of a running turn — and never the word "stuck"', () => {
  const env = install(true)
  const kit = loadKit(env)

  const a = kit.jarvisNowLines(RUNNING, T0)
  assert.equal(a.line, 'running a command', 'line 1 is the tool in plain words')
  assert.equal(a.detail, 'git status', 'line 2 is what it is doing')
  assert.equal(a.meta, 'step 12 · 1 m 40 s · no news for 4 s', 'line 3 is steps, elapsed, silence')
  assert.equal(a.metaState, '', 'four seconds of quiet is just quiet')
  assert.equal(a.thought, 'checking which file writes the receipt')
  assert.equal(a.chips.length, 1, 'the sub-agent rides as a chip')
  assert.equal(a.recent.length, 2, 'the finished steps are listed, newest first')
  assert.equal(a.recent[1].ok, false, 'a step that failed is marked as one')
  assert.equal(a.underOrb, 'running a command · 1 m 40 s', 'and the line under Agent mirrors it')
  assert.ok(!/stuck/i.test(JSON.stringify(a)), 'no verdict is ever printed (§7.3 ruling 3)')

  // The quiet-time facts, at the three thresholds.
  const quiet = kit.jarvisNowLines({ ...RUNNING, lastEventAt: T0 - 48000 }, T0)
  assert.match(quiet.meta, /no news for 48 s$/, '48 seconds is said out loud')
  assert.equal(quiet.metaState, '', 'and is still not a warning')
  assert.equal(kit.jarvisNowLines({ ...RUNNING, lastEventAt: T0 - 61000 }, T0).metaState, 'warm',
    'past a minute the line warms')
  assert.equal(kit.jarvisNowLines({ ...RUNNING, lastEventAt: T0 - 181000 }, T0).metaState, 'hot',
    'past three minutes it goes coral')

  // A turn under 8 s earns no line under the orb (§7.3 ruling 6).
  const young = kit.jarvisNowLines({ ...RUNNING, startedAt: T0 - 5000 }, T0)
  assert.equal(young.underOrb, '', 'five seconds in, Agent keeps the centre to himself')
})

test('the NOW box: quiet, never seen, another chat, and the one coral block', () => {
  const env = install(true)
  const kit = loadKit(env)

  const none = kit.jarvisNowLines(undefined, T0)
  assert.equal(none.line, 'quiet')
  assert.equal(none.meta, 'no work seen yet in this window',
    'a missing feed says exactly that — it does not draw an empty box')

  const idle = kit.jarvisNowLines({
    source: 'events', running: false, focused: true,
    lastTurn: { endedAt: T0 - 360000, seconds: 322, steps: 34, modelCalls: 31, outcome: 'done' }
  }, T0)
  assert.equal(idle.line, 'quiet')
  assert.equal(idle.meta, 'last job took 5 m 22 s, 34 steps, 6 min ago', 'the idle line Owner asked for')

  const elsewhere = kit.jarvisNowLines({ ...RUNNING, focused: false }, T0)
  assert.equal(elsewhere.tag, 'another chat', 'a turn in another chat says so in the header')

  const asked = kit.jarvisNowLines({
    ...RUNNING, needsYou: { kind: 'approval', text: 'run the migration on the mini?' }
  }, T0)
  assert.equal(asked.needsYou, 'Agent needs a yes · run the migration on the mini?')
  const clarify = kit.jarvisNowLines({
    ...RUNNING, needsYou: { kind: 'clarify', text: 'which brain did you mean?' }
  }, T0)
  assert.equal(clarify.needsYou, 'Agent needs an answer · which brain did you mean?',
    'a question is not a yes/no — the block says what it is')

  const busy = kit.jarvisNowLines({ source: 'host-busy', running: true, focused: true, startedAt: T0 - 3000 }, T0)
  assert.equal(busy.line, 'busy')
  assert.equal(busy.detail, 'Hermes says a turn is running · no step detail reached this window')
})

// ---- §7.4: Agent's STATE rows ----------------------------------------------

// SPEC §8 amendment A ruling 7 — every fixture row is SYNTHETIC: invented ids
// and invented wording, never a row copied off Owner's real STATE file.
const STATE_ROWS = {
  status: 'ok',
  updatedAt: T0 - 720000,          // 12 minutes ago
  rows: [
    { id: 'demo-switch', where: '…', next: 'Owner flips the sample switch', owner: 'Owner',
      follow_up_at: new Date(T0 + 7200000).toISOString(), waiting_on_owner: true, overdue: false,
      // §8.4 item 3 — the plain words behind the ask, when Agent has written them
      brief: { title: 'Flip one sample switch', what: 'one setting on one sample screen',
        why: 'the sample run cannot start until it is on', do: 'open the sample panel and flip it',
        takes: 'two minutes', where: 'the sample settings screen', updated: '14:35' } },
    { id: 'demo-seats', where: '…', next: 'Owner confirms the four sample seats', owner: 'Owner',
      follow_up_at: new Date(T0 - 172800000).toISOString(), waiting_on_owner: true, overdue: true },
    { id: 'demo-no-date', where: '…', next: 'Owner picks a sample colour', owner: 'Owner',
      follow_up_at: null, waiting_on_owner: true, overdue: false },
    { id: 'demo-mirror', where: '…', next: 'the sample weekly run', owner: 'Agent',
      follow_up_at: new Date(T0 + 86400000).toISOString(), waiting_on_owner: false, overdue: false },
    { id: 'demo-cron', where: '…', next: 'a rate-conservative sample cron', owner: 'Agent',
      follow_up_at: null, waiting_on_owner: false, overdue: false }
  ],
  closedCount: 4, note: null
}

test('WAITING ON YOU sorts by the soonest date, names an overdue row, and dates the file', () => {
  const env = install(true)
  const kit = loadKit(env)
  const state = kit.jarvisStateRows(STATE_ROWS, T0)

  assert.equal(state.status, 'ok')
  assert.deepEqual(state.waiting.map(r => r.id), ['demo-seats', 'demo-switch', 'demo-no-date'],
    'overdue first, then the soonest date, then the rows with no date at all')
  assert.equal(state.waiting[0].due, 'overdue 2 d', 'an overdue row says how long by')
  assert.equal(state.waiting[0].overdue, true, 'and is marked so the text can go coral')
  assert.match(state.waiting[1].due, /^due (today|tomorrow|\d\d \w{3}) \d\d:\d\d$/, 'a future row reads as a due stamp')
  assert.equal(state.waiting[2].due, 'no date', 'a row with no date says that rather than guessing one')
  assert.deepEqual(state.flight.map(r => r.id), ['demo-mirror', 'demo-cron'], 'everything else is in flight')
  assert.equal(state.header, '5 rows · updated 12 min ago', 'the header dates the file')
  assert.equal(state.waitingMore, 0)
})

test('more waiting rows than the box holds are counted, never dropped silently', () => {
  const env = install(true)
  const kit = loadKit(env)
  const many = { ...STATE_ROWS, rows: [] }
  for (let i = 0; i < 7; i += 1) {
    many.rows.push({
      id: 'demo-row-' + i, next: 'Owner does sample thing ' + i, owner: 'Owner',
      follow_up_at: new Date(T0 + i * 3600000).toISOString(), waiting_on_owner: true, overdue: false
    })
  }
  const state = kit.jarvisStateRows(many, T0)
  assert.equal(state.waiting.length, 4, 'four rows on the glass')
  assert.equal(state.waitingMore, 3, 'and the other three are counted')
})

test('§7 amendment 5: a short window is handed fewer WHOLE rows, never a cut one', () => {
  const env = install(true)
  const kit = loadKit(env)
  const caps = h => kit.jarvisRailCaps(h)

  const four = c => ({ waiting: c.waiting, flight: c.flight, rows: c.rows, recent: c.recent })

  // the four ASKS keep their seats wherever the rail is tall enough. §8
  // amendments C10 raised every reading on this rail to 11 px, so the rows are
  // taller and the literal 5 in flight no longer fits beside them; AGENT IN
  // FLIGHT is the rail's declared give-way and hands one back, counted out
  // loud (the same ruling as §7.1.1 and amendment B.1).
  assert.deepEqual(four(caps(1440)), { waiting: 4, flight: 3, rows: 9, recent: 1 })
  // DEVIATION from the §7.4 amendment, recorded in src/50-overlay.js and ruled
  // the same way as §7.1.1: between 1000 and 1400 px the literal 4 / 5 no
  // longer fit. §8.4 put two more boxes on this rail and opened a brief inside
  // WAITING ON YOU, and the no-cut gate wins over a literal count.
  assert.ok(caps(1000).waiting < 4, 'seven boxes and an open brief cost the literal maxima')
  assert.ok(caps(1000).waiting >= 2, 'but never so much that a person cannot act')

  // the sizes the renders were checked at (tests/overlay-preview.html,
  // ?state=running&rows=max): every box keeps whole rows at each of them.
  // §8 amendment B.5 took ONE row off the shared budget at 1080 and at 900:
  // OVERNIGHT JOBS is 16 px taller with the next run on its own line, and at
  // ?rows=max that 16 px was cutting the NOW box (1080) and the rail (900).
  // The asks keep their seats and their open brief; AGENT IN FLIGHT hands back
  // the row and counts it out loud, which is amendment B.1's ruling again.
  assert.deepEqual(four(caps(1080)), { waiting: 3, flight: 2, rows: 4, recent: 0 })
  assert.deepEqual(four(caps(900)), { waiting: 2, flight: 0, rows: 3, recent: 0 })
  assert.deepEqual(four(caps(813)), { waiting: 2, flight: 0, rows: 2, recent: 0 })
  assert.deepEqual(four(caps(760)), { waiting: 1, flight: 0, rows: 1, recent: 0 })

  // a box may collapse to its header and its count, but it is never handed a
  // fraction of a row, and a shorter window never gets MORE rows than a taller
  let last = null
  for (let h = 1440; h >= 600; h -= 1) {
    const c = caps(h)
    for (const key of ['waiting', 'flight', 'rows', 'recent']) {
      assert.ok(Number.isInteger(c[key]) && c[key] >= 0, `${key} at ${h} is a whole count: ${c[key]}`)
    }
    for (const key of ['waiting', 'flight', 'rows']) {
      if (last) assert.ok(c[key] <= last[key], `${key} may not grow as the window shrinks (${h})`)
    }
    if (last) assert.ok(c.recent <= last.recent, `recent may not grow as the window shrinks (${h})`)
    assert.ok(c.rows >= c.waiting, `the shared budget covers the asks at ${h}`)
    last = c
  }
  assert.equal(caps(1000).recent, 0, 'the STATE rows cost the history below ~1180 px')
  assert.equal(caps(1180).recent, 1, 'and it comes back as soon as both fit')
  assert.deepEqual(caps(0), caps(900), 'an unreadable height is treated as the 900 px window')
})

test('§7 amendment 5: a collapsed box counts its rows out loud instead of dropping them', () => {
  const env = install(true)
  const kit = loadKit(env)
  const state = kit.jarvisStateRows(STATE_ROWS, T0, { waiting: 1, flight: 0 })
  assert.equal(state.waiting.length, 1, 'one whole ask is still drawn')
  assert.equal(state.waitingMore, 2, 'and the two it cannot draw are counted')
  assert.equal(state.flight.length, 0, 'a cap of 0 collapses the box')
  assert.equal(state.flightMore, 2, 'every row it is holding back is counted')
})

test('§7 amendment 5: the NOW history is cut in whole rows, by the same caps', () => {
  const env = install(true)
  const kit = loadKit(env)
  const activity = {
    source: 'events', session: 's', focused: true, running: true,
    startedAt: T0 - 60000, lastEventAt: T0 - 1000, steps: 9, tool: null, saying: '',
    thought: 'a thought', subagents: [], needsYou: { kind: 'approval', text: 'redeploy?' },
    recent: [0, 1, 2, 3, 4, 5].map(i => ({ at: T0 - i * 1000, label: 'reading a file', detail: 'f' + i, ms: 100, ok: true })),
    lastTurn: null
  }
  assert.equal(kit.jarvisNowLines(activity, T0).recent.length, 4, 'four rows when nobody says otherwise')
  assert.equal(kit.jarvisNowLines(activity, T0, { recent: 2 }).recent.length, 2)
  assert.equal(kit.jarvisNowLines(activity, T0, { recent: 0 }).recent.length, 0, 'a short window drops the history whole')
  assert.equal(kit.jarvisNowLines(activity, T0, { recent: 0 }).needsYou, 'Agent needs a yes · redeploy?',
    'and the one thing Owner has to answer is never what gives way')
})

test('no STATE at all reads unreachable — never rows without an age', () => {
  const env = install(true)
  const kit = loadKit(env)
  for (const slice of [undefined, null, { status: 'unreachable', rows: [], note: 'backend offline' }]) {
    const state = kit.jarvisStateRows(slice, T0)
    assert.equal(state.status, 'unreachable')
    assert.deepEqual(state.waiting, [])
    assert.deepEqual(state.flight, [])
  }
})

// ---- §7.4: AGENTS AT WORK and SYSTEMS -------------------------------------

test('AGENTS AT WORK merges busy agents, running jobs and the idle count', () => {
  const env = install(true)
  const kit = loadKit(env)
  const lines = kit.jarvisAgentLines({
    health: { fleet: 'ok', jobs: 'ok' },
    fleet: [{ id: 'agent', label: 'Agent', busy: true }, { id: 'helper-1', label: 'Helper 1', busy: false },
      { id: 'helper-2', label: 'Helper 2', busy: false }],
    jobs: [{ id: 'j1', label: 'weekly mirror', status: 'running' }]
  })
  assert.deepEqual(lines.busy, ['Agent'])
  assert.equal(lines.jobs.length, 1)
  assert.equal(lines.idle, '2 of 3 agents idle')

  const dark = kit.jarvisAgentLines({ health: { fleet: 'unreachable', jobs: 'unreachable' } })
  assert.equal(dark.status, 'unreachable', 'both readings gone = the box says unreachable')
})

test('the SYSTEMS dots carry the same readings the drawer pods show', () => {
  const env = install(true)
  const kit = loadKit(env)
  const dots = kit.jarvisSystemDots({
    health: { brains: 'ok', senses: 'ok' },
    connection: { gateway: 'open', backend: 'ok' },
    brains: [{ id: 'brain-1', label: 'Brain 1', status: 'ok' },
      { id: 'brain-2', label: 'Brain 2', status: 'unknown' }],
    senses: [{ id: 'a', status: 'ok' }, { id: 'b', status: 'unknown' }]
  }, { source: { status: 'native' }, demo: false })

  const bag = {}
  dots.forEach(d => { bag[d.label] = d.state })
  assert.equal(bag.GATEWAY, 'ok')
  assert.equal(bag.BACKEND, 'ok')
  assert.equal(bag['VOICE NATIVE'], 'ok', 'the voice dot names the source word')
  assert.equal(bag['Brain 1'], 'ok')
  assert.equal(bag['Brain 2'], 'off', 'a configured-but-off brain is grey, not green')
  assert.equal(bag['SENSES 1/2'], 'warn')

  const dark = kit.jarvisSystemDots({
    health: { brains: 'unreachable' }, connection: { gateway: '', backend: 'offline' }, senses: []
  }, { source: { status: 'none' } })
  const dbag = {}
  dark.forEach(d => { dbag[d.label] = d.state })
  assert.equal(dbag.BACKEND, 'bad')
  assert.equal(dbag.BRAINS, 'bad')
  assert.equal(dbag['VOICE NONE'], 'bad')
})

// ---- §7.3 ruling 6: the `working` hand-off --------------------------------

test('a running tool hands the scene `working`, and never touches the store', () => {
  const env = install(true)
  const kit = loadKit(env)
  const thinking = { call: 'on', mode: 'thinking', levels: { voice: 0, mic: 0 } }

  const derived = kit.jarvisWorkingPresence(thinking, RUNNING)
  assert.equal(derived.mode, 'working', 'a tool is running: the orb goes amber')
  assert.equal(thinking.mode, 'thinking', 'and the snapshot the store published is untouched')
  assert.notEqual(derived, thinking, 'it is a copy, not the store\'s object')

  assert.equal(kit.jarvisWorkingPresence(thinking, { ...RUNNING, tool: null }).mode, 'thinking',
    'thinking with no tool stays thinking')
  assert.equal(kit.jarvisWorkingPresence(thinking, { ...RUNNING, running: false }).mode, 'thinking',
    'and a finished turn cannot make it work')
  assert.equal(kit.jarvisWorkingPresence({ call: 'off', mode: 'thinking' }, RUNNING).mode, 'thinking',
    'no call, no hand-off')
  assert.equal(kit.jarvisWorkingPresence({ call: 'on', mode: 'speaking' }, RUNNING).mode, 'speaking',
    'speaking is Agent talking — it is never rewritten')
})

// ---- the rail on the glass ------------------------------------------------

const RAIL_DATA = {
  connection: { profile: 'agent', gateway: 'open', model: 'grok-4.6', backend: 'ok' },
  brains: [{ id: 'brain-1', label: 'Brain 1', status: 'ok' }],
  senses: [{ id: 'a', status: 'ok' }],
  fleet: [{ id: 'agent', label: 'Agent', busy: true, sessions: 2 }],
  jobs: [{ id: 'j1', label: 'weekly mirror', status: 'running' }],
  lever: { text: 'Ship Jarvis mode', source: 'STATE.md' },
  events: [], panel: null, health: { brains: 'ok', senses: 'ok', fleet: 'ok', jobs: 'ok', lever: 'ok' },
  activity: { ...RUNNING, startedAt: Date.now() - 100000, lastEventAt: Date.now() - 4000 },
  agentState: STATE_ROWS,
  updatedAt: 0
}

test('the rail draws NOW, both STATE boxes and SYSTEMS — with one coral block', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub({ ...OFF, call: 'on', mode: 'thinking' })
  const data = { get: () => ({ ...RAIL_DATA, activity: { ...RAIL_DATA.activity, needsYou: { kind: 'approval', text: 'ship it?' } } }), subscribe: () => () => {} }
  const overlay = createOverlay({ presence: presence.store, data, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  assert.equal(textsOf(root, 'jv-now-line')[0], 'running a command', 'NOW leads with the tool')
  assert.equal(countOf(root, 'jv-needs'), 1, 'exactly one coral block on the glass')
  assert.equal(textsOf(root, 'jv-needs')[0], 'Agent needs a yes · ship it?')
  assert.ok(textsOf(root, 'jv-srow-t').some(t => /Flip one sample switch/.test(t)),
    'WAITING ON YOU has Owner\'s rows, each led by its plain-words title (§8.4 item 3)')
  // §8 amendments C10 — at 900 px AGENT IN FLIGHT is the rail's declared
  // give-way and 11 px type costs it its last row: the box stands down to its
  // header and COUNTS what it is holding back, which is the no-cut law doing
  // exactly what it says.
  assert.equal(textsOf(root, 'jv-srow-t').some(t => /the sample weekly run/.test(t)), false,
    'AGENT IN FLIGHT hands its row back at 900 px')
  assert.ok(textsOf(root, 'jv-more').some(t => /^\+\d+ more$/.test(t)),
    'and says out loud how many rows it is holding')
  assert.ok(textsOf(root, 'jv-sysdot').length >= 4, 'SYSTEMS is a row of dots')
  assert.ok(textsOf(root, 'jv-underorb')[0].startsWith('running a command · '),
    'and the line under the orb mirrors line 1')

  overlay.destroy()
})

test('an unreachable backend says so in both STATE boxes', () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF)
  const data = { get: () => ({ ...RAIL_DATA, agentState: undefined, activity: undefined }), subscribe: () => () => {} }
  const overlay = createOverlay({ presence: presence.store, data, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const empties = textsOf(root, 'jv-empty')
  assert.equal(empties.filter(t => t === "Agent's STATE unreachable").length, 2,
    'both boxes name the missing file rather than drawing nothing')
  assert.equal(textsOf(root, 'jv-now-line')[0], 'quiet')

  overlay.destroy()
})

// ---- §7.2: its own window -------------------------------------------------

function overlayWithWindow(env, opts = {}) {
  const createOverlay = loadOverlay(env)
  const asked = []
  const presence = presenceStub(opts.presence || OFF)
  const overlay = createOverlay({
    presence: presence.store,
    data: { get: () => RAIL_DATA, subscribe: () => () => {} },
    log: () => {},
    HermesSDK: { host: { notify: msg => asked.push(msg) } },
    openWindow: opts.openWindow,
    getScope: () => ({ id: 'test-scope', connectionId: 'local', routeProfile: 'default', profileId: 'default' })
  })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  return { overlay, root, asked, presence, notice: () => findByClass(root, 'jv-notice').textContent }
}

test('W opens a peer window: flag down first, overlay closed, one honest line', async () => {
  const env = install(true)
  const seen = []
  const kit = overlayWithWindow(env, {
    openWindow: () => {
      seen.push(env.win.localStorage.getItem('hermes-jarvis:test-scope:open-on-boot'))
      return Promise.resolve({ ok: true })
    }
  })

  findByAttr(kit.root, 'data-jv', 'chrome-w').click()
  await null; await null; await null

  assert.equal(seen.length, 1, 'the host was asked for exactly one window')
  assert.ok(Number(seen[0]) > 0, 'and the boot flag was already down when it was asked')
  assert.equal(kit.overlay.isOpen(), false, 'this window\'s overlay stood down')
  assert.deepEqual(kit.asked.map(a => a.message), [
    'Jarvis mode opened in its own window · drag it to the other display, then press ⌃⌥F for full screen'
  ], 'and the line says what to do next')

  kit.overlay.destroy()
})

test('a live call refuses to open a second window — one microphone, one call', async () => {
  const env = install(true)
  let calls = 0
  const kit = overlayWithWindow(env, {
    presence: { ...OFF, call: 'on', mode: 'listening' },
    openWindow: () => { calls += 1; return Promise.resolve({ ok: true }) }
  })

  findByAttr(kit.root, 'data-jv', 'chrome-w').click()
  await null; await null

  assert.equal(calls, 0, 'nothing was opened')
  assert.equal(kit.notice(), 'End this call first · the new window starts its own call')
  assert.equal(kit.overlay.isOpen(), true, 'and the overlay stays where it is')
  assert.equal(env.win.localStorage.getItem(pluginStorageKey('open-on-boot')), null, 'no flag was left lying about')

  kit.overlay.destroy()
})

test('no window bridge: the flag is taken back and the line names the fix', async () => {
  const env = install(true)
  const kit = overlayWithWindow(env, { openWindow: () => Promise.resolve({ ok: false, reason: 'too old' }) })

  findByAttr(kit.root, 'data-jv', 'chrome-w').click()
  await null; await null; await null

  assert.equal(kit.notice(), 'This Hermes cannot open a second window · update Hermes Desktop')
  assert.equal(kit.overlay.isOpen(), true, 'the overlay is still there to read it')
  assert.equal(env.win.localStorage.getItem(pluginStorageKey('open-on-boot')), null,
    'and the flag came back up, so no later window opens itself by mistake')

  kit.overlay.destroy()
})

test('with no bridge at all the button is dead and says the same thing', async () => {
  const env = install(true)
  const kit = overlayWithWindow(env, {})            // no injection, no window.hermesDesktop.openWindow

  const btn = findByAttr(kit.root, 'data-jv', 'chrome-w')
  assert.equal(btn.disabled, true, 'a door that is not there is not offered')
  btn.click()
  await null; await null
  assert.equal(kit.notice(), 'This Hermes cannot open a second window · update Hermes Desktop')

  kit.overlay.destroy()
})

// ---- §7.2 ruling 4 + key guards -------------------------------------------

test('⌃⌥F, ⌃⌥D and ⌃⌥W never fire from a text field or under an extra modifier', async () => {
  const env = install(true)
  let calls = 0
  const kit = overlayWithWindow(env, { openWindow: () => { calls += 1; return Promise.resolve({ ok: false }) } })
  const right = findByClass(kit.root, 'jv-layer jv-right') || findByClass(kit.root, 'jv-right')

  const key = (spec) => {
    let stopped = false
    env.doc.fire('keydown', {
      target: { tagName: 'DIV' },
      preventDefault() { stopped = true }, stopPropagation() {}, ...spec
    })
    return stopped
  }

  assert.equal(key(chord('w', { target: { tagName: 'TEXTAREA' } })), false, 'the composer keeps the chord too')
  assert.equal(key(chord('d', { target: { tagName: 'INPUT' } })), false)
  assert.equal(key(chord('d', { target: { tagName: 'DIV', isContentEditable: true } })), false, 'a contenteditable is a text box')
  assert.equal(key(chord('f', { metaKey: true })), false, '⌘⌃⌥F is somebody else\'s')
  assert.equal(key(chord('f', { shiftKey: true })), false, 'and so is ⇧⌃⌥F')
  assert.equal(calls, 0, 'and none of that reached the window door')

  assert.equal(key(chord('d')), true, '⌃⌥D is ours')
  assert.equal(right.style.display, 'none', 'and it swaps the rail for the diagnostics drawer')
  assert.equal(findByClass(kit.root, 'jv-drawer').style.display, '', 'the pods are on screen')
  key(chord('d'))
  assert.equal(right.style.display, '', 'and ⌃⌥D again puts the rail back')

  key(chord('w'))
  await null; await null
  assert.equal(calls, 1, '⌃⌥W asks for the window')

  kit.overlay.destroy()
})

test('a BARE t / m / z / w / f / d does nothing at all (SPEC §8.1 ruling 1)', async () => {
  const env = install(true)
  let calls = 0
  const kit = overlayWithWindow(env, { openWindow: () => { calls += 1; return Promise.resolve({ ok: true }) } })
  const right = findByClass(kit.root, 'jv-layer jv-right') || findByClass(kit.root, 'jv-right')
  const drawer = findByClass(kit.root, 'jv-drawer')
  let fullscreens = 0
  env.doc.documentElement.requestFullscreen = () => { fullscreens += 1; return Promise.resolve() }

  const swallowed = []
  for (const letter of ['t', 'm', 'z', 'w', 'f', 'd']) {
    let stopped = false
    env.doc.fire('keydown', {
      target: { tagName: 'DIV' },
      preventDefault() { stopped = true }, stopPropagation() {}, ...bare(letter)
    })
    swallowed.push(stopped)
  }

  assert.deepEqual(swallowed, [false, false, false, false, false, false], 'not one bare letter is swallowed')
  assert.equal(calls, 0, 'no window was asked for')
  assert.equal(fullscreens, 0, 'no full screen was asked for')
  assert.notEqual(right.style.display, 'none', 'the rail is still the rail')
  assert.equal(drawer.style.display, 'none', 'and the drawer never opened')
  assert.equal(kit.overlay.isOpen(), true, 'and the dashboard is still standing')

  kit.overlay.destroy()
})

// ---- SPEC §8.2 rulings 4 and 5: the two lines on the glass -----------------

/** A presence stub that also answers the black box's two questions. */
function blackBoxStub(snapshot, end, preflight = '') {
  const kit = presenceStub(snapshot)
  kit.end = end
  kit.preflight = preflight
  kit.store.lastCallEnd = () => kit.end
  kit.store.callEndLine = () => (kit.end && kit.end.by === 'host' ? kit.line : '')
  kit.store.callPreflight = () => kit.preflight
  kit.line = ''
  return kit
}

const HOST_END = { at: 1, by: 'host', secondsOn: 63, why: 'link-blink', evidence: ['gateway open→closed 22:07:07'], toast: '', phrase: '' }

test('a host end puts ONE line under the orb, and a press takes it away', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const kit = blackBoxStub({ ...OFF }, null)
  const overlay = createOverlay({ presence: kit.store, data: dataStub, log: () => {} })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const underOrb = findByClass(root, 'jv-underorb')
  assert.equal(underOrb.textContent, '', 'nothing has ended yet')

  kit.end = HOST_END
  kit.line = 'Call ended by Hermes · the link to the mini blinked · ⌃⌥T to call again'
  await sleep(120); kit.push({ call: 'off' })
  assert.equal(underOrb.textContent,
    'Call ended by Hermes · the link to the mini blinked · ⌃⌥T to call again')
  assert.equal(underOrb.style.display, '', 'and it is on screen')

  // §8.2 ruling 4: "until the next press or chord".
  env.doc.fire('keydown', {
    target: { tagName: 'DIV' }, preventDefault() {}, stopPropagation() {}, ...chord('d')
  })
  assert.equal(underOrb.textContent, '', 'the chord spent the line')

  // Said ONCE: the same end never comes back.
  await sleep(120); kit.push({ call: 'off' })
  assert.equal(underOrb.textContent, '', 'one end, one telling')
  overlay.destroy()
})

test('a call Jarvis or Owner ended writes nothing under the orb', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const kit = blackBoxStub({ ...OFF }, { at: 2, by: 'user', secondsOn: 9, why: 'pressed', evidence: [], toast: '' })
  const overlay = createOverlay({ presence: kit.store, data: dataStub, log: () => {} })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  await sleep(120); kit.push({ call: 'off' })
  assert.equal(findByClass(root, 'jv-underorb').textContent, '', 'his own press is not a drop')
  overlay.destroy()
})

test('the amber pre-flight line rides in the VOICE CONTROL pod, and clears itself', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const kit = blackBoxStub({ ...OFF }, null,
    'The link reconnected at 22:07 · click this chat once before calling · the first job may hang up otherwise')
  const overlay = createOverlay({ presence: kit.store, data: dataStub, log: () => {} })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const warns = []
  const walk = node => {
    if (!node) return
    if (node.style && node.style.color === 'var(--jv-amber)') warns.push(node)
    const kids = node.childNodes || []
    for (let i = 0; i < kids.length; i += 1) walk(kids[i])
  }
  walk(root)
  assert.equal(warns.length, 1, 'one amber line, in the voice pod')
  assert.ok(findByClass(root, 'jv-voice'), 'and the voice pod is the pod it sits in')

  await sleep(120); kit.push({ call: 'off' })
  assert.match(warns[0].textContent, /^The link reconnected at 22:07 · click this chat once/)
  assert.doesNotMatch(warns[0].textContent, /reconnecting|fixed|healed/i, 'it warns; it never claims to have healed anything')

  kit.preflight = ''
  await sleep(120); kit.push({ call: 'off' })
  assert.equal(warns[0].textContent, '', 'the route was entered again')
  assert.equal(warns[0].style.display, 'none')
  overlay.destroy()
})

test('an older store with no black box at all still paints', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const kit = presenceStub({ ...OFF })          // no lastCallEnd, no callPreflight
  const overlay = createOverlay({ presence: kit.store, data: dataStub, log: () => {} })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  await sleep(120); kit.push({ call: 'on', mode: 'listening' })
  assert.equal(findByClass(root, 'jv-underorb').textContent, '')
  assert.equal(overlay.isOpen(), true, 'and nothing threw')
  overlay.destroy()
})

test('every key hint on the glass is the chord, never a bare letter', async () => {
  const env = install(true)
  const kit = overlayWithWindow(env, {})
  const hints = []
  const walk = node => {
    if (!node) return
    if (node.tagName === 'KBD') hints.push(String(node.textContent || ''))
    const kids = node.childNodes || []
    for (let i = 0; i < kids.length; i += 1) walk(kids[i])
  }
  walk(kit.root)

  assert.ok(hints.length >= 6, 'six keys, six hints at least')
  for (const hint of hints) {
    assert.match(hint, /^⌃⌥[TMZWFD]$/, 'a hint that is not a chord: ' + hint)
  }
  kit.overlay.destroy()
})

test('the first Esc leaves full screen and leaves the overlay standing', () => {
  const env = install(true)
  let exits = 0
  env.doc.fullscreenElement = env.doc.documentElement
  env.doc.exitFullscreen = () => { exits += 1; env.doc.fullscreenElement = null; return Promise.resolve() }
  const kit = overlayWithWindow(env, {})

  env.doc.fire('keydown', { key: 'Escape', target: { tagName: 'DIV' }, preventDefault() {}, stopPropagation() {} })
  assert.equal(exits, 1, 'Esc left full screen')
  assert.equal(kit.overlay.isOpen(), true, 'and did NOT close the dashboard')

  env.doc.fire('keydown', { key: 'Escape', target: { tagName: 'DIV' }, preventDefault() {}, stopPropagation() {} })
  assert.equal(kit.overlay.isOpen(), false, 'the second Esc, out of full screen, closes it')

  kit.overlay.destroy()
})

test('F asks the document for full screen, and a refusal is a line not a throw', async () => {
  const env = install(true)
  let asked = 0
  env.doc.documentElement.requestFullscreen = () => { asked += 1; return Promise.reject(new Error('denied')) }
  const kit = overlayWithWindow(env, {})

  env.doc.fire('keydown', {
    target: { tagName: 'DIV' }, preventDefault() {}, stopPropagation() {}, ...chord('f')
  })
  await null; await null
  assert.equal(asked, 1)
  assert.equal(kit.notice(), 'Full screen was refused by the window')
  assert.equal(kit.overlay.isOpen(), true, 'a refusal never takes the dashboard down with it')

  kit.overlay.destroy()
})

// ---- §7.2 ruling 2: the boot flag -----------------------------------------

const BOOT_KEY = pluginStorageKey('open-on-boot')

function rendered(env) {
  env.doc.body.appendChild(env.doc.createElement('div'))   // React has drawn
  return env
}

test('a fresh boot flag opens Jarvis mode once, consumes it, and starts no call', async () => {
  const env = rendered(install(true))
  env.win.localStorage.setItem(BOOT_KEY, String(Date.now()))

  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setTimeout(r, 700))

  const beat = JSON.parse(env.writes[env.writes.length - 1].content)
  assert.equal(beat.bootOpen, true, 'the receipt says this window was sent here')
  assert.equal(beat.overlay, 'open', 'and the overlay came up by itself')
  assert.equal(env.win.localStorage.getItem(BOOT_KEY), null, 'the flag is consumed, so only one window wins it')

  // A per-minute call is never started for you (§7.2 ruling 2).
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  assert.equal(labelOf(findByAttr(root, 'data-jv', 'talk')), 'START TALK',
    'the window opens showing START TALK — nothing was dialled')

  // A hot reload re-runs register(): the flag is gone, so nothing re-triggers.
  const again = fakeCtx()
  plugin.register(again.ctx)
  await new Promise(r => setTimeout(r, 700))
  assert.equal(JSON.parse(env.writes[env.writes.length - 1].content).bootOpen, false,
    'a hot reload never opens itself a second time')

  harness.disposers.forEach(fn => fn())
  again.disposers.forEach(fn => fn())
})

test('a stale boot flag is thrown away, not acted on', async () => {
  const env = rendered(install(true))
  env.win.localStorage.setItem(BOOT_KEY, String(Date.now() - 60000))   // a minute old

  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setTimeout(r, 300))

  const beat = JSON.parse(env.writes[env.writes.length - 1].content)
  assert.equal(beat.bootOpen, false, 'nobody is waiting on a flag that old')
  assert.equal(beat.overlay, 'closed')
  assert.equal(env.win.localStorage.getItem(BOOT_KEY), null, 'and it is cleared anyway, so it cannot fire later')

  harness.disposers.forEach(fn => fn())
})

test('a peer window writes its own receipt, so two windows never overwrite one', async () => {
  const env = rendered(install(true, '?peer=1'))
  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const paths = env.writes.map(w => w.path)
  assert.ok(paths.includes(pluginReceipt('desktop-heartbeat-peer')), 'the peer has its own file')
  assert.ok(!paths.includes(pluginReceipt('desktop-heartbeat')), 'and never writes the primary\'s')
  assert.equal(JSON.parse(env.writes[env.writes.length - 1].content).window, 'peer',
    'the host\'s own ?peer=1 marker is how the role is told')

  harness.disposers.forEach(fn => fn())
})

test('a window wearing an unknown ?win= flag says unknown rather than guessing', async () => {
  const env = rendered(install(true, '?win=secondary'))
  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const beat = JSON.parse(env.writes[env.writes.length - 1].content)
  assert.equal(beat.window, 'unknown')
  assert.equal(env.writes[env.writes.length - 1].path, pluginReceipt('desktop-heartbeat'),
    'an unknown role keeps today\'s receipt file')

  harness.disposers.forEach(fn => fn())
})

test('the palette row for the second window is the same press as W', async () => {
  const env = rendered(install(true))
  const plugin = loadPlugin()
  const harness = fakeCtx()
  plugin.register(harness.ctx)
  await new Promise(r => setImmediate(r))

  const row = harness.registered.find(c => c.id === 'jarvis-palette-window')
  assert.ok(row, 'the row is registered')
  assert.equal(row.data.label, 'Jarvis mode: open in its own window')
  assert.equal(row.data.id, 'jarvis.window', 'the id stays inside the jarvis. family')
  assert.doesNotThrow(() => row.data.run(), 'and pressing it with no bridge is a quiet no')

  harness.disposers.forEach(fn => fn())
})

// ---- §7.3 ruling 6: ONE mode word on the glass ----------------------------

/** The rail data with an activity slice the caller controls, so a test can
 *  hand the overlay a tool that is running (or not) and read the word. */
function overlayWithActivity(env, activity, mode = 'thinking') {
  const createOverlay = loadOverlay(env)
  const presence = presenceStub({ ...OFF, call: 'on', mode: mode })
  let frame = { ...RAIL_DATA, activity: activity }
  const listeners = new Set()
  const data = {
    get: () => frame,
    subscribe(fn) { listeners.add(fn); fn(frame); return () => listeners.delete(fn) }
  }
  const overlay = createOverlay({ presence: presence.store, data, log: () => {} })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  return {
    overlay, root, presence,
    push(next) { frame = { ...frame, activity: next }; listeners.forEach(fn => fn(frame)) },
    word: () => findByClass(root, 'jv-mode').textContent,
    voiceValue: () => textsOf(root, 'jv-pod-v').find(t => / · on$/.test(t)) || '',
    voiceNote: () => textsOf(root, 'jv-pod-n').find(t => /^source /.test(t)) || ''
  }
}

test('the display word, the VOICE reading and the scene all say the same mode', () => {
  const env = install(true)
  const live = { ...RUNNING, startedAt: Date.now() - 100000, lastEventAt: Date.now() - 4000 }
  const kit = overlayWithActivity(env, live)

  assert.equal(kit.word(), 'working',
    'a tool is running, so the big word says what the orb says — never `thinking` under a WORKING orb')
  assert.equal(kit.voiceValue(), 'working · on', 'the VOICE pod reads the same word')
  assert.match(kit.voiceNote(), /source mode thinking$/,
    'and the store\'s own reading survives here, named as the source reading')

  kit.overlay.destroy()
})

test('with no tool running the word is the store\'s own, and nothing is relabelled', () => {
  const env = install(true)
  const kit = overlayWithActivity(env, { ...RUNNING, tool: null, startedAt: Date.now() - 1000 })

  assert.equal(kit.word(), 'thinking', 'thinking is thinking')
  assert.equal(kit.voiceValue(), 'thinking · on')
  assert.ok(!/source mode/.test(kit.voiceNote()),
    'and with nothing derived there is no second reading to explain')

  kit.overlay.destroy()
})

test('a data frame alone flips the word — the presence snapshot never moved', () => {
  const env = install(true)
  const kit = overlayWithActivity(env, { ...RUNNING, tool: null, startedAt: Date.now() - 1000 })
  assert.equal(kit.word(), 'thinking')

  kit.push({ ...RUNNING, startedAt: Date.now() - 100000, lastEventAt: Date.now() - 4000 })
  assert.equal(kit.word(), 'working', 'the tool started, so the word followed it the same frame')
  assert.equal(kit.presence.store.get().mode, 'thinking', 'and the store was never written to')

  kit.push({ ...RUNNING, tool: null, startedAt: Date.now() - 1000 })
  assert.equal(kit.word(), 'thinking', 'the tool finished, and the word came back')

  kit.overlay.destroy()
})

// ---- §7.3: the housekeeping turn, and what line 3 never says --------------

test('a housekeeping turn keeps its label and never asks Owner for a yes', () => {
  const env = install(true)
  const kit = loadKit(env)

  const house = kit.jarvisNowLines({
    ...RUNNING,
    tool: { name: 'skill_view', label: 'housekeeping · opening a skill', detail: 'skill-library', startedAt: T0 - 4000 },
    needsYou: null
  }, T0)
  assert.equal(house.line, 'housekeeping · opening a skill',
    'the host\'s own review turn says so — it never wears Owner\'s request')
  assert.equal(house.needsYou, '', 'and it never raises the coral block')
  assert.match(house.underOrb, /^housekeeping · opening a skill · /,
    'the line under the orb carries the same label')
})

test('line 3 counts steps and seconds — never model calls', () => {
  const env = install(true)
  const kit = loadKit(env)

  const a = kit.jarvisNowLines({ ...RUNNING, modelCalls: 31, steps: 12 }, T0)
  assert.equal(a.meta, 'step 12 · 1 m 40 s · no news for 4 s')
  assert.ok(!/31/.test(a.meta), 'the model-call count is not a number this host can be trusted on')
  assert.ok(!/model/i.test(JSON.stringify(a)), 'and it is nowhere else in the box either')

  const idle = kit.jarvisNowLines({
    source: 'events', running: false, focused: true,
    lastTurn: { endedAt: T0 - 60000, seconds: 322, steps: 34, modelCalls: 31, outcome: 'done' }
  }, T0)
  assert.ok(!/31|model/i.test(idle.meta), 'the idle line does not print it either')
})

/** Every string literal in a file, with comments skipped — a small scanner
 *  rather than a regex, because the bundle carries both `hermes://jarvis` (a
 *  slash pair inside a string) and comments full of apostrophes. */
function stringLiterals(source) {
  const out = []
  let i = 0
  while (i < source.length) {
    const c = source[i]
    if (c === '/' && source[i + 1] === '/') { while (i < source.length && source[i] !== '\n') i += 1; continue }
    if (c === '/' && source[i + 1] === '*') { i = source.indexOf('*/', i + 2); i = i < 0 ? source.length : i + 2; continue }
    if (c === '\'' || c === '"' || c === '`') {
      const quote = c
      let j = i + 1
      let body = ''
      while (j < source.length) {
        if (source[j] === '\\') { body += source[j + 1] || ''; j += 2; continue }
        if (source[j] === quote) break
        if (quote !== '`' && source[j] === '\n') break      // an unterminated quote: not a literal
        body += source[j]
        j += 1
      }
      out.push(body)
      i = j + 1
      continue
    }
    i += 1
  }
  return out
}

test('no user-facing string in the built bundle ever says "stuck"', () => {
  const bundle = fs.readFileSync(BUILT, 'utf8')
  // §7.3 ruling 3 is about what Owner READS. The comments that explain the
  // ruling may name the word they ban; nothing that can reach the glass may.
  const literals = stringLiterals(bundle)
  const guilty = literals.filter(s => /stuck/i.test(s))
  assert.deepEqual(guilty, [], 'the box prints facts; the verdict is Owner\'s')
  assert.ok(literals.length > 500, 'and the scan actually found the strings')
  assert.ok(literals.some(s => s === 'no news for '), 'including the one that replaced it')
})

// ---- §7.3 ruling 5: the once-a-second half of the NOW box -----------------

test('the NOW box re-reads the clock once a second, and stops when idle or closed', () => {
  const env = install(true)
  const realSet = globalThis.setInterval
  const realClear = globalThis.clearInterval
  const timers = []
  globalThis.setInterval = (fn, ms) => { timers.push({ fn, ms, dead: false }); return timers.length }
  globalThis.clearInterval = id => { if (timers[id - 1]) timers[id - 1].dead = true }

  try {
    const live = { ...RUNNING, startedAt: Date.now() - 100000, lastEventAt: Date.now() - 4000 }
    const kit = overlayWithActivity(env, live)
    const tick = timers.find(t => t.ms === 1000)
    assert.ok(tick, 'the overlay runs exactly one one-second timer while it is open')

    const meta = () => textsOf(kit.root, 'jv-now-meta')[0]
    assert.match(meta(), /^step 12 · /)

    // the SAME object the overlay is holding: a tick that re-reads it repaints
    live.steps = 99
    tick.fn()
    assert.match(meta(), /^step 99 · /, 'a second later the elapsed line is re-read')

    // idle: the tick must do nothing at all rather than re-render the glass
    live.running = false
    live.steps = 500
    tick.fn()
    assert.match(meta(), /^step 99 · /, 'with no turn running the second does not cost a repaint')

    kit.overlay.close()
    assert.equal(tick.dead, true, 'and a closed overlay leaves no timer behind')
    kit.overlay.destroy()
  } finally {
    globalThis.setInterval = realSet
    globalThis.clearInterval = realClear
  }
})

// ---- §7.4: the two STATE boxes share the rail's rows ----------------------

const MANY_ROWS = {
  status: 'ok', updatedAt: T0 - 600000, closedCount: 0, note: null,
  rows: [0, 1, 2, 3, 4, 5].map(i => ({
    id: 'demo-ask-' + i, where: 'x', next: 'Owner decides sample item ' + i, owner: 'Owner',
    follow_up_at: new Date(T0 + i * 3600000).toISOString(), waiting_on_owner: true, overdue: false
  })).concat([0, 1, 2, 3, 4].map(i => ({
    id: 'demo-flight-' + i, where: 'x', next: 'Agent keeps going on sample item ' + i, owner: 'Agent',
    follow_up_at: new Date(T0 + (i + 1) * 86400000).toISOString(), waiting_on_owner: false, overdue: false
  })))
}

test('a rail full of asks counts the rest out loud instead of clipping a row', () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF)
  const data = { get: () => ({ ...RAIL_DATA, agentState: MANY_ROWS }), subscribe: () => () => {} }
  const overlay = createOverlay({ presence: presence.store, data, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const rows = textsOf(root, 'jv-srow-t')
  const more = textsOf(root, 'jv-more')
  // A 900 px window, carrying §8.4's seven boxes at §8 amendments C10's 11 px
  // type: two asks — one of them open, with its brief — and NOTHING left for
  // AGENT IN FLIGHT, which is this rail's declared give-way. Not one row is
  // clipped: every row neither box could draw is counted out loud.
  assert.equal(rows.filter(t => /Owner decides/.test(t)).length, 2, 'WAITING ON YOU is served first')
  assert.equal(rows.filter(t => /Agent keeps going/.test(t)).length, 0, 'IN FLIGHT gives way whole')
  assert.equal(more.filter(t => t === '+4 more').length, 1, 'the four asks that did not fit are counted')
  assert.equal(more.filter(t => t === '+5 more').length, 1, 'and so are all five in-flight rows')

  overlay.destroy()
})

test('an empty STATE file says nothing is waiting — it does not read unreachable', () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const presence = presenceStub(OFF)
  const empty = { status: 'ok', rows: [], closedCount: 6, updatedAt: T0, note: null }
  const data = { get: () => ({ ...RAIL_DATA, agentState: empty }), subscribe: () => () => {} }
  const overlay = createOverlay({ presence: presence.store, data, log: () => {} })
  overlay.open()

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  const empties = textsOf(root, 'jv-empty')
  assert.ok(empties.includes('nothing is waiting on you'), 'an empty file is good news, and reads like it')
  assert.ok(empties.includes('nothing else is in flight'))
  assert.equal(empties.includes("Agent's STATE unreachable"), false, 'an empty file is not a missing one')

  overlay.destroy()
})

// ---- the main computer may be a Windows PC (V1 scope ruling, 2026-09-22) ----
//
// Same chord, same handler, different spelling on the glass. The keydown below
// carries `key: 'm'` — no dead-key rewrite, because Windows has none — which is
// the proof that the handler reads `event.code` and not the letter.

test('on a Windows main computer every key hint reads Ctrl+Alt, and the chord still fires', async () => {
  const env = install(true)
  env.win.navigator = { userAgentData: { platform: 'Windows' }, platform: 'Win32' }
  const kit = overlayWithWindow(env, { presence: { ...OFF, call: 'on', mode: 'listening' } })

  const hints = []
  const walk = node => {
    if (!node) return
    if (node.tagName === 'KBD') hints.push(String(node.textContent || ''))
    const kids = node.childNodes || []
    for (let i = 0; i < kids.length; i += 1) walk(kids[i])
  }
  walk(kit.root)

  assert.ok(hints.length >= 6, 'six keys, six hints at least')
  for (const hint of hints) {
    assert.match(hint, /^Ctrl\+Alt\+[TMZWFD]$/, 'a hint a Windows member cannot type: ' + hint)
  }

  const mute = findByAttr(kit.root, 'data-jv', 'mute')
  assert.equal(mute.attributes.title, 'mute  (Ctrl+Alt+M)', 'and the tooltip spells it the same way')

  env.doc.fire('keydown', {
    target: { tagName: 'DIV' },
    preventDefault() {}, stopPropagation() {},
    key: 'm', code: 'KeyM', ctrlKey: true, altKey: true, metaKey: false, shiftKey: false
  })
  assert.deepEqual(kit.presence.asked, ['mute'], 'Ctrl+Alt+M reaches the same voice door')

  kit.overlay.destroy()
})

test('a Mac main computer is still the default, and so is a host that will not say', async () => {
  for (const nav of [{ userAgentData: { platform: 'macOS' }, platform: 'MacIntel' }, undefined]) {
    const env = install(true)
    if (nav) env.win.navigator = nav
    const kit = overlayWithWindow(env, {})
    const talk = findByAttr(kit.root, 'data-jv', 'talk')
    const hint = findByAttr(kit.root, 'data-jv', 'talk').childNodes.find(n => n.tagName === 'KBD')
    assert.equal(hint.textContent, '⌃⌥T', 'the glyphs stay on: ' + JSON.stringify(nav || null))
    assert.match(talk.attributes.title, /\(⌃⌥T\)$/)
    kit.overlay.destroy()
  }
})

// ---- no voice door at all (V1: the face degrades honestly) -----------------
//
// A Hermes with neither the built-in round voice button nor the Talk presence
// bus gives the store nothing to command with. The face is still the face: it
// opens, it paints, the buttons are greyed, and every one of them says the same
// honest sentence instead of offering a press that lands nowhere.

const DOORLESS = {
  get: () => ({ ...OFF }),
  subscribe: () => () => {},
  isDemo: () => false
  // no command(), no canCommand(), no waitBudgetMs() — nothing to call
}

test('with no voice door at all the overlay still opens and says so, rather than throwing', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const overlay = createOverlay({ presence: DOORLESS, data: dataStub, log: () => {} })

  overlay.open()
  assert.equal(overlay.isOpen(), true, 'the face opened')

  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  assert.ok(findByClass(root, 'jv-voice'), 'the voice row is on the glass')
  assert.ok(findByClass(root, 'jv-scene') || root.childNodes.length > 0, 'and so is the rest of it')

  for (const seat of ['talk', 'mute', 'sleep']) {
    const btn = findByAttr(root, 'data-jv', seat)
    assert.ok(btn, seat + ' has a button')
    assert.equal(btn.disabled, true, seat + ' is greyed')
    assert.equal(btn.attributes.title, 'this build has no voice command door',
      seat + ' says why, in the honest words')
  }

  // Pressing one anyway — by mouse and by chord — prints the line; it does not
  // throw, and it does not take the face down with it.
  findByAttr(root, 'data-jv', 'talk').click()
  await null; await null
  assert.equal(findByClass(root, 'jv-cmdmsg').textContent, 'this build has no voice command door')

  env.doc.fire('keydown', {
    target: { tagName: 'DIV' },
    preventDefault() {}, stopPropagation() {},
    key: '†', code: 'KeyT', ctrlKey: true, altKey: true, metaKey: false, shiftKey: false
  })
  assert.equal(overlay.isOpen(), true, 'still standing after the chord too')
  assert.equal(findByClass(root, 'jv-cmdmsg').textContent, 'this build has no voice command door')

  await sleep(120)
  assert.equal(overlay.isOpen(), true, 'and still standing a paint tick later')
  overlay.destroy()
})

test('a doorless build still paints the rest of the face on every tick', async () => {
  const env = install(true)
  const createOverlay = loadOverlay(env)
  const overlay = createOverlay({
    presence: DOORLESS,
    data: { get: () => RAIL_DATA, subscribe: () => () => {} },
    log: () => {},
    getScope: () => ({ id: 'test-scope', connectionId: 'local', routeProfile: 'default', profileId: 'default' })
  })
  overlay.open()
  const root = env.doc.body.childNodes[env.doc.body.childNodes.length - 1]
  await sleep(150)
  assert.equal(overlay.isOpen(), true)
  assert.ok(findByClass(root, 'jv-voice'), 'the voice row survived the repaint')
  overlay.destroy()
})
