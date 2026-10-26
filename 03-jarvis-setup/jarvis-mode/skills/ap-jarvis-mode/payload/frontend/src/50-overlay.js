// hermes-jarvis — file 50: the OVERLAY (SPEC §5 row A1).
//
//   createOverlay({ ctx, presence, data, createScene, HermesSDK, log })
//     -> { open(), close(), toggle(), isOpen(), destroy(), showPanel(panel) }
//
// Vanilla DOM on purpose: runtime plugins get React but NOT react-dom, so the
// only way to own a full-window surface is to build it by hand and append it to
// document.body. React is used elsewhere (title bar, statusbar, palette) where
// the host renders for us.
//
// The canvas belongs to 40-scene.js through the §4.3 contract and nothing else;
// if that file has not landed yet a local stub draws a circle labelled
// "SCENE STUB" so the shell is still testable.
//
// Look v1.1 (SPEC §3b) adds three pieces of chrome, all of them honest:
//   * a status-chip row top-left — ONLINE / VOICE / BRAINS / MIC, every word
//     read off the presence + data stores, coral when something is down;
//   * a mini radar whose blips ARE the live session count (capped at 6, and
//     "no signal" when the gateway has not answered yet);
//   * an ambient telemetry strip driven by a plain timer and labelled
//     "motion, not metrics" out loud — it must never read the voice, because
//     only Agent reacts to voice (SPEC §0 law 1).
//
// Voice controls (SPEC §4.6, Owner 2026-09-18: "the overlay has no voice
// control. I can't start or stop the talk"): three buttons under Agent and the
// keys T / M / Z. Every label is read off the presence snapshot, never off what
// we just asked for; a press shows "starting…" until the BUS reports, and if it
// never does the VOICE pod says so in Owner's words instead of pretending.
//
// Jarvis mode v2 (SPEC §7) added the right rail Owner asked for, with today's
// instrument pods folded into a diagnostics drawer (⌃⌥D) so no reading is lost
// — plus the two window keys: W opens Jarvis mode in its own Hermes window
// (another display) and F takes it full screen.
//
// v3 (SPEC §8.4) makes it TWO rails. RIGHT, Agent's work: NOW · AGENT'S HELPERS ·
// WAITING ON YOU · AGENT IN FLIGHT · OVERNIGHT JOBS · SYSTEMS. LEFT, under VOICE
// CONTROL, Owner's day: NEXT MEETING · TODAY · SPEND · SCOREBOARD. ONE LEVER
// is line 1 of TODAY now and AGENTS AT WORK is FLEET in the drawer — both moved
// to pay for the new boxes, and neither reading was dropped.
//
// Every reader below this line is PURE: it takes the data slice and a clock and
// returns strings. The feed (30-data.js, another package) may not have landed
// yet, so a missing slice reads `source:'none'` / `status:'unreachable'` and the
// box says that out loud instead of drawing an empty frame.

// ---- time words -----------------------------------------------------------

/** 4 s · 1 m 40 s · 1 h 2 m — the way a person says a duration out loud. */
function jarvisSpan(ms) {
  const raw = Math.max(0, Number(ms) || 0)
  // under a second, round to a tenth: a step that took 420 ms took 0.4 s, not
  // "0 s" — a reading that reads as nothing at all
  if (raw > 0 && raw < 1000) return (Math.round(raw / 100) / 10) + ' s'
  const total = Math.max(0, Math.round(raw) / 1000)
  const s = Math.floor(total)
  if (s < 60) return s + ' s'
  const m = Math.floor(s / 60)
  if (m < 60) {
    const rest = s % 60
    return rest ? m + ' m ' + rest + ' s' : m + ' m'
  }
  const h = Math.floor(m / 60)
  const rm = m % 60
  return rm ? h + ' h ' + rm + ' m' : h + ' h'
}

/** The coarse word a due date wants: 2 d, 3 h, 14 m — never '2 d 3 h 9 m'. */
function jarvisCoarse(ms) {
  const s = Math.max(0, Math.round((Number(ms) || 0) / 1000))
  if (s >= 86400) return Math.round(s / 86400) + ' d'
  if (s >= 3600) return Math.round(s / 3600) + ' h'
  return Math.max(1, Math.round(s / 60)) + ' m'
}

/** just now · 6 min ago · 3 h ago · 2 d ago. */
function jarvisAgo(at, now) {
  const stamp = Number(at) || 0
  if (!stamp) return ''
  const ms = Math.max(0, (Number(now) || 0) - stamp)
  if (ms < 45000) return 'just now'
  const min = Math.round(ms / 60000)
  if (min < 60) return min + ' min ago'
  const h = Math.round(min / 60)
  if (h < 24) return h + ' h ago'
  return Math.round(h / 24) + ' d ago'
}

/** Configured wall-clock parts of a stamp. Until a verified settings frame
 *  arrives the overlay uses UTC, so it never borrows the computer's locale or
 *  another profile's day. */
function jarvisZonedParts(at, timezone) {
  const date = new Date(Number(at) || 0)
  const zone = String(timezone || 'UTC')
  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: zone, hourCycle: 'h23',
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    }).formatToParts(date)
    const bag = {}
    for (let i = 0; i < parts.length; i += 1) bag[parts[i].type] = parts[i].value
    return {
      day: String(Number(bag.day)) + ' ' + JARVIS_MONTHS[Math.max(0, Math.min(11, Number(bag.month) - 1))],
      key: bag.year + '-' + bag.month + '-' + bag.day,
      time: bag.hour + ':' + bag.minute
    }
  } catch (err) {
    const pad = function (n) { return (n < 10 ? '0' : '') + n }
    return {
      day: pad(date.getUTCDate()) + ' ' + JARVIS_MONTHS[date.getUTCMonth()],
      key: date.getUTCFullYear() + '-' + pad(date.getUTCMonth() + 1) + '-' + pad(date.getUTCDate()),
      time: pad(date.getUTCHours()) + ':' + pad(date.getUTCMinutes())
    }
  }
}

/** The next calendar date after a zoned YYYY-MM-DD key. Calendar arithmetic
 *  avoids the 23/25-hour mistake that adding 24 hours makes at DST changes. */
function jarvisNextDayKey(key) {
  const found = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(key || ''))
  if (!found) return ''
  const next = new Date(Date.UTC(Number(found[1]), Number(found[2]) - 1, Number(found[3]) + 1))
  const pad = function (n) { return (n < 10 ? '0' : '') + n }
  return next.getUTCFullYear() + '-' + pad(next.getUTCMonth() + 1) + '-' + pad(next.getUTCDate())
}

/** HH:MM:SS plus the engine's short name for the configured timezone. */
function jarvisClockReadout(at, timezone) {
  const date = new Date(Number(at) || 0)
  const zone = String(timezone || 'UTC')
  try {
    const parts = new Intl.DateTimeFormat('en-GB', {
      timeZone: zone, hourCycle: 'h23', hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short'
    }).formatToParts(date)
    const bag = {}
    for (let i = 0; i < parts.length; i += 1) bag[parts[i].type] = parts[i].value
    return bag.hour + ':' + bag.minute + ':' + bag.second + ' ' + (bag.timeZoneName || zone)
  } catch (err) {
    const pad = function (n) { return (n < 10 ? '0' : '') + n }
    return pad(date.getUTCHours()) + ':' + pad(date.getUTCMinutes()) + ':' + pad(date.getUTCSeconds()) + ' UTC'
  }
}

/** A `follow_up_at` as a stamp, or null when it is missing or unparseable. */
function jarvisStamp(value) {
  if (typeof value !== 'string' || !value.trim()) return null
  const at = Date.parse(value.trim())
  return isFinite(at) ? at : null
}

// ---- the NOW box (SPEC §7.3 ruling 5) -------------------------------------

const JARVIS_QUIET_WARM_MS = 60000     // past a minute of silence the line warms
const JARVIS_QUIET_HOT_MS = 180000     // past three minutes it goes coral
const JARVIS_UNDER_ORB_MS = 8000       // a turn this long earns the line under Agent
const JARVIS_RECENT_ROWS = 4
const JARVIS_CHIP_CAP = 6

/** What the NOW box says, as plain strings. `activity` is 30-data.js's slice
 *  (§7.3) and may be undefined while that package is still landing: that reads
 *  `source:'none'`, which is the honest "nothing has been seen here yet". */
function jarvisNowLines(activity, now, caps, labels) {
  const a = activity && typeof activity === 'object' ? activity : null
  const at = Number(now) || 0
  // §7 amendment 5 — the recent list is NOW's give-way, and it gives way in
  // whole rows: a short window is handed fewer of them rather than the box
  // clipping the coral block that sits under them. No cap = the §7.3 four.
  const recentCap = caps && isFinite(Number(caps.recent)) && Number(caps.recent) >= 0
    ? Math.floor(Number(caps.recent)) : JARVIS_RECENT_ROWS
  // §8.4 item 4 — the helper chips are the SECOND thing NOW gives up (after the
  // history): AGENT'S HELPERS carries the same sub-agents, tagged `in this turn`,
  // so a short window loses no reading by dropping them here.
  const chipCap = caps && isFinite(Number(caps.chips)) && Number(caps.chips) >= 0
    ? Math.floor(Number(caps.chips)) : JARVIS_CHIP_CAP
  const out = {
    tag: '', line: 'quiet', detail: '', meta: '', metaState: '',
    thought: '', chips: [], recent: [], needsYou: '',
    running: false, elapsed: 0, quietFor: 0, underOrb: ''
  }
  const source = a && typeof a.source === 'string' ? a.source : 'none'
  if (!a || source === 'none') {
    out.meta = 'no work seen yet in this window'
    return out
  }
  if (a.focused === false) out.tag = 'another chat'
  out.needsYou = jarvisNeedsYou(a.needsYou, labels)

  const running = a.running === true
  out.running = running
  const started = Number(a.startedAt) || 0
  const lastEvent = Number(a.lastEventAt) || 0

  if (!running) {
    const last = a.lastTurn && typeof a.lastTurn === 'object' ? a.lastTurn : null
    if (last) {
      const outcome = String(last.outcome || 'done')
      const verb = outcome === 'interrupted' ? 'was interrupted after'
        : outcome === 'error' ? 'stopped with an error after'
          : 'took'
      const bits = ['last job ' + verb + ' ' + jarvisSpan((Number(last.seconds) || 0) * 1000)]
      const steps = Number(last.steps) || 0
      if (steps) bits.push(steps + ' steps')
      const ago = jarvisAgo(Number(last.endedAt) || 0, at)
      if (ago) bits.push(ago)
      out.meta = bits.join(', ')
    } else {
      out.meta = source === 'host-busy'
        ? 'Hermes said busy, then went quiet'
        : 'nothing has finished in this window yet'
    }
    return out
  }

  // A running turn. Every number below is a subtraction of two clocks; nothing
  // here decides whether Agent is "stuck" (§7.3 ruling 3) — it prints the facts.
  const tool = a.tool && typeof a.tool === 'object' ? a.tool : null
  const saying = typeof a.saying === 'string' ? a.saying.trim() : ''
  out.line = tool && tool.label ? String(tool.label)
    : saying ? 'speaking'
      : source === 'host-busy' ? 'busy'
        : 'thinking'
  out.detail = tool && tool.detail ? String(tool.detail)
    : saying ? saying
      : source === 'host-busy' ? 'Hermes says a turn is running · no step detail reached this window'
        : ''

  out.elapsed = started ? Math.max(0, at - started) : 0
  // No lastEventAt yet (an older feed, or a turn whose first event IS the
  // start) — then the turn's own start is the last news there was.
  const since = lastEvent || started
  out.quietFor = since ? Math.max(0, at - since) : 0
  const bits = []
  const steps = Number(a.steps) || 0
  if (steps > 0) bits.push('step ' + steps)
  if (started) bits.push(jarvisSpan(out.elapsed))
  if (since) bits.push('no news for ' + jarvisSpan(out.quietFor))
  out.meta = bits.join(' · ')
  out.metaState = out.quietFor >= JARVIS_QUIET_HOT_MS ? 'hot'
    : out.quietFor >= JARVIS_QUIET_WARM_MS ? 'warm' : ''

  out.thought = typeof a.thought === 'string' ? a.thought.trim() : ''
  const subs = Array.isArray(a.subagents) ? a.subagents.slice(0, chipCap) : []
  out.chips = subs.map(function (s) {
    const row = s && typeof s === 'object' ? s : {}
    const status = String(row.status || 'running')
    const label = String(row.label || row.id || 'helper')
    return { label: label + (status === 'running' ? '' : ' · ' + status), status: status }
  })
  const recent = Array.isArray(a.recent) ? a.recent.slice(0, recentCap) : []
  out.recent = recent.map(function (r) {
    const row = r && typeof r === 'object' ? r : {}
    const text = String(row.label || 'step') + (row.detail ? ' · ' + String(row.detail) : '')
    return { text: text, right: row.ms ? jarvisSpan(row.ms) : '', ok: row.ok !== false }
  })
  if (out.elapsed > JARVIS_UNDER_ORB_MS) out.underOrb = out.line + ' · ' + jarvisSpan(out.elapsed)
  return out
}

/** The one coral block (§7.3 ruling 5). An approval asks for a yes; a clarify
 *  asks a question — saying "a yes" to a question would be a small lie. */
function jarvisNeedsYou(needsYou, labels) {
  const n = needsYou && typeof needsYou === 'object' ? needsYou : null
  if (!n) return ''
  const text = String(n.text || '').trim()
  const agent = labels && labels.agent_name ? String(labels.agent_name) : 'Agent'
  const head = String(n.kind || 'approval') === 'clarify' ? agent + ' needs an answer' : agent + ' needs a yes'
  return text ? head + ' · ' + text : head
}

// ---- Agent's STATE rows (SPEC §7.4 + the §7.5 contract) --------------------

const JARVIS_WAITING_ROWS = 4
const JARVIS_FLIGHT_ROWS = 5
const JARVIS_ROW_CHARS = 110

/** SPEC §8 amendments C10 — HOW BIG THE RAILS ARE ON THIS DISPLAY.
 *
 *  PURE, and the whole of the rule: viewport WIDTH in, one multiplier out. It
 *  is set on the overlay root as the CSS custom property --jv-rail-k by
 *  measure(), where 10-theme.js multiplies every rail width and every rail
 *  type size by it; 40-scene.js reads the same width through the same two
 *  thresholds so its rail-column keep-out grows with the glass.
 *
 *  Owner reads these rails across a room on a second display: at 2560 and
 *  3440 px a 300 px column of 11 px type is a column of 11 px type seen from
 *  twice as far away. The thresholds are the displays themselves — 2200 px
 *  clears every 1920-wide window, 3000 px clears every 2560-wide one — not a
 *  ratio of anything, because a window is not always the screen it is on.
 *  Height is NOT in this: a short window is the ladder's business. */
function jarvisRailScale(width) {
  const w = Number(width) > 0 ? Number(width) : 0
  if (w >= 3000) return 1.4
  if (w >= 2200) return 1.25
  return 1
}

/** SPEC §7 amendment 5 + §8.4 item 10 — how much of BOTH rails this window is
 *  tall enough for.
 *
 *  PURE, so the rule can be pinned without a browser: height in, row caps out.
 *  The right rail is `height − 82` px of glass (top 26, bottom 56) and holds six
 *  boxes; the left rail is what is left under VOICE CONTROL and holds four.
 *  Every number below was measured off `?measure=1` / `?measure=cut` against the
 *  `rows=max` fixture of tests/overlay-preview.html at 1440 wide — never guessed:
 *
 *      clock row 44 · NOW 150 (no history) – 250 (four rows) · HELPERS 72
 *      OVERNIGHT JOBS 52 (collapsed) – 96 · SYSTEMS 60 · gaps 6 × 5 = 30
 *      a WAITING row ≈ 45 (two lines), ≈ 106 with its brief open
 *      a FLIGHT row ≈ 25 (one line, ellipsised)
 *      a collapsed box — header + `+n more`, no rows — costs 50
 *      LEFT: NEXT MEETING 86 · TODAY 96 · SPEND 84 · SCOREBOARD 80
 *
 *  A row is never half-drawn: the boxes do not shrink (10-theme.js), so the
 *  only thing a short window can take away is a whole row, and what it took is
 *  always counted out loud in `+n more`. `rows` is the two boxes' shared
 *  budget — WAITING ON YOU is served first because it is the one Owner has to
 *  act on, and AGENT IN FLIGHT takes what is left. */
function jarvisRailCaps(height) {
  const h = Number(height) > 0 ? Number(height) : 900
  const rung = function (waiting, flight, rows, recent, extra) {
    return Object.assign({
      waiting: waiting, flight: flight, rows: rows, recent: recent,
      // §8.4 — the v3 boxes. `brief` is how many lines the OPEN waiting row
      // may print (3 = what/do/takes, 5 = + why/where); `*Line` is a box in
      // its one-line form; a cap of 0 is a box holding everything back and
      // saying so with "+n more".
      brief: 3, helpers: 2, helpersDone: 1, jobs: 2, later: 1, items: 3,
      days: 7, models: 2, todayHead: true, chips: 0, left: 4,
      streaksLine: false, spendLine: false, jobsLine: false, meetLine: false
    }, extra || {})
  }
  // The RIGHT rail at 1440×900 is 818 px of glass and holds seven boxes now:
  // clock row 44 · NOW 150–250 · AGENT'S HELPERS 72 · WAITING ON YOU 106 (one
  // row with its brief open) + 44 a row · AGENT IN FLIGHT 50 + 25 a row ·
  // OVERNIGHT JOBS 52 (collapsed) – 96 · SYSTEMS 60 · six 5 px gaps.
  // The LEFT rail is the same glass under VOICE CONTROL: NEXT MEETING 86 ·
  // TODAY 96 · SPEND 84 · SCOREBOARD 80, above the 56 px mode word and the
  // captions. Every number was measured off ?measure=1 / ?measure=cut at the
  // four sizes in §8.4 item 10, never guessed.
  // Every rung below was re-measured at 1440 wide against ?rows=max — the
  // worst case there is — after §8 amendments C10 raised every reading on both
  // rails to 11 px. Bigger type is taller boxes, so several rungs hand back a
  // row they used to afford; every one of them is counted out loud in
  // "+n more" (amendment B.1: the literal row counts give way to the no-cut
  // law, and §8 amendments C8 extends that law down to 600 px).
  //
  // The two rails are measured separately, because they start in different
  // places. The RIGHT one is h - 82 px of glass for seven boxes; the LEFT one
  // is h - 449, because the name, the chips and VOICE CONTROL stand above it,
  // so it runs out first and sheds whole BOXES of its own (`left`) in the
  // §8.4 item 10 order once its one-line forms are spent. Measured costs at
  // 1440 wide, 11 px type: chrome row 44 · SYSTEMS 68 · six gaps 24 · NOW 141
  // (no thought) / 160 (one line) / 174 (two) · a box holding everything back
  // 55 · a WAITING row 43, its open brief 29 a line · a FLIGHT row 32 · a
  // running helper 31 · OVERNIGHT JOBS 59 (one line) / 131 (one failed named)
  // / 144 · LEFT: NEXT MEETING 75-92 · TODAY 107-120 · SPEND 82-139 ·
  // SCOREBOARD 48-96.
  //
  // 1400 px of window and up (2560x1440 and 3440x1440 reach this rung through
  // their own scale, height / k). The four asks keep their seats AND the open
  // brief keeps `why` and `where` — this is the one rung §8.4 item 3 says the
  // ladder allows them. DEVIATION from the §7.4 literal maxima, ruled the same
  // way as §7.1.1 and amendment B.1: eleven-pixel type (C10) is a taller row
  // and the no-cut gate wins over a literal count. What pays for the two extra
  // brief lines is AGENT IN FLIGHT — this rail's declared give-way — at three
  // rows instead of five, the third running helper, and three of the four
  // steps of NOW history, which the ticker carries anyway. Every one of them
  // is counted out loud in "+n more".
  if (h >= 1400) return rung(JARVIS_WAITING_ROWS, 3, 9, 1, { brief: 5, helpers: 2, helpersDone: 1, jobs: 3, later: 2, models: 3, chips: JARVIS_CHIP_CAP })
  // 1180-1400: three asks with their brief open, three in flight, one step of
  // history — and the finished helpers stand down, because a helper that has
  // already answered is the least urgent row on the rail.
  if (h >= 1180) return rung(3, 3, 6, 1, { brief: 3, helpers: 2, helpersDone: 0, jobs: 3, later: 2, models: 3 })
  // 1080 px (1920x1080). DEVIATION from the §7.4 amendment, and the same
  // ruling as §7.1.1: the no-cut gate wins. Seven boxes with an OPEN brief in
  // WAITING ON YOU do not leave room for nine STATE rows at this height.
  if (h >= 1070) return rung(3, 2, 4, 0, { brief: 3, helpers: 2, helpersDone: 0, jobs: 2, later: 2, models: 3 })
  // 1000-1069: the second failed job is what the last two pixels cost — it is
  // counted out loud, and its name is one line down in the drawer's log.
  if (h >= 1000) return rung(2, 2, 4, 0, { brief: 3, helpers: 1, helpersDone: 0, jobs: 1, later: 1, models: 2 })
  // 900 px — Owner's laptop, and the last rung that keeps all four left
  // boxes. What pays for the bigger type here is the second running helper,
  // every in-flight row, the brief's `takes` line, the meeting's later lines,
  // the second spend model and SCOREBOARD's week, which goes to its one-line
  // form here rather than below 900 (§8.4 item 10 order, one rung earlier:
  // eleven-pixel type is a taller box). Never half a row of any of them, and
  // all of it counted out loud.
  if (h >= 900) return rung(2, 0, 3, 0, { brief: 2, helpers: 1, helpersDone: 0, jobs: 1, later: 0, models: 1, days: 0, todayHead: false, streaksLine: true })
  // Below 900 the one-line forms come in, in the §8.4 item 10 order:
  // SCOREBOARD first, then SPEND, then OVERNIGHT JOBS.
  if (h >= 840) return rung(2, 0, 3, 0, { brief: 2, helpers: 1, helpersDone: 0, jobs: 0, later: 0, models: 0, days: 0, todayHead: false, streaksLine: true, spendLine: true, jobsLine: true })
  // Under 840 px the left column is down to three boxes and the right one to
  // the two asks themselves: the brief keeps `what`, which is the line that
  // says what the ask IS.
  if (h >= 790) return rung(2, 0, 2, 0, { brief: 1, helpers: 0, helpersDone: 0, jobs: 0, later: 0, items: 3, days: 0, models: 0, left: 3, todayHead: false, streaksLine: true, spendLine: true, jobsLine: true })
  // Under 790 px the LEFT rail goes to headlines: the countdown, the ONE lever,
  // the call clock and the streak line, each whole, with everything they are
  // holding back counted out loud.
  if (h >= 760) return rung(1, 0, 1, 0, { brief: 1, helpers: 0, helpersDone: 0, jobs: 0, later: 0, items: 0, days: 0, models: 0, left: 3, todayHead: false, streaksLine: true, spendLine: true, jobsLine: true, meetLine: true })
  // Under 760 px the brief closes: one ask, named, with its id and its due
  // date, is worth more than half an explanation of it.
  if (h >= 665) return rung(1, 0, 1, 0, { brief: 0, helpers: 0, helpersDone: 0, jobs: 0, later: 0, items: 0, days: 0, models: 0, left: 2, todayHead: false, streaksLine: true, spendLine: true, jobsLine: true, meetLine: true })
  // Under 665 px even two headlines will not fit the left column, so the last
  // boxes stand down as WHOLE boxes and both rails count them out loud — the
  // same law as a row, one size up. This is the floor of §8 amendments C8:
  // 600 px still cuts nothing.
  return rung(0, 0, 0, 0, { brief: 0, helpers: 0, helpersDone: 0, jobs: 0, later: 0, items: 0, days: 0, models: 0, left: 1, todayHead: false, streaksLine: true, spendLine: true, jobsLine: true, meetLine: true })
}

/** §8.4 item 3 — WAITING ON YOU on its own, for a test (and for a reader) that
 *  only cares about the asks with Owner's name on them. */
function jarvisWaitingRows(agentState, openId, now, caps, timezone) {
  const state = jarvisStateRows(agentState, now, caps, openId, timezone)
  return {
    status: state.status, note: state.note, rows: state.waiting,
    more: state.waitingMore, openId: state.openId
  }
}

/** WAITING ON YOU and AGENT IN FLIGHT, from `data.agentState`. A missing slice
 *  (the feed has not landed, or the backend is offline) is `unreachable` —
 *  never rows without an age stamp.
 *
 *  `caps` is how many rows each box has ROOM for in this window (§7.4: the rail
 *  fits 900 px without scrolling). Whatever is left over is counted in
 *  `+n more`, so a short window hides rows out loud instead of clipping them. */
/** SPEC §8.4 item 3 — the plain words inside an OPEN waiting row.
 *
 *  `what`, `do` and `takes` are the three a person needs to act; `why` and
 *  `where` join them when the height ladder has room. A row Agent has not
 *  written a brief for says exactly that — it never gets invented words. */
function jarvisBriefLines(brief, cap) {
  const room = isFinite(Number(cap)) ? Math.max(0, Math.floor(Number(cap))) : 3
  const b = brief && typeof brief === 'object' ? brief : null
  const out = []
  if (!room) return out
  // the order is the order a person needs them in, so a short window keeps the
  // front of the list: what it is, what to do, how long it takes
  const keys = room >= 5 ? ['what', 'do', 'takes', 'why', 'where'] : ['what', 'do', 'takes']
  if (b) {
    for (let i = 0; i < keys.length && out.length < room; i += 1) {
      const text = b[keys[i]]
      if (typeof text === 'string' && text.trim()) out.push({ label: keys[i], text: text.trim(), missing: false })
    }
  }
  if (!out.length) out.push({ label: '', text: 'no plain-words brief yet · ask Agent', missing: true })
  return out
}

function jarvisStateRows(agentState, now, caps, openId, timezone) {
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  // a cap of 0 is a reading, not a missing value: the box collapses to its
  // header and `+n more` (§7 amendment 5). Only an absent cap takes the maximum.
  const capOf = function (value, fallback) {
    const n = Number(value)
    return isFinite(n) && n >= 0 ? Math.floor(n) : fallback
  }
  const waitingCap = capOf(roomFor.waiting, JARVIS_WAITING_ROWS)
  const flightCap = capOf(roomFor.flight, JARVIS_FLIGHT_ROWS)
  const s = agentState && typeof agentState === 'object' ? agentState : null
  const at = Number(now) || 0
  const out = {
    status: 'unreachable', waiting: [], waitingMore: 0, flight: [], flightMore: 0,
    header: '', openId: '', note: s && typeof s.note === 'string' ? s.note : ''
  }
  if (!s || s.status !== 'ok' || !Array.isArray(s.rows)) return out
  out.status = 'ok'

  const waiting = []
  const flight = []
  for (let i = 0; i < s.rows.length; i += 1) {
    const raw = s.rows[i] && typeof s.rows[i] === 'object' ? s.rows[i] : null
    if (!raw) continue
    const stamp = jarvisStamp(raw.follow_up_at)
    const overdue = stamp !== null ? stamp < at : raw.overdue === true
    const brief = raw.brief && typeof raw.brief === 'object' ? raw.brief : null
    const text = String(raw.next || '').slice(0, JARVIS_ROW_CHARS)
    const row = {
      id: String(raw.id || ''),
      text: text,
      // §8.4 item 3 — the row LEADS with Agent's plain title; his STATE line (a
      // pointer, not an explanation) is the fallback and never a guess
      title: brief && brief.title ? String(brief.title).slice(0, JARVIS_ROW_CHARS) : text,
      brief: brief,
      due: jarvisDueWord(stamp, overdue, at, timezone),
      overdue: overdue,
      at: stamp,
      open: false,
      lines: []
    }
    if (raw.waiting_on_owner === true) waiting.push(row)
    else flight.push(row)
  }
  // soonest first; a row with no date sits behind every dated one
  waiting.sort(function (x, y) {
    if (x.at === null && y.at === null) return 0
    if (x.at === null) return 1
    if (y.at === null) return -1
    return x.at - y.at
  })
  out.waitingMore = Math.max(0, waiting.length - waitingCap)
  out.waiting = waiting.slice(0, waitingCap)
  out.flightMore = Math.max(0, flight.length - flightCap)
  out.flight = flight.slice(0, flightCap)

  // §8.4 item 3 — ONE row is open, and by default it is the first one: the ask
  // Owner is most likely to act on is already explained when he looks up.
  // Clicking another row opens that one and closes this one.
  const wanted = String(openId || '')
  let open = -1
  for (let i = 0; i < out.waiting.length; i += 1) { if (out.waiting[i].id === wanted) { open = i; break } }
  if (open < 0 && out.waiting.length) open = 0
  if (open >= 0) {
    const row = out.waiting[open]
    row.open = true
    row.lines = jarvisBriefLines(row.brief, roomFor.brief)
  }
  out.openId = open >= 0 ? out.waiting[open].id : ''

  const age = jarvisAgo(Number(s.updatedAt) || 0, at)
  out.header = s.rows.length + (s.rows.length === 1 ? ' row' : ' rows') + (age ? ' · updated ' + age : '')
  return out
}

function jarvisDueWord(stamp, overdue, now, timezone) {
  if (stamp === null) return 'no date'
  if (overdue) return 'overdue ' + jarvisCoarse((Number(now) || 0) - stamp)
  const then = jarvisZonedParts(stamp, timezone)
  const today = jarvisZonedParts(now, timezone)
  const tomorrowKey = jarvisNextDayKey(today.key)
  if (then.key === today.key) return 'due today ' + then.time
  if (then.key === tomorrowKey) return 'due tomorrow ' + then.time
  return 'due ' + then.day + ' ' + then.time
}

// ---- the v3 boxes (SPEC §8.4) ---------------------------------------------
//
// Owner, 2026-09-19: "I don't really understand most of this off my memory so
// I will ask Agent, and each time agent would have to check." Every reader below
// turns one backend block (§8.3) into the words a person reads at a glance: one
// big thing, then the detail, then what is being held back. They are PURE —
// block in, strings out — so the words can be pinned without a browser, and
// they never invent a reading: a block that is missing says which reading is
// missing, out loud.

const JARVIS_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const JARVIS_MEETING_WARM_MIN = 15     // amber inside a quarter of an hour
const JARVIS_MEETING_HOT_MIN = 5       // coral inside five minutes, or while it runs

/** 1:54 · 12:03 · 1:02:03 — a running clock, the way a stopwatch reads. */
function jarvisClock(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0))
  const pad = function (n) { return (n < 10 ? '0' : '') + n }
  const s = total % 60
  const m = Math.floor(total / 60) % 60
  const h = Math.floor(total / 3600)
  return h ? h + ':' + pad(m) + ':' + pad(s) : m + ':' + pad(s)
}

/** 940 · 4.2k · 1.3M — token counts a person can hold in their head. */
function jarvisCount(value) {
  const n = Math.max(0, Math.round(Number(value) || 0))
  if (n < 1000) return String(n)
  if (n < 1000000) {
    const k = n / 1000
    return (k < 10 ? Math.round(k * 10) / 10 : Math.round(k)) + 'k'
  }
  const m = n / 1000000
  return (m < 10 ? Math.round(m * 10) / 10 : Math.round(m)) + 'M'
}

/** A plain `YYYY-MM-DD` as `17 Sep`. Parsed from its own digits, never through
 *  a timezone: a date with no time in it has no zone to be shifted by. */
function jarvisDateWord(text) {
  const found = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(text || '').trim())
  if (!found) return String(text || '')
  const month = JARVIS_MONTHS[Math.max(0, Math.min(11, Number(found[2]) - 1))]
  return String(Number(found[3])) + ' ' + month
}

/** The countdown a meeting box leads with (§8.4 item 5).
 *
 *  `now` while it is running or has started, `in 42 min` inside the hour,
 *  `in 3 h` later today, `tomorrow 10:30`, then `21 Sep 10:30`. */
function jarvisCountdown(start, end, now, timezone) {
  const at = Number(now) || 0
  const from = jarvisStamp(start)
  const to = jarvisStamp(end)
  const out = { big: '', range: '', state: '', minutes: null, running: false, ok: false }
  if (from === null) return out
  out.ok = true
  out.minutes = Math.round((from - at) / 60000)
  out.running = to !== null ? (from <= at && at < to) : from <= at
  const then = jarvisZonedParts(from, timezone)
  out.range = to !== null ? then.time + '–' + jarvisZonedParts(to, timezone).time : then.time
  if (from <= at) {
    out.big = 'now'
  } else if (out.minutes < 60) {
    out.big = 'in ' + Math.max(1, out.minutes) + ' min'
  } else {
    const today = jarvisZonedParts(at, timezone)
    const tomorrowKey = jarvisNextDayKey(today.key)
    if (then.key === today.key) out.big = 'in ' + Math.round(out.minutes / 60) + ' h'
    else if (then.key === tomorrowKey) out.big = 'tomorrow ' + then.time
    else out.big = then.day + ' ' + then.time
  }
  out.state = out.running || (out.minutes !== null && out.minutes >= 0 && out.minutes < JARVIS_MEETING_HOT_MIN)
    ? 'hot'
    : (out.minutes !== null && out.minutes >= 0 && out.minutes < JARVIS_MEETING_WARM_MIN ? 'warm' : '')
  return out
}

/** Is this block a reading, and what does it say when it is not?
 *
 *  `missing` is not `unreachable` and neither is `stale` (§8.3): the box prints
 *  the backend's own word and its own reason, never a shrug. */
function jarvisBlockWord(block) {
  const b = block && typeof block === 'object' ? block : null
  const note = b && typeof b.note === 'string' ? b.note : ''
  if (!b) return { ok: false, word: 'unreachable', note: '', stale: false }
  const status = String(b.status || '')
  if (status === 'ok') return { ok: true, word: '', note: b.stale === true ? note : '', stale: b.stale === true }
  if (status === 'stale') return { ok: true, word: 'stale', note: note, stale: true }
  return { ok: false, word: status || 'unreachable', note: note, stale: b.stale === true }
}

/** NEXT MEETING (§8.4 item 5). */
function jarvisMeetingLines(nextMeeting, now, caps, timezone) {
  const at = Number(now) || 0
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  const laterCap = isFinite(Number(roomFor.later)) ? Math.max(0, Math.floor(Number(roomFor.later))) : 2
  const read = jarvisBlockWord(nextMeeting)
  const out = {
    status: read.ok ? 'ok' : 'unreachable', word: read.word, note: read.note,
    stale: read.stale === true,
    big: '', state: '', title: '', range: '', calendar: '', later: [], empty: ''
  }
  if (!read.ok) return out
  const block = nextMeeting || {}
  const next = block.next && typeof block.next === 'object' ? block.next : null
  if (!next) {
    out.empty = 'none in the next ' + (Number(block.windowHours) || 36) + ' h'
    return out
  }
  const count = jarvisCountdown(next.start, next.end, at, timezone)
  out.big = count.big || 'all day'
  out.state = count.state
  out.title = String(next.title || '(untitled)')
  out.range = next.allDay ? 'all day' : count.range
  out.calendar = String(next.calendar || '')
  const later = Array.isArray(block.later) ? block.later.slice(0, laterCap) : []
  out.later = later.map(function (row) {
    const when = jarvisCountdown(row.start, row.end, at, timezone)
    return {
      text: String(row.title || '(untitled)'),
      right: row.allDay ? 'all day' : (when.big || '')
    }
  })
  return out
}

/** AGENT'S HELPERS (§8.4 item 4) — the background helpers the window never sees
 *  as events, plus the in-turn sub-agents the v2 reducer does see. */
function jarvisHelperRows(agentHelpers, activity, now, caps) {
  const at = Number(now) || 0
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  const runCap = isFinite(Number(roomFor.helpers)) ? Math.max(0, Math.floor(Number(roomFor.helpers))) : 3
  const doneCap = isFinite(Number(roomFor.helpersDone)) ? Math.max(0, Math.floor(Number(roomFor.helpersDone))) : 2
  const read = jarvisBlockWord(agentHelpers)
  const out = {
    status: read.ok ? 'ok' : 'unreachable', word: read.word, note: read.note,
    header: 'NONE RUNNING', rows: [], more: 0, empty: '', running: 0
  }
  const block = agentHelpers && typeof agentHelpers === 'object' ? agentHelpers : {}
  const backendRunning = read.ok && Array.isArray(block.running) ? block.running : []
  const backendDone = read.ok && Array.isArray(block.recent) ? block.recent : []

  // the live half: sub-agents of the turn in THIS window (§7.3), tagged as such
  // so a helper Agent spawned in the chat is never confused with one the mini
  // has been running since before this window opened
  const a = activity && typeof activity === 'object' ? activity : null
  const subs = a && Array.isArray(a.subagents) ? a.subagents : []
  const live = subs.filter(function (s) { return s && s.status === 'running' })
  const liveDone = subs.filter(function (s) { return s && s.status !== 'running' })

  out.running = backendRunning.length + live.length
  out.header = out.running ? out.running + ' RUNNING' : 'NONE RUNNING'

  const rows = []
  for (let i = 0; i < backendRunning.length; i += 1) {
    const row = backendRunning[i] || {}
    const started = jarvisStamp(row.startedAt)
    const seconds = started !== null ? Math.max(0, Math.round((at - started) / 1000)) : Number(row.seconds) || 0
    const bits = []
    if (row.model) bits.push(String(row.model))
    bits.push(jarvisClock(seconds))
    rows.push({
      text: String(row.goal || '(no goal written)'),
      meta: bits.join(' · '),
      sub: '',
      tag: String(row.origin || ''),
      state: 'running'
    })
  }
  for (let i = 0; i < live.length; i += 1) {
    const row = live[i] || {}
    rows.push({
      text: String(row.label || row.id || 'helper'),
      meta: row.tool ? String(row.tool) : '',
      sub: '',
      tag: 'in this turn',
      state: 'running'
    })
  }
  const runningShown = rows.slice(0, runCap)
  out.more = Math.max(0, rows.length - runningShown.length)

  const done = []
  for (let i = 0; i < backendDone.length; i += 1) {
    const row = backendDone[i] || {}
    const ended = jarvisStamp(row.endedAt)
    const bits = []
    const ago = ended !== null ? jarvisAgo(ended, at) : ''
    bits.push(ago ? 'done ' + ago : 'done')
    if (Number(row.seconds) > 0) bits.push(jarvisSpan(Number(row.seconds) * 1000))
    const state = String(row.state || '').toLowerCase()
    done.push({
      text: String(row.goal || '(no goal written)'),
      meta: bits.join(' · '),
      sub: String(row.summary || ''),
      tag: String(row.origin || ''),
      state: state === 'completed' || state === 'complete' || state === 'done' || state === 'ok' ? 'done' : 'failed'
    })
  }
  for (let i = 0; i < liveDone.length && done.length < doneCap; i += 1) {
    const row = liveDone[i] || {}
    done.push({
      text: String(row.label || row.id || 'helper'),
      meta: 'done in this turn',
      sub: '',
      tag: 'in this turn',
      state: row.status === 'failed' ? 'failed' : 'done'
    })
  }
  const doneShown = done.slice(0, doneCap)
  out.more += Math.max(0, done.length - doneShown.length)
  out.rows = runningShown.concat(doneShown)
  if (read.ok && !out.rows.length && !out.more) out.empty = 'no helpers in the last 24 h'
  return out
}

/** TODAY (§8.4 item 6) — the ONE lever first, then today's contract. */
function jarvisTodayLines(todayPlan, lever, leverHealth, now, caps) {
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  const itemCap = isFinite(Number(roomFor.items)) ? Math.max(0, Math.floor(Number(roomFor.items))) : 3
  const read = jarvisBlockWord(todayPlan)
  const block = todayPlan && typeof todayPlan === 'object' ? todayPlan : {}
  const out = {
    status: read.ok ? 'ok' : 'unreachable', word: read.word, note: read.note,
    tag: '', tagState: '', lever: '', leverNote: '', headline: '', items: [], more: 0, empty: ''
  }

  // §8.4 item 2 — ONE LEVER is no longer a box of its own; it is line 1 here.
  // The v1 reading (`data.lever`) is the same sentence the backend folds into
  // today_plan, so either one answers; neither one is ever invented.
  const planLever = block.lever && typeof block.lever === 'object' ? block.lever : null
  if (lever && lever.text) {
    out.lever = String(lever.text)
    out.leverNote = String(lever.source || '')
  } else if (planLever && planLever.text) {
    out.lever = String(planLever.text)
    out.leverNote = String(planLever.source || '')
  } else {
    out.lever = leverHealth === 'unreachable' ? 'unreachable' : 'no lever set'
    out.leverNote = leverHealth === 'unreachable' ? 'backend /state' : ''
  }

  if (!read.ok) return out
  // reported, never hidden: a card set two days ago says which day it is for
  if (block.isToday !== true) {
    out.tag = block.date ? 'SET ' + jarvisDateWord(block.date).toUpperCase() + ' · NOT TODAY' : 'NO DATE SET'
    out.tagState = 'warn'
  }
  // the headline is the first thing a short window gives up: the ONE lever
  // line above it already says today's one thing, in Owner's own words
  out.headline = roomFor.todayHead === false ? '' : String(block.headline || '')
  const items = Array.isArray(block.items) ? block.items : []
  const shown = items.slice(0, itemCap)
  out.more = Math.max(0, items.length - shown.length)
  out.items = shown.map(function (row) {
    // §8 amendment C9 — EXACT match, never a substring. The old test asked
    // whether the status CONTAINED "started", and `not-started` contains it:
    // a task nobody had begun was drawn with the amber in-progress mark. The
    // three words the contract uses are matched whole, case-insensitively,
    // with `_` or a space read as a hyphen. Anything else is drawn as
    // not-started AND prints the raw word beside the task, so a status this
    // plugin does not know is visible rather than silently guessed at.
    const raw = String(row.status === null || row.status === undefined ? '' : row.status).trim()
    const status = raw.toLowerCase().replace(/[\s_]+/g, '-')
    const done = status === 'done'
    const live = status === 'in-progress'
    const known = done || live || status === 'not-started' || status === ''
    return {
      kind: String(row.kind || '').toUpperCase(),
      task: String(row.task || row.next || '(nothing written)'),
      mark: done ? '●' : live ? '◐' : '○',
      state: done ? 'done' : live ? 'live' : '',
      raw: known ? '' : raw
    }
  })
  if (!items.length && !String(block.headline || '')) out.empty = 'no contract written for today'
  return out
}

/** OVERNIGHT JOBS (§8.4 item 7) — what ran while he slept. */
function jarvisJobsLines(overnightJobs, now, caps, timezone) {
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  const failCap = isFinite(Number(roomFor.jobs)) ? Math.max(0, Math.floor(Number(roomFor.jobs))) : 3
  const read = jarvisBlockWord(overnightJobs)
  const block = overnightJobs && typeof overnightJobs === 'object' ? overnightJobs : {}
  const out = {
    status: read.ok ? 'ok' : 'unreachable', word: read.word, note: read.note,
    headline: '', failedWord: '', since: '', next: '', failed: [], more: 0,
    allGreen: false, empty: ''
  }
  if (!read.ok) return out
  const window = block.window && typeof block.window === 'object' ? block.window : {}
  const from = jarvisStamp(window.from)
  out.since = from !== null ? 'since ' + jarvisZonedParts(from, timezone).time : 'since 21:00'
  const total = Number(block.total) || 0
  const ok = Number(block.ok) || 0
  const failed = Array.isArray(block.failed) ? block.failed : []
  if (!total) {
    out.allGreen = true
    out.empty = 'nothing ran ' + out.since
  } else {
    out.headline = ok + ' ok'
    out.failedWord = failed.length ? failed.length + ' failed' : ''
    out.allGreen = failed.length === 0
  }
  const shown = failed.slice(0, failCap)
  out.more = Math.max(0, failed.length - shown.length)
  out.failed = shown.map(function (row) {
    return {
      text: String(row.name || row.id || 'a job'),
      right: String(row.lastStatus || 'failed'),
      sub: String(row.error || '')
    }
  })
  // §8 amendment B.5 — the next run is a LINE OF THE BOX, never the header tag:
  // in the header it was truncated to "NEXT 02:35 SAMPLE MORNING S…" and told
  // Owner nothing. The name comes first, because that is what he reads.
  const nextUp = Array.isArray(block.nextUp) ? block.nextUp : []
  if (nextUp.length) {
    const when = jarvisStamp(nextUp[0].nextRunAt)
    const name = String(nextUp[0].name || 'a job')
    out.next = 'next: ' + name + (when !== null ? ' ' + jarvisZonedParts(when, timezone).time : '')
  }
  return out
}

/** SPEND (§8.4 item 8) — Jarvis's own call clock first, then the models. */
function jarvisSpendLines(spend, voiceToday, caps) {
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  const modelCap = isFinite(Number(roomFor.models)) ? Math.max(0, Math.floor(Number(roomFor.models))) : 3
  const read = jarvisBlockWord(spend)
  const block = spend && typeof spend === 'object' ? spend : {}
  const today = block.today && typeof block.today === 'object' ? block.today : {}
  const voice = voiceToday && typeof voiceToday === 'object' ? voiceToday : { seconds: 0, calls: 0 }
  const seconds = Math.max(0, Number(voice.seconds) || 0)
  const calls = Math.max(0, Number(voice.calls) || 0)
  const out = {
    status: read.ok ? 'ok' : 'unreachable', word: read.word, note: read.note,
    // measured by Jarvis in THIS window — said out loud, because it is not a
    // billing figure and it is not the backend's
    voice: (seconds >= 60 ? Math.round(seconds / 60) + ' min' : seconds + ' s') +
      ' · ' + calls + (calls === 1 ? ' call' : ' calls'),
    voiceNote: 'voice today · measured by Jarvis in this window',
    models: [], more: 0, total: '', cost: ''
  }
  if (!read.ok) return out
  const models = Array.isArray(today.byModel) ? today.byModel : []
  const shown = models.slice(0, modelCap)
  out.more = Math.max(0, models.length - shown.length)
  out.models = shown.map(function (row) {
    const tokens = (Number(row.inputTokens) || 0) + (Number(row.outputTokens) || 0)
    return {
      text: String(row.model || 'unknown'),
      right: (Number(row.calls) || 0) + ' calls · ' + jarvisCount(tokens)
    }
  })
  out.total = models.length
    ? (Number(today.totalCalls) || 0) + ' calls · ' + jarvisCount(today.totalTokens) + ' tokens'
    : 'no model calls recorded today'
  // a dollar figure Hermes did not report is never printed as one
  out.cost = today.costKnown === true && today.costUsd !== null && today.costUsd !== undefined
    ? '$' + (Math.round(Number(today.costUsd) * 100) / 100).toFixed(2) + ' today'
    : 'cost not reported by Hermes'
  return out
}

/** SCOREBOARD (§8.4 item 9) — the streaks, and one line when they are old.
 *  §8 amendments D1 — the one-line form has THREE different reasons and they
 *  do not mean the same thing to Owner: the reading is unreachable (`dead`),
 *  the reading is old (`stale`), or the window is short and the same healthy
 *  numbers are said in one line to save the space (`space`). `collapsedWhy`
 *  names which one it is, so the header can tag the stale reading and leave a
 *  healthy scoreboard unlabelled. `collapsed` stays the yes/no it always was. */
function jarvisStreakLines(streaks, now, caps, timezone) {
  const roomFor = caps && typeof caps === 'object' ? caps : {}
  const dayCap = isFinite(Number(roomFor.days)) ? Math.max(0, Math.floor(Number(roomFor.days))) : 7
  const oneLine = roomFor.streaksLine === true
  const read = jarvisBlockWord(streaks)
  const block = streaks && typeof streaks === 'object' ? streaks : {}
  const days = Array.isArray(block.lastDays) ? block.lastDays : []
  const out = {
    status: read.ok ? 'ok' : 'unreachable', word: read.word, note: read.note,
    collapsed: false, collapsedWhy: '', line: '', big: '—', bigLabel: 'day build streak', second: '', days: []
  }
  if (!read.ok) {
    out.collapsed = true
    out.collapsedWhy = 'dead'
    out.line = read.note || 'not read'
    return out
  }
  const newest = days.length ? String(days[0].date || '') : ''
  const stale = read.word === 'stale' || read.stale === true
  if (stale) {
    // §8.4 item 9 — a stale scoreboard is ONE line, and the line says when
    out.collapsed = true
    out.collapsedWhy = 'stale'
    const wrote = jarvisStamp(block.fileUpdatedAt)
    out.line = newest ? 'not updated since ' + jarvisDateWord(newest)
      : (wrote !== null ? 'not updated since ' + jarvisZonedParts(wrote, timezone).day : 'not updated')
    return out
  }
  const build = block.buildStreak
  const content = block.contentStreak
  out.big = build === null || build === undefined ? '—' : String(build)
  const bits = []
  if (content !== null && content !== undefined) bits.push('content ' + content)
  if (block.bestBuildStreak !== null && block.bestBuildStreak !== undefined) bits.push('best ' + block.bestBuildStreak)
  if (block.lessonsShipped !== null && block.lessonsShipped !== undefined) bits.push(block.lessonsShipped + ' lessons')
  out.second = bits.join(' · ')
  if (oneLine) {
    // a short window, not an old reading: the same healthy numbers, one line
    out.collapsed = true
    out.collapsedWhy = 'space'
    out.line = 'build ' + out.big + (out.second ? ' · ' + out.second : '')
    return out
  }
  out.days = days.slice(0, dayCap).map(function (row) {
    const found = /^\d{4}-\d{2}-(\d{2})/.exec(String(row.date || ''))
    return {
      label: found ? String(Number(found[1])) : String(row.date || ''),
      build: row.build === true ? 'yes' : row.build === false ? 'no' : 'unknown',
      content: row.content === true ? 'yes' : row.content === false ? 'no' : 'unknown'
    }
  })
  return out
}

// ---- AGENTS AT WORK (SPEC §7.4: today's JOBS + FLEET, merged) -------------

function jarvisAgentLines(data) {
  const d = data && typeof data === 'object' ? data : {}
  const health = d.health || {}
  const out = { status: 'ok', busy: [], jobs: [], idle: '' }
  if (health.fleet === 'unreachable' && health.jobs === 'unreachable') {
    out.status = 'unreachable'
    return out
  }
  const fleet = Array.isArray(d.fleet) ? d.fleet : []
  const jobs = Array.isArray(d.jobs) ? d.jobs : []
  out.busy = fleet.filter(function (f) { return f && f.busy }).map(function (f) {
    return String(f.label || f.id || 'agent')
  })
  out.jobs = jobs.slice(0, 3).map(function (j) {
    return { label: String(j.label || 'session'), status: String(j.status || 'running') }
  })
  if (health.fleet !== 'unreachable' && fleet.length) {
    out.idle = (fleet.length - out.busy.length) + ' of ' + fleet.length + ' agents idle'
  } else if (health.fleet === 'unreachable') {
    out.idle = 'profiles unreachable'
  } else {
    out.idle = 'no agents read yet'
  }
  if (health.jobs === 'unreachable') out.jobs = []
  return out
}

// ---- SYSTEMS (SPEC §7.4: the same readings the drawer's pods show) --------

function jarvisSystemDots(data, presence) {
  const d = data && typeof data === 'object' ? data : {}
  const p = presence && typeof presence === 'object' ? presence : {}
  const health = d.health || {}
  const conn = d.connection || {}
  const dots = []

  const gateway = String(conn.gateway || '')
  dots.push({
    label: 'GATEWAY',
    state: gateway === 'open' ? 'ok' : gateway === 'connecting' ? 'warn' : gateway ? 'bad' : 'off'
  })
  dots.push({ label: 'BACKEND', state: conn.backend === 'ok' ? 'ok' : 'bad' })

  const src = (p.source && p.source.status) || 'none'
  dots.push({
    label: 'VOICE ' + String(src).toUpperCase(),
    state: p.demo ? 'off'
      : src === 'none' ? 'bad'
        : src === 'dom' || src === 'derived' ? 'warn' : 'ok'
  })

  if (health.brains === 'unreachable') {
    dots.push({ label: 'BRAINS', state: 'bad' })
  } else {
    const brains = Array.isArray(d.brains) ? d.brains.slice(0, 3) : []
    for (let i = 0; i < brains.length; i += 1) {
      const b = brains[i] || {}
      dots.push({
        label: String(b.label || b.id || 'brain').replace(/\s*brain\s*$/i, '').slice(0, 8),
        state: b.status === 'ok' ? 'ok' : b.status === 'unreachable' ? 'bad' : 'off'
      })
    }
    if (!brains.length) dots.push({ label: 'BRAINS', state: 'off' })
  }

  const senses = Array.isArray(d.senses) ? d.senses : []
  const live = senses.filter(function (s) { return s && s.status === 'ok' }).length
  dots.push({
    label: 'SENSES ' + live + '/' + senses.length,
    state: health.senses === 'unreachable' ? 'bad'
      : !senses.length ? 'off'
        : live < senses.length ? 'warn' : 'ok'
  })
  return dots
}

// ---- the `working` hand-off (SPEC §7.3 ruling 6) --------------------------

/** A call is on, the store says `thinking`, and a tool is actually running:
 *  everything that NAMES Agent's mode is handed a copy that says `working` —
 *  the scene (the orb's arc goes amber), the big mode word bottom-left, the
 *  VOICE pod's reading, and the statusbar chip in 60-plugin.js. One screen,
 *  one word. The store itself is never touched, and the pipe's own reading
 *  survives beside the derived one in the drawer's VOICE pod (`source mode …`),
 *  so nothing is hidden. */
function jarvisWorkingPresence(presence, activity) {
  const p = presence && typeof presence === 'object' ? presence : null
  if (!p || p.call !== 'on' || p.mode !== 'thinking') return p
  const a = activity && typeof activity === 'object' ? activity : null
  if (!a || a.running !== true || !a.tool) return p
  return Object.assign({}, p, { mode: 'working' })
}

function createOverlay(options) {
  const opts = options || {}
  const getScope = typeof opts.getScope === 'function' ? opts.getScope : function () { return opts.scope || null }
  const presence = opts.presence
  const data = opts.data
  const sceneFactory = typeof opts.createScene === 'function' ? opts.createScene : null
  const ctx = opts.ctx || null
  const log = typeof opts.log === 'function' ? opts.log : function () {}

  const doc = typeof document !== 'undefined' ? document : null
  const win = typeof window !== 'undefined' ? window : null

  const TEXT_HZ_MS = 100      // DOM text updates: 10 Hz, no more
  const PUSH_HZ_MS = 100      // backend presence push: ≤10 Hz (SPEC §4.4)
  const TELE_MS = 320         // ambient telemetry tick — a timer, never a level
  const TELE_BARS = 28        // SPEC §3b: 24–32 thin bars
  const BLIP_CAP = 6          // radar blips are capped; the label carries the truth
  // Fixed blip seats inside the 96 px dial: chrome that never moves, so a
  // changing session count reads as a changing count and nothing else.
  const BLIP_SEATS = [[34, 25], [60, 39], [26, 56], [64, 63], [47, 30], [21, 43]]
  // SPEC §4.6: a press waits 6 s for the bus, then says so out loud. START TALK
  // may have to open the floating HUD first and wait for the relay to come up
  // (SPEC §4.7), so that one press gets the full 8 s before it gives up.
  // §4.7 amendment — TIMEOUT ORDER. This generic line is the last resort; it
  // must never beat command()'s own named reason to the pod, so it always sits
  // half a second past whatever command() is willing to wait. START TALK has
  // the longest wait of any press: up to 8 s to open the floating HUD and hear
  // it answer, then up to three `start` sends 1.5 s apart (§4.7). The store
  // publishes that budget through waitBudgetMs(); the constant below is the
  // same arithmetic, kept only as the fallback when it does not.
  const VOICE_WAIT_MS = 6000
  const VOICE_GRACE_MS = 500
  // §4.8: START may also have to bring a chat forward and watch 4 s for the
  // composer's Talk action before it clicks anything. §4.9 puts the host's own
  // voice button ahead of all of that: press it, open the folded hub if that is
  // where it lives, and wait for its pill.
  // §4.9 amendment 2 adds the 300 ms the folded Voice hub gets to open before
  // the keyboard fallback, so the fallback arithmetic grows with the store's.
  // §4.10 adds three more: TWENTY seconds for the host to save a draft chat
  // (amendment 3 waits the slow save out instead of racing it), four for the
  // composer to settle around it, and ninety while Agent finishes an answer
  // (the wait of ruling 2, which the pod must never time out under).
  const VOICE_OPEN_WAIT_MS = 4000 + 800 + 300 + 4000 + 8000 + 3 * 1500 +
    20000 + 4000 + 90000 + VOICE_GRACE_MS   // 136 100 ms
  // §4.9 ruling 3: the built-in voice has no sleep. The store owns the wording;
  // this is the same line for a build (and a test) that loads the overlay alone.
  const NATIVE_NO_SLEEP = typeof JARVIS_NATIVE_NO_SLEEP === 'string'
    ? JARVIS_NATIVE_NO_SLEEP
    : 'built-in voice has no sleep'
  const VOICE_MSG_MS = 9000   // how long that honest line stays in the VOICE pod
  // §4.9 amendment 6: the generic line names the door that actually works on
  // this host. It is the last resort — command()'s own named reason always
  // lands first (the budget + 500 ms rule below) — so when it does show, the
  // honest instruction is the round button beside the message box.
  const VOICE_TIMEOUT_MSG = 'No answer · press the round voice button beside the message box once'
  // SPEC §8.1 ruling 1 — EVERY JARVIS LETTER IS A CHORD. Owner was typing on
  // another screen, hit T, and the call ended (2026-09-19). Control+Option is
  // the whole of it: a bare letter does nothing, in every state.
  //
  // The chord is the same two physical keys on both main computers; only the
  // spelling changes, so the labels are asked for once, here (05-scope.js).
  const KEYS = jarvisKeyLabelsFor(win)
  const VOICE_KEYS = { talk: KEYS.talk, mute: KEYS.mute, sleep: KEYS.sleep }
  const VOICE_SEATS = ['talk', 'mute', 'sleep']
  const PENDING_WORDS = {
    start: 'starting…', stop: 'ending…', mute: 'muting…',
    unmute: 'unmuting…', sleep: 'sleeping…', wake: 'waking…'
  }
  const MODE_WORDS = {
    idle: 'idle', listening: 'listening', thinking: 'thinking',
    speaking: 'speaking', working: 'working', muted: 'muted', sleeping: 'sleeping'
  }
  // SPEC §7.2 — the window keys and their exact lines. `open-on-boot` is the
  // one localStorage key the new window looks for; 60-plugin.js consumes it.
  const BOOT_KEY = 'open-on-boot'
  const OWN_WINDOW_OK = 'Jarvis mode opened in its own window · drag it to the other display, then press ' + KEYS.full + ' for full screen'
  const OWN_WINDOW_NO_BRIDGE = 'This Hermes cannot open a second window · update Hermes Desktop'
  const OWN_WINDOW_CALL_ON = 'End this call first · the new window starts its own call'
  const FULLSCREEN_FAILED = 'Full screen was refused by the window'
  const NOTICE_MS = 9000

  let root = null
  let el = {}
  let scene = null
  let open = false
  let offPresence = null
  let offData = null
  let clockTimer = null
  let resizeObs = null
  let lastRailH = 0          // §7 amendment 5 — the height the rail was cut for
  let lastRailK = 0          // §8 amendments C10 — the scale it was cut at
  let onResize = null
  let onKey = null
  let lastText = 0
  let lastPush = 0
  let restoreFocus = null
  let pushBlockedUntil = 0
  let lastEventStamp = 0
  let localPanel = null
  let teleTimer = null
  let teleBars = []
  let teleStart = 0
  // one pending ask per button: { action, timer }. It clears when the presence
  // bus reports the state that was asked for, or at the 6 s timeout.
  const voicePending = { talk: null, mute: null, sleep: null }
  let voiceMsgTimer = null
  // §4.10 ruling 3 — the store's own line (a dropped call, an unsaved chat, a
  // wait for Agent). It is not an answer to a press, so it has no timer: it
  // stays while the store says it is true and steps aside for a pressed
  // button's own reason until that one's nine seconds are up.
  let voiceNotice = ''
  // §8.2 ruling 4 — THE CALL-END LINE. `callEndShown` is the `at` of the end
  // whose line is on the glass (so one end is said once and not again),
  // `callEndLine` the line itself and `callEndAt` when it went up: it stands
  // until the next button press or chord, or sixty seconds, whichever is
  // first. Nothing here restarts a call — §8.2 ruling 5 is a warning line and
  // §4.10 ruling 3 still holds: the press is Owner's, it costs per minute.
  let callEndShown = 0
  let callEndLine = ''
  let callEndAt = 0
  let underOrbLine = ''      // what the NOW box last wanted under the orb
  // DEMO mode drives these labels and nothing else — no command ever leaves.
  let demoVoice = { call: 'on', muted: false, sleeping: false }
  // §7: the last data frame (the NOW box re-reads it once a second while a
  // turn runs), the drawer's state, and the window-notice timer.
  let lastData = null
  let drawerOpen = false
  let noticeTimer = null
  let onFullscreen = null
  let lastSysKey = ''
  // §7.2 — a window/full-screen line is showing at the foot of the left column.
  // It is drawn over the column's floor, so the rail gives up its LAST box
  // while it is up rather than being covered (§8.4 item 10: nothing overlaps).
  let noticeShowing = false
  // §8.4 item 3 — which WAITING ON YOU row is open. '' means "the first one",
  // so the ask Owner is most likely to act on explains itself without a
  // click; a click puts an id here and closes every other row.
  let openBriefId = ''
  // the mode word the glass is showing right now (§7.3 ruling 6). A data frame
  // that changes the derivation repaints it without waiting for the next
  // presence frame, so the word and the orb never disagree for a second.
  let lastShownMode = ''

  // The data feed verifies settings against the selected backend profile.
  // Before its first frame this overlay uses UTC instead of the computer's
  // locale, and the value never escapes this overlay instance.
  function currentTimezone() {
    const settings = lastData && lastData.settings
    return settings && settings.timezone ? String(settings.timezone) : 'UTC'
  }

  function reduced() {
    try {
      return Boolean(win && win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches)
    } catch (err) {
      return false
    }
  }

  function make(tag, cls, text) {
    const node = doc.createElement(tag)
    if (cls) node.className = cls
    if (text !== undefined && text !== null) node.textContent = String(text)
    return node
  }

  function injectStyle() {
    if (!doc || doc.getElementById('jv-style')) return
    if (typeof JARVIS_CSS !== 'string') return
    const style = doc.createElement('style')
    style.id = 'jv-style'
    style.textContent = JARVIS_CSS
    ;(doc.head || doc.documentElement).appendChild(style)
  }

  // ---- fallback scene (A2 replaces this through the §4.3 contract) ---------

  function stubScene(canvas) {
    let raf = null
    let alive = false
    let w = canvas.clientWidth || 800
    let h = canvas.clientHeight || 600
    let dpr = (win && win.devicePixelRatio) || 1
    let pres = { mode: 'idle', levels: { voice: 0, mic: 0 } }

    function paint() {
      const c2d = canvas.getContext('2d')
      if (!c2d) return
      canvas.width = Math.max(1, Math.round(w * dpr))
      canvas.height = Math.max(1, Math.round(h * dpr))
      c2d.setTransform(dpr, 0, 0, dpr, 0, 0)
      c2d.clearRect(0, 0, w, h)
      const tokens = typeof JARVIS_TOKENS === 'object' && JARVIS_TOKENS ? JARVIS_TOKENS : { silver: '#8A93A6', wash: '#E5EBFF' }
      const colors = typeof JARVIS_MODE_COLORS === 'object' && JARVIS_MODE_COLORS ? JARVIS_MODE_COLORS : {}
      const r = Math.min(w, h) * 0.13 * (1 + (pres.levels.voice || 0) * 0.25)
      c2d.beginPath()
      c2d.arc(w * 0.5, h * 0.58, r, 0, Math.PI * 2)
      c2d.strokeStyle = colors[pres.mode] || tokens.silver
      c2d.lineWidth = 2
      c2d.stroke()
      c2d.font = '10px ui-monospace, monospace'
      c2d.fillStyle = tokens.silver
      c2d.textAlign = 'center'
      c2d.fillText('SCENE STUB', w * 0.5, h * 0.58 + r + 22)
    }

    function loop() {
      if (!alive) return
      paint()
      raf = win && win.requestAnimationFrame ? win.requestAnimationFrame(loop) : null
    }

    return {
      setPresence: function (p) { if (p) pres = p },
      setData: function () {},
      setSize: function (nw, nh, ndpr) {
        w = nw || w
        h = nh || h
        dpr = ndpr || dpr
      },
      start: function () { if (alive) return; alive = true; loop() },
      stop: function () {
        alive = false
        if (raf !== null && win && win.cancelAnimationFrame) win.cancelAnimationFrame(raf)
        raf = null
      },
      destroy: function () { this.stop() },
      snapshotState: function () { return { stub: true, w: w, h: h, mode: pres.mode } }
    }
  }

  // ---- DOM ----------------------------------------------------------------

  // A pod. `hue` is decoration only (SPEC §3b): a solid bar in the pod's colour,
  // or — when an array is passed — one dot per item, the BRAINS case. It is
  // never a gauge, so it never implies a reading nobody took.
  function pod(name, accent, hue, body) {
    const box = make('div', 'jv-pod')
    if (accent) box.style.setProperty('--jv-ac', accent)
    const head = make('div', 'jv-pod-h')
    head.appendChild(make('b'))
    head.appendChild(make('span', null, name))
    const value = make('div', 'jv-pod-v', '—')
    const note = make('div', 'jv-pod-n', '')
    box.appendChild(head)
    if (Array.isArray(hue)) {
      const dots = make('div', 'jv-pod-dots')
      for (let i = 0; i < hue.length; i += 1) {
        const dot = make('i')
        dot.style.color = hue[i]
        dots.appendChild(dot)
      }
      box.appendChild(dots)
    } else if (hue) {
      box.appendChild(make('div', 'jv-pod-bar'))
    }
    if (body) box.appendChild(body)
    box.appendChild(value)
    box.appendChild(note)
    // `head` is handed back so a §7.4 box can hang a right-aligned tag off it
    // (the NOW box's `another chat`, AGENT IN FLIGHT's row count and file age).
    return { box: box, value: value, note: note, head: head }
  }

  /** A §7.4 rail box: the same glass, a tag in the header, a body of our own
   *  and no value/note line unless the box asks for one. */
  function railBox(name, accent, body) {
    const built = pod(name, accent, accent, body)
    const tag = make('em', 'jv-box-tag', '')
    built.head.appendChild(tag)
    built.value.style.display = 'none'
    built.note.style.display = 'none'
    return { box: built.box, tag: tag, value: built.value, note: built.note }
  }

  function setText(node, text) {
    if (!node) return
    const next = text === null || text === undefined ? '' : String(text)
    if (node.textContent !== next) node.textContent = next
    node.style.display = next ? '' : 'none'
  }

  // A status chip: dot + one short mono reading (SPEC §3b, top-left row).
  function chip(text) {
    const box = make('span', 'jv-chipx')
    box.appendChild(make('i'))
    const label = make('span', null, text)
    box.appendChild(label)
    return { box: box, label: label }
  }

  function setChip(c, text, state) {
    if (!c) return
    if (c.label.textContent !== text) c.label.textContent = text
    c.box.classList.toggle('jv-alarm', state === 'alarm')
    c.box.classList.toggle('jv-off', state === 'off')
  }

  // The radar: a constant conic sweep (chrome) plus up to six blips that ARE
  // the live session count. Nothing here follows the voice.
  function buildRadar() {
    const wrap = make('div', 'jv-radar')
    const dial = make('div', 'jv-radar-dial')
    dial.appendChild(make('div', 'jv-radar-sweep'))
    const blips = []
    for (let i = 0; i < BLIP_CAP; i += 1) {
      const blip = make('span', 'jv-blip')
      blip.style.left = BLIP_SEATS[i][0] + 'px'
      blip.style.top = BLIP_SEATS[i][1] + 'px'
      blip.style.display = 'none'
      dial.appendChild(blip)
      blips.push(blip)
    }
    wrap.appendChild(dial)
    return { wrap: wrap, blips: blips }
  }

  // Ambient telemetry: 28 bars on a timer. Deliberately NOT a reading — the
  // label under it says so, and the heights come from the clock, not the mic.
  function buildTelemetry(tokens) {
    const wrap = make('div', 'jv-tele')
    const hues = [
      tokens.cobaltBright || '#3A62FF', tokens.cyan || '#35E0FF',
      tokens.cobaltBright || '#3A62FF', tokens.violet || '#8B6CFF',
      tokens.cobaltBright || '#3A62FF', tokens.teal || '#2DD4BF',
      tokens.cobaltBright || '#3A62FF', tokens.magenta || '#FF4FD8'
    ]
    const bars = []
    for (let i = 0; i < TELE_BARS; i += 1) {
      const bar = make('span', 'jv-tbar')
      bar.style.color = hues[i % hues.length]
      wrap.appendChild(bar)
      bars.push(bar)
    }
    return { wrap: wrap, bars: bars }
  }

  function paintTelemetry() {
    if (!teleBars.length) return
    const t = (Date.now() - teleStart) / 1000
    for (let i = 0; i < teleBars.length; i += 1) {
      const wave = Math.sin(t * (0.62 + i * 0.085) + i * 0.79) * 0.34 +
        Math.sin(t * 0.29 + i * 0.41) * 0.16
      const h = Math.round(52 + wave * 100)
      teleBars[i].style.height = Math.max(8, Math.min(100, h)) + '%'
    }
  }

  // ---- voice controls (SPEC §4.6) -----------------------------------------

  // A glass button. It never keeps focus: the composer behind the overlay is
  // Owner's typing seat, so the button blurs the moment it is clicked.
  function voiceButton(seat) {
    const btn = make('button', 'jv-vbtn')
    btn.type = 'button'
    btn.setAttribute('data-jv', seat)
    const label = make('span', 'jv-vbtn-l', '')
    btn.appendChild(label)
    btn.appendChild(make('kbd', null, VOICE_KEYS[seat]))
    btn.addEventListener('mousedown', function (event) {
      if (event && typeof event.preventDefault === 'function') event.preventDefault()
    })
    btn.addEventListener('click', function (event) {
      if (event && typeof event.preventDefault === 'function') event.preventDefault()
      pressVoice(seat)
      try { btn.blur() } catch (err) { /* focus is a nicety, not a requirement */ }
    })
    return { box: btn, label: label }
  }

  /** A small top-chrome button (SPEC §7.2 ruling 1 and 4). Same no-focus rule
   *  as the voice buttons: the composer behind the overlay keeps the caret. */
  function chromeButton(text, key, title) {
    const btn = make('button', 'jv-cbtn')
    btn.type = 'button'
    btn.setAttribute('data-jv', 'chrome-' + String(key).slice(-1).toLowerCase())
    btn.setAttribute('title', title + '  (' + key + ')')
    btn.setAttribute('aria-label', title)
    const label = make('span', 'jv-cbtn-l', text)
    btn.appendChild(label)
    btn.appendChild(make('kbd', null, key))
    btn.addEventListener('mousedown', function (event) {
      if (event && typeof event.preventDefault === 'function') event.preventDefault()
    })
    btn.addEventListener('click', function () {
      try { btn.blur() } catch (err) { /* focus is a nicety */ }
    })
    return { box: btn, label: label }
  }

  // SPEC §4.6 amendment (2026-09-18 18:14): the cluster is a glass pod in the
  // LEFT rail under TELEMETRY, not a row under Agent. The centre band is his.
  function buildVoice(accent) {
    const wrap = make('div', 'jv-voice')
    const row = make('div', 'jv-voice-row')
    const talk = voiceButton('talk')
    const mute = voiceButton('mute')
    const sleep = voiceButton('sleep')
    row.appendChild(talk.box)
    row.appendChild(mute.box)
    row.appendChild(sleep.box)
    wrap.appendChild(row)
    // DEMO label only — the key hints ride on the buttons.
    const tag = make('div', 'jv-voice-tag', '')
    tag.style.display = 'none'
    wrap.appendChild(tag)
    // same glass as every other pod: cobalt border, header accent line, hue bar
    const box = pod('VOICE CONTROL', accent, accent, wrap)
    box.value.textContent = ''
    box.value.style.display = 'none'
    box.note.textContent = ''
    box.note.style.display = 'none'
    return { box: box.box, wrap: wrap, talk: talk, mute: mute, sleep: sleep, tag: tag }
  }

  function build() {
    const tokens = typeof JARVIS_TOKENS === 'object' && JARVIS_TOKENS ? JARVIS_TOKENS : {}
    const hues = typeof JARVIS_POD_HUES === 'object' && JARVIS_POD_HUES ? JARVIS_POD_HUES : {
      connection: tokens.cobaltBright, voice: tokens.cyan, lever: tokens.amber,
      jobs: tokens.coral, fleet: tokens.violet, scan: tokens.cobaltBright,
      telemetry: tokens.teal, brains: [tokens.magenta, tokens.cyan, tokens.teal]
    }
    root = make('div', 'jv-overlay')
    root.setAttribute('role', 'dialog')
    root.setAttribute('aria-modal', 'true')
    root.setAttribute('aria-label', 'Jarvis mode')
    root.tabIndex = -1

    const canvas = make('canvas', 'jv-canvas')
    root.appendChild(canvas)

    const corners = ['tl', 'tr', 'bl', 'br']
    for (let i = 0; i < corners.length; i += 1) root.appendChild(make('span', 'jv-bracket ' + corners[i]))

    // top-left: the name, the status chips (every chip a real reading) and the
    // ambient telemetry strip — same side as the reference's SYSTEM VITALS panel.
    const topLeft = make('div', 'jv-layer jv-top-left')
    const head = make('div', 'jv-head')
    const mainTitle = make('div', 'jv-title', 'JARVIS MODE · AGENT')
    head.appendChild(mainTitle)
    const sub = make('div', 'jv-sub', 'command centre')
    head.appendChild(sub)
    topLeft.appendChild(head)
    const chips = make('div', 'jv-chips')
    const chipOnline = chip('OFFLINE')
    const chipVoice = chip('VOICE NONE')
    const chipBrains = chip('— BRAINS')
    const chipMic = chip('MIC OFF')
    chips.appendChild(chipOnline.box)
    chips.appendChild(chipVoice.box)
    chips.appendChild(chipBrains.box)
    chips.appendChild(chipMic.box)
    topLeft.appendChild(chips)
    // the voice cluster is the left rail's one working control (SPEC §4.6
    // amendment); TELEMETRY now lives in the diagnostics drawer (§7.4)
    const voiceBox = buildVoice(hues.connection)
    topLeft.appendChild(voiceBox.box)

    // ---- the LEFT rail (SPEC §8.4 item 2) ---------------------------------
    // Under VOICE CONTROL: NEXT MEETING · TODAY · SPEND · SCOREBOARD. Same
    // glass, same law as the right rail — boxes do not shrink, rows are whole,
    // and what will not fit is counted out loud or collapses to one line.
    const leftRail = make('div', 'jv-left-rail')

    const meetBody = make('div', 'jv-meet')
    const meetBig = make('div', 'jv-big', '—')
    const meetTitle = make('div', 'jv-meet-t', '')
    const meetMeta = make('div', 'jv-meet-m', '')
    const meetLater = make('div', 'jv-rows')
    meetLater.style.display = 'none'
    meetBody.appendChild(meetBig)
    meetBody.appendChild(meetTitle)
    meetBody.appendChild(meetMeta)
    meetBody.appendChild(meetLater)
    const meetBox = railBox('NEXT MEETING', tokens.cyan || hues.voice, meetBody)
    leftRail.appendChild(meetBox.box)

    const todayBody = make('div', 'jv-today')
    const todayLever = make('div', 'jv-lever')
    const todayLeverEye = make('i', null, 'ONE LEVER')
    const todayLeverText = make('span', null, '—')
    todayLever.appendChild(todayLeverEye)
    todayLever.appendChild(todayLeverText)
    const todayHead = make('div', 'jv-today-h', '')
    const todayRows = make('div', 'jv-trows')
    todayBody.appendChild(todayLever)
    todayBody.appendChild(todayHead)
    todayBody.appendChild(todayRows)
    const todayBox = railBox('TODAY', tokens.amber || hues.lever, todayBody)
    leftRail.appendChild(todayBox.box)

    const spendBody = make('div', 'jv-spend')
    const spendBig = make('div', 'jv-big', '0 s · 0 calls')
    const spendNote = make('div', 'jv-subline', 'voice today · measured by Jarvis in this window')
    const spendRows = make('div', 'jv-rows')
    const spendTotal = make('div', 'jv-spend-t', '')
    const spendCost = make('div', 'jv-spend-c', '')
    spendBody.appendChild(spendBig)
    spendBody.appendChild(spendNote)
    spendBody.appendChild(spendRows)
    spendBody.appendChild(spendTotal)
    spendBody.appendChild(spendCost)
    const spendBox = railBox('SPEND', tokens.teal || hues.telemetry, spendBody)
    leftRail.appendChild(spendBox.box)

    const scoreBody = make('div', 'jv-score')
    const scoreTop = make('div', 'jv-score-top')
    const scoreLeft = make('div', 'jv-score-l')
    const scoreBig = make('div', 'jv-big', '—')
    const scoreLabel = make('div', 'jv-subline', 'day build streak')
    const scoreDays = make('div', 'jv-days')
    scoreLeft.appendChild(scoreBig)
    scoreLeft.appendChild(scoreLabel)
    scoreTop.appendChild(scoreLeft)
    scoreTop.appendChild(scoreDays)
    const scoreSecond = make('div', 'jv-spend-t', '')
    const scoreLine = make('div', 'jv-empty', '')
    scoreLine.style.display = 'none'
    scoreBody.appendChild(scoreTop)
    scoreBody.appendChild(scoreSecond)
    scoreBody.appendChild(scoreLine)
    const scoreBox = railBox('SCOREBOARD', tokens.violet || hues.fleet, scoreBody)
    leftRail.appendChild(scoreBox.box)

    // §8.4 item 10 — what the left rail is holding back, said out loud. It is
    // only ever seen under 730 px of window, where a fourth headline does not
    // fit at all.
    const leftMore = make('div', 'jv-more', '')
    leftMore.style.display = 'none'
    leftRail.appendChild(leftMore)

    topLeft.appendChild(leftRail)
    root.appendChild(topLeft)

    // the RIGHT RAIL (SPEC §7.4, re-stacked by §8.4 item 2) — one column, top
    // to bottom: the clock, the two window buttons, then NOW · AGENT'S HELPERS ·
    // WAITING ON YOU · AGENT IN FLIGHT · OVERNIGHT JOBS · SYSTEMS. Today's
    // instrument pods (CONNECTION, FLEET, SCAN, VOICE, BRAINS, TELEMETRY) live
    // in the drawer below, unchanged — nothing was dropped, it is one chord
    // (⌃⌥D) away.
    const right = make('div', 'jv-layer jv-right')
    // the clock and the two window buttons share ONE row: eight boxes in
    // 818 px means every 24 px of chrome is a row of Agent's work
    const clockRow = make('div', 'jv-top-row')
    const clock = make('span', 'jv-clock', '--:--:--')
    const chrome = make('div', 'jv-chrome')
    const ownBtn = chromeButton('WINDOW', KEYS.window, 'Open Jarvis mode in its own Hermes window')
    const fullBtn = chromeButton('FULL', KEYS.full, 'Take this window full screen')
    const diagBtn = chromeButton('SYSTEMS', KEYS.drawer, 'Open the diagnostics drawer')
    chrome.appendChild(ownBtn.box)
    chrome.appendChild(fullBtn.box)
    chrome.appendChild(diagBtn.box)
    ownBtn.box.addEventListener('click', function () { pressOwnWindow() })
    fullBtn.box.addEventListener('click', function () { toggleFullscreen() })
    diagBtn.box.addEventListener('click', function () { toggleDrawer() })
    clockRow.appendChild(chrome)
    clockRow.appendChild(clock)
    right.appendChild(clockRow)

    // NOW — the biggest box, and the first thing Owner's eye lands on.
    const nowBody = make('div', 'jv-now-body')
    const nowLine = make('div', 'jv-now-line', 'quiet')
    const nowDetail = make('div', 'jv-now-detail', '')
    const nowMeta = make('div', 'jv-now-meta', '')
    const nowThought = make('div', 'jv-now-thought', '')
    const nowChips = make('div', 'jv-chipsrow')
    const nowRecent = make('div', 'jv-now-recent')
    const nowNeeds = make('div', 'jv-needs', '')
    nowDetail.style.display = 'none'
    nowThought.style.display = 'none'
    nowChips.style.display = 'none'
    nowRecent.style.display = 'none'
    nowNeeds.style.display = 'none'
    nowBody.appendChild(nowLine)
    nowBody.appendChild(nowDetail)
    nowBody.appendChild(nowMeta)
    nowBody.appendChild(nowThought)
    nowBody.appendChild(nowChips)
    nowBody.appendChild(nowRecent)
    nowBody.appendChild(nowNeeds)
    const nowBox = railBox('NOW', tokens.cyan || hues.voice, nowBody)
    nowBox.box.classList.add('jv-now')
    right.appendChild(nowBox.box)

    // AGENT'S HELPERS takes AGENTS AT WORK's seat (§8.4 item 2): the helpers
    // Agent actually spawned, which no `subagent.*` event ever reaches this
    // window (they run on the mini as background delegations).
    const helperRows = make('div', 'jv-hrows')
    const helpersBox = railBox("AGENT'S HELPERS", tokens.violet || hues.fleet, helperRows)
    right.appendChild(helpersBox.box)

    const waitingRows = make('div', 'jv-rows jv-rows-2')
    const waitingBox = railBox('WAITING ON YOU', tokens.amber || hues.lever, waitingRows)
    waitingBox.box.classList.add('jv-waiting')
    right.appendChild(waitingBox.box)

    const flightRows = make('div', 'jv-rows jv-rows-1')
    const flightBox = railBox('AGENT IN FLIGHT', tokens.violet || hues.fleet, flightRows)
    // the rail's designated give-way: when six boxes will not fit, this is the
    // one that shrinks, and its header still carries the true row count
    flightBox.box.classList.add('jv-flight')
    right.appendChild(flightBox.box)

    // OVERNIGHT JOBS (§8.4 item 7) — what ran while he slept, since 21:00.
    const jobsBody = make('div', 'jv-jobs')
    const jobsLine = make('div', 'jv-jobline')
    const jobsOk = make('b', null, '—')
    const jobsFailed = make('em', null, '')
    const jobsSince = make('span', null, '')
    jobsLine.appendChild(jobsOk)
    jobsLine.appendChild(jobsFailed)
    jobsLine.appendChild(jobsSince)
    const jobsRows = make('div', 'jv-rows')
    // §8 amendment B.5 — the next run, on the LAST line of the box
    const jobsNext = make('div', 'jv-jobnext', '')
    jobsNext.style.display = 'none'
    jobsBody.appendChild(jobsLine)
    jobsBody.appendChild(jobsRows)
    jobsBody.appendChild(jobsNext)
    const jobsBox = railBox('OVERNIGHT JOBS', tokens.coral || hues.jobs, jobsBody)
    right.appendChild(jobsBox.box)

    // AGENTS AT WORK becomes FLEET inside the drawer (§8.4 item 2). Same
    // readings, same words, one chord (⌃⌥D) away — nothing was dropped.
    const agentBody = make('div', 'jv-agents')
    const agentBusy = make('div', 'jv-agents-busy', 'nobody is working')
    const agentRows = make('div', 'jv-rows')
    const agentIdle = make('div', 'jv-agents-idle', '')
    agentBody.appendChild(agentBusy)
    agentBody.appendChild(agentRows)
    agentBody.appendChild(agentIdle)
    const agentsBox = railBox('FLEET', tokens.teal || hues.telemetry, agentBody)

    const sysRow = make('div', 'jv-sysrow')
    sysRow.setAttribute('role', 'button')
    sysRow.setAttribute('tabindex', '-1')
    sysRow.setAttribute('title', 'Open the diagnostics drawer  (' + KEYS.drawer + ')')
    sysRow.addEventListener('click', function () { toggleDrawer() })
    const systemsBox = railBox('SYSTEMS', hues.connection, sysRow)
    right.appendChild(systemsBox.box)
    root.appendChild(right)

    // ---- the diagnostics drawer (⌃⌥D) -------------------------------
    // Today's pods, word for word. Built once and painted on every frame
    // whether it is on screen or not, so opening it never shows a stale value.
    const drawer = make('div', 'jv-drawer')
    drawer.style.display = 'none'
    const drawerHead = make('div', 'jv-drawer-h')
    drawerHead.appendChild(make('span', null, 'DIAGNOSTICS'))
    const drawerClose = chromeButton('CLOSE', KEYS.drawer, 'Close the diagnostics drawer')
    drawerClose.box.addEventListener('click', function () { toggleDrawer() })
    drawerHead.appendChild(drawerClose.box)
    drawer.appendChild(drawerHead)

    const connection = pod('CONNECTION', hues.connection, hues.connection)
    const radar = buildRadar()
    // the radar goes in LAST, under the reading instead of over it: when the
    // column is short SCAN is the pod that gives way, and what it gives up has
    // to be the dial, never the session count and its label.
    const scan = pod('SCAN', hues.scan, hues.scan)
    scan.box.classList.add('jv-scan')
    scan.box.appendChild(radar.wrap)
    scan.value.textContent = 'no signal'
    scan.note.textContent = 'sessions'

    const voice = pod('VOICE', hues.voice, hues.voice)
    // the honest answer when a command goes nowhere (SPEC §4.6) — its own line
    // INSIDE the VOICE pod, in flow, because the note above it is the source
    // reading and must stay readable
    const voiceMsg = make('div', 'jv-cmdmsg', '')
    voiceMsg.style.display = 'none'
    voice.box.appendChild(voiceMsg)
    // §8.2 ruling 5 — the amber PRE-FLIGHT line: the link came back and this
    // chat's route has not been entered since, so the first delegated job may
    // hang the call up. One line, call off only, and nothing is healed.
    const voiceWarn = make('div', 'jv-cmdmsg', '')
    voiceWarn.style.color = 'var(--jv-amber)'
    voiceWarn.style.display = 'none'
    voice.box.appendChild(voiceWarn)
    const brains = pod('BRAINS', tokens.violet, hues.brains)
    // TELEMETRY moves in here with them (SPEC §7.4); the left rail keeps only
    // the name, the chips and VOICE CONTROL.
    const tele = buildTelemetry(tokens)
    const telemetry = pod('TELEMETRY', hues.telemetry, hues.telemetry, tele.wrap)
    telemetry.value.textContent = ''
    telemetry.value.style.display = 'none'
    telemetry.note.textContent = 'ambient telemetry · motion, not metrics'
    teleBars = tele.bars
    drawer.appendChild(connection.box)
    drawer.appendChild(agentsBox.box)      // §8.4 item 2 — AGENTS AT WORK, as FLEET
    drawer.appendChild(scan.box)
    drawer.appendChild(voice.box)
    drawer.appendChild(brains.box)
    drawer.appendChild(telemetry.box)
    root.appendChild(drawer)

    // bottom-left: the one display word, the live line, the captions
    const botLeft = make('div', 'jv-layer jv-bot-left')
    const mode = make('div', 'jv-mode', 'idle')
    const live = make('div', 'jv-live', '')
    const captions = make('div', 'jv-captions')
    botLeft.appendChild(mode)
    botLeft.appendChild(live)
    botLeft.appendChild(captions)
    root.appendChild(botLeft)

    // Agent's card
    const panel = make('div', 'jv-panel')
    panel.style.display = 'none'
    const panelTitle = make('h2', null, '')
    const panelBody = make('p', null, '')
    panel.appendChild(panelTitle)
    panel.appendChild(panelBody)
    root.appendChild(panel)

    // §7 amendment 3 — the DEMO badge and the §7.2 notice used to be centred
    // at the top of the glass, which is where the MIDDLE BRAIN is drawn
    // (≈ y 12–160 at 1440×900): the badge sat on its face. Both now ride at
    // the foot of the left column, under VOICE CONTROL, where the scene keeps
    // its own labels out (40-scene.js keepOut [0,0,366,306]) and nothing can
    // move them onto the display.
    const demo = make('div', 'jv-demo', 'DEMO')
    demo.style.display = 'none'
    topLeft.appendChild(demo)

    // §7.3 ruling 6 — the one quiet line under Agent, so a long silent turn is
    // readable without looking right. Empty until a turn has run 8 s.
    const underOrb = make('div', 'jv-underorb', '')
    underOrb.style.display = 'none'
    root.appendChild(underOrb)

    // §7.2 — what happened when a window or full screen was asked for. It sits
    // under the DEMO badge in the left column (amendment 3), so the two never
    // fight for a seat and neither one lands on a brain.
    const notice = make('div', 'jv-notice', '')
    notice.style.display = 'none'
    topLeft.appendChild(notice)

    root.appendChild(make('div', 'jv-hint', 'ESC TO CLOSE'))

    const ticker = make('div', 'jv-ticker')
    const track = make('div', 'jv-ticker-track')
    if (reduced()) track.style.animation = 'none'
    ticker.appendChild(track)
    root.appendChild(ticker)

    el = {
      canvas: canvas, clock: clock, connection: connection, mode: mode, live: live, mainTitle: mainTitle,
      captions: captions, voice: voice, brains: brains,
      panel: panel, panelTitle: panelTitle, panelBody: panelBody,
      demo: demo, ticker: ticker, track: track,
      scan: scan, blips: radar.blips, telemetry: telemetry,
      chipOnline: chipOnline, chipVoice: chipVoice, chipBrains: chipBrains, chipMic: chipMic,
      voiceMsg: voiceMsg, voiceWarn: voiceWarn, voiceBox: voiceBox.wrap, voiceTag: voiceBox.tag,
      vcTalk: voiceBox.talk, vcMute: voiceBox.mute, vcSleep: voiceBox.sleep,
      // §7.2 / §7.4 — the rail, the drawer and the two window buttons
      right: right, drawer: drawer, chromeOwn: ownBtn, chromeFull: fullBtn, chromeDiag: diagBtn,
      notice: notice, underOrb: underOrb,
      now: nowBox, nowLine: nowLine, nowDetail: nowDetail, nowMeta: nowMeta,
      nowThought: nowThought, nowChips: nowChips, nowRecent: nowRecent, nowNeeds: nowNeeds,
      waiting: waitingBox, waitingRows: waitingRows,
      flight: flightBox, flightRows: flightRows,
      agents: agentsBox, agentRows: agentRows, agentBusy: agentBusy, agentIdle: agentIdle,
      systems: systemsBox, sysRow: sysRow,
      // §8.4 — the v3 boxes: the right rail's two new ones and the left rail
      helpers: helpersBox, helperRows: helperRows,
      jobs: jobsBox, jobsLine: jobsLine, jobsOk: jobsOk, jobsFailed: jobsFailed,
      jobsSince: jobsSince, jobsRows: jobsRows, jobsNext: jobsNext,
      leftRail: leftRail, leftBoxes: [meetBox.box, todayBox.box, spendBox.box, scoreBox.box],
      leftBoxIds: ['next_meeting', 'today', 'spend', 'scoreboard'],
      leftMore: leftMore,
      meet: meetBox, meetBig: meetBig, meetTitle: meetTitle, meetMeta: meetMeta, meetLater: meetLater,
      today: todayBox, todayLever: todayLeverText, todayLeverEye: todayLeverEye,
      todayHead: todayHead, todayRows: todayRows,
      spend: spendBox, spendBig: spendBig, spendNote: spendNote, spendRows: spendRows,
      spendTotal: spendTotal, spendCost: spendCost,
      score: scoreBox, scoreBig: scoreBig, scoreLabel: scoreLabel, scoreSecond: scoreSecond,
      scoreDays: scoreDays, scoreLine: scoreLine
    }
  }

  // ---- voice controls: state, press, paint (SPEC §4.6) --------------------

  function isDemo(p) {
    if (presence && typeof presence.isDemo === 'function') {
      try { return presence.isDemo() === true } catch (err) { /* fall through */ }
    }
    return Boolean(p && p.demo)
  }

  // What the buttons are allowed to say. Off the snapshot only: `muted` and
  // `sleeping` are optional fields, so the mode word (which the bus sets first)
  // is the fallback. In DEMO it is the demo's own little state machine.
  function voiceState(p) {
    if (isDemo(p)) {
      return { demo: true, call: demoVoice.call, muted: demoVoice.muted, sleeping: demoVoice.sleeping, native: false }
    }
    const pres = p || {}
    return {
      demo: false,
      call: pres.call || 'off',
      muted: pres.muted === true || pres.mode === 'muted',
      sleeping: pres.sleeping === true || pres.mode === 'sleeping',
      // §4.9 ruling 6: which voice system is feeding this pod. The VOICE pod
      // already prints the source word; the buttons read it too, because the
      // built-in voice has no sleep to offer.
      native: Boolean(pres.source && pres.source.status === 'native')
    }
  }

  function voiceAction(seat, st) {
    if (seat === 'talk') return st.call === 'off' ? 'start' : 'stop'
    if (seat === 'mute') return st.muted ? 'unmute' : 'mute'
    return st.sleeping ? 'wake' : 'sleep'
  }

  function voiceLabel(seat, st) {
    if (seat === 'talk') return st.call === 'off' ? 'START TALK' : 'END TALK'
    if (seat === 'mute') return st.muted ? 'UNMUTE' : 'MUTE'
    return st.sleeping ? 'WAKE' : 'SLEEP'
  }

  // Coral is for the live/quiet states: a call that can be ended, a mic that is
  // muted, an Agent that is asleep.
  function voiceHot(seat, st) {
    if (seat === 'talk') return st.call !== 'off'
    if (seat === 'mute') return st.muted === true
    return st.sleeping === true
  }

  // §4.8 ruling 6 — MUTE and SLEEP follow the DOOR, not only the snapshot.
  // A call can be perfectly live while this window's snapshot still reads
  // `off` (Talk in the floating HUD between frames, a quiet composer call), so
  // the store is asked whether a press would reach Talk at all. The older
  // snapshot test stays as the fallback for a store without canCommand().
  function voiceDoorOpen(st) {
    if (st.call === 'on') return true
    if (!presence || typeof presence.canCommand !== 'function') return false
    try {
      return presence.canCommand() === true
    } catch (err) {
      return false
    }
  }

  // Disabled ONLY when we actually know the door is shut (SPEC §4.6, §4.8).
  function voiceBlocked(seat, st) {
    if (st.demo) return ''
    if (!presence || typeof presence.command !== 'function') return 'this build has no voice command door'
    // §4.9 ruling 3: SLEEP and WAKE are Talk's, not the host's. With the
    // built-in voice on the line the button is greyed and says so, rather than
    // offering a press that has nowhere to land.
    if (seat === 'sleep' && st.native) return NATIVE_NO_SLEEP
    if (seat !== 'talk' && !voiceDoorOpen(st)) return 'no live call · start Talk first'
    return ''
  }

  function voiceSettled(action, st) {
    if (action === 'start') return st.call !== 'off'
    if (action === 'stop') return st.call === 'off'
    if (action === 'mute') return st.muted === true
    if (action === 'unmute') return st.muted === false
    if (action === 'sleep') return st.sleeping === true
    return st.sleeping === false
  }

  function timerSet(fn, ms) {
    const setT = win && typeof win.setTimeout === 'function' ? win.setTimeout : setTimeout
    return setT(fn, ms)
  }

  function timerClear(id) {
    const clearT = win && typeof win.clearTimeout === 'function' ? win.clearTimeout : clearTimeout
    try { clearT(id) } catch (err) { /* already gone */ }
  }

  function voiceMessage(text) {
    if (!el.voiceMsg) return
    if (voiceMsgTimer) { timerClear(voiceMsgTimer); voiceMsgTimer = null }
    if (!text) {
      el.voiceMsg.textContent = ''
      el.voiceMsg.style.display = 'none'
      return
    }
    el.voiceMsg.textContent = text
    el.voiceMsg.style.display = ''
    log('voice: ' + text)
    voiceMsgTimer = timerSet(function () {
      voiceMsgTimer = null
      if (el.voiceMsg) {
        el.voiceMsg.textContent = ''
        el.voiceMsg.style.display = 'none'
      }
    }, VOICE_MSG_MS)
  }

  /** §4.10 ruling 3 — paint the store's line without stealing the glass from a
   *  press. A transient message (voiceMsgTimer set) is always allowed to finish;
   *  the notice comes back on the next paint. */
  function paintNotice(p) {
    if (!el.voiceMsg) return
    const next = noticeOf(p)
    if (next) {
      if (!voiceMsgTimer && el.voiceMsg.textContent !== next) {
        el.voiceMsg.textContent = next
        el.voiceMsg.style.display = ''
        if (next !== voiceNotice) log('voice: ' + next)
      }
    } else if (!voiceMsgTimer && voiceNotice && el.voiceMsg.textContent === voiceNotice) {
      el.voiceMsg.textContent = ''
      el.voiceMsg.style.display = 'none'
    }
    voiceNotice = next
    // §8.2 ruling 5 — the amber line rides beside the notice, on the same
    // paint. It is not a notice: it never times out, it goes when the route is
    // entered again or a call comes on.
    setText(el.voiceWarn, preflightOf())
    paintUnderOrb()
  }

  // §8 amendment A ruling 5, finished by §8 amendment C1 — ONE MESSAGE PER
  // ENDED CALL. The §4.10 line "The call ended on its own · press START TALK to
  // reconnect" said the same thing the §8.2 under-orb line says, in a second
  // place and in fewer words: the black box names the CAUSE ("the link to the
  // mini blinked") and the way back. Wave 3 filtered it out here by its exact
  // words; C1 removed it AT THE SOURCE instead, so there is nothing left to
  // filter and this function simply prints what the store publishes. Every
  // other notice (the draft-chat warning, the slow save) still lands here,
  // because each of those says something the under-orb line does not.

  /** The line the store is publishing right now: live from the store where it
   *  offers one, off the snapshot otherwise. */
  function noticeOf(p) {
    let line = ''
    let asked = false
    if (presence && typeof presence.notice === 'function') {
      try {
        const live = presence.notice()
        line = typeof live === 'string' ? live : ''
        asked = true
      } catch (err) { /* fall through to the snapshot */ }
    }
    if (!asked) line = p && typeof p.notice === 'string' ? p.notice : ''
    return line
  }

  // ---- §8.2 the call black box, as one line on the glass -------------------

  const CALL_END_LINE_MS = 60000   // §8.2 ruling 4 — sixty seconds, then it goes

  /** The store's verdict on the last call that stopped, or null. */
  function lastCallEnd() {
    if (!presence || typeof presence.lastCallEnd !== 'function') return null
    try {
      const end = presence.lastCallEnd()
      return end && typeof end === 'object' ? end : null
    } catch (err) {
      return null
    }
  }

  /** The store's own wording for that end — '' for a press, and '' for a store
   *  too old to have a black box in it. */
  function callEndLineOf() {
    if (!presence || typeof presence.callEndLine !== 'function') return ''
    try {
      const line = presence.callEndLine()
      return typeof line === 'string' ? line : ''
    } catch (err) {
      return ''
    }
  }

  /** §8.2 ruling 4 — the ONE line, shown once per end. A call Jarvis or Owner
   *  ended says nothing at all; only an end the host made gets a line, and only
   *  the first time that end is seen. */
  function callEndNow(at) {
    const end = lastCallEnd()
    if (end && end.at && end.at !== callEndShown) {
      const line = callEndLineOf()
      callEndShown = end.at
      callEndLine = line
      callEndAt = line ? at : 0
      if (line) log('call end: ' + line)
    }
    if (callEndLine && at - callEndAt > CALL_END_LINE_MS) clearCallEnd()
    return callEndLine
  }

  /** §8.2 ruling 4 — THE CALL-END LINE TAKES THE UNDER-ORB LINE while it is up.
   *  A dropped call is news; a running turn's "thinking · 2m 10s" is ambient,
   *  and it comes back the moment the line clears. Painted from the PRESENCE
   *  path as well as the NOW path, because a call that ends has to be named
   *  within a frame, not at the next sixty-second data poll. */
  function paintUnderOrb() {
    if (!el.underOrb) return
    setText(el.underOrb, callEndNow(Date.now()) || underOrbLine)
  }

  /** "Until the next press or chord": every accepted press and every accepted
   *  chord calls this. The end itself stays in the receipt; only the glass
   *  gives the line back. */
  function clearCallEnd() {
    callEndLine = ''
    callEndAt = 0
  }

  /** §8.2 ruling 5 — the store's amber pre-flight line, live. */
  function preflightOf() {
    if (!presence || typeof presence.callPreflight !== 'function') return ''
    try {
      const line = presence.callPreflight()
      return typeof line === 'string' ? line : ''
    } catch (err) {
      return ''
    }
  }

  /** §4.10 ruling 2 — is the store standing by for Agent to finish his answer? */
  function startWaiting() {
    if (!presence || typeof presence.startWaiting !== 'function') return false
    try {
      return presence.startWaiting() === true
    } catch (err) {
      return false
    }
  }

  function clearPending(seat) {
    const pend = voicePending[seat]
    if (!pend) return
    if (pend.timer !== null && pend.timer !== undefined) timerClear(pend.timer)
    voicePending[seat] = null
  }

  function clearAllPending() {
    for (let i = 0; i < VOICE_SEATS.length; i += 1) clearPending(VOICE_SEATS[i])
    if (voiceMsgTimer) { timerClear(voiceMsgTimer); voiceMsgTimer = null }
  }

  /** command()'s own budget plus half a second, so its named reason wins. */
  function pendingWaitMs(action) {
    if (action !== 'start') return VOICE_WAIT_MS
    const budget = presence && typeof presence.waitBudgetMs === 'function'
      ? Number(presence.waitBudgetMs('start'))
      : 0
    return budget > 0 ? budget + VOICE_GRACE_MS : VOICE_OPEN_WAIT_MS
  }

  function startPending(seat, action) {
    clearPending(seat)
    voicePending[seat] = {
      action: action,
      timer: timerSet(function () {
        // The wait is over and nothing reported. Say exactly that.
        voicePending[seat] = null
        voiceMessage(VOICE_TIMEOUT_MSG)
        repaintVoice()
      }, pendingWaitMs(action))
    }
  }

  function repaintVoice() {
    const p = presence && typeof presence.get === 'function' ? presence.get() : null
    try { paintVoice(p) } catch (err) { log('voice paint failed: ' + (err && err.message ? err.message : err)) }
  }

  function pressVoice(seat) {
    if (!open || VOICE_SEATS.indexOf(seat) < 0) return
    // §8.2 ruling 4: "until the next press" — this is the next press.
    clearCallEnd()
    paintUnderOrb()
    const p = presence && typeof presence.get === 'function' ? presence.get() : null
    const st = voiceState(p)
    const action = voiceAction(seat, st)

    // §4.10 ruling 2: while START is waiting for Agent to finish, this button
    // reads CANCEL and T calls the wait off instead of asking twice.
    if (seat === 'talk' && voicePending.talk && startWaiting()) {
      try { presence.cancelStart() } catch (err) { /* the wait is already gone */ }
      return
    }

    if (st.demo) {
      // DEMO moves the demo's own labels. Nothing is dispatched to Talk.
      if (seat === 'talk') demoVoice.call = demoVoice.call === 'off' ? 'on' : 'off'
      else if (seat === 'mute') demoVoice.muted = !demoVoice.muted
      else demoVoice.sleeping = !demoVoice.sleeping
      voiceMessage('DEMO · ' + action + ' was not sent to Talk')
      repaintVoice()
      return
    }

    const blocked = voiceBlocked(seat, st)
    if (blocked) { voiceMessage(blocked); return }

    startPending(seat, action)
    voiceMessage('')
    repaintVoice()

    let out = null
    try {
      out = presence.command(action)
    } catch (err) {
      clearPending(seat)
      voiceMessage('voice command failed: ' + (err && err.message ? err.message : err))
      repaintVoice()
      return
    }
    Promise.resolve(out).then(function (res) {
      // ok:true only means the ask left the building — the label still waits
      // for the bus to report the new state (or for the 6 s timeout).
      if (!res || res.ok !== true) {
        clearPending(seat)
        voiceMessage(res && res.reason ? res.reason : VOICE_TIMEOUT_MSG)
        repaintVoice()
      }
    }).catch(function (err) {
      clearPending(seat)
      voiceMessage('voice command failed: ' + (err && err.message ? err.message : err))
      repaintVoice()
    })
  }

  function paintVoiceButton(btn, seat, st) {
    if (!btn) return
    const pend = voicePending[seat]
    const label = voiceLabel(seat, st)
    // §4.10 ruling 2: a START that is waiting for Agent offers the way out.
    const waiting = seat === 'talk' && pend && pend.action === 'start' && startWaiting()
    const text = waiting ? 'CANCEL' : pend ? PENDING_WORDS[pend.action] : label
    if (btn.label.textContent !== text) btn.label.textContent = text
    const blocked = voiceBlocked(seat, st)
    btn.box.disabled = Boolean(blocked)
    btn.box.setAttribute('title', blocked
      ? blocked
      : st.demo
        ? 'DEMO · this does not touch Talk'
        : label.toLowerCase() + '  (' + VOICE_KEYS[seat] + ')')
    btn.box.setAttribute('aria-label', label)
    btn.box.classList.toggle('jv-live', voiceHot(seat, st) && !pend)
    btn.box.classList.toggle('jv-pending', Boolean(pend))
  }

  function paintVoice(p) {
    if (!el.vcTalk) return
    const st = voiceState(p)
    for (let i = 0; i < VOICE_SEATS.length; i += 1) {
      const seat = VOICE_SEATS[i]
      const pend = voicePending[seat]
      if (pend && voiceSettled(pend.action, st)) clearPending(seat)
    }
    paintVoiceButton(el.vcTalk, 'talk', st)
    paintVoiceButton(el.vcMute, 'mute', st)
    paintVoiceButton(el.vcSleep, 'sleep', st)
    if (el.voiceTag) {
      const tag = st.demo ? 'DEMO · these do not touch talk' : ''
      if (el.voiceTag.textContent !== tag) el.voiceTag.textContent = tag
      el.voiceTag.style.display = tag ? '' : 'none'
    }
    if (el.voiceBox) el.voiceBox.classList.toggle('jv-demo-on', st.demo)
    paintNotice(p)
  }

  // ---- painting ------------------------------------------------------------

  function dash(value) {
    return value === null || value === undefined || value === '' ? '—' : String(value)
  }

  function paintPresence(p) {
    if (!el.mode) return
    // §7.3 ruling 6 — ONE mode word on the glass. The scene is handed a copy
    // that says `working` while a tool runs; the display word, the VOICE pod's
    // reading and the statusbar chip read that same copy, so the screen can
    // never say `thinking` under an orb that is labelled WORKING. The raw
    // store reading survives in one place only: the drawer's VOICE pod, named
    // as the source reading.
    const view = jarvisWorkingPresence(p, lastData && lastData.activity) || p
    const derived = view.mode !== p.mode
    lastShownMode = view.mode
    el.mode.textContent = MODE_WORDS[view.mode] || view.mode
    const colors = typeof JARVIS_MODE_COLORS === 'object' && JARVIS_MODE_COLORS ? JARVIS_MODE_COLORS : {}
    if (colors[view.mode]) {
      el.mode.style.color = colors[view.mode]
      // the word glows in its own mode colour (SPEC §3b)
      el.mode.style.setProperty('--jv-mode-c', colors[view.mode])
    }
    el.live.textContent = p.live || (p.call === 'on' ? 'live' : 'call off')
    el.demo.style.display = p.demo ? '' : 'none'
    paintVoice(p)

    el.voice.value.textContent = (MODE_WORDS[view.mode] || view.mode) + ' · ' + p.call
    // Honest to the letter: 'relay' means Talk is in the floating HUD window
    // and these readings came across from there (SPEC §4.7). When the word
    // above was derived, the store's own reading is printed here beside it —
    // this pod is the source of truth for what the pipe actually said.
    el.voice.note.textContent = 'source ' + p.source.status + ' / ' + p.source.voice + ' / ' + p.source.mic +
      (derived ? ' · source mode ' + (MODE_WORDS[p.mode] || p.mode) : '')
    el.voice.box.classList.toggle('jv-dead', p.source.status === 'none' && !p.demo)

    // chips: what we can actually see of the voice pipe, in two words
    const src = p.source.status
    setChip(el.chipVoice, 'VOICE ' + String(src).toUpperCase(), src === 'none' ? 'alarm' : 'on')
    const listening = p.mode !== 'muted' && p.mode !== 'sleeping'
    setChip(
      el.chipMic,
      p.call !== 'on' ? 'MIC OFF' : listening ? 'MIC ON' : 'MIC MUTED',
      p.call !== 'on' ? 'off' : listening ? 'on' : 'alarm'
    )

    const rows = (p.captions || []).slice(-2)
    const labels = lastData && lastData.settings ? lastData.settings : {}
    const ownerLabel = String(labels.owner_label || 'Owner').toUpperCase()
    const agentLabel = String(labels.agent_name || 'Agent').toUpperCase()
    if (el.captions.childNodes.length !== rows.length) {
      el.captions.textContent = ''
      for (let i = 0; i < rows.length; i += 1) {
        const line = make('div', 'jv-cap')
        line.appendChild(make('span', null, rows[i].role === 'user' ? ownerLabel : agentLabel))
        line.appendChild(doc.createTextNode(rows[i].text))
        el.captions.appendChild(line)
      }
    } else {
      for (let i = 0; i < rows.length; i += 1) {
        const line = el.captions.childNodes[i]
        line.childNodes[0].textContent = rows[i].role === 'user' ? ownerLabel : agentLabel
        line.childNodes[1].nodeValue = rows[i].text
      }
    }
    for (let i = 0; i < el.captions.childNodes.length; i += 1) {
      el.captions.childNodes[i].classList.toggle('jv-new', i === el.captions.childNodes.length - 1)
    }
  }

  function statusClass(status) {
    return status === 'ok' ? 'ok' : status === 'unreachable' ? 'bad' : 'idle'
  }

  function rowsInto(node, rows) {
    node.textContent = ''
    for (let i = 0; i < rows.length; i += 1) {
      const line = make('div', 'jv-row')
      line.appendChild(make('i', statusClass(rows[i].status)))
      line.appendChild(make('b', null, rows[i].label))
      line.appendChild(make('em', null, rows[i].right || ''))
      node.appendChild(line)
    }
  }

  function paintData(d) {
    if (!el.connection) return
    const health = d.health || {}
    const settings = d.settings || null

    function sourceOn(id) {
      return !!settings && Array.isArray(settings.enabled_sources) && settings.enabled_sources.indexOf(id) >= 0
    }
    function boxOn(id, source) {
      if (!settings) return false
      if (Array.isArray(settings.enabled_boxes)) return settings.enabled_boxes.indexOf(id) >= 0
      return id === 'fleet' ? true : sourceOn(source)
    }
    function showBox(box, shown) {
      if (box && box.box) box.box.style.display = shown ? '' : 'none'
    }
    showBox(el.helpers, boxOn('agent_helpers', 'agent_helpers'))
    showBox(el.waiting, boxOn('waiting_on_you', 'agent_state'))
    showBox(el.flight, boxOn('agent_in_flight', 'agent_state'))
    showBox(el.jobs, boxOn('overnight_jobs', 'overnight_jobs'))
    showBox(el.meet, boxOn('next_meeting', 'next_meeting'))
    showBox(el.today, boxOn('today', 'today_plan'))
    showBox(el.spend, boxOn('spend', 'spend'))
    showBox(el.score, boxOn('scoreboard', 'one_thing_scoreboard'))
    showBox(el.agents, boxOn('fleet', ''))
    const agentName = settings && settings.agent_name ? String(settings.agent_name) : 'Agent'
    if (el.mainTitle) el.mainTitle.textContent = 'JARVIS MODE · ' + agentName.toUpperCase()
    const helperHead = el.helpers && el.helpers.box.querySelector ? el.helpers.box.querySelector('.jv-pod-h span') : null
    const flightHead = el.flight && el.flight.box.querySelector ? el.flight.box.querySelector('.jv-pod-h span') : null
    if (helperHead) helperHead.textContent = agentName.toUpperCase() + "'S HELPERS"
    if (flightHead) flightHead.textContent = agentName.toUpperCase() + ' IN FLIGHT'

    const conn = d.connection || {}
    el.connection.value.textContent = dash(conn.profile) + ' · ' + dash(conn.gateway)
    el.connection.note.textContent = conn.note
      ? String(conn.note)
      : dash(conn.model) + ' · backend ' + (conn.backend === 'ok' ? 'ok' : 'offline')
    el.connection.box.classList.toggle('jv-dead', conn.gateway !== 'open')
    // ONLINE means one thing only: the backend half answered.
    const backendOk = conn.backend === 'ok'
    setChip(el.chipOnline, backendOk ? 'ONLINE' : 'OFFLINE', backendOk ? 'on' : 'alarm')

    if (health.brains === 'unreachable') {
      el.brains.value.textContent = 'unreachable'
      el.brains.note.textContent = 'mcp catalog'
      el.brains.box.classList.add('jv-dead')
      setChip(el.chipBrains, 'BRAINS UNREACHABLE', 'alarm')
    } else {
      const brains = (d.brains || []).slice(0, 3)
      // "configured", never "connected": the MCP list proves the server is set up
      // and switched on, not that anything answered (SPEC §0 honesty rule).
      el.brains.value.textContent = brains.length ? String(brains.length) + ' configured' : '—'
      setChip(el.chipBrains, brains.length ? String(brains.length) + ' BRAINS' : '— BRAINS', brains.length ? 'on' : 'off')
      el.brains.note.textContent = ''
      rowsInto(el.brains.note, brains.map(function (b) {
        return { label: b.label, status: b.status, right: b.status }
      }))
      el.brains.box.classList.toggle('jv-dead', brains.length === 0)
    }

    paintRadar(d)
    paintPanel(localPanel || d.panel)
    paintTicker(d.events || [])
    paintNow(d)
    paintHelpers(d)
    paintAgentState(d)
    paintJobs(d)
    paintAgents(d)
    paintSystems(d)
    paintLeftRail()
    paintMeeting(d)
    paintToday(d)
    paintSpend(d)
    paintStreaks(d)
  }

  // ---- the §7.4 rail -------------------------------------------------------

  /** The NOW box. Everything it prints comes from `jarvisNowLines`, so the box
   *  is one layout and the words are testable without a browser. */
  function paintNow(d) {
    if (!el.nowLine) return
    const lines = jarvisNowLines(d && d.activity, Date.now(), railCaps(), d && d.settings)
    if (el.nowLine.textContent !== lines.line) el.nowLine.textContent = lines.line
    setText(el.nowDetail, lines.detail)
    if (el.nowMeta.textContent !== lines.meta) el.nowMeta.textContent = lines.meta
    el.nowMeta.classList.toggle('jv-warm', lines.metaState === 'warm')
    el.nowMeta.classList.toggle('jv-hot', lines.metaState === 'hot')
    setText(el.now.tag, lines.tag)
    setText(el.nowThought, lines.thought)
    setText(el.nowNeeds, lines.needsYou)

    if (el.nowChips) {
      el.nowChips.textContent = ''
      for (let i = 0; i < lines.chips.length; i += 1) {
        const chipEl = make('span', 'jv-subchip', lines.chips[i].label)
        if (lines.chips[i].status === 'done') chipEl.classList.add('jv-done')
        if (lines.chips[i].status === 'failed') chipEl.classList.add('jv-failed')
        el.nowChips.appendChild(chipEl)
      }
      el.nowChips.style.display = lines.chips.length ? '' : 'none'
    }
    if (el.nowRecent) {
      el.nowRecent.textContent = ''
      for (let i = 0; i < lines.recent.length; i += 1) {
        const row = make('div', 'jv-rrow' + (lines.recent[i].ok ? '' : ' jv-bad'))
        row.appendChild(make('b', null, lines.recent[i].text))
        row.appendChild(make('em', null, lines.recent[i].right))
        el.nowRecent.appendChild(row)
      }
      el.nowRecent.style.display = lines.recent.length ? '' : 'none'
    }
    underOrbLine = lines.underOrb
    paintUnderOrb()
  }

  /** This window's height, as the rail sees it. */
  function railHeight() {
    try {
      return (root && root.clientHeight) || (win && win.innerHeight) || 900
    } catch (err) { return 900 }
  }

  /** This window's width, and the rail multiplier it earns (§8 amendments C10). */
  function railWidth() {
    try {
      return (root && root.clientWidth) || (win && win.innerWidth) || 1440
    } catch (err) { return 1440 }
  }
  function railScale() { return jarvisRailScale(railWidth()) }

  /** How many STATE rows this window has room for (§7 amendment 5) — the rule
   *  itself is the pure `jarvisRailCaps` above, so it can be tested.
   *
   *  §8 amendments C10: THE LADDER COUNTS IN SCALED PIXELS. Every box on a
   *  scaled rail is about k times taller, so the height it is asked about is
   *  this window's height DIVIDED by k — 1440 px of glass at 1.4 buys what
   *  1029 px buys at 1. (Padding and gaps do not scale, so the real boxes come
   *  out a little shorter than that, which leaves the answer on the safe side
   *  of a cut rather than the wrong one.) */
  function railCaps() {
    return jarvisRailCaps(railHeight() / railScale())
  }

  /** WAITING ON YOU and AGENT IN FLIGHT. Backend offline or file missing: both
   *  boxes say `Agent's STATE unreachable` and dim — never rows with no age. */
  function paintAgentState(d) {
    if (!el.waitingRows) return
    const at = Date.now()
    const caps = railCaps()
    let state = jarvisStateRows(d && d.agentState, at, caps, openBriefId, currentTimezone())
    // second pass: the asks that fit are known now, so AGENT IN FLIGHT is given
    // exactly the rows left over rather than more than the box can draw
    const floor = Number(caps.flight) === 0 ? 0 : 1
    const left = Math.max(floor, Number(caps.rows) - state.waiting.length)
    if (state.status === 'ok' && state.flight.length > left) {
      state = jarvisStateRows(d && d.agentState, at,
        { waiting: caps.waiting, flight: left, brief: caps.brief }, openBriefId, currentTimezone())
    }
    const dead = state.status !== 'ok'
    el.waiting.box.classList.toggle('jv-dead', dead || state.waiting.length === 0)
    el.flight.box.classList.toggle('jv-dead', dead || state.flight.length === 0)
    setText(el.waiting.tag, dead ? '' : state.waiting.length + ' of ' + (state.waiting.length + state.waitingMore))
    // §7.4 — when the file cannot be read BOTH boxes say the same sentence, so
    // neither can be mistaken for "nothing to do". The backend's own reason,
    // when it gives one, rides in the header where the row count usually sits.
    setText(el.flight.tag, dead ? state.note : state.header)

    if (dead) {
      const agent = d && d.settings && d.settings.agent_name ? String(d.settings.agent_name) : 'Agent'
      stateRowsInto(el.waitingRows, [], agent + "'s STATE unreachable", 0, true)
      stateRowsInto(el.flightRows, [], agent + "'s STATE unreachable", 0, false)
      return
    }
    stateRowsInto(el.waitingRows, state.waiting, 'nothing is waiting on you', state.waitingMore, true)
    stateRowsInto(el.flightRows, state.flight, 'nothing else is in flight', state.flightMore, false)
  }

  /** §8.4 item 3 — a WAITING ON YOU row is a real button: it can be clicked,
   *  it can be reached with Tab, and Enter or Space opens it while it has the
   *  focus. It blurs itself the moment it is used, because the composer behind
   *  the overlay is Owner's typing seat — and because the chord keys
   *  (⌃⌥T and friends) must keep working right after a click. */
  function openRow(id) {
    openBriefId = String(id || '')
    if (lastData) {
      try { paintAgentState(lastData) } catch (err) { log('rail repaint failed: ' + (err && err.message ? err.message : err)) }
    }
  }

  function stateRowsInto(node, rows, emptyLine, more, clickable) {
    node.textContent = ''
    // no rows AND none held back is the only case that means "nothing here";
    // a collapsed box (§7 amendment 5) still has to say what it is holding
    if (!rows.length && !more) {
      node.appendChild(make('div', 'jv-empty', emptyLine))
      return
    }
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i]
      const wrap = make(clickable ? 'button' : 'div', 'jv-srow' + (row.open ? ' jv-open' : ''))
      if (clickable) {
        wrap.type = 'button'
        wrap.setAttribute('data-jv', 'row-' + row.id)
        wrap.setAttribute('aria-expanded', row.open ? 'true' : 'false')
        wrap.setAttribute('title', row.open ? 'Open · click another row to read that one' : 'Read this one in plain words')
        wrap.addEventListener('mousedown', function (event) {
          if (event && typeof event.preventDefault === 'function') event.preventDefault()
        })
        wrap.addEventListener('click', function (event) {
          if (event && typeof event.preventDefault === 'function') event.preventDefault()
          openRow(row.id)
          try { wrap.blur() } catch (err) { /* focus is a nicety, not a requirement */ }
        })
        wrap.addEventListener('keydown', function (event) {
          if (!event) return
          if (event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return
          const code = typeof event.code === 'string' ? event.code : ''
          if (code !== 'Enter' && code !== 'Space' && event.key !== 'Enter' && event.key !== ' ') return
          if (typeof event.preventDefault === 'function') event.preventDefault()
          if (typeof event.stopPropagation === 'function') event.stopPropagation()
          openRow(row.id)
        })
      }
      wrap.appendChild(make('div', 'jv-srow-t', row.title || row.text || '(no next step written)'))
      const meta = make('div', 'jv-srow-m')
      meta.appendChild(make('i', null, row.id))
      const due = make('em', row.overdue ? 'jv-over' : null, row.due)
      meta.appendChild(due)
      wrap.appendChild(meta)
      const lines = Array.isArray(row.lines) ? row.lines : []
      if (row.open && lines.length) {
        const brief = make('div', 'jv-brief')
        for (let k = 0; k < lines.length; k += 1) {
          const line = make('div', 'jv-brief-l' + (lines[k].missing ? ' jv-brief-none' : ''))
          if (lines[k].label) line.appendChild(make('i', null, lines[k].label))
          line.appendChild(make('span', null, lines[k].text))
          brief.appendChild(line)
        }
        wrap.appendChild(brief)
      }
      node.appendChild(wrap)
    }
    if (more > 0) node.appendChild(make('div', 'jv-more', '+' + more + ' more'))
  }

  /** AGENT'S HELPERS (§8.4 item 4). */
  function paintHelpers(d) {
    if (!el.helperRows) return
    const lines = jarvisHelperRows(d && d.agentHelpers, d && d.activity, Date.now(), railCaps())
    const dead = lines.status !== 'ok'
    el.helpers.box.classList.toggle('jv-dead', dead || (!lines.rows.length && !lines.more))
    setText(el.helpers.tag, dead ? lines.word : lines.header)
    el.helperRows.textContent = ''
    if (dead) {
      el.helperRows.appendChild(make('div', 'jv-empty', lines.note || 'helpers unreachable'))
      return
    }
    if (!lines.rows.length && !lines.more) {
      el.helperRows.appendChild(make('div', 'jv-empty', lines.empty))
      return
    }
    for (let i = 0; i < lines.rows.length; i += 1) {
      const row = lines.rows[i]
      const wrap = make('div', 'jv-hrow' + (row.state === 'running' ? ' jv-live-row' : '') +
        (row.state === 'failed' ? ' jv-bad' : ''))
      const head = make('div', 'jv-hrow-t')
      head.appendChild(make('b', null, row.text))
      if (row.tag) head.appendChild(make('em', null, row.tag))
      wrap.appendChild(head)
      if (row.meta) wrap.appendChild(make('div', 'jv-hrow-m', row.meta))
      if (row.sub) wrap.appendChild(make('div', 'jv-hrow-s', row.sub))
      el.helperRows.appendChild(wrap)
    }
    if (lines.more > 0) el.helperRows.appendChild(make('div', 'jv-more', '+' + lines.more + ' more'))
  }

  /** OVERNIGHT JOBS (§8.4 item 7). All green is one line. */
  function paintJobs(d) {
    if (!el.jobsRows) return
    const caps = railCaps()
    const lines = jarvisJobsLines(d && d.overnightJobs, Date.now(), caps, currentTimezone())
    const dead = lines.status !== 'ok'
    el.jobs.box.classList.toggle('jv-dead', dead || lines.allGreen)
    // §8 amendment B.5 — the header carries the status word and nothing else
    setText(el.jobs.tag, dead ? lines.word : '')
    el.jobsRows.textContent = ''
    setText(el.jobsNext, '')
    if (dead) {
      el.jobsLine.style.display = 'none'
      el.jobsRows.appendChild(make('div', 'jv-empty', lines.note || 'cron file unreachable'))
      return
    }
    el.jobsLine.style.display = ''
    // a night with nothing in it stays ONE line (§8.4 item 7), so the next run
    // waits for a box that already has a second line to sit under
    if (lines.empty) {
      setText(el.jobsOk, lines.empty)
      setText(el.jobsFailed, '')
      setText(el.jobsSince, '')
      return
    }
    setText(el.jobsOk, lines.headline)
    setText(el.jobsFailed, lines.failedWord)
    setText(el.jobsSince, lines.since)
    // the one-line form (a short window, §8.4 item 10) keeps the count and
    // gives up the list; the count still says how many failed
    if (caps.jobsLine === true) return
    for (let i = 0; i < lines.failed.length; i += 1) {
      const row = make('div', 'jv-rrow jv-bad')
      row.appendChild(make('b', null, lines.failed[i].text))
      row.appendChild(make('em', null, lines.failed[i].right))
      el.jobsRows.appendChild(row)
      if (lines.failed[i].sub) el.jobsRows.appendChild(make('div', 'jv-hrow-s', lines.failed[i].sub))
    }
    if (lines.more > 0) el.jobsRows.appendChild(make('div', 'jv-more', '+' + lines.more + ' more'))
    // last line of the box, under whatever the night left behind
    if (!lines.allGreen) setText(el.jobsNext, lines.next)
  }

  /** §8.4 item 10 — how many of the four left-rail boxes this window can hold.
   *  A box that stands down is counted in the rail's own `+n more` line, never
   *  dropped in silence. */
  function paintLeftRail() {
    if (!el.leftBoxes) return
    const asked = Number(railCaps().left) - (noticeShowing ? 1 : 0)
    const settings = lastData && lastData.settings
    const selected = function (id) {
      if (!settings || !Array.isArray(settings.enabled_boxes)) return true
      return settings.enabled_boxes.indexOf(id) >= 0
    }
    const chosen = []
    for (let i = 0; i < el.leftBoxes.length; i += 1) {
      if (selected(el.leftBoxIds[i])) chosen.push(i)
      else el.leftBoxes[i].style.display = 'none'
    }
    const room = Math.max(0, Math.min(chosen.length, asked))
    for (let i = 0; i < chosen.length; i += 1) {
      el.leftBoxes[chosen[i]].style.display = i < room ? '' : 'none'
    }
    const hidden = chosen.length - room
    setText(el.leftMore, hidden > 0 ? '+' + hidden + ' more' : '')
  }

  /** NEXT MEETING (§8.4 item 5). */
  function paintMeeting(d) {
    if (!el.meetBig) return
    const lines = jarvisMeetingLines(d && d.nextMeeting, Date.now(), railCaps(), currentTimezone())
    const dead = lines.status !== 'ok'
    el.meet.box.classList.toggle('jv-dead', dead || !!lines.empty)
    setText(el.meet.tag, dead ? lines.word : (lines.stale ? 'stale' : lines.calendar))
    el.meetBig.classList.toggle('jv-warm', lines.state === 'warm')
    el.meetBig.classList.toggle('jv-hot', lines.state === 'hot')
    if (dead) {
      setText(el.meetBig, lines.word || 'unreachable')
      // collapsed (a short window): the word alone, with the reason held back
      setText(el.meetTitle, railCaps().meetLine === true ? '' : (lines.note || ''))
      setText(el.meetMeta, '')
      el.meetLater.textContent = ''
      el.meetLater.style.display = 'none'
      return
    }
    if (lines.empty) {
      setText(el.meetBig, 'clear')
      setText(el.meetTitle, lines.empty)
      setText(el.meetMeta, '')
      el.meetLater.textContent = ''
      el.meetLater.style.display = 'none'
      return
    }
    setText(el.meetBig, lines.big)
    setText(el.meetTitle, lines.title)
    // §8.4 item 10 — the one-line form keeps the countdown and the title and
    // holds the time range and the calendar back
    setText(el.meetMeta, railCaps().meetLine === true ? ''
      : lines.range + (lines.calendar ? ' · ' + lines.calendar : ''))
    el.meetLater.textContent = ''
    for (let i = 0; i < lines.later.length; i += 1) {
      const row = make('div', 'jv-rrow')
      row.appendChild(make('b', null, lines.later[i].text))
      row.appendChild(make('em', null, lines.later[i].right))
      el.meetLater.appendChild(row)
    }
    el.meetLater.style.display = lines.later.length ? '' : 'none'
  }

  /** TODAY (§8.4 item 6) — the ONE lever is line 1 of this box now. */
  function paintToday(d) {
    if (!el.todayLever) return
    const health = (d && d.health) || {}
    const lines = jarvisTodayLines(d && d.todayPlan, d && d.lever, health.lever, Date.now(), railCaps())
    const dead = lines.status !== 'ok'
    setText(el.todayLever, lines.lever)
    el.today.box.classList.toggle('jv-dead', dead && !lines.lever)
    setText(el.today.tag, dead ? lines.word : lines.tag)
    if (el.today.tag) {
      el.today.tag.classList.toggle('jv-warm', !dead && lines.tagState === 'warn')
    }
    el.todayRows.textContent = ''
    if (dead) {
      setText(el.todayHead, lines.note || 'today unreachable')
      return
    }
    setText(el.todayHead, lines.headline || lines.empty)
    for (let i = 0; i < lines.items.length; i += 1) {
      const item = lines.items[i]
      // §8 amendment B.4 — the in-progress class is jv-live-ROW, as it is in
      // AGENT'S HELPERS: a bare .jv-live is the voice line's own class (mono,
      // wide-tracked, 10-theme.js), and the task text was inheriting it.
      const row = make('div', 'jv-titem' + (item.state === 'live' ? ' jv-live-row'
        : (item.state ? ' jv-' + item.state : '')))
      row.appendChild(make('b', null, item.mark))
      if (item.kind) row.appendChild(make('i', null, item.kind))
      row.appendChild(make('span', null, item.task))
      // §8 amendment C9 — a status word this plugin does not know is SHOWN,
      // beside the task it belongs to, rather than quietly read as something.
      if (item.raw) row.appendChild(make('em', null, item.raw))
      el.todayRows.appendChild(row)
    }
    if (lines.more > 0) el.todayRows.appendChild(make('div', 'jv-more', '+' + lines.more + ' more'))
  }

  /** SPEND (§8.4 item 8). */
  function paintSpend(d) {
    if (!el.spendBig) return
    const caps = railCaps()
    const lines = jarvisSpendLines(d && d.spend, d && d.voiceToday, caps)
    const dead = lines.status !== 'ok'
    setText(el.spendBig, lines.voice)
    setText(el.spendNote, lines.voiceNote)
    setText(el.spend.tag, dead ? lines.word : '')
    el.spend.box.classList.toggle('jv-dead', dead)
    el.spendRows.textContent = ''
    if (dead) {
      setText(el.spendTotal, caps.spendLine === true ? '' : (lines.note || 'model spend unreachable'))
      setText(el.spendCost, '')
      return
    }
    // §8.4 item 10 — the one-line form. A short window keeps the call clock
    // (the number Jarvis measured itself) and holds the model list, the totals
    // and the cost line back rather than cutting any of them.
    if (caps.spendLine === true) {
      setText(el.spendTotal, '')
      setText(el.spendCost, '')
      return
    }
    for (let i = 0; i < lines.models.length; i += 1) {
      const row = make('div', 'jv-rrow')
      row.appendChild(make('b', null, lines.models[i].text))
      row.appendChild(make('em', null, lines.models[i].right))
      el.spendRows.appendChild(row)
    }
    if (lines.more > 0) el.spendRows.appendChild(make('div', 'jv-more', '+' + lines.more + ' more'))
    setText(el.spendTotal, lines.total)
    setText(el.spendCost, lines.cost)
  }

  /** SCOREBOARD (§8.4 item 9) — one line when the file is old, and one line
   *  when the window is short; only the first of those is tagged stale. */
  function paintStreaks(d) {
    if (!el.scoreBig) return
    const lines = jarvisStreakLines(d && d.streaks, Date.now(), railCaps(), currentTimezone())
    const dead = lines.status !== 'ok'
    // §8 amendments D1 — the header says `stale` only when the READING is
    // stale. The space-saving one-line form is a healthy scoreboard in a short
    // window: no tag, and no dimming either — nothing about it is dead.
    const stale = lines.collapsedWhy === 'stale'
    el.score.box.classList.toggle('jv-dead', dead || stale)
    setText(el.score.tag, dead ? lines.word : (stale ? 'stale' : ''))
    if (lines.collapsed) {
      el.scoreBig.style.display = 'none'
      el.scoreLabel.style.display = 'none'
      setText(el.scoreSecond, '')
      el.scoreDays.textContent = ''
      setText(el.scoreLine, lines.line)
      return
    }
    el.scoreBig.style.display = ''
    el.scoreLabel.style.display = ''
    setText(el.scoreBig, lines.big)
    setText(el.scoreLabel, lines.bigLabel)
    setText(el.scoreSecond, lines.second)
    setText(el.scoreLine, '')
    el.scoreDays.textContent = ''
    for (let i = 0; i < lines.days.length; i += 1) {
      const day = lines.days[i]
      const cell = make('span', 'jv-day')
      cell.appendChild(make('i', 'b-' + day.build))
      cell.appendChild(make('i', 'c-' + day.content))
      cell.appendChild(make('em', null, day.label))
      el.scoreDays.appendChild(cell)
    }
  }

  /** AGENTS AT WORK — today's JOBS and FLEET readings in one box: who is busy
   *  by name, what is running, and how many agents are idle. */
  function paintAgents(d) {
    if (!el.agentRows) return
    const lines = jarvisAgentLines(d)
    if (lines.status === 'unreachable') {
      el.agentBusy.textContent = 'unreachable'
      el.agentIdle.textContent = 'profiles.list · session.active_list'
      el.agentRows.textContent = ''
      el.agents.box.classList.add('jv-dead')
      setText(el.agents.tag, '')
      return
    }
    el.agentBusy.textContent = lines.busy.length ? lines.busy.join(' · ') : 'nobody is working'
    el.agentIdle.textContent = lines.idle
    setText(el.agents.tag, lines.jobs.length ? lines.jobs.length + ' running' : '')
    el.agentRows.textContent = ''
    for (let i = 0; i < lines.jobs.length; i += 1) {
      const row = make('div', 'jv-rrow')
      row.appendChild(make('b', null, lines.jobs[i].label))
      row.appendChild(make('em', null, lines.jobs[i].status))
      el.agentRows.appendChild(row)
    }
    el.agents.box.classList.toggle('jv-dead', !lines.busy.length && !lines.jobs.length)
  }

  /** SYSTEMS — one row of dots, the same readings the drawer's pods print. */
  function paintSystems(d) {
    if (!el.sysRow) return
    const p = presence && typeof presence.get === 'function' ? presence.get() : null
    const dots = jarvisSystemDots(d, p)
    // the row is rebuilt only when a dot actually changed: presence paints at
    // 10 Hz and seven nodes a frame is churn nobody can see
    let key = ''
    for (let i = 0; i < dots.length; i += 1) key += dots[i].label + dots[i].state + '|'
    if (key === lastSysKey) return
    lastSysKey = key
    el.sysRow.textContent = ''
    let worst = 'ok'
    for (let i = 0; i < dots.length; i += 1) {
      const dot = make('span', 'jv-sysdot ' + dots[i].state)
      dot.appendChild(make('i'))
      dot.appendChild(make('span', null, dots[i].label))
      el.sysRow.appendChild(dot)
      if (dots[i].state === 'bad') worst = 'bad'
      else if (dots[i].state === 'warn' && worst !== 'bad') worst = 'warn'
    }
    setText(el.systems.tag, worst === 'bad' ? 'something is down' : worst === 'warn' ? 'watch' : 'all green')
  }

  // Blips ARE the live session count. The count itself only exists for the
  // profile this gateway is routed to (30-data.js keeps every other profile
  // null rather than guessing), so a missing count says "no signal" out loud.
  function liveSessionCount(d) {
    const health = d.health || {}
    if (health.jobs === 'unreachable' || health.fleet === 'unreachable') return null
    const fleet = d.fleet || []
    let total = null
    for (let i = 0; i < fleet.length; i += 1) {
      const n = fleet[i] ? fleet[i].sessions : null
      if (typeof n === 'number' && isFinite(n)) total = (total === null ? 0 : total) + n
    }
    return total
  }

  function paintRadar(d) {
    if (!el.blips || !el.scan) return
    const count = liveSessionCount(d)
    const shown = count === null ? 0 : Math.min(count, BLIP_CAP)
    for (let i = 0; i < el.blips.length; i += 1) {
      el.blips[i].style.display = i < shown ? '' : 'none'
    }
    el.scan.value.textContent = count === null ? 'no signal' : String(count)
    el.scan.note.textContent = count === null
      ? 'sessions · gateway quiet'
      : count > BLIP_CAP ? 'sessions · 6 shown' : 'sessions'
    el.scan.box.classList.toggle('jv-dead', count === null)
  }

  function paintPanel(panel) {
    if (!el.panel) return
    if (!panel || !panel.title) {
      el.panel.style.display = 'none'
      return
    }
    if (panel.at && panel.ttl && Date.now() - panel.at > panel.ttl * 1000) {
      el.panel.style.display = 'none'
      if (localPanel && localPanel.id === panel.id) localPanel = null
      return
    }
    el.panelTitle.textContent = panel.title
    el.panelBody.textContent = panel.body || ''
    el.panel.style.display = ''
  }

  function paintTicker(events) {
    if (!el.track || !events.length) return
    const newest = events[events.length - 1]
    const stamp = newest ? newest.at : 0
    if (stamp === lastEventStamp) return
    lastEventStamp = stamp
    el.track.textContent = ''
    const line = events.slice(-40)
    for (let copy = 0; copy < 2; copy += 1) {
      for (let i = 0; i < line.length; i += 1) {
        const span = make('span')
        span.appendChild(make('b', null, line[i].type))
        span.appendChild(doc.createTextNode(line[i].text ? '  ' + line[i].text : ''))
        el.track.appendChild(span)
      }
    }
  }

  function paintClock() {
    if (!el.clock) return
    el.clock.textContent = jarvisClockReadout(Date.now(), currentTimezone())
  }

  // ---- presence → scene + backend -----------------------------------------

  function onPresence(p) {
    if (!open) return
    // §7.3 ruling 6 — the scene gets `working` instead of `thinking` while a
    // tool is actually running. The store is untouched; this copy dies here.
    if (scene && typeof scene.setPresence === 'function') {
      scene.setPresence(jarvisWorkingPresence(p, lastData && lastData.activity))
    }
    const at = Date.now()
    if (at - lastText >= TEXT_HZ_MS) {
      lastText = at
      try {
        paintPresence(p)
      } catch (err) {
        log('overlay paint failed: ' + (err && err.message ? err.message : err))
      }
    }
    if (at - lastPush >= PUSH_HZ_MS && at >= pushBlockedUntil) {
      lastPush = at
      pushPresence(p)
    }
  }

  function pushPresence(p) {
    if (data && typeof data.pushPresence === 'function') {
      data.pushPresence(p)
      return
    }
  }

  function onData(d) {
    if (!open) return
    lastData = d
    if (scene && typeof scene.setData === 'function') scene.setData(d)
    try {
      paintData(d)
    } catch (err) {
      log('overlay data paint failed: ' + (err && err.message ? err.message : err))
    }
    // §7.3 ruling 6 — the derived word lives on `activity`, which arrives
    // here, not on the presence frame. If this frame changed it, the display
    // word, the VOICE reading and the scene are brought level at once.
    try {
      const p = presence && typeof presence.get === 'function' ? presence.get() : null
      if (!p) return
      const view = jarvisWorkingPresence(p, d && d.activity) || p
      // Data carries the configured agent and owner labels. Presence can land
      // first during boot, so repaint its captions even when the mode did not
      // change; otherwise the initial generic labels can remain on screen.
      if (view.mode !== lastShownMode && scene && typeof scene.setPresence === 'function') scene.setPresence(view)
      paintPresence(p)
    } catch (err) {
      log('overlay mode repaint failed: ' + (err && err.message ? err.message : err))
    }
  }

  /** §7.3 ruling 5 — the clock-driven half of the NOW box (elapsed, "no news
   *  for", the line under the orb), once a second. It rides the clock timer
   *  that only exists while the overlay is open, and does nothing at all when
   *  no turn is running: no busy loop, ever. */
  function tickNow() {
    if (!open || !el.nowLine) return
    const act = lastData && lastData.activity
    if (!act || act.running !== true) return
    try {
      paintNow(lastData)
    } catch (err) {
      log('now paint failed: ' + (err && err.message ? err.message : err))
    }
  }

  // ---- its own window, full screen, the drawer (SPEC §7.2) -----------------

  /** The one place a §7.2 line reaches Owner: the band under the DEMO badge,
   *  and the app's own toast when the overlay is about to close behind it. */
  function showNotice(text, alsoToast) {
    if (el.notice) {
      if (noticeTimer) { timerClear(noticeTimer); noticeTimer = null }
      setText(el.notice, text)
      noticeShowing = Boolean(text)
      paintLeftRail()
      if (text) {
        noticeTimer = timerSet(function () {
          noticeTimer = null
          if (el.notice) setText(el.notice, '')
          noticeShowing = false
          paintLeftRail()
        }, NOTICE_MS)
      }
    }
    if (text) log('window: ' + text)
    // with the overlay closed (the palette row) the toast is the only place a
    // line can land, so it always goes there
    if (text && (alsoToast || !open)) {
      try {
        const SDK = opts.HermesSDK || (typeof HermesSDK !== 'undefined' ? HermesSDK : null)
        if (SDK && SDK.host && typeof SDK.host.notify === 'function') {
          SDK.host.notify({ kind: 'info', message: text })
        }
      } catch (err) { /* toasts are optional; the line above is not */ }
    }
  }

  /** Is there any door to a second Hermes window from here? */
  function canOwnWindow() {
    if (typeof opts.openWindow === 'function') return true
    try {
      const bridge = win ? win.hermesDesktop : null
      return Boolean(bridge && typeof bridge.openWindow === 'function')
    } catch (err) {
      return false
    }
  }

  /** Ask the host for a peer window. 60-plugin.js injects `openWindow` (it
   *  carries this window's connection and profile); the bridge itself is the
   *  fallback for a build where it does not. Always resolves {ok, reason}. */
  function openPeerWindow() {
    if (typeof opts.openWindow === 'function') {
      try {
        return Promise.resolve(opts.openWindow()).then(function (res) {
          return { ok: Boolean(res && res.ok === true), reason: (res && res.reason) || '' }
        }, function (err) {
          return { ok: false, reason: String(err && err.message ? err.message : err) }
        })
      } catch (err) {
        return Promise.resolve({ ok: false, reason: String(err && err.message ? err.message : err) })
      }
    }
    let bridge = null
    try {
      bridge = win ? win.hermesDesktop : null
    } catch (err) { bridge = null }
    if (!bridge || typeof bridge.openWindow !== 'function') {
      return Promise.resolve({ ok: false, reason: 'no openWindow bridge' })
    }
    try {
      return Promise.resolve(bridge.openWindow()).then(function (res) {
        return { ok: Boolean(res && res.ok !== false), reason: (res && res.error) || '' }
      }, function (err) {
        return { ok: false, reason: String(err && err.message ? err.message : err) }
      })
    } catch (err) {
      return Promise.resolve({ ok: false, reason: String(err && err.message ? err.message : err) })
    }
  }

  function bootFlagWrite(value) {
    try {
      const store = win ? win.localStorage : null
      if (!store) return
      const key = jarvisScopedKey(getScope(), BOOT_KEY)
      if (!key) return
      if (value === null) store.removeItem(key)
      else store.setItem(key, String(value))
    } catch (err) { /* a window without storage still opens, it just will not
                       auto-open the overlay over there */ }
  }

  /** SPEC §7.2 rulings 1 and 3 — W, the palette row and the top-chrome button
   *  all land here. One microphone, one call: a live call refuses. */
  function pressOwnWindow() {
    const p = presence && typeof presence.get === 'function' ? presence.get() : null
    // the REAL call, not the demo's label machine — demo never had a call
    if (p && p.call === 'on') {
      showNotice(OWN_WINDOW_CALL_ON, false)
      return
    }
    if (!canOwnWindow()) {
      showNotice(OWN_WINDOW_NO_BRIDGE, false)
      return
    }
    // the flag goes down BEFORE the ask, so the new window finds it however
    // fast it boots; a refusal takes it straight back up again
    bootFlagWrite(Date.now())
    openPeerWindow().then(function (res) {
      if (res && res.ok) {
        showNotice(OWN_WINDOW_OK, true)
        doClose()
        return
      }
      bootFlagWrite(null)
      showNotice(OWN_WINDOW_NO_BRIDGE, false)
      if (res && res.reason) log('own window refused: ' + res.reason)
    })
  }

  function isFullscreen() {
    try {
      return Boolean(doc && (doc.fullscreenElement || doc.webkitFullscreenElement))
    } catch (err) {
      return false
    }
  }

  /** SPEC §7.2 ruling 4 — F and the button. A refusal is a quiet line, never
   *  a throw, and Esc's first press leaves full screen (see the key handler). */
  function toggleFullscreen() {
    if (!doc) return
    try {
      if (isFullscreen()) {
        const exit = doc.exitFullscreen || doc.webkitExitFullscreen
        if (typeof exit !== 'function') { showNotice(FULLSCREEN_FAILED, false); return }
        Promise.resolve(exit.call(doc)).catch(function () { showNotice(FULLSCREEN_FAILED, false) })
        return
      }
      const target = doc.documentElement
      const request = target && (target.requestFullscreen || target.webkitRequestFullscreen)
      if (typeof request !== 'function') { showNotice(FULLSCREEN_FAILED, false); return }
      Promise.resolve(request.call(target)).catch(function () { showNotice(FULLSCREEN_FAILED, false) })
    } catch (err) {
      showNotice(FULLSCREEN_FAILED, false)
    }
  }

  function paintChrome() {
    if (el.chromeFull) {
      const full = isFullscreen()
      const text = full ? 'LEAVE FULL' : 'FULL SCREEN'
      if (el.chromeFull.label.textContent !== text) el.chromeFull.label.textContent = text
    }
    if (el.chromeOwn) el.chromeOwn.box.disabled = !canOwnWindow()
    if (el.chromeDiag) {
      const text = drawerOpen ? 'HIDE SYSTEMS' : 'SYSTEMS'
      if (el.chromeDiag.label.textContent !== text) el.chromeDiag.label.textContent = text
    }
  }

  /** SPEC §7.4 — ⌃⌥D (and a click on SYSTEMS) swaps the rail for today's
   *  instrument pods. They are painted either way, so nothing is ever stale. */
  function toggleDrawer(force) {
    drawerOpen = force === undefined ? !drawerOpen : Boolean(force)
    if (el.drawer) el.drawer.style.display = drawerOpen ? '' : 'none'
    if (el.right) el.right.style.display = drawerOpen ? 'none' : ''
    paintChrome()
  }

  function measure() {
    if (!root) return
    const w = root.clientWidth || (win ? win.innerWidth : 0)
    const h = root.clientHeight || (win ? win.innerHeight : 0)
    if (scene && typeof scene.setSize === 'function') {
      scene.setSize(w, h, (win && win.devicePixelRatio) || 1)
    }
    // §8 amendments C10 — the rail multiplier is a reading of the window's
    // WIDTH, published as one custom property the stylesheet does the rest
    // with. Written before the re-cut below, because the caps are counted in
    // the pixels it decides.
    const k = jarvisRailScale(w)
    if (k !== lastRailK) {
      lastRailK = k
      try {
        if (root.style && typeof root.style.setProperty === 'function') {
          root.style.setProperty('--jv-rail-k', String(k))
        }
      } catch (err) { /* a shell without inline styles keeps the 1 in the CSS */ }
      lastRailH = 0                 // the rung is counted in new pixels now
    }
    // §7 amendment 5 — the row caps are a reading of the window's height, so a
    // resize has to re-cut the rail then and there. Without this the boxes keep
    // the rows the LAST size allowed until the next 60 s poll lands, and that
    // is exactly when a row gets cut.
    if (h !== lastRailH) {
      lastRailH = h
      if (open && lastData && el.waitingRows) {
        try {
          // §8.4 item 10 — BOTH rails are cut by height, so both are re-cut
          // here: the NOW history, the STATE rows, the helper rows, the failed
          // jobs, and the one-line forms of SPEND and SCOREBOARD.
          paintNow(lastData)
          paintHelpers(lastData)
          paintAgentState(lastData)
          paintJobs(lastData)
          paintLeftRail()
          paintMeeting(lastData)
          paintToday(lastData)
          paintSpend(lastData)
          paintStreaks(lastData)
        } catch (err) {
          log('rail re-cut failed: ' + (err && err.message ? err.message : err))
        }
      }
    }
  }

  // ---- lifecycle -----------------------------------------------------------

  function doOpen() {
    if (open || !doc || !doc.body) return
    injectStyle()
    if (!root) build()
    doc.body.appendChild(root)
    open = true
    restoreFocus = doc.activeElement && typeof doc.activeElement.focus === 'function' ? doc.activeElement : null

    try {
      scene = sceneFactory
        ? sceneFactory(el.canvas, { reducedMotion: reduced(), dpr: (win && win.devicePixelRatio) || 1 })
        : stubScene(el.canvas)
    } catch (err) {
      log('scene failed, using the stub: ' + (err && err.message ? err.message : err))
      scene = stubScene(el.canvas)
    }
    measure()
    if (scene && typeof scene.start === 'function') scene.start()

    if (presence && typeof presence.subscribe === 'function') offPresence = presence.subscribe(onPresence)
    if (data && typeof data.subscribe === 'function') offData = data.subscribe(onData)
    if (presence && typeof presence.get === 'function') onPresence(presence.get())
    if (data && typeof data.get === 'function') onData(data.get())

    paintClock()
    clockTimer = setInterval(function () { paintClock(); tickNow() }, 1000)

    // The telemetry strip moves because a clock moves, never because a voice
    // does (SPEC §0 law 1). Reduced motion gets one still frame.
    teleStart = Date.now()
    paintTelemetry()
    if (!reduced()) teleTimer = setInterval(paintTelemetry, TELE_MS)

    onKey = function (event) {
      if (event.key === 'Escape') {
        // §7.2 ruling 4: the FIRST Esc leaves full screen and leaves the
        // overlay standing. Only an Esc in a window that is not full screen
        // closes it.
        if (isFullscreen()) {
          event.preventDefault()
          event.stopPropagation()
          toggleFullscreen()
          return
        }
        event.preventDefault()
        event.stopPropagation()
        doClose()
        return
      }
      // SPEC §8.1 — KEYS NEED A CHORD. Control+Option/Alt with T talk, M mute,
      // Z sleep, W own window, F full screen, D drawer, and a BARE letter does
      // nothing in every state: Owner typed a T on another screen on
      // 2026-09-19 and his call ended.
      //
      // The SAME two physical keys on either main computer — Control and
      // Alt/Option — which is `ctrlKey && altKey` to every browser. Only the
      // printed label differs (KEYS, above), so nothing here needs to know
      // which computer it is running on.
      //
      // Matched on `event.code`, never on `event.key`: the modifier rewrites
      // the letter (on macOS ⌥T arrives as "†" and ⌥Z as "Ω"; a Windows AltGr
      // layout rewrites it too), so the letter is only safe to read off the
      // physical key. EXACTLY ctrl+alt — a Command/Windows key or a Shift on
      // top belongs to somebody else, and the host's own open chord is left
      // alone. Space and Enter are never taken, and the caret guard below still
      // stands, which is also what keeps an AltGr typist out of here: they are
      // typing into a field, and fields are skipped.
      if (!event.ctrlKey || !event.altKey || event.metaKey || event.shiftKey) return
      const code = typeof event.code === 'string' ? event.code : ''
      const seat = code === 'KeyT' ? 'talk' : code === 'KeyM' ? 'mute' : code === 'KeyZ' ? 'sleep' : ''
      const window_ = code === 'KeyW' ? 'own' : code === 'KeyF' ? 'full' : code === 'KeyD' ? 'drawer' : ''
      if (!seat && !window_) return
      const target = event.target || null
      const tag = target && target.tagName ? String(target.tagName).toUpperCase() : ''
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
      if (target && target.isContentEditable) return
      event.preventDefault()
      event.stopPropagation()
      // §8.2 ruling 4: the call-end line lives until the next press or chord.
      // This is the chord.
      clearCallEnd()
      paintUnderOrb()
      if (seat) { pressVoice(seat); return }
      if (window_ === 'own') pressOwnWindow()
      else if (window_ === 'full') toggleFullscreen()
      else toggleDrawer()
    }
    doc.addEventListener('keydown', onKey, true)

    // the FULL SCREEN button follows the window, however it got there (the
    // green button, the menu, Esc, another plugin)
    onFullscreen = function () { paintChrome() }
    try {
      doc.addEventListener('fullscreenchange', onFullscreen)
      doc.addEventListener('webkitfullscreenchange', onFullscreen)
    } catch (err) { onFullscreen = null }
    paintChrome()

    if (win && typeof win.ResizeObserver === 'function') {
      try {
        resizeObs = new win.ResizeObserver(measure)
        resizeObs.observe(root)
      } catch (err) {
        resizeObs = null
      }
    }
    if (!resizeObs && win) {
      onResize = measure
      win.addEventListener('resize', onResize)
    }

    try {
      root.focus()
    } catch (err) { /* focus is a nicety, not a requirement */ }
  }

  function doClose() {
    if (!open) return
    open = false
    // §4.10 amendment 2 — CLOSING CANCELS A WAITING START. A per-minute call
    // must never come on behind a closed dashboard: whatever START was standing
    // by for, it stops here.
    if (presence && typeof presence.cancelStart === 'function') {
      try { presence.cancelStart() } catch (err) { /* nothing was waiting */ }
    }
    if (offPresence) { offPresence(); offPresence = null }
    if (offData) { offData(); offData = null }
    if (clockTimer) { clearInterval(clockTimer); clockTimer = null }
    if (teleTimer) { clearInterval(teleTimer); teleTimer = null }
    clearAllPending()
    if (noticeTimer) { timerClear(noticeTimer); noticeTimer = null }
    if (onKey && doc) { doc.removeEventListener('keydown', onKey, true); onKey = null }
    if (onFullscreen && doc) {
      try {
        doc.removeEventListener('fullscreenchange', onFullscreen)
        doc.removeEventListener('webkitfullscreenchange', onFullscreen)
      } catch (err) { /* gone */ }
      onFullscreen = null
    }
    // the drawer never survives a close: the rail is what opens next time
    toggleDrawer(false)
    lastSysKey = ''
    lastShownMode = ''
    lastRailH = 0              // the next open re-cuts the rail for its window
    lastRailK = 0              // …at whatever scale that window's width earns
    if (resizeObs) { try { resizeObs.disconnect() } catch (err) { /* gone */ } resizeObs = null }
    if (onResize && win) { win.removeEventListener('resize', onResize); onResize = null }
    if (scene) {
      try {
        if (typeof scene.stop === 'function') scene.stop()
        if (typeof scene.destroy === 'function') scene.destroy()
      } catch (err) { /* a dead scene cannot block the close */ }
      scene = null
    }
    if (root && root.parentNode) root.parentNode.removeChild(root)
    lastEventStamp = 0
    if (restoreFocus) {
      try { restoreFocus.focus() } catch (err) { /* the app took it back already */ }
      restoreFocus = null
    }
  }

  return {
    open: doOpen,
    close: doClose,
    toggle: function () { if (open) doClose(); else doOpen() },
    isOpen: function () { return open },
    // §7.2: the palette row and the title-bar menu press the same button W does
    ownWindow: pressOwnWindow,
    fullScreen: toggleFullscreen,
    diagnostics: function (force) { if (open) toggleDrawer(force) },
    showPanel: function (panel) {
      if (!panel || !panel.title) { localPanel = null } else {
        localPanel = {
          id: String(panel.id || panel.title),
          title: String(panel.title),
          body: String(panel.body || ''),
          kind: String(panel.kind || 'card'),
          ttl: Number(panel.ttl_s || panel.ttl) || 20,
          at: Number(panel.at) || Date.now()
        }
      }
      if (open) paintPanel(localPanel)
    },
    destroy: function () {
      doClose()
      root = null
      el = {}
      teleBars = []
      lastData = null
      const style = doc && doc.getElementById ? doc.getElementById('jv-style') : null
      if (style && style.parentNode) style.parentNode.removeChild(style)
    }
  }
}
