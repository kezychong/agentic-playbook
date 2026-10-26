// hermes-jarvis — file 60: the PLUGIN itself (SPEC §5 row A1).
//
// The one `export default` in the built file. Wires presence + data + overlay
// and hands the app five doors into it: the title-bar button, ⌘⌥J, two palette
// rows, a statusbar chip, and the `hermes://jarvis/...` deep link when the
// desktop bridge exposes one. Every registration's disposer goes through
// `ctx.onDispose`, so a hot reload leaves nothing behind (no stray mic, no
// orphan overlay, no dead timers).
//
// It also drops a HEARTBEAT at ~/.hermes/jarvis/desktop-heartbeat.json through
// the preload bridge (`writeTextFile` → IPC `hermes:fs:writeText`), so the
// overlay's state is provable from a shell without screenshotting the app.
// The bridge never creates directories — scripts/install-desktop.sh makes
// ~/.hermes/jarvis — and every write is throttled, try/catch'd and silent.
//
// TWO ROLES, one file (SPEC §4.7). Hermes runs this plugin in every renderer,
// and Talk lives in the floating HUD window (`index.html?win=hud`). In that
// window this plugin is the RELAY and nothing else: no title-bar tool, no
// statusbar chip, no palette rows, no keybind, no room, no overlay, and no
// desktop-heartbeat.json (it writes hud-heartbeat.json instead). In the main
// window everything is as it was, plus the relay's frames as a presence source
// and (SPEC §4.9) the window.Audio tap that gives the orb Agent's level when the
// host's OWN voice conversation is the one doing the talking.
//
// SPEC §4.10 adds one INVISIBLE registration in the main window: a
// `composer.actions` contribution that renders `null` and exists only to hold
// the host's composer voice controller, so a draft chat can be saved before a
// call is started on it. It is a registration, not a door: the ways in stay
// seven (8 registrations, 7 doors).
// SPEC §7.6 — the product is called **Jarvis mode**. Display strings only: the
// id `hermes-jarvis`, every path, every localStorage key, every event name, the
// route and the keybind id are unchanged, because they are what the rest of the
// machine already knows this plugin by.
//
// SPEC §7.2 adds the second window. The host denies `window.open`, but its
// preload exposes `openWindow({connectionId, profile})` = a full PEER Hermes
// window (`?peer=1`), which loads runtime plugins like any other and has its
// own composer, so it can own its own voice call on another display. A window
// opened that way finds `localStorage['hermes-jarvis:open-on-boot']`, consumes
// it (removing it first, so only one window can win) and raises the overlay
// once the app's root has actually rendered.
export default {
  id: 'hermes-jarvis',
  name: 'Jarvis mode',
  description: 'Agent in the middle, brains behind him, everything moving. Full-window command centre over hermes-talk.',
  defaultEnabled: true,
  register(ctx) {
    const PLUGIN_VERSION = '1.0.0-jarvis-mode'
    // §7.2 ruling 5: a peer window keeps its own receipt so two windows never
    // overwrite each other's. A window whose role cannot be told keeps today's.
    const HEARTBEAT_MS = 30000
    const BEAT_THROTTLE_MS = 500
    const BOOT_KEY = 'open-on-boot'
    const BOOT_FRESH_MS = 20000      // older than this and nobody is waiting
    const BOOT_WAIT_MS = 10000       // how long we watch for the app to render
    const BOOT_POLL_MS = 250

    // Everything but the one registration receipt stays at debug level; warn
    // is what reaches ~/.hermes/logs/desktop.log.
    const log = function (message) {
      try {
        console.debug('[hermes-jarvis] ' + message)
      } catch (err) { /* console is a nicety */ }
    }

    // Which window is this? The host's own test (store/windows.ts:39-52) is
    // `new URLSearchParams(location.search).get('win') === 'hud'` — same test
    // here, same answer, no guessing from window size or chrome.
    function isHudWindow() {
      try {
        const loc = typeof window !== 'undefined' && window ? window.location : null
        const search = loc && loc.search ? String(loc.search) : ''
        if (!search) return false
        if (typeof URLSearchParams === 'function') {
          return new URLSearchParams(search).get('win') === 'hud'
        }
        return /[?&]win=hud(?:&|$)/.test(search)
      } catch (err) {
        return false
      }
    }

    // Which SEAT this window has (SPEC §7.2 ruling 5). The host's own markers,
    // read the host's own way: a full peer instance carries `?peer=1`
    // (`isPeerInstanceWindow`, store/windows.ts), and the primary app window
    // carries no `win=` flag at all. A window wearing some other `win=` kind is
    // a specialized renderer we have not been taught to name — it says
    // `unknown` rather than guessing.
    function windowRole() {
      try {
        const loc = typeof window !== 'undefined' && window ? window.location : null
        const search = loc && loc.search ? String(loc.search) : ''
        const params = typeof URLSearchParams === 'function' ? new URLSearchParams(search) : null
        if (!params) return /[?&]peer=1(?:&|$)/.test(search) ? 'peer' : /[?&]win=/.test(search) ? 'unknown' : 'primary'
        if (params.get('peer') === '1') return 'peer'
        if (params.get('win')) return 'unknown'
        return 'primary'
      } catch (err) {
        return 'unknown'
      }
    }

    function routeAtom(name) {
      try {
        const state = HermesSDK && HermesSDK.host && HermesSDK.host.state ? HermesSDK.host.state[name] : null
        return state && typeof state.get === 'function' ? state.get() : null
      } catch (err) { return null }
    }

    let pluginScope = null
    let hermesRoot = ''
    let hudRelay = null
    let bootCheck = null
    let scopeGeneration = 0
    function getPluginScope() { return pluginScope }
    function getHermesRoot() { return hermesRoot }
    try {
      const bridge = typeof window !== 'undefined' && window ? window.hermesDesktop : null
      if (bridge && typeof bridge.logsRoot === 'function') {
        Promise.resolve(bridge.logsRoot()).then(function (logsPath) {
          const path = String(logsPath || '').replace(/[\\/]+$/, '')
          if (/(?:^|[\\/])logs$/.test(path)) hermesRoot = path.replace(/[\\/]logs$/, '')
          if (pluginScope && isHudWindow() && hudRelay) hudRelay.beat(true)
          else if (pluginScope) heartbeat(true)
        }).catch(function () { hermesRoot = '' })
      }
    } catch (err) { hermesRoot = '' }
    function refreshPluginScope() {
      const selected = jarvisSelectedOwner(HermesSDK && HermesSDK.host)
      const generation = ++scopeGeneration
      pluginScope = null
      if (!selected) return
      jarvisTargetProfile(HermesSDK && HermesSDK.host, selected.connectionId, selected.routeProfile).then(function (targetProfile) {
        if (generation !== scopeGeneration) return
        pluginScope = jarvisScope(selected.connectionId, selected.routeProfile, targetProfile)
        if (bootCheck) bootCheck()
        if (pluginScope && isHudWindow() && hudRelay) hudRelay.beat(true)
        else if (pluginScope) heartbeat(true)
      })
    }
    refreshPluginScope()
    ;['connectionId', 'focusedSessionOwner', 'focusedSessionProfile', 'profile'].forEach(function (name) {
      try {
        const state = HermesSDK && HermesSDK.host && HermesSDK.host.state ? HermesSDK.host.state[name] : null
        if (state && typeof state.listen === 'function') {
          const unlisten = state.listen(refreshPluginScope)
          if (typeof unlisten === 'function') ctx.onDispose(unlisten)
        }
      } catch (err) { /* the periodic data read remains the fallback */ }
    })

    // ---- the HUD instance: relay only, nothing registered ------------------
    if (isHudWindow()) {
      try {
        hudRelay = createRelay({
          win: typeof window !== 'undefined' ? window : null,
          doc: typeof document !== 'undefined' ? document : null,
          log: log,
          pluginVersion: PLUGIN_VERSION,
          getScope: getPluginScope,
          getHermesRoot: getHermesRoot
        })
        ctx.onDispose(function () {
          try { if (hudRelay) hudRelay.stop() } catch (err) { /* already gone */ }
        })
        hudRelay.start()
        try {
          console.warn('[hermes-jarvis] HUD relay started — Talk lives in this window, the overlay is in the other one')
        } catch (err) { /* console is a nicety */ }
      } catch (err) {
        try {
          console.warn('[hermes-jarvis] HUD relay failed: ' + (err && err.message ? err.message : err))
        } catch (e) { /* console is a nicety */ }
        throw err
      }
      return
    }

    // ---- the main window: the audio tap goes in FIRST (SPEC §4.9 ruling 2) -
    //
    // The host's own voice plays Agent through a DETACHED `new Audio()` that is
    // never in the document, so the constructor is the only door to a level.
    // The wrapper goes on HERE and nowhere else: the HUD instance returned
    // above, so this line only ever runs in the main window. It is honoured
    // before anything else is built, because an element created during load is
    // one we would otherwise never see, and it comes off again on dispose.
    const audioTap = installJarvisAudioTap(typeof window !== 'undefined' ? window : null, getPluginScope)
    ctx.onDispose(function () {
      try { audioTap.restore() } catch (err) { /* already gone */ }
    })
    log('audio tap ' + (audioTap.wrapped ? 'installed on window.Audio' : 'not installed (kill switch or no Audio here)'))

    // Declared out here so the heartbeat closure and the catch below can both
    // see them however far the register body got.
    let presence = null
    let data = null
    let rawOverlay = null
    let contributionIds = []
    let deepLinkWired = false
    let lastError = null
    const loadedAt = new Date().toISOString()
    const role = windowRole()
    const beatStem = role === 'peer' ? 'desktop-heartbeat-peer' : 'desktop-heartbeat'
    // §7.2 ruling 2: did THIS window open because another one sent it here?
    let bootOpen = false
    let bootTimer = null

    let lastBeatAt = 0
    let beatTrailing = null
    let beatTimer = null

    // §4.8 rulings 1 and 5 — the three host readings the presence store and the
    // heartbeat need, read through the SDK HERE so 20-presence.js stays
    // SDK-free. Each one is a plain try/catch: an older shell that does not
    // expose a door simply gives nothing back, and the store falls back to the
    // behaviour it had before the chat door existed.
    function hostState(name) {
      try {
        const state = HermesSDK && HermesSDK.host && HermesSDK.host.state ? HermesSDK.host.state[name] : null
        return state && typeof state.get === 'function' ? state.get() : null
      } catch (err) {
        return null
      }
    }

    function focusedSession() {
      const value = hostState('focusedStoredSessionId')
      return typeof value === 'string' ? value : ''
    }

    function gatewayState() {
      const value = hostState('gateway')
      return typeof value === 'string' ? value : ''
    }

    // §8.2 ruling 1 — the two extra readings the call black box's ring needs:
    // the RUNTIME session id (a new one after a reconnect is what bumps the
    // composer's voice epoch and drops the call) and the connection id. Read
    // through the same `hostState` door as everything else — no new host API,
    // and an atom this shell does not have simply gives nothing back, which
    // leaves that fact out of the ring instead of faking it.
    function runtimeSessionId() {
      const value = hostState('focusedSessionId')
      return typeof value === 'string' ? value : ''
    }

    function connectionIdOf() {
      const value = hostState('connectionId')
      return typeof value === 'string' ? value : ''
    }

    // §4.10 ruling 1 — THE COMPOSER VOICE CONTROLLER, handed over by an
    // invisible `composer.actions` contribution below. The host exposes it only
    // through a React hook (`HermesSDK.useComposerVoiceController`), so the only
    // way to hold it is to be mounted inside the composer; the contribution
    // renders nothing at all and exists purely to pass this reference out.
    // §4.10 amendment 7 — EVERY mounted composer, in mount order. With two chat
    // tiles open there are two controllers, and the one that matters is the one
    // whose chat has the focus: `host.state.focusedStoredSessionId`, with a
    // draft's empty string standing for the host's null. An unmount falls back
    // to another mounted composer, never to nothing.
    const voiceControllers = []

    /** The controller's own stored session id, '' for a draft. */
    function storedOf(controller) {
      try {
        const owner = (controller && controller.owner) || {}
        return typeof owner.storedSessionId === 'string' ? owner.storedSessionId : ''
      } catch (err) {
        return ''
      }
    }

    /** The composer Owner is looking at (§4.10 amendment 7). */
    function currentController() {
      if (!voiceControllers.length) return null
      const focused = focusedSession()
      for (let i = voiceControllers.length - 1; i >= 0; i -= 1) {
        if (storedOf(voiceControllers[i]) === focused) return voiceControllers[i]
      }
      return voiceControllers[voiceControllers.length - 1]
    }

    /** {present, stored, canPrepare} — what the store needs to decide whether
     *  this is a draft chat worth preparing (§4.10 rulings 1 and 4). */
    function controllerInfo() {
      const current = currentController()
      if (!current) return { present: false, stored: '', canPrepare: false }
      const stored = storedOf(current)
      let canPrepare = false
      try {
        const caps = current.capabilities || {}
        canPrepare = caps.prepareSession === 1 && typeof current.prepareSession === 'function'
      } catch (err) { canPrepare = false }
      return { present: true, stored: stored, canPrepare: canPrepare }
    }

    /** Ask the host to save the draft chat before a call is started on it.
     *  Always resolves {ok, reason} — the store owns the deadline. */
    function prepareChat() {
      const current = currentController()
      if (!current || typeof current.prepareSession !== 'function') {
        return Promise.resolve({ ok: false, reason: 'no composer voice controller in this window' })
      }
      let out = null
      try {
        out = current.prepareSession()
      } catch (err) {
        return Promise.resolve({ ok: false, reason: String(err && err.message ? err.message : err) })
      }
      return Promise.resolve(out).then(function (prepared) {
        const stored = prepared && typeof prepared.storedSessionId === 'string' ? prepared.storedSessionId : ''
        if (!stored) return { ok: false, reason: 'the host prepared no stored session' }
        log('the host saved the chat before the call (' + stored + ')')
        return { ok: true, reason: '' }
      }, function (err) {
        return { ok: false, reason: String(err && err.message ? err.message : err) }
      })
    }

    // ---- the second window (SPEC §7.2 ruling 1) ---------------------------
    //
    // The bridge takes a route; the profile name is validated against the same
    // rule the main process enforces (`DESKTOP_PROFILE_NAME_RE`), because an
    // invalid one makes the IPC throw instead of opening a window. When this
    // window cannot name its own profile we ask with NO route at all, which
    // makes the host inherit the sender's connection and profile — the same
    // thing ⌘⇧N does.
    const PROFILE_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/

    function openOwnWindow() {
      let bridge = null
      try {
        bridge = typeof window !== 'undefined' && window ? window.hermesDesktop : null
      } catch (err) { bridge = null }
      if (!bridge || typeof bridge.openWindow !== 'function') {
        return Promise.resolve({ ok: false, reason: 'this Hermes has no openWindow bridge' })
      }
      const profile = String(hostState('focusedSessionProfile') || hostState('profile') || '').trim()
      const connectionId = hostState('connectionId')
      const route = PROFILE_RE.test(profile)
        ? { connectionId: typeof connectionId === 'string' && connectionId ? connectionId : null, profile: profile }
        : undefined
      try {
        return Promise.resolve(bridge.openWindow(route)).then(function (res) {
          // the bridge answers {ok} (main.ts `hermes:window:openInstance`); an
          // older shell that answers nothing at all still opened a window
          const ok = res === undefined || res === null ? true : res.ok !== false
          return { ok: ok, reason: (res && res.error) || '' }
        }, function (err) {
          return { ok: false, reason: String(err && err.message ? err.message : err) }
        })
      } catch (err) {
        return Promise.resolve({ ok: false, reason: String(err && err.message ? err.message : err) })
      }
    }

    /** §7.2 ruling 2 — the boot flag, CONSUMED: the key is removed first, so
     *  two windows racing the same flag cannot both win it, and a hot reload
     *  (which re-runs register()) finds nothing left to act on. */
    function consumeBootFlag() {
      try {
        const store = typeof window !== 'undefined' && window ? window.localStorage : null
        if (!store || typeof store.getItem !== 'function') return false
        const key = jarvisScopedKey(getPluginScope(), BOOT_KEY)
        if (!key) return false
        const raw = store.getItem(key)
        if (raw === null || raw === undefined) return false
        store.removeItem(key)
        const at = Number(raw)
        if (!isFinite(at) || at <= 0) return false
        const age = Date.now() - at
        // stale (the flag has been sitting there since an earlier session) or
        // in the future by more than a clock's worth of skew: not for us
        return age >= -5000 && age <= BOOT_FRESH_MS
      } catch (err) {
        return false
      }
    }

    /** Has the app itself rendered into this window yet? The overlay appends to
     *  document.body, and appending before React's first paint puts it under a
     *  root that is about to be replaced. */
    function appRendered() {
      try {
        const d = typeof document !== 'undefined' ? document : null
        if (!d || !d.body) return false
        const root = typeof d.getElementById === 'function' ? d.getElementById('root') : null
        if (root) {
          const kids = root.childNodes ? root.childNodes.length : 0
          return kids > 0
        }
        return Boolean(d.body.childNodes && d.body.childNodes.length > 0)
      } catch (err) {
        return false
      }
    }

    const hostNavigate = (function () {
      try {
        if (HermesSDK && HermesSDK.host && typeof HermesSDK.host.navigate === 'function') {
          return function (path) {
            try {
              HermesSDK.host.navigate(path)
            } catch (err) {
              log('navigate to ' + path + ' failed: ' + (err && err.message ? err.message : err))
            }
          }
        }
      } catch (err) { /* older shell: no navigator, no chat door */ }
      return null
    })()

    function heartbeat(force) {
      try {
        const bridge = typeof window !== 'undefined' && window ? window.hermesDesktop : null
        const write = bridge && bridge.writeTextFile
        if (typeof write !== 'function') return // plain browser / older shell
        const scope = getPluginScope()
        const beatPath = scope ? jarvisScopedReceipt(scope, beatStem, getHermesRoot()) : null
        if (!beatPath) return
        const at = Date.now()
        if (!force && at - lastBeatAt < BEAT_THROTTLE_MS) {
          if (!beatTrailing) {
            beatTrailing = setTimeout(function () { beatTrailing = null; heartbeat(true) }, BEAT_THROTTLE_MS)
          }
          return
        }
        lastBeatAt = at
        const p = presence && typeof presence.get === 'function' ? presence.get() : null
        const body = {
          pluginVersion: PLUGIN_VERSION,
          loadedAt: loadedAt,
          at: new Date(at).toISOString(),
          connectionId: scope.connectionId,
          profile: scope.profileId,
          contributions: contributionIds,
          deepLink: deepLinkWired,
          // §7.2 ruling 5 — which window wrote this receipt, and whether it
          // came up because another window asked for it.
          window: role,
          bootOpen: bootOpen,
          overlay: rawOverlay && typeof rawOverlay.isOpen === 'function' && rawOverlay.isOpen() ? 'open' : 'closed',
          mode: p ? p.mode : null,
          call: p ? p.call : null,
          source: p ? p.source : null,
          demo: p ? Boolean(p.demo) : false,
          // What the live DOM holds for Talk right now (20-presence.js). Pure,
          // never throws, and the one way to debug START TALK from a shell.
          // §4.8 ruling 5: route, focused session and gateway ride along, so the
          // next failed START can be read from the receipt without a screen.
          talkProbe: probeTalkDom(typeof document !== 'undefined' ? document : null, {
            win: typeof window !== 'undefined' ? window : null,
            focusedSession: Boolean(focusedSession()),
            gateway: gatewayState(),
            // §4.9 ruling 5: the wrapper's own state. The store knows whether
            // it is metering; before the store exists, the tap still knows
            // whether it is wrapped and how many elements it has seen.
            audioTap: presence && typeof presence.audioTap === 'function'
              ? presence.audioTap()
              : { wrapped: audioTap.wrapped, seen: audioTap.seen(), metering: false },
            // §4.10 ruling 4: was a composer voice controller mounted, was its
            // chat already saved, and how did the last call end.
            controller: controllerInfo(),
            lastCallEnd: presence && typeof presence.lastCallEnd === 'function'
              ? presence.lastCallEnd()
              : null
          }),
          // §8.2 ruling 3 — THE CALL BLACK BOX, additive: the last ten built-in
          // calls that stopped, newest first, each with why it stopped and the
          // facts that verdict was read from. Nothing else in this receipt
          // changes shape.
          callEnds: presence && typeof presence.callEnds === 'function'
            ? presence.callEnds()
            : [],
          lastError: lastError
        }
        Promise.resolve(write(beatPath, JSON.stringify(body, null, 2))).catch(function () {
          /* the heartbeat is a receipt, never a dependency */
        })
      } catch (err) {
        /* silent by contract */
      }
    }

    function onOverlayChanged() {
      if (beatTimer) { clearInterval(beatTimer); beatTimer = null }
      if (rawOverlay && rawOverlay.isOpen()) {
        beatTimer = setInterval(function () { heartbeat(true) }, HEARTBEAT_MS)
      }
      heartbeat(false)
    }

    try {
      const PALETTE_AREA = HermesSDK.PALETTE_AREA || 'palette'
      const KEYBINDS_AREA = HermesSDK.KEYBINDS_AREA || 'keybinds'
      const STATUSBAR_RIGHT = (HermesSDK.STATUSBAR_AREAS && HermesSDK.STATUSBAR_AREAS.right) || 'statusBar.right'
      const TITLEBAR_RIGHT = 'titleBar.tools.right'
      const TOGGLE_ACTION = 'jarvis.toggle'

      presence = createPresence({
        log: log,
        // §4.8 ruling 1: START's door into a chat, injected.
        navigate: hostNavigate,
        focusedSession: focusedSession,
        gateway: gatewayState,
        // §8.2 ruling 1: the black box's two extra host readings.
        sessionId: runtimeSessionId,
        connectionId: connectionIdOf,
        // §4.9 ruling 2: the elements `new Audio()` handed out, so the store
        // can meter the one that is playing without ever touching playback.
        audioTap: audioTap,
        // §4.10 ruling 1: the draft-chat prepare, injected — the store never
        // sees the SDK, only these two plain functions.
        prepareChat: prepareChat,
        controllerInfo: controllerInfo
        ,getScope: getPluginScope
      })
      data = createDataFeed({ ctx: ctx, HermesSDK: HermesSDK, log: log })
      rawOverlay = createOverlay({
        ctx: ctx,
        presence: presence,
        data: data,
        // 40-scene.js lands beside this file in the concat build; until it does,
        // the overlay draws its own labelled stub.
        createScene: typeof createScene === 'function' ? createScene : null,
        HermesSDK: HermesSDK,
        log: log,
        // §7.2 ruling 1: the overlay owns the key, the button and the boot
        // flag; this is the one line of host it needs, injected.
        openWindow: openOwnWindow
        ,getScope: getPluginScope
      })

      // Thin wrapper: everything that can change open/closed stamps the
      // heartbeat, without 50-overlay.js having to know the heartbeat exists.
      const overlay = {
        open: function () { rawOverlay.open(); onOverlayChanged() },
        close: function () { rawOverlay.close(); onOverlayChanged() },
        toggle: function () { rawOverlay.toggle(); onOverlayChanged() },
        isOpen: function () { return rawOverlay.isOpen() },
        showPanel: function (panel) { rawOverlay.showPanel(panel) },
        ownWindow: function () { rawOverlay.ownWindow() },
        destroy: function () { rawOverlay.destroy() }
      }

      // Teardown FIRST: from here on, anything that throws still gets unwound.
      // A disposer registered after start() would be skipped by a throw at
      // registerMany and leave the rAF loop, the poll timers and a live mic tap
      // behind until the app restarted.
      ctx.onDispose(function () {
        if (beatTimer) { clearInterval(beatTimer); beatTimer = null }
        if (beatTrailing) { clearTimeout(beatTrailing); beatTrailing = null }
        // §4.10 amendment 2: an unloading plugin holds nobody waiting to press
        // a per-minute call's button.
        try { if (presence && typeof presence.cancelStart === 'function') presence.cancelStart() } catch (err) { /* nothing waiting */ }
        try { if (rawOverlay) rawOverlay.destroy() } catch (err) { /* already gone */ }
        try { if (presence) presence.stop() } catch (err) { /* already gone */ }
        try { if (data) data.stop() } catch (err) { /* already gone */ }
      })

      presence.start()
      data.start()

      const toggle = function () { overlay.toggle() }
      const openJarvis = function () { overlay.open() }
      const closeJarvis = function () { overlay.close() }
      const toggleDemo = function () {
        const next = !presence.isDemo()
        presence.setDemo(next)
        if (next) overlay.open()
        else heartbeat(false)
        try {
          HermesSDK.host.notify({ kind: 'info', message: next ? 'Jarvis mode: demo on' : 'Jarvis mode: demo off' })
        } catch (err) { /* toasts are optional */ }
      }

      // ---- statusbar chip: a coloured dot and the mode word -----------------

      function StatusChip() {
        const state = React.useState({ mode: 'idle', call: 'off', demo: false })
        const value = state[0]
        const setValue = state[1]

        // §7.3 ruling 6 — the chip names the SAME mode the orb and the display
        // word name: `working` while a tool is actually running, not the
        // store's raw `thinking`. The derivation lives in 50-overlay.js so
        // there is exactly one of it.
        const derive = function (p) {
          if (typeof jarvisWorkingPresence !== 'function') return p
          try {
            const act = data && typeof data.get === 'function' ? (data.get() || {}).activity : null
            return jarvisWorkingPresence(p, act) || p
          } catch (err) {
            return p
          }
        }

        React.useEffect(function () {
          let last = ''
          const push = function (p) {
            if (!p) return
            const view = derive(p)
            const key = view.mode + p.call + p.demo
            if (key === last) return
            last = key
            setValue({ mode: view.mode, call: p.call, demo: p.demo })
          }
          const offPresence = presence.subscribe(push)
          // a data frame can change the derivation on its own (the tool
          // started, the tool ended) — the chip follows it too
          const offData = data && typeof data.subscribe === 'function'
            ? data.subscribe(function () {
              try { push(presence.get()) } catch (err) { /* the store is between frames */ }
            })
            : null
          return function () {
            if (typeof offPresence === 'function') offPresence()
            if (typeof offData === 'function') offData()
          }
        }, [])

        const colors = typeof JARVIS_MODE_COLORS === 'object' && JARVIS_MODE_COLORS ? JARVIS_MODE_COLORS : {}
        return React.createElement(
          'button',
          {
            type: 'button',
            className: 'jv-chip' + (value.call === 'on' ? ' jv-on' : ''),
            style: { color: colors[value.mode] || 'inherit' },
            title: 'Jarvis mode · ' + value.mode + (value.demo ? ' (demo)' : ''),
            'aria-label': 'Toggle Jarvis mode',
            onClick: toggle
          },
          React.createElement('i', null),
          React.createElement('span', null, value.demo ? 'demo' : value.mode)
        )
      }

      // ---- the invisible composer contribution (SPEC §4.10 ruling 1) --------
      //
      // Renders NOTHING — `null`, no wrapper, no layout change — and exists
      // only to sit inside the composer where `useComposerVoiceController()` is
      // callable, and hand the controller out. The hook is called
      // unconditionally (rules of hooks); the decision whether to register at
      // all is made out here, before the component exists, so a host without
      // the hook simply never mounts it and START behaves exactly as it did.
      const hasControllerHook = (function () {
        try {
          return typeof HermesSDK.useComposerVoiceController === 'function'
        } catch (err) {
          return false
        }
      })()

      function ComposerVoiceBridge() {
        const controller = HermesSDK.useComposerVoiceController()
        React.useEffect(function () {
          if (!controller) return undefined
          // §4.10 amendment 7: this composer joins the list and leaves it on
          // unmount. Whoever is left is still there to be used.
          voiceControllers.push(controller)
          return function () {
            const at = voiceControllers.indexOf(controller)
            if (at >= 0) voiceControllers.splice(at, 1)
          }
        }, [controller])
        return null
      }

      // ---- contributions ----------------------------------------------------

      const contributions = [
        {
          // titleBar.tools.* consumes DATA (a TitlebarTool), not `render` — the
          // same shape hermes-talk registers its `talk-topbar` with.
          id: 'jarvis-topbar',
          area: TITLEBAR_RIGHT,
          order: 44,
          data: {
            id: 'hermes-jarvis',
            label: 'Jarvis mode',
            title: 'Jarvis mode',
            actionId: TOGGLE_ACTION,
            icon: React.createElement(HermesSDK.Codicon, { name: 'radio-tower', 'aria-label': 'Jarvis mode' }),
            onSelect: toggle
          }
        },
        {
          id: 'jarvis-statusbar',
          area: STATUSBAR_RIGHT,
          order: 12,
          render: function () { return React.createElement(StatusChip, null) }
        },
        {
          id: 'jarvis-palette-toggle',
          area: PALETTE_AREA,
          data: {
            id: 'jarvis.toggle',
            label: 'Jarvis mode: toggle',
            action: TOGGLE_ACTION,
            keywords: ['jarvis', 'agent', 'voice', 'dashboard', 'overlay', 'hud'],
            keepOpen: false,
            detail: function () { return overlay.isOpen() ? 'open' : 'closed' },
            detailVariant: 'state',
            run: toggle
          }
        },
        {
          id: 'jarvis-palette-demo',
          area: PALETTE_AREA,
          data: {
            id: 'jarvis.demo',
            label: 'Jarvis mode: demo on/off',
            keywords: ['jarvis', 'demo', 'sample', 'preview', 'states'],
            keepOpen: false,
            detail: function () { return presence.isDemo() ? 'on' : 'off' },
            detailVariant: 'state',
            run: toggleDemo
          }
        },
        {
          // §7.2 ruling 1 — the same press as W and the top-chrome button.
          // The id stays inside the `jarvis.` family; only the words are new.
          id: 'jarvis-palette-window',
          area: PALETTE_AREA,
          data: {
            id: 'jarvis.window',
            label: 'Jarvis mode: open in its own window',
            keywords: ['jarvis', 'window', 'display', 'screen', 'monitor', 'peer'],
            keepOpen: false,
            run: function () { overlay.ownWindow() }
          }
        },
        {
          id: 'jarvis-keybind',
          area: KEYBINDS_AREA,
          data: {
            // the keybind id is a contract with whatever has it bound —
            // §7.6 leaves it exactly as it was
            id: TOGGLE_ACTION,
            label: 'Toggle Jarvis mode',
            category: 'view',
            defaults: ['mod+alt+j'],
            run: toggle
          }
        }
      ]

      // §4.10 ruling 1: the eighth REGISTRATION, and no eighth door — it draws
      // nothing and Owner cannot press it. The seven ways in stay seven.
      if (hasControllerHook) {
        contributions.push({
          id: 'jarvis-composer-voice',
          area: 'composer.actions',
          order: 99,
          render: function () { return React.createElement(ComposerVoiceBridge, null) }
        })
      } else {
        log('this host has no useComposerVoiceController — a draft chat cannot be prepared before a call')
      }

      ctx.registerMany(contributions)
      contributionIds = contributions.map(function (c) { return c.id })

      // ---- hermes:// deep link (bin/jarvis-toggle prefers this door) --------

      try {
        const bridge = typeof window !== 'undefined' ? window.hermesDesktop : null
        if (bridge && typeof bridge.onDeepLink === 'function') {
          const offLink = bridge.onDeepLink(function (payload) {
            if (!payload || payload.kind !== 'jarvis') return
            const name = String(payload.name || 'toggle')
            if (name === 'open') openJarvis()
            else if (name === 'close') closeJarvis()
            else if (name === 'demo') toggleDemo()
            else toggle()
          })
          if (typeof offLink === 'function') ctx.onDispose(offLink)
          deepLinkWired = true
          log('deep link bridge reachable (hermes://jarvis/toggle)')
        } else {
          log('deep link bridge not exposed to plugins — use the button, ' +
            jarvisKeyLabelsFor(typeof window !== 'undefined' ? window : null).open + ', or the palette')
        }
      } catch (err) {
        log('deep link wiring failed: ' + (err && err.message ? err.message : err))
      }

      // ---- optional display-only room (WP-D, src/55-room.js) ---------------

      try {
        if (typeof registerJarvisRoom === 'function') {
          const roomIds = registerJarvisRoom(ctx, {
            presence: presence,
            data: data,
            createScene: (typeof createScene === 'function' ? createScene : null),
            HermesSDK: HermesSDK,
            React: React,
            log: log,
            overlay: overlay
          })
          /* the room's own contributions count in the heartbeat receipt too */
          if (Array.isArray(roomIds)) contributionIds = contributionIds.concat(roomIds)
        }
      } catch (e) {
        log('room hook failed: ' + (e && e.message ? e.message : e))
      }

      // ---- opened by another window? (SPEC §7.2 ruling 2) ------------------
      //
      // The flag is consumed HERE, once per register(): a hot reload finds it
      // already gone, and a flag older than 20 s belonged to a session nobody
      // is waiting on any more. No call is ever started: the window comes up
      // showing START TALK, exactly as if Owner had pressed ⌘⌥J himself.
      bootCheck = function () {
       if (bootOpen || bootTimer || !consumeBootFlag()) return
        bootOpen = true
        const until = Date.now() + BOOT_WAIT_MS
        const raise = function () {
          if (appRendered()) {
            bootTimer = null
            try {
              overlay.open()
            } catch (err) {
              log('boot open failed: ' + (err && err.message ? err.message : err))
            }
            return
          }
          if (Date.now() >= until) {
            // ten seconds and the app never drew: the overlay would be
            // appended to a body React is about to replace. Say so instead.
            bootTimer = null
            bootOpen = false
            log('the app root never rendered in 10 s — Jarvis mode stayed closed (press ' +
              jarvisKeyLabelsFor(typeof window !== 'undefined' ? window : null).open + ')')
            heartbeat(true)
            return
          }
          bootTimer = setTimeout(raise, BOOT_POLL_MS)
        }
        ctx.onDispose(function () {
          if (bootTimer) { clearTimeout(bootTimer); bootTimer = null }
        })
        raise()
        log('this window was opened by Jarvis mode — raising the overlay')
      }
      bootCheck()

      heartbeat(true)

      try {
        console.warn('[hermes-jarvis] registered', contributionIds)
      } catch (err) { /* console is a nicety */ }
    } catch (err) {
      lastError = {
        message: String(err && err.message ? err.message : err),
        at: new Date().toISOString()
      }
      heartbeat(true)
      throw err // the loader still toasts and inventories the failure
    }
  }
}
