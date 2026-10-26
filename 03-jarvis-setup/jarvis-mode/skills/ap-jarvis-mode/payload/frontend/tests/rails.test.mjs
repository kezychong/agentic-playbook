// tests/rails.test.mjs — node --test tests/rails.test.mjs
//
// SPEC §8.4 "the glass: two rails, rows a person can read".
//
// Every reader in 50-overlay.js is PURE — one backend block in, the words that
// go on the glass out — so this file needs no browser: it reads 10-theme.js +
// 50-overlay.js as text and wraps them in a Function, the same way
// tests/plugin-smoke.test.mjs loads the overlay and tests/scene.test.mjs loads
// the scene. The last third does use a stub DOM, because WAITING ON YOU rows
// are real buttons and "can Owner open one with the keyboard" is a question
// only the DOM can answer.
//
// HONESTY LAW (SPEC §8.4): nothing on this glass may be invented. Every row,
// every calendar title, every helper goal and every id below is SYNTHETIC —
// `demo-…` ids and sample wording that exists nowhere but in these fixtures.
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'

const SCOPE_SRC = fileURLToPath(new URL('../src/05-scope.js', import.meta.url))
const THEME_SRC = fileURLToPath(new URL('../src/10-theme.js', import.meta.url))
const OVERLAY_SRC = fileURLToPath(new URL('../src/50-overlay.js', import.meta.url))

/* --------------------------------------------------------------- the DOM -- */

const ctx2d = new Proxy({}, {
  get: (t, k) => {
    if (k === 'canvas') return { width: 100, height: 100 }
    if (k === 'createLinearGradient' || k === 'createRadialGradient') return () => ({ addColorStop() {} })
    if (k === 'measureText') return () => ({ width: 40 })
    return typeof k === 'string' ? () => undefined : t[k]
  },
  set: () => true
})

/* How tall the stub window is. §8 amendments C8 made the rails a LADDER, so
 * height is now part of what a rail test is asking about: 900 px — the screen
 * this plugin was built on — is the default, and a test that wants every box
 * at once raises it and puts it back. */
let VIEW_H = 900

function domNode(tag) {
  const n = {
    tagName: String(tag).toUpperCase(), className: '', _text: '', children: [], childNodes: [],
    style: { setProperty() {}, removeProperty() {} }, attributes: {}, parentNode: null,
    blurred: 0,
    get textContent() { return this._text },
    set textContent(v) { this._text = String(v); this.children.length = 0; this.childNodes.length = 0 },
    classList: {
      _s: new Set(),
      add(...c) { c.forEach(x => this._s.add(x)) },
      remove(...c) { c.forEach(x => this._s.delete(x)) },
      toggle(c, on) { on ? this._s.add(c) : this._s.delete(c) },
      contains(c) { return this._s.has(c) }
    },
    appendChild(c) { c.parentNode = this; this.children.push(c); this.childNodes.push(c); return c },
    removeChild(c) {
      this.children = this.children.filter(x => x !== c)
      this.childNodes = this.childNodes.filter(x => x !== c)
      c.parentNode = null
    },
    setAttribute(k, v) { this.attributes[k] = v },
    getAttribute(k) { return this.attributes[k] ?? null },
    querySelector: () => null, querySelectorAll: () => [],
    _on: {},
    addEventListener(type, fn) { (this._on[type] || (this._on[type] = [])).push(fn) },
    removeEventListener(type, fn) { this._on[type] = (this._on[type] || []).filter(x => x !== fn) },
    dispatch(type, event) {
      const ev = event || { type, preventDefault() {}, stopPropagation() {} }
      ;(this._on[type] || []).slice().forEach(fn => fn(ev))
      return ev
    },
    click() { this.dispatch('click') },
    focus() {}, blur() { this.blurred += 1 },
    getContext: () => ctx2d, clientWidth: 1440, get clientHeight() { return VIEW_H }, width: 0, height: 0
  }
  n.classList = { ...n.classList, _s: new Set() }
  n._on = {}
  return n
}

function env() {
  VIEW_H = 900   // every test starts on the 900 px screen unless it says otherwise
  const win = {
    location: { search: '', href: 'app://hermes/index.html' },
    localStorage: (() => {
      const cells = new Map()
      return {
        getItem: k => (cells.has(k) ? cells.get(k) : null),
        setItem: (k, v) => { cells.set(k, String(v)) },
        removeItem: k => { cells.delete(k) }
      }
    })(),
    requestAnimationFrame: () => 1, cancelAnimationFrame: () => {},
    addEventListener: () => {}, removeEventListener: () => {},
    matchMedia: () => ({ matches: false }),
    setTimeout, clearTimeout, setInterval, clearInterval
  }
  const doc = {
    body: domNode('body'), head: domNode('head'), documentElement: domNode('html'),
    activeElement: null,
    createElement: domNode, createTextNode: t => ({ nodeValue: String(t) }),
    querySelector: () => null, querySelectorAll: () => [],
    getElementById: () => null,
    _on: {},
    addEventListener(type, fn) { (this._on[type] || (this._on[type] = [])).push(fn) },
    removeEventListener(type, fn) { this._on[type] = (this._on[type] || []).filter(x => x !== fn) },
    fire(type, event) { (this._on[type] || []).slice().forEach(fn => fn(event)) }
  }
  globalThis.window = win
  globalThis.document = doc
  return { win, doc }
}

/** 10-theme.js + 50-overlay.js as text, with every §8.4 reader handed back. */
function loadRails(e) {
  const source = fs.readFileSync(SCOPE_SRC, 'utf8') + '\n' +
    fs.readFileSync(THEME_SRC, 'utf8') + '\n' + fs.readFileSync(OVERLAY_SRC, 'utf8')
  return new Function('window', 'document', `${source}
    return { JARVIS_CSS, createOverlay, jarvisRailCaps, jarvisRailScale, jarvisStateRows, jarvisWaitingRows, jarvisBriefLines,
             jarvisCountdown, jarvisBlockWord, jarvisMeetingLines, jarvisHelperRows,
             jarvisTodayLines, jarvisJobsLines, jarvisSpendLines, jarvisStreakLines,
             jarvisClock, jarvisClockReadout, jarvisCount, jarvisDateWord }`)(e.win, e.doc)
}

function kit() {
  return loadRails(env())
}

function findByClass(node, cls, out = []) {
  if (!node) return out
  const named = typeof node.className === 'string' && node.className.split(' ').includes(cls)
  const added = !!node.classList && typeof node.classList.contains === 'function' && node.classList.contains(cls)
  if (named || added) out.push(node)
  ;(node.childNodes || []).forEach(kid => findByClass(kid, cls, out))
  return out
}

function textsOf(node, cls) {
  return findByClass(node, cls).map(n => n.textContent)
}

/** Every string anywhere under `node`. The stub DOM keeps each node's own text,
 *  so a row built out of <b>/<i>/<span> is read here and not by its parent. */
function allTexts(node, out = []) {
  if (!node) return out
  if (typeof node.textContent === 'string' && node.textContent) out.push(node.textContent)
  ;(node.childNodes || []).forEach(kid => allTexts(kid, out))
  return out
}

const says = (node, re) => allTexts(node).some(t => (re instanceof RegExp ? re.test(t) : t === re))

function findByAttr(node, attr, value) {
  if (!node) return null
  if (node.attributes && node.attributes[attr] === value) return node
  for (const kid of node.childNodes || []) {
    const hit = findByAttr(kid, attr, value)
    if (hit) return hit
  }
  return null
}

/* ------------------------------------------------------------- fixtures --- */

const T0 = 1789800000000     // a fixed clock shared by every sample

const ok = (body, extra) => Object.assign({ status: 'ok', note: null, updatedAt: null, source: 'sample', stale: false }, body, extra || {})

// A synthetic backend, invented end to end (SPEC §8.4 honesty law).
const HELPERS = ok({
  running: [
    { id: 'demo-helper-1', goal: 'Read the sample folder and list what changed', model: 'a-sample-model', startedAt: new Date(T0 - 118000).toISOString(), seconds: null, origin: 'chat' },
    { id: 'demo-helper-2', goal: 'Draft the sample summary for the sample review', model: 'a-sample-model', startedAt: new Date(T0 - 42000).toISOString(), seconds: null, origin: 'cron' }
  ],
  recent: [
    { id: 'demo-helper-3', goal: 'Check the sample numbers against the sample file', state: 'completed', endedAt: new Date(T0 - 360000).toISOString(), seconds: 64, summary: 'Found two sample rows that disagree', delivered: true, origin: 'chat' },
    { id: 'demo-helper-4', goal: 'Sweep the sample inbox', state: 'failed', endedAt: new Date(T0 - 900000).toISOString(), seconds: 20, summary: 'The sample sweep stopped on a sample permission', delivered: false, origin: 'telegram' }
  ],
  runningCount: 2, todayCount: 4
})

const MEETING = ok({
  next: {
    title: 'Sample stand-up with the sample team', start: new Date(T0 + 2520000).toISOString(),
    end: new Date(T0 + 4320000).toISOString(), calendar: 'sample calendar', allDay: false, minutesUntil: 42
  },
  later: [
    { title: 'Sample review call', start: new Date(T0 + 100800000).toISOString(), end: null, calendar: 'sample calendar', allDay: false, minutesUntil: 1680 },
    { title: 'Sample all-day block', start: new Date(T0 + 187200000).toISOString(), end: null, calendar: 'sample calendar', allDay: true, minutesUntil: 3120 }
  ],
  windowHours: 36
})

const TODAY = ok({
  date: '2026-09-20', isToday: true, headline: 'Ship the sample thing end to end, then write the sample lesson.',
  items: [
    { kind: 'build', task: 'Finish the sample rail and look at every sample size', status: 'in progress', next: '' },
    { kind: 'content', task: 'Write the sample lesson from this sample build', status: '', next: '' },
    { kind: 'momentum', task: 'Send the two sample replies', status: 'done', next: '' }
  ],
  lever: { text: 'Ship the sample lever so the sample glass is useful', source: 'sample STATE file' },
  fileUpdatedAt: new Date(T0 - 7200000).toISOString()
})

const JOBS = ok({
  window: { from: new Date(T0 - 48000000).toISOString(), to: new Date(T0).toISOString() },
  total: 25, ok: 23,
  failed: [
    { id: 'demo-job-1', name: 'Sample nightly sweep', lastRunAt: new Date(T0 - 21600000).toISOString(), lastStatus: 'error', error: 'the sample source answered 500 twice in a row' },
    { id: 'demo-job-2', name: 'Sample digest', lastRunAt: new Date(T0 - 18000000).toISOString(), lastStatus: 'timeout', error: 'the sample digest ran past its sample budget' }
  ],
  pausedCount: 1,
  nextUp: [{ name: 'Sample morning sweep', nextRunAt: new Date(T0 + 4200000).toISOString() }]
})

const STREAKS = ok({
  buildStreak: 12, contentStreak: 3, bestBuildStreak: 14, lessonsShipped: 26,
  lastDays: [
    { date: '2026-09-19', build: true, content: true, note: '' },
    { date: '2026-09-18', build: true, content: false, note: '' },
    { date: '2026-09-17', build: true, content: true, note: '' }
  ],
  fileUpdatedAt: new Date(T0 - 3600000).toISOString(), staleDays: 0
})

const SPEND = ok({
  today: {
    byModel: [
      { model: 'a-sample-model', calls: 142, inputTokens: 900000, outputTokens: 100000, cacheReadTokens: 0, costUsd: null },
      { model: 'another-sample-model', calls: 31, inputTokens: 120000, outputTokens: 9000, cacheReadTokens: 0, costUsd: null }
    ],
    totalCalls: 173, totalTokens: 1129000, costUsd: null, costKnown: false
  }
})

const VOICE = { seconds: 1380, calls: 4, date: '2026-09-20' }

// WAITING ON YOU / AGENT IN FLIGHT, briefs and all — synthetic ids only.
const STATE = {
  status: 'ok',
  updatedAt: T0 - 720000,
  rows: [
    {
      id: 'demo-switch', where: 'waiting on the sample switch', next: 'Owner flips the sample switch',
      owner: 'Owner', follow_up_at: new Date(T0 - 172800000).toISOString(), updated: '14:35',
      waiting_on_owner: true, overdue: true,
      brief: {
        title: 'Flip one sample switch', what: 'one setting on one sample screen',
        why: 'the sample run cannot start until it is on', do: 'open the sample panel, flip it, say done',
        takes: 'two minutes', where: 'the sample settings screen', updated: '14:35'
      }
    },
    {
      id: 'demo-approve', where: 'waiting on a sample yes', next: 'Owner says yes to the sample draft',
      owner: 'Owner', follow_up_at: new Date(T0 + 7200000).toISOString(), updated: '13:02',
      waiting_on_owner: true, overdue: false,
      brief: { title: 'Approve the sample draft', what: 'one sample draft', why: '', do: 'read it and say yes or no', takes: 'five minutes', where: '', updated: '13:02' }
    },
    {
      id: 'demo-no-brief', where: 'waiting on a sample choice', next: 'Owner picks one of the two sample options',
      owner: 'Owner', follow_up_at: null, updated: null, waiting_on_owner: true, overdue: false, brief: null
    },
    {
      id: 'demo-redeploy', where: 'the sample service', next: 'redeploy the sample service and restart it',
      owner: 'Agent', follow_up_at: new Date(T0 + 86400000).toISOString(), updated: '12:10',
      waiting_on_owner: false, overdue: false, brief: null
    },
    {
      id: 'demo-watch', where: 'the sample weekly run', next: 'watch the sample weekly run for a refusal',
      owner: 'Agent', follow_up_at: null, updated: null, waiting_on_owner: false, overdue: false, brief: null
    }
  ],
  closedCount: 4, note: null
}

/* ============================================================ the numbers == */

test('§8.4 — the little readers: a clock, a token count and a plain date', () => {
  const k = kit()
  assert.equal(k.jarvisClock(0), '0:00')
  assert.equal(k.jarvisClock(9), '0:09')
  assert.equal(k.jarvisClock(114), '1:54')
  assert.equal(k.jarvisClock(3723), '1:02:03')

  assert.equal(k.jarvisCount(940), '940')
  assert.equal(k.jarvisCount(4210), '4.2k')
  assert.equal(k.jarvisCount(42100), '42k')
  assert.equal(k.jarvisCount(1300000), '1.3M')
  assert.equal(k.jarvisCount(null), '0')

  // a date with no time in it has no timezone to be shifted by
  assert.equal(k.jarvisDateWord('2026-09-17'), '17 Sep')
  assert.equal(k.jarvisDateWord('2026-01-01'), '1 Jan')
  assert.equal(k.jarvisDateWord('not a date'), 'not a date')
})

test('§8.4 item 5 — the countdown says now, minutes, hours, tomorrow, then a date', () => {
  const k = kit()
  const at = T0

  const soon = k.jarvisCountdown(new Date(at + 2520000).toISOString(), new Date(at + 4320000).toISOString(), at)
  assert.equal(soon.big, 'in 42 min')
  assert.equal(soon.minutes, 42)
  assert.equal(soon.running, false)
  assert.equal(soon.state, '', '42 minutes out is not a warning')
  assert.match(soon.range, /^\d\d:\d\d–\d\d:\d\d$/, 'the range reads as two configured-zone clock times')

  assert.equal(k.jarvisCountdown(new Date(at + 600000).toISOString(), null, at).state, 'warm',
    'inside a quarter of an hour the box warms')
  assert.equal(k.jarvisCountdown(new Date(at + 120000).toISOString(), null, at).state, 'hot',
    'inside five minutes it goes coral')

  const live = k.jarvisCountdown(new Date(at - 300000).toISOString(), new Date(at + 900000).toISOString(), at)
  assert.equal(live.big, 'now')
  assert.equal(live.running, true)
  assert.equal(live.state, 'hot')

  assert.match(k.jarvisCountdown(new Date(at + 3 * 3600000).toISOString(), null, at).big, /^(in \d+ h|tomorrow \d\d:\d\d)$/)
  assert.match(k.jarvisCountdown(new Date(at + 30 * 3600000).toISOString(), null, at).big, /^(tomorrow \d\d:\d\d|\d{1,2} \w{3,4} \d\d:\d\d)$/)
  assert.match(k.jarvisCountdown(new Date(at + 5 * 86400000).toISOString(), null, at).big, /^\d{1,2} \w{3,4} \d\d:\d\d$/)

  const none = k.jarvisCountdown(null, null, at)
  assert.equal(none.ok, false, 'no start stamp is not a countdown, and never a guess')
  assert.equal(none.big, '')
})

test('configured timezone controls the clock, meeting day, and task due day', () => {
  const k = kit()
  const at = Date.parse('2026-01-02T04:30:00Z')
  const next = '2026-01-02T05:30:00Z'

  assert.match(k.jarvisClockReadout(at, 'UTC'), /^04:30:00 /)
  assert.match(k.jarvisClockReadout(at, 'America/New_York'), /^23:30:00 /)
  assert.equal(k.jarvisCountdown(next, null, at, 'UTC').big, 'in 1 h')
  assert.equal(k.jarvisCountdown(next, null, at, 'America/New_York').big, 'tomorrow 00:30')

  const row = {
    status: 'ok', updatedAt: at, rows: [{
      id: 'sample-due', next: 'sample follow-up', follow_up_at: next,
      waiting_on_owner: true, overdue: false
    }]
  }
  assert.equal(k.jarvisStateRows(row, at, {}, '', 'UTC').waiting[0].due, 'due today 05:30')
  assert.equal(k.jarvisStateRows(row, at, {}, '', 'America/New_York').waiting[0].due, 'due tomorrow 00:30')
})

test('§8.3 — a block says its own word: ok, stale, missing, or never served', () => {
  const k = kit()
  assert.deepEqual(k.jarvisBlockWord(ok({})), { ok: true, word: '', note: '', stale: false })
  assert.deepEqual(k.jarvisBlockWord(ok({}, { status: 'stale', note: 'read 3 h ago' })),
    { ok: true, word: 'stale', note: 'read 3 h ago', stale: true })
  assert.deepEqual(k.jarvisBlockWord(ok({}, { status: 'missing', note: 'not found: a sample path' })),
    { ok: false, word: 'missing', note: 'not found: a sample path', stale: false })
  // the old-backend law (§8.4 item 1): a Hermes too old to know a block says so
  assert.deepEqual(k.jarvisBlockWord({ status: 'unreachable', note: 'backend has no spend yet' }),
    { ok: false, word: 'unreachable', note: 'backend has no spend yet', stale: false })
  assert.deepEqual(k.jarvisBlockWord(null), { ok: false, word: 'unreachable', note: '', stale: false })
})

/* ================================================== the six §8.4 readers == */

test('§8.4 item 5 — NEXT MEETING: the countdown, the title, the later lines', () => {
  const k = kit()
  const lines = k.jarvisMeetingLines(MEETING, T0, { later: 2 })
  assert.equal(lines.status, 'ok')
  assert.equal(lines.big, 'in 42 min')
  assert.equal(lines.title, 'Sample stand-up with the sample team')
  assert.equal(lines.calendar, 'sample calendar')
  assert.equal(lines.later.length, 2)
  assert.equal(lines.later[1].right, 'all day', 'an all-day block says so instead of a time')

  assert.equal(k.jarvisMeetingLines(MEETING, T0, { later: 0 }).later.length, 0,
    'a short window drops the later lines whole')

  const clear = k.jarvisMeetingLines(ok({ next: null, later: [], windowHours: 36 }), T0)
  assert.equal(clear.empty, 'none in the next 36 h', 'an empty calendar is a reading, and says the window')
  assert.equal(clear.big, '')

  const dark = k.jarvisMeetingLines({ status: 'unreachable', note: 'backend has no next_meeting yet' }, T0)
  assert.equal(dark.status, 'unreachable')
  assert.equal(dark.note, 'backend has no next_meeting yet')
  assert.equal(dark.title, '', 'nothing is drawn from a block that was never served')

  const late = k.jarvisMeetingLines(ok({ next: MEETING.next }, { status: 'stale', note: 'calendar read 20 min ago' }), T0)
  assert.equal(late.stale, true)
  assert.equal(late.big, 'in 42 min', 'a stale calendar still shows what it last knew, marked')
})

test("§8.4 item 4 — AGENT'S HELPERS counts what is running and names what finished", () => {
  const k = kit()
  const activity = {
    subagents: [
      { id: 'sub-1', label: 'reader', status: 'running', tool: 'read_file' },
      { id: 'sub-2', label: 'writer', status: 'completed', tool: '' }
    ]
  }
  const rows = k.jarvisHelperRows(HELPERS, activity, T0, { helpers: 3, helpersDone: 2 })
  assert.equal(rows.status, 'ok')
  assert.equal(rows.running, 3, 'two on the mini plus one in this turn')
  assert.equal(rows.header, '3 RUNNING')
  assert.equal(rows.rows[0].text, 'Read the sample folder and list what changed')
  assert.equal(rows.rows[0].meta, 'a-sample-model · 1:58', 'the model and how long it has been up')
  assert.equal(rows.rows[2].tag, 'in this turn', 'a helper spawned in the chat is never confused with one on the mini')
  assert.equal(rows.rows[3].state, 'done')
  assert.equal(rows.rows[4].state, 'failed', 'a helper that failed is marked as one')

  const tight = k.jarvisHelperRows(HELPERS, activity, T0, { helpers: 1, helpersDone: 0 })
  assert.equal(tight.rows.length, 1, 'a short window draws one WHOLE row')
  assert.equal(tight.more, 4, 'and counts every row it is holding back')
  assert.equal(tight.header, '3 RUNNING', 'the true count never shrinks with the box')

  const quiet = k.jarvisHelperRows(ok({ running: [], recent: [], runningCount: 0, todayCount: 0 }), null, T0)
  assert.equal(quiet.header, 'NONE RUNNING')
  assert.equal(quiet.empty, 'no helpers in the last 24 h')

  const dark = k.jarvisHelperRows({ status: 'unreachable', note: 'backend has no agent_helpers yet' }, null, T0)
  assert.equal(dark.status, 'unreachable')
  assert.equal(dark.note, 'backend has no agent_helpers yet')
  assert.deepEqual(dark.rows, [])
})

test('§8.4 items 2 + 6 — TODAY leads with the ONE lever, then today\'s contract', () => {
  const k = kit()
  const lines = k.jarvisTodayLines(TODAY, null, 'ok', T0, { items: 3, todayHead: true })
  assert.equal(lines.lever, 'Ship the sample lever so the sample glass is useful',
    'ONE LEVER is line 1 of this box now, not a box of its own')
  assert.equal(lines.leverNote, 'sample STATE file')
  assert.equal(lines.headline, 'Ship the sample thing end to end, then write the sample lesson.')
  assert.equal(lines.items.length, 3)
  assert.deepEqual(lines.items.map(i => i.mark), ['◐', '○', '●'], 'in progress, not started, done')
  assert.equal(lines.items[0].kind, 'BUILD')
  assert.equal(lines.tag, '', 'a card written for today needs no warning')

  // the v1 reading wins when the backend still serves it beside the plan
  const v1 = k.jarvisTodayLines(TODAY, { text: 'The sample v1 lever', source: 'sample file' }, 'ok', T0)
  assert.equal(v1.lever, 'The sample v1 lever')

  const noLever = k.jarvisTodayLines(ok({ date: '2026-09-20', isToday: true, items: [], headline: '' }), null, 'ok', T0)
  assert.equal(noLever.lever, 'no lever set', 'no lever is said out loud, never invented')
  assert.equal(noLever.empty, 'no contract written for today')

  const old = k.jarvisTodayLines(ok({ date: '2026-09-17', isToday: false, headline: 'A sample headline', items: [] }), null, 'ok', T0)
  assert.equal(old.tag, 'SET 17 SEP · NOT TODAY', 'a card set days ago says which day it is for')
  assert.equal(old.tagState, 'warn')

  const short = k.jarvisTodayLines(TODAY, null, 'ok', T0, { items: 1, todayHead: false })
  assert.equal(short.headline, '', 'the headline is the first thing a short window gives up')
  assert.equal(short.items.length, 1)
  assert.equal(short.more, 2)

  const dark = k.jarvisTodayLines({ status: 'unreachable', note: 'backend has no today_plan yet' }, null, 'unreachable', T0)
  assert.equal(dark.status, 'unreachable')
  assert.equal(dark.lever, 'unreachable')
  assert.deepEqual(dark.items, [])
})

test('TODAY display caps do not turn a real contract into an empty contract', () => {
  const k = kit()
  const capped = k.jarvisTodayLines(TODAY, null, 'ok', T0, { items: 0, todayHead: false })
  assert.equal(capped.items.length, 0)
  assert.equal(capped.headline, '')
  assert.equal(capped.more, 3)
  assert.equal(capped.empty, '', 'hidden display rows are still real underlying content')

  const trulyEmpty = k.jarvisTodayLines(ok({
    date: '2026-09-20', isToday: true, items: [], headline: ''
  }), null, 'ok', T0, { items: 0, todayHead: false })
  assert.equal(trulyEmpty.more, 0)
  assert.equal(trulyEmpty.empty, 'no contract written for today')
})

// §8 amendment C9 — THE STATUS WORD IS MATCHED WHOLE.
test('§8 amendment C9 — `not-started` is not-started, and an unknown word is shown', () => {
  const k = kit()
  const card = ok({
    date: '2026-09-20', isToday: true, headline: '',
    items: [
      { kind: 'build', task: 'A sample task nobody has begun', status: 'not-started', next: '' },
      { kind: 'content', task: 'A sample task under way', status: 'in_progress', next: '' },
      { kind: 'momentum', task: 'A sample task that shipped', status: 'DONE', next: '' },
      { kind: 'build', task: 'A sample task with a word we do not know', status: 'parked', next: '' }
    ],
    lever: null, fileUpdatedAt: new Date(T0 - 7200000).toISOString()
  })
  const lines = k.jarvisTodayLines(card, null, 'ok', T0, { items: 4, todayHead: true })
  assert.deepEqual(lines.items.map(i => i.mark), ['○', '◐', '●', '○'],
    'not-started, in-progress, done, and an unknown word drawn as not-started')
  assert.deepEqual(lines.items.map(i => i.state), ['', 'live', 'done', ''],
    '"not-started" no longer matches on the substring "started"')
  assert.deepEqual(lines.items.map(i => i.raw), ['', '', '', 'parked'],
    'only the word this plugin does not know is printed beside its task')

  // a card with no status at all says nothing extra: an empty word is not an
  // unknown one, it is simply a row nobody has marked.
  const blank = k.jarvisTodayLines(ok({
    date: '2026-09-20', isToday: true, headline: '',
    items: [{ kind: 'build', task: 'A sample unmarked task', status: '', next: '' }],
    lever: null, fileUpdatedAt: new Date(T0 - 7200000).toISOString()
  }), null, 'ok', T0, { items: 3, todayHead: true })
  assert.equal(blank.items[0].mark, '○')
  assert.equal(blank.items[0].raw, '')
})

// §8.4 item 6 + §8 amendment C9 — the spaced spelling a person types. "not
// started" holds the word "started"; it must still read as not-started. A bare
// "started" is not one of the contract's three words, so it is drawn as
// not-started with the raw word shown, never guessed at as in-progress.
test('§8.4 item 6 — "not started" is not-started, and a bare "started" is shown raw', () => {
  const k = kit()
  const card = ok({
    date: '2026-09-20', isToday: true, headline: '',
    items: [
      { kind: 'content', task: 'A sample task nobody has begun', status: 'not started', next: '' },
      { kind: 'content', task: 'A sample task not yet begun', status: 'Not Yet Started', next: '' },
      { kind: 'build', task: 'A sample task under way', status: 'in progress', next: '' },
      { kind: 'build', task: 'A sample task with a loose word', status: 'started', next: '' },
      { kind: 'momentum', task: 'A sample task that shipped', status: 'done', next: '' }
    ],
    lever: null, fileUpdatedAt: new Date(T0 - 7200000).toISOString()
  })
  const lines = k.jarvisTodayLines(card, null, 'ok', T0, { items: 5, todayHead: true })
  assert.deepEqual(lines.items.map(i => i.mark), ['○', '○', '◐', '○', '●'],
    'three distinct marks; nothing holding the word "started" is amber unless it is in-progress')
  assert.deepEqual(lines.items.map(i => i.state), ['', '', 'live', '', 'done'])
  assert.deepEqual(lines.items.map(i => i.raw), ['', 'Not Yet Started', '', 'started', ''],
    'the contract words print nothing extra; the unknown ones are shown as written')
})

test('§8.4 item 7 — OVERNIGHT JOBS: how many ran, what failed, what is next', () => {
  const k = kit()
  const lines = k.jarvisJobsLines(JOBS, T0, { jobs: 2 })
  assert.equal(lines.headline, '23 ok')
  assert.equal(lines.failedWord, '2 failed')
  assert.equal(lines.allGreen, false)
  assert.match(lines.since, /^since \d\d:\d\d$/)
  assert.equal(lines.failed.length, 2)
  assert.equal(lines.failed[0].text, 'Sample nightly sweep')
  assert.equal(lines.failed[0].right, 'error')
  // §8 amendment B.5 — the next run is a LINE of the box, name first, and the
  // header tag is empty while the reading is ok
  assert.match(lines.next, /^next: Sample morning sweep \d\d:\d\d$/)
  assert.equal(lines.tag, undefined, 'the header tag is gone from the reading')

  const tight = k.jarvisJobsLines(JOBS, T0, { jobs: 0 })
  assert.equal(tight.failed.length, 0, 'a one-line box draws no rows')
  assert.equal(tight.more, 2, 'and counts the two it is holding back')
  assert.equal(tight.headline, '23 ok', 'the headline is what survives')

  const green = k.jarvisJobsLines(ok({ window: JOBS.window, total: 9, ok: 9, failed: [], nextUp: [] }), T0)
  assert.equal(green.allGreen, true)
  assert.equal(green.failedWord, '')

  const nothing = k.jarvisJobsLines(ok({ window: JOBS.window, total: 0, ok: 0, failed: [], nextUp: [] }), T0)
  assert.match(nothing.empty, /^nothing ran since \d\d:\d\d$/, 'nothing running is a reading too')

  const dark = k.jarvisJobsLines({ status: 'unreachable', note: 'the cron file is not readable JSON' }, T0)
  assert.equal(dark.status, 'unreachable')
  assert.equal(dark.note, 'the cron file is not readable JSON')
})

test("§8.4 item 8 — SPEND leads with Jarvis's OWN call clock, and never invents a dollar", () => {
  const k = kit()
  const lines = k.jarvisSpendLines(SPEND, VOICE, { models: 2 })
  assert.equal(lines.voice, '23 min · 4 calls')
  assert.equal(lines.voiceNote, 'voice today · measured by Jarvis in this window',
    'the one reading Jarvis measures itself says so on the glass')
  assert.equal(lines.models.length, 2)
  assert.equal(lines.models[0].right, '142 calls · 1M')
  assert.equal(lines.total, '173 calls · 1.1M tokens')
  assert.equal(lines.cost, 'cost not reported by Hermes',
    'a dollar figure Hermes did not report is never printed as one')

  assert.equal(k.jarvisSpendLines(SPEND, { seconds: 41, calls: 1 }).voice, '41 s · 1 call',
    'under a minute reads in seconds, and one call is not "1 calls"')
  assert.equal(k.jarvisSpendLines(SPEND, { seconds: 0, calls: 0 }).voice, '0 s · 0 calls')

  const tight = k.jarvisSpendLines(SPEND, VOICE, { models: 1 })
  assert.equal(tight.models.length, 1)
  assert.equal(tight.more, 1)

  const paid = k.jarvisSpendLines(ok({ today: { byModel: [], totalCalls: 0, totalTokens: 0, costUsd: 12.345, costKnown: true } }), VOICE)
  assert.equal(paid.cost, '$12.35 today', 'a cost Hermes DID report is printed')
  assert.equal(paid.total, 'no model calls recorded today')

  const dark = k.jarvisSpendLines({ status: 'unreachable', note: 'not found: a sample path' }, VOICE)
  assert.equal(dark.status, 'unreachable')
  assert.equal(dark.voice, '23 min · 4 calls',
    "the backend being down cannot erase Jarvis's own measurement")
  assert.deepEqual(dark.models, [])
})

test('§8.4 item 9 — SCOREBOARD: the streak, the marks, and one line when it is old', () => {
  const k = kit()
  const lines = k.jarvisStreakLines(STREAKS, T0, { days: 7 })
  assert.equal(lines.big, '12')
  assert.equal(lines.bigLabel, 'day build streak')
  assert.equal(lines.second, 'content 3 · best 14 · 26 lessons')
  assert.equal(lines.days.length, 3)
  assert.deepEqual(lines.days[0], { label: '19', build: 'yes', content: 'yes' })
  assert.equal(lines.days[1].content, 'no')
  assert.equal(lines.collapsed, false)

  assert.equal(lines.collapsedWhy, '', 'a whole scoreboard collapses for no reason at all')

  const oneLine = k.jarvisStreakLines(STREAKS, T0, { streaksLine: true })
  assert.equal(oneLine.collapsed, true)
  assert.equal(oneLine.line, 'build 12 · content 3 · best 14 · 26 lessons',
    'a short window says the same numbers in one line rather than cutting the marks')

  const stale = k.jarvisStreakLines(ok({ buildStreak: 4, lastDays: [{ date: '2026-07-25', build: true, content: false }] }, { status: 'stale', note: 'not written for 8 weeks' }), T0)
  assert.equal(stale.collapsed, true)
  assert.equal(stale.line, 'not updated since 25 Jul', 'a stale scoreboard is ONE line, and the line says when')

  const unknown = k.jarvisStreakLines(ok({ buildStreak: null, contentStreak: null, lastDays: [] }), T0)
  assert.equal(unknown.big, '—', 'a number the backend did not send prints as a dash, never a zero')

  const dark = k.jarvisStreakLines({ status: 'unreachable', note: 'backend has no one_thing_scoreboard yet' }, T0)
  assert.equal(dark.collapsed, true)
  assert.equal(dark.line, 'backend has no one_thing_scoreboard yet')
})

test('§8 amendments D1 — the one line says WHY it is one line: dead, stale, or short of space', () => {
  const k = kit()

  // the three reasons, named apart
  const space = k.jarvisStreakLines(STREAKS, T0, { streaksLine: true })
  assert.equal(space.collapsedWhy, 'space', 'a short window is a SPACE reason, never a stale one')
  assert.equal(space.status, 'ok')
  assert.notEqual(space.word, 'stale', 'the reading itself is not stale')

  const stale = k.jarvisStreakLines(ok({ buildStreak: 4, lastDays: [{ date: '2026-07-25', build: true, content: false }] }, { status: 'stale', note: 'not written for 8 weeks' }), T0)
  assert.equal(stale.collapsedWhy, 'stale')

  const dead = k.jarvisStreakLines({ status: 'unreachable', note: 'backend has no one_thing_scoreboard yet' }, T0)
  assert.equal(dead.collapsedWhy, 'dead')

  // a stale reading in a short window is still STALE: the older truth wins
  const both = k.jarvisStreakLines(ok({ buildStreak: 4, lastDays: [{ date: '2026-07-25', build: true, content: false }] }, { status: 'stale', note: 'not written for 8 weeks' }), T0, { streaksLine: true })
  assert.equal(both.collapsedWhy, 'stale')

  // and on the glass: the tag follows the reason, not the shape of the box.
  // 900 px is the render the flaw was read off — the box IS in its one line here
  assert.equal(k.jarvisRailCaps(900).streaksLine, true)
  const e = env()
  const rails = openRails(e)
  const score = findByClass(rails.root, 'jv-score')[0]
  assert.ok(score, 'SCOREBOARD is on the left rail')
  const box = score.parentNode
  const tag = findByClass(box, 'jv-box-tag')[0]
  assert.ok(tag, 'the header carries a tag slot')
  assert.equal(tag.textContent, '',
    'a HEALTHY scoreboard in its one-line form is not labelled stale at 1440x900')
  assert.equal(box.classList.contains('jv-dead'), false,
    'and it is not dimmed as a dead reading either')
  rails.overlay.destroy()
})

/* ===================================== §8.4 item 3 — WAITING ON YOU rows == */

test('§8.4 item 3 — a row leads with the brief\'s plain title, the STATE line is the fallback', () => {
  const k = kit()
  const state = k.jarvisStateRows(STATE, T0, { waiting: 4, flight: 5, brief: 3 })
  assert.deepEqual(state.waiting.map(r => r.id), ['demo-switch', 'demo-approve', 'demo-no-brief'],
    'overdue first, then the soonest date, then the row with no date at all')
  assert.equal(state.waiting[0].title, 'Flip one sample switch', "Agent's plain title leads the row")
  assert.equal(state.waiting[2].title, 'Owner picks one of the two sample options',
    'a row with no brief falls back to the STATE line — never to an invented title')
  assert.equal(state.waiting[0].due, 'overdue 2 d')
  assert.deepEqual(state.flight.map(r => r.id), ['demo-redeploy', 'demo-watch'])
  assert.equal(state.header, '5 rows · updated 12 min ago')
})

test('§8.4 item 3 — the first ask is open by default, and only one is ever open', () => {
  const k = kit()
  const first = k.jarvisStateRows(STATE, T0, { waiting: 4, brief: 3 })
  assert.equal(first.openId, 'demo-switch')
  assert.deepEqual(first.waiting.map(r => r.open), [true, false, false])
  assert.deepEqual(first.waiting[0].lines.map(l => l.label), ['what', 'do', 'takes'],
    'three lines is what a person needs to act')
  assert.equal(first.waiting[0].lines[0].text, 'one setting on one sample screen')

  const second = k.jarvisStateRows(STATE, T0, { waiting: 4, brief: 3 }, 'demo-approve')
  assert.equal(second.openId, 'demo-approve')
  assert.deepEqual(second.waiting.map(r => r.open), [false, true, false], 'opening one closes the others')
  assert.deepEqual(second.waiting[0].lines, [], 'and a closed row carries no brief lines at all')

  // a tall window has room for the whole brief
  const tall = k.jarvisStateRows(STATE, T0, { waiting: 4, brief: 5 })
  assert.deepEqual(tall.waiting[0].lines.map(l => l.label), ['what', 'do', 'takes', 'why', 'where'])

  // a row Agent never wrote a brief for says so, in Owner's words
  const none = k.jarvisStateRows(STATE, T0, { waiting: 4, brief: 3 }, 'demo-no-brief')
  assert.deepEqual(none.waiting[2].lines, [{ label: '', text: 'no plain-words brief yet · ask Agent', missing: true }])

  // an id that is not on the glass falls back to the first row rather than
  // leaving every row shut
  const gone = k.jarvisStateRows(STATE, T0, { waiting: 4, brief: 3 }, 'demo-not-here')
  assert.equal(gone.openId, 'demo-switch')
})

test('§8.4 item 3 — jarvisBriefLines keeps the front of the list and never invents a line', () => {
  const k = kit()
  const brief = { title: 't', what: 'the sample what', why: 'the sample why', do: 'the sample do', takes: '2 min', where: 'the sample where' }
  assert.deepEqual(k.jarvisBriefLines(brief, 3).map(l => l.label), ['what', 'do', 'takes'])
  assert.deepEqual(k.jarvisBriefLines(brief, 5).map(l => l.label), ['what', 'do', 'takes', 'why', 'where'])
  assert.deepEqual(k.jarvisBriefLines(brief, 2).map(l => l.label), ['what', 'do'])
  assert.deepEqual(k.jarvisBriefLines(brief, 0), [], 'a cap of 0 draws nothing')
  assert.deepEqual(k.jarvisBriefLines({ title: 't', what: '', do: '', takes: '' }, 3),
    [{ label: '', text: 'no plain-words brief yet · ask Agent', missing: true }],
    'a brief with nothing in it is the same as no brief: say so')
  assert.deepEqual(k.jarvisBriefLines(null, 3),
    [{ label: '', text: 'no plain-words brief yet · ask Agent', missing: true }])
})

test('§8.4 item 3 — jarvisWaitingRows is WAITING ON YOU on its own', () => {
  const k = kit()
  const rows = k.jarvisWaitingRows(STATE, '', T0, { waiting: 2, brief: 3 })
  assert.equal(rows.status, 'ok')
  assert.equal(rows.rows.length, 2)
  assert.equal(rows.more, 1, 'the ask it cannot draw is counted, never dropped silently')
  assert.equal(rows.openId, 'demo-switch')

  const dark = k.jarvisWaitingRows(undefined, '', T0)
  assert.equal(dark.status, 'unreachable')
  assert.deepEqual(dark.rows, [])
})

/* ========================== §8 amendments C10 — the rail scale ============ */

test('§8 amendments C10 — the rails scale with the DISPLAY, by width, in two steps', () => {
  const k = kit()
  const scale = w => k.jarvisRailScale(w)

  assert.equal(scale(1440), 1, "Owner's laptop is the 1x rail the whole look was drawn at")
  assert.equal(scale(1920), 1, 'and so is a 1920 window: it is still a desk away')
  assert.equal(scale(2199), 1, 'the step is AT 2200, not a pixel before it')
  assert.equal(scale(2200), 1.25)
  assert.equal(scale(2560), 1.25, 'a 2560 display reads at 1.25')
  assert.equal(scale(2999), 1.25)
  assert.equal(scale(3000), 1.4)
  assert.equal(scale(3440), 1.4, 'and the wall-sized one at 1.4')
  assert.equal(scale(5120), 1.4, 'there is no third step: 1.4 is the top')

  // a width this window cannot read is the 1x rail, never a guess at a bigger one
  assert.equal(scale(0), 1)
  assert.equal(scale(-100), 1)
  assert.equal(scale('nonsense'), 1)
  assert.equal(scale(undefined), 1)

  // it never goes DOWN as the display gets wider
  let last = 0
  for (let w = 320; w <= 4000; w += 1) {
    const s = scale(w)
    assert.ok(s >= last, `the rail shrank as the display grew, at ${w}`)
    last = s
  }
})

/* ============================================ §8.4 item 10 — the ladder === */

const CAP_KEYS = ['waiting', 'flight', 'rows', 'recent', 'brief', 'helpers', 'helpersDone', 'jobs', 'later', 'items', 'days', 'models', 'chips', 'left']
const FLAG_KEYS = ['streaksLine', 'spendLine', 'jobsLine', 'meetLine']

test('§8.4 item 10 — the ladder is pure, whole-numbered, and never grows as the glass shrinks', () => {
  const k = kit()
  const caps = h => k.jarvisRailCaps(h)

  // the two rails at the four sizes the renders were checked at
  const tall = caps(1440)
  assert.equal(tall.waiting, 4, 'the four asks keep their seats wherever the rail is tall enough')
  assert.equal(tall.flight, 3, '§8 amendments C10: 11 px rows cost two of the five in-flight rows')
  assert.equal(tall.rows, 9)
  assert.equal(tall.brief, 5, 'a 1440 px window has room for why and where as well')
  assert.equal(tall.chips, 6)
  assert.equal(tall.left, 4, 'and all four left-rail boxes')

  const laptop = caps(900)               // Owner's MacBook
  assert.equal(laptop.waiting, 2)
  assert.equal(laptop.brief, 2, 'what / do still fit whole; `takes` is what the 11 px type costs')
  assert.equal(laptop.todayHead, false, "TODAY's headline gives way before any row does")
  assert.equal(laptop.left, 4, 'all four left boxes are still on the glass at 900')
  assert.equal(laptop.streaksLine, true, 'SCOREBOARD goes to its one line here, the first of the three')
  assert.equal(laptop.spendLine, false, 'SPEND keeps its box')
  assert.equal(laptop.jobsLine, false)
  assert.equal(laptop.meetLine, false)

  assert.equal(caps(840).spendLine, true, 'then SPEND, in the §8.4 item 10 order')
  assert.equal(caps(840).jobsLine, true, 'and OVERNIGHT JOBS with it at this height')
  assert.equal(caps(840).left, 4)
  assert.equal(caps(790).left, 3, 'under 840 the left column starts losing whole boxes')
  assert.equal(caps(755).meetLine, true, 'and under 790 the left rail is headlines only')
  assert.equal(caps(755).items, 0)
  assert.equal(caps(755).left, 2)
  assert.equal(caps(720).left, 2, 'two whole boxes stand down and are counted out loud')
  assert.equal(caps(640).left, 1, 'and under 665 only the countdown is left, with +3 more under it')
  assert.equal(caps(640).waiting, 0, 'a box may collapse to its header — never to half a row')

  // whole numbers, monotone down the ladder, and a one-line form never goes
  // BACK to a full box as the window shrinks
  let last = null
  for (let h = 1440; h >= 600; h -= 1) {
    const c = caps(h)
    CAP_KEYS.forEach(key => {
      assert.ok(Number.isInteger(c[key]) && c[key] >= 0, `${key} at ${h} is a whole count: ${c[key]}`)
    })
    if (last) {
      ;['waiting', 'flight', 'rows', 'brief', 'helpers', 'helpersDone', 'jobs', 'later', 'items', 'days', 'models', 'left', 'chips'].forEach(key => {
        assert.ok(c[key] <= last[key], `${key} may not grow as the window shrinks (${h})`)
      })
      FLAG_KEYS.forEach(f => {
        if (last[f] === true) assert.equal(c[f], true, `${f} may not come back as the window shrinks (${h})`)
      })
      if (last.todayHead === false) assert.equal(c.todayHead, false, `todayHead may not come back (${h})`)
    }
    assert.ok(c.rows >= c.waiting, `the shared STATE budget covers the asks at ${h}`)
    assert.ok(c.brief === 0 || c.waiting > 0, `a brief with no row to open it is nonsense (${h})`)
    last = c
  }

  // the history is the one count that may go UP as the window shrinks, and
  // only where the taller rung spends the room on STATE rows instead
  assert.equal(caps(1000).recent, 0)
  assert.equal(caps(1180).recent, 1, 'and it comes back as soon as both fit')

  assert.deepEqual(caps(0), caps(900), 'an unreadable height is treated as the 900 px window')
  assert.deepEqual(caps(-40), caps(900))
  assert.deepEqual(caps('nonsense'), caps(900))
  assert.deepEqual(caps(5000), caps(1440), 'and a wall-sized display is still the top rung')
})

/* ===================== §8 amendments C8 — no cut from 600 px up =========== */

/* The ladder is a STEP function: inside a band every height is handed exactly
 * the same caps, so the tightest point of a band is its FLOOR — the height with
 * the least glass. That is what makes a handful of rendered sizes proof for the
 * whole range: `?measure=cut` was run at 1440x600, x640 and x740 (the sizes §8
 * amendments C8 names), and at every band floor and every 20 px step from 600
 * to 1100 besides, and reported no cut and no part line anywhere.
 *
 * These floors are measured, not chosen. Each one is the shortest window whose
 * two rails still hold that rung's boxes whole at 1440 wide against ?rows=max,
 * with the left rail the binding one under 840 px (it starts 449 px down the
 * glass, under the name, the chips and VOICE CONTROL). */
/* The last entry is the bottom band's floor, not zero: a height of 0 or less
 * is unreadable, and `jarvisRailCaps` answers an unreadable height with the
 * 900 px rung, so 1 px is the shortest window the bottom band really owns. */
const LADDER_FLOORS = [1400, 1180, 1070, 1000, 900, 840, 790, 760, 665, 1]

test('§8 amendments C8 — 600 to 1100 px in 20 px steps: whole rows all the way down', () => {
  const k = kit()
  const caps = h => k.jarvisRailCaps(h)
  const floorOf = h => LADDER_FLOORS.find(f => h >= f)

  // every band floor really is a rung: the caps change there and nowhere else
  for (const floor of LADDER_FLOORS) {
    // the bottom band has no rung under it to differ from
    if (floor === 1) continue
    assert.notDeepEqual(caps(floor), caps(floor - 1),
      `${floor} px is a dead rung: the ladder hands the same caps one pixel below it`)
  }

  let steps = 0
  let last = null
  for (let h = 600; h <= 1100; h += 20) {
    const c = caps(h)
    steps += 1
    // a height inside a band is cut exactly as its floor is — this is why
    // measuring the floor proves every height above it in the same band
    assert.deepEqual(c, caps(floorOf(h)),
      `${h} px is not handed its own band's caps (floor ${floorOf(h)})`)
    // whole rows only: no cap is ever a fraction of a row
    CAP_KEYS.forEach(key => {
      assert.ok(Number.isInteger(c[key]) && c[key] >= 0, `${key} at ${h} is a whole count: ${c[key]}`)
    })
    assert.ok(c.left >= 1 && c.left <= 4, `${h} px: the left rail holds one to four boxes, not ${c.left}`)
    assert.ok(c.rows >= c.waiting, `${h} px: the shared STATE budget covers the asks`)
    if (last) {
      ;['waiting', 'flight', 'rows', 'brief', 'helpers', 'jobs', 'items', 'models', 'left'].forEach(key => {
        assert.ok(c[key] >= last[key], `${key} may not shrink as the window GROWS (${h})`)
      })
      FLAG_KEYS.forEach(f => {
        if (c[f] === true) assert.equal(last[f], true, `${f} may not come back as the window grows (${h})`)
      })
    }
    last = c
  }
  assert.equal(steps, 26, '600 to 1100 in 20 px steps is 26 readings')

  // the bottom of the range: everything stands down as WHOLE boxes and says so
  const floorCaps = caps(600)
  assert.equal(floorCaps.waiting, 0)
  assert.equal(floorCaps.flight, 0)
  assert.equal(floorCaps.helpers, 0)
  assert.equal(floorCaps.left, 1, 'one left box, and the other three counted out loud')
  FLAG_KEYS.forEach(f => assert.equal(floorCaps[f], true, `${f}: every one-line form is in at 600 px`))
  assert.deepEqual(caps(600), caps(640), '600 and 640 are the same band, and both were rendered')
})

/* ================================================= the rails on the glass = */

// The painters read the wall clock, so the fixtures the GLASS is given carry
// stamps around `Date.now()` — the same synthetic rows, told from today.
function railData() {
  const at = Date.now()
  const iso = ms => new Date(at + ms).toISOString()
  return {
    connection: { profile: 'agent', gateway: 'open', model: 'a-sample-model', backend: 'ok' },
    brains: [{ id: 'demo-brain', label: 'Sample brain', status: 'ok' }],
    senses: [{ id: 'demo-sense', status: 'ok' }],
    fleet: [{ id: 'agent', label: 'Agent', busy: true, sessions: 2 }],
    jobs: [{ id: 'demo-job', label: 'a sample job', status: 'running' }],
    lever: null, events: [], panel: null,
    health: { brains: 'ok', senses: 'ok', fleet: 'ok', jobs: 'ok', lever: 'ok' },
    activity: undefined,
    agentState: Object.assign({}, STATE, {
      updatedAt: at - 720000,
      rows: STATE.rows.map((row, i) => Object.assign({}, row, {
        follow_up_at: row.follow_up_at === null ? null : iso(i === 0 ? -172800000 : 7200000 * (i + 1))
      }))
    }),
    agentHelpers: Object.assign({}, HELPERS, {
      running: HELPERS.running.map((row, i) => Object.assign({}, row, { startedAt: iso(i === 0 ? -118000 : -42000) })),
      recent: HELPERS.recent.map((row, i) => Object.assign({}, row, { endedAt: iso(i === 0 ? -360000 : -900000) }))
    }),
    nextMeeting: Object.assign({}, MEETING, {
      next: Object.assign({}, MEETING.next, { start: iso(2520000), end: iso(4320000) }),
      later: MEETING.later.map((row, i) => Object.assign({}, row, { start: iso(100800000 * (i + 1)) }))
    }),
    todayPlan: TODAY,
    overnightJobs: Object.assign({}, JOBS, {
      window: { from: iso(-48000000), to: iso(0) },
      nextUp: [{ name: 'Sample morning sweep', nextRunAt: iso(4200000) }]
    }),
    streaks: Object.assign({}, STREAKS, { fileUpdatedAt: iso(-3600000) }),
    spend: SPEND, voiceToday: VOICE,
    updatedAt: 0
  }
}

const OFF = {
  call: 'off', mode: 'idle', live: '', levels: { voice: 0, mic: 0 }, captions: [],
  source: { status: 'none', voice: 'none', mic: 'none' }, demo: false, updatedAt: 0
}

function openRails(e) {
  const k = loadRails(e)
  const presence = {
    get: () => OFF, subscribe: () => () => {}, isDemo: () => false,
    command: () => Promise.resolve({ ok: true, via: 'bus', reason: '' })
  }
  const overlay = k.createOverlay({
    presence, data: { get: railData, subscribe: () => () => {} }, log: () => {}
  })
  overlay.open()
  const root = e.doc.body.childNodes[e.doc.body.childNodes.length - 1]
  return { overlay, root }
}

/** The header word of every box in a rail, in the order they are drawn. */
function boxNames(rail) {
  return (rail.childNodes || [])
    .map(box => {
      const head = findByClass(box, 'jv-pod-h')[0]
      if (!head) return null
      const span = (head.childNodes || []).find(c => c.tagName === 'SPAN')
      return span ? span.textContent : null
    })
    .filter(Boolean)
}

test('§8.4 item 2 — the two rails are drawn in the order the SPEC sets', () => {
  const e = env()
  const rails = openRails(e)

  const right = findByClass(rails.root, 'jv-right')[0]
  assert.deepEqual(boxNames(right), ['NOW', "AGENT'S HELPERS", 'WAITING ON YOU', 'AGENT IN FLIGHT', 'OVERNIGHT JOBS', 'SYSTEMS'],
    'the right rail, top to bottom')

  const left = findByClass(rails.root, 'jv-left-rail')[0]
  assert.ok(left, 'the left rail exists, under VOICE CONTROL')
  assert.deepEqual(boxNames(left), ['NEXT MEETING', 'TODAY', 'SPEND', 'SCOREBOARD'])

  // ONE LEVER left the rail: it is line 1 of TODAY (§8.4 item 2)
  assert.equal(boxNames(right).includes('ONE LEVER'), false)
  assert.equal(boxNames(left).includes('ONE LEVER'), false)
  assert.equal(findByClass(rails.root, 'jv-lever').length, 1, 'and there is exactly one lever line on the glass')

  // AGENTS AT WORK left the rail too, as FLEET in the diagnostics drawer
  assert.equal(boxNames(right).includes('AGENTS AT WORK'), false)
  assert.equal(boxNames(right).includes('FLEET'), false)
  const drawer = findByClass(rails.root, 'jv-drawer')[0]
  assert.ok(boxNames(drawer).includes('FLEET'), 'FLEET is one chord away, not gone')

  rails.overlay.destroy()
})

test('a box selection counts only selected left-rail boxes', () => {
  const e = env()
  VIEW_H = 720
  const k = loadRails(e)
  const frame = railData()
  frame.settings = {
    schema_version: 1, profile_id: 'sample-agent', agent_name: 'Sample Agent', owner_label: 'Sample Owner',
    timezone: 'UTC', enabled_sources: ['next_meeting', 'today_plan'], brains: [],
    enabled_boxes: ['next_meeting', 'today']
  }
  const presence = { get: () => OFF, subscribe: () => () => {}, isDemo: () => false, command: () => Promise.resolve({ ok: true }) }
  const overlay = k.createOverlay({ presence, data: { get: () => frame, subscribe: () => () => {} }, log: () => {} })
  overlay.open()
  const root = e.doc.body.childNodes[e.doc.body.childNodes.length - 1]
  const left = findByClass(root, 'jv-left-rail')[0]
  const directMore = left.childNodes.find(n => String(n.className || '').split(' ').includes('jv-more'))
  assert.equal(directMore.textContent, '', 'disabled boxes are not counted as hidden overflow')
  assert.notEqual(left.childNodes[0].style.display, 'none')
  assert.notEqual(left.childNodes[1].style.display, 'none')
  assert.equal(left.childNodes[2].style.display, 'none')
  assert.equal(left.childNodes[3].style.display, 'none')
  overlay.destroy()
  VIEW_H = 900
})

test('§8.4 item 3 — WAITING ON YOU rows are real buttons a keyboard can open', () => {
  const e = env()
  const rails = openRails(e)

  const first = findByAttr(rails.root, 'data-jv', 'row-demo-switch')
  const second = findByAttr(rails.root, 'data-jv', 'row-demo-approve')
  assert.ok(first && second, 'every ask is tagged with its own id')
  assert.equal(first.tagName, 'BUTTON', 'a row is a button, so the tab key reaches it')
  assert.equal(first.getAttribute('aria-expanded'), 'true', 'the first ask is open when Owner looks up')
  assert.equal(second.getAttribute('aria-expanded'), 'false')
  assert.ok(findByClass(first, 'jv-brief').length === 1, 'and the open one shows the plain words')
  assert.equal(findByClass(second, 'jv-brief').length, 0)

  // a click opens that one, closes the other, and hands the caret straight back
  // to the host composer (§8.4 item 3)
  second.dispatch('click', { preventDefault() {}, stopPropagation() {} })
  const afterClick = findByAttr(rails.root, 'data-jv', 'row-demo-approve')
  assert.equal(afterClick.getAttribute('aria-expanded'), 'true')
  assert.equal(findByAttr(rails.root, 'data-jv', 'row-demo-switch').getAttribute('aria-expanded'), 'false')
  assert.ok(second.blurred >= 1, 'the row lets go of the focus it took')

  // Enter and Space do the same, and nothing else does
  let prevented = 0
  findByAttr(rails.root, 'data-jv', 'row-demo-switch')
    .dispatch('keydown', { code: 'Enter', key: 'Enter', preventDefault() { prevented += 1 }, stopPropagation() {} })
  assert.equal(findByAttr(rails.root, 'data-jv', 'row-demo-switch').getAttribute('aria-expanded'), 'true',
    'Enter opens the row under the caret')
  assert.equal(prevented, 1)

  findByAttr(rails.root, 'data-jv', 'row-demo-approve')
    .dispatch('keydown', { code: 'Space', key: ' ', preventDefault() {}, stopPropagation() {} })
  assert.equal(findByAttr(rails.root, 'data-jv', 'row-demo-approve').getAttribute('aria-expanded'), 'true',
    'and so does Space')
  assert.equal(findByAttr(rails.root, 'data-jv', 'row-demo-switch').getAttribute('aria-expanded'), 'false')

  // the third ask does not fit this window: it is counted, never dropped
  assert.equal(findByAttr(rails.root, 'data-jv', 'row-demo-no-brief'), null)
  assert.ok(says(findByClass(rails.root, 'jv-waiting')[0], '+1 more'),
    'and the box says out loud what it is holding back')

  // the chords the overlay owns (⌃⌥ + a letter) must still reach the window
  const shut = findByAttr(rails.root, 'data-jv', 'row-demo-switch')
  let chordPrevented = 0
  shut.dispatch('keydown', { code: 'KeyD', key: 'd', ctrlKey: true, altKey: true, preventDefault() { chordPrevented += 1 }, stopPropagation() {} })
  shut.dispatch('keydown', { code: 'Enter', key: 'Enter', ctrlKey: true, altKey: true, preventDefault() { chordPrevented += 1 }, stopPropagation() {} })
  assert.equal(chordPrevented, 0, 'a row never swallows a chord')
  assert.equal(findByAttr(rails.root, 'data-jv', 'row-demo-switch').getAttribute('aria-expanded'), 'false',
    'and a chord never opens a row by accident')

  rails.overlay.destroy()
})

test('§8.4 items 4–9 — every new box paints its live reading', () => {
  const e = env()
  // Every box at once needs a window with room for every box. At 900 px the
  // ladder stands AGENT IN FLIGHT down WHOLE and counts it in "+n more"
  // (§8 amendments C8) — that is the ladder's job, proven by the sweep above,
  // not this test's. This one asks what each box PRINTS when it is drawn.
  VIEW_H = 1200
  const rails = openRails(e)

  const helpers = findByClass(rails.root, 'jv-hrows')[0]
  assert.ok(says(helpers, /Read the sample folder/), "AGENT'S HELPERS")
  assert.ok(says(helpers, /a-sample-model · \d+:\d\d/), 'with the model and how long it has been up')
  assert.ok(textsOf(rails.root, 'jv-srow-t').some(t => t === 'Flip one sample switch'),
    'WAITING ON YOU leads with the brief title')
  assert.ok(says(findByClass(rails.root, 'jv-brief')[0], /one setting on one sample screen/), 'with its brief open')
  assert.ok(textsOf(rails.root, 'jv-srow-t').some(t => /redeploy the sample service/.test(t)), 'AGENT IN FLIGHT')
  const jobsBox = findByClass(rails.root, 'jv-jobs')[0]
  assert.ok(says(jobsBox, '23 ok'), 'OVERNIGHT JOBS')
  // §8 amendment B.5 — the next run is the LAST line of the box, not the header
  const jobsNext = findByClass(jobsBox, 'jv-jobnext')[0]
  assert.ok(jobsNext, 'the next run has a line of its own')
  assert.match(jobsNext.textContent, /^next: Sample morning sweep \d\d:\d\d$/)
  assert.strictEqual(jobsBox.childNodes[jobsBox.childNodes.length - 1], jobsNext,
    'and it is the last thing in the box')
  const jobsHead = findByClass(jobsBox.parentNode || rails.root, 'jv-box-tag')
    .filter(t => /next/i.test(t.textContent))
  assert.equal(jobsHead.length, 0, 'nothing about the next run is left in a header tag')

  const left = findByClass(rails.root, 'jv-left-rail')[0]
  assert.ok(says(findByClass(left, 'jv-meet')[0], 'in 42 min'), 'NEXT MEETING')
  assert.ok(says(findByClass(left, 'jv-lever')[0], /Ship the sample lever/), 'TODAY leads with the ONE lever')
  assert.ok(says(findByClass(left, 'jv-trows')[0], /Finish the sample rail/), "and today's contract")
  assert.ok(says(findByClass(left, 'jv-spend')[0], '23 min · 4 calls'), 'SPEND')
  assert.ok(says(findByClass(left, 'jv-score')[0], '12'), 'SCOREBOARD')
  assert.ok(findByClass(left, 'jv-day').length >= 3, 'with a mark for each day it knows')

  rails.overlay.destroy()
  VIEW_H = 900
})

test('§8.4 item 1 — a backend too old for a block says which reading is missing', () => {
  const e = env()
  const k = loadRails(e)
  const dark = {}
  const names = { agentHelpers: 'agent_helpers', nextMeeting: 'next_meeting', todayPlan: 'today_plan', overnightJobs: 'overnight_jobs', streaks: 'one_thing_scoreboard', spend: 'spend' }
  Object.keys(names).forEach(key => { dark[key] = { status: 'unreachable', note: 'backend has no ' + names[key] + ' yet', updatedAt: null, source: '', stale: false } })
  const presence = { get: () => OFF, subscribe: () => () => {}, isDemo: () => false, command: () => Promise.resolve({ ok: true }) }
  const overlay = k.createOverlay({
    presence, data: { get: () => Object.assign(railData(), dark), subscribe: () => () => {} }, log: () => {}
  })
  overlay.open()
  const root = e.doc.body.childNodes[e.doc.body.childNodes.length - 1]

  const left = findByClass(root, 'jv-left-rail')[0]
  const box = cls => findByClass(root, cls)[0]

  assert.ok(says(findByClass(root, 'jv-hrows')[0], 'backend has no agent_helpers yet'))
  assert.ok(says(box('jv-jobs'), 'backend has no overnight_jobs yet'))
  assert.ok(says(box('jv-meet'), 'backend has no next_meeting yet'))
  assert.ok(says(box('jv-today'), 'backend has no today_plan yet'))
  assert.ok(says(box('jv-spend'), 'backend has no spend yet'))
  assert.ok(says(box('jv-score'), 'backend has no one_thing_scoreboard yet'))

  // and no box prints a number it never read
  assert.ok(says(box('jv-meet'), 'unreachable'), 'NEXT MEETING says the word instead of a countdown')
  assert.equal(says(box('jv-meet'), /^in \d+ min$/), false)
  assert.equal(says(box('jv-score'), '12'), false, 'no streak is printed at all')
  assert.equal(says(box('jv-today'), /Finish the sample rail/), false)
  // …except the one Jarvis measured itself, which the backend cannot take away
  assert.ok(says(box('jv-spend'), '23 min · 4 calls'))
  assert.ok(left, 'the left rail is still drawn')

  overlay.destroy()
})

/* ======================= §8 amendments D2 — the rails follow the scale ==== */
//
// The rail type is supposed to grow with the display: every size on the two
// rails is calc(Npx * var(--jv-rail-k, 1)). One rule had slipped out of that
// (a plain 11 px on the open WAITING ON YOU row's title), and at 2560 the
// title read SMALLER than the id line under it. These checks walk the real
// CSS, cascade and all, so the next one cannot slip out quietly.

/** Every style rule in JARVIS_CSS that sets a font-size, in source order,
 *  comments stripped and the @media / @supports rungs flattened in. */
function fontSizeRules(css) {
  const out = []
  const walk = text => {
    let i = 0
    while (i < text.length) {
      const open = text.indexOf('{', i)
      if (open < 0) return
      const head = text.slice(i, open).trim()
      let depth = 1
      let j = open + 1
      while (j < text.length && depth > 0) {
        if (text[j] === '{') depth += 1
        else if (text[j] === '}') depth -= 1
        j += 1
      }
      const body = text.slice(open + 1, j - 1)
      if (head.startsWith('@')) {
        if (/^@(media|supports)/.test(head)) walk(body)   // @keyframes is not a rule list
      } else if (head) {
        let size = null
        const re = /(?:^|[;{\s])font-size\s*:\s*([^;}]+)/g
        let hit
        while ((hit = re.exec(body))) size = hit[1].trim()
        if (size !== null) {
          head.split(',').forEach(sel => {
            if (sel.trim()) out.push({ selector: sel.trim().replace(/\s+/g, ' '), size, order: out.length })
          })
        }
      }
      i = j
    }
  }
  walk(String(css).replace(/\/\*[\s\S]*?\*\//g, ''))
  return out
}

/** CSS specificity, one number. :not() does not count; its argument does. */
function specificity(selector) {
  const sel = selector.replace(/:not\(([^)]*)\)/g, ' $1 ')
  const ids = (sel.match(/#[\w-]+/g) || []).length
  const classes = (sel.match(/\.[\w-]+|\[[^\]]+\]|:[\w-]+/g) || []).length
  const tags = (sel.replace(/\.[\w-]+|\[[^\]]+\]|::?[\w-]+/g, ' ').match(/[a-zA-Z][\w-]*/g) || []).length
  return ids * 10000 + classes * 100 + tags
}

function classesOf(node) {
  const set = new Set()
  if (typeof node.className === 'string') node.className.split(/\s+/).filter(Boolean).forEach(c => set.add(c))
  if (node.classList && node.classList._s) node.classList._s.forEach(c => set.add(c))
  return set
}

/** One compound (`button.jv-srow`, `.jv-day em`, `.jv-live:not(.jv-vbtn)`)
 *  against one node. A state pseudo it cannot judge (:hover, :first-child) is
 *  READ AS MATCHING on purpose: a size hidden behind a state still has to
 *  follow the scale, so the conservative answer is the honest one here. */
function compoundMatches(text, node) {
  const negatives = []
  const body = text.replace(/:not\(([^)]*)\)/g, (m, inner) => { negatives.push(inner); return '' })
    .replace(/::?[\w-]+/g, '')
  const own = classesOf(node)
  const tag = body.replace(/\.[\w-]+/g, '').trim()
  if (tag && tag !== '*' && tag.toUpperCase() !== String(node.tagName || '').toUpperCase()) return false
  const wanted = (body.match(/\.[\w-]+/g) || []).map(c => c.slice(1))
  if (!wanted.every(c => own.has(c))) return false
  return !negatives.some(n => {
    const no = (n.match(/\.[\w-]+/g) || []).map(c => c.slice(1))
    return no.length > 0 && no.every(c => own.has(c))
  })
}

/** Does `selector` match `node`? Descendant and child combinators only, which
 *  is all this sheet uses. */
function selectorMatches(selector, node) {
  const parts = []
  let child = false
  selector.replace(/\s*>\s*/g, ' > ').split(/\s+/).filter(Boolean).forEach(tok => {
    if (tok === '>') { child = true; return }
    parts.push({ text: tok, child })
    child = false
  })
  const step = (idx, target) => {
    if (idx < 0) return true
    if (!target) return false
    if (idx === parts.length - 1) {
      return compoundMatches(parts[idx].text, target) && step(idx - 1, target.parentNode)
    }
    let cur = target
    while (cur) {
      if (compoundMatches(parts[idx].text, cur) && step(idx - 1, cur.parentNode)) return true
      if (parts[idx + 1].child) return false
      cur = cur.parentNode
    }
    return false
  }
  return step(parts.length - 1, node)
}

/** The font-size declaration that actually wins on `node` — specificity, then
 *  source order, exactly as a browser decides it. */
function winningSize(node, rules) {
  let best = null
  rules.forEach(rule => {
    if (!selectorMatches(rule.selector, node)) return
    const spec = specificity(rule.selector)
    if (!best || spec > best.spec || (spec === best.spec && rule.order > best.order)) {
      best = { spec, order: rule.order, size: rule.size, selector: rule.selector }
    }
  })
  return best
}

/** What this node is actually drawn at: its own winning size, or the nearest
 *  ancestor's, since font-size inherits. */
function effectiveSize(node, rules) {
  let cur = node
  while (cur) {
    const win = winningSize(cur, rules)
    if (win) return Object.assign({ from: cur }, win)
    cur = cur.parentNode
  }
  return null
}

/** A declaration in real pixels at this rail scale. */
function pixelsAt(size, k) {
  const scaled = /^calc\(\s*([\d.]+)px\s*\*\s*var\(\s*--jv-rail-k[^)]*\)\s*\)$/.exec(size)
  if (scaled) return Number(scaled[1]) * k
  const plain = /^([\d.]+)px$/.exec(size)
  return plain ? Number(plain[1]) : null
}

/** Every node under `root` that carries words of its own. */
function textNodes(node, out = []) {
  if (!node) return out
  if (typeof node.textContent === 'string' && node.textContent.trim()) out.push(node)
  ;(node.childNodes || []).forEach(kid => textNodes(kid, out))
  return out
}

const namesOf = node => [String(node.tagName || '').toLowerCase()].concat([...classesOf(node)]).join('.')

test('§8 amendments D2 — every font-size the rail CSS sets is expressed through --jv-rail-k', () => {
  const k = kit()
  const rules = fontSizeRules(k.JARVIS_CSS)
  assert.ok(rules.length > 40, 'the walker found the sheet')

  const railScoped = rules.filter(r => /(^|\s)\.jv-(right|left-rail)(\s|\.)/.test(r.selector))
  assert.ok(railScoped.length > 20, 'and the rail block inside it')
  railScoped.forEach(rule => {
    assert.match(rule.size, /var\(\s*--jv-rail-k/,
      `${rule.selector} sets ${rule.size}, which does not follow the rail scale`)
  })
})

test('§8 amendments D2 — every text node on both rails is drawn at the rail scale', () => {
  const rules = fontSizeRules(kit().JARVIS_CSS)
  const off = []

  // two heights: the ladder draws different rungs, so between them the walk
  // sees the boxes whole AND the one-line forms
  ;[1200, 900].forEach(height => {
    const e = env()
    VIEW_H = height
    const rails = openRails(e)
    try {
      ;['jv-right', 'jv-left-rail'].forEach(railClass => {
        const rail = findByClass(rails.root, railClass)[0]
        assert.ok(rail, `${railClass} is on the glass`)
        textNodes(rail).forEach(node => {
          const win = effectiveSize(node, rules)
          if (!win) { off.push(`${height}: ${namesOf(node)} is drawn at no size at all`); return }
          if (!/var\(\s*--jv-rail-k/.test(win.size)) {
            off.push(`${height}: ${namesOf(node)} ("${String(node.textContent).slice(0, 24)}") `
              + `is drawn at ${win.size} by "${win.selector}"`)
          }
        })
      })
    } finally {
      rails.overlay.destroy()
      VIEW_H = 900
    }
  })

  assert.deepEqual(off, [], 'these rail readings do not follow the rail scale:\n' + off.join('\n'))
})

test('§8 amendments D2 — a WAITING ON YOU row title is the largest text in its row, at every size', () => {
  const rules = fontSizeRules(kit().JARVIS_CSS)
  const e = env()
  VIEW_H = 1200
  const rails = openRails(e)
  const wrong = []
  try {
    const rows = findByClass(rails.root, 'jv-srow')
    assert.ok(rows.length >= 2, 'the fixture draws the open row and at least one closed one')
    assert.ok(rows.some(r => classesOf(r).has('jv-open')), 'one of them is open, with its brief under it')

    ;[1, 1.25, 1.4].forEach(scale => {
      rows.forEach(row => {
        const title = findByClass(row, 'jv-srow-t')[0]
        assert.ok(title, 'every row leads with a title')
        const titleSize = pixelsAt(effectiveSize(title, rules).size, scale)
        assert.ok(titleSize !== null, 'the title size is a plain number of pixels')
        textNodes(row).forEach(node => {
          if (node === title) return
          const size = pixelsAt(effectiveSize(node, rules).size, scale)
          if (size === null) { wrong.push(`${namesOf(node)}: ${effectiveSize(node, rules).size} is not a size this test can read`); return }
          if (!(titleSize > size)) {
            wrong.push(`k=${scale}: the title (${titleSize} px) is not bigger than ${namesOf(node)} (${size} px)`)
          }
        })
      })
    })
  } finally {
    rails.overlay.destroy()
    VIEW_H = 900
  }

  assert.deepEqual(wrong, [], 'the row title is not the biggest thing in its row:\n' + wrong.join('\n'))
})
