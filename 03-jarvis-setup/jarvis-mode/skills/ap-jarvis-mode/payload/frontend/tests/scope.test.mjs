import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const SCOPE = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const DATA = fileURLToPath(new URL('../src/30-data.js', import.meta.url))
const source = fs.readFileSync(SCOPE, 'utf8') + '\n' + fs.readFileSync(DATA, 'utf8')
const M = new Function('window', 'document', source + `
return { jarvisScope, jarvisScopedKey, jarvisValidateSettings, jarvisSourceEnabled, jarvisTargetProfile, jarvisSelectedOwner, createDataFeed,
         jarvisKeyLabels, jarvisKeyLabelsFor, jarvisIsWindowsPlatform, jarvisPlatformName };
`)(undefined, undefined)

const allSources = [
  'agent_state', 'agent_helpers', 'next_meeting', 'today_plan', 'overnight_jobs',
  'one_thing_scoreboard', 'spend', 'lever', 'brains', 'scoreboard', 'log'
]

function settings(profile, sources = allSources, extra = {}) {
  return {
    schema_version: 1,
    profile_id: profile,
    agent_name: 'Sample Agent',
    owner_label: 'Sample Owner',
    timezone: 'America/New_York',
    enabled_sources: sources,
    brains: [{ id: 'sample-brain', label: 'Sample Brain' }],
    ...extra
  }
}

function atom(initial) {
  let value = initial
  const listeners = new Set()
  return {
    get: () => value,
    listen(fn) { listeners.add(fn); return () => listeners.delete(fn) },
    set(next) { value = next; listeners.forEach(fn => fn(next)) }
  }
}

function harness(answer, profile = 'chief') {
  const connectionId = atom('sample-connection')
  const routeProfile = atom(profile)
  const calls = []
  const requests = []
  const ctx = {
    rest(path, opts) {
      calls.push({ path, opts })
      if (path === '/state') return answer(path, opts)
      if (path === '/panel') return Promise.resolve(null)
      if (path === '/presence') return Promise.resolve({ ok: true })
      return Promise.reject(new Error('unexpected route'))
    }
  }
  const host = {
    state: { connectionId, profile: routeProfile },
    profileRoutes: () => Promise.resolve([
      { connectionId: 'sample-connection', profile: 'chief', targetProfile: 'chief-backend' },
      { connectionId: 'sample-connection', profile: 'second', targetProfile: 'second-backend' }
    ]),
    request(method, params) { requests.push({ method, params }); return Promise.resolve({}) }
  }
  const feed = M.createDataFeed({ ctx, HermesSDK: { host }, log: () => {}, now: () => 1_800_000_000_000 })
  return { feed, calls, requests, connectionId, routeProfile }
}

test('connection and canonical profile both namespace browser state', () => {
  const a = M.jarvisScope('connection-a', 'chief', 'backend-chief')
  const b = M.jarvisScope('connection-b', 'chief', 'backend-chief')
  const c = M.jarvisScope('connection-a', 'chief', 'other-chief')
  assert.notEqual(M.jarvisScopedKey(a, 'presence'), M.jarvisScopedKey(b, 'presence'))
  assert.notEqual(M.jarvisScopedKey(a, 'presence'), M.jarvisScopedKey(c, 'presence'))
  assert.equal(M.jarvisScopedKey(null, 'presence'), null, 'no verified scope means no storage key')
})

test('settings bind to route.targetProfile, not the local route alias', () => {
  assert.equal(M.jarvisValidateSettings(settings('chief-backend'), 'chief-backend').ok, true)
  const mismatch = M.jarvisValidateSettings(settings('chief'), 'chief-backend')
  assert.equal(mismatch.ok, false)
  assert.match(mismatch.reason, /connect to this chief profile dashboard/)
  assert.equal(M.jarvisValidateSettings({ ...settings('chief-backend'), schema_version: true }, 'chief-backend').ok, false)
  assert.equal(M.jarvisValidateSettings(settings('chief-backend', allSources, { enabled_boxes: ['fleet', 'fleet'] }), 'chief-backend').ok, false)
  assert.equal(M.jarvisValidateSettings(settings('chief-backend', allSources, { enabled_boxes: ['unknown-box'] }), 'chief-backend').ok, false)
  assert.equal(M.jarvisValidateSettings(settings('chief-backend', allSources, { enabled_boxes: null }), 'chief-backend').ok, false)
})

test('an alias with no registered canonical route fails closed', async () => {
  const target = await M.jarvisTargetProfile({ profileRoutes: () => Promise.resolve([]) }, 'sample-connection', 'chief')
  assert.equal(target, '')
})

test('a mismatched state clears the last profile and blocks presence', async () => {
  let payload = { settings: settings('chief-backend'), lever: { text: 'Sample private lever' } }
  const env = harness(() => Promise.resolve(payload))
  await env.feed.refresh('state')
  assert.equal(env.feed.get().settings.profile_id, 'chief-backend')
  assert.equal(env.feed.get().lever.text, 'Sample private lever')

  payload = { settings: settings('different-backend'), lever: { text: 'Must not land' } }
  await env.feed.refresh('state')
  assert.equal(env.feed.get().settings, null)
  assert.equal(env.feed.get().lever, null)
  assert.match(env.feed.get().connection.note, /connect to this chief profile dashboard/)
  assert.equal(await env.feed.pushPresence({ mode: 'listening' }), false)
  assert.equal(env.calls.filter(row => row.path === '/presence').length, 0)
})

test('a state response from the previous selection is discarded', async () => {
  let resolveFirst
  let count = 0
  const env = harness(() => {
    count += 1
    if (count === 1) return new Promise(resolve => { resolveFirst = resolve })
    return Promise.resolve({ settings: settings('second-backend'), lever: { text: 'Second selection' } })
  })
  env.feed.start()
  await new Promise(resolve => setImmediate(resolve))
  assert.equal(typeof resolveFirst, 'function')
  env.routeProfile.set('second')
  const second = env.feed.refresh('state')
  await second
  resolveFirst({ settings: settings('chief-backend'), lever: { text: 'Old selection' } })
  await Promise.resolve()
  assert.equal(env.feed.get().settings.profile_id, 'second-backend')
  assert.equal(env.feed.get().lever.text, 'Second selection')
  env.feed.stop()
})

test('disabled boxes do not launch fleet or brain host reads', async () => {
  const enabled = ['agent_state', 'lever']
  const env = harness(() => Promise.resolve({
    settings: settings('chief-backend', enabled, { enabled_boxes: ['waiting_on_you'] }),
    agent_state: { status: 'ok', rows: [] },
    lever: { text: 'One sample thing' }
  }))
  await env.feed.refresh('state')
  assert.equal(env.feed.get().brains.length, 0)
  assert.equal(M.jarvisSourceEnabled(env.feed.get().settings, 'brains'), false)
  assert.deepEqual(env.requests, [], 'no profiles, sessions, cron, or MCP request was launched')
})

test('configured timezone handles a daylight-saving boundary', () => {
  const before = Date.parse('2026-11-01T05:30:00Z')
  const after = Date.parse('2026-11-01T07:30:00Z')
  const checked = M.jarvisValidateSettings(settings('chief-backend'), 'chief-backend')
  assert.equal(checked.ok, true)
  assert.equal(checked.settings.timezone, 'America/New_York')
  const day = new Intl.DateTimeFormat('en-CA', { timeZone: checked.settings.timezone, year: 'numeric', month: '2-digit', day: '2-digit' })
  assert.equal(day.format(new Date(before)), day.format(new Date(after)), 'the repeated DST hour stays on the same configured day')
})

test('the supported local pool keeps connectionId null in scope and REST routing', async () => {
  const calls = []
  const host = {
    state: { connectionId: atom(null), profile: atom('default') },
    profileRoutes: async () => [{ connectionId: 'local', mode: 'local', profile: 'default', targetProfile: 'default' }],
    request: async () => ({})
  }
  const ctx = { rest: async (path, opts) => {
    calls.push({ path, opts })
    if (path === '/state') return { settings: settings('default', ['agent_state'], { enabled_boxes: ['waiting_on_you'] }) }
    return null
  } }
  const feed = M.createDataFeed({ ctx, HermesSDK: { host }, log: () => {}, now: () => 1_800_000_000_000 })
  await feed.refresh('state')
  assert.equal(feed.get().settings.profile_id, 'default')
  assert.equal(calls[0].opts.scope.connectionId, null)
  assert.equal(calls[0].opts.scope.profile, 'default')
  const local = M.jarvisScope(null, 'default', 'default')
  assert.equal(local.connectionId, null)
  assert.notEqual(local.id, M.jarvisScope('null', 'default', 'default').id)
})

test('the nullable local pool refuses remote and ambiguous local registry rows', async () => {
  const remoteOnly = await M.jarvisTargetProfile({ profileRoutes: async () => [
    { connectionId: 'remote-a', mode: 'remote', profile: 'default', targetProfile: 'default' }
  ] }, null, 'default')
  assert.equal(remoteOnly, '')

  const ambiguous = await M.jarvisTargetProfile({ profileRoutes: async () => [
    { connectionId: 'local-a', mode: 'local', profile: 'default', targetProfile: 'default' },
    { connectionId: 'local-b', mode: 'local', profile: 'default', targetProfile: 'other-default' }
  ] }, null, 'default')
  assert.equal(ambiguous, '')
})

test('focusedSessionOwner supplies one connection-qualified tuple to REST and optional RPC reads', async () => {
  const restCalls = []
  const rpcCalls = []
  const host = {
    state: {
      connectionId: atom('active-connection'), profile: atom('active-profile'),
      focusedSessionOwner: atom({ connectionId: 'focused-connection', profile: 'focused-profile' })
    },
    profileRoutes: async () => [{ connectionId: 'focused-connection', profile: 'focused-profile', targetProfile: 'focused-backend' }],
    requestProfile: async (route, method) => { rpcCalls.push({ route, method }); return {} }
  }
  const ctx = { rest: async (path, opts) => {
    restCalls.push({ path, opts })
    return { settings: settings('focused-backend', ['brains'], { enabled_boxes: [] }) }
  } }
  const feed = M.createDataFeed({ ctx, HermesSDK: { host }, log: () => {}, now: () => 1_800_000_000_000 })
  await feed.refresh('state')
  await new Promise(resolve => setImmediate(resolve))
  assert.deepEqual(restCalls[0].opts.scope, { connectionId: 'focused-connection', profile: 'focused-profile' })
  assert.equal(rpcCalls[0].route.connectionId, 'focused-connection')
  assert.equal(rpcCalls[0].route.profile, 'focused-profile')
})

test('profile switch retires the old socket before any old panel frame can land', async () => {
  const connectionId = atom('sample-connection')
  const profile = atom('chief')
  const socketRows = []
  const host = {
    state: { connectionId, profile },
    profileRoutes: async () => [
      { connectionId: 'sample-connection', profile: 'chief', targetProfile: 'chief-backend' },
      { connectionId: 'sample-connection', profile: 'second', targetProfile: 'second-backend' }
    ],
    request: async () => ({})
  }
  const ctx = {
    rest: async path => path === '/state'
      ? { settings: settings(profile.get() === 'chief' ? 'chief-backend' : 'second-backend', ['agent_state'], { enabled_boxes: ['waiting_on_you'] }) }
      : null,
    socket(path, callback) {
      const row = { path, callback, closed: false }
      socketRows.push(row)
      return () => { row.closed = true }
    },
    onEvent() {}
  }
  const feed = M.createDataFeed({ ctx, HermesSDK: { host }, log: () => {}, now: () => 1_800_000_000_000 })
  feed.start()
  await new Promise(resolve => setImmediate(resolve)); await new Promise(resolve => setImmediate(resolve))
  assert.equal(socketRows.length, 1)
  const old = socketRows[0]
  profile.set('second')
  await feed.refresh('state')
  assert.equal(old.closed, true)
  assert.equal(socketRows.length, 2)
  old.callback({ type: 'panel', data: { id: 'old', title: 'Old private card', body: 'old', at: 1_800_000_000_000 } })
  assert.equal(feed.get().panel, null)
  feed.stop()
})

test('late optional profile readers cannot write into a newer profile', async () => {
  const connectionId = atom('sample-connection')
  const profile = atom('chief')
  let resolveOld
  const host = {
    state: { connectionId, profile },
    profileRoutes: async () => [
      { connectionId: 'sample-connection', profile: 'chief', targetProfile: 'chief-backend' },
      { connectionId: 'sample-connection', profile: 'second', targetProfile: 'second-backend' }
    ],
    requestProfile(route, method) {
      if (route.profile === 'chief' && method === 'profiles.describe') return new Promise(resolve => { resolveOld = resolve })
      return Promise.resolve(method === 'profiles.describe' ? { mcp_servers: [] } : null)
    }
  }
  const ctx = { rest: async path => path === '/state'
    ? { settings: settings(profile.get() === 'chief' ? 'chief-backend' : 'second-backend', ['brains'], { enabled_boxes: [] }) }
    : null }
  const feed = M.createDataFeed({ ctx, HermesSDK: { host }, log: () => {}, now: () => 1_800_000_000_000 })
  feed.start()
  await new Promise(resolve => setImmediate(resolve)); await new Promise(resolve => setImmediate(resolve))
  assert.equal(typeof resolveOld, 'function')
  profile.set('second')
  await feed.refresh('state')
  resolveOld({ mcp_servers: [{ name: 'private-old-source', enabled: true }] })
  await new Promise(resolve => setImmediate(resolve))
  assert.equal(feed.get().settings.profile_id, 'second-backend')
  assert.deepEqual(feed.get().senses, [])
  feed.stop()
})

test('within one route only the newest state request may change settings', async () => {
  let resolveOld
  let count = 0
  const env = harness(() => {
    count += 1
    if (count === 1) return new Promise(resolve => { resolveOld = resolve })
    return Promise.resolve({ settings: settings('chief-backend', ['today_plan'], { enabled_boxes: [] }) })
  })
  const old = env.feed.refresh('state')
  await new Promise(resolve => setImmediate(resolve))
  await env.feed.refresh('state')
  resolveOld({ settings: settings('chief-backend', ['today_plan'], { enabled_boxes: ['today'] }) })
  await old
  assert.deepEqual(env.feed.get().settings.enabled_boxes, [])
})

/* ------------------------------------------------- the chord labels (V1) --
 * The main computer is a Mac OR a Windows PC, so the same chord is printed two
 * ways: ⌃⌥T on a Mac, Ctrl+Alt+T on Windows. The chord itself never changes —
 * Control and Alt/Option are the same two physical keys on both — so this is a
 * LABEL chooser and nothing else. An unreadable platform keeps the Mac glyphs,
 * which is what Hermes Desktop itself prints.
 */

const MAC_LABELS = { talk: '⌃⌥T', mute: '⌃⌥M', sleep: '⌃⌥Z', window: '⌃⌥W', full: '⌃⌥F', drawer: '⌃⌥D', open: '⌘⌥J' }
const WIN_LABELS = {
  talk: 'Ctrl+Alt+T', mute: 'Ctrl+Alt+M', sleep: 'Ctrl+Alt+Z',
  window: 'Ctrl+Alt+W', full: 'Ctrl+Alt+F', drawer: 'Ctrl+Alt+D', open: 'Ctrl+Alt+J'
}

const labelsOf = set => Object.fromEntries(Object.keys(MAC_LABELS).map(k => [k, set[k]]))

test('a Windows platform prints Ctrl+Alt, a Mac prints the glyphs', () => {
  for (const name of ['Windows', 'Win32', 'Win64', 'win32', '  Windows  ']) {
    assert.deepEqual(labelsOf(M.jarvisKeyLabels(name)), WIN_LABELS, name + ' is a Windows PC')
    assert.equal(M.jarvisIsWindowsPlatform(name), true)
  }
  for (const name of ['macOS', 'MacIntel', 'iPhone']) {
    assert.deepEqual(labelsOf(M.jarvisKeyLabels(name)), MAC_LABELS, name + ' keeps the glyphs')
    assert.equal(M.jarvisIsWindowsPlatform(name), false)
  }
})

test('an unreadable platform keeps the Mac glyphs rather than guessing', () => {
  for (const name of ['', '   ', null, undefined, 0, {}, [], 'Linux x86_64']) {
    assert.deepEqual(labelsOf(M.jarvisKeyLabels(name)), MAC_LABELS,
      'no honest Windows answer: ' + String(name))
  }
})

test('the chord is the same two keys on both computers — only the spelling moves', () => {
  for (const seat of ['talk', 'mute', 'sleep', 'window', 'full', 'drawer']) {
    assert.equal(WIN_LABELS[seat].slice(-1), MAC_LABELS[seat].slice(-1),
      seat + ' is the same physical letter on both')
    assert.match(MAC_LABELS[seat], /^⌃⌥/, seat + ' is Control+Option on a Mac')
    assert.match(WIN_LABELS[seat], /^Ctrl\+Alt\+/, seat + ' is Ctrl+Alt on Windows')
  }
  // `mod+alt+j` — the chord Hermes registers to open Jarvis mode — is the one
  // that is Command on a Mac and Control on Windows.
  assert.equal(MAC_LABELS.open, '⌘⌥J')
  assert.equal(WIN_LABELS.open, 'Ctrl+Alt+J')
})

test('the window is asked, userAgentData first, and a hostile navigator cannot throw', () => {
  const win = nav => ({ navigator: nav })

  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(win({ userAgentData: { platform: 'Windows' } }))), WIN_LABELS)
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(win({ platform: 'Win32' }))), WIN_LABELS,
    'the deprecated reader is the fallback, not the first choice')
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(win({ userAgentData: { platform: 'Windows' }, platform: 'MacIntel' }))),
    WIN_LABELS, 'userAgentData wins when the two disagree')
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(win({ userAgentData: {}, platform: 'MacIntel' }))), MAC_LABELS)

  // nothing to read, and nothing that will let itself be read
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(win({}))), MAC_LABELS)
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor({})), MAC_LABELS)
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(null)), MAC_LABELS)
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(undefined)), MAC_LABELS)

  const hostile = {}
  Object.defineProperty(hostile, 'userAgentData', { get() { throw new Error('blocked') } })
  Object.defineProperty(hostile, 'platform', { get() { throw new Error('blocked') } })
  assert.deepEqual(labelsOf(M.jarvisKeyLabelsFor(win(hostile))), MAC_LABELS, 'a refusal is not a crash')
  assert.equal(M.jarvisPlatformName(win(hostile)), '')
})
