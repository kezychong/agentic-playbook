// tests/mirror.test.mjs — node --test tests/mirror.test.mjs
//
// Loads src/45-mirror.js into a stub page (same shape of fake window/document as
// plugin-smoke.test.mjs) and proves the WebSocket ticket flow: the host's socket
// auth never reads cookies, so the page must POST /api/auth/ws-ticket before
// every connect and spend that single-use ticket in the query string.
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const SRC = fileURLToPath(new URL('../src/45-mirror.js', import.meta.url))
const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const EVENTS = 'wss://mini:9119/api/plugins/hermes-jarvis/events'
const tick = () => new Promise(r => setImmediate(r))

function domNode(tag) {
  return {
    tagName: String(tag).toUpperCase(), _text: '', innerHTML: '', children: [],
    style: { cssText: '' },
    get textContent() { return this._text },
    set textContent(v) { this._text = String(v) },
    appendChild(c) { this.children.push(c); return c },
    removeChild(c) { this.children = this.children.filter(x => x !== c) },
    addEventListener() {}, removeEventListener() {},
    clientWidth: 1440, clientHeight: 900
  }
}

// Mount one mirror on a stub page. `reply(n)` answers the n-th ticket POST;
// timers are queued and only run when the test says so, so nothing leaks.
function mount(reply, opts) {
  const timers = []
  const env = {
    mints: [], sockets: [], listeners: new Map(), parentMessages: [],
    fire() { timers.splice(0).forEach(t => t.fn()) },
    stamp: () => env.doc.body.children[1].textContent
  }
  class FakeSocket {
    constructor(url) { this.url = url; env.sockets.push(this) }
    close() { this.closed = true }
  }
  const parentWindow = { postMessage(body, target) { env.parentMessages.push({ body, target }) } }
  const win = {
    devicePixelRatio: 2, innerWidth: 1440, innerHeight: 900,
    parent: opts && opts.parentWsBridge ? parentWindow : null,
    addEventListener(type, fn) { env.listeners.set(type, fn) },
    removeEventListener(type, fn) { if (env.listeners.get(type) === fn) env.listeners.delete(type) }
  }
  if (!win.parent) win.parent = win
  env.parentWindow = parentWindow
  env.doc = { body: domNode('body'), documentElement: domNode('html'), createElement: domNode }
  const scene = {
    data: [], presence: [], setSize() {}, start() {}, stop() {}, destroy() {},
    setPresence(value) { this.presence.push(value) }, setData(value) { this.data.push(value) }
  }
  env.scene = scene
  const fetchStub = (url, init) => { env.mints.push({ url, init }); return reply(env.mints.length) }
  const setT = fn => { const t = { fn }; timers.push(t); return t }
  const clearT = t => { const i = timers.indexOf(t); if (i >= 0) timers.splice(i, 1) }
  const start = new Function(
    'window', 'document', 'location', 'getComputedStyle', 'WebSocket', 'fetch', 'createScene',
    'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval',
    fs.readFileSync(SCOPE_SRC, 'utf8') + '\n' + fs.readFileSync(SRC, 'utf8') + '\nreturn startJarvisMirror'
  )(win, env.doc, { protocol: 'https:', host: 'mini:9119' }, () => ({ position: 'relative' }),
    FakeSocket, fetchStub, () => scene, setT, clearT, setT, clearT)
  env.mirror = start(null, { profileId: 'chief', ...(opts || {}) })
  return env
}

const minted = n => Promise.resolve({ ok: true, status: 200, json: async () => ({ ticket: 't-' + n, ttl_seconds: 30 }) })
const denied = () => Promise.resolve({ ok: false, status: 401, json: async () => ({ detail: 'no session' }) })

test('a ticket is minted before the socket, and rides in the url', async () => {
  const env = mount(minted)
  await tick()

  assert.equal(env.mints.length, 1, 'the first connect minted exactly one ticket')
  const mint = env.mints[0]
  assert.equal(mint.url, 'https://mini:9119/api/auth/ws-ticket', 'same origin as the socket')
  assert.equal(mint.init.method, 'POST')
  assert.equal(mint.init.credentials, 'same-origin', 'the session cookie rides along')
  assert.equal(mint.init.headers['Content-Type'], 'application/json')
  assert.equal(mint.init.body, '{}')

  assert.equal(env.sockets.length, 1, 'one socket, opened after the mint')
  assert.equal(env.sockets[0].url, EVENTS + '?ticket=t-1')

  env.mirror.stop()
})

test('a url override mints from that same origin', async () => {
  const env = mount(minted, { url: 'wss://other.host:9119/api/plugins/hermes-jarvis/events' })
  await tick()
  assert.equal(env.mints[0].url, 'https://other.host:9119/api/auth/ws-ticket')
  assert.equal(env.sockets[0].url, 'wss://other.host:9119/api/plugins/hermes-jarvis/events?ticket=t-1')
  env.mirror.stop()
})

test('a 401 mint shows the signed-out state and opens no socket', async () => {
  const env = mount(denied)
  await tick()

  assert.equal(env.sockets.length, 0, 'no ticket, no socket')
  assert.match(env.stamp(), /SIGNED OUT/, 'the page says so instead of faking a reading')
  assert.match(env.stamp(), /SIGN IN/i)

  env.mirror.stop()
})

test('a mint that cannot be reached shows unreachable and retries', async () => {
  const env = mount(n => (n === 1 ? Promise.reject(new Error('network down')) : minted(n)))
  await tick()
  assert.equal(env.sockets.length, 0)
  assert.match(env.stamp(), /UNREACHABLE/)

  env.fire()                                  // the backoff timer comes due
  await tick()
  assert.equal(env.mints.length, 2, 'the retry minted again')
  assert.equal(env.sockets[0].url, EVENTS + '?ticket=t-2')

  env.mirror.stop()
})

test('every reconnect mints a fresh ticket', async () => {
  const env = mount(minted)
  await tick()
  env.sockets[0].onclose()                    // the host dropped the socket
  env.fire()
  await tick()

  assert.equal(env.mints.length, 2, 'the reconnect minted again')
  assert.equal(env.sockets.length, 2)
  assert.equal(env.sockets[1].url, EVENTS + '?ticket=t-2', 'a single-use ticket is never reused')

  env.mirror.stop()
  env.fire()
  await tick()
  assert.equal(env.mints.length, 2, 'stop() leaves no timer minting behind it')
})

test('an authenticated web parent supplies a fresh socket URL without exposing HTTP credentials', async () => {
  const env = mount(minted, { parentWsBridge: true, bridgeId: 'bridge-1' })
  assert.equal(env.mints.length, 0, 'the embedded page does not bypass the web SDK with raw HTTP')
  assert.equal(env.parentMessages.length, 1)
  const request = env.parentMessages[0].body
  assert.equal(request.type, 'hermes-jarvis:ws-url-request')
  env.listeners.get('message')({
    source: env.parentWindow,
    data: {
      type: 'hermes-jarvis:ws-url-response', bridgeId: 'bridge-1', requestId: request.requestId,
      url: EVENTS + '?ticket=web-1'
    }
  })
  await tick()
  assert.equal(env.sockets[0].url, EVENTS + '?ticket=web-1')
  env.mirror.stop()
  assert.equal(env.listeners.has('message'), false)
})

test('the mirror accepts frames only after the canonical profile binds', async () => {
  const env = mount(minted, { profileId: 'chief' })
  await tick()
  const socket = env.sockets[0]
  socket.onopen()
  socket.onmessage({ data: JSON.stringify({ type: 'presence', data: { mode: 'speaking', private: 'old' } }) })
  assert.equal(env.scene.presence.length, 0, 'presence before a verified state is ignored')

  const good = {
    schema_version: 1, profile_id: 'chief', agent_name: 'Sample Agent', owner_label: 'Sample Owner',
    timezone: 'UTC', enabled_sources: [], brains: []
  }
  socket.onmessage({ data: JSON.stringify({ type: 'state', data: { settings: good, brains: [] } }) })
  socket.onmessage({ data: JSON.stringify({ type: 'presence', data: { mode: 'listening' } }) })
  assert.equal(env.scene.presence.at(-1).mode, 'listening')

  socket.onmessage({ data: JSON.stringify({ type: 'state', data: { settings: { ...good, profile_id: 'other' }, brains: [{ id: 'private', label: 'Private' }] } }) })
  assert.match(env.stamp(), /CONNECT TO THIS CHIEF PROFILE DASHBOARD/)
  assert.deepEqual(env.scene.data.at(-1).brains, [], 'mismatch clears the previous private scene data')
  assert.equal(env.scene.presence.at(-1).mode, 'idle', 'mismatch also clears the previous presence')
  env.mirror.stop()
})
