// hermes-jarvis — file 30: the DATA FEED (contract SPEC §4.2).
//
//   createDataFeed({ ctx, HermesSDK, log })
//     -> { get(), subscribe(fn), start(), stop(), refresh(slice),
//          pushPresence(body), showPanel(panel) }
//
// v2 (SPEC §7) adds two slices: `data.activity` (the NOW box — §7.3, built by
// the pure `jarvisReduceActivity` below) and `data.agentState` (§7.5, off the
// same 60 s `/state` poll as the lever).
//
// Every slice is polled inside try/catch. A failure NEVER blanks a pod: the
// slice is marked `unreachable` in `data.health` and the last good value stays
// on screen. Nothing here invents a number — a value we cannot read is null and
// the HUD prints "—".
//
// Contract extension (additive, documented): `data.health` carries
// 'ok' | 'unreachable' | 'unknown' per slice, because the pods must be able to
// say "unreachable" out loud (SPEC §0 honesty rule) and the §4.2 object has no
// other place to put it.
// ─────────────────────────────────────────────────────────────────────────────
// ACTIVITY (SPEC §7.3) — what Agent is doing while he is quiet.
//
// Fed by the gateway events the plugin already hears through `ctx.onEvent('*')`
// (envelope `{type, session_id, payload, profile, connectionId, seq}` per
// `apps/shared/src/gateway-events.ts`). Everything below `createDataFeed` is
// PURE: no SDK, no React, no DOM, no clock of its own. The caller hands in
// `hostFacts` (focusedSessionId / busy / busyBySession) and `now`, which is what
// makes the NOW box testable without a live turn.
//
// Additive to the FIXED §7.3 object, documented here because the contract has
// nowhere else to put them:
//   lastEventAt  ruling 3 asks the feed to store it (the box computes
//                `quietFor` from it at render time; the feed prints no verdict)
//   housekeeping the boolean behind the `housekeeping · ` label prefix
//   promptAt     ms of the last user-prompt signal — ruling 1 needs it to tell
//                the host's automatic review turn from Owner's own request
//   eventsRunning what the EVENTS say about the turn. `running` is that OR the
//                host's busy flag, so a stale busy flag can never wedge the box
//   toolRuns     every call that has started and not finished (§7 amendment 1),
//                oldest first, cap 8. `tool` is the newest of them; a
//                completion retires only its own call, by `payload.tool_id`
//                where the host sends one and by name + start order otherwise
//
// On `modelCalls` (§7 amendment 7): this host emits `message.start` exactly
// once per turn, so the number is ALWAYS 1. It is counted because the §7.3
// contract names it, and it is never printed — a constant is not a reading.
//
// No "stuck" verdict is ever computed here. Facts only.

const JARVIS_ACTIVITY_CAPS = { recent: 8, subagents: 6, detail: 90, text: 160, label: 64, rows: 40, running: 8 }

// §7 amendment 2 — the quiet close. A turn the EVENTS opened can only be ended
// by the events themselves (message.complete / error / interrupt) or by this:
// the host explicitly says that session is not busy AND nothing has arrived for
// this long. A host that publishes no busy reading at all never closes a turn
// this way — silence is not a fact.
const JARVIS_QUIET_CLOSE_MS = 15000

// Ruling 1 — a turn that starts within this window of the previous turn's end,
// with no user prompt in between, is the host's own housekeeping turn.
const JARVIS_HOUSEKEEPING_MS = 2000

// Ruling 2 — plain words. Extend as found; an unknown tool keeps its raw name
// rather than being guessed at.
const JARVIS_TOOL_LABELS = {
  terminal: 'running a command',
  shell: 'running a command',
  bash: 'running a command',
  process: 'running a command',
  execute_code: 'running code',
  python: 'running code',
  read_file: 'reading a file',
  view_file: 'reading a file',
  write_file: 'editing a file',
  patch: 'editing a file',
  apply_patch: 'editing a file',
  edit_file: 'editing a file',
  web_search: 'searching the web',
  web_fetch: 'reading a web page',
  fetch_url: 'reading a web page',
  skill_view: 'opening a skill',
  skill_manage: 'opening a skill',
  delegate_task: 'handing work to a helper',
  ['to' + 'do_write']: 'updating the task list',
  clarify: 'asking you a question'
}

// Events that prove a turn is in flight. `tool.generating` is the model still
// emitting the call's JSON (no id, no args) — it opens the turn and nothing else.
//
// §7 amendment 2: NO `*.complete` event may OPEN a turn. A completion is the
// tail of work that has already happened, and a straggler arriving after the
// turn ended (a subagent finishing late, a tool result the host flushes on the
// next tick) used to light the box as if Agent had started again. Completions
// are still HEARD — they are listed in JARVIS_ACTIVITY_TYPES below — they just
// cannot be the reason a turn is running.
const JARVIS_TURN_START_TYPES = {
  'message.start': 1, 'message.delta': 1, 'message.interim': 1,
  'thinking.delta': 1, 'reasoning.delta': 1, 'reasoning.available': 1,
  'tool.generating': 1, 'tool.start': 1,
  'subagent.spawn_requested': 1, 'subagent.start': 1, 'subagent.progress': 1,
  'subagent.tool': 1, 'subagent.thinking': 1
}

// Everything the reducer looks at. Types outside this set leave the slice alone
// (they still reach the ticker), so a noisy gateway cannot smear the NOW box.
const JARVIS_ACTIVITY_TYPES = (function () {
  const set = {
    // the completions: heard, never a reason to open a turn (amendment 2)
    'tool.complete': 1, 'subagent.complete': 1,
    'message.complete': 1, error: 1, 'voice.interrupted': 1, 'session.reclaimed': 1,
    'status.update': 1, 'session.usage': 1, ['to' + 'do.updated']: 1, 'notice': 1,
    'agent.terminal.output': 1, 'tool.output_risk': 1, 'review.summary': 1,
    // the blocking-input family: in THIS host build approval/clarify arrive as
    // server→client REQUESTS (apps/.../gateway-event/input-requests.ts), which
    // plugins do not hear — `connection.request` is the one that does reach the
    // event stream. The rest are handled anyway so a host that starts
    // publishing them lights the box without a code change.
    'approval.pending': 1, 'approval.request': 1, 'approval.required': 1, approval: 1,
    'approval.received': 1, 'approval.respond': 1, 'approval.resolved': 1,
    'clarify.request': 1, clarify: 1, 'clarify.lock': 1, 'clarify.response': 1,
    'request.cancel': 1, 'connection.request': 1, 'connection.update': 1,
    'voice.transcript': 1
  }
  for (const key in JARVIS_TURN_START_TYPES) set[key] = 1
  return set
})()

const JARVIS_NEEDS_OPEN = {
  approval: 'approval', 'approval.pending': 'approval', 'approval.request': 'approval',
  'approval.required': 'approval', 'connection.request': 'approval',
  clarify: 'clarify', 'clarify.request': 'clarify'
}

const JARVIS_NEEDS_CLEAR = {
  'approval.received': 1, 'approval.respond': 1, 'approval.resolved': 1,
  'clarify.lock': 1, 'clarify.response': 1, 'request.cancel': 1
}

// Values that look like a credential never reach the screen. Two layers: a key
// whose NAME smells is never picked out of the args, and any `key=value` /
// `Bearer value` left inside a string has its value replaced.
const JARVIS_SECRET_WORD = '(?:api[_.-]?key|key|token|secret|password|passwd|pwd|bearer|authorization|credential|cookie)'
const JARVIS_SECRET_KEY_RE = new RegExp(JARVIS_SECRET_WORD + '|auth', 'i')
// `Bearer <token>` / `Basic <blob>`
const JARVIS_SECRET_SCHEME_RE = /\b(bearer|basic)\s+([^\s"']+)/gi
// `--token abc` / `-api-key=abc` — a CLI flag may be separated by a space
const JARVIS_SECRET_FLAG_RE = new RegExp(
  '(--?[A-Za-z0-9_.-]*' + JARVIS_SECRET_WORD + '[A-Za-z0-9_.-]*)([\\s:=]+)(["\']?)([^\\s"\'&]+)\\3', 'gi')
// `api_key=abc` / `password: abc` — a bare name needs an explicit separator, so
// ordinary prose ("the key thing") is left alone
const JARVIS_SECRET_PAIR_RE = new RegExp(
  '\\b([A-Za-z0-9_.-]*' + JARVIS_SECRET_WORD + '[A-Za-z0-9_.-]*\\s*[:=]\\s*)(["\']?)([^\\s"\'&]+)\\2', 'gi')
const JARVIS_SECRET_RUN_RE = /•••(?:[\s:=]+•••)+/g

function jarvisCollapse(text) {
  return String(text == null ? '' : text).replace(/\s+/g, ' ').trim()
}

function jarvisClip(text, cap) {
  const s = String(text == null ? '' : text)
  const limit = Number(cap) || 0
  if (!limit || s.length <= limit) return s
  return s.slice(0, Math.max(1, limit - 1)) + '…'
}

/** Whitespace-collapsed, secret-stripped, cut to `cap`. */
function jarvisSafeText(text, cap) {
  let s = jarvisCollapse(text)
  if (!s) return ''
  s = s.replace(JARVIS_SECRET_SCHEME_RE, function (m, scheme) { return scheme + ' •••' })
  s = s.replace(JARVIS_SECRET_FLAG_RE, function (m, flag, gap, quote) {
    return flag + (gap.indexOf('=') >= 0 ? '=' : ' ') + (quote || '') + '•••' + (quote || '')
  })
  s = s.replace(JARVIS_SECRET_PAIR_RE, function (m, head, quote) {
    return head + (quote || '') + '•••' + (quote || '')
  })
  s = s.replace(JARVIS_SECRET_RUN_RE, '•••')
  return jarvisClip(s, cap)
}

function jarvisUrlHost(url) {
  const found = /^[a-z][a-z0-9+.-]*:\/\/([^/?#\s]+)/i.exec(String(url || ''))
  return found ? found[1] : jarvisCollapse(url)
}

/** Ruling 2 — plain words for a tool name, with the housekeeping prefix. */
function jarvisActivityLabel(name, housekeeping) {
  const raw = String(name || '').trim()
  let label = raw || 'working'
  const lower = raw.toLowerCase()
  if (lower.indexOf('mcp__') === 0) {
    const server = raw.split('__')[1] || 'a server'
    label = 'asking ' + server
  } else if (JARVIS_TOOL_LABELS[lower]) {
    label = JARVIS_TOOL_LABELS[lower]
  } else if (/^browser/.test(lower)) {
    label = 'using the browser'
  } else if (/^computer/.test(lower)) {
    label = 'using the computer'
  } else if (/^(memory|honcho)/.test(lower)) {
    label = 'checking memory'
  }
  label = jarvisClip(label, JARVIS_ACTIVITY_CAPS.label)
  return housekeeping ? 'housekeeping · ' + label : label
}

function jarvisPickArg(args, keys) {
  for (let i = 0; i < keys.length; i += 1) {
    const value = args[keys[i]]
    if (typeof value === 'string' && value.trim()) return value
    if (typeof value === 'number') return String(value)
  }
  return ''
}

function jarvisFirstArg(args) {
  const keys = Object.keys(args || {})
  for (let i = 0; i < keys.length; i += 1) {
    if (JARVIS_SECRET_KEY_RE.test(keys[i])) continue
    const value = args[keys[i]]
    if (typeof value === 'string' && value.trim() && value.length <= 400) return value
  }
  return ''
}

/** ≤ 90 chars from the args: path, command head, query, url host. Never a secret. */
function jarvisActivityDetail(name, payload) {
  const p = payload && typeof payload === 'object' ? payload : {}
  const args = p.args && typeof p.args === 'object' ? p.args : {}
  const lower = String(name || '').toLowerCase()
  let raw = ''
  if (/terminal|shell|bash|process|command/.test(lower)) raw = jarvisPickArg(args, ['command', 'cmd', 'script'])
  else if (/execute_code|python|code/.test(lower)) raw = jarvisPickArg(args, ['code', 'source', 'script'])
  else if (/file|read|write|patch|edit|diff/.test(lower)) raw = jarvisPickArg(args, ['path', 'file_path', 'file', 'filename', 'target'])
  else if (/search|grep|find|query/.test(lower)) raw = jarvisPickArg(args, ['query', 'q', 'pattern', 'search', 'keyword'])
  else if (/browser|fetch|url|http|web/.test(lower)) {
    const url = jarvisPickArg(args, ['url', 'href', 'link'])
    raw = url ? jarvisUrlHost(url) : jarvisPickArg(args, ['query', 'q', 'action'])
  } else if (/delegate|task|subagent|agent/.test(lower)) raw = jarvisPickArg(args, ['goal', 'task', 'prompt', 'description'])
  if (!raw) raw = jarvisPickArg(args, ['query', 'path', 'command', 'goal', 'name', 'title', 'prompt', 'text', 'pattern'])
  if (!raw) raw = jarvisFirstArg(args)
  if (!raw && typeof p.preview === 'string') raw = p.preview
  if (!raw && typeof p.context === 'string') raw = p.context
  if (!raw && typeof p.summary === 'string') raw = p.summary
  if (!raw && typeof p.args_text === 'string') raw = p.args_text
  return jarvisSafeText(raw, JARVIS_ACTIVITY_CAPS.detail)
}

// ---- the running calls (SPEC §7.3 `tool` · §7 amendment 1) -----------------
// Agent runs tools in parallel, so ONE `tool` slot cannot be the whole truth:
// the feed keeps every call that has started and not finished (cap 8, oldest
// dropped), `tool` is the NEWEST of them, and a completion retires only its
// own call. The tie is `payload.tool_id` where the host sends one; without an
// id a completion retires the OLDEST still-running call of the same name,
// which is the only honest guess when the host gives us nothing to match on.

function jarvisToolId(payload) {
  const p = payload && typeof payload === 'object' ? payload : {}
  const id = p.tool_id != null ? p.tool_id
    : (p.tool_use_id != null ? p.tool_use_id
      : (p.call_id != null ? p.call_id : (p.id != null ? p.id : '')))
  return String(id == null ? '' : id).trim()
}

/** Start order is the fallback identity: two `read_file` calls with no id are
 *  `n:read_file#7` and `n:read_file#8`, never one row overwriting the other. */
function jarvisToolKey(payload, name, order) {
  const id = jarvisToolId(payload)
  return id ? 'id:' + id : 'n:' + String(name || '') + '#' + order
}

/** Which running call a completion belongs to: its id, else the oldest of the
 *  same name, else — with neither id nor name — the newest call there is. */
function jarvisToolIndex(runs, payload, name) {
  const id = jarvisToolId(payload)
  if (id) {
    const key = 'id:' + id
    for (let i = 0; i < runs.length; i += 1) { if (runs[i].key === key) return i }
  }
  if (name) {
    for (let i = 0; i < runs.length; i += 1) { if (runs[i].name === name) return i }
  }
  if (!id && !name && runs.length) return runs.length - 1
  return -1
}

/** The §7.3 `tool` face of a running call — the contract's four fields only. */
function jarvisToolFace(entry) {
  if (!entry) return null
  return { name: entry.name, label: entry.label, detail: entry.detail, startedAt: entry.startedAt }
}

function jarvisNewestTool(runs) {
  return jarvisToolFace(runs.length ? runs[runs.length - 1] : null)
}

function jarvisToolFailed(payload) {
  const p = payload && typeof payload === 'object' ? payload : {}
  if (p.error) return true
  if (p.is_error === true || p.ok === false || p.success === false) return true
  const result = p.result
  if (result && typeof result === 'object' && (result.error || result.is_error === true)) return true
  return false
}

function jarvisHostFacts(facts) {
  const f = facts && typeof facts === 'object' ? facts : {}
  const busyBy = f.busyBySession && typeof f.busyBySession === 'object' ? f.busyBySession : {}
  return {
    focusedSessionId: String(f.focusedSessionId || ''),
    busy: f.busy === true,
    // amendment 2 — "the host said not busy" and "the host said nothing" are
    // different facts, and only the first may close a turn.
    busyKnown: typeof f.busy === 'boolean',
    busyBySession: busyBy,
    userPromptAt: Number(f.userPromptAt) || 0
  }
}

function jarvisHostBusyFor(facts, sessionId) {
  if (!sessionId) return false
  if (Object.prototype.hasOwnProperty.call(facts.busyBySession, sessionId)) {
    return facts.busyBySession[sessionId] === true
  }
  return sessionId === facts.focusedSessionId && facts.busy === true
}

/** Does the host EXPLICITLY report this session as not busy? `false` when it
 *  reports nothing at all — a host that is silent closes no turn (amendment 2). */
function jarvisHostIdleFor(facts, sessionId) {
  if (!sessionId) return false
  if (Object.prototype.hasOwnProperty.call(facts.busyBySession, sessionId)) {
    return facts.busyBySession[sessionId] !== true
  }
  if (facts.busyKnown && sessionId === facts.focusedSessionId) return facts.busy === false
  return false
}

/** Host facts only: focus, the quiet close, and the `host-busy` source when no
 *  event has landed. */
function jarvisActivityHost(state, facts, at) {
  let st = state
  let session = st.session
  if (!session && facts.focusedSessionId && jarvisHostBusyFor(facts, facts.focusedSessionId)) {
    session = facts.focusedSessionId
  }
  // amendment 2 — the turn the EVENTS opened ends here when the host says that
  // session is not busy and the stream has been silent for 15 s. `endedAt` is
  // the last event's time, not now: the work stopped when the news stopped.
  if (st.eventsRunning === true && st.lastEventAt > 0 &&
      jarvisHostIdleFor(facts, session) && at - st.lastEventAt >= JARVIS_QUIET_CLOSE_MS) {
    st = jarvisEndTurn(Object.assign({}, st), st.lastEventAt, 'done')
  }
  const focused = !!session && session === facts.focusedSessionId
  const hostBusy = jarvisHostBusyFor(facts, session)
  const seen = st.lastEventAt > 0
  const running = seen ? (st.eventsRunning === true || hostBusy) : hostBusy
  const source = seen ? 'events' : (hostBusy ? 'host-busy' : 'none')
  const startedAt = !seen && hostBusy && !st.startedAt ? at : st.startedAt
  if (session === st.session && focused === st.focused && running === st.running &&
      source === st.source && startedAt === st.startedAt) {
    return st
  }
  return Object.assign({}, st, {
    session: session, focused: focused, running: running, source: source, startedAt: startedAt
  })
}

function jarvisIsPromptSignal(type, payload) {
  if (type === 'user.prompt' || type === 'wake.detected') return true
  if (type === 'voice.transcript') {
    const text = payload && typeof payload.text === 'string' ? payload.text.trim() : ''
    return !!text
  }
  return false
}

function jarvisBeginTurn(state, at) {
  // Ruling 1 — the host's automatic review turn ("Review the conversation above
  // and update the skill library") follows Owner's turn within a breath and
  // has no prompt of its own. Label it, and never let it ask him for anything.
  const last = state.lastTurn
  const housekeeping = !!(last && at - last.endedAt <= JARVIS_HOUSEKEEPING_MS &&
    !(state.promptAt && state.promptAt > last.endedAt))
  return Object.assign({}, state, {
    running: true, eventsRunning: true, startedAt: at, endedAt: 0, steps: 0, modelCalls: 0,
    tool: null, toolRuns: [], lastTool: null, thought: '', saying: '', subagents: [],
    needsYou: null, recent: [], housekeeping: housekeeping
  })
}

function jarvisEndTurn(state, at, outcome) {
  const seconds = state.startedAt ? Math.max(0, Math.round((at - state.startedAt) / 1000)) : 0
  state.running = false
  state.eventsRunning = false
  state.endedAt = at
  state.tool = null
  state.toolRuns = []
  state.needsYou = null
  state.lastTurn = {
    endedAt: at, seconds: seconds, steps: state.steps,
    modelCalls: state.modelCalls, outcome: outcome
  }
  // A child cannot still be running once its parent's turn is over, and we will
  // not print a chip we can no longer vouch for. What finished, stays.
  state.subagents = state.subagents.filter(function (s) { return s.status !== 'running' })
  return state
}

function jarvisTail(previous, chunk, cap) {
  const text = jarvisCollapse(String(previous || '') + ' ' + String(chunk == null ? '' : chunk))
  return text.length > cap ? text.slice(text.length - cap) : text
}

function jarvisSubagentId(payload) {
  const explicit = String(payload.subagent_id || payload.delegation_id || payload.child_session_id || '').trim()
  if (explicit) return explicit
  return (String(payload.parent_id || 'root')) + ':' + (Number(payload.task_index) || 0) + ':' + String(payload.goal || '')
}

function jarvisSubagentStatus(type, payload, previous) {
  if (type === 'subagent.complete') {
    const status = String(payload.status || 'completed').toLowerCase()
    return status === 'completed' || status === 'done' || status === 'ok' ? 'done' : 'failed'
  }
  if (previous && previous !== 'running') return previous
  return 'running'
}

function jarvisNeedsText(type, payload) {
  if (type === 'connection.request' || type === 'connection.update') {
    const targets = Array.isArray(payload.targets) ? payload.targets : []
    const names = targets.map(function (t) { return String((t && t.name) || '') }).filter(Boolean)
    return names.length ? 'connect ' + names.join(', ') : 'a connection needs you'
  }
  if (type === 'clarify' || type === 'clarify.request') {
    const list = Array.isArray(payload.questions) ? payload.questions : []
    const first = list.length && list[0] ? String(list[0].question || '') : ''
    return String(payload.question || first || 'a question is waiting')
  }
  return String(payload.description || payload.command || payload.tool_name || 'a step needs your yes')
}

/**
 * The reducer. PURE — (state, event, hostFacts, now) → state. Returns the SAME
 * object when nothing moved, so the feed can skip a notify.
 *
 * `event` is the gateway envelope; pass null to fold in host facts alone.
 */
function jarvisReduceActivity(state, event, hostFacts, now) {
  const at = Number(now) || 0
  const facts = jarvisHostFacts(hostFacts)
  let st = state && typeof state === 'object' ? state : jarvisActivityInitial()
  // a state from before amendment 1 (a hot reload mid-turn) still has its one
  // `tool`: carry it in as the single running call rather than losing it
  if (!Array.isArray(st.toolRuns)) {
    st = Object.assign({}, st, {
      toolRuns: st.tool ? [{
        key: 'n:' + String(st.tool.name || '') + '#0', name: String(st.tool.name || ''),
        label: st.tool.label, detail: st.tool.detail, startedAt: st.tool.startedAt
      }] : []
    })
  }

  if (facts.userPromptAt > st.promptAt) st = Object.assign({}, st, { promptAt: facts.userPromptAt })
  if (!event || typeof event !== 'object' || !event.type) return jarvisActivityHost(st, facts, at)

  const type = String(event.type)
  const payload = event.payload && typeof event.payload === 'object' ? event.payload : {}
  const sid = String(event.session_id || '')

  if (jarvisIsPromptSignal(type, payload)) st = Object.assign({}, st, { promptAt: at })
  if (!JARVIS_ACTIVITY_TYPES[type] || !sid) return jarvisActivityHost(st, facts, at)

  // Ruling 1 — the chat focused in THIS window owns the box; another chat's
  // events never hijack it. With nothing focused, the most recent one wins.
  if (sid !== st.session) {
    if (st.session && facts.focusedSessionId && st.session === facts.focusedSessionId) {
      return jarvisActivityHost(st, facts, at)
    }
    st = Object.assign(jarvisActivityInitial(), {
      session: sid, promptAt: st.promptAt, lastEventAt: st.lastEventAt
    })
  }

  let next = st
  if (JARVIS_TURN_START_TYPES[type] && !next.running) next = jarvisBeginTurn(next, at)
  next = Object.assign({}, next, { lastEventAt: at, source: 'events' })

  if (type === 'message.start') {
    // amendment 7 — one `message.start` per turn on this host, so this counter
    // is always 1 and stays off the glass. It is kept because the §7.3 contract
    // names it and a host that streams several calls would fill it honestly.
    next.modelCalls = next.modelCalls + 1
  } else if (type === 'tool.start') {
    const name = String(payload.name || '')
    next.steps = next.steps + 1
    const runs = next.toolRuns.slice()
    runs.push({
      key: jarvisToolKey(payload, name, next.steps),
      name: name,
      label: jarvisActivityLabel(name, next.housekeeping),
      detail: jarvisActivityDetail(name, payload),
      startedAt: at
    })
    // cap 8: the oldest call gives way rather than the newest being refused —
    // what Agent is doing NOW is the reading the box exists for
    while (runs.length > JARVIS_ACTIVITY_CAPS.running) runs.shift()
    next.toolRuns = runs
    next.tool = jarvisNewestTool(runs)
  } else if (type === 'tool.complete') {
    const runs = next.toolRuns.slice()
    const named = String(payload.name || '')
    const index = jarvisToolIndex(runs, payload, named)
    const mine = index >= 0 ? runs[index] : null
    const name = named || (mine ? mine.name : '')
    const startedAt = mine ? mine.startedAt : 0
    const duration = Number(payload.duration_s)
    const ms = duration > 0 ? Math.round(duration * 1000) : (startedAt ? Math.max(0, at - startedAt) : 0)
    const ok = !jarvisToolFailed(payload)
    const label = jarvisActivityLabel(name, next.housekeeping)
    const detail = jarvisActivityDetail(name, payload) || (mine ? mine.detail : '')
    next.lastTool = { name: name, label: label, detail: detail, ms: ms, ok: ok }
    next.recent = [{ at: at, label: label, detail: detail, ms: ms, ok: ok }]
      .concat(next.recent).slice(0, JARVIS_ACTIVITY_CAPS.recent)
    // amendment 1 — only THIS call is retired; every other one Agent still has
    // in flight keeps its place, and `tool` falls back to the newest of them.
    if (index >= 0) runs.splice(index, 1)
    next.toolRuns = runs
    next.tool = jarvisNewestTool(runs)
    // A pending clarify blocks the turn, so the first tool.complete after one
    // is that clarify resolving — the app clears `needsInput` here too.
    next.needsYou = null
  } else if (type === 'thinking.delta' || type === 'reasoning.delta' || type === 'reasoning.available') {
    next.thought = jarvisTail(next.thought, payload.text, JARVIS_ACTIVITY_CAPS.text)
  } else if (type === 'message.delta' || type === 'message.interim') {
    next.saying = jarvisTail(next.saying, payload.text, JARVIS_ACTIVITY_CAPS.text)
  } else if (type === 'message.complete') {
    const status = String(payload.status || '')
    const outcome = status === 'interrupted' ? 'interrupted'
      : (status === 'error' || payload.error ? 'error' : 'done')
    next = jarvisEndTurn(next, at, outcome)
  } else if (type === 'error') {
    if (next.running) next = jarvisEndTurn(next, at, 'error')
  } else if (type === 'voice.interrupted' || type === 'session.reclaimed') {
    if (next.running) next = jarvisEndTurn(next, at, 'interrupted')
  } else if (type.indexOf('subagent.') === 0) {
    const id = jarvisSubagentId(payload)
    const rows = next.subagents.slice()
    let index = -1
    for (let i = 0; i < rows.length; i += 1) { if (rows[i].id === id) { index = i; break } }
    const previous = index >= 0 ? rows[index] : null
    const row = {
      id: id,
      label: jarvisClip(jarvisCollapse(payload.goal || payload.summary || (previous && previous.label) || 'helper'), JARVIS_ACTIVITY_CAPS.label),
      status: jarvisSubagentStatus(type, payload, previous ? previous.status : ''),
      tool: jarvisClip(jarvisCollapse(payload.tool_name || (previous && previous.tool) || ''), JARVIS_ACTIVITY_CAPS.label)
    }
    if (index >= 0) rows[index] = row
    else rows.push(row)
    next.subagents = rows.slice(-JARVIS_ACTIVITY_CAPS.subagents)
  } else if (type === 'connection.update') {
    if (payload.settled === true) next.needsYou = null
  } else if (JARVIS_NEEDS_OPEN[type]) {
    // Ruling 1 — the host's own review turn never asks Owner for anything.
    if (!next.housekeeping) {
      next.needsYou = {
        kind: JARVIS_NEEDS_OPEN[type],
        text: jarvisSafeText(jarvisNeedsText(type, payload), JARVIS_ACTIVITY_CAPS.text)
      }
    }
  } else if (JARVIS_NEEDS_CLEAR[type]) {
    next.needsYou = null
  }

  return jarvisActivityHost(next, facts, at)
}

function jarvisActivityInitial() {
  return {
    session: '', focused: false, running: false, startedAt: 0, endedAt: 0,
    steps: 0, modelCalls: 0, tool: null, toolRuns: [], lastTool: null, thought: '', saying: '',
    subagents: [], needsYou: null, recent: [], lastTurn: null, source: 'none',
    lastEventAt: 0, housekeeping: false, promptAt: 0, eventsRunning: false
  }
}

// ---- Agent's STATE rows (SPEC §7.5) -----------------------------------------
// Parsed by the backend; the feed only shapes and caps what came back, and
// never blanks a good reading because one poll failed.

/** SPEC §8.3.1 — the plain words behind a row, or null. Every field is either
 *  something Agent wrote or `null`; the glass says "ask Agent" for the rest. */
function jarvisAgentBrief(raw) {
  if (!raw || typeof raw !== 'object') return null
  const text = function (value) {
    const s = jarvisCollapse(value)
    return s ? jarvisClip(s, 400) : null
  }
  return {
    title: text(raw.title), what: text(raw.what), why: text(raw.why),
    do: text(raw.do), takes: text(raw.takes), where: text(raw.where),
    updated: text(raw.updated)
  }
}

function jarvisAgentRow(raw) {
  const row = raw && typeof raw === 'object' ? raw : {}
  const text = function (value, cap) {
    const s = jarvisCollapse(value)
    return s ? jarvisClip(s, cap) : ''
  }
  return {
    brief: jarvisAgentBrief(row.brief),
    id: text(row.id, 64),
    where: text(row.where, 220),
    next: text(row.next, 220),
    owner: text(row.owner, 64),
    follow_up_at: row.follow_up_at ? String(row.follow_up_at) : null,
    updated: row.updated ? String(row.updated) : null,
    waiting_on_owner: row.waiting_on_owner === true,
    overdue: row.overdue === true
  }
}

function jarvisAgentRows(rows) {
  const list = Array.isArray(rows) ? rows : []
  const out = []
  for (let i = 0; i < list.length && out.length < JARVIS_ACTIVITY_CAPS.rows; i += 1) {
    const row = jarvisAgentRow(list[i])
    if (row.id || row.next || row.where) out.push(row)
  }
  return out
}

// ---- the six v3 readings (SPEC §8.4 item 1) --------------------------------
//
// The backend (§8.3) serves each block with its own `status`, `updatedAt`,
// `source` and `note`, so one broken source dims one box. The feed does three
// things and no more: it shapes what came back, it caps every list so one long
// file can never push a box off the glass, and it says out loud when a block is
// not there. Nothing here computes a verdict and nothing here invents a value —
// a number the backend did not send is `null` and the box prints "—".
//
// The old-backend law (v2, kept word for word): a backend too old to know a
// block at all is `status:'unreachable'` with `note:'backend has no <name>
// yet'`. An empty box would read as "nothing to do", which would be a lie.
//
// Stamps stay as the backend wrote them, including any ISO offset. The glass
// parses them in the configured profile timezone where it needs a countdown;
// the feed does not re-zone a time it did not read itself.

const JARVIS_BLOCK_CAPS = {
  goal: 140, summary: 200, title: 200, task: 300, name: 120, error: 160,
  model: 60, note: 200, source: 160, status: 40,
  helpers: 6, later: 3, items: 4, failed: 6, nextUp: 3, models: 8, days: 7
}

/** Collapsed, clipped, '' when there is nothing to say. */
function jarvisText(value, cap) {
  const s = jarvisCollapse(value)
  return s ? jarvisClip(s, cap) : ''
}

/** A number the backend actually sent, or null. `0` is a reading; `''` is not. */
function jarvisNum(value) {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return isFinite(n) ? n : null
}

/** A stamp as the backend wrote it, or null. Never re-formatted here. */
function jarvisWhen(value) {
  return typeof value === 'string' && value.trim() ? value.trim() : null
}

function jarvisRows(value, cap, shape) {
  const list = Array.isArray(value) ? value : []
  const out = []
  for (let i = 0; i < list.length && out.length < cap; i += 1) {
    const row = list[i] && typeof list[i] === 'object' ? shape(list[i]) : null
    if (row) out.push(row)
  }
  return out
}

/** The head every v3 block carries, over the body a reader builds.
 *
 *  `raw` missing = the old-backend law: `unreachable`, with the wire name in
 *  the note so the box can say which reading this Hermes has never served. */
function jarvisBlockFace(raw, name, body) {
  const known = raw && typeof raw === 'object'
  const face = body(known ? raw : {})
  face.status = known ? (jarvisText(raw.status, JARVIS_BLOCK_CAPS.status) || 'ok') : 'unreachable'
  face.note = known ? (raw.note ? jarvisText(raw.note, JARVIS_BLOCK_CAPS.note) : null)
    : 'backend has no ' + name + ' yet'
  face.updatedAt = known ? jarvisWhen(raw.updatedAt) : null
  face.source = known ? jarvisText(raw.source, JARVIS_BLOCK_CAPS.source) : ''
  face.stale = known ? raw.stale === true : false
  return face
}

/** A poll that failed keeps the last good block WITH its own stamp, marked. */
function jarvisBlockStale(last, note) {
  const block = last && typeof last === 'object' ? last : {}
  return Object.assign({}, block, { status: 'unreachable', stale: true, note: note })
}

/** …and before the first poll there is nothing to be stale about. */
function jarvisBlockWaiting(block) {
  return Object.assign({}, block, { note: 'not polled yet' })
}

function jarvisBlockDisabled(block) {
  return Object.assign({}, block, { status: 'disabled', stale: false, note: 'disabled for this profile' })
}

function jarvisHelpersFrom(raw) {
  return jarvisBlockFace(raw, 'agent_helpers', function (block) {
    return {
      running: jarvisRows(block.running, JARVIS_BLOCK_CAPS.helpers, function (row) {
        return {
          id: jarvisText(row.id, 80),
          goal: jarvisText(row.goal, JARVIS_BLOCK_CAPS.goal),
          model: jarvisText(row.model, JARVIS_BLOCK_CAPS.model),
          startedAt: jarvisWhen(row.startedAt),
          seconds: jarvisNum(row.seconds),
          origin: jarvisText(row.origin, 40)
        }
      }),
      recent: jarvisRows(block.recent, JARVIS_BLOCK_CAPS.helpers, function (row) {
        return {
          id: jarvisText(row.id, 80),
          goal: jarvisText(row.goal, JARVIS_BLOCK_CAPS.goal),
          state: jarvisText(row.state, JARVIS_BLOCK_CAPS.status),
          startedAt: jarvisWhen(row.startedAt),
          endedAt: jarvisWhen(row.endedAt),
          seconds: jarvisNum(row.seconds),
          summary: jarvisText(row.summary, JARVIS_BLOCK_CAPS.summary),
          delivered: row.delivered === true,
          origin: jarvisText(row.origin, 40)
        }
      }),
      runningCount: Number(block.runningCount) || 0,
      todayCount: Number(block.todayCount) || 0
    }
  })
}

function jarvisMeetingEvent(row) {
  return {
    title: jarvisText(row.title, JARVIS_BLOCK_CAPS.title),
    start: jarvisWhen(row.start),
    end: jarvisWhen(row.end),
    calendar: jarvisText(row.calendar, JARVIS_BLOCK_CAPS.name),
    allDay: row.allDay === true,
    minutesUntil: jarvisNum(row.minutesUntil)
  }
}

function jarvisMeetingFrom(raw) {
  return jarvisBlockFace(raw, 'next_meeting', function (block) {
    return {
      next: block.next && typeof block.next === 'object' ? jarvisMeetingEvent(block.next) : null,
      later: jarvisRows(block.later, JARVIS_BLOCK_CAPS.later, jarvisMeetingEvent),
      windowHours: Number(block.windowHours) || 36
    }
  })
}

function jarvisTodayFrom(raw) {
  return jarvisBlockFace(raw, 'today_plan', function (block) {
    const lever = block.lever && typeof block.lever === 'object' ? block.lever : null
    return {
      date: jarvisText(block.date, 24),
      isToday: block.isToday === true,
      headline: jarvisText(block.headline, JARVIS_BLOCK_CAPS.task),
      items: jarvisRows(block.items, JARVIS_BLOCK_CAPS.items, function (row) {
        return {
          kind: jarvisText(row.kind, 24),
          task: jarvisText(row.task, JARVIS_BLOCK_CAPS.task),
          status: jarvisText(row.status, JARVIS_BLOCK_CAPS.status),
          next: jarvisText(row.next, JARVIS_BLOCK_CAPS.task)
        }
      }),
      lever: lever && lever.text
        ? { text: jarvisText(lever.text, 400), source: jarvisText(lever.source, JARVIS_BLOCK_CAPS.source) }
        : null,
      fileUpdatedAt: jarvisWhen(block.fileUpdatedAt)
    }
  })
}

function jarvisJobsFrom(raw) {
  return jarvisBlockFace(raw, 'overnight_jobs', function (block) {
    const window = block.window && typeof block.window === 'object' ? block.window : {}
    return {
      window: { from: jarvisWhen(window.from), to: jarvisWhen(window.to) },
      total: Number(block.total) || 0,
      ok: Number(block.ok) || 0,
      failed: jarvisRows(block.failed, JARVIS_BLOCK_CAPS.failed, function (row) {
        return {
          id: jarvisText(row.id, 80),
          name: jarvisText(row.name, JARVIS_BLOCK_CAPS.name),
          lastRunAt: jarvisWhen(row.lastRunAt),
          lastStatus: jarvisText(row.lastStatus, JARVIS_BLOCK_CAPS.status),
          error: jarvisText(row.error, JARVIS_BLOCK_CAPS.error)
        }
      }),
      pausedCount: Number(block.pausedCount) || 0,
      nextUp: jarvisRows(block.nextUp, JARVIS_BLOCK_CAPS.nextUp, function (row) {
        return { name: jarvisText(row.name, JARVIS_BLOCK_CAPS.name), nextRunAt: jarvisWhen(row.nextRunAt) }
      })
    }
  })
}

// §8 amendment A ruling 1 — the streaks file rides as `one_thing_scoreboard`,
// because `scoreboard` has been the v1 headline reading since 1.0. On the glass
// it is `data.streaks`; `data.scoreboard` keeps its v1 shape untouched.
function jarvisStreaksFrom(raw) {
  return jarvisBlockFace(raw, 'one_thing_scoreboard', function (block) {
    return {
      buildStreak: jarvisNum(block.buildStreak),
      contentStreak: jarvisNum(block.contentStreak),
      bestBuildStreak: jarvisNum(block.bestBuildStreak),
      lessonsShipped: jarvisNum(block.lessonsShipped),
      lastDays: jarvisRows(block.lastDays, JARVIS_BLOCK_CAPS.days, function (row) {
        return {
          date: jarvisText(row.date, 24),
          // a tick that was neither ✅ nor ❌ stays null — never guessed into a day
          build: row.build === true ? true : row.build === false ? false : null,
          content: row.content === true ? true : row.content === false ? false : null,
          note: jarvisText(row.note, JARVIS_BLOCK_CAPS.error)
        }
      }),
      fileUpdatedAt: jarvisWhen(block.fileUpdatedAt),
      staleDays: jarvisNum(block.staleDays)
    }
  })
}

function jarvisSpendFrom(raw) {
  return jarvisBlockFace(raw, 'spend', function (block) {
    const today = block.today && typeof block.today === 'object' ? block.today : {}
    return {
      today: {
        byModel: jarvisRows(today.byModel, JARVIS_BLOCK_CAPS.models, function (row) {
          return {
            model: jarvisText(row.model, JARVIS_BLOCK_CAPS.model),
            calls: Number(row.calls) || 0,
            inputTokens: Number(row.inputTokens) || 0,
            outputTokens: Number(row.outputTokens) || 0,
            cacheReadTokens: Number(row.cacheReadTokens) || 0,
            // a dollar figure Hermes did not report stays null, always
            costUsd: jarvisNum(row.costUsd)
          }
        }),
        totalCalls: Number(today.totalCalls) || 0,
        totalTokens: Number(today.totalTokens) || 0,
        costUsd: jarvisNum(today.costUsd),
        costKnown: today.costKnown === true
      }
    }
  })
}

// ---- voice today (SPEC §8.4 item 1) ----------------------------------------
//
// The one reading on the glass that Jarvis measures ITSELF: how long a call has
// been up in THIS window today, and how many calls that was. Not a backend
// number, not a billing number — the SPEND box labels it "this window" for
// exactly that reason.
//
// The rules, all of them:
//   * the clock only runs while the presence snapshot says `call: 'on'`;
//   * DEMO never counts a second (its call flag is a label machine, §4.6);
//   * a gap longer than JARVIS_VOICE_GAP_MS is not counted at all — the window
//     was closed, or asleep, and time nobody watched is not a measurement;
//   * the day is the configured profile timezone, and a new day starts at zero.

const JARVIS_VOICE_GAP_MS = 5000
const JARVIS_VOICE_KEY = 'hermes-jarvis:voice-today'

/** `YYYY-MM-DD` in the configured profile timezone. Without Intl, or before a
 *  verified setting arrives, UTC is the fail-closed day boundary. */
function jarvisSgtDay(at, timezone) {
  const date = new Date(Number(at) || 0)
  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: String(timezone || 'UTC'), year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(date)
    const bag = {}
    for (let i = 0; i < parts.length; i += 1) bag[parts[i].type] = parts[i].value
    if (bag.year && bag.month && bag.day) return bag.year + '-' + bag.month + '-' + bag.day
  } catch (err) { /* use UTC below */ }
  const pad = function (n) { return (n < 10 ? '0' : '') + n }
  return date.getUTCFullYear() + '-' + pad(date.getUTCMonth() + 1) + '-' + pad(date.getUTCDate())
}

function jarvisVoiceInitial(day) {
  return { ms: 0, seconds: 0, calls: 0, date: String(day || ''), on: false, at: 0 }
}

/**
 * PURE — (state, presence snapshot, now) → state. Returns the SAME object when
 * nothing moved, so the feed can skip a notify.
 */
function jarvisVoiceToday(state, snapshot, now, timezone) {
  const at = Number(now) || 0
  const day = jarvisSgtDay(at, timezone)
  let st = state && typeof state === 'object' ? state : jarvisVoiceInitial(day)
  // Midnight in the configured zone starts today's numbers at zero. Nothing
  // is carried over and nothing is averaged.
  if (st.date !== day) st = jarvisVoiceInitial(day)
  const p = snapshot && typeof snapshot === 'object' ? snapshot : null
  const live = !!p && p.call === 'on' && p.demo !== true
  let ms = st.ms
  let calls = st.calls
  if (live && st.on && st.at) {
    const gap = at - st.at
    if (gap > 0 && gap <= JARVIS_VOICE_GAP_MS) ms += gap
  }
  if (live && !st.on) calls += 1
  const seconds = Math.round(ms / 1000)
  if (st === state && live === st.on && ms === st.ms && calls === st.calls && at === st.at) return state
  return { ms: ms, seconds: seconds, calls: calls, date: day, on: live, at: at }
}

/** What the glass reads: the three fields of the §8.4 contract. */
function jarvisVoiceFace(state) {
  const st = state && typeof state === 'object' ? state : null
  return {
    seconds: st ? Number(st.seconds) || 0 : 0,
    calls: st ? Number(st.calls) || 0 : 0,
    date: st ? String(st.date || '') : ''
  }
}

/** localStorage, in both directions, and never a throw: a window with no
 *  storage (or a wiped one) simply starts today's count at zero. */
function jarvisVoiceLoad(store, now, key, timezone) {
  const day = jarvisSgtDay(now, timezone)
  try {
    const raw = store && typeof store.getItem === 'function' && key ? store.getItem(key) : null
    if (!raw) return jarvisVoiceInitial(day)
    const saved = JSON.parse(String(raw))
    if (!saved || typeof saved !== 'object' || String(saved.date || '') !== day) {
      return jarvisVoiceInitial(day)
    }
    const ms = Math.max(0, Number(saved.ms) || 0)
    return {
      ms: ms, seconds: Math.round(ms / 1000), calls: Math.max(0, Number(saved.calls) || 0),
      date: day, on: false, at: 0
    }
  } catch (err) {
    return jarvisVoiceInitial(day)
  }
}

function jarvisVoiceSave(store, state, key) {
  try {
    if (!store || typeof store.setItem !== 'function' || !state || !key) return false
    store.setItem(key, JSON.stringify({
      ms: Math.round(Number(state.ms) || 0), calls: Number(state.calls) || 0, date: String(state.date || '')
    }))
    return true
  } catch (err) {
    return false
  }
}


function createDataFeed(options) {
  const opts = options || {}
  const ctx = opts.ctx || null
  const SDK = opts.HermesSDK || null
  const host = SDK && SDK.host ? SDK.host : null
  const log = typeof opts.log === 'function' ? opts.log : function () {}
  const now = typeof opts.now === 'function' ? opts.now : function () { return Date.now() }

  const EVENT_CAP = 40
  const BRAIN_RE = /brain|vault/i
  const SENSE_CAP = 12
  const KNOWN_BRAINS = {
    'brain-1': 'Brain 1',
    'brain-2': 'Brain 2',
    'brain-3': 'Brain 3',
    'gbrain': 'G brain'
  }
  const SOCKET_GRACE_MS = 5000

  let running = false
  let socketOff = null
  let socketFrameAt = 0
  const timers = []
  const listeners = new Set()
  let notifyPending = null

  let data = {
    connection: { id: '', profile: '', targetProfile: '', gateway: 'idle', model: '', backend: 'offline', note: '' },
    settings: null,
    brains: [],
    senses: [],
    fleet: [],
    jobs: [],
    lever: null,
    events: [],
    panel: null,
    scoreboard: null,
    logLine: null,
    activity: jarvisActivityInitial(),
    agentState: { rows: [], closedCount: 0, updatedAt: 0, status: 'unreachable', note: 'not polled yet', briefs: null },
    // SPEC §8.4 item 1 — the six v3 blocks, each in its own "nothing yet" state
    // until the first `/state` lands. A box that has never been polled says so.
    agentHelpers: jarvisBlockWaiting(jarvisHelpersFrom(null)),
    nextMeeting: jarvisBlockWaiting(jarvisMeetingFrom(null)),
    todayPlan: jarvisBlockWaiting(jarvisTodayFrom(null)),
    overnightJobs: jarvisBlockWaiting(jarvisJobsFrom(null)),
    streaks: jarvisBlockWaiting(jarvisStreaksFrom(null)),
    spend: jarvisBlockWaiting(jarvisSpendFrom(null)),
    voiceToday: jarvisVoiceFace(jarvisVoiceInitial(jarvisSgtDay(now(), 'UTC'))),
    health: {
      brains: 'unknown', senses: 'unknown', fleet: 'unknown', jobs: 'unknown',
      lever: 'unknown', panel: 'unknown', events: 'unknown', connection: 'unknown'
    },
    updatedAt: 0
  }
  let routeScope = null
  let routeGeneration = 0
  let routeLookup = null
  let settingsSignature = ''
  let settingsGeneration = 0
  let stateRequestGeneration = 0
  let socketToken = ''

  function boxEnabled(id) {
    const settings = data.settings
    if (!settings) return false
    if (Array.isArray(settings.enabled_boxes)) return settings.enabled_boxes.indexOf(id) >= 0
    return id === 'fleet' ? true : ({
      agent_helpers: 'agent_helpers', waiting_on_you: 'agent_state', agent_in_flight: 'agent_state',
      overnight_jobs: 'overnight_jobs', next_meeting: 'next_meeting', today: 'today_plan',
      spend: 'spend', scoreboard: 'one_thing_scoreboard'
    }[id] ? jarvisSourceEnabled(settings, ({
      agent_helpers: 'agent_helpers', waiting_on_you: 'agent_state', agent_in_flight: 'agent_state',
      overnight_jobs: 'overnight_jobs', next_meeting: 'next_meeting', today: 'today_plan',
      spend: 'spend', scoreboard: 'one_thing_scoreboard'
    })[id]) : false)
  }

  function resetPrivate(reason, conn) {
    settingsGeneration += 1
    closeSocket()
    mirrorNotes = {}
    liveSessions = { count: null, busy: false }
    sessionJobs = []
    cronJobs = []
    settingsSignature = ''
    const note = String(reason || 'connect to this chief profile dashboard')
    data = Object.assign({}, data, {
      connection: Object.assign({}, conn || data.connection, { backend: 'blocked', note: note }),
      settings: null,
      brains: [], senses: [], fleet: [], jobs: [], lever: null, events: [], panel: null,
      scoreboard: null, logLine: null, activity: jarvisActivityInitial(),
      agentState: { rows: [], closedCount: 0, updatedAt: 0, status: 'unreachable', note: note, briefs: null },
      agentHelpers: jarvisBlockWaiting(jarvisHelpersFrom(null)),
      nextMeeting: jarvisBlockWaiting(jarvisMeetingFrom(null)),
      todayPlan: jarvisBlockWaiting(jarvisTodayFrom(null)),
      overnightJobs: jarvisBlockWaiting(jarvisJobsFrom(null)),
      streaks: jarvisBlockWaiting(jarvisStreaksFrom(null)),
      spend: jarvisBlockWaiting(jarvisSpendFrom(null)),
      health: {
        brains: 'unknown', senses: 'unknown', fleet: 'unknown', jobs: 'unknown',
        lever: 'unknown', panel: 'unknown', events: 'unknown', connection: 'unknown'
      },
      updatedAt: now()
    })
    notifyNow()
  }

  function ensureRouteScope() {
    const selected = jarvisSelectedOwner(host)
    if (!selected) {
      resetPrivate('selected profile identity is unavailable')
      return Promise.resolve(null)
    }
    const connectionId = selected.connectionId
    const routeProfile = selected.routeProfile
    if (routeScope && routeScope.connectionId === connectionId && routeScope.routeProfile === routeProfile) {
      return Promise.resolve(routeScope)
    }
    if (routeLookup) return routeLookup
    const generation = routeGeneration
    routeLookup = jarvisTargetProfile(host, connectionId, routeProfile).then(function (targetProfile) {
      routeLookup = null
      if (generation !== routeGeneration) return null
      const scope = jarvisScope(connectionId, routeProfile, targetProfile)
      routeScope = scope
      if (!scope) resetPrivate('selected profile identity is unavailable')
      else patch({ connection: Object.assign({}, data.connection, { targetProfile: scope.profileId }) })
      return scope
    })
    return routeLookup
  }

  // ---- doors ---------------------------------------------------------------

  function rpc(method, params) {
    if (!host || (typeof host.request !== 'function' && typeof host.requestProfile !== 'function')) {
      return Promise.reject(new Error('gateway unavailable'))
    }
    try {
      if (routeScope && typeof host.requestProfile === 'function') {
        const route = routeScope.connectionId === null ? routeScope.profileId : {
          connectionId: routeScope.connectionId,
          profile: routeScope.routeProfile,
          targetProfile: routeScope.profileId
        }
        return Promise.resolve(host.requestProfile(route, method, params || {}))
      }
      return Promise.resolve(host.request(method, params || {}))
    } catch (err) {
      return Promise.reject(err)
    }
  }

  function rest(path, restOpts) {
    if (!ctx || typeof ctx.rest !== 'function') {
      return Promise.reject(new Error('plugin backend door unavailable'))
    }
    try {
      const nextOpts = Object.assign({}, restOpts || {})
      if (routeScope) nextOpts.scope = { connectionId: routeScope.connectionId, profile: routeScope.routeProfile }
      return Promise.resolve(ctx.rest(path, nextOpts))
    } catch (err) {
      return Promise.reject(err)
    }
  }

  function atom(name) {
    const a = host && host.state ? host.state[name] : null
    if (!a || typeof a.get !== 'function') return null
    try {
      return a.get()
    } catch (err) {
      return null
    }
  }

  function activeProfile() {
    const selected = jarvisSelectedOwner(host)
    return selected ? selected.routeProfile : 'default'
  }

  function patch(next) {
    data = Object.assign({}, data, next, { updatedAt: now() })
    notify()
  }

  function mark(slice, status) {
    const health = Object.assign({}, data.health)
    health[slice] = status
    data = Object.assign({}, data, { health: health, updatedAt: now() })
  }

  let lastFlushAt = 0

  function flush() {
    notifyPending = null
    lastFlushAt = now()
    const snapshot = data
    listeners.forEach(function (fn) {
      try {
        fn(snapshot)
      } catch (err) {
        log('data listener failed: ' + (err && err.message ? err.message : err))
      }
    })
  }

  function notify() {
    if (notifyPending) return
    notifyPending = setTimeout(flush, 100) // ≤10 Hz — the pods are text, they do not need frames
  }

  // §7.3 — a tool starting or finishing, a turn opening or closing and anything
  // that needs Owner land on the screen at once; nobody waits 100 ms to learn
  // that Agent is asking for a yes.
  function notifyNow() {
    if (notifyPending) { clearTimeout(notifyPending); notifyPending = null }
    flush()
  }

  // …and the delta storm (thinking / speaking text) is held to ~4 frames a
  // second, whatever the model's token rate.
  function notifySoon(minGapMs) {
    if (notifyPending) return
    const wait = Math.max(0, minGapMs - (now() - lastFlushAt))
    notifyPending = setTimeout(flush, wait)
  }

  function titleCase(id) {
    return String(id || '')
      .replace(/[-_.]+/g, ' ')
      .replace(/\b\w/g, function (c) { return c.toUpperCase() })
      .trim()
  }

  // ---- connection ----------------------------------------------------------

  function readConnection() {
    try {
      const selected = jarvisSelectedOwner(host)
      if (!selected) {
        routeGeneration += 1
        routeScope = null
        routeLookup = null
        resetPrivate('selected profile identity is unavailable')
        return
      }
      const id = selected.connectionId
      const profile = selected.routeProfile
      const conn = {
        id: id,
        profile: profile,
        targetProfile: routeScope && routeScope.connectionId === id && routeScope.routeProfile === profile
          ? routeScope.profileId : '',
        gateway: String(atom('gateway') || 'idle'),
        model: String(atom('model') || ''),
        backend: data.connection.backend,
        note: data.connection.note || ''
      }
      if (id !== data.connection.id || profile !== data.connection.profile) {
        routeGeneration += 1
        routeScope = null
        routeLookup = null
        resetPrivate('waiting for the selected chief profile dashboard', conn)
        ensureRouteScope()
      }
      mark('connection', host ? 'ok' : 'unreachable')
      patch({ connection: conn })
    } catch (err) {
      mark('connection', 'unreachable')
      notify()
    }
  }

  // ---- brains + senses (MCP servers on the active profile) -----------------

  function applyMcpNames(rows) {
    const brains = []
    const senses = []
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i] || {}
      const id = String(row.name || row.id || '').trim()
      if (!id) continue
      const enabled = row.enabled !== false
      const entry = {
        id: id,
        label: KNOWN_BRAINS[id.toLowerCase()] || titleCase(id),
        status: enabled ? 'ok' : 'unknown',
        note: enabled ? 'configured' : 'disabled'
      }
      if (BRAIN_RE.test(id)) brains.push(entry)
      else if (senses.length < SENSE_CAP) senses.push(entry)
    }
    return { brains: brains, senses: senses }
  }

  function pollMcp() {
    if (!data.settings || !jarvisSourceEnabled(data.settings, 'brains')) {
      if (data.brains.length || data.senses.length) patch({ brains: [], senses: [] })
      return Promise.resolve(false)
    }
    const profile = activeProfile()
    const stamp = producerStamp()
    // `profiles.describe` carries the profile's CONFIGURED servers
    // ([{name, enabled, transport}]); `mcp.catalog` is the installable catalog
    // ({servers:[{name, installed, …}]}). Defend against both shapes and both
    // gateway ages — either alone is enough to paint the pods.
    return Promise.all([
      rpc('profiles.describe', { name: profile }).catch(function () { return null }),
      rpc('mcp.catalog', { profile: profile }).catch(function () { return null })
    ]).then(function (pair) {
      if (!producerCurrent(stamp) || !jarvisSourceEnabled(data.settings, 'brains')) return false
      const described = pair[0]
      const catalog = pair[1]
      let rows = []
      if (described && Array.isArray(described.mcp_servers)) {
        rows = described.mcp_servers
      } else if (catalog && Array.isArray(catalog.servers)) {
        rows = catalog.servers.filter(function (s) { return s && s.installed })
          .map(function (s) { return { name: s.name, enabled: true } })
      }
      if (!described && !catalog) {
        mark('brains', 'unreachable')
        mark('senses', 'unreachable')
        notify()
        return
      }
      const split = applyMcpNames(rows)
      mark('brains', 'ok')
      mark('senses', 'ok')
      patch({ brains: mergeBrainNotes(split.brains), senses: split.senses })
    }).catch(function (err) {
      if (!producerCurrent(stamp)) return false
      mark('brains', 'unreachable')
      mark('senses', 'unreachable')
      notify()
      log('mcp poll failed: ' + (err && err.message ? err.message : err))
    })
  }

  // Backend `/state` knows how fresh each brain's mirror is; merge that
  // note onto the MCP rows without inventing a brain the profile does not have.
  let mirrorNotes = {}

  function mergeBrainNotes(brains) {
    return brains.map(function (b) {
      const note = mirrorNotes[b.id]
      return note ? Object.assign({}, b, { note: b.note + ' · ' + note }) : b
    })
  }

  function producerStamp() {
    return {
      route: routeGeneration,
      settings: settingsGeneration,
      scope: routeScope ? routeScope.id : ''
    }
  }

  function producerCurrent(stamp) {
    return !!stamp && stamp.route === routeGeneration && stamp.settings === settingsGeneration &&
      !!routeScope && stamp.scope === routeScope.id && !!data.settings && data.settings.profile_id === routeScope.profileId
  }

  // ---- fleet + jobs --------------------------------------------------------

  // Live session facts for the profile this gateway is routed to. Held apart
  // from `data` so the 30 s fleet poll and the 5 s session poll can land in any
  // order without one blanking the other's reading.
  let liveSessions = { count: null, busy: false }
  let sessionJobs = []

  function fleetRow(p, mine) {
    const name = String(p.name || '').trim()
    return {
      id: name,
      label: String(p.display_name || '').trim() || titleCase(name),
      busy: name === mine ? liveSessions.busy : false,
      // Live counts exist only for the profile this gateway is routed to;
      // for every other profile we say nothing rather than guess.
      sessions: name === mine ? liveSessions.count : null
    }
  }

  function pollFleet() {
    if (!boxEnabled('fleet')) {
      if (data.fleet.length) patch({ fleet: [] })
      return Promise.resolve(false)
    }
    const stamp = producerStamp()
    return rpc('profiles.list', { include_sessions: false }).then(function (res) {
      if (!producerCurrent(stamp) || !boxEnabled('fleet')) return false
      const rows = res && Array.isArray(res.profiles) ? res.profiles : []
      const mine = activeProfile()
      const fleet = rows.map(function (p) { return fleetRow(p, mine) })
      mark('fleet', 'ok')
      patch({ fleet: fleet })
    }).catch(function (err) {
      if (!producerCurrent(stamp)) return false
      mark('fleet', 'unreachable')
      notify()
      log('fleet poll failed: ' + (err && err.message ? err.message : err))
    })
  }

  function jobLabel(row) {
    const text = String(row.title || row.preview || row.session_key || row.id || '').trim()
    return text ? text.slice(0, 64) : 'session'
  }

  function pollSessions() {
    if (!boxEnabled('fleet')) {
      liveSessions = { count: null, busy: false }
      sessionJobs = []
      if (data.jobs.length || data.fleet.length) patch({ jobs: [], fleet: [] })
      return Promise.resolve(false)
    }
    const stamp = producerStamp()
    return rpc('session.active_list', {}).then(function (res) {
      if (!producerCurrent(stamp) || !boxEnabled('fleet')) return false
      const rows = res && Array.isArray(res.sessions) ? res.sessions : []
      const jobs = []
      let busy = 0
      for (let i = 0; i < rows.length; i += 1) {
        const row = rows[i] || {}
        const status = String(row.status || '')
        if (status === 'working') busy += 1
        if (status !== 'working' && status !== 'waiting' && status !== 'starting') continue
        jobs.push({
          id: String(row.id || row.session_key || ('session-' + i)),
          label: jobLabel(row),
          status: status === 'working' ? 'running' : status === 'starting' ? 'queued' : 'waiting',
          since: Math.round((Number(row.started_at) || 0) * 1000) || null
        })
      }
      const mine = activeProfile()
      liveSessions = { count: rows.length, busy: busy > 0 }
      sessionJobs = jobs
      const fleet = data.fleet.map(function (f) {
        return f.id === mine ? Object.assign({}, f, { busy: liveSessions.busy, sessions: liveSessions.count }) : f
      })
      mark('jobs', 'ok')
      patch({ jobs: sessionJobs.concat(cronJobs), fleet: fleet })
    }).catch(function (err) {
      if (!producerCurrent(stamp)) return false
      mark('jobs', 'unreachable')
      notify()
      log('session poll failed: ' + (err && err.message ? err.message : err))
    })
  }

  // Cron rows are SCHEDULES, not work. Only a row the gateway reports as
  // actually running earns a JOBS line — a schedule on a shelf is not a job.
  let cronJobs = []

  function pollCron() {
    if (!boxEnabled('fleet')) {
      cronJobs = []
      if (data.jobs.length) patch({ jobs: [] })
      return Promise.resolve(false)
    }
    const stamp = producerStamp()
    return rpc('cron.manage', { action: 'list', include_disabled: false }).then(function (res) {
      if (!producerCurrent(stamp) || !boxEnabled('fleet')) return false
      const rows = res && Array.isArray(res.jobs) ? res.jobs : []
      cronJobs = rows.filter(function (j) {
        return j && (j.running === true || String(j.state || '') === 'running')
      }).slice(0, 6).map(function (j) {
        return {
          id: String(j.job_id || j.name || 'cron'),
          label: String(j.name || j.job_id || 'cron job').slice(0, 64),
          status: 'running',
          since: Number(j.started_at) ? Math.round(Number(j.started_at) * 1000) : null
        }
      })
      patch({ jobs: sessionJobs.concat(cronJobs) })
    }).catch(function () {
      if (!producerCurrent(stamp)) return false
      cronJobs = [] // no cron read = no cron claims
      patch({ jobs: sessionJobs.concat(cronJobs) })
    })
  }

  // ---- backend /state (the ONE lever + mirrors + scoreboard + log) ---------

  function pollState() {
    const generation = routeGeneration
    const requestGeneration = ++stateRequestGeneration
    return ensureRouteScope().then(function (scope) {
      if (!scope || generation !== routeGeneration) throw new Error('selected profile changed')
      return rest('/state').then(function (res) { return { scope: scope, res: res } })
    }).then(function (answer) {
      const scope = answer.scope
      const res = answer.res
      if (generation !== routeGeneration || requestGeneration !== stateRequestGeneration || !routeScope || routeScope.id !== scope.id) return false
      if (!res || typeof res !== 'object') throw new Error('empty /state')
      const checked = jarvisValidateSettings(res.settings, scope.profileId)
      if (!checked.ok) {
        resetPrivate(checked.reason, Object.assign({}, data.connection, { targetProfile: scope.profileId }))
        return false
      }
      const settings = checked.settings
      const nextSignature = jarvisSettingsSignature(settings)
      const settingsChanged = settingsSignature !== nextSignature
      if (settingsSignature && settingsSignature !== nextSignature) {
        resetPrivate('dashboard selection changed', Object.assign({}, data.connection, { targetProfile: scope.profileId }))
      }
      if (settingsChanged) settingsGeneration += 1
      settingsSignature = nextSignature
      const next = {}
      next.settings = settings
      const nextVoiceKey = jarvisScopedKey(scope, JARVIS_VOICE_KEY.replace('hermes-jarvis:', ''))
      if (voiceKey !== nextVoiceKey || voiceTimezone !== settings.timezone) {
        voiceKey = nextVoiceKey
        voiceTimezone = settings.timezone
        voiceState = jarvisVoiceLoad(voiceStore, now(), voiceKey, voiceTimezone)
        next.voiceToday = jarvisVoiceFace(voiceState)
      }
      next.lever = jarvisSourceEnabled(settings, 'lever') && res.lever && res.lever.text
        ? { text: String(res.lever.text), source: String(res.lever.source || ''), updatedAt: Number(res.lever.updatedAt) || now() }
        : null
      next.scoreboard = jarvisSourceEnabled(settings, 'scoreboard') && res.scoreboard && res.scoreboard.headline
        ? { headline: String(res.scoreboard.headline), source: String(res.scoreboard.source || '') }
        : null
      next.logLine = jarvisSourceEnabled(settings, 'log') && res.log && res.log.text
        ? { text: String(res.log.text), source: String(res.log.source || '') }
        : null
      mirrorNotes = {}
      const rows = jarvisSourceEnabled(settings, 'brains') && Array.isArray(res.brains) ? res.brains : []
      for (let i = 0; i < rows.length; i += 1) {
        const row = rows[i] || {}
        const id = String(row.id || '').toLowerCase()
        if (id && row.mirror_updated) mirrorNotes[id] = 'mirror ' + String(row.mirror_updated)
      }
      next.brains = jarvisSourceEnabled(settings, 'brains')
        ? settings.brains.map(function (brain) {
          return { id: brain.id, label: brain.label, status: 'unknown', note: mirrorNotes[brain.id] || 'configured' }
        }) : []
      next.senses = jarvisSourceEnabled(settings, 'brains') ? data.senses : []
      next.agentState = jarvisSourceEnabled(settings, 'agent_state')
        ? agentStateFrom(res)
        : { rows: [], closedCount: 0, updatedAt: 0, status: 'disabled', note: 'disabled for this profile', briefs: null }
      // SPEC §8.4 item 1 — the six v3 blocks ride the SAME 60 s answer as the
      // lever: no extra request, no second poll of the mini.
      next.agentHelpers = jarvisSourceEnabled(settings, 'agent_helpers')
        ? jarvisHelpersFrom(res.agent_helpers) : jarvisBlockDisabled(jarvisHelpersFrom(null))
      next.nextMeeting = jarvisSourceEnabled(settings, 'next_meeting')
        ? jarvisMeetingFrom(res.next_meeting) : jarvisBlockDisabled(jarvisMeetingFrom(null))
      next.todayPlan = jarvisSourceEnabled(settings, 'today_plan')
        ? jarvisTodayFrom(res.today_plan) : jarvisBlockDisabled(jarvisTodayFrom(null))
      next.overnightJobs = jarvisSourceEnabled(settings, 'overnight_jobs')
        ? jarvisJobsFrom(res.overnight_jobs) : jarvisBlockDisabled(jarvisJobsFrom(null))
      next.streaks = jarvisSourceEnabled(settings, 'one_thing_scoreboard')
        ? jarvisStreaksFrom(res.one_thing_scoreboard) : jarvisBlockDisabled(jarvisStreaksFrom(null))
      next.spend = jarvisSourceEnabled(settings, 'spend')
        ? jarvisSpendFrom(res.spend) : jarvisBlockDisabled(jarvisSpendFrom(null))
      next.connection = Object.assign({}, data.connection, { backend: 'ok', note: '', targetProfile: scope.profileId })
      mark('lever', 'ok')
      patch(next)
      rebindSocket()
      pollMcp()
      if (boxEnabled('fleet')) { pollFleet(); pollSessions(); pollCron() }
      return true
    }).catch(function (err) {
      if (generation !== routeGeneration || requestGeneration !== stateRequestGeneration) return false
      mark('lever', 'unreachable')
      patch({
        connection: Object.assign({}, data.connection, { backend: 'offline', note: 'dashboard backend unreachable' }),
        agentState: agentStateStale('backend unreachable'),
        // the numbers Owner last saw stay on the glass, with the reason and
        // their own stamp, rather than six boxes blanking at once
        agentHelpers: jarvisBlockStale(data.agentHelpers, 'backend unreachable'),
        nextMeeting: jarvisBlockStale(data.nextMeeting, 'backend unreachable'),
        todayPlan: jarvisBlockStale(data.todayPlan, 'backend unreachable'),
        overnightJobs: jarvisBlockStale(data.overnightJobs, 'backend unreachable'),
        streaks: jarvisBlockStale(data.streaks, 'backend unreachable'),
        spend: jarvisBlockStale(data.spend, 'backend unreachable')
      })
      log('state poll failed: ' + (err && err.message ? err.message : err))
      return false
    })
  }

  // §7.5 — Agent's STATE rows ride the SAME /state answer as the lever: no extra
  // request, no poll of the mini. A failed poll keeps the last good rows WITH
  // their own stamp, so the boxes can print an age instead of pretending.

  function agentStateStale(note) {
    const last = data.agentState || { rows: [], closedCount: 0, updatedAt: 0, briefs: null }
    return {
      rows: last.rows,
      closedCount: last.closedCount,
      updatedAt: last.updatedAt,
      briefs: last.briefs || null,
      status: 'unreachable',
      note: note
    }
  }

  function agentStateFrom(res) {
    const raw = res && res.agent_state
    if (!raw || typeof raw !== 'object') return agentStateStale('backend has no agent_state yet')
    const rows = jarvisAgentRows(raw.rows)
    const note = raw.note ? String(raw.note) : null
    // The backend reports a missing or unreadable STATE.md as `rows: []` plus a
    // note (§7.5). That is not "nothing is waiting on you": §7.4 wants the boxes
    // to say unreachable, so an empty answer carrying a note is unreachable.
    if (!rows.length && note) return agentStateStale(note)
    return {
      rows: rows,
      closedCount: Number(raw.closed_count) || 0,
      updatedAt: Number(raw.updatedAt) || now(),
      // §8.3.1 — how many briefs Agent has written, and how many found a row.
      // A backend too old to have the file at all simply sends nothing.
      briefs: raw.briefs && typeof raw.briefs === 'object' ? {
        status: jarvisText(raw.briefs.status, JARVIS_BLOCK_CAPS.status) || 'ok',
        count: Number(raw.briefs.count) || 0,
        matched: Number(raw.briefs.matched) || 0,
        note: raw.briefs.note ? jarvisText(raw.briefs.note, JARVIS_BLOCK_CAPS.note) : null,
        updatedAt: jarvisWhen(raw.briefs.updatedAt),
        source: jarvisText(raw.briefs.source, JARVIS_BLOCK_CAPS.source)
      } : null,
      status: 'ok',
      note: note
    }
  }

  // ---- backend /panel (Agent-summoned card) ---------------------------------

  function applyPanel(raw) {
    if (!raw || !raw.title) {
      if (data.panel) patch({ panel: null })
      return
    }
    const panel = {
      id: String(raw.id || raw.title),
      title: String(raw.title),
      body: String(raw.body || ''),
      kind: String(raw.kind || 'card'),
      ttl: Number(raw.ttl_s || raw.ttl) || 20,
      at: Number(raw.at) ? (Number(raw.at) < 1e12 ? Number(raw.at) * 1000 : Number(raw.at)) : now()
    }
    if (data.panel && data.panel.id === panel.id && data.panel.at === panel.at) return
    patch({ panel: panel })
  }

  function expirePanel() {
    const panel = data.panel
    if (!panel) return
    if (now() - panel.at > panel.ttl * 1000) patch({ panel: null })
  }

  function pollPanel() {
    expirePanel()
    if (!data.settings || !routeScope || data.settings.profile_id !== routeScope.profileId) {
      if (data.panel) patch({ panel: null })
      return Promise.resolve(false)
    }
    if (socketFrameAt && now() - socketFrameAt < SOCKET_GRACE_MS * 3) return Promise.resolve()
    const generation = routeGeneration
    const scopeId = routeScope.id
    return rest('/panel').then(function (res) {
      if (generation !== routeGeneration || !routeScope || routeScope.id !== scopeId || !data.settings) return false
      mark('panel', 'ok')
      applyPanel(res && res.panel ? res.panel : res)
      return true
    }).catch(function () {
      mark('panel', 'unreachable')
      notify()
    })
  }

  function closeSocket() {
    if (typeof socketOff === 'function') {
      try { socketOff() } catch (err) { /* already gone */ }
    }
    socketOff = null
    socketToken = ''
    socketFrameAt = 0
  }

  function activeGatewayMatchesSelected() {
    const selected = jarvisSelectedOwner(host)
    const connectionAtom = host && host.state ? host.state.connectionId : null
    if (!selected || !connectionAtom || typeof connectionAtom.get !== 'function') return false
    let activeConnection
    try { activeConnection = connectionAtom.get() } catch (err) { return false }
    const admitted = jarvisConnectionId(activeConnection)
    const activeRoute = jarvisCleanId(atom('profile')) || 'default'
    return admitted.ok && admitted.value === selected.connectionId && activeRoute === selected.routeProfile
  }

  function rebindSocket() {
    const stamp = producerStamp()
    const token = stamp.route + ':' + stamp.settings + ':' + stamp.scope
    if (socketOff && socketToken === token) return
    closeSocket()
    if (!running || !ctx || typeof ctx.socket !== 'function' || !producerCurrent(stamp) || !activeGatewayMatchesSelected()) return
    socketToken = token
    try {
      socketOff = ctx.socket('/events', function (frame) {
        if (socketToken !== token || !producerCurrent(stamp)) return
        socketFrameAt = now()
        if (!frame || typeof frame !== 'object') return
        if (frame.type === 'panel' && data.settings && routeScope && data.settings.profile_id === routeScope.profileId) applyPanel(frame.data)
        else if (frame.type === 'state') pollState()
      })
    } catch (err) {
      closeSocket()
      log('events socket unavailable, polling instead')
    }
    // No frame inside the grace window = the socket never landed; polling
    // (already running) stays the source of truth. Nothing to undo.
  }

  // ---- gateway event ticker ------------------------------------------------

  function eventText(ev) {
    if (!ev || typeof ev !== 'object') return ''
    const keys = ['message', 'text', 'title', 'name', 'status', 'session_id', 'profile', 'model']
    for (let i = 0; i < keys.length; i += 1) {
      const v = ev[keys[i]]
      if (typeof v === 'string' && v.trim()) return v.trim().replace(/\s+/g, ' ').slice(0, 120)
    }
    return ''
  }

  function pushEvent(ev) {
    const type = String((ev && ev.type) || 'event')
    const events = data.events.concat([{ at: now(), type: type, text: eventText(ev) }]).slice(-EVENT_CAP)
    const health = Object.assign({}, data.health, { events: 'ok' })
    data = Object.assign({}, data, { events: events, health: health, updatedAt: now() })
    if (!reduceActivity(ev)) notify()
  }

  // ---- activity (SPEC §7.3) ------------------------------------------------
  //
  // The same `ctx.onEvent('*')` tap that feeds the ticker feeds the NOW box,
  // through the pure reducer above. Host facts come from the SDK atoms; a host
  // too old to have them reads as empty and the box simply says less.

  // Instantly on the beats Owner is waiting for; the delta storm is throttled.
  const ACTIVITY_INSTANT = {
    'tool.start': 1, 'tool.complete': 1, 'message.start': 1, 'message.complete': 1,
    error: 1, 'voice.interrupted': 1, 'session.reclaimed': 1,
    'subagent.start': 1, 'subagent.spawn_requested': 1, 'subagent.complete': 1,
    'connection.request': 1, 'connection.update': 1, 'request.cancel': 1,
    approval: 1, 'approval.pending': 1, 'approval.request': 1, 'approval.required': 1,
    'approval.received': 1, 'approval.respond': 1, 'approval.resolved': 1,
    clarify: 1, 'clarify.request': 1, 'clarify.lock': 1, 'clarify.response': 1
  }
  const ACTIVITY_DELTA_GAP_MS = 250 // ≤ ~4 notifies a second from deltas

  function hostFacts() {
    const busyBySession = atom('busyBySession')
    return {
      focusedSessionId: String(atom('focusedSessionId') || ''),
      busy: atom('busy') === true,
      busyBySession: busyBySession && typeof busyBySession === 'object' ? busyBySession : {}
    }
  }

  function needsKey(needs) {
    return needs ? String(needs.kind) + ' · ' + String(needs.text) : ''
  }

  /** Fold one event (or null, for a host-facts refresh) in. True = notified. */
  function reduceActivity(ev) {
    const before = data.activity
    let after = before
    try {
      after = jarvisReduceActivity(before, ev, hostFacts(), now())
    } catch (err) {
      log('activity reduce failed: ' + (err && err.message ? err.message : err))
      return false
    }
    if (after === before) return false
    data = Object.assign({}, data, { activity: after, updatedAt: now() })
    const type = ev && ev.type ? String(ev.type) : ''
    const toolChanged = before.tool && after.tool
      ? before.tool.startedAt !== after.tool.startedAt
      : before.tool !== after.tool
    const instant = ACTIVITY_INSTANT[type] === 1 ||
      before.running !== after.running ||
      before.session !== after.session ||
      needsKey(before.needsYou) !== needsKey(after.needsYou) ||
      toolChanged
    if (instant) notifyNow()
    else notifySoon(ACTIVITY_DELTA_GAP_MS)
    return true
  }

  function refreshActivity() {
    reduceActivity(null)
  }

  // ---- presence push (the overlay's door to the mirror) --------------------

  let pushBlockedUntil = 0
  let lastPushAt = 0

  // ---- voice today (SPEC §8.4 item 1) --------------------------------------
  // Every presence frame the overlay pushes passes through here first, so the
  // call clock is measured on the SAME frames the glass is painted from. It is
  // measured whether or not the backend is up: this reading is Jarvis's own.

  const voiceStore = (function () {
    try {
      return typeof window !== 'undefined' && window && window.localStorage ? window.localStorage : null
    } catch (err) {
      return null    // a window that refuses storage still gets a live count
    }
  })()
  let voiceKey = null
  let voiceTimezone = 'UTC'
  let voiceState = jarvisVoiceInitial(jarvisSgtDay(now(), voiceTimezone))
  let voiceSavedAt = 0
  const VOICE_SAVE_MS = 5000

  function trackVoice(snapshot) {
    let next = voiceState
    try {
      next = jarvisVoiceToday(voiceState, snapshot, now(), voiceTimezone)
    } catch (err) {
      return   // a clock that will not read is never a reason to lose a frame
    }
    if (next === voiceState) return
    const before = voiceState
    voiceState = next
    const face = jarvisVoiceFace(next)
    const shown = data.voiceToday || {}
    if (face.seconds !== shown.seconds || face.calls !== shown.calls || face.date !== shown.date) {
      data = Object.assign({}, data, { voiceToday: face, updatedAt: now() })
      notify()
    }
    // written on every call edge (so a crash cannot lose a whole call) and at
    // most every five seconds while one is running
    if (next.calls !== before.calls || next.on !== before.on || now() - voiceSavedAt >= VOICE_SAVE_MS) {
      voiceSavedAt = now()
      jarvisVoiceSave(voiceStore, next, voiceKey)
    }
  }

  function pushPresence(body) {
    if (!data.settings || !routeScope || data.settings.profile_id !== routeScope.profileId) return Promise.resolve(false)
    trackVoice(body)
    const at = now()
    if (at - lastPushAt < 100 || at < pushBlockedUntil) return Promise.resolve(false)
    lastPushAt = at
    return rest('/presence', { method: 'POST', body: body }).then(function () {
      return true
    }).catch(function () {
      pushBlockedUntil = now() + 30000 // backend offline — stop knocking for 30 s
      return false
    })
  }

  // ---- lifecycle -----------------------------------------------------------

  function every(ms, fn) {
    try {
      fn()
    } catch (err) {
      log('poll failed: ' + (err && err.message ? err.message : err))
    }
    timers.push(setInterval(function () {
      try {
        fn()
      } catch (err) {
        log('poll failed: ' + (err && err.message ? err.message : err))
      }
    }, ms))
  }

  function start() {
    if (running) return
    running = true

    if (ctx && typeof ctx.onEvent === 'function') {
      try {
        ctx.onEvent('*', pushEvent)
      } catch (err) {
        mark('events', 'unreachable')
      }
    }

    const stateAtoms = ['profile', 'gateway', 'model', 'connectionId', 'focusedSessionOwner', 'focusedSessionProfile']
    for (let i = 0; i < stateAtoms.length; i += 1) {
      const a = host && host.state ? host.state[stateAtoms[i]] : null
      if (a && typeof a.listen === 'function') {
        try {
          timers.push({ unlisten: a.listen(function () { readConnection() }) })
        } catch (err) { /* older SDK — the 5 s poll still refreshes it */ }
      }
    }

    // §7.3 — focus and busy move the NOW box without an event of their own
    // (a tile switch, or the host going busy before the first frame lands).
    const activityAtoms = ['focusedSessionId', 'busy', 'busyBySession']
    for (let i = 0; i < activityAtoms.length; i += 1) {
      const a = host && host.state ? host.state[activityAtoms[i]] : null
      if (a && typeof a.listen === 'function') {
        try {
          timers.push({ unlisten: a.listen(function () { refreshActivity() }) })
        } catch (err) { /* older SDK — the 5 s tick still refreshes it */ }
      }
    }

    every(5000, refreshActivity)
    every(5000, readConnection)
    every(5000, pollSessions)
    every(30000, pollFleet)
    every(60000, pollMcp)
    every(60000, pollCron)
    every(60000, pollState)
    every(2000, pollPanel)
  }

  function stop() {
    running = false
    for (let i = 0; i < timers.length; i += 1) {
      const t = timers[i]
      if (t && typeof t.unlisten === 'function') {
        try { t.unlisten() } catch (err) { /* already gone */ }
      } else {
        clearInterval(t)
      }
    }
    timers.length = 0
    if (notifyPending) { clearTimeout(notifyPending); notifyPending = null }
    closeSocket()
    listeners.clear()
  }

  return {
    get: function () { return data },
    subscribe: function (fn) {
      if (typeof fn !== 'function') return function () {}
      listeners.add(fn)
      return function () { listeners.delete(fn) }
    },
    start: start,
    stop: stop,
    /** Re-run one slice on demand: 'state' (lever + Agent's STATE), 'panel',
     *  'sessions', 'activity' (host facts only) or 'all'. */
    refresh: function (which) {
      const what = String(which || 'all')
      if (what === 'activity') return refreshActivity()
      if (what === 'state') return pollState()
      if (what === 'panel') return pollPanel()
      if (what === 'sessions') return pollSessions()
      refreshActivity()
      return Promise.all([pollState(), pollSessions(), pollPanel()])
    },
    pushPresence: pushPresence,
    showPanel: function (panel) { applyPanel(panel) }
  }
}
