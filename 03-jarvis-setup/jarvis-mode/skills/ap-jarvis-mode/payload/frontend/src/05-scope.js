// hermes-jarvis — profile and connection isolation helpers.
//
// Plugin REST calls are routed by the desktop SDK. These helpers add the
// second half of the boundary: data is accepted only when the backend states
// the same canonical profile identity as the selected route.

const JARVIS_SOURCE_IDS = [
  'agent_state', 'agent_helpers', 'next_meeting', 'today_plan',
  'overnight_jobs', 'one_thing_scoreboard', 'spend', 'lever', 'brains',
  'scoreboard', 'log'
]

const JARVIS_SOURCE_SET = (function () {
  const out = {}
  for (let i = 0; i < JARVIS_SOURCE_IDS.length; i += 1) out[JARVIS_SOURCE_IDS[i]] = true
  return out
})()
const JARVIS_BOX_IDS = [
  'agent_helpers', 'waiting_on_you', 'agent_in_flight', 'overnight_jobs',
  'next_meeting', 'today', 'spend', 'scoreboard', 'fleet'
]
const JARVIS_BOX_SET = (function () {
  const out = {}
  for (let i = 0; i < JARVIS_BOX_IDS.length; i += 1) out[JARVIS_BOX_IDS[i]] = true
  return out
})()

function jarvisCleanId(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function jarvisHash(value) {
  const text = String(value || '')
  let hash = 2166136261
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(36)
}

function jarvisConnectionId(value) {
  if (value === null) return { ok: true, value: null }
  const text = jarvisCleanId(value)
  return { ok: !!text, value: text || null }
}

function jarvisScope(connectionId, routeProfile, targetProfile) {
  const admitted = jarvisConnectionId(connectionId)
  const connection = admitted.value
  const route = jarvisCleanId(routeProfile)
  const target = jarvisCleanId(targetProfile)
  if (!admitted.ok || !route || !target) return null
  return {
    connectionId: connection,
    routeProfile: route,
    profileId: target,
    id: jarvisHash(JSON.stringify([connection, route, target]))
  }
}

/** The complete route owner selected by Desktop. A focused session owner is
 * authoritative when present; drafts fall back to the active gateway tuple.
 * `connectionId:null` is the explicit local pool, while a missing atom fails. */
function jarvisSelectedOwner(host) {
  const state = host && host.state ? host.state : null
  if (!state) return null
  function read(name) {
    const item = state[name]
    if (!item || typeof item.get !== 'function') return { present: false, value: undefined }
    try { return { present: true, value: item.get() } } catch (err) { return { present: true, value: undefined } }
  }
  const focused = read('focusedSessionOwner')
  const owner = focused.value && typeof focused.value === 'object' ? focused.value : null
  if (owner) {
    const route = jarvisCleanId(owner.profile)
    const connection = jarvisConnectionId(owner.connectionId)
    if (route && connection.ok) return { connectionId: connection.value, routeProfile: route }
    return null
  }
  const connectionRaw = read('connectionId')
  if (!connectionRaw.present) return null
  const connection = jarvisConnectionId(connectionRaw.value)
  const focusedProfile = read('focusedSessionProfile')
  const activeProfile = read('profile')
  const route = jarvisCleanId(focusedProfile.value) || jarvisCleanId(activeProfile.value) || 'default'
  return connection.ok && route ? { connectionId: connection.value, routeProfile: route } : null
}

function jarvisScopedKey(scope, name) {
  if (!scope || !scope.id || !jarvisCleanId(name)) return null
  return 'hermes-jarvis:' + scope.id + ':' + jarvisCleanId(name)
}

function jarvisScopedReceipt(scope, stem, hermesRoot) {
  const root = jarvisCleanId(hermesRoot).replace(/[\\/]+$/, '')
  if (!scope || !scope.id || !jarvisCleanId(stem) || !root) return null
  const separator = root.indexOf('\\') >= 0 && root.indexOf('/') < 0 ? '\\' : '/'
  return root + separator + 'jarvis' + separator + jarvisCleanId(stem) + '-' + scope.id + '.json'
}

function jarvisSourceEnabled(settings, id) {
  return !!settings && Array.isArray(settings.enabled_sources) &&
    settings.enabled_sources.indexOf(String(id || '')) >= 0
}

function jarvisValidateSettings(raw, expectedProfile) {
  const expected = jarvisCleanId(expectedProfile)
  if (!expected) return { ok: false, reason: 'selected profile identity is unavailable', settings: null }
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, reason: 'dashboard backend did not identify its chief profile', settings: null }
  }
  if (!Number.isInteger(raw.schema_version) || raw.schema_version !== 1) {
    return { ok: false, reason: 'dashboard settings schema is unsupported', settings: null }
  }
  const profileId = jarvisCleanId(raw.profile_id)
  if (!profileId || profileId !== expected) {
    return { ok: false, reason: 'connect to this chief profile dashboard', settings: null }
  }
  const agentName = jarvisCleanId(raw.agent_name)
  const ownerLabel = jarvisCleanId(raw.owner_label)
  const timezone = jarvisCleanId(raw.timezone)
  if (!agentName || !ownerLabel || !timezone || !Array.isArray(raw.enabled_sources) || !Array.isArray(raw.brains)) {
    return { ok: false, reason: 'dashboard settings are incomplete', settings: null }
  }
  const enabled = []
  for (let i = 0; i < raw.enabled_sources.length; i += 1) {
    const id = jarvisCleanId(raw.enabled_sources[i])
    if (!JARVIS_SOURCE_SET[id]) return { ok: false, reason: 'dashboard settings contain an unknown source', settings: null }
    if (enabled.indexOf(id) < 0) enabled.push(id)
  }
  const brains = []
  for (let i = 0; i < raw.brains.length; i += 1) {
    const row = raw.brains[i]
    const id = jarvisCleanId(row && row.id)
    const label = jarvisCleanId(row && row.label)
    if (!id || !label) return { ok: false, reason: 'dashboard brain labels are incomplete', settings: null }
    brains.push({ id: id, label: label })
  }
  let enabledBoxes = null
  if (Object.prototype.hasOwnProperty.call(raw, 'enabled_boxes')) {
    if (!Array.isArray(raw.enabled_boxes)) {
      return { ok: false, reason: 'dashboard box selection is malformed', settings: null }
    }
    enabledBoxes = []
    for (let i = 0; i < raw.enabled_boxes.length; i += 1) {
      if (typeof raw.enabled_boxes[i] !== 'string') {
        return { ok: false, reason: 'dashboard box selection is malformed', settings: null }
      }
      const id = jarvisCleanId(raw.enabled_boxes[i])
      if (!JARVIS_BOX_SET[id] || enabledBoxes.indexOf(id) >= 0) {
        return { ok: false, reason: 'dashboard box selection is malformed', settings: null }
      }
      enabledBoxes.push(id)
    }
  }
  return {
    ok: true,
    reason: '',
    settings: {
      schema_version: 1,
      profile_id: profileId,
      agent_name: agentName,
      owner_label: ownerLabel,
      timezone: timezone,
      enabled_sources: enabled,
      brains: brains,
      enabled_boxes: enabledBoxes
    }
  }
}

function jarvisSettingsSignature(settings) {
  if (!settings) return ''
  return JSON.stringify([
    settings.profile_id, settings.agent_name, settings.owner_label,
    settings.timezone, settings.enabled_sources, settings.brains,
    settings.enabled_boxes
  ])
}

function jarvisTargetProfile(host, connectionId, routeProfile) {
  const admitted = jarvisConnectionId(connectionId)
  const connection = admitted.value
  const route = jarvisCleanId(routeProfile)
  if (!admitted.ok || !route) return Promise.resolve('')
  if (!host || typeof host.profileRoutes !== 'function') return Promise.resolve('')
  return Promise.resolve(host.profileRoutes()).then(function (rows) {
    const list = Array.isArray(rows) ? rows : []
    if (connection === null) {
      const localMatches = []
      for (let i = 0; i < list.length; i += 1) {
        const row = list[i] || {}
        if (jarvisCleanId(row.mode) !== 'local' || jarvisCleanId(row.profile) !== route) continue
        const target = jarvisCleanId(row.targetProfile)
        if (target) localMatches.push(target)
      }
      return localMatches.length === 1 ? localMatches[0] : ''
    }
    for (let i = 0; i < list.length; i += 1) {
      const row = list[i] || {}
      const rowConnection = Object.prototype.hasOwnProperty.call(row, 'connectionId')
        ? jarvisConnectionId(row.connectionId) : { ok: false, value: null }
      if (rowConnection.ok && rowConnection.value === connection && jarvisCleanId(row.profile) === route) {
        return jarvisCleanId(row.targetProfile)
      }
    }
    return ''
  }).catch(function () { return '' })
}

// --- keyboard shortcut labels ------------------------------------------------
//
// V1 scope ruling (2026-09-22): the main computer is a Mac OR a Windows PC, so
// every chord printed on the glass has two spellings — ⌃⌥T on a Mac,
// Ctrl+Alt+T on Windows. The CHORD does not change: it is the same two physical
// keys (Control and Alt/Option) in both places, which is `ctrlKey && altKey` to
// every browser, so only the LABEL is platform-aware and the key handling is
// not. `mod+alt+j`, the chord Hermes registers to open Jarvis mode, resolves to
// Command on a Mac and Control on Windows, so it gets the same treatment.
//
// The platform is read inside the renderer and nowhere else: `userAgentData`
// first (Chromium ships it and it is not the deprecated one), then
// `navigator.platform`. An unreadable answer keeps the Mac glyphs, which is
// what Hermes Desktop itself prints.

const JARVIS_MAC_KEYS = Object.freeze({
  platform: 'mac',
  talk: '⌃⌥T', mute: '⌃⌥M', sleep: '⌃⌥Z',
  window: '⌃⌥W', full: '⌃⌥F', drawer: '⌃⌥D',
  open: '⌘⌥J'
})

const JARVIS_WINDOWS_KEYS = Object.freeze({
  platform: 'windows',
  talk: 'Ctrl+Alt+T', mute: 'Ctrl+Alt+M', sleep: 'Ctrl+Alt+Z',
  window: 'Ctrl+Alt+W', full: 'Ctrl+Alt+F', drawer: 'Ctrl+Alt+D',
  open: 'Ctrl+Alt+J'
})

/** The platform string a browser will admit to, or '' when it will not. */
function jarvisReadPlatform(nav) {
  if (!nav || typeof nav !== 'object') return ''
  try {
    const hinted = nav.userAgentData
    if (hinted && typeof hinted.platform === 'string' && hinted.platform.trim()) {
      return hinted.platform.trim()
    }
  } catch (err) { /* a host that guards the getter answers nothing */ }
  try {
    if (typeof nav.platform === 'string' && nav.platform.trim()) return nav.platform.trim()
  } catch (err) { /* same */ }
  return ''
}

/** Read only the window we were handed — never a global. A renderer always has
 *  one, and a test that passes a bare object gets the honest default. */
function jarvisPlatformName(win) {
  return jarvisReadPlatform(win && win.navigator ? win.navigator : null)
}

/** 'Windows' (userAgentData) and 'Win32'/'Win64' (navigator.platform) are the
 *  only answers that mean a Windows PC. Anything else — including nothing at
 *  all — keeps the Mac glyphs. */
function jarvisIsWindowsPlatform(name) {
  return /^win/i.test(String(name == null ? '' : name).trim())
}

/** The label set for a platform string. Pure: the unit test drives it. */
function jarvisKeyLabels(platform) {
  return jarvisIsWindowsPlatform(platform) ? JARVIS_WINDOWS_KEYS : JARVIS_MAC_KEYS
}

/** The label set for a window. What every caller in the plugin actually uses. */
function jarvisKeyLabelsFor(win) {
  return jarvisKeyLabels(jarvisPlatformName(win))
}
