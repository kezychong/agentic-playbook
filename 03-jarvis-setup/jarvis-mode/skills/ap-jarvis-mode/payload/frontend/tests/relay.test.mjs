// tests/relay.test.mjs — node --test tests/relay.test.mjs
//
// The HUD relay (SPEC §4.7) without Electron. 20-presence.js + 25-relay.js are
// loaded as TEXT through `new Function` — the same order scripts/build.py
// concatenates them in, so the relay calls the real shared readers — with a
// fake window that has a localStorage, a CustomEvent and hand-driven timers.
//
// What is proved here: a Talk presence event becomes a storage frame with a
// rising seq; a storage command becomes exactly one `hermes-talk:command` on
// this window (stale and repeated ones are dropped); the liveness key carries a
// Talk probe; the hud-heartbeat.json receipt goes through the bridge; and the
// relay never opens a microphone (the one mic belongs to the main window).
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const PRESENCE_SRC = fileURLToPath(new URL('../src/20-presence.js', import.meta.url))
const RELAY_SRC = fileURLToPath(new URL('../src/25-relay.js', import.meta.url))
const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const SOURCE = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n' + fs.readFileSync(PRESENCE_SRC, 'utf8') + '\n' + fs.readFileSync(RELAY_SRC, 'utf8')

const GAIN = 3.5 // JARVIS_LEVEL_GAIN inside 20-presence.js

/** A square wave of amplitude `a` has RMS `a`, so a raw level L needs a = L / GAIN. */
function analyserByteFor(level) {
  return Math.round((level / GAIN) * 128)
}

function fakeStream(level) {
  const track = { kind: 'audio', stop() {} }
  return { __level: level, getAudioTracks: () => [track], getTracks: () => [track] }
}

const analyserProto = {
  getByteTimeDomainData(buf) {
    const level = this.__stream ? this.__stream.__level || 0 : 0
    const amp = analyserByteFor(level)
    for (let i = 0; i < buf.length; i += 1) buf[i] = 128 + (i % 2 ? amp : -amp)
  },
  disconnect() {}
}

class FakeAudioContext {
  constructor() { this.state = 'running' }
  createMediaStreamSource(stream) {
    return { stream, connect(analyser) { analyser.__stream = stream }, disconnect() {} }
  }
  createAnalyser() {
    return Object.assign(Object.create(analyserProto), { fftSize: 256, smoothingTimeConstant: 0, __stream: null })
  }
  resume() {}
  close() {}
}

const SCOPE = { id: 'test-scope', connectionId: 'test-connection', routeProfile: 'test-route', profileId: 'test-profile' }
const PRESENCE_KEY = 'hermes-jarvis:test-scope:presence'
const LIVE_KEY = 'hermes-jarvis:test-scope:relay'
const COMMAND_KEY = 'hermes-jarvis:test-scope:command'

function makeEnv() {
  let t = 1_700_000_000_000
  let frames = []
  let nextFrame = 1
  let nextInterval = 1
  let micCalls = 0
  const intervals = new Map()
  const store = new Map()
  const commands = []
  const writes = []
  const listeners = { 'hermes-talk:presence': new Set(), storage: new Set() }
  const talk = { hud: null, audios: [] }

  class FakeCustomEvent {
    constructor(type, init) {
      this.type = type
      this.detail = init ? init.detail : undefined
    }
  }

  const window = {
    AudioContext: FakeAudioContext,
    CustomEvent: FakeCustomEvent,
    localStorage: {
      getItem: key => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => { store.set(key, String(value)) },
      removeItem: key => { store.delete(key) }
    },
    dispatchEvent(event) {
      if (!event) return true
      if (event.type === 'hermes-talk:command') commands.push(event.detail)
      if (event.type === 'hermes-talk:presence') listeners['hermes-talk:presence'].forEach(fn => fn(event))
      return true
    },
    addEventListener(type, fn) { if (listeners[type]) listeners[type].add(fn) },
    removeEventListener(type, fn) { if (listeners[type]) listeners[type].delete(fn) },
    requestAnimationFrame(cb) { const id = nextFrame++; frames.push({ id, cb }); return id },
    cancelAnimationFrame(id) { frames = frames.filter(f => f.id !== id) },
    // Real intervals on the fake clock. The HUD window's store runs on a timer,
    // not on rAF (§4.7 amendment: an occluded window's rAF is throttled to
    // nothing), so a harness that never fires a timer would freeze exactly the
    // thing the amendment exists to keep moving. pump() advances the clock and
    // fires whatever is due; advance() moves the clock and fires nothing, for
    // the throttle assertions that want a jump without a run.
    setInterval(fn, ms) {
      const period = Math.max(1, Number(ms) || 1)
      const id = nextInterval++
      intervals.set(id, { fn, ms: period, next: t + period })
      return id
    },
    clearInterval(id) { intervals.delete(id) },
    setTimeout: (fn, ms) => setTimeout(fn, ms),
    clearTimeout: id => clearTimeout(id)
  }

  const document = {
    body: { tagName: 'BODY' },
    querySelector: sel => (sel === 'section.ht-hud' ? talk.hud : null),
    querySelectorAll: sel => (sel === 'audio' ? talk.audios.slice() : []),
    activeElement: null
  }

  const navigator = {
    mediaDevices: {
      getUserMedia: async () => { micCalls += 1; return { getAudioTracks: () => [], getTracks: () => [] } }
    }
  }

  const env = {
    window,
    document,
    navigator,
    commands,
    writes,
    talk,
    now: () => t,
    micCallCount: () => micCalls,
    read(key) {
      const raw = store.get(key)
      return raw ? JSON.parse(raw) : null
    },
    writeTextFile: async (path, content) => { writes.push({ path, content }); return { path } },
    setAudio(stream) {
      talk.audios.length = 0
      if (stream) talk.audios.push({ srcObject: stream })
    },
    mountHud(status, active = 'true') {
      talk.hud = { getAttribute: name => (name === 'data-active' ? active : ''), textContent: status }
    },
    dispatchBus(detail) {
      listeners['hermes-talk:presence'].forEach(fn => fn({ type: 'hermes-talk:presence', detail }))
    },
    fireStorage(key, newValue) {
      if (newValue === null) store.delete(key)
      else store.set(key, typeof newValue === 'string' ? newValue : JSON.stringify(newValue))
      listeners.storage.forEach(fn => fn({ key, newValue: newValue === null ? null : (typeof newValue === 'string' ? newValue : JSON.stringify(newValue)) }))
    },
    async pump(ms, step = 16) {
      let left = ms
      while (left > 0) {
        const slice = Math.min(step, left)
        t += slice
        left -= slice
        const due = frames
        frames = []
        for (const f of due) f.cb(t)
        for (const id of Array.from(intervals.keys())) {
          let guard = 0
          while (intervals.has(id) && intervals.get(id).next <= t && guard < 64) {
            guard += 1
            const iv = intervals.get(id)
            iv.next += iv.ms
            iv.fn()
          }
        }
        await null
        await null
      }
    },
    advance(ms) { t += ms },
    intervalPeriods: () => Array.from(intervals.values()).map(iv => iv.ms).sort((a, b) => a - b),
    rafPending: () => frames.length
  }

  return env
}

function loadRelay(env, extra = {}) {
  const factory = new Function('window', 'document', 'navigator', `${SOURCE}\nreturn createRelay;`)
  const createRelay = factory(env.window, env.document, env.navigator)
  return createRelay({
    win: env.window,
    doc: env.document,
    log: () => {},
    now: env.now,
    writeTextFile: env.writeTextFile,
    pluginVersion: 'test-1.1.0',
    getScope: () => SCOPE,
    getHermesRoot: () => '/tmp/hermes-test',
    ...extra
  })
}

test('a Talk presence event becomes a storage frame, with a rising seq', async () => {
  const env = makeEnv()
  const relay = loadRelay(env)
  relay.start()

  env.dispatchBus({
    phase: 'active', live: 'Using web_search…',
    audioActivity: { input: false, output: true },
    transcript: [{ id: 'r1', role: 'assistant', text: 'on my way' }],
    muted: false, sleeping: false
  })
  await env.pump(120)     // the relay's inner store reduces the frame
  relay.publish()

  const frame = env.read(PRESENCE_KEY)
  assert.ok(frame, 'the relay wrote hermes-jarvis:presence')
  assert.equal(frame.phase, 'active')
  assert.equal(frame.call, 'on')
  assert.equal(frame.mode, 'working', 'a "Using …" status is working, the same reading the store makes')
  assert.equal(frame.live, 'Using web_search…')
  assert.deepEqual(frame.audioActivity, { input: false, output: true }, 'the raw bus flags ride along')
  assert.equal(frame.transcript.length, 1)
  assert.equal(frame.transcript[0].text, 'on my way')
  assert.equal(frame.muted, false)
  assert.equal(frame.sleeping, false)
  assert.equal(typeof frame.at, 'number')
  assert.ok(frame.seq >= 1, 'every frame carries a sequence number')

  const first = frame.seq
  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: true, sleeping: false })
  await env.pump(120)
  relay.publish()
  const next = env.read(PRESENCE_KEY)
  assert.ok(next.seq > first, 'the sequence rises')
  assert.equal(next.muted, true, 'and the new state is carried')
  assert.equal(next.mode, 'muted')

  relay.stop()
})

test('a scope change never republishes the previous scope voice or transcript', async () => {
  const env = makeEnv()
  const scopeA = { ...SCOPE, id: 'scope-a', profileId: 'profile-a' }
  const scopeB = { ...SCOPE, id: 'scope-b', profileId: 'profile-b' }
  let selected = scopeA
  const relay = loadRelay(env, { getScope: () => selected })
  relay.start()
  env.dispatchBus({
    phase: 'active', live: 'Old private live', audioActivity: { output: true },
    transcript: [{ id: 'old-1', role: 'assistant', text: 'Old private words', at: env.now() }],
    muted: false, sleeping: false
  })
  await env.pump(120)
  assert.ok(env.read('hermes-jarvis:scope-a:presence'))

  selected = scopeB
  relay.beat(false)
  assert.equal(env.read('hermes-jarvis:scope-b:presence'), null, 'a heartbeat cannot relabel cached A data as B')

  env.advance(1)
  env.dispatchBus({
    phase: 'active', live: 'New scope live', audioActivity: {},
    transcript: [{ id: 'new-1', role: 'assistant', text: 'New scope words', at: env.now() }],
    muted: false, sleeping: false
  })
  await env.pump(120)
  const frame = env.read('hermes-jarvis:scope-b:presence')
  assert.equal(frame.live, 'New scope live')
  assert.deepEqual(frame.transcript.map(row => row.text), ['New scope words'])
  relay.stop()
})

test('Agent\'s level rides along, and level-only frames are capped at 15 Hz', async () => {
  const env = makeEnv()
  const voice = fakeStream(0.8)       // Talk's hidden <audio>, Agent mid-word
  env.setAudio(voice)
  const relay = loadRelay(env)
  relay.start()

  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(400)
  relay.publish()
  const loud = env.read(PRESENCE_KEY)
  assert.ok(loud.voiceLevel > 0.06, `the analyser reading crosses the gate (got ${loud.voiceLevel})`)
  assert.equal(loud.mode, 'speaking', 'and the HUD window knows Agent is speaking')

  // A quiet spell with nothing else changing: the frame stops carrying a level
  // it cannot measure, and the writes stay inside the 15 Hz cap.
  const before = env.read(PRESENCE_KEY).seq
  for (let i = 0; i < 20; i += 1) {
    voice.__level = i % 2 ? 0.8 : 0.05   // move it constantly, on purpose
    await env.pump(16)
    relay.tick()
  }
  const writes = env.read(PRESENCE_KEY).seq - before
  assert.ok(writes >= 1, 'a moving level is still relayed')
  assert.ok(writes <= 6, `≤ 15 Hz over 320 ms means at most 6 writes, saw ${writes}`)

  // Agent stops. Nothing moves, nothing changes: the 15 Hz tick has nothing to
  // say and says nothing — that is what keeps the wire quiet during a call.
  voice.__level = 0
  await env.pump(600)
  const quiet = env.read(PRESENCE_KEY)
  relay.tick()
  assert.equal(env.read(PRESENCE_KEY).seq, quiet.seq, 'a still picture is not re-written on the tick')

  // But the two-second BEAT re-stamps it anyway (§4.6/4.7 amendment). The state
  // is the same state; what changes is `at`. That is what lets the main window
  // hold this frame through a silent call instead of watching it rot.
  env.advance(2000)
  relay.beat()
  const restamped = env.read(PRESENCE_KEY)
  assert.ok(restamped.at > quiet.at, 'the beat gives the current frame a fresh stamp')
  assert.ok(restamped.seq > quiet.seq, 'with a rising seq, so nothing looks replayed')
  assert.equal(restamped.call, quiet.call, 'and it is the SAME reading, not a new claim')
  assert.equal(restamped.mode, quiet.mode)

  relay.stop()
})

test('an unknown action on the wire is never handed to Talk', () => {
  const env = makeEnv()
  const relay = loadRelay(env)
  relay.start()

  // The wire is plain localStorage on a shared origin. Anything in this window
  // can write that key, so the relay checks the word against Talk's own six
  // before it passes it on — the same list command() checks before writing.
  env.fireStorage(COMMAND_KEY, { action: 'drop-database', at: env.now(), nonce: 'x-1' })
  env.fireStorage(COMMAND_KEY, { action: '', at: env.now(), nonce: 'x-2' })
  env.fireStorage(COMMAND_KEY, { action: 'START', at: env.now(), nonce: 'x-3' })
  assert.deepEqual(env.commands, [{ action: 'start' }], 'only a real action, and case is forgiven')

  relay.stop()
})

test('the HUD store runs on a timer, not on requestAnimationFrame', () => {
  const env = makeEnv()
  const relay = loadRelay(env)
  relay.start()

  // An occluded Electron window has its rAF throttled to nothing, and the
  // floating Talk HUD spends most of a call behind something. If the store in
  // there ticked on rAF, the orb in the main window would freeze with it.
  assert.equal(env.rafPending(), 0, 'the HUD instance asks for no animation frames at all')
  assert.ok(env.intervalPeriods().includes(66), 'it ticks on a ~15 Hz interval instead')

  relay.stop()
})

test('a storage command is re-dispatched on this window exactly once', () => {
  const env = makeEnv()
  const relay = loadRelay(env)
  relay.start()

  env.fireStorage(COMMAND_KEY, { action: 'start', at: env.now(), nonce: 'n-1' })
  assert.deepEqual(env.commands, [{ action: 'start' }], 'the relay handed it to Talk on its own window')

  // The same nonce again (a coalesced or replayed event): ignored.
  env.fireStorage(COMMAND_KEY, { action: 'start', at: env.now(), nonce: 'n-1' })
  assert.equal(env.commands.length, 1, 'a seen nonce is never re-dispatched')

  // A new command goes through.
  env.fireStorage(COMMAND_KEY, { action: 'mute', at: env.now(), nonce: 'n-2' })
  assert.deepEqual(env.commands[1], { action: 'mute' })

  // Older than 5 s: dropped, because Talk must never act on yesterday's press.
  env.fireStorage(COMMAND_KEY, { action: 'stop', at: env.now() - 9000, nonce: 'n-3' })
  assert.equal(env.commands.length, 2, 'a stale command is ignored')

  // Another key on the same wire is none of our business.
  env.fireStorage('hermes.desktop.something', { action: 'stop', at: env.now(), nonce: 'n-4' })
  assert.equal(env.commands.length, 2)

  relay.stop()
})

test('the liveness key carries a Talk probe every beat', () => {
  const env = makeEnv()
  env.mountHud('Audio playing · Addressed: Hermes · Active work: 0')
  const relay = loadRelay(env)
  relay.start()

  const beat = env.read(LIVE_KEY)
  assert.ok(beat, 'the relay wrote hermes-jarvis:relay')
  assert.equal(typeof beat.at, 'number')
  assert.equal(typeof beat.seq, 'number')
  assert.deepEqual(beat.talk, { hud: true, view: false, audio: 0 }, 'what Talk is drawing in THIS window')

  env.advance(2000)
  relay.beat()
  const later = env.read(LIVE_KEY)
  assert.ok(later.at > beat.at, 'each beat is newer than the last')

  relay.stop()
})

test('the HUD writes its own receipt through the desktop bridge', async () => {
  const env = makeEnv()
  env.mountHud('Connected · microphone on')
  const relay = loadRelay(env)
  relay.start()
  await null

  // §4.7 relay hygiene / §4.8 ruling 8: EXACTLY one receipt at start. Two of
  // them made hud-heartbeat.json look like it was beating at twice its rate.
  assert.equal(env.writes.length, 1, 'exactly one hud heartbeat is written on start')
  const beat = env.writes[env.writes.length - 1]
  assert.equal(beat.path, '/tmp/hermes-test/jarvis/hud-heartbeat-test-scope.json', 'the receipt uses the active desktop root and profile scope')

  const body = JSON.parse(beat.content)
  assert.equal(body.pluginVersion, 'test-1.1.0')
  assert.ok(Date.parse(body.loadedAt) > 0, 'loadedAt is an ISO stamp')
  assert.ok(Date.parse(body.at) > 0, 'at is an ISO stamp')
  assert.equal(typeof body.relaySeq, 'number')
  assert.equal(body.lastError, null)
  assert.ok(body.talkProbe && typeof body.talkProbe === 'object', 'the probe rides along')
  assert.equal(body.talkProbe.hud, true, 'and it is the live reading of this window')

  // Throttled: a second beat inside 5 s writes nothing new.
  const before = env.writes.length
  relay.beat()
  assert.equal(env.writes.length, before, 'the receipt is throttled to one write per 5 s')
  env.advance(6000)
  relay.beat()
  assert.equal(env.writes.length, before + 1, 'and resumes after the throttle')

  relay.stop()
})

test('the relay never opens a microphone, and stop() lets go of the wire', async () => {
  const env = makeEnv()
  const relay = loadRelay(env)
  relay.start()

  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(1200)
  relay.publish()
  assert.equal(env.read(PRESENCE_KEY).call, 'on', 'a live call is relayed')
  assert.equal(env.micCallCount(), 0, 'the one microphone on this machine belongs to the main window')

  relay.stop()
  const frozen = env.read(PRESENCE_KEY).seq
  env.dispatchBus({ phase: 'idle', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  env.fireStorage(COMMAND_KEY, { action: 'stop', at: env.now(), nonce: 'after-stop' })
  assert.equal(env.read(PRESENCE_KEY).seq, frozen, 'a stopped relay writes nothing')
  assert.equal(env.commands.length, 0, 'and dispatches nothing')
})

test('the relay reads Talk, never the wire it just wrote to', async () => {
  const env = makeEnv()
  env.setAudio(fakeStream(0.4))
  const relay = loadRelay(env)
  relay.start()

  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(200)
  relay.publish()
  assert.equal(env.read(PRESENCE_KEY).call, 'on', 'a live call is on the wire')

  // Talk hangs up: the bus goes quiet and the audio element is gone. A store
  // that read its OWN last frame back out of localStorage would keep saying
  // "on" forever — the loop this fence exists to stop.
  env.setAudio(null)
  await env.pump(4000)
  relay.publish()
  const frame = env.read(PRESENCE_KEY)
  assert.equal(frame.call, 'off', 'the relay follows Talk down, not its own echo')
  assert.equal(frame.mode, 'idle')

  relay.stop()
})

// ---- SPEC §4.7 end to end: two windows, one wire ---------------------------
//
// Everything above tests one side at a time. This is the pair, running against
// each other the way they really do on Owner's Mac: Talk speaks ONLY in the
// HUD window, the overlay's store reads ONLY the main one, and the wire between
// them is the host's localStorage — where a write fires a `storage` event in
// every window EXCEPT the one that wrote it. Getting that last detail right is
// the whole point: a relay that heard its own writes would feed on itself.
class WorldEvent {
  constructor(type, init) {
    this.type = type
    this.detail = init ? init.detail : undefined
  }
}

function makeWorld() {
  let t = 1_700_000_000_000
  const cells = new Map()
  const panes = []

  function makePane(name) {
    const listeners = { 'hermes-talk:presence': new Set(), storage: new Set() }
    const commands = []
    const intervals = new Map()
    let nextInterval = 1
    let rafs = []
    let nextRaf = 1
    const audios = []

    const win = {
      AudioContext: FakeAudioContext,
      CustomEvent: WorldEvent,
      localStorage: {
        getItem: key => (cells.has(key) ? cells.get(key) : null),
        setItem(key, value) {
          const text = String(value)
          cells.set(key, text)
          // The whole trick: everyone else hears it, the writer never does.
          for (const other of panes) {
            if (other.name === name) continue
            other.listeners.storage.forEach(fn => fn({ key, newValue: text }))
          }
        },
        removeItem: key => { cells.delete(key) }
      },
      dispatchEvent(event) {
        if (!event) return true
        if (event.type === 'hermes-talk:command') {
          commands.push(event.detail)
          if (pane.onCommand) pane.onCommand(event.detail)
        }
        if (event.type === 'hermes-talk:presence') {
          listeners['hermes-talk:presence'].forEach(fn => fn(event))
        }
        return true
      },
      addEventListener(type, fn) { if (listeners[type]) listeners[type].add(fn) },
      removeEventListener(type, fn) { if (listeners[type]) listeners[type].delete(fn) },
      requestAnimationFrame(cb) { const id = nextRaf++; rafs.push({ id, cb }); return id },
      cancelAnimationFrame(id) { rafs = rafs.filter(f => f.id !== id) },
      setInterval(fn, ms) {
        const period = Math.max(1, Number(ms) || 1)
        const id = nextInterval++
        intervals.set(id, { fn, ms: period, next: t + period })
        return id
      },
      clearInterval(id) { intervals.delete(id) },
      setTimeout: (fn, ms) => setTimeout(fn, ms),
      clearTimeout: id => clearTimeout(id)
    }

    const doc = {
      body: { tagName: 'BODY' },
      querySelector: sel => (sel === 'section.ht-hud' ? pane.hud : null),
      querySelectorAll: sel => (sel === 'audio' ? audios.slice() : []),
      activeElement: null
    }

    const pane = {
      name, win, doc, commands, audios, listeners,
      hud: null,
      onCommand: null,
      talkSays(detail) {
        listeners['hermes-talk:presence'].forEach(fn => fn({ type: 'hermes-talk:presence', detail }))
      },
      setAudio(stream) {
        audios.length = 0
        if (stream) audios.push({ srcObject: stream })
      },
      run() {
        const due = rafs
        rafs = []
        for (const f of due) f.cb(t)
        for (const id of Array.from(intervals.keys())) {
          let guard = 0
          while (intervals.has(id) && intervals.get(id).next <= t && guard < 64) {
            guard += 1
            const iv = intervals.get(id)
            iv.next += iv.ms
            iv.fn()
          }
        }
      }
    }
    panes.push(pane)
    return pane
  }

  const world = {
    hud: makePane('hud'),
    main: makePane('main'),
    now: () => t,
    read(key) {
      const raw = cells.get(key)
      return raw ? JSON.parse(raw) : null
    },
    async pump(ms, step = 16) {
      let left = ms
      while (left > 0) {
        const slice = Math.min(step, left)
        t += slice
        left -= slice
        for (const pane of panes) pane.run()
        await null
        await null
      }
    }
  }
  return world
}

function loadIn(pane) {
  return new Function('window', 'document', 'navigator',
    `${SOURCE}\nreturn { createRelay: createRelay, createPresence: createPresence };`
  )(pane.win, pane.doc, { mediaDevices: null })
}

test('end to end: Talk in the HUD, the overlay in the main window, one wire', async () => {
  const world = makeWorld()
  const hudSide = loadIn(world.hud)
  const mainSide = loadIn(world.main)

  // The HUD window: Talk lives here, but has not been asked for anything yet.
  const relay = hudSide.createRelay({
    win: world.hud.win, doc: world.hud.doc, log: () => {},
    now: world.now, writeTextFile: async () => ({}), pluginVersion: 'e2e', getScope: () => SCOPE,
    getHermesRoot: () => '/tmp/hermes-test'
  })
  relay.start()

  // The main window: the overlay's store, and nothing of Talk at all.
  const store = mainSide.createPresence({ now: world.now, log: () => {}, commandWaitMs: 200, getScope: () => SCOPE })
  store.start()
  // The relay was already up, so the store finds it immediately — and what it
  // finds is the truth at that moment: a relay that is watching nothing yet.
  // §4.9 amendment 4 — a beat is not a call. A relay frame reporting `off`
  // no longer owns the ranking, so with nothing else to read this window says
  // `none` rather than dressing an empty relay up as the source of a reading.
  assert.equal(store.get().call, 'off', 'it honestly reports no call')
  assert.equal(store.get().source.status, 'none', 'and a relay watching nothing is not a source')

  // Talk goes live — in the HUD window, on the HUD window's bus. Its markup
  // and its hidden <audio> appear in that window and nowhere else.
  world.hud.hud = { getAttribute: name => (name === 'data-active' ? 'true' : ''), textContent: 'Listening…' }
  world.hud.setAudio(fakeStream(0.8))
  world.hud.talkSays({
    phase: 'active', live: '', audioActivity: { input: false, output: true },
    transcript: [{ id: 'e1', role: 'assistant', text: 'go ahead' }], muted: false, sleeping: false
  })
  await world.pump(400)

  let p = store.get()
  assert.equal(p.source.status, 'relay', 'the main window found it across the wire')
  assert.equal(p.call, 'on')
  assert.equal(p.source.voice, 'relay-analyser', 'and the level was measured over there')
  assert.ok(p.levels.voice > 0.06, `Agent's voice reached the orb (got ${p.levels.voice})`)
  assert.equal(p.captions[0].text, 'go ahead')
  assert.equal(world.hud.commands.length, 0, 'nothing has been asked of Talk yet')

  // Ten seconds of a steady call: Talk says nothing more, the relay beats on.
  await world.pump(10000)
  p = store.get()
  assert.equal(p.call, 'on', 'a quiet call is still a call, ten seconds in')
  assert.equal(p.source.status, 'relay')

  // Owner presses MUTE in the main window. It crosses the wire, the relay
  // re-dispatches it on Talk's own window, and Talk answers with a new frame.
  world.hud.onCommand = detail => {
    if (detail.action !== 'mute') return
    world.hud.talkSays({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: true, sleeping: false })
  }
  const res = await store.command('mute')
  assert.deepEqual(res, { ok: true, via: 'relay', reason: '' })
  assert.deepEqual(world.hud.commands, [{ action: 'mute' }], 'Talk heard it once, in its own window')
  assert.equal(world.main.commands.length, 0, 'and nothing was dispatched into the main window')

  await world.pump(300)
  assert.equal(store.get().mode, 'muted', 'the proof came back as a frame, not as optimism')

  // The HUD window closes. The beat stops, and the overlay says so.
  relay.stop()
  await world.pump(5400)
  const after = store.get()
  assert.equal(after.source.status, 'none', 'no relay, no reading')
  assert.equal(after.call, 'off')

  store.stop()
})
