// tests/callend.test.mjs — node --test tests/callend.test.mjs
//
// SPEC §8.2 — THE CALL BLACK BOX. Owner, 2026-09-19: "agent just drop the
// call." A call that stops with nobody pressing End has to say WHY, out of
// facts the window measured itself.
//
// Most of this file talks to PURE functions: `jarvisClassifyCallEnd` takes a
// ring (a plain array of rows), the moment the call ended and the last user
// caption, and answers — no clock, no document, no host inside it. That is the
// whole reason it is shaped that way: an evening can be written down here by
// hand and the verdict read back. The last block drives the real store through
// a fake composer, so the ring, the receipt and the pre-flight line are proved
// end to end and not only in theory.
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const SRC = fileURLToPath(new URL('../src/20-presence.js', import.meta.url))
const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const SOURCE = fs.readFileSync(SRC, 'utf8')
// file 05 of the concat build, always in front of this one in the real plugin
const PRELUDE = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n'

/** Load the file's top-level helpers with nothing real behind them. */
function loadHelpers(win = {}, doc = {}, nav = {}) {
  const factory = new Function('window', 'document', 'navigator', `${PRELUDE}${SOURCE}
return {
  jarvisClassifyCallEnd, jarvisCallEndLine, jarvisPreflightLine,
  jarvisStopPhraseOf, jarvisIsVoiceToast, jarvisToastTexts,
  createJarvisEndRing, createPresence,
  JARVIS_STOP_PHRASES, JARVIS_END_RING_MS, JARVIS_CALL_ENDS_CAP
}`)
  return factory(win, doc, nav)
}

const H = loadHelpers()
const T0 = 1_700_000_000_000          // the moment every ring below hangs off

/** One ring row, the shape `createJarvisEndRing` stores. */
const row = (offsetMs, kind, from, to) => ({ at: T0 + offsetMs, kind, from, to })

// ---- ruling 2: one class at a time ----------------------------------------

test('link-blink: the gateway left open inside the window', () => {
  const out = H.jarvisClassifyCallEnd([row(-1200, 'gateway', 'open', 'closed')], T0, '')
  assert.equal(out.why, 'link-blink')
  assert.equal(out.evidence.length, 1)
  assert.match(out.evidence[0], /^gateway open→closed \d\d:\d\d:\d\d$/, 'the evidence line names the change and the second')
})

test('link-blink: an offline event says it too', () => {
  const out = H.jarvisClassifyCallEnd([row(-800, 'online', 'online', 'offline')], T0, '')
  assert.equal(out.why, 'link-blink')
  assert.match(out.evidence[0], /^browser went offline /)
})

test('link-blink: a gateway that came BACK to open is not a blink on its own', () => {
  const out = H.jarvisClassifyCallEnd([row(-900, 'gateway', 'connecting', 'open')], T0, '')
  assert.equal(out.why, 'unknown', 'only LEAVING open is a blink')
})

test('session-restarted: the runtime id moved while the stored chat did not', () => {
  const out = H.jarvisClassifyCallEnd([row(-400, 'session', 'run-a', 'run-b')], T0, '')
  assert.equal(out.why, 'session-restarted')
  assert.deepEqual(out.evidence.map(e => e.replace(/ \d\d:\d\d:\d\d$/, '')), ['runtime session changed'])
})

test('chat-changed: the stored chat id moved', () => {
  const out = H.jarvisClassifyCallEnd([
    row(-600, 'session', 'run-a', 'run-b'),
    row(-600, 'stored', 'chat-a', 'chat-b')
  ], T0, '')
  assert.equal(out.why, 'chat-changed', 'a stored id that moved too is a different chat, not a restart')
})

test('chat-changed: the route moved', () => {
  const out = H.jarvisClassifyCallEnd([row(-100, 'route', '#/session/a', '#/session/b')], T0, '')
  assert.equal(out.why, 'chat-changed')
})

test('voice-service: the host toast is carried verbatim, capped', () => {
  const toast = 'Live voice session ended The live voice session lost its connection. (127s)'
  const out = H.jarvisClassifyCallEnd([row(900, 'toast', '', toast)], T0, '')
  assert.equal(out.why, 'voice-service')
  assert.equal(out.toast, toast, 'word for word, the host\'s own sentence')
  assert.ok(out.toast.length <= 160)
})

test('voice-service ignores a toast that is not about the voice', () => {
  const out = H.jarvisClassifyCallEnd([row(500, 'toast', '', 'Update available')], T0, '')
  assert.equal(out.why, 'unknown', 'an unrelated toast is not a cause')
  assert.equal(out.toast, '')
})

test('stop-word: the last caption was one of the host\'s stop phrases', () => {
  const out = H.jarvisClassifyCallEnd([], T0, 'Hey Hermes, stop.')
  assert.equal(out.why, 'stop-word')
  assert.equal(out.phrase, 'stop', 'the address is stripped, the phrase is quoted back')
})

test('unknown: nothing in the ring, and nothing is invented', () => {
  const out = H.jarvisClassifyCallEnd([], T0, 'what is the weather like')
  assert.equal(out.why, 'unknown')
  assert.deepEqual(out.evidence, [])
  assert.equal(out.toast, '')
  assert.equal(out.phrase, '')
})

// ---- ruling 2: the window, 5 s before to 3 s after -------------------------

test('a fact older than 5 s before the end is out of the window', () => {
  const out = H.jarvisClassifyCallEnd([row(-5001, 'gateway', 'open', 'closed')], T0, '')
  assert.equal(out.why, 'unknown')
  const inside = H.jarvisClassifyCallEnd([row(-4999, 'gateway', 'open', 'closed')], T0, '')
  assert.equal(inside.why, 'link-blink')
})

test('a toast more than 3 s after the end is out of the window', () => {
  const late = H.jarvisClassifyCallEnd([row(3001, 'toast', '', 'Live voice session ended')], T0, '')
  assert.equal(late.why, 'unknown')
  const inTime = H.jarvisClassifyCallEnd([row(2999, 'toast', '', 'Live voice session ended')], T0, '')
  assert.equal(inTime.why, 'voice-service')
})

test('a seed row is never evidence — a first sighting is not a change', () => {
  const seed = { at: T0 - 100, kind: 'gateway', from: '', to: 'closed', seed: true }
  const out = H.jarvisClassifyCallEnd([seed], T0, '')
  assert.equal(out.why, 'unknown')
  assert.deepEqual(out.evidence, [])
})

test('evidence is capped at six, keeping the six closest to the end', () => {
  const ring = []
  for (let i = 9; i >= 1; i -= 1) ring.push(row(-i * 100, 'visibility', 'visible', 'hidden-' + i))
  const out = H.jarvisClassifyCallEnd(ring, T0, '')
  assert.equal(out.evidence.length, 6)
  assert.match(out.evidence[5], /^window hidden-1 /, 'the last line is the newest fact')
})

// ---- ruling 2: PRECEDENCE --------------------------------------------------
//
// link-blink > session-restarted > chat-changed > voice-service > stop-word >
// unknown. Each step below is the reason that order exists.

test('precedence: link-blink BEATS session-restarted (the blink causes the restart)', () => {
  const out = H.jarvisClassifyCallEnd([
    row(-1500, 'gateway', 'open', 'closed'),
    row(-200, 'session', 'run-a', 'run-b')
  ], T0, '')
  assert.equal(out.why, 'link-blink')
})

test('precedence: link-blink BEATS a voice toast and a stop word too', () => {
  const out = H.jarvisClassifyCallEnd([
    row(-1500, 'gateway', 'open', 'closed'),
    row(600, 'toast', '', 'Live voice session ended')
  ], T0, 'stop')
  assert.equal(out.why, 'link-blink')
  assert.equal(out.toast, 'Live voice session ended', 'the toast still rides along as a fact')
})

test('precedence: session-restarted beats chat-changed\'s route row', () => {
  const out = H.jarvisClassifyCallEnd([
    row(-300, 'session', 'run-a', 'run-b'),
    row(-300, 'route', '#/', '#/session/a')
  ], T0, '')
  assert.equal(out.why, 'session-restarted', 'the runtime id moved and the stored chat did not')
})

test('precedence: voice-service BEATS unknown', () => {
  const out = H.jarvisClassifyCallEnd([
    row(-100, 'visibility', 'visible', 'hidden'),
    row(400, 'toast', '', 'Live voice session ended')
  ], T0, '')
  assert.equal(out.why, 'voice-service', 'a named toast beats silence')
})

test('precedence: stop-word fires ONLY when nothing else matched', () => {
  const beaten = H.jarvisClassifyCallEnd([row(600, 'toast', '', 'Live voice session ended')], T0, 'goodbye')
  assert.equal(beaten.why, 'voice-service', 'a measured toast outranks a copied phrase list')
  const alone = H.jarvisClassifyCallEnd([], T0, 'goodbye')
  assert.equal(alone.why, 'stop-word')
})

// ---- the host's stop phrases (copied from lib/voice-stop-word.ts) ----------

test('the stop phrases match the host\'s rule, and nothing wider', () => {
  assert.equal(H.jarvisStopPhraseOf('Stop!'), 'stop')
  assert.equal(H.jarvisStopPhraseOf("that's all"), "that's all")
  assert.equal(H.jarvisStopPhraseOf('ok never mind'), 'never mind')
  assert.equal(H.jarvisStopPhraseOf('stop the docker container'), '', 'a real request that contains "stop" is not a stop')
  assert.equal(H.jarvisStopPhraseOf('hermes'), '', 'a bare address is not a command')
  assert.equal(H.jarvisStopPhraseOf(''), '')
  assert.equal(H.JARVIS_STOP_PHRASES.length, 16, 'all sixteen host phrases are carried')
})

// ---- ruling 4: the line on the glass, word for word ------------------------

test('the glass line is exactly what §8.2 ruling 4 says, per class', () => {
  const line = (why, extra = {}) => H.jarvisCallEndLine({ by: 'host', at: T0, secondsOn: 63, why, ...extra })
  assert.equal(line('link-blink'),
    'Call ended by Hermes · the link to the mini blinked · ⌃⌥T to call again')
  assert.equal(line('session-restarted'),
    'Call ended by Hermes · Hermes restarted this chat\'s session · click the chat once, then ⌃⌥T')
  assert.equal(line('chat-changed'),
    'Call ended by Hermes · the chat changed · ⌃⌥T to call again')
  assert.equal(line('voice-service', { toast: 'The live voice session lost its connection.' }),
    'Call ended by Hermes · voice service: The live voice session lost its connection. · ⌃⌥T to call again')
  assert.equal(line('stop-word', { phrase: 'goodbye' }),
    'Call ended by Hermes · you said "goodbye" · ⌃⌥T to call again')
  assert.equal(line('unknown'),
    'Call ended by Hermes · no cause seen · ⌃⌥T to call again')
})

test('a call Jarvis or Owner ended says NOTHING on the glass', () => {
  assert.equal(H.jarvisCallEndLine({ by: 'jarvis', at: T0, secondsOn: 12, why: 'pressed' }), '')
  assert.equal(H.jarvisCallEndLine({ by: 'user', at: T0, secondsOn: 12, why: 'pressed' }), '')
  assert.equal(H.jarvisCallEndLine(null), '')
})

test('no glass line ever offers to restart the call by itself', () => {
  const whys = ['link-blink', 'session-restarted', 'chat-changed', 'voice-service', 'stop-word', 'unknown']
  for (const why of whys) {
    const line = H.jarvisCallEndLine({ by: 'host', at: T0, why, toast: 'x', phrase: 'bye' })
    assert.match(line, /⌃⌥T/, why + ' tells Owner which chord is his')
    assert.doesNotMatch(line, /reconnect(ing|ed)? automatically|calling again now/i)
  }
})

// ---- ruling 5: the amber pre-flight line -----------------------------------

test('the pre-flight line names the hour the link came back', () => {
  const at = new Date(2026, 8, 19, 22, 7, 7).getTime()
  assert.equal(H.jarvisPreflightLine(at),
    'The link reconnected at 22:07 · click this chat once before calling · the first job may hang up otherwise')
  assert.equal(H.jarvisPreflightLine(0), '', 'no reconnect, no line')
})

// ---- ruling 1: the host's toasts, text only --------------------------------

/** The host's own toast markup: a portalled `role="region"` whose toasts carry
 *  role alert/status AND aria-live (components/notifications.tsx). */
function fakeToastDom(texts, { ariaLive = true, region = true } = {}) {
  const clicks = []
  const items = texts.map(text => ({
    textContent: text,
    getAttribute: name => (name === 'aria-live' && ariaLive ? 'polite' : name === 'role' ? 'status' : null),
    click: () => clicks.push(text)
  }))
  const regionNode = {
    getAttribute: name => (name === 'aria-label' ? 'Notifications' : name === 'role' ? 'region' : null),
    querySelectorAll: sel => (sel.includes('alert') ? items : [])
  }
  return {
    clicks,
    doc: { querySelectorAll: sel => (sel.includes('region') && region ? [regionNode] : []) }
  }
}

test('toasts are read as text, never clicked and never dismissed', () => {
  const kit = fakeToastDom(['Live voice session ended The live voice session was closed by the service.'])
  const texts = H.jarvisToastTexts(kit.doc)
  assert.equal(texts.length, 1)
  assert.match(texts[0], /^Live voice session ended/)
  assert.equal(H.jarvisIsVoiceToast(texts[0]), true)
  assert.deepEqual(kit.clicks, [], 'nothing on the host\'s toast was pressed')
})

test('a region whose rows carry no aria-live is not a toast stack', () => {
  const kit = fakeToastDom(['Saved'], { ariaLive: false })
  assert.deepEqual(H.jarvisToastTexts(kit.doc), [])
})

test('a document with no toast region at all is simply empty', () => {
  assert.deepEqual(H.jarvisToastTexts(fakeToastDom([], { region: false }).doc), [])
  assert.deepEqual(H.jarvisToastTexts(null), [])
  assert.deepEqual(H.jarvisToastTexts({}), [])
})

// ---- ruling 1: the ring itself ---------------------------------------------

test('the ring writes CHANGES, seeds the first sighting, and drops what is old', () => {
  const ring = H.createJarvisEndRing({ win: null, now: () => T0, limitMs: 20000 })
  assert.equal(ring.note(T0, 'gateway', 'open').seed, true, 'the first reading teaches, it does not report')
  assert.deepEqual(ring.all(), [])
  assert.equal(ring.note(T0 + 100, 'gateway', 'open'), null, 'unchanged is not a row')
  const change = ring.note(T0 + 200, 'gateway', 'closed')
  assert.equal(change.from, 'open')
  assert.equal(ring.all().length, 1)
  ring.note(T0 + 21000, 'gateway', 'open')
  assert.equal(ring.all().length, 1, 'the 20 s window dropped the old row as the new one landed')
  assert.equal(ring.all()[0].to, 'open')
})

test('the same toast is written down once per window', () => {
  const ring = H.createJarvisEndRing({ win: null, now: () => T0 })
  assert.ok(ring.noteToast(T0, 'Live voice session ended'))
  assert.equal(ring.noteToast(T0 + 300, 'Live voice session ended'), null)
  assert.equal(ring.all().length, 1)
  assert.equal(ring.noteToast(T0, ''), null, 'an empty toast is not a fact')
})

test('the ring takes its two window listeners off again when it stops', () => {
  const on = []
  const off = []
  const win = {
    addEventListener: (name) => on.push(name),
    removeEventListener: (name) => off.push(name)
  }
  const ring = H.createJarvisEndRing({ win, now: () => T0 })
  ring.arm()
  ring.arm()
  assert.deepEqual(on, ['online', 'offline'], 'armed once, two listeners, no more')
  ring.note(T0, 'route', '#/')
  ring.note(T0 + 10, 'route', '#/session/a')
  ring.stop()
  assert.deepEqual(off, ['online', 'offline'])
  assert.deepEqual(ring.all(), [], 'and it keeps nothing about a store that stopped')
})

// ---- the store, end to end -------------------------------------------------
//
// A fake composer with the host's own "End voice conversation" control: while
// it is in the document the built-in call is ON, and taking it out is the call
// ending. Nothing else about the window is real, which is exactly the point —
// every reading the black box makes is injected or read off this document.

function storeEnv() {
  let now = T0
  const present = new Set()
  const listeners = new Map()
  const node = label => ({
    getAttribute: name => (name === 'aria-label' ? label : null),
    parentElement: null, parentNode: null,
    click() {}
  })
  const doc = {
    visibilityState: 'visible',
    querySelector(sel) {
      for (const label of present) if (sel.includes(label)) return node(label)
      return null
    },
    querySelectorAll() { return [] },
    addEventListener() {}, removeEventListener() {},
    getElementsByTagName() { return [] }
  }
  const win = {
    location: { hash: '#/session/chat-a' },
    setInterval: () => 1,
    clearInterval: () => {},
    setTimeout: () => 1,
    clearTimeout: () => {},
    addEventListener: (name, fn) => listeners.set(name, fn),
    removeEventListener: name => listeners.delete(name)
  }
  const nav = { onLine: true }
  const host = { gateway: 'open', session: 'run-a', stored: 'chat-a' }
  const api = loadHelpers(win, doc, nav)
  const presence = api.createPresence({
    now: () => now,
    log: () => {},
    micTap: false,
    relaySource: false,
    tick: 'timer',
    gateway: () => host.gateway,
    sessionId: () => host.session,
    focusedSession: () => host.stored,
    connectionId: () => 'conn-1'
  })
  presence.start()
  return {
    presence, host, win, doc, nav,
    at: () => now,
    /** Move the clock on and force one sample. */
    step(ms) { now += ms; presence.sample(); return now },
    callOn() { present.add('End voice conversation') },
    callOff() { present.delete('End voice conversation') }
  }
}

test('a host end is classified, logged into the receipt, and named on the glass', () => {
  const env = storeEnv()
  env.step(500)
  env.callOn()
  env.step(500)
  assert.equal(env.presence.get().call, 'on', 'the fake composer reads as a live built-in call')

  // The link blinks, and the call goes with it — the 2026-09-19 22:07 shape.
  env.host.gateway = 'closed'
  env.step(500)
  env.callOff()
  env.step(500)

  const end = env.presence.lastCallEnd()
  assert.ok(end, 'the end was written down')
  assert.equal(end.by, 'host', 'nobody pressed End')
  assert.equal(end.why, 'link-blink')
  assert.ok(end.secondsOn > 0)
  assert.ok(end.evidence.length >= 1 && end.evidence.length <= 6)
  assert.ok(end.evidence.some(e => /^gateway open→closed /.test(e)), 'the evidence is the fact it measured')

  const ends = env.presence.callEnds()
  assert.equal(ends.length, 1, 'the receipt carries it')
  assert.equal(ends[0], end, 'newest first, and it is the same end')
  assert.equal(H.jarvisCallEndLine(end),
    'Call ended by Hermes · the link to the mini blinked · ⌃⌥T to call again')
  env.presence.stop()
})

test('a call Jarvis ended is `pressed`, with no verdict and no evidence', () => {
  const env = storeEnv()
  env.callOn()
  env.step(500)
  env.presence.command('stop')       // Jarvis presses the host's End control
  env.callOff()
  env.step(500)

  const end = env.presence.lastCallEnd()
  assert.ok(end)
  assert.equal(end.by, 'jarvis')
  assert.equal(end.why, 'pressed')
  assert.deepEqual(end.evidence, [])
  assert.equal(H.jarvisCallEndLine(end), '', 'a press is a decision, not a drop')
  env.presence.stop()
})

test('the receipt keeps the last ten ends, newest first', () => {
  const env = storeEnv()
  for (let i = 0; i < 12; i += 1) {
    env.callOn()
    env.step(400)
    env.callOff()
    env.step(400)
  }
  const ends = env.presence.callEnds()
  assert.equal(ends.length, H.JARVIS_CALL_ENDS_CAP)
  for (let i = 1; i < ends.length; i += 1) {
    assert.ok(ends[i - 1].at >= ends[i].at, 'newest first')
  }
  env.presence.stop()
})

test('the pre-flight line comes up after a reconnect and goes when the route is entered', () => {
  const env = storeEnv()
  env.step(500)
  assert.equal(env.presence.callPreflight(), '', 'a steady link warns about nothing')

  env.host.gateway = 'connecting'
  env.step(500)
  env.host.gateway = 'open'
  const backAt = env.step(500)
  const line = env.presence.callPreflight()
  assert.match(line, /^The link reconnected at \d\d:\d\d · click this chat once before calling · the first job may hang up otherwise$/)
  assert.ok(backAt > 0)

  // Entering the chat's route again is what clears it. Jarvis never does this
  // itself — §8.2 ruling 5 ships the warning, not the cure.
  env.win.location.hash = '#/session/chat-b'
  env.step(500)
  assert.equal(env.presence.callPreflight(), '', 'the route was entered, the warning is spent')
  env.presence.stop()
})

// §8 amendment C2 — THE CLICK THE LINE ASKS FOR, on the chat that is already
// open. The hash does not move and the stored id does not move; the host
// rebinds the RUNTIME session underneath and that is the whole signal. Before
// this ruling the amber line survived the very act that answers it.
test('the pre-flight line clears on a runtime-id change on the SAME chat', () => {
  const env = storeEnv()
  env.step(500)
  const hashBefore = env.win.location.hash
  const storedBefore = env.host.stored

  env.host.gateway = 'connecting'
  env.step(500)
  env.host.gateway = 'open'
  env.step(500)
  assert.notEqual(env.presence.callPreflight(), '', 'the link came back and nothing has been entered since')

  // The click: same chat, same route, a new runtime id underneath it.
  env.host.session = 'run-b'
  env.step(500)

  assert.equal(env.win.location.hash, hashBefore, 'the route never moved')
  assert.equal(env.host.stored, storedBefore, 'and neither did the stored chat id')
  assert.equal(env.presence.callPreflight(), '',
    'a new runtime id on the same chat IS this chat being entered again')
  env.presence.stop()
})

test('the pre-flight line never shows while a call is on', () => {
  const env = storeEnv()
  env.host.gateway = 'connecting'
  env.step(500)
  env.host.gateway = 'open'
  env.step(500)
  assert.notEqual(env.presence.callPreflight(), '')
  env.callOn()
  env.step(500)
  assert.equal(env.presence.call, undefined)
  assert.equal(env.presence.get().call, 'on')
  assert.equal(env.presence.callPreflight(), '', 'a live call is not the moment to warn about the next one')
  env.presence.stop()
})

test('a shell with no host atoms leaves those facts OUT of the ring, never faked', () => {
  const api = loadHelpers(
    { location: { hash: '#/' }, setInterval: () => 1, clearInterval: () => {}, addEventListener() {}, removeEventListener() {} },
    { visibilityState: 'visible', querySelector: () => null, querySelectorAll: () => [], addEventListener() {}, removeEventListener() {} },
    { onLine: true }
  )
  let now = T0
  const presence = api.createPresence({ now: () => now, log: () => {}, micTap: false, relaySource: false, tick: 'timer' })
  presence.start()
  now += 500; presence.sample()
  now += 500; presence.sample()
  const kinds = presence.callRing().map(r => r.kind)
  assert.equal(kinds.includes('gateway'), false, 'no gateway reading was injected, so there is no gateway row')
  assert.equal(kinds.includes('session'), false)
  assert.equal(presence.callPreflight(), '', 'and nothing is warned about on facts we do not have')
  presence.stop()
})

test('no createMediaElementSource call was added by the black box', () => {
  // §4.9 ruling 2 / §8.2 ruling 6 — it re-routes playback and is banned. The
  // name appears once, in the comment that says so, and never with a paren.
  assert.equal(SOURCE.includes('createMediaElementSource('), false, 'not one call to it')
  assert.equal(SOURCE.split('createMediaElementSource').length - 1, 1, 'named once, in the guard comment')
})
