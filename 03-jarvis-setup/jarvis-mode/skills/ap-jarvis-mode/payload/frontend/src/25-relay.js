// hermes-jarvis — file 25: the HUD RELAY (contract SPEC §4.7).
//
//   createRelay({ win, doc, log, writeTextFile, pluginVersion }) -> { start(), stop() }
//
// Why this file exists, in one paragraph. Hermes Desktop 0.21.3 provides
// `context.voice`, so hermes-talk does NOT mount TalkPage in the main window:
// it mounts it in the host's floating HUD, a second Electron window running the
// same app (`index.html?win=hud`, same origin). Runtime plugins load there too,
// so THIS plugin is running in that window as well. Talk's presence bus, its
// command listener and its hidden <audio> element all live there. That is why
// the overlay read `source none` all day and why START TALK found no trigger.
//
// The relay is our instance inside that window. It registers no UI at all. It
// reads Talk exactly as the main window would — same store, same DOM detectors,
// same analyser (20-presence.js, shared at file level) — and pushes what it
// sees through the one wire both windows share: the host's own localStorage.
//
//   hermes-jarvis:presence   relay -> main   a frame, ≤15 Hz, instant on change
//   hermes-jarvis:relay      relay -> main   liveness + a Talk DOM probe, 2 s
//   hermes-jarvis:command    main -> relay   one command, stamped and nonced
//
// Laws: the microphone stays in the main window (this store runs micTap:false —
// one mic on the machine, and it is Owner's ripples). Talk's <audio> is read
// only. Talk's own buttons are never clicked. Nothing here is ever written that
// was not measured in this window.
function createRelay(options) {
  const opts = options || {}
  const win = opts.win || (typeof window !== 'undefined' && window ? window : null)
  const doc = opts.doc || (typeof document !== 'undefined' && document ? document : null)
  const log = typeof opts.log === 'function' ? opts.log : function () {}
  const now = typeof opts.now === 'function' ? opts.now : function () { return Date.now() }
  const getScope = typeof opts.getScope === 'function' ? opts.getScope : function () { return opts.scope || null }
  const getHermesRoot = typeof opts.getHermesRoot === 'function' ? opts.getHermesRoot : function () { return '' }

  const TICK_MS = 66                 // 15 Hz — the level cap in §4.7
  // §4.8 ruling 8: the gate sits just UNDER the tick. A 66 ms timer that fires
  // a millisecond early used to fail a 66 ms test and drop the frame, halving
  // the real rate to 7.5 Hz. 60 ms absorbs that jitter and still never writes
  // faster than the tick can call.
  const LEVEL_GATE_MS = 60
  const BEAT_MS = 2000               // liveness key
  const HEARTBEAT_MS = 5000          // the file receipt, throttled
  const BUS_FRESH_MS = 2000          // a raw bus detail is current for 2 s
  const LEVEL_STEP = 0.02            // below this a level change is not worth a write
  const NONCE_CAP = 32
  const CAPTION_CAP = 6

  const loadedAt = new Date().toISOString()
  const pluginVersion = String(opts.pluginVersion || 'unknown')

  let running = false
  let presence = null
  let tickTimer = null
  let beatTimer = null
  let seq = 0
  let lastWriteAt = 0
  let lastSignature = null
  let lastLevel = 0
  let rawBus = null                  // the last 'hermes-talk:presence' detail
  let rawBusAt = 0
  let seen = []                      // command nonces already re-dispatched
  let lastBeatFileAt = 0
  let lastError = null
  let onBusRef = null
  let onStorageRef = null
  let activeScopeId = ''
  let scopeReady = false
  let scopeChangedAt = 0

  function safe(fn, fallback) {
    try {
      return fn()
    } catch (err) {
      lastError = { message: String(err && err.message ? err.message : err), at: new Date().toISOString() }
      return fallback
    }
  }

  function storageArea() {
    return win ? safe(function () { return win.localStorage }, null) : null
  }

  function syncScope(initial) {
    const scope = getScope()
    const id = scope && scope.id ? String(scope.id) : ''
    if (id === activeScopeId) return scope
    activeScopeId = id
    scopeReady = initial === true && !!id
    scopeChangedAt = initial === true ? 0 : now()
    rawBus = null
    rawBusAt = 0
    lastSignature = null
    lastLevel = 0
    lastWriteAt = 0
    seen = []
    return scope
  }

  function scopedKey(base) {
    const scope = syncScope(false)
    return scope && scope.id ? 'hermes-jarvis:' + scope.id + ':' + String(base || '').replace(/^hermes-jarvis:/, '') : ''
  }

  function writeKey(key, value) {
    const store = storageArea()
    if (!key || !store || typeof store.setItem !== 'function') return false
    return safe(function () { store.setItem(key, JSON.stringify(value)); return true }, false)
  }

  // ---- 1. Talk -> localStorage: the presence frames -------------------------

  function onBus(event) {
    const scope = syncScope(false)
    if (!scope || !scope.id) return
    const detail = event && event.detail
    if (!detail || typeof detail !== 'object') return
    rawBus = detail
    rawBusAt = now()
    scopeReady = true
    // Re-run the store against this event BEFORE the frame is built. Without
    // this the forced frame mixed a brand-new bus detail (phase, muted,
    // sleeping) with the snapshot from the previous tick, so a state change
    // could go out carrying the mode and call it had just stopped having.
    // One reducer, one reading: the store is asked, then quoted.
    if (presence && typeof presence.sample === 'function') {
      safe(function () { presence.sample(); return true }, false)
    }
    publish(true)                    // a state change never waits for the tick
  }

  function busFresh() {
    return Boolean(rawBus) && now() - rawBusAt <= BUS_FRESH_MS
  }

  /** The frame shape §4.7 fixes. Only fields this window actually measured. */
  function frameOf(snap) {
    const fresh = busFresh()
    const level = snap.source && snap.source.voice === 'analyser' ? snap.levels.voice : null
    const captions = (snap.captions || []).filter(function (row) {
      if (!scopeChangedAt) return true
      const at = Number(row && row.at) || 0
      return at >= scopeChangedAt
    }).slice(-CAPTION_CAP)
    const frame = {
      phase: fresh ? String(rawBus.phase || '')
        : snap.call === 'on' ? 'active' : snap.call === 'connecting' ? 'starting' : 'idle',
      live: String(snap.live || ''),
      // Unknown is written as unknown: without the bus nothing in this window
      // reports input/output flags, and the mode already carries what we saw.
      audioActivity: fresh && rawBus.audioActivity && typeof rawBus.audioActivity === 'object' ? rawBus.audioActivity : {},
      transcript: captions,
      muted: fresh ? rawBus.muted === true : snap.mode === 'muted',
      sleeping: fresh ? rawBus.sleeping === true : snap.mode === 'sleeping',
      mode: snap.mode,
      call: snap.call,
      at: now(),
      seq: seq + 1
    }
    if (level !== null) frame.voiceLevel = level
    return frame
  }

  /** Everything except the level. A change here is published immediately. */
  function signatureOf(frame) {
    const rows = frame.transcript.map(function (row) { return String(row.id || '') + ':' + String(row.text || '').slice(0, 40) })
    return [frame.phase, frame.live, frame.call, frame.mode, frame.muted, frame.sleeping, rows.join('|')].join('¬')
  }

  function publish(force) {
    if (!running || !presence) return
    syncScope(false)
    if (!scopeReady) return
    const snap = safe(function () { return presence.get() }, null)
    if (!snap) return
    const frame = frameOf(snap)
    const signature = signatureOf(frame)
    const level = typeof frame.voiceLevel === 'number' ? frame.voiceLevel : 0
    const at = now()
    const changed = signature !== lastSignature
    if (!force && !changed) {
      if (Math.abs(level - lastLevel) < LEVEL_STEP) return
      if (at - lastWriteAt < LEVEL_GATE_MS) return   // ≤ 15 Hz for level-only frames
    }
    seq += 1
    frame.seq = seq
    if (!writeKey(scopedKey(JARVIS_RELAY_KEYS.presence), frame)) return
    lastWriteAt = at
    lastSignature = signature
    lastLevel = level
  }

  // ---- 2. liveness + the file receipt ---------------------------------------

  function talkProbe() {
    return probeTalkDom(doc)
  }

  // Every two seconds: the current frame again with a fresh `at`, then the
  // liveness key, then (throttled) the file receipt.
  //
  // Re-stamping an unchanged frame is the other half of the amendment the main
  // window implements as "hold the last frame while the beat is alive". Talk's
  // bus fires on CHANGES, so a steady call produces no new state for minutes at
  // a time; a relay that only wrote on change left the overlay holding a frame
  // that got older and older with nothing wrong. Now the frame's age is never
  // more than one beat, and the two windows agree without either of them
  // inventing a reading. `first` is true only for the one pass at start().
  function beat(first) {
    if (!running) return
    publish(true)
    const probe = talkProbe()
    writeKey(scopedKey(JARVIS_RELAY_KEYS.live), {
      at: now(),
      seq: seq,
      talk: { hud: probe.hud, view: probe.view, audio: probe.audio }
    })
    heartbeat(first === true, probe)
  }

  // The HUD window's own receipt, beside the main window's
  // desktop-heartbeat.json. It is how "is the relay loaded?" gets answered from
  // a shell instead of from a screenshot. A receipt, never a dependency.
  function heartbeat(force, probe) {
    const write = typeof opts.writeTextFile === 'function'
      ? opts.writeTextFile
      : (win && win.hermesDesktop && typeof win.hermesDesktop.writeTextFile === 'function' ? win.hermesDesktop.writeTextFile : null)
    if (typeof write !== 'function') return
    const scope = syncScope(false)
    const path = scope ? jarvisScopedReceipt(scope, 'hud-heartbeat', getHermesRoot()) : null
    if (!path) return
    const at = now()
    if (!force && at - lastBeatFileAt < HEARTBEAT_MS) return
    lastBeatFileAt = at
    const body = {
      pluginVersion: pluginVersion,
      loadedAt: loadedAt,
      at: new Date(at).toISOString(),
      relaySeq: seq,
      connectionId: scope.connectionId,
      profile: scope.profileId,
      talkProbe: probe || talkProbe(),
      lastError: lastError
    }
    safe(function () {
      Promise.resolve(write(path, JSON.stringify(body, null, 2))).catch(function () {})
      return true
    }, false)
  }

  // ---- 3. localStorage -> Talk: the commands --------------------------------

  function onStorage(event) {
    const key = event && event.key ? String(event.key) : ''
    const commandKey = scopedKey(JARVIS_RELAY_KEYS.command)
    if (!commandKey || key !== commandKey) return
    const store = storageArea()
    const raw = event.newValue !== undefined && event.newValue !== null
      ? event.newValue
      : (store && typeof store.getItem === 'function' ? safe(function () { return store.getItem(key) }, null) : null)
    if (!raw) return
    const value = safe(function () { return JSON.parse(raw) }, null)
    if (!value || typeof value !== 'object') return
    // The wire is plain localStorage on a shared origin: anything running here
    // can put a word in that key. Only the six actions Talk actually has are
    // ever handed on — the same list command() checks before it writes, so
    // neither end has to trust the other (§4.7 relay hygiene).
    const action = String(value.action || '').toLowerCase()
    if (JARVIS_COMMANDS.indexOf(action) < 0) {
      if (action) log('relay ignored an unknown command: ' + action)
      return
    }
    const at = Number(value.at) || 0
    if (!at || now() - at > JARVIS_COMMAND_TTL_MS) {
      log('relay ignored a stale ' + action + ' command')
      return
    }
    const nonce = String(value.nonce || '')
    if (nonce) {
      if (seen.indexOf(nonce) >= 0) return
      seen.push(nonce)
      if (seen.length > NONCE_CAP) seen = seen.slice(-NONCE_CAP)
    }
    dispatch(action)
  }

  /** Talk's own listener is on THIS window — that is the whole point (§4.7). */
  function dispatch(action) {
    if (!win || typeof win.dispatchEvent !== 'function') return false
    return safe(function () {
      const Ctor = win.CustomEvent
      const event = typeof Ctor === 'function'
        ? new Ctor('hermes-talk:command', { detail: { action: action } })
        : { type: 'hermes-talk:command', detail: { action: action } }
      win.dispatchEvent(event)
      log('relay -> talk: ' + action)
      return true
    }, false)
  }

  // ---- lifecycle -------------------------------------------------------------

  function start() {
    if (running) return
    running = true
    syncScope(true)
    // The same reducer the overlay runs, minus the microphone: mute and sleep
    // still mean no listening, and the one mic on this machine is the main
    // window's (SPEC §4.1, §4.7).
    // tick:'timer' — the HUD window is usually occluded, and an occluded
    // Electron window gets its requestAnimationFrame throttled to nothing. A
    // frozen store here is a frozen orb in the main window, so this store runs
    // on a ~15 Hz interval no compositor can pause (§4.7 amendment).
    presence = safe(function () {
      // nativeSource:false — §4.9 belongs to the MAIN window. The relay's job is
      // to be Talk's reader in the window Talk mounted in; the host's own voice
      // conversation is read first-hand where Owner is typing, and a pill in
      // THIS window published as a relay frame would reach the overlay wearing
      // Talk's word (`source relay`) for a reading Talk never made.
      return createPresence({
        log: log, now: now, micTap: false, relaySource: false, nativeSource: false,
        tick: 'timer', getScope: getScope
      })
    }, null)
    if (presence) safe(function () { presence.start(); return true }, false)

    if (win && typeof win.addEventListener === 'function') {
      onBusRef = onBus
      onStorageRef = onStorage
      win.addEventListener('hermes-talk:presence', onBusRef)
      win.addEventListener('storage', onStorageRef)
    }

    const setI = win && typeof win.setInterval === 'function' ? win.setInterval : setInterval
    tickTimer = setI(function () { publish(false) }, TICK_MS)
    beatTimer = setI(function () { beat(false) }, BEAT_MS)
    // ONE opening pass: the first frame, the first liveness key and the one
    // receipt. It used to write the receipt twice — beat() wrote it and then
    // start() wrote it again — which made hud-heartbeat.json look like it was
    // beating at twice its real rate to anyone reading it from a shell.
    beat(true)
    log('HUD relay started (this window owns Talk)')
  }

  function stop() {
    if (!running) return
    running = false
    const clearI = win && typeof win.clearInterval === 'function' ? win.clearInterval : clearInterval
    if (tickTimer !== null) { safe(function () { clearI(tickTimer); return true }, false); tickTimer = null }
    if (beatTimer !== null) { safe(function () { clearI(beatTimer); return true }, false); beatTimer = null }
    if (win && typeof win.removeEventListener === 'function') {
      if (onBusRef) win.removeEventListener('hermes-talk:presence', onBusRef)
      if (onStorageRef) win.removeEventListener('storage', onStorageRef)
    }
    onBusRef = null
    onStorageRef = null
    if (presence) { safe(function () { presence.stop(); return true }, false); presence = null }
    rawBus = null
    rawBusAt = 0
    activeScopeId = ''
    scopeReady = false
    scopeChangedAt = 0
    seen = []
    log('HUD relay stopped')
  }

  return {
    start: start,
    stop: stop,
    // Test seams: no timers, no clock.
    publish: function () { publish(true) },
    tick: function () { publish(false) },
    beat: beat,
    seq: function () { return seq }
  }
}
