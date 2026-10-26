// tests/presence.test.mjs — node --test tests/presence.test.mjs
//
// Loads src/20-presence.js as TEXT through `new Function` with a fake
// window/document/navigator, so the presence reducer is proved without a
// browser, without a build step and without importing the plugin (which has
// imports Node cannot resolve).
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const SRC = fileURLToPath(new URL('../src/20-presence.js', import.meta.url))
const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const SOURCE = fs.readFileSync(SRC, 'utf8')
// 05-scope.js is file 05 of the concat build, so it is always in front of this
// one in the real plugin. It carries the shared helpers (the chord labels).
const PRELUDE = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n'
const GAIN = 3.5 // LEVEL_GAIN inside 20-presence.js
const SCOPE = { id: 'test-scope', connectionId: 'test-connection', routeProfile: 'test-route', profileId: 'test-profile' }

/** A square wave of amplitude `a` has RMS `a`, so a raw level L needs a = L / GAIN. */
function analyserByteFor(level) {
  return Math.round((level / GAIN) * 128)
}

function fakeStream(level) {
  const track = { kind: 'audio', stopped: false, stop() { track.stopped = true } }
  return {
    __level: level,
    __track: track,
    getAudioTracks: () => [track],
    getTracks: () => [track]
  }
}

function makeEnv() {
  let t = 1_700_000_000_000
  let frames = []
  let nextId = 1
  let micCalls = 0
  let mediaElementSources = 0
  const audios = []
  const busListeners = new Set()
  // The HUD relay's half of the wire (SPEC §4.7): the host's localStorage, and
  // the `storage` events it fires in THIS window when the other one writes.
  const cells = new Map()
  const storageListeners = new Set()

  const analyserProto = {
    getByteTimeDomainData(buf) {
      const level = this.__stream ? this.__stream.__level || 0 : 0
      const amp = analyserByteFor(level)
      for (let i = 0; i < buf.length; i += 1) buf[i] = 128 + (i % 2 ? amp : -amp)
    },
    disconnect() {}
  }

  class FakeAudioContext {
    constructor() {
      this.state = 'running'
    }
    // SPEC §4.9 ruling 2: metering must never re-route playback, so this is the
    // one AudioContext call the plugin may never make. It is here to be counted.
    createMediaElementSource() {
      mediaElementSources += 1
      throw new Error('createMediaElementSource re-routes playback and is banned (SPEC §4.9)')
    }
    createMediaStreamSource(stream) {
      return {
        stream,
        connect(analyser) { analyser.__stream = stream },
        disconnect() {}
      }
    }
    createAnalyser() {
      return Object.assign(Object.create(analyserProto), { fftSize: 256, smoothingTimeConstant: 0, __stream: null })
    }
    resume() {}
    close() {}
  }

  const commands = []

  class FakeCustomEvent {
    constructor(type, init) {
      this.type = type
      this.detail = init ? init.detail : undefined
    }
  }

  const window = {
    AudioContext: FakeAudioContext,
    CustomEvent: FakeCustomEvent,
    devicePixelRatio: 1,
    // Talk's end of the wire: commands are taped, presence frames are delivered
    // to whoever is listening (the store, and command()'s own one-off waiter).
    dispatchEvent(event) {
      if (!event) return true
      if (event.type === 'hermes-talk:command') {
        commands.push(event.detail)
        // Real Talk ANSWERS a command with a presence frame. Tests that care
        // how many times `start` had to be sent hang their fake Talk here.
        if (env.onCommand) env.onCommand(event.detail)
      }
      if (event.type === 'hermes-talk:presence') busListeners.forEach(fn => fn(event))
      return true
    },
    requestAnimationFrame(cb) {
      const id = nextId++
      frames.push({ id, cb })
      return id
    },
    cancelAnimationFrame(id) {
      frames = frames.filter(f => f.id !== id)
    },
    localStorage: {
      getItem: key => (cells.has(key) ? cells.get(key) : null),
      setItem: (key, value) => {
        cells.set(key, String(value))
        // The other window's half: the relay re-dispatches on Talk, and Talk
        // answers with a frame. Tests plug their fake HUD in here.
        if (key === 'hermes-jarvis:test-scope:command' && env.onRelayCommand) {
          env.onRelayCommand(JSON.parse(String(value)))
        }
      },
      removeItem: key => { cells.delete(key) }
    },
    addEventListener(type, fn) {
      if (type === 'hermes-talk:presence') busListeners.add(fn)
      if (type === 'storage') storageListeners.add(fn)
    },
    removeEventListener(type, fn) {
      if (type === 'hermes-talk:presence') busListeners.delete(fn)
      if (type === 'storage') storageListeners.delete(fn)
    },
    setTimeout: (fn, ms) => setTimeout(fn, ms),
    clearTimeout: id => clearTimeout(id),
    setInterval: (fn, ms) => setInterval(fn, ms),
    clearInterval: id => clearInterval(id)
    // No MutationObserver on purpose: the DOM source is exercised through
    // document.querySelector, not through mutation plumbing.
  }

  // §4.10 amendment 4: the store watches the document for a press on the
  // host's own End button, so this fake has to carry listeners.
  const docListeners = new Map()
  const document = {
    body: { tagName: 'BODY' },
    querySelector: () => null,
    querySelectorAll: sel => (sel === 'audio' ? audios.slice() : []),
    activeElement: null,
    addEventListener(type, fn) {
      if (!docListeners.has(type)) docListeners.set(type, new Set())
      docListeners.get(type).add(fn)
    },
    removeEventListener(type, fn) {
      const set = docListeners.get(type)
      if (set) set.delete(fn)
    }
  }

  const navigator = {
    mediaDevices: {
      getUserMedia: async () => {
        micCalls += 1
        return env.micStream
      }
    }
  }

  const env = {
    window,
    document,
    navigator,
    micStream: fakeStream(0),
    onCommand: null,        // fake Talk on this window's bus
    onRelayCommand: null,   // fake Talk behind the HUD relay
    now: () => t,
    audios,
    commands,
    micCallCount: () => micCalls,
    mediaElementSourceCount: () => mediaElementSources,
    setAudio(stream) {
      audios.length = 0
      if (stream) audios.push({ srcObject: stream })
    },
    dispatchBus(detail) {
      busListeners.forEach(fn => fn({ type: 'hermes-talk:presence', detail }))
    },
    /** A hand on a control in the page: the capture-phase listeners see it,
     *  exactly as they would in the app (§4.10 amendment 4). */
    clickDoc(target) {
      const set = docListeners.get('click')
      if (set) Array.from(set).forEach(fn => fn({ type: 'click', target }))
    },
    // What the HUD relay does from the other window.
    relayFrame(patch = {}) {
      const frame = {
        phase: 'active', live: '', audioActivity: {}, transcript: [],
        muted: false, sleeping: false, mode: 'listening', call: 'on',
        at: t, seq: (env.relaySeq += 1), ...patch
      }
      env.writeCell('hermes-jarvis:test-scope:presence', frame)
      return frame
    },
    relayBeat(patch = {}) {
      const beat = { at: t, seq: env.relaySeq, talk: { hud: true, view: false, audio: 1 }, ...patch }
      env.writeCell('hermes-jarvis:test-scope:relay', beat)
      return beat
    },
    relaySeq: 0,
    /** Write a cell exactly as the other window would: value first, then the
     *  `storage` event this window receives. */
    writeCell(key, value, notify = true) {
      cells.set(key, JSON.stringify(value))
      if (notify) storageListeners.forEach(fn => fn({ key, newValue: JSON.stringify(value) }))
    },
    /** Put a value on the wire WITHOUT an event — the window that was asleep. */
    seedCell(key, value) {
      cells.set(key, JSON.stringify(value))
    },
    readCell(key) {
      const raw = cells.get(key)
      return raw ? JSON.parse(raw) : null
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
        await null
        await null
      }
    }
  }

  return env
}

function loadPresence(env, extra = {}) {
  const factory = new Function('window', 'document', 'navigator', `${PRELUDE}${SOURCE}\nreturn createPresence;`)
  const createPresence = factory(env.window, env.document, env.navigator)
  return createPresence({ now: env.now, log: () => {}, getScope: () => SCOPE, ...extra })
}

// Hermes Desktop 0.21.3 renders the composer action as
// button[aria-label="Open Hermes Talk"]; the unavailable popover shows its
// reason in a [role="status"] inside PopoverContent (aria-label "Hermes Talk").
function mountTalkTrigger(env, { onClick = null, status = '', present = true } = {}) {
  const previous = env.document.querySelector
  const clicks = []
  const button = {
    tagName: 'BUTTON',
    click() {
      clicks.push(env.now())
      if (onClick) onClick()
    }
  }
  const statusNode = { textContent: status }
  env.document.querySelector = sel => {
    if (present && sel === 'button[aria-label="Open Hermes Talk"]') return button
    if (status && sel === '[aria-label="Hermes Talk"] [role="status"]') return statusNode
    return previous ? previous(sel) : null
  }
  return { clicks, button }
}

// Hermes Desktop 0.21.3 with context.voice: the composer renders
// DesktopTalkLauncher (aria-label "Open floating Hermes Talk") and clicking it
// opens the HUD window where TalkPage — and our relay — actually live.
function mountFloatingTrigger(env, { onClick = null } = {}) {
  const previous = env.document.querySelector
  const clicks = []
  const button = { tagName: 'BUTTON', click() { clicks.push(env.now()); if (onClick) onClick() } }
  env.document.querySelector = sel => {
    if (sel === 'button[aria-label="Open floating Hermes Talk"]') return button
    return previous ? previous(sel) : null
  }
  return { clicks, button }
}

test('the presence bus wins over the derived source, and expires after 2 s', async () => {
  const env = makeEnv()
  const voice = fakeStream(0.8)
  env.setAudio(voice)
  const presence = loadPresence(env)
  presence.start()

  await env.pump(300)
  let p = presence.get()
  assert.equal(p.source.status, 'derived', 'no bus, no Talk HUD → derived')
  assert.equal(p.mode, 'speaking', 'Agent is loud on the analyser')

  env.dispatchBus({ phase: 'active', live: '', audioActivity: { input: false, output: false }, transcript: [], muted: true, sleeping: false })
  await env.pump(100)
  p = presence.get()
  assert.equal(p.source.status, 'bus', 'a fresh bus frame outranks the analyser')
  assert.equal(p.mode, 'muted', 'the bus knows a mute the analyser cannot see')

  await env.pump(900)
  assert.equal(presence.get().source.status, 'bus', 'still inside the 2 s window')

  await env.pump(1400)
  p = presence.get()
  assert.equal(p.source.status, 'derived', 'the bus went quiet → fall back')
  assert.equal(p.mode, 'speaking')

  presence.stop()
})

test('derived mode rules: speaking, listening, the thinking window, and idle', async () => {
  const env = makeEnv()
  const voice = fakeStream(0.8)
  env.micStream = fakeStream(0)
  env.setAudio(voice)
  const presence = loadPresence(env)
  presence.start()

  await env.pump(300)
  assert.equal(presence.get().mode, 'speaking', 'voice > 0.06 → speaking')
  assert.ok(presence.get().levels.voice > 0.06)

  // Agent stops; Owner starts. The mic tap is open because the call is on.
  // The analyser release is 250 ms, so 0.8 needs ~900 ms to fall under the gate.
  voice.__level = 0
  env.micStream.__level = 0.8
  await env.pump(900)
  let p = presence.get()
  assert.equal(p.source.mic, 'tap', 'the mic tap attached while the call is on')
  assert.ok(p.levels.mic > 0.06)
  assert.equal(p.mode, 'listening', 'mic > 0.06 → listening')

  // Owner stops talking: inside 1500 ms of the last mic activity → thinking.
  env.micStream.__level = 0
  await env.pump(800)
  assert.equal(presence.get().mode, 'thinking', 'the thinking window after speech ends')

  await env.pump(1700)
  assert.equal(presence.get().mode, 'listening', 'past the window, the call is still on')

  // Call ends: no audio element with tracks at all.
  env.setAudio(null)
  await env.pump(1200)
  p = presence.get()
  assert.equal(p.call, 'off')
  assert.equal(p.mode, 'idle', 'call off → idle')
  assert.equal(p.source.mic, 'none', 'the mic is released within 1 s of the call ending')

  presence.stop()
})

test('the microphone is never opened while the call is off', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env)
  presence.start()
  await env.pump(2000)
  assert.equal(env.micCallCount(), 0, 'getUserMedia must not be called with the call off')
  assert.equal(presence.get().mode, 'idle')
  presence.stop()
})

test('demo mode cycles modes and flags itself', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env)
  presence.start()
  presence.setDemo(true)

  const seen = []
  for (let i = 0; i < 6; i += 1) {
    await env.pump(3100)
    const p = presence.get()
    assert.equal(p.demo, true, 'demo mode labels itself')
    assert.equal(p.source.status, 'none', 'demo claims no real source')
    seen.push(p.mode)
  }
  assert.ok(new Set(seen).size >= 3, `expected the demo to cycle, saw ${seen.join(',')}`)
  assert.equal(env.micCallCount(), 0, 'demo mode never touches the microphone')

  presence.setDemo(false)
  await env.pump(100)
  assert.equal(presence.get().demo, false)
  presence.stop()
})

test('captions are capped at 6, newest last', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env)
  presence.start()

  const transcript = Array.from({ length: 10 }, (_, i) => ({
    id: `row-${i}`,
    role: i % 2 ? 'assistant' : 'user',
    text: `line ${i}`
  }))
  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript, muted: false, sleeping: false })
  await env.pump(100)

  const caps = presence.get().captions
  assert.equal(caps.length, 6, 'CAPTION_CAP is 6')
  assert.equal(caps[5].text, 'line 9', 'newest last')
  assert.equal(caps[0].text, 'line 4', 'oldest two dropped')
  assert.equal(caps[5].role, 'assistant')

  presence.stop()
})

// Talk renders data-active = String(active && !muted && !sleeping)
// (desktop-entry.js:242), so a muted or sleeping call shows "false" on the
// compact HUD. Mount exactly that: the collapsed HUD, no expanded panel.
function mountCompactHud(env, statusText, active = 'false') {
  const state = { status: statusText, active }
  const hud = { getAttribute: name => (name === 'data-active' ? state.active : ''), textContent: '' }
  const status = {
    get textContent() { return state.status },
    set textContent(v) { state.status = v }
  }
  env.document.querySelector = sel => {
    if (sel === 'section.ht-hud') return hud
    if (sel === '#hermes-talk-hud-status') return status
    return null // no section.ht-desktop-view: the panel is collapsed
  }
  return {
    set(nextStatus, nextActive) {
      state.status = nextStatus
      if (nextActive !== undefined) state.active = nextActive
    }
  }
}

test('the collapsed Talk HUD outranks the analyser', async () => {
  const env = makeEnv()
  env.setAudio(fakeStream(0.8)) // the analyser alone would say "speaking"
  mountCompactHud(env, 'Sleeping · microphone off · Addressed: Hermes · Active work: 0')

  const presence = loadPresence(env)
  presence.start()
  await env.pump(400)

  const p = presence.get()
  assert.equal(p.source.status, 'dom', 'Talk HUD present → dom source')
  assert.equal(p.mode, 'sleeping', 'the HUD status text beats the analyser')
  assert.equal(p.call, 'on', 'sleeping is still a live call')

  presence.stop()
})

test('a muted call reads as on from the live audio element, not data-active', async () => {
  const env = makeEnv()
  const voice = fakeStream(0)
  env.setAudio(voice)
  mountCompactHud(env, 'Microphone muted · Addressed: Hermes · Active work: 0')

  const presence = loadPresence(env)
  presence.start()
  await env.pump(400)

  let p = presence.get()
  assert.equal(p.source.status, 'dom')
  assert.equal(p.mode, 'muted', 'the HUD says muted')
  assert.equal(p.call, 'on', 'data-active is "false" — the audio element carries the call')

  // Drop the audio element: nothing is left to prove a call, so it reads off.
  env.setAudio(null)
  await env.pump(400)
  p = presence.get()
  assert.equal(p.call, 'off', 'no HUD active flag and no audio element → off')

  presence.stop()
})

test('the listen-only tap closes on mute and reopens on unmute', async () => {
  const env = makeEnv()
  env.setAudio(fakeStream(0))        // a live call, Agent silent
  env.micStream = fakeStream(0.5)
  const hud = mountCompactHud(env, 'Connected · microphone on · Addressed: Hermes · Active work: 0', 'true')

  const presence = loadPresence(env)
  presence.start()
  await env.pump(400)

  let p = presence.get()
  assert.equal(p.mode, 'listening')
  assert.equal(p.source.mic, 'tap', 'an unmuted live call opens the meter')
  assert.equal(env.micCallCount(), 1)
  const firstGrant = env.micStream

  // Owner mutes Talk. Mute means "no listening" — the meter must go.
  hud.set('Microphone muted · Addressed: Hermes · Active work: 0', 'false')
  await env.pump(800) // > MIC_RELEASE_MS (600)
  p = presence.get()
  assert.equal(p.mode, 'muted')
  assert.equal(p.call, 'on', 'muting does not end the call')
  assert.equal(p.source.mic, 'none', 'the tap is closed while muted')
  assert.equal(p.levels.mic, 0, 'and it stops reporting a level')
  assert.equal(firstGrant.__track.stopped, true, 'the microphone track was actually stopped')
  assert.equal(env.micCallCount(), 1, 'no new grant was requested while muted')

  // Sleep is the same promise as mute.
  hud.set('Sleeping · microphone off · Addressed: Hermes · Active work: 0', 'false')
  await env.pump(400)
  assert.equal(presence.get().mode, 'sleeping')
  assert.equal(presence.get().source.mic, 'none', 'sleeping keeps the tap closed')
  assert.equal(env.micCallCount(), 1)

  // Unmute: the meter comes back on its own.
  env.micStream = fakeStream(0.5)
  hud.set('Connected · microphone on · Addressed: Hermes · Active work: 0', 'true')
  await env.pump(600)
  p = presence.get()
  assert.equal(p.mode, 'listening')
  assert.equal(p.source.mic, 'tap', 'unmuting reopens the meter')
  assert.equal(env.micCallCount(), 2, 'exactly one new grant')

  presence.stop()
  assert.equal(env.micStream.__track.stopped, true, 'stop() releases the microphone too')
})

// ---- SPEC §4.6: command(action), the overlay's one door into Talk ----------

test('command() rides the bus when the bus is alive', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env)
  presence.start()

  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(100)
  assert.equal(presence.get().source.status, 'bus')

  const res = await presence.command('mute')
  assert.deepEqual(res, { ok: true, via: 'bus', reason: '' })
  assert.deepEqual(env.commands, [{ action: 'mute' }], 'exactly one hermes-talk:command left the building')

  const again = await presence.command('stop')
  assert.equal(again.via, 'bus')
  assert.deepEqual(env.commands[1], { action: 'stop' })

  presence.stop()
})

test('with no bus, start clicks the composer Talk trigger and then dispatches', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 200 })
  presence.start()

  // Clicking Talk mounts TalkPage, which announces itself on the presence bus.
  const talk = mountTalkTrigger(env, {
    onClick: () => env.dispatchBus({
      phase: 'starting', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false
    })
  })
  // …and answering `start` is what takes it from starting to active.
  env.onCommand = detail => {
    if (detail.action === 'start') {
      env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
    }
  }

  const res = await presence.command('start')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'opened-then-bus')
  assert.equal(talk.clicks.length, 1, 'the host trigger was clicked exactly once')
  assert.deepEqual(env.commands, [{ action: 'start' }], 'start is dispatched AFTER the bus answers')

  presence.stop()
})

test('with no bus, anything but start refuses out loud', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 200 })
  presence.start()
  mountTalkTrigger(env, {})

  for (const action of ['stop', 'mute', 'unmute', 'sleep', 'wake']) {
    const res = await presence.command(action)
    assert.deepEqual(res, { ok: false, via: 'none', reason: 'no live call' }, action)
  }
  assert.equal(env.commands.length, 0, 'nothing was dispatched without a live call')

  presence.stop()
})

test('an unavailable Talk popover is quoted back, not papered over', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 120 })
  presence.start()

  // The popover opens and shows its reason instead of a call: no presence frame.
  const talk = mountTalkTrigger(env, { status: 'Talk needs a voice key in this profile.' })

  const res = await presence.command('start')
  assert.equal(res.ok, false)
  assert.equal(res.via, 'none')
  assert.equal(res.reason, 'Talk needs a voice key in this profile.')
  assert.equal(talk.clicks.length, 1)
  assert.equal(env.commands.length, 0, 'no command is dispatched at a popover that cannot start')

  presence.stop()
})

test('command() never throws and never touches Talk from a demo', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 60 })
  presence.start()
  presence.setDemo(true)

  const res = await presence.command('start')
  assert.equal(res.ok, false)
  assert.equal(env.commands.length, 0, 'a demo is a drawing — it never reaches Talk')

  const bogus = await presence.command('explode')
  assert.deepEqual(bogus, { ok: false, via: 'none', reason: 'unknown command' })

  presence.setDemo(false)
  presence.stop()
})

// ---- SPEC §4.7: the HUD relay, seen from the main window -------------------

test('relay frames become snapshots, ranked under the bus and over the DOM', async () => {
  const env = makeEnv()
  env.setAudio(null)                 // no audio element here: Talk is in the HUD
  const presence = loadPresence(env)
  presence.start()
  await env.pump(100)
  assert.equal(presence.get().source.status, 'none', 'nothing to read in this window yet')

  env.relayBeat()
  env.relayFrame({
    mode: 'speaking', call: 'on', live: 'Audio playing', voiceLevel: 0.7,
    transcript: [{ id: 'c1', role: 'assistant', text: 'here you go' }]
  })
  await env.pump(300)

  let p = presence.get()
  assert.equal(p.source.status, 'relay', 'the relay is a real source, named honestly')
  assert.equal(p.source.voice, 'relay-analyser', 'the level was measured — in the other window')
  assert.equal(p.mode, 'speaking')
  assert.equal(p.call, 'on')
  assert.equal(p.live, 'Audio playing')
  assert.ok(p.levels.voice > 0.06, 'the orb gets its level across the wire')
  assert.equal(p.captions.length, 1)
  assert.equal(p.captions[0].text, 'here you go')

  // The bus still outranks it: if Talk ever speaks in THIS window, it wins.
  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: true, sleeping: false })
  await env.pump(100)
  assert.equal(presence.get().source.status, 'bus')
  assert.equal(presence.get().mode, 'muted')

  // The bus goes quiet AND the relay stops beating — nothing renews either key.
  // Only then is the reading over. It is the BEAT that ends it, never the age
  // of the last frame: see the quiet-call test below, where the frame goes
  // twelve seconds without changing and the call stays honestly on.
  await env.pump(6000)
  p = presence.get()
  assert.equal(p.source.status, 'none', 'no beat for 5 s → the relay is gone')
  assert.equal(p.levels.voice, 0, 'and the orb stops moving rather than coasting')

  presence.stop()
})

test('a relay left running before this window opened is found at start', async () => {
  const env = makeEnv()
  env.setAudio(null)
  // No storage events at all — the values were written before we subscribed.
  env.seedCell('hermes-jarvis:test-scope:relay', { at: env.now(), seq: 4, talk: { hud: true, view: true, audio: 1 } })
  env.seedCell('hermes-jarvis:test-scope:presence', {
    phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false,
    sleeping: false, mode: 'listening', call: 'on', at: env.now(), seq: 4
  })

  const presence = loadPresence(env)
  presence.start()
  await env.pump(100)

  const p = presence.get()
  assert.equal(p.source.status, 'relay', 'start() reads the current value, not just events')
  assert.equal(p.call, 'on')
  assert.equal(p.mode, 'listening')

  presence.stop()
})

test('command() writes the relay key when Talk is in the HUD window', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 200 })
  presence.start()
  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on' })
  await env.pump(100)
  assert.equal(presence.get().source.status, 'relay')

  const res = await presence.command('mute')
  assert.deepEqual(res, { ok: true, via: 'relay', reason: '' })
  assert.equal(env.commands.length, 0, 'nothing is dispatched in THIS window — Talk is not here')

  const first = env.readCell('hermes-jarvis:test-scope:command')
  assert.equal(first.action, 'mute')
  assert.equal(first.at, env.now(), 'stamped, so the relay can drop a stale one')
  assert.ok(first.nonce, 'and nonced, so the relay never acts on it twice')

  const again = await presence.command('stop')
  const second = env.readCell('hermes-jarvis:test-scope:command')
  assert.equal(again.via, 'relay')
  assert.equal(second.action, 'stop')
  assert.notEqual(second.nonce, first.nonce, 'every press gets its own nonce')

  presence.stop()
})

test('with no bus and no relay, start opens the floating HUD and waits for it', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 400 })
  presence.start()

  // Clicking the composer's launcher opens the HUD window; our plugin loads
  // there, starts the relay, and the relay's first write lands on the wire.
  const trigger = mountFloatingTrigger(env, {
    onClick: () => {
      env.relayBeat()
      env.relayFrame({ mode: 'thinking', call: 'connecting', phase: 'starting' })
    }
  })
  // The relay hands `start` to Talk in that window, and Talk goes live.
  env.onRelayCommand = cmd => {
    if (cmd.action === 'start') env.relayFrame({ mode: 'listening', call: 'on', phase: 'active' })
  }

  const res = await presence.command('start')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'opened-then-relay', 'the HUD answered, so the command went by the relay')
  assert.equal(trigger.clicks.length, 1, 'the floating launcher was clicked exactly once')
  assert.equal(env.commands.length, 0, 'and nothing was dispatched into this window')
  assert.equal(env.readCell('hermes-jarvis:test-scope:command').action, 'start')

  presence.stop()
})

test('with no composer and no relay, the title-bar tool is tried LAST and named plainly', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 120, navWaitMs: 120 })
  presence.start()

  // Owner's real window on 2026-09-19 14:30: one talk-named button, the
  // title-bar tool, no chat composer, no relay. Clicking that tool only toasts.
  const win = mountWindow(env, { titlebar: true })

  const res = await presence.command('start')
  assert.deepEqual(win.clicks, ['titlebar'], 'the title-bar tool IS a door — but the last one')
  assert.equal(res.ok, false)
  assert.equal(res.reason, 'No chat is open · open a chat with Agent, then press START TALK',
    'and the pod line is the plain instruction, with no button counts in it')

  presence.stop()
})

// ---- the 4.6 / 4.7 amendments: a quiet call is still a call ----------------

test('a quiet live call stays on: the beat is alive, not the last frame', async () => {
  const env = makeEnv()
  env.setAudio(null)                 // Talk is in the HUD; nothing to tap here
  const presence = loadPresence(env)
  presence.start()

  // Talk goes live and says so ONCE. Its bus fires on state CHANGES, so while
  // Agent simply listens there is nothing further to send — and the relay has
  // nothing new to relay. All it can do is keep beating.
  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on', live: 'Listening…' })
  await env.pump(200)
  assert.equal(presence.get().source.status, 'relay', 'the first frame lands')
  assert.equal(presence.get().call, 'on')

  // Twelve seconds of a perfectly steady call: the beat every 2 s, and NOT one
  // new frame. The frame is twelve seconds old by the end and still true.
  for (let i = 1; i <= 6; i += 1) {
    await env.pump(2000)
    env.relayBeat()
    const q = presence.get()
    assert.equal(q.call, 'on', `still on ${i * 2} s into the quiet`)
    assert.equal(q.mode, 'listening', 'and still holding the mode it was given')
    assert.equal(q.source.status, 'relay', 'named honestly the whole way through')
  }

  // The HUD window closes. The beat stops with it, and within five seconds the
  // reading is over — that, and only that, is what ends it.
  await env.pump(5200)
  let gone = presence.get()
  assert.equal(gone.call, 'off', 'the call falls off within five seconds of the last beat')
  assert.notEqual(gone.source.status, 'relay', 'and the relay stops being named as a source')
  assert.equal(gone.levels.voice, 0, 'nothing coasts on a frame nobody renewed')

  // The listen-only mic tap closes behind it — it is only ever open on a live
  // call — and after that there is nothing left in this window to read at all.
  await env.pump(900)
  gone = presence.get()
  assert.equal(gone.source.mic, 'none', 'the microphone went with the call')
  assert.equal(gone.source.status, 'none', 'no beat → no relay → no reading')

  presence.stop()
})

test('a relay frame with no level says voice none, never bus', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env)
  presence.start()

  // The relay is up and reading Talk, but it found no <audio> to meter, so it
  // sent no voiceLevel. Nobody measured Agent's voice — say exactly that.
  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on' })
  await env.pump(300)

  const p = presence.get()
  assert.equal(p.source.status, 'relay', 'the mode did come across')
  assert.equal(p.source.voice, 'none', 'but no level did, and "bus" would be a claim')
  assert.equal(p.levels.voice, 0, 'an unmeasured level is zero, not a guess')

  presence.stop()
})

test('a local audio element outranks the level the relay sent', async () => {
  const env = makeEnv()
  const voice = fakeStream(0.8)
  env.setAudio(voice)                // Talk's <audio> IS reachable in this window
  const presence = loadPresence(env)
  presence.start()

  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on', voiceLevel: 0.02 })
  await env.pump(400)

  const p = presence.get()
  assert.equal(p.source.status, 'relay', 'the relay still decides the mode')
  assert.equal(p.source.voice, 'analyser', 'but the level is measured here, not carried')
  assert.ok(p.levels.voice > 0.4, `the nearer meter wins (got ${p.levels.voice})`)
  assert.equal(p.mode, 'speaking', 'and what this window hears upgrades a coarse "listening"')

  presence.stop()
})

test('a quiet call in the composer popover still takes a mute', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 100 })
  presence.start()

  // The other real mounting mode: TalkPage inside the composer popover, in THIS
  // window, announcing one live frame. Then seven and a half seconds of quiet.
  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(7500)

  const res = await presence.command('mute')
  assert.deepEqual(res, { ok: true, via: 'bus', reason: '' }, 'silence is not a hang-up')
  assert.deepEqual(env.commands, [{ action: 'mute' }], 'and it went out on this window\'s bus')

  // What DOES close the door: Talk reporting the call off. (The fresh-frame
  // window is five seconds wide, so the door is only really shut after it.)
  env.dispatchBus({ phase: 'idle', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(5200)
  const after = await presence.command('mute')
  assert.equal(after.ok, false, 'a frame saying "off" is what ends it')
  assert.equal(after.reason, 'no live call')
  assert.equal(env.commands.length, 1, 'and nothing more was sent')

  presence.stop()
})

test('start is re-sent up to three times, and stops the moment a call answers', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 200, startRetryMs: 60 })
  presence.start()

  const trigger = mountFloatingTrigger(env, {
    onClick: () => {
      env.relayBeat()
      env.relayFrame({ mode: 'thinking', call: 'connecting', phase: 'starting' })
    }
  })
  // The HUD window is still wiring Talk up and misses the first two starts.
  let sends = 0
  env.onRelayCommand = cmd => {
    if (cmd.action !== 'start') return
    sends += 1
    if (sends >= 3) env.relayFrame({ mode: 'listening', call: 'on', phase: 'active' })
  }

  const res = await presence.command('start')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'opened-then-relay')
  assert.equal(sends, 3, 'three sends — and not a fourth, because a frame answered')
  assert.equal(trigger.clicks.length, 1, 'the HUD is opened once, not once per retry')

  presence.stop()
})

test('a start nothing ever answers is reported, not claimed', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 200, startRetryMs: 60 })
  presence.start()

  mountFloatingTrigger(env, {
    onClick: () => {
      env.relayBeat()
      env.relayFrame({ mode: 'idle', call: 'off', phase: 'idle' })
    }
  })
  let sends = 0
  env.onRelayCommand = cmd => { if (cmd.action === 'start') sends += 1 }

  const res = await presence.command('start')
  assert.equal(res.ok, false, 'no frame reported a call, so no call is claimed')
  assert.equal(res.via, 'none')
  // §4.9 amendment 6: wherever the retries run out, the pod shows the
  // reworded Talk line 3 — the old door-shaped sentence is gone.
  assert.equal(res.reason, 'Talk is open but could not connect · read the message in Talk\'s panel',
    'and the reason is the line §4.8 ruling 3 wrote for exactly this case')
  assert.equal(sends, 3, 'it gave up after exactly three sends')

  presence.stop()
})


// ---- SPEC §4.8, the chat door ---------------------------------------------
//
// A window we can rearrange mid-press: the composer's Talk action can be
// absent and then appear (what navigation does), Talk's own view can already
// be mounted, and every click is taped so "which door did it try?" is a fact.
function mountWindow(env, { composer = false, titlebar = false, view = false } = {}) {
  const state = { composer, titlebar, view }
  const clicks = []
  const composerBtn = {
    tagName: 'BUTTON', className: '', textContent: 'Talk',
    getAttribute: name => (name === 'aria-label' ? 'Open Hermes Talk' : ''),
    click() { clicks.push('composer') }
  }
  const titlebarBtn = {
    tagName: 'BUTTON', className: '', textContent: '',
    getAttribute: name => (name === 'aria-label' ? 'Talk' : ''),
    click() { clicks.push('titlebar') }
  }
  const viewNode = {
    tagName: 'SECTION', className: 'ht-desktop-view',
    getAttribute: () => '', querySelector: () => null
  }
  env.document.querySelector = sel => {
    if (state.composer && /Open Hermes Talk/.test(sel)) return composerBtn
    if (state.titlebar && (sel === 'button[aria-label="Talk"]' || sel === '[aria-label="Talk"]')) return titlebarBtn
    if (state.view && sel === 'section.ht-desktop-view') return viewNode
    return null
  }
  env.document.querySelectorAll = sel => {
    if (sel === 'audio') return []
    if (/button/.test(sel)) {
      const out = []
      if (state.composer) out.push(composerBtn)
      if (state.titlebar) out.push(titlebarBtn)
      return out
    }
    return []
  }
  return { clicks, state }
}

function loadProbe(env) {
  const factory = new Function('window', 'document', 'navigator', `${PRELUDE}${SOURCE}\nreturn probeTalkDom;`)
  return factory(env.window, env.document, env.navigator)
}

test('with no composer, START asks the host for the focused chat and clicks THAT', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const paths = []
  const win = mountWindow(env, { titlebar: true })
  const presence = loadPresence(env, {
    commandWaitMs: 120,
    navWaitMs: 400,
    // The host brings the chat forward; its composer — and Talk's action with
    // it — mounts a moment later.
    navigate: path => { paths.push(path); win.state.composer = true },
    focusedSession: () => 'sess-42'
  })
  presence.start()

  await presence.command('start')
  assert.deepEqual(paths, ['/sess-42'], 'the focused stored session is the route')
  assert.deepEqual(win.clicks, ['composer'], 'the composer action is clicked — never the title-bar tool')

  presence.stop()
})

test('with no focused session, START asks for the new-chat route', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const paths = []
  const win = mountWindow(env, { titlebar: true })
  const presence = loadPresence(env, {
    commandWaitMs: 120,
    navWaitMs: 400,
    navigate: path => { paths.push(path); win.state.composer = true },
    focusedSession: () => ''
  })
  presence.start()

  await presence.command('start')
  assert.deepEqual(paths, ['/'], 'no focused session → the new chat')
  assert.deepEqual(win.clicks, ['composer'], 'and the composer action is what gets pressed')

  presence.stop()
})

test('the three §4.8 failure lines are the ones the pod shows, verbatim', async () => {
  // 1. Navigation brought no composer: no chat is open.
  const one = makeEnv()
  one.setAudio(null)
  const winOne = mountWindow(one, { titlebar: true })
  const first = loadPresence(one, {
    commandWaitMs: 100, navWaitMs: 150, navigate: () => {}, focusedSession: () => ''
  })
  first.start()
  const noChat = await first.command('start')
  assert.equal(noChat.reason, 'No chat is open · open a chat with Agent, then press START TALK')
  assert.deepEqual(winOne.clicks, ['titlebar'], 'the last door was still tried before giving up')
  first.stop()

  // 2. The composer action was clicked and Talk never opened.
  const two = makeEnv()
  two.setAudio(null)
  const winTwo = mountWindow(two, { composer: true })
  const second = loadPresence(two, { commandWaitMs: 100, navWaitMs: 100 })
  second.start()
  const noTalk = await second.command('start')
  assert.deepEqual(winTwo.clicks, ['composer'])
  assert.equal(noTalk.reason, 'Talk did not open · press the Talk button beside the message box once')
  second.stop()

  // 3. Talk's view is right there, three starts went out, no call answered.
  const three = makeEnv()
  three.setAudio(null)
  const winThree = mountWindow(three, { view: true })
  const third = loadPresence(three, { commandWaitMs: 100, navWaitMs: 100, startRetryMs: 40 })
  third.start()
  const noCall = await third.command('start')
  assert.equal(noCall.reason, 'Talk is open but could not connect · read the message in Talk\'s panel')
  assert.equal(three.commands.length, 3, 'three sends, then the truth')
  assert.deepEqual(winThree.clicks, [], 'and nothing was clicked: the view was already the door')
  third.stop()
})

test("Talk's view in this window is an open door: start goes out with no waiting", async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { view: true, titlebar: true })
  // Talk answers the way it really does: one frame, on the change.
  env.onCommand = cmd => {
    if (cmd.action === 'start') {
      env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
    }
  }
  const presence = loadPresence(env, { commandWaitMs: 4000, navWaitMs: 4000, startRetryMs: 60 })
  presence.start()

  const began = Date.now()
  const res = await presence.command('start')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'opened-then-bus', 'the bus was the door')
  assert.deepEqual(env.commands, [{ action: 'start' }], 'exactly one start, sent straight away')
  assert.deepEqual(win.clicks, [], 'no trigger was clicked: Talk is already mounted here')
  assert.ok(Date.now() - began < 1000, 'and it never waited out the 4 s door budget')

  presence.stop()
})

test('the probe skips Jarvis\'s own buttons and records route, session and gateway', () => {
  const env = makeEnv()
  const overlay = { tagName: 'DIV', className: 'jv-overlay', parentElement: null, parentNode: null, getAttribute: () => null }
  const ours = ['START TALK', 'MUTE'].map(text => ({
    tagName: 'BUTTON', className: 'jv-vbtn', textContent: text,
    parentElement: overlay, parentNode: overlay, getAttribute: () => null
  }))
  const theirs = {
    tagName: 'BUTTON', className: '', textContent: '', parentElement: null, parentNode: null,
    getAttribute: name => (name === 'aria-label' ? 'Talk' : null)
  }
  env.document.querySelector = sel => (/\[aria-label="Talk"\]/.test(sel) ? theirs : null)
  env.document.querySelectorAll = sel => (sel === 'audio' ? [] : /button/.test(sel) ? ours.concat([theirs]) : [])

  const probeTalkDom = loadProbe(env)
  const probe = probeTalkDom(env.document, {
    win: { location: { hash: '#/sess-42' } },
    focusedSession: true,
    gateway: 'open'
  })

  assert.equal(probe.buttons, 1, 'our three-button pod is not part of the window\'s button count')
  assert.equal(probe.candidates.length, 1, 'and START TALK / MUTE are not talk-named candidates')
  assert.equal(probe.candidates[0].ariaLabel, 'Talk', 'the real title-bar tool is')
  assert.equal(probe.composer, null, 'no composer door in this window')
  assert.equal(probe.route, '#/sess-42', 'the route rides along')
  assert.equal(probe.focusedSession, true, 'so does whether a session is focused')
  assert.equal(probe.gateway, 'open', 'and the gateway state')
})

test('the local bus door closes when Talk\'s view leaves this window', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { view: true })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100 })
  presence.start()

  // Talk is mounted here and says so once: the local door is open.
  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(300)
  assert.equal(presence.canCommand(), true, 'a door is open, so a press can be delivered')

  // Talk's view leaves the document (the popover closed, the page changed).
  win.state.view = false
  await env.pump(5400)                 // past the 5 s fresh-frame window too

  const res = await presence.command('mute')
  assert.equal(res.ok, false, 'the view is gone, so the door went with it')
  assert.equal(res.reason, 'no live call')
  assert.equal(presence.canCommand(), false, 'and the overlay greys MUTE again')
  assert.deepEqual(env.commands, [], 'nothing was dispatched into an empty window')

  presence.stop()
})

test('canCommand() follows the door, not the snapshot', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env)
  presence.start()

  assert.equal(presence.canCommand(), false, 'nothing open, nothing to press')

  // A relay beating in the floating HUD with a live call: this window's
  // snapshot can read call off between frames, but the door is open.
  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on' })
  await env.pump(200)
  assert.equal(presence.canCommand(), true, 'the relay is usable → MUTE and SLEEP are live')

  presence.stop()
})


// ---- SPEC §4.9, the native voice door ---------------------------------------
//
// Hermes Desktop's OWN voice chat, the one in the composer. A round button
// starts it; while a call runs the composer shows the conversation pill — a
// mute toggle carrying aria-pressed, an End button, and a screen-reader
// [role="status"] with the word (app/chat/composer/controls.tsx). Every label
// below is the English string the host renders (i18n/en.ts, composer block).
//
// The mount DELEGATES to whatever querySelector was there before it, so a test
// can stack Talk's doors and the host's voice controls in one document and
// watch which one a press actually chooses.
function mountNative(env, options = {}) {
  const state = {
    call: options.call === true,
    pill: options.pill === undefined ? 'Listening' : options.pill,
    muted: options.muted === true,
    start: options.start !== false,
    folded: options.folded === true,
    // §4.9 amendment 5: the composer is here and the host is showing Send or
    // Stop in the round button's seat (a draft in the box, a turn running).
    hidden: options.hidden === true,
    hiddenLabel: options.hiddenLabel === undefined ? 'Send' : options.hiddenLabel,
    // §4.9 second amendment 4: a DISABLED Send on an empty box is the host at
    // rest, not a host hiding its voice button.
    hiddenDisabled: options.hiddenDisabled === true,
    // §4.9 amendment 2: the hub's label is whatever the mic is doing.
    hubLabel: options.hubLabel === undefined ? 'Voice' : options.hubLabel,
    // Which door the fake Radix trigger actually answers to. The real one has
    // NO click handler at all, so 'click' is deliberately not an option.
    hubOpensOn: options.hubOpensOn === undefined ? 'pointerdown' : options.hubOpensOn,
    // How the hub can be found: by the Radix attribute, by the old exact
    // label selectors, or both (the live host offers both).
    hubVia: options.hubVia === undefined ? 'both' : options.hubVia,
    menuOpen: false,
    openedBy: '',
    closedBy: '',
    startsCall: options.startsCall === true
  }
  const clicks = []
  const events = []
  const keys = []          // every key dispatched at the folded hub, in order
  const beneath = env.document.querySelector
  const beneathAll = env.document.querySelectorAll
  // The sr-only status word lives inside the pill, beside the End button.
  const status = { tagName: 'SPAN', get textContent() { return state.pill } }
  const pillRoot = {
    tagName: 'DIV', className: 'composer-pill', parentElement: null, parentNode: null,
    querySelector: sel => (sel === '[role="status"]' ? status : null)
  }
  // The host's control row, the thing the store's composer walk actually
  // reads: `gap-(--composer-control-gap)` carries the word "composer".
  const composerRow = {
    tagName: 'DIV', className: 'ml-auto flex items-center gap-(--composer-control-gap)',
    parentElement: null, parentNode: null
  }
  const button = (id, label, opts = {}) => ({
    tagName: 'BUTTON', className: '', textContent: opts.text || '',
    parentElement: opts.parent || null, parentNode: opts.parent || null,
    getAttribute(name) {
      if (name === 'aria-label') return label
      if (opts.attrs && typeof opts.attrs[name] === 'function') return opts.attrs[name]()
      return opts.attrs && name in opts.attrs ? opts.attrs[name] : null
    },
    // A real element answers `closest` for its own selector; the End watch of
    // §4.10 amendment 4 asks exactly that.
    closest(sel) { return sel.indexOf('"' + label + '"') >= 0 ? this : null },
    click() { clicks.push(id); if (opts.onClick) opts.onClick() }
  })
  const endBtn = button('end', 'End voice conversation', {
    parent: pillRoot, onClick: () => { state.call = false }
  })
  const muteBtn = button('mute', 'Mute microphone', {
    parent: pillRoot, attrs: { 'aria-pressed': () => String(state.muted) },
    onClick: () => { state.muted = true }
  })
  const unmuteBtn = button('unmute', 'Unmute microphone', {
    parent: pillRoot, attrs: { 'aria-pressed': () => String(state.muted) },
    onClick: () => { state.muted = false }
  })
  const startBtn = button('start', 'Start voice conversation', {
    onClick: () => { if (state.startsCall) state.call = true }
  })
  // The FOLDED voice hub, as Radix actually renders it (§4.9 amendment 2):
  // it toggles on pointerdown (button 0, ctrlKey false) and on keydown, and
  // it has NO click handler — `.click()` on it does nothing at all.
  const openHub = how => {
    if (state.menuOpen) return
    state.menuOpen = true
    state.openedBy = how
    clicks.push('hub')
  }
  const hubBtn = {
    tagName: 'BUTTON', className: '', textContent: '',
    parentElement: composerRow, parentNode: composerRow,
    getAttribute(name) {
      if (name === 'aria-label') return state.hubLabel
      if (name === 'aria-haspopup') return 'menu'
      return null
    },
    focus() { events.push('hub-focus') },
    dispatchEvent(event) {
      events.push('hub-' + (event && event.type))
      if (!event) return true
      if (event.type === 'keydown') {
        keys.push(event.key)
        // Radix closes on Escape, and so does this stand-in.
        if (event.key === 'Escape') { state.menuOpen = false; state.closedBy = 'Escape' }
      }
      if (event.type === 'pointerdown' && state.hubOpensOn === 'pointerdown' &&
          event.button === 0 && event.ctrlKey === false) openHub('pointerdown')
      if (event.type === 'keydown' && (event.key === 'Enter' || event.key === ' ')) openHub('keydown')
      return true
    },
    // Taped in `events`, never in `clicks`: a click here changes nothing.
    click() { events.push('hub-click') }
  }
  // The composer's primary control while the round button is hidden.
  const submitBtn = {
    tagName: 'BUTTON', className: '', textContent: '',
    parentElement: composerRow, parentNode: composerRow,
    get disabled() { return state.hiddenDisabled },
    getAttribute(name) {
      if (name === 'aria-label') return state.hiddenLabel
      if (name === 'type') return 'submit'
      return null
    },
    click() { clicks.push('submit') }
  }
  const menuRow = {
    tagName: 'DIV', className: '', textContent: 'Start voice conversation',
    parentElement: null, parentNode: null,
    getAttribute: name => (name === 'role' ? 'menuitem' : null),
    click() { clicks.push('menu-start'); if (state.startsCall) state.call = true }
  }

  env.document.querySelector = sel => {
    if (state.call) {
      if (/End voice conversation/.test(sel)) return endBtn
      if (/"Mute microphone"/.test(sel)) return state.muted ? null : muteBtn
      if (/"Unmute microphone"/.test(sel)) return state.muted ? unmuteBtn : null
    }
    if (!state.call && state.start) {
      if (!state.folded && /"Start voice conversation"/.test(sel)) return startBtn
      if (state.folded && state.hubVia !== 'attribute' &&
          /aria-haspopup="menu"/.test(sel) && /\[aria-label="Voice"\]/.test(sel)) return hubBtn
    }
    if (!state.call && state.hidden && new RegExp('"' + state.hiddenLabel + '"').test(sel)) return submitBtn
    return beneath ? beneath(sel) : null
  }
  env.document.querySelectorAll = sel => {
    if (sel === '[role="menuitem"]') return state.menuOpen ? [menuRow] : []
    if (sel === '[aria-haspopup="menu"]') {
      return !state.call && state.start && state.folded && state.hubVia !== 'label' ? [hubBtn] : []
    }
    return beneathAll ? beneathAll(sel) : []
  }
  return { state, clicks, events, keys, nodes: { endBtn, muteBtn, unmuteBtn, startBtn, hubBtn, submitBtn } }
}

const sleep = ms => new Promise(r => setTimeout(r, ms))

/** A window whose `new Audio()` can be wrapped, with the two prototypes a real
 *  browser has: HTMLAudioElement and the Audio factory that extends it. */
function fakeAudioWindow(extra = {}) {
  class FakeHTMLAudioElement {
    constructor() { this.srcObject = null; this.paused = false }
  }
  class FakeAudio extends FakeHTMLAudioElement {
    constructor(src) { super(); this.src = src === undefined ? '' : src }
  }
  FakeAudio.KEEPSAKE = 'static property'
  const cells = new Map()
  const win = {
    Audio: FakeAudio,
    HTMLAudioElement: FakeHTMLAudioElement,
    WeakRef: typeof WeakRef === 'function' ? WeakRef : undefined,
    localStorage: {
      getItem: k => (cells.has(k) ? cells.get(k) : null),
      setItem: (k, v) => { cells.set(k, String(v)) },
      removeItem: k => { cells.delete(k) }
    },
    ...extra
  }
  return { win, FakeAudio, FakeHTMLAudioElement, cells }
}

function loadTap(env) {
  const factory = new Function('window', 'document', 'navigator', `${PRELUDE}${SOURCE}\nreturn installJarvisAudioTap;`)
  return factory(env.window, env.document, env.navigator)
}

test('the native voice: an End control is a live call, and the pill is the mode', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Listening' })
  const presence = loadPresence(env)
  presence.start()

  await env.pump(300)
  let p = presence.get()
  assert.equal(p.source.status, 'native', 'the composer pill is a source of its own')
  assert.equal(p.call, 'on', 'an End control means a call is running')
  assert.equal(p.mode, 'listening')

  const words = [['Speaking', 'speaking'], ['Thinking', 'thinking'], ['Transcribing', 'thinking'], ['Muted', 'muted'], ['Listening', 'listening']]
  for (const [word, mode] of words) {
    native.state.pill = word
    await env.pump(300)
    assert.equal(presence.get().mode, mode, `the pill said ${word}`)
  }

  // The mute button reports its own state; a plain "Listening" yields to it.
  native.state.muted = true
  await env.pump(300)
  assert.equal(presence.get().mode, 'muted', 'aria-pressed on the mic button is a muted call')
  native.state.muted = false

  // A word we do not know is SHOWN, never guessed at (§4.9 ruling 1).
  native.state.pill = 'Reconnecting…'
  await env.pump(300)
  p = presence.get()
  assert.equal(p.mode, 'listening', 'an unknown label falls back to listening')
  assert.equal(p.live, 'Reconnecting…', 'and the raw text rides under the big word')

  // The pill leaves: no End control, no call.
  native.state.call = false
  await env.pump(300)
  assert.equal(presence.get().call, 'off')
  assert.notEqual(presence.get().source.status, 'native')

  presence.stop()
})

test('the sources rank bus > relay > native > dom > derived', async () => {
  const env = makeEnv()
  const voice = fakeStream(0.8)
  env.setAudio(voice)                         // 5: Talk's own <audio> element
  const talk = { hud: false }
  const hudNode = {
    tagName: 'SECTION', className: 'ht-hud',
    getAttribute: name => (name === 'data-active' ? 'true' : ''),
    querySelector: () => null
  }
  const statusNode = { textContent: 'Audio playing' }
  const beneath = env.document.querySelector
  env.document.querySelector = sel => {
    if (talk.hud && sel === 'section.ht-hud') return hudNode
    if (talk.hud && sel === '#hermes-talk-hud-status') return statusNode
    return beneath ? beneath(sel) : null
  }
  const native = mountNative(env, { call: false, pill: 'Speaking' })
  const presence = loadPresence(env)
  presence.start()

  await env.pump(300)
  assert.equal(presence.get().source.status, 'derived', 'an analyser and nothing else')

  talk.hud = true
  await env.pump(300)
  assert.equal(presence.get().source.status, 'dom', 'Talk\'s own markup beats the analyser')

  native.state.call = true
  await env.pump(300)
  assert.equal(presence.get().source.status, 'native', 'a first-hand pill beats Talk\'s markup')

  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on' })
  await env.pump(200)
  assert.equal(presence.get().source.status, 'relay', 'the HUD relay beats the pill')

  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(100)
  assert.equal(presence.get().source.status, 'bus', 'and Talk itself beats everything')

  presence.stop()
})

test('START presses the built-in voice button before any Talk door', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true, titlebar: true })
  const native = mountNative(env, { call: false, startsCall: true })
  const presence = loadPresence(env, { commandWaitMs: 200, navWaitMs: 200, nativeWaitMs: 400 })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native', 'the host\'s own voice answered')
  assert.deepEqual(native.clicks, ['start'], 'the round button was the one press')
  assert.deepEqual(win.clicks, [], 'and no Talk door was touched at all')
  assert.deepEqual(env.commands, [], 'nothing went out on Talk\'s bus either')

  presence.stop()
})

// §4.9 amendment 2 — the fake here opens ONLY on pointerdown or keydown, the
// way Radix's DropdownMenuTrigger does. The first build pressed the hub with
// `.click()`, which a click-driven fake answered and the live host ignored:
// the tests passed on a door that could never open.
test('the folded Voice hub opens on a real pointer press, never on .click()', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true })
  const native = mountNative(env, { call: false, folded: true, startsCall: true, hubVia: 'label' })
  const presence = loadPresence(env, { commandWaitMs: 200, navWaitMs: 200, nativeWaitMs: 400 })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native')
  assert.deepEqual(native.clicks, ['hub', 'menu-start'], 'the hub, then the row inside it')
  assert.equal(native.state.openedBy, 'pointerdown', 'and pointerdown is what opened it')
  assert.equal(native.events[0], 'hub-pointerdown', 'the sequence starts where Radix listens')
  assert.ok(native.events.includes('hub-pointerup'), 'and finishes the press honestly')
  assert.deepEqual(win.clicks, [], 'the Talk door stayed shut')

  presence.stop()
})

// §4.9 amendment 2 — the trigger is found by its Radix attribute inside the
// composer, because its LABEL becomes the wake-word sentence (voice-menu.tsx:78)
// exactly when Owner is using his voice. And when the pointer sequence is
// ignored, Enter on the focused trigger is the fallback.
test('the hub is found by its attribute under a wake-word label, and Enter is the fallback', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, {
    call: false, folded: true, startsCall: true, hubVia: 'attribute',
    hubLabel: 'Wake word: "hey hermes" — listening',
    hubOpensOn: 'keydown'
  })
  const presence = loadPresence(env, { nativeWaitMs: 400, nativeMenuOpenMs: 120 })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.via, 'native', 'a label we could never have guessed still found the trigger')
  assert.deepEqual(native.clicks, ['hub', 'menu-start'])
  assert.equal(native.state.openedBy, 'keydown', 'the pointer press was ignored, so Enter went out')
  assert.ok(native.events.includes('hub-focus'), 'and the trigger was focused before the key')

  presence.stop()
})

// §4.9 amendment 2 — the dictation fan (aria-haspopup="true") is NOT the hub.
test('a dictation fan hub is never pressed in the voice hub\'s place', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const fanClicks = []
  const fan = {
    tagName: 'BUTTON', className: 'gap-(--composer-control-gap)',
    parentElement: null, parentNode: null,
    getAttribute: name => (name === 'aria-label' ? 'Voice' : name === 'aria-haspopup' ? 'true' : null),
    dispatchEvent: () => { fanClicks.push('fan'); return true },
    click() { fanClicks.push('fan') }
  }
  const beneathAll = env.document.querySelectorAll
  env.document.querySelectorAll = sel => (sel === '[aria-haspopup="menu"]' ? [] : beneathAll(sel))
  const native = mountNative(env, { call: false, start: false })
  void native
  const presence = loadPresence(env, { commandWaitMs: 80, navWaitMs: 80 })
  presence.start()

  await presence.command('start')
  assert.deepEqual(fanClicks, [], 'the fan toggles dictation — it is not a door into a conversation')

  presence.stop()
})

test('with no built-in voice button, START falls back to Talk\'s doors', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true })
  const native = mountNative(env, { call: false, start: false })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100 })
  presence.start()

  await presence.command('start')
  assert.deepEqual(native.clicks, [], 'there was nothing native to press')
  assert.deepEqual(win.clicks, ['composer'], 'so §4.8 took over exactly as before')

  presence.stop()
})

test('with the built-in voice on the line, the commands press its own controls', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Listening' })
  const presence = loadPresence(env)
  presence.start()
  await env.pump(300)

  let res = await presence.command('mute')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native')
  await env.pump(300)
  assert.equal(presence.get().mode, 'muted', 'and the host reports the mute back')

  res = await presence.command('unmute')
  assert.equal(res.via, 'native')
  assert.deepEqual(native.clicks, ['mute', 'unmute'], 'each press hit the label that was on screen')

  // §4.9 ruling 3: sleep and wake belong to Talk, and the refusal is the exact
  // line the overlay puts on the greyed button.
  for (const action of ['sleep', 'wake']) {
    const refused = await presence.command(action)
    assert.equal(refused.ok, false)
    assert.equal(refused.via, 'none')
    assert.equal(refused.reason, 'built-in voice has no sleep')
  }

  res = await presence.command('stop')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native')
  assert.deepEqual(native.clicks, ['mute', 'unmute', 'end'], 'END pressed End voice conversation')
  assert.deepEqual(env.commands, [], 'Talk\'s bus was never used for any of it')

  presence.stop()
})

test('the §4.9 plain lines are the ones the pod shows, verbatim', async () => {
  // 1. The built-in voice was pressed and no pill ever appeared.
  const one = makeEnv()
  one.setAudio(null)
  const native = mountNative(one, { call: false, startsCall: false })
  const first = loadPresence(one, { nativeWaitMs: 120 })
  first.start()
  const noVoice = await first.command('start')
  assert.deepEqual(native.clicks, ['start'])
  assert.equal(noVoice.reason, 'Voice did not start · press the round voice button beside the message box once')
  first.stop()

  // 2. Talk's view is here, three starts went out, nothing connected.
  const two = makeEnv()
  two.setAudio(null)
  const win = mountWindow(two, { view: true })
  const second = loadPresence(two, { commandWaitMs: 100, navWaitMs: 100, startRetryMs: 40 })
  second.start()
  const noCall = await second.command('start')
  assert.equal(noCall.reason, 'Talk is open but could not connect · read the message in Talk\'s panel')
  assert.deepEqual(win.clicks, [], 'the view was already the door')
  second.stop()
})

test('the audio tap hands the host back exactly what it asked for', () => {
  const env = makeEnv()
  const installJarvisAudioTap = loadTap(env)
  const { win, FakeAudio, FakeHTMLAudioElement } = fakeAudioWindow()

  const tap = installJarvisAudioTap(win, () => SCOPE)
  assert.equal(tap.wrapped, true, 'window.Audio is wrapped')
  assert.notEqual(win.Audio, FakeAudio, 'by a proxy, not by the original')

  const el = new win.Audio('agent.mp3')
  assert.equal(Object.getPrototypeOf(el), FakeAudio.prototype, 'same prototype')
  assert.ok(el instanceof FakeAudio, 'instanceof Audio')
  assert.ok(el instanceof FakeHTMLAudioElement, 'instanceof HTMLAudioElement')
  assert.ok(el instanceof win.Audio, 'and instanceof the wrapper too')
  assert.equal(el.src, 'agent.mp3', 'the constructor argument went through untouched')
  assert.equal(win.Audio.KEEPSAKE, 'static property', 'static properties still read through')

  assert.deepEqual(tap.elements(), [el], 'and we kept a reference to it')
  assert.equal(tap.seen(), 1)

  tap.restore()
  assert.equal(win.Audio, FakeAudio, 'dispose puts the original constructor back')
  const after = new win.Audio()
  assert.ok(after instanceof FakeAudio, 'which still builds elements the same way')
  assert.deepEqual(tap.elements(), [], 'and nothing is held after a restore')
})

test('the audio tap kill switch is honoured before anything is wrapped', () => {
  const env = makeEnv()
  const installJarvisAudioTap = loadTap(env)
  const { win, FakeAudio } = fakeAudioWindow()
  win.localStorage.setItem('hermes-jarvis:test-scope:no-audio-tap', '1')

  const tap = installJarvisAudioTap(win, () => SCOPE)
  assert.equal(tap.wrapped, false, 'the switch means no wrapper at all')
  assert.equal(win.Audio, FakeAudio, 'window.Audio was never touched')
  const el = new win.Audio()
  assert.ok(el instanceof FakeAudio)
  assert.deepEqual(tap.elements(), [], 'and nothing is recorded')
  assert.equal(tap.seen(), 0)
})

test('a failure in OUR bookkeeping never reaches the host', () => {
  const env = makeEnv()
  const installJarvisAudioTap = loadTap(env)
  const { win, FakeAudio } = fakeAudioWindow({
    WeakRef: function BrokenWeakRef() { throw new Error('no weak refs today') }
  })

  const tap = installJarvisAudioTap(win, () => SCOPE)
  assert.equal(tap.wrapped, true)
  const el = new win.Audio('still-works.mp3')   // must not throw
  assert.ok(el instanceof FakeAudio, 'the host got its element')
  assert.equal(el.src, 'still-works.mp3')
  assert.deepEqual(tap.elements(), [], 'we simply have no reference to show for it')
  tap.restore()
})

test('metering takes the MediaStream, else captureStream, and NEVER the element', async () => {
  const env = makeEnv()
  env.setAudio(null)
  mountNative(env, { call: true, pill: 'Speaking' })

  // 1. A detached element with a MediaStream srcObject: straight into
  //    createMediaStreamSource, the way GPT-Live plays Agent.
  const streamed = { srcObject: fakeStream(0.8), paused: false }
  const presence = loadPresence(env, {
    audioTap: { wrapped: true, seen: () => 1, elements: () => [streamed] }
  })
  presence.start()
  await env.pump(400)
  let p = presence.get()
  assert.equal(p.source.voice, 'native-analyser', 'the level came from our own analyser')
  assert.ok(p.levels.voice > 0.06, 'and it is Agent mid-word')
  assert.equal(env.mediaElementSourceCount(), 0, 'createMediaElementSource was never called')
  presence.stop()

  // 2. No srcObject: captureStream() is the only honest door left.
  const captured = { srcObject: null, paused: false, captureStream: () => fakeStream(0.5) }
  const second = loadPresence(env, {
    audioTap: { wrapped: true, seen: () => 1, elements: () => [captured] }
  })
  second.start()
  await env.pump(400)
  p = second.get()
  assert.equal(p.source.voice, 'native-analyser')
  assert.ok(p.levels.voice > 0.06)
  assert.equal(env.mediaElementSourceCount(), 0, 'still never the element source')
  second.stop()
})

test('nothing to tap is an honest zero — the orb still changes mode', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Speaking' })
  const presence = loadPresence(env, {
    audioTap: { wrapped: true, seen: () => 0, elements: () => [] }
  })
  presence.start()
  await env.pump(400)

  const p = presence.get()
  assert.equal(p.source.status, 'native')
  assert.equal(p.source.voice, 'none', 'no element, no analyser, no claim')
  assert.equal(p.levels.voice, 0, 'and the level is zero, not a guess')
  assert.equal(p.mode, 'speaking', 'but the mode the host reported is still shown')
  assert.equal(presence.audioTap().metering, false, 'and the receipt says we are not metering')

  native.state.pill = 'Listening'
  await env.pump(300)
  assert.equal(presence.get().mode, 'listening', 'the orb follows the pill either way')

  presence.stop()
})

test('the probe carries the built-in voice and the audio tap', () => {
  const env = makeEnv()
  mountNative(env, { call: true, pill: 'Speaking' })
  const probeTalkDom = loadProbe(env)

  const probe = probeTalkDom(env.document, { audioTap: { wrapped: true, seen: 3, metering: true } })
  assert.deepEqual(probe.native, { start: false, end: true, mute: true, pill: 'Speaking' },
    'what the composer showed, word for word')
  assert.deepEqual(probe.audioTap, { wrapped: true, seen: 3, metering: true })

  // Told nothing about the tap, it claims nothing about the tap.
  const quiet = probeTalkDom(env.document, {})
  assert.deepEqual(quiet.audioTap, { wrapped: false, seen: 0, metering: false })
})

// ---- SPEC §4.9 amendments (the Fable native-voice judge, 2026-09-19) -------

// Amendment 1 — MUTED WINS. The live failure: a muted call while Agent was
// speaking read `speaking`, so the listen-only mic tap opened on a microphone
// the host had already shut, and the overlay offered a MUTE whose button was
// not on screen ("the mute button is not on screen").
test('a muted call outranks the pill: mode muted, mic shut, UNMUTE is the press', async () => {
  const env = makeEnv()
  env.setAudio(null)
  env.micStream = fakeStream(0.8)
  const native = mountNative(env, { call: true, pill: 'Speaking', muted: true })
  const presence = loadPresence(env)
  presence.start()
  await env.pump(900)

  const p = presence.get()
  assert.equal(p.mode, 'muted', 'aria-pressed="true" beats the word "Speaking"')
  assert.equal(p.live, 'Speaking', 'and the pill\'s own word still rides the live line')
  assert.equal(p.source.mic, 'none', 'a muted call never opens the listen-only tap')
  assert.equal(env.micCallCount(), 0, 'getUserMedia was not even asked')

  // mode `muted` is what makes the overlay read UNMUTE, and the press lands on
  // the label the host actually has on screen.
  const res = await presence.command('unmute')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native')
  assert.deepEqual(native.clicks, ['unmute'], 'the button that was there is the one pressed')

  presence.stop()
})

// Amendment 3 — ONE CAPTURE PER ELEMENT. Before this, `captureStream()` ran on
// every tick: sixty calls a second on a playing element (the chained engine).
test('captureStream is called once per element, and dropped when the call ends', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Speaking' })
  let captures = 0
  const el = { srcObject: null, paused: false, captureStream() { captures += 1; return fakeStream(0.5) } }
  const presence = loadPresence(env, {
    audioTap: { wrapped: true, seen: () => 1, elements: () => [el] }
  })
  presence.start()

  await env.pump(1200)                       // ~75 ticks
  assert.equal(presence.get().source.voice, 'native-analyser', 'we are metering it')
  assert.equal(captures, 1, 'one capture for the whole call, not one per tick')

  native.state.call = false                  // the call ends
  await env.pump(400)
  assert.equal(presence.get().source.voice, 'none', 'nothing is metered with no call')

  native.state.call = true                   // a new call meters afresh
  await env.pump(400)
  assert.equal(captures, 2, 'the capture was dropped with the call, then taken once more')
  assert.equal(env.mediaElementSourceCount(), 0, 'and never through the element source')

  presence.stop()
})

// Amendment 4 — A QUIET RELAY NEVER OUTRANKS A LIVE CALL. The relay beats
// every two seconds whether or not Talk has a call; a frame saying `off` is
// the HUD reporting nothing to report, and it must not sit on top of a
// built-in call running right here.
test('a beating relay with the call off yields to a live built-in call', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Listening' })
  const presence = loadPresence(env)
  presence.start()

  env.relayBeat()
  env.relayFrame({ mode: 'idle', call: 'off', phase: 'idle' })
  await env.pump(300)
  assert.equal(presence.get().source.status, 'native', 'a relay with no call does not own the voice')
  assert.equal(presence.get().call, 'on', 'the call that is live is the one reported')

  const res = await presence.command('stop')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native', 'stop follows the source that is live')
  assert.deepEqual(native.clicks, ['end'], 'and presses End voice conversation')
  assert.equal(env.readCell('hermes-jarvis:test-scope:command'), null, 'nothing went to the relay')

  presence.stop()
})

test('a relay reporting a live call still outranks the built-in voice', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Listening' })
  const presence = loadPresence(env)
  presence.start()

  env.relayBeat()
  env.relayFrame({ mode: 'listening', call: 'on' })
  await env.pump(300)
  assert.equal(presence.get().source.status, 'relay', 'Talk in the HUD is still the higher door')

  const res = await presence.command('stop')
  assert.equal(res.via, 'relay', 'and the command goes across the wire, not to the composer')
  assert.deepEqual(native.clicks, [], 'the built-in controls were left alone')
  assert.equal(env.readCell('hermes-jarvis:test-scope:command').action, 'stop')

  presence.stop()
})

// Amendment 5 — TALK'S DOOR IS OPT-IN ON START.
test('a hidden round button is said plainly, and Talk\'s panel is never opened', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true, titlebar: true })
  const native = mountNative(env, { call: false, start: false, hidden: true })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100 })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, false)
  assert.equal(res.via, 'none')
  assert.equal(res.reason,
    'The voice button is hidden · clear the message box or wait for Agent to finish, then press START TALK',
    'the line §4.9 amendment 5 wrote, verbatim')
  assert.deepEqual(win.clicks, [], 'Talk was never opened — it cannot connect on this host')
  assert.deepEqual(native.clicks, [], 'and nothing else was pressed either')
  // §4.10 ruling 2: a DRAFT in the box is still a refusal — only Owner can
  // clear that, so there is nothing to wait for.
  assert.equal(presence.startWaiting(), false, 'an enabled Send is never waited out')

  presence.stop()
})

// §4.10 ruling 2 — A RUNNING TURN IS A WAIT, NOT A REFUSAL. Agent's own answer
// is what hid the round button (the 2026-09-19 16:31 drop: a 31.4 s delegated
// turn), and it comes back the moment he finishes.
test('Agent is answering: START says so, waits, and presses the button when it returns', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true })
  const native = mountNative(env, {
    call: false, start: false, hidden: true, hiddenLabel: 'Stop', startsCall: true
  })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 4000 })
  presence.start()

  const pending = presence.command('start')
  await new Promise(r => setTimeout(r, 30))
  assert.equal(presence.startWaiting(), true, 'the store is standing by, not answering')
  assert.equal(presence.notice(), 'Agent is answering · voice starts when he finishes',
    'the §4.10 line, verbatim')
  assert.deepEqual(native.clicks, [], 'nothing is pressed while Agent is still talking')

  // Agent finishes: the composer puts its round voice button back.
  native.state.hidden = false
  native.state.start = true

  const res = await pending
  assert.equal(res.ok, true, 'the call started the moment the button returned')
  assert.equal(res.via, 'native')
  assert.deepEqual(native.clicks, ['start'], 'and it is the built-in voice button that was pressed')
  assert.deepEqual(win.clicks, [], 'still no detour into Talk')
  assert.equal(presence.startWaiting(), false, 'the wait is over')

  presence.stop()
})

test('the wait for Agent is cancelled by T, and gives up at its budget with the hidden line', async () => {
  // CANCEL — the button reads it while the wait is on, and T presses it.
  const one = makeEnv()
  one.setAudio(null)
  const oneNative = mountNative(one, { call: false, start: false, hidden: true, hiddenLabel: 'Stop' })
  const first = loadPresence(one, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 4000 })
  first.start()
  const waiting = first.command('start')
  await new Promise(r => setTimeout(r, 30))
  assert.equal(first.cancelStart(), true, 'there was a wait to call off')
  const cancelled = await waiting
  assert.equal(cancelled.ok, false)
  assert.equal(cancelled.reason, 'Start cancelled · press START TALK when Agent is done')
  assert.equal(first.startWaiting(), false, 'and nothing is left waiting')
  assert.deepEqual(oneNative.clicks, [], 'a cancelled wait presses nothing')
  assert.equal(first.cancelStart(), false, 'a second cancel has nothing to cancel')
  first.stop()

  // The budget runs out with Agent still answering: the hidden line is the truth.
  const two = makeEnv()
  two.setAudio(null)
  const win = mountWindow(two, { composer: true })
  mountNative(two, { call: false, start: false, hidden: true, hiddenLabel: 'Stop' })
  const second = loadPresence(two, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 300 })
  second.start()
  const res = await second.command('start')
  assert.equal(res.reason,
    'The voice button is hidden · clear the message box or wait for Agent to finish, then press START TALK',
    'ninety seconds of Agent still answering ends on the hidden line')
  assert.deepEqual(win.clicks, [], 'and Talk is never opened for it')
  second.stop()
})

test('hermes-jarvis:voice-door = talk asks for Talk\'s doors on purpose', async () => {
  const env = makeEnv()
  env.setAudio(null)
  env.window.localStorage.setItem('hermes-jarvis:test-scope:voice-door', 'talk')
  const win = mountWindow(env, { composer: true })
  const native = mountNative(env, { call: false, startsCall: true })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100 })
  presence.start()

  await presence.command('start')
  assert.deepEqual(native.clicks, [], 'the built-in voice was left alone, as asked')
  assert.deepEqual(win.clicks, ['composer'], 'Talk\'s composer door is the one tried')

  presence.stop()
})

// Amendment 7 — ROUTE IDS ARE ENCODED, as the host encodes them (routes.ts:211).
test('the chat the host is asked for carries an encoded id', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const paths = []
  const win = mountWindow(env, { titlebar: true })
  const presence = loadPresence(env, {
    commandWaitMs: 120,
    navWaitMs: 300,
    navigate: path => { paths.push(path); win.state.composer = true },
    focusedSession: () => 'sess 42/beta'
  })
  presence.start()

  await presence.command('start')
  assert.deepEqual(paths, ['/sess%2042%2Fbeta'], 'encodeURIComponent, exactly as the host does')

  presence.stop()
})

// ---- SPEC §4.9 second amendments (the Fable native-voice RE-judge) ---------

// Second amendment 2 — A FINISHED ELEMENT LEAVES THE METER. The chained engine
// (`voice-playback.ts`) builds one `new Audio()` per sentence and leaves the
// finished ones in the list, so a cache hit that ignored `ended`/`paused` kept
// the meter on sentence one for the whole answer and pinned that element.
test('a finished player leaves the meter and the next one is picked up', async () => {
  const env = makeEnv()
  env.setAudio(null)
  mountNative(env, { call: true, pill: 'Speaking' })
  const counts = { one: 0, two: 0, idle: 0 }
  const player = (key, level) => ({
    srcObject: null, paused: false, ended: false,
    captureStream() { counts[key] += 1; return fakeStream(level) }
  })
  const one = player('one', 0.15)
  const two = player('two', 0.9)
  // A player that never starts: paused from the moment it was built.
  const idle = player('idle', 0.9)
  idle.paused = true
  let list = [one, idle]

  const presence = loadPresence(env, {
    audioTap: { wrapped: true, seen: () => list.length, elements: () => list.slice() }
  })
  presence.start()

  await env.pump(700)
  assert.equal(presence.get().source.voice, 'native-analyser', 'sentence one is being metered')
  assert.equal(counts.one, 1, 'one capture for it, not one per tick')
  assert.equal(counts.idle, 0, 'a paused element is never metered')
  const quiet = presence.get().levels.voice
  assert.ok(quiet < 0.3, 'and sentence one is the quiet one')

  // The sentence ends; the next one is already playing.
  one.ended = true
  one.paused = true
  list = [one, two, idle]
  await env.pump(700)
  assert.equal(counts.two, 1, 'the player that IS playing was captured, once')
  assert.equal(counts.one, 1, 'and the finished one was never captured again')
  assert.ok(presence.get().levels.voice > 0.5, 'the meter moved to the sentence being spoken')
  assert.equal(presence.audioTap().metering, true)

  // Everything has finished: nothing is metered and nothing is claimed.
  two.ended = true
  await env.pump(500)
  assert.equal(presence.get().source.voice, 'none', 'an ended element is never metered')
  assert.equal(presence.get().levels.voice, 0, 'the level is zero, not the last one we saw')
  assert.equal(presence.audioTap().metering, false, 'and the tap reference went with it')
  assert.equal(counts.one + counts.two + counts.idle, 2, 'exactly one captureStream per element')
  assert.equal(env.mediaElementSourceCount(), 0, 'never through the element source')

  presence.stop()
})

// Second amendment 3 — DEFAULT START NEVER WRITES TO TALK. A relay beating in a
// HUD window (or a Talk panel opened once in this one) used to swallow START
// before the chat door ever ran: `start` went to Talk, which cannot connect on
// this host, and the built-in voice was never pressed.
test('default START with no composer writes nothing to Talk: chat door, then the voice button', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const paths = []
  const win = mountWindow(env, { titlebar: true })
  const native = mountNative(env, { call: false, start: false, startsCall: true })
  const presence = loadPresence(env, {
    commandWaitMs: 200,
    navWaitMs: 600,
    nativeWaitMs: 400,
    // The host brings a chat forward; its composer arrives with the round
    // voice button on it.
    navigate: path => { paths.push(path); native.state.start = true },
    focusedSession: () => ''
  })
  presence.start()

  // Talk is mounted in this window (a panel opened once) and a HUD relay is
  // beating — neither has a call, and neither may take this START.
  env.dispatchBus({ phase: 'idle', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  env.relayBeat()
  env.relayFrame({ mode: 'idle', call: 'off', phase: 'idle' })
  await env.pump(100)

  const res = await presence.command('start')
  assert.equal(res.via, 'native', 'the built-in voice is the door START uses')
  assert.deepEqual(paths, ['/'], 'the chat door ran first')
  assert.deepEqual(native.clicks, ['start'], 'and the round button was the one press')
  assert.deepEqual(env.commands, [], 'nothing was dispatched on Talk\'s bus')
  assert.equal(env.readCell('hermes-jarvis:test-scope:command'), null, 'and nothing was written to the relay')
  assert.deepEqual(win.clicks, [], 'no Talk door was clicked either')

  presence.stop()
})

test('an already-live Talk call still takes its §4.6 commands', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const presence = loadPresence(env, { commandWaitMs: 200 })
  presence.start()

  env.dispatchBus({ phase: 'active', live: '', audioActivity: {}, transcript: [], muted: false, sleeping: false })
  await env.pump(100)

  const muted = await presence.command('mute')
  assert.equal(muted.via, 'bus', 'a live Talk call keeps §4.6 in full')
  const started = await presence.command('start')
  assert.equal(started.via, 'bus', 'and START on that live call still rides its bus')
  assert.deepEqual(env.commands, [{ action: 'mute' }, { action: 'start' }])

  presence.stop()
})

// Second amendment 4 — "HIDDEN" MEANS HIDDEN.
test('a disabled Send is not a hidden voice button: this host simply has none', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true })
  const native = mountNative(env, { call: false, start: false, hidden: true, hiddenDisabled: true })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100 })
  presence.start()

  const res = await presence.command('start')
  assert.notEqual(res.reason,
    'The voice button is hidden · clear the message box or wait for Agent to finish, then press START TALK',
    'an empty box with a greyed Send is hiding nothing')
  assert.deepEqual(win.clicks, ['composer'], 'no native control at all → Talk\'s doors apply (§4.9 amendment 5)')
  assert.deepEqual(native.clicks, [], 'and nothing native was pressed')

  presence.stop()
})

test('a Stop control still reads as hidden, disabled or not', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true })
  mountNative(env, {
    call: false, start: false, hidden: true, hiddenLabel: 'Stop', hiddenDisabled: true
  })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 300 })
  presence.start()

  const pending = presence.command('start')
  await new Promise(r => setTimeout(r, 30))
  // §4.10 ruling 2: a Stop means a turn is running, so this is the WAIT case.
  assert.equal(presence.notice(), 'Agent is answering · voice starts when he finishes',
    'a disabled Stop is still a running turn')
  const res = await pending
  assert.equal(res.reason,
    'The voice button is hidden · clear the message box or wait for Agent to finish, then press START TALK',
    'and when Agent never finishes, the hidden line is what is left')
  assert.deepEqual(win.clicks, [], 'and Talk is not opened for it')

  presence.stop()
})

// Second amendment 5 — THE ENGINE CHEVRON IS NOT THE VOICE MENU.
function mountEngineChevron(env) {
  const events = []
  const chevron = {
    tagName: 'BUTTON', className: 'gap-(--composer-control-gap)', textContent: '',
    parentElement: null, parentNode: null,
    getAttribute: name => (name === 'aria-label' ? 'Voice chat engine'
      : name === 'aria-haspopup' ? 'menu' : null),
    focus() { events.push('focus') },
    dispatchEvent(event) { events.push(event && event.type); return true },
    click() { events.push('click') }
  }
  const beneathAll = env.document.querySelectorAll
  env.document.querySelectorAll = sel => {
    if (sel === '[aria-haspopup="menu"]') {
      return [chevron].concat(beneathAll ? beneathAll(sel) : [])
    }
    return beneathAll ? beneathAll(sel) : []
  }
  return { events, chevron }
}

test('the engine chevron is never treated as the Voice menu', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const win = mountWindow(env, { composer: true })
  const native = mountNative(env, { call: false, start: false, hidden: true })
  const engine = mountEngineChevron(env)
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100, nativeMenuOpenMs: 60 })
  presence.start()

  // A folded composer with a draft in the box: the hidden line, and no menu.
  const res = await presence.command('start')
  assert.equal(res.reason,
    'The voice button is hidden · clear the message box or wait for Agent to finish, then press START TALK',
    'the draft is what to clear — the engine menu would start nothing')
  assert.deepEqual(engine.events, [], 'the chevron was never pressed')
  assert.deepEqual(native.clicks, [], 'and neither was anything else')
  assert.deepEqual(win.clicks, [], 'no detour into Talk')

  presence.stop()
})

test('a folded-menu attempt that reaches no call closes the menu it opened', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, {
    call: false, folded: true, startsCall: false, hubVia: 'attribute'
  })
  const presence = loadPresence(env, { nativeWaitMs: 150, nativeMenuOpenMs: 80 })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, false)
  assert.equal(res.reason,
    'Voice did not start · press the round voice button beside the message box once')
  assert.deepEqual(native.clicks, ['hub', 'menu-start'], 'the hub was opened and the row pressed')
  assert.ok(native.keys.includes('Escape'), 'and the menu Jarvis opened was closed again')
  assert.equal(native.state.menuOpen, false, 'no modal menu is left holding the page')
  assert.equal(native.state.closedBy, 'Escape')

  presence.stop()
})

// ---- SPEC §4.10: the draft-chat drop --------------------------------------
//
// A brand-new chat has no stored session. The host keys the composer voice's
// lifetime on that id, so the first delegated request saves the chat, bumps the
// epoch and ABORTS the call that was running — the 21-second drop of
// 2026-09-19 16:31. Ruling 1 saves the chat first.

/** A stand-in for the invisible composer contribution's controller, with the
 *  two readings the store asks for and a prepare that can be made to fail. */
function fakeController(options = {}) {
  const state = {
    present: options.present !== false,
    stored: options.stored === undefined ? '' : options.stored,
    canPrepare: options.canPrepare !== false
  }
  const calls = []
  return {
    state,
    calls,
    info: () => ({ present: state.present, stored: state.stored, canPrepare: state.canPrepare }),
    prepare(at, onPrepare) {
      calls.push(at)
      return onPrepare ? onPrepare() : Promise.resolve({ ok: true, reason: '' })
    }
  }
}

test('a draft chat is prepared BEFORE the voice button is pressed, and the settle is waited out', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: '' })
  let focused = ''
  const order = []
  let savedAt = 0
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    prepareWaitMs: 1000,
    settleWaitMs: 1000,
    controllerInfo: ctrl.info,
    prepareChat: () => {
      order.push('prepare')
      // The host saves the chat a moment later — which is exactly what the
      // settle wait is for: the composer must be back with a focused session
      // before the button is pressed.
      setTimeout(() => {
        savedAt = Date.now()
        focused = 'sess-new'
        ctrl.state.stored = 'sess-new'
      }, 120)
      return Promise.resolve({ ok: true, reason: '' })
    },
    focusedSession: () => focused
  })
  presence.start()

  const res = await presence.command('start')
  const pressedAt = Date.now()
  assert.deepEqual(order, ['prepare'], 'the chat was prepared')
  assert.deepEqual(native.clicks, ['start'], 'and then the voice button was pressed')
  assert.ok(savedAt > 0 && pressedAt >= savedAt,
    'the press waited for the composer to settle around the saved chat')
  assert.equal(res.ok, true)
  assert.equal(res.via, 'native')

  await env.pump(400)
  assert.equal(presence.get().notice, '', 'a prepared chat carries no warning')

  presence.stop()
})

// §4.10 amendment 3 — a REJECTED prepare is the one that presses anyway. A slow
// one is waited out (the two tests below it); racing the host's own save is what
// dropped the call on 2026-09-19.
test('a prepare the host REFUSES still presses the button, and the pod warns while the call is on', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: '' })
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    prepareWaitMs: 200,
    prepareMaxMs: 600,
    settleWaitMs: 200,
    controllerInfo: ctrl.info,
    // The host answered, and the answer was no.
    prepareChat: () => Promise.resolve({ ok: false, reason: 'the host prepared no stored session' }),
    focusedSession: () => ''
  })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, true, 'START still starts the call')
  assert.deepEqual(native.clicks, ['start'], 'the button was pressed anyway')

  await env.pump(400)
  assert.equal(presence.get().notice,
    'New chat · the call may drop when Agent\'s first answer starts',
    'and the pod says what may happen, in the §4.10 words')

  // The call ends — the warning goes with it.
  native.state.call = false
  await env.pump(400)
  assert.notEqual(presence.get().notice,
    'New chat · the call may drop when Agent\'s first answer starts',
    'the warning belongs to the live call, not to the pod forever')

  presence.stop()
})

test('a saved chat is never prepared: there is nothing to save', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: 'sess-42' })
  let prepares = 0
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    controllerInfo: ctrl.info,
    prepareChat: () => { prepares += 1; return Promise.resolve({ ok: true, reason: '' }) },
    focusedSession: () => 'sess-42'
  })
  presence.start()

  const res = await presence.command('start')
  assert.equal(prepares, 0, 'a chat that is already saved is left alone')
  assert.deepEqual(native.clicks, ['start'])
  assert.equal(res.ok, true)

  await env.pump(300)
  assert.equal(presence.get().notice, '', 'and nothing is warned about')

  presence.stop()
})

// §4.10 ruling 3, as §8 amendment C1 left it — A CALL THAT ENDS ON ITS OWN IS
// NAMED ONCE, and the pod is not where it is named. The store writes the end
// down (`lastCallEnd`, and the receipt's `callEnds`) and the §8.2 under-orb
// line says it with its CAUSE; the vaguer pod copy was removed at the source,
// so `notice` stays empty through the whole event.
test('a call the host drops is written down, said once under the orb, and never restarted', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Listening' })
  const presence = loadPresence(env)
  presence.start()

  await env.pump(400)
  assert.equal(presence.get().source.status, 'native', 'the built-in call is the live source')
  native.clicks.length = 0

  // The host aborts it — nobody pressed End.
  native.state.call = false
  await env.pump(500)

  const ended = presence.lastCallEnd()
  assert.ok(ended, 'the end is written down')
  assert.equal(ended.by, 'host', 'nobody from Jarvis pressed End')
  assert.ok(ended.secondsOn > 0, 'and how long it had been up')
  assert.equal(presence.get().notice, '',
    'the pod says nothing: one message per ended call, and it is the under-orb one')
  assert.deepEqual(native.clicks, [], 'Jarvis never restarts a call by itself — it costs per minute')

  // A second end, the same way: still written down, still nothing in the pod.
  native.state.call = true
  await env.pump(400)
  assert.equal(presence.get().notice, '', 'a call is on again: nothing to say')
  native.state.call = false
  await env.pump(500)
  assert.ok(presence.callEnds().length >= 2, 'and the second end is written down too')
  assert.equal(presence.get().notice, '', 'and the pod is still quiet')

  await env.pump(21000)
  assert.equal(presence.get().notice, '', 'there was never a line here to time out')

  presence.stop()
})

test('after Jarvis\'s own End there is no such line: the end was ours', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Speaking' })
  const presence = loadPresence(env)
  presence.start()

  await env.pump(400)
  const res = await presence.command('stop')
  assert.equal(res.ok, true, 'the End control was pressed')
  assert.deepEqual(native.clicks, ['end'])

  await env.pump(500)
  const ended = presence.lastCallEnd()
  assert.ok(ended, 'the end is still written down')
  assert.equal(ended.by, 'jarvis', 'because we are the ones who pressed End')
  assert.equal(presence.get().notice, '', 'so nothing is said about a call ending on its own')

  presence.stop()
})

// §4.10 ruling 4 — the receipt carries both readings.
test('the probe carries the composer controller and the last call end', () => {
  const env = makeEnv()
  const probe = loadProbe(env)

  const blank = probe(env.document, {})
  assert.deepEqual(blank.controller, { present: false, stored: '', canPrepare: false },
    'no controller in this window, and it says so')
  assert.equal(blank.lastCallEnd, null, 'no call has ended yet')

  const read = probe(env.document, {
    controller: { present: true, stored: '', canPrepare: true },
    lastCallEnd: { at: 1700000000000, by: 'host', secondsOn: 21 }
  })
  assert.deepEqual(read.controller, { present: true, stored: '', canPrepare: true },
    'a draft chat with a controller that can prepare it')
  assert.deepEqual(read.lastCallEnd, { at: 1700000000000, by: 'host', secondsOn: 21 },
    'and the 21-second call the host dropped')
})

test('the start budget covers the prepare, the settle and the wait for Agent', () => {
  const env = makeEnv()
  const presence = loadPresence(env)
  // 4 s native pill + 0.8 s hub rows + 0.3 s menu open + 4 s chat door + 8 s
  // Talk's doors + 3 x 1.5 s start retries + TWENTY s of save (§4.10 amendment
  // 3 waits a slow one out) + 4 s settle + 90 s while Agent finishes his answer
  // (§4.10 ruling 2). The overlay's pending timeout is this number plus half a
  // second, and never less.
  assert.equal(presence.waitBudgetMs('start'),
    4000 + 800 + 300 + 4000 + 8000 + 3 * 1500 + 20000 + 4000 + 90000)
  assert.equal(presence.waitBudgetMs('mute'), 0, 'nothing else waits at all')
})

// ---- SPEC §4.10 amendments (2026-09-19 17:08) ------------------------------

// Amendment 3 — A SLOW SAVE IS WAITED FOR, NOT RACED. Six seconds is when the
// pod starts saying what the pause is; twenty is when Jarvis gives up. Pressing
// the voice button while the host is still writing the chat is the drop itself.
test('a slow save: the pod says so past six seconds, and the press follows the save', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: '' })
  let focused = ''
  let release = null
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    prepareWaitMs: 200,      // the "six seconds" of this test's clock
    prepareMaxMs: 900,       // and its "twenty"
    settleWaitMs: 400,
    controllerInfo: ctrl.info,
    prepareChat: () => new Promise(resolve => {
      release = () => {
        focused = 'sess-new'
        ctrl.state.stored = 'sess-new'
        resolve({ ok: true, reason: '' })
      }
    }),
    focusedSession: () => focused
  })
  presence.start()

  const pending = presence.command('start')
  await sleep(320)
  assert.equal(presence.notice(), 'Saving the chat first…', 'the §4.10 line, verbatim')
  assert.deepEqual(native.clicks, [], 'and nothing is pressed while the host writes')

  release()                                   // the save lands inside the twenty
  const res = await pending
  assert.equal(res.ok, true, 'and then the call is started')
  assert.deepEqual(native.clicks, ['start'], 'on a chat that is saved')
  assert.equal(presence.notice(), '', 'the saving line goes with the wait')

  presence.stop()
})

test('a save that never lands presses nothing at all', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: '' })
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    prepareWaitMs: 120,
    prepareMaxMs: 400,
    settleWaitMs: 200,
    controllerInfo: ctrl.info,
    prepareChat: () => new Promise(() => {}),   // the host never answers
    focusedSession: () => ''
  })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, false, 'a call is not started on a chat mid-save')
  assert.equal(res.reason, 'Hermes is still saving this chat · press START TALK again in a moment',
    'the §4.10 amendment 3 line, verbatim')
  assert.deepEqual(native.clicks, [], 'the button was never pressed')
  assert.equal(presence.notice(), '', 'and the saving line is down again')

  presence.stop()
})

// Amendment 3 / judge D7 — the settle waits for the CONTROLLER to publish the
// stored id, which is the condition hermes-talk itself waits on.
test('the settle waits for the controller to publish the stored id', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: '' })
  let focused = ''
  let storedAt = 0
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    prepareWaitMs: 400,
    prepareMaxMs: 900,
    settleWaitMs: 800,
    controllerInfo: ctrl.info,
    prepareChat: () => {
      focused = 'sess-new'                     // the host's own reading is quick
      setTimeout(() => {                       // the composer's is not
        ctrl.state.stored = 'sess-new'
        storedAt = Date.now()
      }, 180)
      return Promise.resolve({ ok: true, reason: '' })
    },
    focusedSession: () => focused
  })
  presence.start()

  const res = await presence.command('start')
  const pressedAt = Date.now()
  assert.equal(res.ok, true)
  assert.deepEqual(native.clicks, ['start'])
  assert.ok(storedAt > 0 && pressedAt >= storedAt,
    'the press waited for the composer to own the saved session, not just for the route')
  await env.pump(300)
  assert.equal(presence.get().notice, '', 'a settled chat carries no warning')

  presence.stop()
})

// Amendment 6 — ANY unprepared draft warns, controller or not.
test('a draft call on a host with no controller at all still warns', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    focusedSession: () => ''          // route '#/': a brand-new chat
    // no controllerInfo and no prepareChat: an older shell
  })
  presence.start()

  const res = await presence.command('start')
  assert.equal(res.ok, true, 'the call still starts')
  assert.deepEqual(native.clicks, ['start'])

  await env.pump(400)
  assert.equal(presence.get().notice, 'New chat · the call may drop when Agent\'s first answer starts',
    'and the pod says what may happen, with no controller to ask')

  presence.stop()
})

// Amendment 4 — OWNER'S OWN END PRESS is not a call that ended on its own.
test('the End button pressed by hand ends the call without a word on the glass', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: true, pill: 'Listening' })
  const presence = loadPresence(env)
  presence.start()

  await env.pump(400)
  assert.equal(presence.get().source.status, 'native')

  env.clickDoc(native.nodes.endBtn)       // his hand, not ours
  native.state.call = false               // and the host's own handler
  await env.pump(500)

  const ended = presence.lastCallEnd()
  assert.ok(ended, 'the end is still written down')
  assert.equal(ended.by, 'user', 'he ended it himself')
  assert.equal(presence.get().notice, '',
    'so the pod says nothing: it did not end on its own')

  presence.stop()
})

// Amendment 5 — ONE WAIT, and a live call ends it.
test('a call that comes on ends the wait, and the pod goes back to reading it', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, {
    call: false, start: false, hidden: true, hiddenLabel: 'Stop'
  })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 8000 })
  presence.start()

  await env.pump(200)
  const pending = presence.command('start')
  await sleep(30)
  assert.equal(presence.startWaiting(), true, 'START is standing by for Agent')

  native.state.call = true                // the call comes on anyway
  native.state.hidden = false
  await env.pump(400)

  const res = await pending
  assert.equal(res.ok, true, 'a live call is what START was waiting for')
  assert.deepEqual(native.clicks, [], 'and nothing was pressed to get it')
  assert.equal(presence.startWaiting(), false, 'the wait is over')
  assert.equal(presence.get().notice, '', 'the pod is back to the live reading')

  presence.stop()
})

test('a second START while waiting is the CANCEL press: one wait, no press', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, {
    call: false, start: false, hidden: true, hiddenLabel: 'Stop'
  })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 8000 })
  presence.start()

  await env.pump(200)
  const first = presence.command('start')
  await sleep(30)
  assert.equal(presence.startWaiting(), true)

  const second = await presence.command('start')
  assert.equal(second.ok, false)
  assert.equal(second.reason, 'Start cancelled · press START TALK when Agent is done',
    'the second press calls the first off')

  const res = await first
  assert.equal(res.reason, 'Start cancelled · press START TALK when Agent is done')
  assert.equal(presence.startWaiting(), false, 'two waits never run at once')
  assert.deepEqual(native.clicks, [], 'and nothing was pressed')

  presence.stop()
})

// Amendment 2 — A CLOSED JARVIS PRESSES NOTHING. The overlay's close and the
// plugin's dispose both call the wait off; a per-minute call never starts
// behind a closed door.
test('a store that stops presses nothing afterwards, however long Agent takes', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, {
    call: false, start: false, hidden: true, hiddenLabel: 'Stop', startsCall: true
  })
  const presence = loadPresence(env, { commandWaitMs: 100, navWaitMs: 100, answerWaitMs: 8000 })
  presence.start()

  await env.pump(200)
  const pending = presence.command('start')
  await sleep(30)
  assert.equal(presence.startWaiting(), true)

  presence.stop()                          // the plugin unloaded
  const res = await pending
  assert.equal(res.reason, 'Start cancelled · press START TALK when Agent is done')

  native.state.hidden = false              // Agent finishes: the button is back
  native.state.start = true
  await sleep(400)
  assert.deepEqual(native.clicks, [], 'a stopped Jarvis never presses a per-minute call\'s button')
})

test('cancelling mid-save stops the press too', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const native = mountNative(env, { call: false, startsCall: true })
  const ctrl = fakeController({ stored: '' })
  let release = null
  const presence = loadPresence(env, {
    commandWaitMs: 100,
    navWaitMs: 100,
    prepareWaitMs: 400,
    prepareMaxMs: 900,
    settleWaitMs: 200,
    controllerInfo: ctrl.info,
    prepareChat: () => new Promise(resolve => {
      release = () => { ctrl.state.stored = 'sess-new'; resolve({ ok: true, reason: '' }) }
    }),
    focusedSession: () => (ctrl.state.stored ? ctrl.state.stored : '')
  })
  presence.start()

  const pending = presence.command('start')
  await sleep(60)
  presence.cancelStart()                   // Owner closed the dashboard
  release()                                // and only then did the save land

  const res = await pending
  assert.equal(res.ok, false)
  assert.equal(res.reason, 'Start cancelled · press START TALK when Agent is done')
  assert.deepEqual(native.clicks, [], 'the saved chat is left without a call on it')

  presence.stop()
})

// Amendment 7 — THE RIGHT COMPOSER. Two tiles, two sets of voice controls: the
// one that holds the focus is the one that is pressed.
test('with two composers open, the controls pressed are the focused one\'s', async () => {
  const env = makeEnv()
  env.setAudio(null)
  const pressed = []
  const endButton = name => ({
    tagName: 'BUTTON', className: '', textContent: '',
    parentElement: null, parentNode: null,
    getAttribute: attr => (attr === 'aria-label' ? 'End voice conversation' : null),
    closest: sel => (sel.indexOf('"End voice conversation"') >= 0 ? null : null),
    click() { pressed.push(name) }
  })
  const first = endButton('first-tile')
  const second = endButton('second-tile')
  const focusedComposer = {
    className: 'ht-composer-row',
    querySelector: sel => (/End voice conversation/.test(sel) ? second : null)
  }
  const messageBox = { closest: sel => (sel.indexOf('composer') >= 0 ? focusedComposer : null) }
  env.document.activeElement = messageBox
  env.document.querySelector = sel => (/End voice conversation/.test(sel) ? first : null)

  const presence = loadPresence(env)
  presence.start()
  await env.pump(300)
  assert.equal(presence.get().call, 'on', 'an End control in the page is a live call')

  const res = await presence.command('stop')
  assert.equal(res.ok, true)
  assert.deepEqual(pressed, ['second-tile'],
    'the tile Owner is typing in is the one that is ended, not the first in the document')

  presence.stop()
})
