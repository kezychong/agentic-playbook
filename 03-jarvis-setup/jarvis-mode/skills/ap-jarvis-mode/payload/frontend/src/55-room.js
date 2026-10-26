// hermes-jarvis — file 55: the display-only ROOM (SPEC §5 row D, §1 placement).
//
//   registerJarvisRoom(ctx, deps)
//     deps = { presence, data, createScene, HermesSDK, React, log, overlay }
//
// A page at `/jarvis` plus a sidebar row, registered through the hook
// 60-plugin.js calls. It is a WINDOW, not a cockpit:
//
//   The chat composer owns the microphone lease. `useComposerVoiceLifetime`
//   (apps/desktop/src/app/chat/composer/hooks/use-composer-voice.ts) ABORTS the
//   voice lease on a real composer unmount — and navigating to a contributed
//   route unmounts the composer. So a page can never be where Talk is driven;
//   put a start button here and it would hang up the call that pressing it was
//   meant to join. That is why the voice controls live in the full-window
//   overlay (the open chord), which floats OVER the chat and leaves the composer mounted,
//   and why the banner on this page says so out loud instead of hiding it.
//
// This file therefore: subscribes to the SAME presence/data stores the overlay
// reads (it never start()s or stop()s them — 60-plugin.js owns their lifetime),
// paints the same scene, never calls getUserMedia, and never starts or stops a
// call. On unmount it unsubscribes and destroys only its own scene.
//
// No import / export (scripts/build.py concatenates src/*.js into one module),
// and React.createElement only — runtime plugins get `react` but never
// `react-dom`, so JSX and portals are both off the table.

const JARVIS_ROOM_PATH = '/jarvis'
/** The chord labels this computer prints (05-scope.js). Mac glyphs on a Mac,
 *  Ctrl+Alt on a Windows PC, Mac glyphs when the platform will not say. */
function jarvisRoomKeys() {
  return jarvisKeyLabelsFor(typeof window !== 'undefined' ? window : null)
}

function jarvisRoomBanner() {
  return 'Display only · voice controls live in the overlay (' + jarvisRoomKeys().open +
    ') — opening this page does not start or stop Talk'
}

function registerJarvisRoom(ctx, deps) {
  const d = deps || {}
  const R = d.React || (typeof React !== 'undefined' ? React : null)
  const SDK = d.HermesSDK || (typeof HermesSDK !== 'undefined' ? HermesSDK : null)
  const log = typeof d.log === 'function' ? d.log : function () {}

  if (!ctx || typeof ctx.registerMany !== 'function') {
    log('room: no ctx.registerMany — route not registered')
    return []
  }
  if (!R || typeof R.createElement !== 'function') {
    log('room: no React — route not registered')
    return []
  }

  // The app exports both area names from @hermes/plugin-sdk
  // (apps/desktop/src/sdk/index.ts:1605). The literals are the same values
  // routes.ts defines, kept as a fallback for an older shell.
  const ROUTES_AREA = (SDK && SDK.ROUTES_AREA) || 'routes'
  const SIDEBAR_NAV_AREA = (SDK && SDK.SIDEBAR_NAV_AREA) || 'sidebar.nav'

  const presence = d.presence || null
  const data = d.data || null
  const overlay = d.overlay || null
  const sceneFactory = typeof d.createScene === 'function' ? d.createScene : null
  const tokens = (typeof JARVIS_TOKENS === 'object' && JARVIS_TOKENS) ? JARVIS_TOKENS : {
    bg: '#07080C', line: '#1F2229', silver: '#8A93A6', bodyDark: '#C8CDD8',
    wash: '#E5EBFF', cobaltBright: '#3A62FF'
  }
  const modeColors = (typeof JARVIS_MODE_COLORS === 'object' && JARVIS_MODE_COLORS) ? JARVIS_MODE_COLORS : {}
  const MONO = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace"
  const SANS = "'DM Sans', system-ui, -apple-system, sans-serif"
  const READOUT_MS = 100 // the mode readout repaints at 10 Hz, never per frame

  function reducedMotion() {
    try {
      return Boolean(typeof window !== 'undefined' && window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches)
    } catch (err) {
      return false
    }
  }

  function dpr() {
    try {
      return (typeof window !== 'undefined' && window.devicePixelRatio) || 1
    } catch (err) {
      return 1
    }
  }

  // ---- the page --------------------------------------------------------

  function JarvisRoomPage() {
    const hostRef = R.useRef(null)
    const canvasRef = R.useRef(null)
    const readoutRef = R.useRef(null)

    R.useEffect(function () {
      const canvas = canvasRef.current
      const host = hostRef.current
      const doc = typeof document !== 'undefined' ? document : null
      const win = typeof window !== 'undefined' ? window : null

      let scene = null
      let offPresence = null
      let offData = null
      let resizeObs = null
      let onResize = null
      let onVisibility = null
      let lastReadout = 0
      let wantRunning = false

      if (canvas && sceneFactory) {
        try {
          scene = sceneFactory(canvas, { reducedMotion: reducedMotion(), dpr: dpr() })
        } catch (err) {
          scene = null
          log('room scene failed: ' + (err && err.message ? err.message : err))
        }
      }

      function measure() {
        if (!scene || typeof scene.setSize !== 'function') return
        const box = host || canvas
        if (!box) return
        const w = box.clientWidth || (win ? win.innerWidth : 0)
        const h = box.clientHeight || (win ? win.innerHeight : 0)
        if (w > 0 && h > 0) scene.setSize(w, h)
      }

      function paintReadout(p, force) {
        const node = readoutRef.current
        if (!node || !p) return
        const at = Date.now()
        if (!force && at - lastReadout < READOUT_MS) return
        lastReadout = at
        const mode = String(p.mode || 'idle')
        const src = (p.source && p.source.status) || 'none'
        node.textContent = (p.demo ? 'DEMO · ' : '') + mode + ' · call ' + String(p.call || 'off') + ' · source ' + src
        try {
          node.style.color = modeColors[mode] || tokens.silver
        } catch (err) { /* colour is a nicety */ }
      }

      // The stores are started and stopped by 60-plugin.js for the whole
      // plugin's lifetime. This page only listens.
      if (presence && typeof presence.subscribe === 'function') {
        offPresence = presence.subscribe(function (p) {
          if (scene && typeof scene.setPresence === 'function') scene.setPresence(p)
          paintReadout(p, false)
        })
      }
      if (data && typeof data.subscribe === 'function') {
        offData = data.subscribe(function (value) {
          if (scene && typeof scene.setData === 'function') scene.setData(value)
        })
      }
      if (presence && typeof presence.get === 'function') {
        const first = presence.get()
        if (scene && typeof scene.setPresence === 'function') scene.setPresence(first)
        paintReadout(first, true)
      }
      if (data && typeof data.get === 'function' && scene && typeof scene.setData === 'function') {
        scene.setData(data.get())
      }

      measure()
      if (scene && typeof scene.start === 'function' && !(doc && doc.hidden)) {
        wantRunning = true
        scene.start()
      } else if (scene) {
        wantRunning = true // start it when the window comes back
      }

      // Only a live scene needs measuring, so a banner-only build wires no
      // listeners at all rather than leaving no-ops on the window.
      if (scene) {
        if (win && typeof win.ResizeObserver === 'function' && host) {
          try {
            resizeObs = new win.ResizeObserver(measure)
            resizeObs.observe(host)
          } catch (err) {
            resizeObs = null
          }
        }
        if (!resizeObs && win) {
          onResize = measure
          win.addEventListener('resize', onResize)
        }
      }

      // A hidden window must not burn a GPU on an animation nobody sees. The
      // scene skips frames on document.hidden by itself; stopping the loop
      // outright also drops its keep-alive interval.
      if (scene && doc && typeof doc.addEventListener === 'function') {
        onVisibility = function () {
          if (!scene || !wantRunning) return
          try {
            if (doc.hidden) scene.stop()
            else { scene.start(); measure() }
          } catch (err) { /* a dead scene cannot block a tab switch */ }
        }
        doc.addEventListener('visibilitychange', onVisibility)
      }

      return function cleanup() {
        if (offPresence) { try { offPresence() } catch (err) { /* gone */ } offPresence = null }
        if (offData) { try { offData() } catch (err) { /* gone */ } offData = null }
        if (resizeObs) { try { resizeObs.disconnect() } catch (err) { /* gone */ } resizeObs = null }
        if (onResize && win) { win.removeEventListener('resize', onResize); onResize = null }
        if (onVisibility && doc) { doc.removeEventListener('visibilitychange', onVisibility); onVisibility = null }
        if (scene) {
          try {
            if (typeof scene.stop === 'function') scene.stop()
            if (typeof scene.destroy === 'function') scene.destroy()
          } catch (err) { /* already gone */ }
          scene = null
        }
        // presence/data are NOT stopped here — they belong to the plugin.
      }
    }, [])

    const openOverlay = function () {
      if (!overlay || typeof overlay.open !== 'function') return
      try {
        overlay.open()
      } catch (err) {
        log('room: overlay.open failed: ' + (err && err.message ? err.message : err))
      }
    }

    const eyebrow = R.createElement('span', {
      style: { font: '600 10px/1 ' + MONO, letterSpacing: '.14em', textTransform: 'uppercase', color: tokens.silverBright || tokens.silver }
    }, 'Jarvis mode · room')

    const readout = R.createElement('span', {
      ref: readoutRef,
      style: { font: '500 11px/1 ' + MONO, letterSpacing: '.04em', color: tokens.silverBright || tokens.silver }
    }, 'no signal yet')

    const button = R.createElement('button', {
      type: 'button',
      onClick: openOverlay,
      disabled: !(overlay && typeof overlay.open === 'function'),
      title: 'Open Jarvis mode over the chat (' + jarvisRoomKeys().open + ')',
      style: {
        font: '500 11px/1 ' + SANS,
        color: tokens.wash,
        background: 'rgba(255,255,255,.04)',
        border: '1px solid ' + (tokens.lineBright || tokens.line),
        borderRadius: '8px',
        padding: '6px 12px',
        cursor: overlay && typeof overlay.open === 'function' ? 'pointer' : 'default'
      }
    }, 'Open overlay')

    const header = R.createElement('div', {
      style: {
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '12px 16px 0 16px', flex: '0 0 auto'
      }
    }, eyebrow, readout, R.createElement('span', { style: { flex: '1 1 auto' } }), button)

    // The honest line. It is not decoration: it is the whole reason this page
    // has no start/stop control (SPEC §1 placement decision).
    const banner = R.createElement('div', {
      role: 'note',
      style: {
        margin: '10px 16px 0 16px', padding: '8px 12px', flex: '0 0 auto',
        font: '400 12px/1.4 ' + SANS, color: tokens.bodyDark,
        background: 'rgba(255,255,255,.04)',
        border: '1px solid ' + (tokens.lineBright || tokens.line), borderRadius: '10px'
      }
    }, jarvisRoomBanner())

    const stage = sceneFactory
      ? R.createElement('div', {
        ref: hostRef,
        style: { position: 'relative', flex: '1 1 auto', minHeight: 0, margin: '12px 0 0 0' }
      }, R.createElement('canvas', {
        ref: canvasRef,
        style: { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', display: 'block' }
      }))
      // No renderer in this build: the banner is the whole page rather than an
      // empty black rectangle pretending to be a scene.
      : null

    return R.createElement('div', {
      // §4.8 ruling 5: the probe skips anything under `jv-room` (and the
      // overlay's `jv-overlay`), so Jarvis's own buttons are never counted as
      // Talk doors in a heartbeat receipt.
      className: 'jv-room',
      style: {
        position: 'relative', width: '100%', height: '100%',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        background: 'radial-gradient(64% 52% at 50% 60%, rgba(58,98,255,.26) 0%, rgba(58,98,255,.09) 46%, rgba(58,98,255,0) 72%), ' +
          'radial-gradient(128% 106% at 50% 46%, rgba(8,12,34,0) 34%, rgba(8,12,34,.55) 100%), ' + (tokens.navy || tokens.bg),
        color: tokens.bodyDark, fontFamily: SANS
      }
    }, header, banner, stage)
  }

  // ---- contributions ----------------------------------------------------
  //
  // Shapes copied from the bundled Kanban plugin
  // (apps/desktop/src/plugins/kanban/plugin.tsx:106-118), which is what
  // apps/desktop/src/app/routes.ts actually reads:
  //   routes     — `data: { path }` (RouteContribution) and `render` on the
  //                CONTRIBUTION (contributedRoutes() reads c.data.path,
  //                c.title and c.render — routes.ts:105-116).
  //   sidebar.nav— a DATA-only row `{ codicon, label, path }`
  //                (SidebarNavContribution, routes.ts:127-136).

  const contributions = [
    {
      id: 'jarvis-room-page',
      area: ROUTES_AREA,
      title: 'Jarvis mode',
      data: { path: JARVIS_ROOM_PATH },
      render: function () { return R.createElement(JarvisRoomPage, null) }
    },
    {
      id: 'jarvis-room-nav',
      area: SIDEBAR_NAV_AREA,
      order: 52,
      data: { codicon: 'radio-tower', label: 'Jarvis mode', path: JARVIS_ROOM_PATH }
    }
  ]

  ctx.registerMany(contributions)
  log('room registered at ' + JARVIS_ROOM_PATH + (sceneFactory ? '' : ' (banner only — no scene in this build)'))

  return contributions.map(function (c) { return c.id })
}
