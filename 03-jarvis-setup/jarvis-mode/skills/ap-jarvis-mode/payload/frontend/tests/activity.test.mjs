/* tests/activity.test.mjs — node --test tests/activity.test.mjs
 *
 * WP-D: the NOW box feed (SPEC §7.3) and Agent's STATE rows (§7.5).
 *
 * 30-data.js is a plain concatenated file (no import/export), so it loads the
 * same way tests/scene.test.mjs loads the scene: read the bytes, wrap them in a
 * Function, hand back the names the tests need. `jarvisReduceActivity` is pure,
 * so a whole turn can be replayed against a fake clock with no host at all.
 *
 * Event shapes follow the host contract in
 * ~/.hermes/hermes-agent/apps/shared/src/gateway-contract.generated.ts
 * (envelope {type, session_id, payload}; ToolStartPayload {tool_id,name,args},
 * ToolCompletePayload {name,duration_s,error?}, StreamDeltaPayload {text},
 * MessageCompletePayload {status}, SubagentEventPayload {goal,subagent_id,…}).
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const SRC = fileURLToPath(new URL('../src/30-data.js', import.meta.url))
const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))

function load() {
  const src = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n' + fs.readFileSync(SRC, 'utf8')
  const factory = new Function(
    'window', 'document',
    src + '\n;return { createDataFeed, jarvisReduceActivity, jarvisActivityInitial, jarvisActivityLabel, jarvisActivityDetail, jarvisAgentRows, jarvisAgentBrief, jarvisHelpersFrom, jarvisMeetingFrom, jarvisTodayFrom, jarvisJobsFrom, jarvisStreaksFrom, jarvisSpendFrom, jarvisVoiceToday, jarvisVoiceFace, jarvisVoiceInitial, jarvisVoiceLoad, jarvisVoiceSave, jarvisSgtDay };'
  )
  return factory(undefined, undefined)
}
const M = load()

/* ------------------------------------------------------------------ tools -- */

const S1 = 'runtime-session-1'
const S2 = 'runtime-session-2'

/** A replay harness: one clock, one state, host facts you can move. */
function turn(facts = { focusedSessionId: S1, busy: false, busyBySession: {} }) {
  let clock = 1_700_000_000_000
  let state = M.jarvisActivityInitial()
  return {
    get state() { return state },
    get at() { return clock },
    facts,
    tick(ms) { clock += ms; return clock },
    /** Feed one gateway event (optionally after advancing the clock). */
    feed(type, payload, opts = {}) {
      if (opts.after) clock += opts.after
      const event = { type, session_id: opts.session ?? S1, payload, profile: 'agent', seq: 1 }
      state = M.jarvisReduceActivity(state, event, opts.facts ?? facts, clock)
      return state
    },
    /** Fold host facts in with no event (the 5 s tick / an atom moving). */
    host(nextFacts, ms = 0) {
      clock += ms
      state = M.jarvisReduceActivity(state, null, nextFacts ?? facts, clock)
      return state
    }
  }
}

const toolStart = (name, args) => ({ tool_id: `t-${name}-${Math.random()}`, name, args })

/* ------------------------------------------------------- a realistic turn -- */

test('a whole turn: start, three tools, thinking, a subagent, an approval, deltas, complete', () => {
  const t = turn()

  // 1 — the turn opens
  let s = t.feed('message.start', {})
  assert.equal(s.session, S1)
  assert.equal(s.focused, true)
  assert.equal(s.running, true)
  assert.equal(s.source, 'events')
  assert.equal(s.modelCalls, 1)
  assert.equal(s.steps, 0)
  assert.equal(s.startedAt, t.at)
  assert.equal(s.housekeeping, false, 'the first turn of a window is never housekeeping')
  assert.equal(s.lastTurn, null)

  // 2 — a terminal command whose argument carries something secret-looking
  s = t.feed('tool.start', toolStart('terminal', {
    command: 'curl -H "Authorization: ' + 'Bear' + 'er sample-redacted-value" https://api.example.com/v1/state --api_' + 'key=sample-redacted-value'
  }), { after: 400 })
  assert.equal(s.tool.label, 'running a command')
  assert.equal(s.steps, 1)
  assert.equal(s.tool.startedAt, t.at)
  assert.ok(s.tool.detail.length <= 90, `detail ${s.tool.detail.length} chars`)
  assert.ok(!/sample-redacted-value/.test(s.tool.detail), 'authorization value must not reach the screen')
  assert.ok(/curl/.test(s.tool.detail), 'the command head still shows')

  // 3 — the model narrates while it works
  s = t.feed('thinking.delta', { text: 'Checking the backend answer' }, { after: 600 })
  s = t.feed('thinking.delta', { text: '  before I touch the file.\n' }, { after: 300 })
  assert.equal(s.thought, 'Checking the backend answer before I touch the file.')
  assert.ok(s.thought.length <= 160)
  assert.equal(s.running, true)

  // 4 — the command finishes
  s = t.feed('tool.complete', { name: 'terminal', duration_s: 1.4 }, { after: 100 })
  assert.equal(s.tool, null)
  assert.equal(s.lastTool.label, 'running a command')
  assert.equal(s.lastTool.ms, 1400)
  assert.equal(s.lastTool.ok, true)
  assert.equal(s.recent.length, 1)
  assert.equal(s.recent[0].at, t.at)

  // 5 — a file read, then an MCP call that fails
  s = t.feed('tool.start', toolStart('read_file', { path: '~/notes/STATE.md' }), { after: 200 })
  assert.equal(s.tool.label, 'reading a file')
  assert.equal(s.tool.detail, '~/notes/STATE.md')
  assert.equal(s.steps, 2)
  s = t.feed('tool.complete', { name: 'read_file' }, { after: 900 })
  assert.equal(s.lastTool.ms, 900, 'no duration_s → measured from tool.start')

  s = t.feed('tool.start', toolStart('mcp__brain-2__search', { query: 'one lever' }), { after: 50 })
  assert.equal(s.tool.label, 'asking brain-2')
  assert.equal(s.tool.detail, 'one lever')
  assert.equal(s.steps, 3)
  s = t.feed('tool.complete', { name: 'mcp__brain-2__search', error: 'server unreachable' }, { after: 2_000 })
  assert.equal(s.lastTool.ok, false)
  assert.equal(s.recent.length, 3)
  assert.equal(s.recent[0].label, 'asking brain-2', 'newest first')
  assert.equal(s.recent[0].ok, false)

  // 6 — a helper is delegated, reports, finishes
  s = t.feed('subagent.start', { subagent_id: 'kid-1', goal: 'Read the three mirrors', task_index: 0, task_count: 1 }, { after: 100 })
  assert.deepEqual(s.subagents.map(x => [x.id, x.status]), [['kid-1', 'running']])
  s = t.feed('subagent.progress', { subagent_id: 'kid-1', goal: 'Read the three mirrors', tool_name: 'read_file', task_index: 0, task_count: 1 }, { after: 400 })
  assert.equal(s.subagents[0].tool, 'read_file')
  assert.equal(s.subagents[0].status, 'running')
  s = t.feed('subagent.complete', { subagent_id: 'kid-1', goal: 'Read the three mirrors', status: 'completed', task_index: 0, task_count: 1 }, { after: 3_000 })
  assert.equal(s.subagents[0].status, 'done')

  // 7 — Agent asks for a yes, then it is answered
  s = t.feed('approval.pending', { request_id: 'req-9', command: 'rm -rf build', description: 'Delete the build folder' }, { after: 100 })
  assert.deepEqual(s.needsYou, { kind: 'approval', text: 'Delete the build folder' })
  const quietBefore = s.lastEventAt
  s = t.feed('approval.received', { request_id: 'req-9' }, { after: 5_000 })
  assert.equal(s.needsYou, null)
  assert.ok(s.lastEventAt > quietBefore, 'lastEventAt moves with every event of the turn')

  // 8 — Agent speaks, then the turn ends
  s = t.feed('message.delta', { text: 'Done — the lever file is' }, { after: 200 })
  s = t.feed('message.delta', { text: ' unchanged.' }, { after: 100 })
  assert.equal(s.saying, 'Done — the lever file is unchanged.')

  const startedAt = s.startedAt
  s = t.feed('message.complete', { status: 'complete', text: 'Done.' }, { after: 500 })
  assert.equal(s.running, false)
  assert.equal(s.tool, null)
  assert.equal(s.needsYou, null)
  assert.equal(s.endedAt, t.at)
  assert.equal(s.lastTurn.outcome, 'done')
  assert.equal(s.lastTurn.steps, 3)
  assert.equal(s.lastTurn.modelCalls, 1)
  assert.equal(s.lastTurn.seconds, Math.round((t.at - startedAt) / 1000))
  assert.equal(s.recent.length, 3, 'the finished steps stay on screen while Agent is quiet')
  assert.equal(s.subagents.length, 1, 'a finished helper keeps its chip')
})

test('an interrupted turn and an error turn are named as such, never as stuck', () => {
  const a = turn()
  a.feed('message.start', {})
  a.feed('tool.start', toolStart('terminal', { command: 'sleep 600' }), { after: 100 })
  let s = a.feed('voice.interrupted', {}, { after: 4_000 })
  assert.equal(s.running, false)
  assert.equal(s.lastTurn.outcome, 'interrupted')

  const b = turn()
  b.feed('message.start', {})
  s = b.feed('error', { message: 'model overloaded' }, { after: 2_000 })
  assert.equal(s.lastTurn.outcome, 'error')

  const c = turn()
  c.feed('message.start', {})
  s = c.feed('message.complete', { status: 'interrupted' }, { after: 1_000 })
  assert.equal(s.lastTurn.outcome, 'interrupted')

  // The feed never prints a verdict — it stores the clock and stops there.
  assert.equal(typeof s.lastEventAt, 'number')
  assert.ok(!('stuck' in s), 'no stuck flag anywhere in the slice')
  assert.ok(!('quietFor' in s), 'quietFor is computed at render time, not stored')
})

/* ----------------------------------------------------------- housekeeping -- */

test("the host's automatic review turn is labelled housekeeping and never asks for a yes", () => {
  const t = turn()
  t.feed('message.start', {})
  t.feed('tool.start', toolStart('read_file', { path: 'a.md' }), { after: 100 })
  t.feed('tool.complete', { name: 'read_file' }, { after: 100 })
  let s = t.feed('message.complete', { status: 'complete' }, { after: 200 })
  assert.equal(s.housekeeping, false)

  // …and 1.2 s later a turn starts that Owner never asked for
  s = t.feed('message.start', {}, { after: 1_200 })
  assert.equal(s.housekeeping, true)
  assert.equal(s.running, true)

  s = t.feed('tool.start', toolStart('skill_view', { name: 'brain-2-value-page' }), { after: 100 })
  assert.equal(s.tool.label, 'housekeeping · opening a skill')
  assert.equal(s.recent.length, 0, 'a new turn starts its own step list')

  s = t.feed('approval.pending', { description: 'Write the skill file' }, { after: 100 })
  assert.equal(s.needsYou, null, 'housekeeping never raises needsYou')

  s = t.feed('tool.complete', { name: 'skill_view' }, { after: 300 })
  assert.equal(s.lastTool.label, 'housekeeping · opening a skill')
  assert.equal(s.recent[0].label, 'housekeeping · opening a skill')
})

test('a turn Owner asked for is not housekeeping, even right after the last one', () => {
  const t = turn()
  t.feed('message.start', {})
  t.feed('message.complete', { status: 'complete' }, { after: 500 })

  // he speaks (voice transcript) inside the 2 s window
  t.feed('voice.transcript', { text: 'check the lever again' }, { after: 400 })
  let s = t.feed('message.start', {}, { after: 300 })
  assert.equal(s.housekeeping, false)

  // and a turn that opens long after the last one is his too
  s = t.feed('message.complete', { status: 'complete' }, { after: 1_000 })
  s = t.feed('message.start', {}, { after: 30_000 })
  assert.equal(s.housekeeping, false)
})

/* ------------------------------------------------- focus beats everything -- */

test('a second chat never hijacks the focused one', () => {
  const facts = { focusedSessionId: S1, busy: false, busyBySession: {} }
  const t = turn(facts)

  t.feed('message.start', {})
  t.feed('tool.start', toolStart('terminal', { command: 'ls' }), { after: 100 })

  // the other chat is working hard; the box does not move
  let s = t.feed('message.start', {}, { after: 100, session: S2 })
  s = t.feed('tool.start', toolStart('web_search', { query: 'other chat' }), { after: 100, session: S2 })
  s = t.feed('tool.complete', { name: 'web_search' }, { after: 100, session: S2 })
  assert.equal(s.session, S1)
  assert.equal(s.steps, 1)
  assert.equal(s.tool.label, 'running a command')
  assert.equal(s.recent.length, 0)

  // the focused chat's own events still land
  s = t.feed('tool.complete', { name: 'terminal' }, { after: 100 })
  assert.equal(s.recent.length, 1)
  assert.equal(s.session, S1)
})

test('with nothing focused, the most recently active chat wins and says so', () => {
  const facts = { focusedSessionId: '', busy: false, busyBySession: {} }
  const t = turn(facts)

  let s = t.feed('message.start', {}, { session: S2 })
  assert.equal(s.session, S2)
  assert.equal(s.focused, false, 'the box must say "another chat"')

  s = t.feed('tool.start', toolStart('read_file', { path: 'b.md' }), { after: 100, session: S2 })
  assert.equal(s.steps, 1)

  // a different chat takes over: its turn is tracked from scratch, and the
  // other chat's history never gets printed under this one's name
  s = t.feed('message.start', {}, { after: 100, session: S1 })
  assert.equal(s.session, S1)
  assert.equal(s.steps, 0)
  assert.equal(s.lastTurn, null)
  assert.equal(s.recent.length, 0)
})

test('focus moving to the tracked chat flips `focused` with no event at all', () => {
  const t = turn({ focusedSessionId: '', busy: false, busyBySession: {} })
  let s = t.feed('message.start', {}, { session: S2 })
  assert.equal(s.focused, false)
  s = t.host({ focusedSessionId: S2, busy: false, busyBySession: {} }, 1_000)
  assert.equal(s.focused, true)
  assert.equal(s.session, S2)
})

/* ----------------------------------------------------------------- source -- */

test("source: none → host-busy → events, and the host's busy flag can hold a turn open", () => {
  const t = turn({ focusedSessionId: S1, busy: false, busyBySession: {} })
  let s = t.host()
  assert.equal(s.source, 'none')
  assert.equal(s.running, false)
  assert.equal(s.session, '')

  s = t.host({ focusedSessionId: S1, busy: true, busyBySession: {} }, 1_000)
  assert.equal(s.source, 'host-busy')
  assert.equal(s.running, true)
  assert.equal(s.session, S1, 'the host named the busy session')
  assert.equal(s.startedAt, t.at, 'the clock starts when the host says busy')

  s = t.feed('message.start', {}, { after: 500, facts: { focusedSessionId: S1, busy: true, busyBySession: {} } })
  assert.equal(s.source, 'events')

  // events say the turn is over but the host has not caught up: running stays
  // true (the contract's OR), and settles when the host agrees
  s = t.feed('message.complete', { status: 'complete' }, { after: 1_000, facts: { focusedSessionId: S1, busy: true, busyBySession: {} } })
  assert.equal(s.running, true)
  s = t.host({ focusedSessionId: S1, busy: false, busyBySession: { [S1]: false } }, 100)
  assert.equal(s.running, false)
  assert.equal(s.source, 'events')
})

test('busyBySession is read per session, not globally', () => {
  const t = turn({ focusedSessionId: S1, busy: false, busyBySession: { [S2]: true } })
  let s = t.host()
  assert.equal(s.source, 'none', 'another session being busy is not this box being busy')
  s = t.host({ focusedSessionId: S1, busy: false, busyBySession: { [S1]: true, [S2]: true } }, 100)
  assert.equal(s.source, 'host-busy')
  assert.equal(s.running, true)
})

/* ------------------------------- §7 amendment 1: calls that overlap --------- */

test('two overlapping read_file calls each keep their place; a completion retires only its own', () => {
  const t = turn()
  t.feed('message.start', {})

  let s = t.feed('tool.start', { tool_id: 'call-a', name: 'read_file', args: { path: 'SPEC.md' } }, { after: 100 })
  assert.equal(s.tool.detail, 'SPEC.md')
  const firstStartedAt = t.at

  s = t.feed('tool.start', { tool_id: 'call-b', name: 'read_file', args: { path: 'AGENTS.md' } }, { after: 100 })
  assert.equal(s.toolRuns.length, 2, 'both calls are in flight')
  assert.equal(s.tool.detail, 'AGENTS.md', 'the NEWEST running call is the one on the glass')
  assert.equal(s.steps, 2)

  // the FIRST call finishes. The second is still running, so the box must not
  // go blank — and the finished one is the one reported as lastTool.
  s = t.feed('tool.complete', { tool_id: 'call-a', name: 'read_file', duration_s: 0.4 }, { after: 300 })
  assert.equal(s.toolRuns.length, 1)
  assert.ok(s.tool, 'a completion never blanks a call that is still running')
  assert.equal(s.tool.detail, 'AGENTS.md')
  assert.equal(s.tool.startedAt, firstStartedAt + 100)
  assert.equal(s.lastTool.detail, 'SPEC.md', 'the row that finished is the one that just finished')
  assert.equal(s.lastTool.ms, 400)
  assert.equal(s.recent[0].detail, 'SPEC.md')

  s = t.feed('tool.complete', { tool_id: 'call-b', name: 'read_file', duration_s: 0.1 }, { after: 100 })
  assert.equal(s.toolRuns.length, 0)
  assert.equal(s.tool, null, 'with nothing left running the slot is empty, not stale')
  assert.equal(s.lastTool.detail, 'AGENTS.md')
})

test('with no tool_id the oldest call of that name retires first, and the list caps at 8', () => {
  const t = turn()
  t.feed('message.start', {})
  for (let i = 0; i < 10; i += 1) {
    t.feed('tool.start', { name: 'read_file', args: { path: `file-${i}.md` } }, { after: 10 })
  }
  let s = t.state
  assert.equal(s.toolRuns.length, 8, 'eight running calls at most')
  assert.equal(s.tool.detail, 'file-9.md', 'the newest is still the one shown')
  assert.equal(s.toolRuns[0].detail, 'file-2.md', 'the oldest two gave way')

  s = t.feed('tool.complete', { name: 'read_file' }, { after: 10 })
  assert.equal(s.lastTool.detail, 'file-2.md', 'a nameless completion retires the oldest call of that name')
  assert.equal(s.toolRuns.length, 7)
  assert.equal(s.tool.detail, 'file-9.md', 'and the newest running call keeps the glass')
})

/* -------------------- §7 amendment 2: what may open and close a turn ------- */

test('a late *.complete opens nothing on an idle session', () => {
  const t = turn()
  t.feed('message.start', {})
  t.feed('tool.start', toolStart('read_file', { path: 'SPEC.md' }), { after: 100 })
  t.feed('tool.complete', { name: 'read_file', duration_s: 0.2 }, { after: 200 })
  let s = t.feed('message.complete', { status: 'complete' }, { after: 100 })
  assert.equal(s.running, false)
  const endedAt = s.endedAt

  s = t.feed('subagent.complete', { subagent_id: 'kid-1', goal: 'read the spec', status: 'completed' }, { after: 9_000 })
  assert.equal(s.running, false, 'a straggling subagent.complete is not a new turn')
  assert.equal(s.endedAt, endedAt, 'and it does not reopen the turn that ended')

  const startedAt = s.startedAt
  s = t.feed('tool.complete', { name: 'read_file', duration_s: 0.2 }, { after: 3_000 })
  assert.equal(s.running, false, 'nor does a late tool.complete')
  assert.equal(s.startedAt, startedAt, 'no turn was opened, so no new clock was started')
  assert.equal(s.steps, 1, 'and a completion never counts as a step of its own')
})

test('a running turn closes when the host says not busy and 15 s of silence pass', () => {
  const busy = { focusedSessionId: S1, busy: true, busyBySession: { [S1]: true } }
  const idle = { focusedSessionId: S1, busy: false, busyBySession: { [S1]: false } }
  const t = turn(busy)
  t.feed('message.start', {}, { facts: busy })
  let s = t.feed('tool.start', toolStart('terminal', { command: 'node --test tests/' }), { after: 1_000, facts: busy })
  const lastEventAt = t.at

  s = t.host(busy, 60_000)
  assert.equal(s.running, true, 'a busy host holds the turn open however long it is quiet')

  // the host now says not busy — but it said so while the stream was still
  // fresh, so the 15 s are counted from the last EVENT, not from the flag
  const t2 = turn(busy)
  t2.feed('message.start', {}, { facts: busy })
  t2.feed('tool.start', toolStart('terminal', { command: 'node --test tests/' }), { after: 1_000, facts: busy })
  let s2 = t2.host(idle, 5_000)
  assert.equal(s2.running, true, 'five seconds of silence is not fifteen')
  s2 = t2.host(idle, 9_999)
  assert.equal(s2.running, true, 'and neither is 14.999')
  s2 = t2.host(idle, 1)
  assert.equal(s2.running, false, 'at 15 s of silence with the host reporting not busy, it ends')

  s = t.host(idle, 1)
  assert.equal(s.running, false, '15 s of silence with the host reporting not busy ends it')
  assert.equal(s.endedAt, lastEventAt, 'the work stopped when the news stopped, not when we noticed')
  assert.equal(s.lastTurn.outcome, 'done')
  assert.equal(s.lastTurn.endedAt, lastEventAt)
  assert.equal(s.tool, null)
  assert.equal(s.toolRuns.length, 0)
})

test('a host that reports nothing never closes a turn on silence alone', () => {
  const mute = { focusedSessionId: '', busyBySession: {} }
  const t = turn(mute)
  t.feed('message.start', {}, { facts: mute })
  let s = t.feed('tool.start', toolStart('terminal', { command: 'sleep 600' }), { after: 1_000, facts: mute })

  s = t.host(mute, 600_000)
  assert.equal(s.running, true, 'silence from the host is not a fact about the turn')
  assert.equal(s.endedAt, 0)
  assert.ok(s.tool, 'and the call it last saw start is still the call it reports')

  // another session named busy says nothing about THIS one either
  s = t.host({ focusedSessionId: '', busy: true, busyBySession: { [S2]: true } }, 60_000)
  assert.equal(s.running, true)
})

/* ------------------------------------------------------- bounded memory ---- */

test('memory stays bounded: 8 recent steps, 6 helpers, capped strings', () => {
  const t = turn()
  t.feed('message.start', {})
  for (let i = 0; i < 14; i += 1) {
    t.feed('tool.start', toolStart('read_file', { path: `file-${i}.md` }), { after: 50 })
    t.feed('tool.complete', { name: 'read_file' }, { after: 50 })
  }
  for (let i = 0; i < 9; i += 1) {
    t.feed('subagent.start', { subagent_id: `kid-${i}`, goal: `job ${i}`, task_index: i, task_count: 9 }, { after: 10 })
  }
  const long = 'x'.repeat(400)
  let s = t.feed('thinking.delta', { text: long }, { after: 10 })
  s = t.feed('message.delta', { text: long }, { after: 10 })
  s = t.feed('tool.start', toolStart('terminal', { command: long }), { after: 10 })

  assert.equal(s.recent.length, 8)
  assert.equal(s.subagents.length, 6)
  assert.equal(s.subagents[5].id, 'kid-8', 'the newest helpers are the ones kept')
  assert.equal(s.thought.length, 160)
  assert.equal(s.saying.length, 160)
  assert.ok(s.tool.detail.length <= 90)
  assert.equal(s.steps, 15, 'the step counter still counts every one of them')
})

/* -------------------------------------------------------- the label map ---- */

test('plain-word labels, and an unknown tool keeps its own name', () => {
  const cases = [
    ['terminal', 'running a command'],
    ['execute_code', 'running code'],
    ['read_file', 'reading a file'],
    ['write_file', 'editing a file'],
    ['patch', 'editing a file'],
    ['web_search', 'searching the web'],
    ['browser_click', 'using the browser'],
    ['skill_view', 'opening a skill'],
    ['delegate_task', 'handing work to a helper'],
    ['memory_search', 'checking memory'],
    ['honcho_get', 'checking memory'],
    ['computer_use', 'using the computer'],
    ['mcp__screenpipe__search-content', 'asking screenpipe'],
    ['some_new_tool', 'some_new_tool']
  ]
  for (const [name, label] of cases) assert.equal(M.jarvisActivityLabel(name, false), label, name)
  assert.equal(M.jarvisActivityLabel('terminal', true), 'housekeeping · running a command')
})

test('details come from the args and never carry a secret-looking value', () => {
  const detail = (name, payload) => M.jarvisActivityDetail(name, payload)
  assert.equal(detail('read_file', { args: { path: '/etc/hosts' } }), '/etc/hosts')
  assert.equal(detail('web_search', { args: { query: 'hermes plugin sdk' } }), 'hermes plugin sdk')
  assert.equal(detail('browser_open', { args: { url: 'https://example.com/agentic-playbook' } }), 'example.com')
  assert.equal(detail('delegate_task', { args: { goal: 'Read the mirrors' } }), 'Read the mirrors')
  assert.equal(detail('unknown_tool', { preview: 'whatever it was' }), 'whatever it was')

  const secrets = detail('terminal', { args: { command: 'deploy --pass' + 'word=sample-value --to' + 'ken sample-value -H "authorization: ' + 'Bear' + 'er sample-value"' } })
  assert.ok(!/sample-value/.test(secrets), secrets)
  // a key-named argument is never the one we print
  const byKey = detail('mcp__x__y', { args: { ['api' + '_key']: 'sample-value', q: 'the real query' } })
  assert.equal(byKey, 'the real query')
  const onlySecret = detail('mcp__x__y', { args: { ['api' + '_key']: 'sample-value' } })
  assert.equal(onlySecret, '', 'with nothing safe to say, say nothing')
})

/* ------------------------------------------------------------ Agent STATE --- */

/** A feed with a fake backend door; `answer` decides what /state returns. */
function feedWith(answer) {
  let clock = 1_700_000_000_000
  const calls = []
  const feed = M.createDataFeed({
    ctx: {
      rest: (path, opts) => {
        calls.push(path)
        if (path === '/state') return Promise.resolve(answer()).then(res => Object.assign({}, res, {
          settings: {
            schema_version: 1, profile_id: 'default', agent_name: 'Sample Agent', owner_label: 'Sample Owner',
            timezone: 'UTC',
            enabled_sources: ['agent_state', 'agent_helpers', 'next_meeting', 'today_plan', 'overnight_jobs', 'one_thing_scoreboard', 'spend', 'lever', 'brains', 'scoreboard', 'log'],
            brains: []
          }
        }))
        if (path === '/panel') return Promise.resolve(null)
        return Promise.reject(new Error('no route'))
      },
      onEvent: () => () => {},
      socket: () => () => {}
    },
    HermesSDK: { host: {
      state: {
        connectionId: { get: () => 'local' },
        profile: { get: () => 'default' }
      },
      profileRoutes: () => Promise.resolve([{ connectionId: 'local', profile: 'default', targetProfile: 'default' }])
    } },
    log: () => {},
    now: () => clock
  })
  return { feed, calls, tick: ms => { clock += ms }, at: () => clock }
}

test('agentState: an old backend with no agent_state key says so, and keeps nothing it never had', async () => {
  const env = feedWith(() => Promise.resolve({ lever: { text: 'Ship the NOW box', source: 'STATE.md', updatedAt: 1 } }))
  env.feed.start()
  await env.feed.refresh('state')
  const data = env.feed.get()
  env.feed.stop()

  assert.equal(data.agentState.status, 'unreachable')
  assert.equal(data.agentState.note, 'backend has no agent_state yet')
  assert.deepEqual(data.agentState.rows, [])
  assert.equal(data.lever.text, 'Ship the NOW box', 'the lever still lands off the same poll')
})

test('agentState: a good poll shapes the rows, a failed poll keeps them with their stamp', async () => {
  let mode = 'ok'
  // SPEC §8 amendment A ruling 7 — fixtures are SYNTHETIC: invented ids and
  // invented wording, never a row copied off Owner's real STATE file.
  const rows = [
    {
      id: 'demo-switch', where: 'waiting for the sample tap', next: 'Owner taps the sample switch',
      owner: 'Agent', follow_up_at: '2026-09-22T09:00+08:00', updated: '14:35',
      waiting_on_owner: true, overdue: false,
      brief: {
        title: 'Flip one sample switch', what: 'one setting on one sample screen',
        why: 'the sample run cannot start until it is on', do: 'open the sample panel and flip it',
        takes: 'two minutes', where: 'the sample settings screen', updated: '14:35'
      }
    },
    { id: 'demo-wave', where: 'four sample builders out', next: 'judge the sample wave', owner: 'Agent', follow_up_at: null, updated: null, waiting_on_owner: false, overdue: true }
  ]
  const env = feedWith(() => {
    if (mode === 'ok') return Promise.resolve({ agent_state: { rows, closed_count: 4, source: '~/.hermes/…/STATE.md', updatedAt: 1_789_810_000_000, note: null } })
    if (mode === 'missing') return Promise.resolve({ agent_state: { rows: [], closed_count: 0, note: 'STATE.md not found', updatedAt: 0 } })
    return Promise.reject(new Error('backend offline'))
  })

  env.feed.start()
  await env.feed.refresh('state')
  let data = env.feed.get()
  assert.equal(data.agentState.status, 'ok')
  assert.equal(data.agentState.closedCount, 4)
  assert.equal(data.agentState.updatedAt, 1_789_810_000_000)
  assert.equal(data.agentState.rows.length, 2)
  assert.deepEqual(data.agentState.rows[0], {
    // §8.4 item 1 — the row carries Agent's plain-words brief now, first key
    brief: {
      title: 'Flip one sample switch', what: 'one setting on one sample screen',
      why: 'the sample run cannot start until it is on', do: 'open the sample panel and flip it',
      takes: 'two minutes', where: 'the sample settings screen', updated: '14:35'
    },
    id: 'demo-switch', where: 'waiting for the sample tap', next: 'Owner taps the sample switch',
    owner: 'Agent', follow_up_at: '2026-09-22T09:00+08:00', updated: '14:35',
    waiting_on_owner: true, overdue: false
  })
  assert.equal(data.agentState.briefs, null,
    'a backend too old to have the briefs file sends nothing, and nothing is what is carried')
  assert.equal(data.agentState.rows[1].follow_up_at, null)
  assert.equal(data.agentState.rows[1].overdue, true)
  assert.equal(data.connection.backend, 'ok')

  // the backend falls over: the rows Owner last saw stay, with their own age
  mode = 'down'
  env.tick(60_000)
  await env.feed.refresh('state')
  data = env.feed.get()
  assert.equal(data.agentState.status, 'unreachable')
  assert.equal(data.agentState.note, 'backend unreachable')
  assert.equal(data.agentState.rows.length, 2, 'last good rows survive a failed poll')
  assert.equal(data.agentState.updatedAt, 1_789_810_000_000, 'with the stamp they were read at')
  assert.equal(data.connection.backend, 'offline')

  // the file itself is gone: the backend says rows [] + a note, which is
  // "unreachable" on screen, not "nothing is waiting on you"
  mode = 'missing'
  await env.feed.refresh('state')
  data = env.feed.get()
  env.feed.stop()
  assert.equal(data.agentState.status, 'unreachable')
  assert.equal(data.agentState.note, 'STATE.md not found')
})

test('agentState rows are capped and cleaned', () => {
  const many = Array.from({ length: 60 }, (_, i) => ({ id: `demo-row-${i}`, where: 'w', next: 'n' }))
  assert.equal(M.jarvisAgentRows(many).length, 40)
  assert.deepEqual(M.jarvisAgentRows(null), [])
  assert.deepEqual(M.jarvisAgentRows([{}, { id: 'keep' }]), [{
    brief: null, id: 'keep', where: '', next: '', owner: '', follow_up_at: null, updated: null,
    waiting_on_owner: false, overdue: false
  }], 'a row with no brief carries null — never an invented one')
  const long = M.jarvisAgentRows([{ id: 'demo-x', next: 'y'.repeat(400) }])[0]
  assert.ok(long.next.length <= 220)
})

/* ------------------------------------------------- the feed's own wiring --- */

test('the feed folds gateway events into data.activity and notifies on the beats', async () => {
  let clock = 1_700_000_000_000
  let handler = null
  const seen = []
  const feed = M.createDataFeed({
    ctx: {
      rest: () => Promise.reject(new Error('no backend')),
      onEvent: (type, fn) => { handler = fn; return () => {} }
    },
    HermesSDK: {
      host: {
        state: {
          focusedSessionId: { get: () => S1, listen: () => () => {} },
          busy: { get: () => false, listen: () => () => {} },
          busyBySession: { get: () => ({}), listen: () => () => {} }
        },
        request: () => Promise.reject(new Error('no gateway'))
      }
    },
    log: () => {},
    now: () => clock
  })
  feed.subscribe(d => seen.push(d.activity))
  feed.start()
  assert.equal(typeof handler, 'function', "the feed subscribes with ctx.onEvent('*')")

  handler({ type: 'message.start', session_id: S1, payload: {} })
  clock += 100
  handler({ type: 'tool.start', session_id: S1, payload: toolStart('terminal', { command: 'python3 scripts/build.py' }) })

  const activity = feed.get().activity
  assert.equal(activity.session, S1)
  assert.equal(activity.focused, true)
  assert.equal(activity.running, true)
  assert.equal(activity.tool.label, 'running a command')
  assert.equal(activity.tool.detail, 'python3 scripts/build.py')
  assert.ok(seen.length >= 2, 'turn start and tool start are instant notifies')
  assert.equal(seen[seen.length - 1].tool.detail, 'python3 scripts/build.py')

  // the ticker keeps working beside it
  assert.ok(feed.get().events.length >= 2)
  feed.stop()
})

test('deltas are throttled to ~4 a second, tool starts are not', async () => {
  let clock = 1_700_000_000_000
  let handler = null
  let notifies = 0
  const feed = M.createDataFeed({
    ctx: { rest: () => Promise.reject(new Error('no backend')), onEvent: (t, fn) => { handler = fn; return () => {} } },
    HermesSDK: { host: { state: { focusedSessionId: { get: () => S1 } }, request: () => Promise.reject(new Error('x')) } },
    log: () => {},
    now: () => clock
  })
  feed.subscribe(() => { notifies += 1 })
  feed.start()
  await new Promise(r => setTimeout(r, 120))
  notifies = 0
  handler({ type: 'message.start', session_id: S1, payload: {} })
  const afterStart = notifies
  assert.ok(afterStart >= 1, 'the turn opening is instant')

  for (let i = 0; i < 40; i += 1) {
    clock += 5
    handler({ type: 'message.delta', session_id: S1, payload: { text: `chunk ${i} ` } })
  }
  assert.equal(notifies, afterStart, '40 deltas in 200 ms fire no extra synchronous notify')
  await new Promise(r => setTimeout(r, 320))
  assert.ok(notifies - afterStart <= 2, `deltas flushed ${notifies - afterStart} times, expected ≤ 2`)
  assert.equal(feed.get().activity.saying.endsWith('chunk 39'), true)

  const before = notifies
  clock += 10
  handler({ type: 'tool.complete', session_id: S1, payload: { name: 'terminal', duration_s: 0.2 } })
  assert.ok(notifies > before, 'a tool finishing is instant')
  feed.stop()
})

/* ---------------------------------------- the six v3 blocks (SPEC §8.4) --- */
//
// The feed's ONE job with these: shape what came back, cap every list, and say
// out loud when a block is not there. It never computes a verdict and it never
// invents a value. Fixtures below are SYNTHETIC (§8 amendment A ruling 7).

test('the six blocks: a backend that never heard of one says which one, by name', () => {
  const law = [
    [M.jarvisHelpersFrom, 'agent_helpers'],
    [M.jarvisMeetingFrom, 'next_meeting'],
    [M.jarvisTodayFrom, 'today_plan'],
    [M.jarvisJobsFrom, 'overnight_jobs'],
    [M.jarvisStreaksFrom, 'one_thing_scoreboard'],
    [M.jarvisSpendFrom, 'spend']
  ]
  for (const [shape, name] of law) {
    const block = shape(undefined)
    assert.equal(block.status, 'unreachable', name)
    assert.equal(block.note, 'backend has no ' + name + ' yet')
    assert.equal(block.updatedAt, null, 'and it carries no stamp it never read')
  }
  // an empty box would read as "nothing to do", which would be a lie
  assert.deepEqual(M.jarvisHelpersFrom(undefined).running, [])
  assert.equal(M.jarvisStreaksFrom(undefined).buildStreak, null, 'never a zero it did not read')
})

test('the six blocks shape what came back, cap every list, and keep a null a null', () => {
  const helpers = M.jarvisHelpersFrom({
    status: 'ok', updatedAt: '2026-09-20T09:00:00+08:00', source: 'a sample file', note: null,
    running: Array.from({ length: 9 }, (_, i) => ({ id: 'demo-h-' + i, goal: 'sample goal ' + i, model: 'a-sample-model', startedAt: '2026-09-20T08:00:00+08:00' })),
    recent: [{ id: 'demo-h-x', goal: 'a sample finished goal', state: 'completed', endedAt: '2026-09-20T07:00:00+08:00', seconds: 12, summary: 'a sample summary', delivered: true }],
    runningCount: 9, todayCount: 14
  })
  assert.equal(helpers.status, 'ok')
  assert.equal(helpers.updatedAt, '2026-09-20T09:00:00+08:00', 'the stamp stays as the backend wrote it')
  assert.equal(helpers.running.length, 6, 'one long file can never push a box off the glass')
  assert.equal(helpers.running[0].seconds, null, 'a number the backend did not send is null, not 0')
  assert.equal(helpers.recent[0].delivered, true)

  const meeting = M.jarvisMeetingFrom({
    status: 'ok', next: { title: 'Sample stand-up', start: '2026-09-20T10:00:00+08:00', end: '2026-09-20T10:30:00+08:00', calendar: 'sample calendar', allDay: false, minutesUntil: 42 },
    later: [1, 2, 3, 4, 5].map(i => ({ title: 'Sample block ' + i, start: '2026-09-21T0' + i + ':00:00+08:00', allDay: false })),
    windowHours: 36
  })
  assert.equal(meeting.next.title, 'Sample stand-up')
  assert.equal(meeting.next.allDay, false)
  assert.equal(meeting.later.length, 3, 'the later list is capped')
  assert.equal(meeting.windowHours, 36)

  const today = M.jarvisTodayFrom({
    status: 'ok', date: '2026-09-20', isToday: true, headline: 'A sample headline',
    items: [1, 2, 3, 4, 5, 6].map(i => ({ kind: 'build', task: 'sample task ' + i, status: '', next: '' })),
    lever: { text: 'A sample lever', source: 'a sample file' }, fileUpdatedAt: '2026-09-20T06:00:00+08:00'
  })
  assert.equal(today.items.length, 4)
  assert.equal(today.lever.text, 'A sample lever')
  assert.equal(M.jarvisTodayFrom({ status: 'ok', lever: { text: '' } }).lever, null,
    'a lever with nothing in it is no lever')

  const jobs = M.jarvisJobsFrom({
    status: 'ok', window: { from: '2026-09-19T21:00:00+08:00', to: '2026-09-20T09:00:00+08:00' },
    total: 25, ok: 23,
    failed: Array.from({ length: 8 }, (_, i) => ({ id: 'demo-j-' + i, name: 'Sample job ' + i, lastStatus: 'error', error: 'a sample error' })),
    pausedCount: 1, nextUp: [{ name: 'Sample sweep', nextRunAt: '2026-09-20T10:00:00+08:00' }]
  })
  assert.equal(jobs.ok, 23)
  assert.equal(jobs.failed.length, 6, 'the failed list is capped')
  assert.equal(jobs.nextUp[0].name, 'Sample sweep')

  // ruling 1 — the streak file rides as `one_thing_scoreboard` on the wire
  const streaks = M.jarvisStreaksFrom({
    status: 'ok', buildStreak: 12, contentStreak: 0, bestBuildStreak: 14, lessonsShipped: 26,
    lastDays: Array.from({ length: 12 }, (_, i) => ({ date: '2026-09-' + (19 - i), build: true, content: i % 2 === 0, note: '' })),
    fileUpdatedAt: '2026-09-20T07:00:00+08:00', staleDays: 0
  })
  assert.equal(streaks.buildStreak, 12)
  assert.equal(streaks.contentStreak, 0, 'a zero IS a reading and is kept as one')
  assert.equal(streaks.lastDays.length, 7)
  assert.equal(M.jarvisStreaksFrom({ status: 'ok', lastDays: [{ date: '2026-09-19', build: 'maybe' }] }).lastDays[0].build, null,
    'a tick that was neither yes nor no is never guessed into a day')

  const spend = M.jarvisSpendFrom({
    status: 'ok',
    today: {
      byModel: [{ model: 'a-sample-model', calls: 142, inputTokens: 900000, outputTokens: 100000, cacheReadTokens: 0, costUsd: null }],
      totalCalls: 173, totalTokens: 1129000, costUsd: null, costKnown: false
    }
  })
  assert.equal(spend.today.byModel[0].costUsd, null, 'a dollar figure Hermes did not report stays null')
  assert.equal(spend.today.costKnown, false)
  assert.equal(spend.today.totalCalls, 173)
})

test('the six blocks ride the same /state answer, and a failed poll keeps them marked', async () => {
  let mode = 'ok'
  const env = feedWith(() => {
    if (mode === 'ok') {
      return Promise.resolve({
        agent_helpers: { status: 'ok', running: [{ id: 'demo-h', goal: 'a sample goal' }], recent: [], runningCount: 1, todayCount: 1 },
        next_meeting: { status: 'ok', next: { title: 'Sample stand-up', start: '2026-09-20T10:00:00+08:00' }, later: [], windowHours: 36 },
        today_plan: { status: 'ok', date: '2026-09-20', isToday: true, headline: 'A sample headline', items: [], lever: null },
        overnight_jobs: { status: 'ok', total: 4, ok: 4, failed: [], nextUp: [] },
        one_thing_scoreboard: { status: 'ok', buildStreak: 12, lastDays: [] },
        spend: { status: 'ok', today: { byModel: [], totalCalls: 0, totalTokens: 0, costKnown: false } }
      })
    }
    return Promise.reject(new Error('backend offline'))
  })

  env.feed.start()
  await env.feed.refresh('state')
  let data = env.feed.get()
  assert.equal(data.agentHelpers.status, 'ok')
  assert.equal(data.agentHelpers.running[0].goal, 'a sample goal')
  assert.equal(data.nextMeeting.next.title, 'Sample stand-up')
  assert.equal(data.todayPlan.headline, 'A sample headline')
  assert.equal(data.overnightJobs.ok, 4)
  assert.equal(data.streaks.buildStreak, 12, 'one_thing_scoreboard lands on data.streaks (ruling 1)')
  assert.equal(data.spend.today.costKnown, false)
  assert.deepEqual([...new Set(env.calls)].filter(p => p !== '/state' && p !== '/panel'), [],
    'all six ride the SAME /state answer as the lever — no second poll of the mini')

  mode = 'down'
  env.tick(60000)
  await env.feed.refresh('state')
  data = env.feed.get()
  env.feed.stop()
  for (const key of ['agentHelpers', 'nextMeeting', 'todayPlan', 'overnightJobs', 'streaks', 'spend']) {
    assert.equal(data[key].status, 'unreachable', key)
    assert.equal(data[key].stale, true, key + ' is marked stale, not blanked')
    assert.equal(data[key].note, 'backend unreachable')
  }
  assert.equal(data.streaks.buildStreak, 12, 'the number Owner last saw stays on the glass, with its reason')
})

/* ----------------------------------- voice today, measured by Jarvis ------ */

test('voiceToday: the clock only runs while a call is on, and demo never counts', () => {
  const day = M.jarvisSgtDay(1789800000000)
  let st = M.jarvisVoiceInitial(day)
  let at = 1789800000000
  const on = { call: 'on', demo: false }
  const off = { call: 'off', demo: false }

  st = M.jarvisVoiceToday(st, on, at)                  // the call opens
  assert.equal(st.calls, 1, 'the edge into a call is one call')
  assert.equal(st.seconds, 0, 'and nothing is counted for the edge itself')

  for (let i = 0; i < 4; i += 1) { at += 1000; st = M.jarvisVoiceToday(st, on, at) }
  assert.equal(st.seconds, 4, 'four one-second frames are four seconds')

  at += 1000; st = M.jarvisVoiceToday(st, off, at)
  assert.equal(st.on, false)
  assert.equal(st.seconds, 4, 'the second the call ended is not counted twice')

  // a window nobody watched: the gap is NOT a measurement
  at += 600000
  st = M.jarvisVoiceToday(st, on, at)
  at += 20000
  st = M.jarvisVoiceToday(st, on, at)
  assert.equal(st.calls, 2)
  assert.equal(st.seconds, 4, 'a gap longer than five seconds is never counted')

  // DEMO is a label machine (§4.6): it can never add a second
  const demo = M.jarvisVoiceToday(M.jarvisVoiceInitial(day), { call: 'on', demo: true }, at)
  assert.equal(demo.calls, 0)
  assert.equal(demo.seconds, 0)

  // and the same state, same frame, same clock is the SAME object back
  const still = M.jarvisVoiceToday(demo, { call: 'off', demo: true }, at)
  assert.equal(still, demo, 'nothing moved, so the feed can skip a notify')
})

test('voiceToday: a new configured-timezone day starts at zero, and survives a reload', () => {
  const at = 1789800000000
  const day = M.jarvisSgtDay(at)
  assert.match(day, /^\d{4}-\d{2}-\d{2}$/)

  let st = M.jarvisVoiceToday(M.jarvisVoiceInitial(day), { call: 'on' }, at)
  st = M.jarvisVoiceToday(st, { call: 'on' }, at + 3000)
  assert.equal(st.seconds, 3)

  const tomorrow = at + 86400000
  const rolled = M.jarvisVoiceToday(st, { call: 'on' }, tomorrow)
  assert.equal(rolled.date, M.jarvisSgtDay(tomorrow))
  assert.notEqual(rolled.date, day)
  assert.equal(rolled.seconds, 0, "yesterday's numbers are gone, never carried or averaged")
  assert.equal(rolled.calls, 1, 'and today opens with the call that is running')

  // the three fields the glass reads
  assert.deepEqual(M.jarvisVoiceFace(st), { seconds: 3, calls: 1, date: day })
  assert.deepEqual(M.jarvisVoiceFace(null), { seconds: 0, calls: 0, date: '' })

  // localStorage, in both directions — and never a throw
  const cells = new Map()
  const store = { getItem: k => (cells.has(k) ? cells.get(k) : null), setItem: (k, v) => cells.set(k, String(v)) }
  assert.equal(M.jarvisVoiceSave(store, st, 'test:voice'), true)
  const back = M.jarvisVoiceLoad(store, at, 'test:voice', 'UTC')
  assert.equal(back.seconds, 3)
  assert.equal(back.calls, 1)
  assert.equal(back.on, false, 'a reloaded window is not in a call it cannot see')
  assert.equal(M.jarvisVoiceLoad(store, tomorrow).seconds, 0, 'yesterday\'s file does not become today')

  const angry = { getItem: () => { throw new Error('no storage here') }, setItem: () => { throw new Error('no') } }
  assert.equal(M.jarvisVoiceLoad(angry, at).seconds, 0, 'a window that refuses storage still counts live')
  assert.equal(M.jarvisVoiceSave(angry, st), false)
  assert.equal(M.jarvisVoiceLoad(null, at).calls, 0)
  cells.set('hermes-jarvis:voice-today', 'not json at all')
  assert.equal(M.jarvisVoiceLoad(store, at).seconds, 0, 'and a wiped or broken cell starts today at zero')
})

// Agentic Playbook — by Kezy
