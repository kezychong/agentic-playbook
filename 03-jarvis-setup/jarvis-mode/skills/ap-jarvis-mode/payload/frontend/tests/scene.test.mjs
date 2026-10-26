/* tests/scene.test.mjs — node --test tests/scene.test.mjs
 *
 * 40-scene.js is a PURE module (no import/export) that the build concatenates.
 * We load it with fs.readFileSync + new Function so the test exercises the very
 * bytes that ship, with every browser global explicitly undefined.
 */
import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(here, '..', 'src', '40-scene.js');

function loadScene() {
  const src = fs.readFileSync(SRC, 'utf8');
  const factory = new Function(
    'window', 'document', 'requestAnimationFrame', 'cancelAnimationFrame', 'matchMedia', 'performance',
    src + '\n;return { createScene, jarvisSceneStep, jarvisSceneSnapshot, jarvisBrainPos, JARVIS_SCENE_TOKENS, JARVIS_LOOK, JARVIS_EASE };'
  );
  return factory(undefined, undefined, undefined, undefined, undefined, undefined);
}
const M = loadScene();
const L = M.JARVIS_LOOK;

/* ------------------------------------------------------------ fake canvas -- */
function makeCanvas(w, h) {
  const calls = [];
  const paints = [];                  // [kind, strokeStyle|fillStyle, lineWidth]
  const grads = [];                   // every gradient made, with its stops
  const rec = (name) => (...args) => { calls.push([name, ...args]); };
  const mkGrad = (kind) => (...args) => {
    const g = { kind, args, stops: [], addColorStop(p, c) { this.stops.push([p, c]); } };
    grads.push(g);
    return g;
  };
  const ctx = {
    calls, paints, grads,
    setTransform: rec('setTransform'), clearRect: rec('clearRect'), fillRect: rec('fillRect'),
    beginPath: rec('beginPath'), moveTo: rec('moveTo'), lineTo: rec('lineTo'), arc: rec('arc'),
    ellipse: rec('ellipse'), clip: rec('clip'), quadraticCurveTo: rec('quadraticCurveTo'),
    setLineDash: rec('setLineDash'), fillText: rec('fillText'),
    save: rec('save'), restore: rec('restore'),
    translate: rec('translate'), rotate: rec('rotate'),
    // stroke/fill also record the style in force, so a test can ask what
    // COLOUR something was painted in (Look v1.1 cares: cobalt in, coral out)
    stroke: (...a) => { calls.push(['stroke', ...a]); paints.push(['stroke', ctx.strokeStyle, ctx.lineWidth]); },
    fill : (...a) => { calls.push(['fill', ...a]); paints.push(['fill', ctx.fillStyle, ctx.lineWidth]); },
    measureText: (t) => ({ width: String(t).length * 6 }),
    createRadialGradient: mkGrad('radial'),
    createLinearGradient: mkGrad('linear')
  };
  return {
    width: w, height: h, clientWidth: w, clientHeight: h, style: {},
    getContext: (k) => (k === '2d' ? ctx : null),
    __ctx: ctx
  };
}
const painted = (canvas, kind, rgb) =>
  canvas.__ctx.paints.filter((p) => p[0] === kind && String(p[1]).indexOf('rgba(' + rgb + ',') === 0).length;

/** every arc drawn concentric with Agent, as radii */
const agentArcs = (canvas, g) => canvas.__ctx.calls
  .filter((c) => c[0] === 'arc' && Math.abs(c[1] - g.cx) < 0.5 && Math.abs(c[2] - g.cy) < 0.5)
  .map((c) => c[3]);
/** the alpha of an `rgba(r,g,b,a)` string */
const alphaOf = (s) => {
  const m = /rgba\([^,]+,[^,]+,[^,]+,\s*([0-9.]+)\)/.exec(String(s));
  return m ? parseFloat(m[1]) : 0;
};

/* --------------------------------------------------------------- fixtures -- */
const DATA = {
  brains: [
    { id: 'brain-1', label: 'Brain 1', status: 'ok' },
    { id: 'brain-2', label: 'Brain 2', status: 'ok' },
    { id: 'brain-3', label: 'Brain 3', status: 'ok' }
  ],
  senses: [
    { id: 'screenpipe', label: 'Screenpipe', status: 'ok' },
    { id: 'plaud', label: 'Plaud', status: 'ok' },
    { id: 'skool', label: 'Skool', status: 'unreachable' },
    { id: 'slack', label: 'Slack', status: 'ok' }
  ],
  fleet: [
    { id: 'agent', label: 'Agent', busy: true },
    { id: 'helper-1', label: 'Helper 1', busy: false },
    { id: 'helper-2', label: 'Helper 2', busy: true }
  ]
};
const presence = (mode, levels, call = 'on', live = '') => ({
  call, mode, live, levels: { voice: 0, mic: 0, ...(levels || {}) },
  captions: [], source: { status: 'bus', voice: 'analyser', mic: 'tap' }, demo: false, updatedAt: 0
});

/** deterministic run: init -> apply data -> N steps of the same dt */
function run({ mode = 'speaking', levels = {}, call = 'on', steps = 120, dt = 33, seed = 7, reducedMotion = false, data = DATA, w = 1440, h = 900 } = {}) {
  let st = M.jarvisSceneStep({ w, h, seed, reducedMotion }, 0, presence(mode, levels, call), data);
  const p = presence(mode, levels, call);
  for (let i = 0; i < steps; i++) st = M.jarvisSceneStep(st, dt, p);
  return { st, snap: M.jarvisSceneSnapshot(st) };
}
const stripAgent = (s) => { const c = { ...s }; delete c.agent; return c; };
/** a settled scene: mode + voice held long enough for the 350 ms eases to land */
const settled = (o) => run({ steps: 200, ...o }).snap.agent;

/* ================================ THE LAW ================================= */
test('only Agent reacts to voice', () => {
  const hot = run({ levels: { voice: 0.9, mic: 0 } }).snap;
  const cold = run({ levels: { voice: 0.0, mic: 0 } }).snap;

  // the world layer is byte-identical: brains, links, packets, senses, fleet, stars
  assert.deepStrictEqual(stripAgent(hot), stripAgent(cold),
    'a voice level must not move anything except Agent');
  assert.deepStrictEqual(hot.brains, cold.brains);
  assert.deepStrictEqual(hot.links, cold.links);
  assert.deepStrictEqual(hot.senses, cold.senses);
  assert.deepStrictEqual(hot.fleet, cold.fleet);
  assert.strictEqual(hot.t, cold.t);

  // ...and Agent DOES react: bigger orb, brighter core, wider halo, faster plasma
  assert.notDeepStrictEqual(hot.agent, cold.agent);
  assert.ok(hot.agent.radius > cold.agent.radius * 1.18,
    `voice 0.9 must swell the orb (${hot.agent.radius} vs ${cold.agent.radius})`);
  assert.ok(hot.agent.radius <= cold.agent.idleRadius * 1.29, 'the swell is capped at idle x 1.28');
  assert.ok(hot.agent.brightness > cold.agent.brightness, 'voice must brighten the core');
  assert.ok(hot.agent.halo > cold.agent.halo, 'voice must open the halo');
  assert.ok(hot.agent.plasmaSpeed > cold.agent.plasmaSpeed, 'voice must speed the plasma');
});

test('only Agent reacts to mic: ripples spawn, world untouched', () => {
  const wet = run({ mode: 'listening', levels: { voice: 0, mic: 0.8 } }).snap;
  const dry = run({ mode: 'listening', levels: { voice: 0, mic: 0 } }).snap;
  assert.deepStrictEqual(stripAgent(wet), stripAgent(dry));
  assert.ok(wet.agent.ripples > 0, 'mic must draw inward ripples');
  assert.strictEqual(dry.agent.ripples, 0);
});

/* ============================ CONSTANT MOTION ============================= */
test('packets advance at a constant pace regardless of presence', () => {
  const cases = [
    run({ mode: 'speaking', levels: { voice: 1, mic: 1 } }).snap,
    run({ mode: 'idle', levels: { voice: 0, mic: 0 } }).snap,
    run({ mode: 'muted', levels: { voice: 0, mic: 0 }, call: 'off' }).snap
  ];
  assert.deepStrictEqual(cases[0].links, cases[1].links);
  assert.deepStrictEqual(cases[1].links, cases[2].links);

  // and they really are moving, at a linear rate
  const a = run({ steps: 30 }).snap, b = run({ steps: 60 }).snap, c = run({ steps: 90 }).snap;
  const p = (s) => s.links[0].packets[0];
  const d1 = (p(b) - p(a) + 1) % 1, d2 = (p(c) - p(b) + 1) % 1;
  assert.ok(d1 > 0.001, 'packets must move');
  assert.ok(Math.abs(d1 - d2) < 1e-9, `constant speed (${d1} vs ${d2})`);

  // brain rings / senses orbit / fleet phase all advance too
  assert.ok(Math.abs(b.brains[0].ring) > 0);
  assert.ok(b.senses.orbit > 0);
  assert.ok(b.fleet[0].phase !== c.fleet[0].phase);
});

/* ============================== MODE COLOURS ============================== */
test('mode maps to the SPEC §3 colour', () => {
  const T = M.JARVIS_SCENE_TOKENS;
  const want = {
    idle: T.silver, listening: T.cyan, thinking: T.violet,
    speaking: T.cobaltBright, working: T.amber, muted: T.coral, sleeping: T.coral
  };
  for (const [mode, hex] of Object.entries(want)) {
    const s = run({ mode, steps: 150 }).snap;
    assert.strictEqual(s.agent.modeColour, hex, `${mode} -> ${hex}`);
    // the eased colour converges on the target (no snapping, but it gets there)
    const a = s.agent.colour.replace('#', ''), b = hex.replace('#', '').toUpperCase();
    for (let i = 0; i < 3; i++) {
      const d = Math.abs(parseInt(a.substr(i * 2, 2), 16) - parseInt(b.substr(i * 2, 2), 16));
      assert.ok(d <= 4, `${mode}: eased colour ${s.agent.colour} ~= ${hex}`);
    }
  }
  // off-call is dim silver whatever the mode says
  const off = run({ mode: 'speaking', call: 'off', steps: 150 }).snap;
  assert.strictEqual(off.agent.modeColour, T.silver);
  assert.ok(off.agent.brightness < 0.6, 'off-call orb is dim');
  assert.strictEqual(off.agent.arc, null, 'off-call never wears a thinking arc');
});

/* ============================= REDUCED MOTION ============================= */
test('reduced motion halves the speeds but never freezes', () => {
  const full = run({ steps: 90, reducedMotion: false }).snap;
  const half = run({ steps: 90, reducedMotion: true }).snap;
  assert.ok(half.t > 0, 'reduced motion must still advance');
  assert.ok(Math.abs(half.t - full.t / 2) < 1e-5, `t halved (${half.t} vs ${full.t})`);
  assert.ok(half.senses.orbit > 0 && Math.abs(half.senses.orbit - full.senses.orbit / 2) < 1e-5);
  const zero = run({ steps: 0 }).snap;
  const dFull = (full.links[0].packets[0] - zero.links[0].packets[0] + 1) % 1;
  const dHalf = (half.links[0].packets[0] - zero.links[0].packets[0] + 1) % 1;
  assert.ok(dHalf > 0, 'packets still move under reduced motion');
  assert.ok(Math.abs(dHalf - dFull / 2) < 1e-5, `packet speed halved (${dHalf} vs ${dFull})`);
});

/* =============================== HONESTY ================================== */
test('setData with an unreachable brain turns its packets off', () => {
  const data = { ...DATA, brains: DATA.brains.map((b, i) => (i === 1 ? { ...b, status: 'unreachable' } : b)) };
  let { st } = run({ data, steps: 40 });
  const s1 = M.jarvisSceneSnapshot(st);
  assert.strictEqual(s1.brains[1].status, 'unreachable');
  assert.strictEqual(s1.brains[1].dim, 0.35, 'unreachable dims to 35%');
  assert.strictEqual(s1.links[1].on, false);
  assert.strictEqual(s1.links[1].active, 0, 'no packets on an unreachable link');
  assert.strictEqual(s1.links[0].on, true);

  const frozen = s1.links[1].packets.slice(), moving = s1.links[0].packets.slice();
  const p = presence('speaking', { voice: 0.5 });
  for (let i = 0; i < 60; i++) st = M.jarvisSceneStep(st, 33, p);
  const s2 = M.jarvisSceneSnapshot(st);
  assert.deepStrictEqual(s2.links[1].packets, frozen, 'off packets do not advance');
  assert.notDeepStrictEqual(s2.links[0].packets, moving, 'reachable packets keep flowing');

  // and it comes back when the brain does
  st = M.jarvisSceneStep(st, 0, p, DATA);   // a poll arriving between frames
  const s3 = M.jarvisSceneSnapshot(st);
  assert.strictEqual(s3.links[1].on, true);
  assert.strictEqual(s3.brains[1].dim, 1);
  assert.strictEqual(s3.brains[1].ring, s2.brains[1].ring, 'a data poll must not reset a ring phase');
});

test('nothing is invented: empty data draws Agent and a waiting ring only', () => {
  const { st, snap } = run({ data: { brains: [], senses: [], fleet: [] }, steps: 40 });
  assert.strictEqual(snap.waiting, true);
  assert.strictEqual(snap.brains.length, 0);
  assert.strictEqual(snap.links.length, 0);
  assert.strictEqual(snap.senses.count, 0);
  assert.strictEqual(snap.fleet.length, 0);

  const canvas = makeCanvas(1440, 900);
  const scene = M.createScene(canvas, { dpr: 1, reducedMotion: false, warmupMs: 0, width: 1440, height: 900 });
  scene.setData({ brains: [], senses: [], fleet: [] });
  scene.render();
  const texts = canvas.__ctx.calls.filter((c) => c[0] === 'fillText').map((c) => c[1]);
  assert.ok(texts.includes('WAITING FOR DATA'), 'empty data is labelled, not faked');
  assert.ok(!texts.some((t) => /BRAIN/.test(t) && t !== 'WAITING FOR DATA'), 'no phantom brains');
  scene.destroy();
  assert.ok(st.t > 0);
});

test('senses are capped at 12 and unreachable ones are counted', () => {
  const senses = Array.from({ length: 18 }, (_, i) => ({ id: 's' + i, label: 'S' + i, status: i % 5 === 0 ? 'unreachable' : 'ok' }));
  const { snap } = run({ data: { ...DATA, senses }, steps: 10 });
  assert.strictEqual(snap.senses.count, 12);
  assert.strictEqual(snap.senses.unreachable, 3);
});

/* ============================= DETERMINISM ================================ */
test('snapshotState() is deterministic for the same seed and dt sequence', () => {
  const a = run({ seed: 42, steps: 137, dt: 33, levels: { voice: 0.6, mic: 0.3 } }).snap;
  const b = run({ seed: 42, steps: 137, dt: 33, levels: { voice: 0.6, mic: 0.3 } }).snap;
  assert.deepStrictEqual(a, b);
  const c = run({ seed: 99, steps: 137, dt: 33, levels: { voice: 0.6, mic: 0.3 } }).snap;
  assert.notDeepStrictEqual(a.starDrift === c.starDrift && a.t === c.t ? a : {}, {});
  // a fresh module load reproduces the same numbers
  const fresh = loadScene();
  let st = fresh.jarvisSceneStep({ w: 1440, h: 900, seed: 42 }, 0, presence('speaking', { voice: 0.6, mic: 0.3 }), DATA);
  const p = presence('speaking', { voice: 0.6, mic: 0.3 });
  for (let i = 0; i < 137; i++) st = fresh.jarvisSceneStep(st, 33, p);
  assert.deepStrictEqual(fresh.jarvisSceneSnapshot(st), a);
});

/* ============================== CANVAS WIRING ============================= */
test('createScene honours the §4.3 contract on a canvas-less-ish stub', () => {
  const canvas = makeCanvas(1200, 800);
  const scene = M.createScene(canvas, { dpr: 2, reducedMotion: false, warmupMs: 0, width: 1200, height: 800 });
  for (const k of ['setPresence', 'setData', 'setSize', 'start', 'stop', 'destroy', 'snapshotState']) {
    assert.strictEqual(typeof scene[k], 'function', `contract method ${k}`);
  }
  scene.setData(DATA).setPresence(presence('speaking', { voice: 0.7 }));
  scene.setSize(1440, 900);
  assert.strictEqual(canvas.width, 2880, 'DPR-aware backing store');
  assert.strictEqual(canvas.height, 1800);
  assert.strictEqual(canvas.style.width, '1440px');
  scene.render();
  const c = canvas.__ctx.calls;
  assert.ok(c.filter((x) => x[0] === 'fillRect').length > 100, 'particles were drawn');
  assert.ok(c.some((x) => x[0] === 'ellipse'), 'senses ring drawn');
  const texts = c.filter((x) => x[0] === 'fillText').map((x) => x[1]);
  assert.ok(texts.includes('AGENT'), 'Agent is labelled');
  assert.ok(texts.includes('BRAIN 1'), 'brain labels come from data');
  assert.ok(texts.includes('FLEET · 2 BUSY / 3'), 'fleet counts are read from data');
  const snap = scene.snapshotState();
  assert.strictEqual(snap.w, 1440);
  assert.strictEqual(snap.brains.length, 3);
  scene.destroy();
});

test('an unreachable brain says so in its label', () => {
  const canvas = makeCanvas(1440, 900);
  const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900, reducedMotion: false });
  scene.setData({ ...DATA, brains: [{ id: 'brain-2', label: 'Brain 2', status: 'unreachable' }] });
  scene.render();
  const texts = canvas.__ctx.calls.filter((x) => x[0] === 'fillText').map((x) => x[1]);
  assert.ok(texts.some((t) => /BRAIN 2 · UNREACHABLE/.test(t)), texts.join(' | '));
  scene.destroy();
});

test('a disabled fleet clears its old nodes and caption', () => {
  const canvas = makeCanvas(1440, 900);
  const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900, reducedMotion: false });
  scene.setData(DATA);
  assert.equal(scene.snapshotState().fleet.length, 3);
  scene.setData({ ...DATA, settings: { agent_name: 'Sample Agent', owner_label: 'Sample Owner', enabled_boxes: ['today'] } });
  assert.equal(scene.snapshotState().fleet.length, 0, 'the prior profile selection cannot remain in the scene');
  canvas.__ctx.calls.length = 0;
  scene.render();
  const texts = canvas.__ctx.calls.filter((x) => x[0] === 'fillText').map((x) => x[1]);
  assert.equal(texts.some((text) => /^FLEET ·/.test(text)), false);
  scene.destroy();
});

/* ============================ LOOK v1.1 (SPEC §3b) ======================== */
/* The art layer is OPTIONAL by construction: 35-assets.js and a DOM are both
 * absent here, and the scene must still paint every element. */
test('the art layer is optional: no JARVIS_ASSETS, no DOM, still a full scene', () => {
  const canvas = makeCanvas(1440, 900);
  const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900, reducedMotion: false });
  scene.setData(DATA).setPresence(presence('speaking', { voice: 0.7 }));
  scene.render();
  assert.strictEqual(scene.state.img, null, 'no Image constructor -> no image bag');
  assert.strictEqual(scene.state.imgInit, true, 'but the probe ran exactly once');
  assert.strictEqual(scene.state.bg, null, 'and no backplate was cached');
  const texts = canvas.__ctx.calls.filter((c) => c[0] === 'fillText').map((c) => c[1]);
  assert.ok(texts.includes('AGENT') && texts.includes('BRAIN 1'));
  scene.destroy();
});

test('each brain wears its own plasma sphere and hue', () => {
  const canvas = makeCanvas(1440, 900);
  const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900 });
  scene.setData(DATA);
  const by = {};
  for (const b of scene.state.brains) by[b.id] = b;
  assert.deepStrictEqual(
    [by['brain-1'].asset, by['brain-2'].asset, by['brain-3'].asset],
    ['orbBrain1', 'orbBrain2', 'orbBrain3']);
  assert.deepStrictEqual(
    [by['brain-1'].lane, by['brain-2'].lane, by['brain-3'].lane],
    ['magenta', 'cyan', 'teal']);
  // an unrecognised brain falls back to a plate and a hue by index
  scene.setData({ brains: [{ id: 'mystery-1', label: 'Something else', status: 'ok' }] });
  assert.ok(['orbBrain2', 'orbBrain1', 'orbBrain3'].includes(scene.state.brains[0].asset));
  assert.strictEqual(scene.state.brains[0].lane, 'magenta', 'slot 0 keeps the first brain hue');
  scene.destroy();
});

test('links run cobalt IN to Agent and coral OUT to the brain', () => {
  const canvas = makeCanvas(1440, 900);
  const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900 });
  scene.setData(DATA).setPresence(presence('speaking', { voice: 0.5 }));
  scene.render();
  // two-way traffic exists in the state...
  const dirs = scene.state.links[0].packets.map((p) => p.dir);
  assert.ok(dirs.includes(1) && dirs.includes(-1), 'each link carries both directions');
  // ...and both §3b colours reached the canvas
  assert.ok(painted(canvas, 'stroke', '58,98,255') > 0, 'cobalt-bright packets drawn');
  assert.ok(painted(canvas, 'stroke', '232,93,79') > 0, 'coral packets drawn');
  scene.destroy();
});

test('setSize re-derives the plate sizes and destroy() releases the caches', () => {
  const canvas = makeCanvas(1200, 800);
  const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1200, height: 800 });
  scene.setData(DATA);
  const small = { agent: scene.state.geo.agentPlate, brain: scene.state.geo.brainPlate };
  assert.ok(small.agent > 0 && small.brain > 0, 'plate sizes are derived from the layout');
  scene.setSize(1920, 1200);
  assert.ok(scene.state.geo.agentPlate > small.agent, 'a bigger stage rasterises bigger plates');
  assert.strictEqual(scene.state.bg, null, 'the backplate cache is dropped on resize');
  scene.render();
  scene.destroy();
  assert.strictEqual(scene.state.img, null);
  assert.strictEqual(scene.state.bg, null);
  assert.deepStrictEqual(scene.state.cache, {});
});

/* ======================= JARVIS MODE v2 — THE ORB ========================= */
/* SPEC §7.1, Owner 2026-09-19: "I want Jarvis ball to look bigger. And when
 * it speaks and thinks, it's more obvious. Like when it's speaking, it glows
 * more and move more when it thinks, it shrinks and becomes darker."         */

const SIZES = [[1440, 900], [1920, 1080], [2560, 1440], [3440, 1440]];

test('§7.1.1 — Agent idles at exactly min(w,h) x 0.235 on every stage', () => {
  for (const [w, h] of SIZES) {
    const { st } = run({ w, h, mode: 'idle', steps: 4 });
    const m = Math.min(w, h);
    assert.ok(Math.abs(st.geo.r0 - m * 0.235) < 0.01,
      `${w}x${h}: idle radius ${st.geo.r0.toFixed(1)} is not min(w,h) x 0.235 (${(m * 0.235).toFixed(1)})`);
    assert.strictEqual(M.JARVIS_LOOK.agentR, 0.235);
    // and the centre stays in the middle, near the 57% of SPEC §7.1.1
    assert.ok(Math.abs(st.geo.cx - w * 0.5) < 0.01, 'Agent is centred across');
    assert.ok(st.geo.cy > h * 0.49 && st.geo.cy <= h * 0.57 + 0.01,
      `${w}x${h}: the centre wandered to ${(st.geo.cy / h).toFixed(3)}h`);
  }
});

test('§7.1.2 — speaking = idle x (1.04 + 0.24 x voice), and it is the only swell', () => {
  for (const v of [0, 0.2, 0.5, 0.9, 1]) {
    const a = settled({ mode: 'speaking', levels: { voice: v } });
    const want = 1.04 + 0.24 * v;
    assert.ok(Math.abs(a.radius / a.idleRadius - want) < 0.004,
      `voice ${v}: r/idle ${(a.radius / a.idleRadius).toFixed(4)} != ${want}`);
  }
  // at voice 0 he is still visibly brighter than idle — Owner must be able to
  // tell "speaking, silent right now" from "idle" without a word on screen
  const sp = settled({ mode: 'speaking', levels: { voice: 0 } });
  const idle = settled({ mode: 'idle' });
  assert.ok(sp.brightness > idle.brightness * 1.15,
    `speaking at voice 0 must out-glow idle (${sp.brightness} vs ${idle.brightness})`);
  assert.ok(sp.halo > idle.halo * 1.08, 'and carry a wider halo than idle');
});

test('§7.1.2 — the halo at least DOUBLES in radius and in alpha from voice 0 to 1', () => {
  const lo = settled({ mode: 'speaking', levels: { voice: 0 } });
  const hi = settled({ mode: 'speaking', levels: { voice: 1 } });
  assert.ok(hi.halo >= lo.halo * 2,
    `halo ${lo.halo} -> ${hi.halo} is not a doubling`);

  // ...and the PAINT follows that one number, radius and alpha alike
  const shot = (voice) => {
    const canvas = makeCanvas(1920, 1080);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1920, height: 1080, reducedMotion: false });
    scene.setData(DATA).setPresence(presence('speaking', { voice }));
    const p = presence('speaking', { voice });
    for (let i = 0; i < 200; i++) M.jarvisSceneStep(scene.state, 33, p);
    canvas.__ctx.grads.length = 0;
    scene.render();
    const g = scene.state.geo;
    // the halo is Agent's own three-stop gradient (0 / 0.30 / 1); the big
    // background glow behind him is the one with a 0.42 middle stop
    const halo = canvas.__ctx.grads.filter((q) => q.kind === 'radial' &&
      Math.abs(q.args[0] - g.cx) < 0.5 && Math.abs(q.args[1] - g.cy) < 0.5 &&
      q.args[2] === 0 && q.stops.length === 3 && q.stops[1][0] === 0.30)[0];
    assert.ok(halo, 'the halo gradient was not painted');
    scene.destroy();
    return { r: halo.args[5], a: Math.max(...halo.stops.map((s) => alphaOf(s[1]))) };
  };
  const a0 = shot(0), a1 = shot(1);
  assert.ok(a1.r >= a0.r * 2, `painted halo radius ${a0.r.toFixed(1)} -> ${a1.r.toFixed(1)}`);
  assert.ok(a1.a >= a0.a * 2, `painted halo alpha ${a0.a} -> ${a1.a}`);
});

test('§7.1.2 — plasma and lightning speed up at least 2.5x with the voice', () => {
  const lo = settled({ mode: 'speaking', levels: { voice: 0 } });
  const hi = settled({ mode: 'speaking', levels: { voice: 1 } });
  assert.ok(hi.plasmaSpeed >= lo.plasmaSpeed * 2.5,
    `plasma ${lo.plasmaSpeed} -> ${hi.plasmaSpeed} is short of 2.5x`);

  // the lightning rides the same clock, so it strikes far more often
  const strikes = (voice) => {
    const canvas = makeCanvas(1440, 900);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900, reducedMotion: false, seed: 5 });
    scene.setData(DATA).setPresence(presence('speaking', { voice }));
    const p = presence('speaking', { voice });
    let n = 0;
    for (let i = 0; i < 120; i++) {
      M.jarvisSceneStep(scene.state, 33, p);
      canvas.__ctx.calls.length = 0;
      scene.render();
      n += canvas.__ctx.calls.filter((c) => c[0] === 'stroke').length;
    }
    scene.destroy();
    return n;
  };
  const hot = strikes(0.9), cold = strikes(0);
  assert.ok(hot > cold, `voice must strike filaments (${hot} vs ${cold})`);
});

test('§7.1.2 — a voice PEAK fires a shock ring, at most one every 260 ms', () => {
  // a square wave: 0.1 for 100 ms, 0.9 for 100 ms, ... — a peak every 200 ms,
  // which is faster than the ruling allows a ring to be born.
  let st = M.jarvisSceneStep({ w: 1440, h: 900, seed: 3 }, 0, presence('speaking', { voice: 0 }), DATA);
  const born = [];
  let last = st.agent.shockAt;
  for (let i = 0; i < 120; i++) {
    const v = (Math.floor(i / 3) % 2) ? 0.9 : 0.1;
    st = M.jarvisSceneStep(st, 33, presence('speaking', { voice: v }));
    if (st.agent.shockAt !== last) { born.push(st.agent.shockAt); last = st.agent.shockAt; }
  }
  assert.ok(born.length >= 4, `peaks must fire shock rings (${born.length})`);
  for (let i = 1; i < born.length; i++) {
    assert.ok(born[i] - born[i - 1] >= 0.26 - 1e-9,
      `two shock rings only ${(born[i] - born[i - 1]).toFixed(3)} s apart`);
  }
  // they are gone inside a second
  let quiet = M.jarvisSceneStep(st, 0, presence('speaking', { voice: 0.9 }));
  for (let i = 0; i < 40; i++) quiet = M.jarvisSceneStep(quiet, 33, presence('speaking', { voice: 0.9 }));
  assert.strictEqual(M.jarvisSceneSnapshot(quiet).agent.rings, 0, 'a steady level fires nothing');

  // a level that never rises never fires one at all
  const flat = run({ mode: 'speaking', levels: { voice: 0.5 }, steps: 200 }).snap;
  assert.strictEqual(flat.agent.rings, 0);
  // and neither does a tool call: thinking/working carry no voice reaction
  let think = M.jarvisSceneStep({ w: 1440, h: 900, seed: 3 }, 0, presence('thinking', { voice: 0 }), DATA);
  for (let i = 0; i < 60; i++) {
    think = M.jarvisSceneStep(think, 33, presence('thinking', { voice: (Math.floor(i / 3) % 2) ? 0.9 : 0.1 }));
    assert.strictEqual(M.jarvisSceneSnapshot(think).agent.rings, 0, 'thinking must not ring');
  }
});

test('§7.1.3 — thinking and working shrink to idle x 0.78 and go dark', () => {
  for (const mode of ['thinking', 'working']) {
    const a = settled({ mode, levels: { voice: 0.8 } });        // voice is ignored here
    const ratio = a.radius / a.idleRadius;
    assert.ok(Math.abs(ratio - 0.78) <= 0.78 * 0.021,
      `${mode}: r/idle ${ratio.toFixed(4)} is not 0.78 (+/- the 2% breath)`);
    assert.ok(a.brightness <= 0.45, `${mode}: core brightness ${a.brightness} > 45% of idle`);
    assert.ok(a.halo <= 0.35, `${mode}: halo ${a.halo} > 35% of idle`);
    assert.ok(a.plasmaSpeed < 0, `${mode}: the plasma must swirl INWARD (${a.plasmaSpeed})`);
    assert.ok(Math.abs(a.plasmaSpeed) <= 0.5, `${mode}: plasma ${a.plasmaSpeed} faster than 0.5x`);
    assert.strictEqual(a.arc, mode, `${mode}: the orbiting arc says so`);
  }
  // the 4 s +/-2% breath: sampled across one period the radius really moves,
  // and never by more than 2%
  let st = M.jarvisSceneStep({ w: 1440, h: 900, seed: 11 }, 0, presence('thinking'), DATA);
  const p = presence('thinking');
  for (let i = 0; i < 200; i++) st = M.jarvisSceneStep(st, 33, p);   // settle
  let lo = Infinity, hi = 0;
  for (let i = 0; i < 130; i++) {                                    // ~4.3 s
    st = M.jarvisSceneStep(st, 33, p);
    const a = M.jarvisSceneSnapshot(st).agent, k = a.radius / a.idleRadius;
    lo = Math.min(lo, k); hi = Math.max(hi, k);
  }
  assert.ok(hi - lo > 0.012, `the thinking breath is invisible (${(hi - lo).toFixed(4)})`);
  assert.ok(hi <= 0.78 * 1.021 && lo >= 0.78 * 0.979, `the breath is bigger than +/-2% (${lo}..${hi})`);
});

test('§7.1.3 — nothing but the arc and the colour tells thinking from working', () => {
  const t = settled({ mode: 'thinking', levels: { voice: 0.4, mic: 0 } });
  const w = settled({ mode: 'working', levels: { voice: 0.4, mic: 0 } });
  const strip = (a) => { const c = { ...a }; delete c.arc; delete c.mode; delete c.colour; delete c.modeColour; return c; };
  assert.deepStrictEqual(strip(t), strip(w), 'thinking and working differ beyond the arc');
  assert.strictEqual(t.modeColour, M.JARVIS_SCENE_TOKENS.violet);
  assert.strictEqual(w.modeColour, M.JARVIS_SCENE_TOKENS.amber);
});

test('§7.1.4 — listening sits at exactly idle x 1.0 and ripples inward', () => {
  const a = settled({ mode: 'listening', levels: { mic: 0.8 } });
  assert.ok(Math.abs(a.radius / a.idleRadius - 1) < 0.002,
    `listening r/idle ${(a.radius / a.idleRadius).toFixed(4)} is not 1.0`);
  assert.ok(a.ripples > 0, 'the mic still draws ripples');
  assert.strictEqual(a.arc, null, 'listening wears no arc');
});

test('§7.1.5 — a mode change eases over 350 ms: no pop, and it lands', () => {
  const p0 = presence('idle'), p1 = presence('thinking');
  let st = M.jarvisSceneStep({ w: 1440, h: 900, seed: 4 }, 0, p0, DATA);
  for (let i = 0; i < 200; i++) st = M.jarvisSceneStep(st, 33, p0);
  const from = M.jarvisSceneSnapshot(st).agent;
  /* brightness carries no breath, so it measures the EASE itself: idle 1.0 ->
   * thinking 0.40. Radius, halo and colour ride the same constant. */
  const to = 0.40;
  const at = (ms) => {
    let s = st, left = ms;
    while (left > 0) { const dt = Math.min(33, left); s = M.jarvisSceneStep(s, dt, p1); left -= dt; }
    const a = M.jarvisSceneSnapshot(s).agent;
    return { k: (a.brightness - from.brightness) / (to - from.brightness), a: a };
  };
  const first = at(33), mid = at(175), done = at(350), after = at(700);
  assert.ok(first.k > 0.05 && first.k < 0.40, `the first frame popped or froze (${first.k.toFixed(3)})`);
  assert.ok(mid.k > 0.5 && mid.k < 0.95, `the middle of the ease is wrong (${mid.k.toFixed(3)})`);
  assert.ok(done.k > 0.9, `350 ms did not land the change (${done.k.toFixed(3)})`);
  assert.ok(after.k > 0.98, `it never landed (${after.k.toFixed(3)})`);
  // the radius and the halo come with it, and neither jumps on frame one
  const rFrom = from.radius / from.idleRadius;
  assert.ok(first.a.radius / first.a.idleRadius > rFrom - 0.40 * (rFrom - 0.78),
    'the radius popped on the first frame');
  assert.ok(Math.abs(after.a.radius / after.a.idleRadius - 0.78) < 0.021, 'the radius landed');
  assert.ok(Math.abs(after.a.halo - 0.30) < 0.01, 'the halo landed');
  assert.ok(Math.abs(M.JARVIS_EASE - 0.1167) < 1e-9);
});

test('§7.1.5 — reduced motion keeps the sizes and parks the moving marks', () => {
  // sizes and brightness still change with the mode
  const think = settled({ mode: 'thinking', reducedMotion: true });
  const speak = settled({ mode: 'speaking', levels: { voice: 0.9 }, reducedMotion: true });
  assert.ok(Math.abs(think.radius / think.idleRadius - 0.78) < 0.02, 'thinking still shrinks');
  assert.ok(speak.radius / speak.idleRadius > 1.2, 'speaking still swells');
  assert.ok(think.brightness <= 0.45 && speak.brightness > 1.2, 'brightness still moves');

  // ...but the orbiting arc is a static mark
  const arcAngles = (reducedMotion) => {
    const canvas = makeCanvas(1440, 900);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: 1440, height: 900, reducedMotion });
    scene.setData(DATA).setPresence(presence('working'));
    const p = presence('working');
    const seen = [];
    for (let k = 0; k < 3; k++) {
      for (let i = 0; i < 20; i++) M.jarvisSceneStep(scene.state, 33, p);
      canvas.__ctx.calls.length = 0;
      scene.render();
      const g = scene.state.geo;
      const arcs = canvas.__ctx.calls.filter((c) => c[0] === 'arc' &&
        Math.abs(c[1] - g.cx) < 0.5 && Math.abs(c[2] - g.cy) < 0.5 && c[5] !== undefined &&
        Math.abs(c[5] - c[4] - 70 * Math.PI / 180) < 1e-6);
      seen.push(arcs.length ? arcs[0][4] : null);
    }
    scene.destroy();
    return seen;
  };
  const still = arcAngles(true), moving = arcAngles(false);
  assert.ok(still.every((x) => x !== null), 'the arc must still be drawn');
  assert.ok(still[0] === still[1] && still[1] === still[2], `reduced motion must park the arc (${still})`);
  assert.ok(moving[0] !== moving[1] && moving[1] !== moving[2], `the arc must orbit otherwise (${moving})`);
});

test('§7.1.6 — snapshotState() carries the orb fields the rulings are made of', () => {
  const a = run({ mode: 'working', steps: 40 }).snap.agent;
  assert.deepStrictEqual(Object.keys(a).sort(), [
    'arc', 'breath', 'brightness', 'call', 'colour', 'halo', 'idleRadius',
    'mic', 'mode', 'modeColour', 'plasmaSpeed', 'radius', 'rings', 'ripples', 'voice'
  ]);
  for (const k of ['radius', 'idleRadius', 'brightness', 'halo', 'plasmaSpeed', 'rings']) {
    assert.strictEqual(typeof a[k], 'number', `${k} must be a number`);
  }
  assert.strictEqual(a.arc, 'working');
});

/* ---------------------------- NOTHING OVERLAPS ---------------------------- */
/* SPEC §7.1.1: the orb at its LARGEST speaking size — the bright core, not the
 * soft halo — against the brain nodes, the brain labels, the bottom 17% and
 * the left/right 23% rails, at the four sizes Owner actually runs. */
test('§7.1.1 — nothing overlaps at 1440x900, 1920x1080, 2560x1440, 3440x1440', () => {
  for (const [w, h] of SIZES) {
    const where = `${w}x${h}`;
    const canvas = makeCanvas(w, h);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: w, height: h });
    scene.setData(DATA);
    const st = scene.state, g = st.geo, n = st.brains.length;
    const core = g.rMax;                       /* the core at its very largest */
    assert.ok(Math.abs(core - g.r0 * 1.28) < 1e-6, `${where}: rMax is not idle x 1.28`);

    // 1. the bottom 17% (captions ribbon + ticker)
    assert.ok(g.cy + core <= h * 0.83 + 0.01,
      `${where}: the loudest core reaches ${(g.cy + core).toFixed(1)}, past the 17% band at ${(h * 0.83).toFixed(1)}`);
    // 2. the left and right 23% rails
    assert.ok(g.cx - core >= w * 0.23, `${where}: the core enters the left rail`);
    assert.ok(g.cx + core <= w * 0.77, `${where}: the core enters the right rail`);
    // 3. the brain nodes, rings included
    const pos = [0, 0];
    for (let i = 0; i < n; i++) {
      M.jarvisBrainPos(st, i, n, pos);
      const d = Math.hypot(pos[0] - g.cx, pos[1] - g.cy) - L.brainRing * g.brainR;
      assert.ok(d > core, `${where}: brain ${i} sits ${(d - core).toFixed(1)} px inside the loudest core`);
      // 4. and its label, taken as the widest box fitText can leave behind
      const lx0 = pos[0] - w * 0.095, lx1 = pos[0] + w * 0.095;
      const ly1 = pos[1] - L.brainLabel * g.brainR - 11, ly0 = ly1 - 12;
      const nx = Math.max(lx0, Math.min(g.cx, lx1)), ny = Math.max(ly0, Math.min(g.cy, ly1));
      assert.ok(Math.hypot(nx - g.cx, ny - g.cy) > core, `${where}: brain label ${i} crosses the loudest core`);
      assert.ok(ly0 >= 8, `${where}: brain label ${i} crowds the top edge (${ly0.toFixed(1)})`);
      // brains never climb into a rail either
      assert.ok(pos[0] - L.brainRing * g.brainR > Math.max(w * 0.23, 354) - 6, `${where}: brain ${i} enters the left rail`);
      assert.ok(pos[0] + L.brainRing * g.brainR < w - Math.max(w * 0.23, 300) + 6, `${where}: brain ${i} enters the right rail`);
    }
    // adjacent brains keep off each other
    assert.ok(g.brainDx >= 2 * L.brainRing * g.brainR, `${where}: adjacent brains overlap`);

    // the brains kept their size where the stage allowed it, and where it did
    // not, they are exactly as big as the chain permits — "up/out only as far
    // as needed", never an arbitrary shrink.
    const m = Math.min(w, h);
    assert.ok(g.brainR <= m * L.brainWish + 1e-6, `${where}: brains grew past their v1.3 size`);
    assert.ok(g.brainR >= m * 0.045, `${where}: brains collapsed to ${g.brainR.toFixed(1)}`);
    if (g.brainR < m * L.brainWish - 0.01) {
      const bottom = g.brainY + L.brainRing * g.brainR + L.brainGap;
      assert.ok(Math.abs(bottom - (g.cy - g.ringOut)) < 0.5,
        `${where}: the brain row is smaller than the room it has`);
    }

    // the readout still fits between his ring and the fleet arc
    const stack = [0, L.readout1, L.readout2, L.readout3][g.textLines];
    assert.ok(g.textLines >= 1, `${where}: the AGENT readout vanished`);
    assert.ok(g.textY + stack <= g.fleetY - 9 + 0.5, `${where}: the readout runs into the fleet arc`);
    scene.destroy();
  }
});

/* -------------------------- THE RAIL COLUMNS ------------------------------ */
/* SPEC §8 amendment B.3: the left and right rails are COLUMNS of glass boxes
 * with 4 px of air between them. A sense label or dot that lands in that air
 * shows through and reads as a collision (Owner saw one between SPEND and
 * SCOREBOARD at 1440x900). Neither a name nor a mark may be drawn inside a
 * column at any of the four sizes, at any point of the 90 s orbit. */
test('§8 amendment B.3 — a rail column takes no sense label and no sense dot', () => {
  const heads = DATA.senses.map((s) => s.label.toUpperCase().slice(0, 4));
  for (const [w, h] of SIZES) {
    const where = `${w}x${h}`;
    const canvas = makeCanvas(w, h);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: w, height: h });
    scene.setData(DATA).setPresence(presence('listening'));
    const st = scene.state, cols = st.geo.railCols;

    // one rect per rail, and each one IS the column: top of the glass to the
    // foot of the rail, the gaps between the boxes inside it
    assert.strictEqual(cols.length, 2, `${where}: the two rail columns are missing`);
    assert.ok(cols[0][1] <= 0 && cols[0][3] >= h - 206,
      `${where}: the left column stops at ${cols[0][3]}, above its last box (${h - 206})`);
    assert.ok(cols[1][1] <= 0 && cols[1][3] >= h - 56,
      `${where}: the right column stops at ${cols[1][3]}, above its last box (${h - 56})`);
    assert.ok(cols[0][2] >= 354, `${where}: the left column is narrower than its glass`);
    assert.ok(cols[1][0] <= w - 330, `${where}: the right column is narrower than its glass`);

    const inCol = (x, y) => cols.some((r) => x > r[0] && x < r[2] && y > r[1] && y < r[3]);
    let dots = 0, names = 0;
    // a whole turn of the ring: 90 s of scene time in 2.4 s bites (dt is
    // clamped at 200 ms, so the orbit is walked, never jumped)
    for (let sweep = 0; sweep < 40; sweep += 1) {
      for (let k = 0; k < 12; k += 1) M.jarvisSceneStep(st, 200, presence('listening'));
      canvas.__ctx.calls.length = 0;
      scene.render();
      for (const c of canvas.__ctx.calls) {
        if (c[0] === 'fillText' && heads.some((head) => String(c[1]).startsWith(head))) {
          names += 1;
          assert.ok(!inCol(c[2], c[3]),
            `${where}: sense label ${c[1]} drew at ${Math.round(c[2])},${Math.round(c[3])} inside a rail column`);
        }
        if (c[0] === 'arc' && (c[3] === 5.2 || c[3] === 1.9)) {
          dots += 1;
          assert.ok(!inCol(c[1], c[2]),
            `${where}: a sense dot drew at ${Math.round(c[1])},${Math.round(c[2])} inside a rail column`);
        }
        if (c[0] === 'fillRect' && c[3] === 2.6 && c[4] === 2.6) {   // an unreachable sense
          dots += 1;
          assert.ok(!inCol(c[1] + 1.3, c[2] + 1.3),
            `${where}: an unreachable sense mark drew inside a rail column`);
        }
      }
    }
    // the readings did not simply vanish: they are drawn everywhere else
    assert.ok(dots > 40, `${where}: only ${dots} sense marks were drawn in a whole orbit`);
    assert.ok(names > 20, `${where}: only ${names} sense names were drawn in a whole orbit`);
    scene.destroy();
  }
});

/* ------------------------- THE BRAIN NAME LABELS -------------------------- */
/* SPEC §8 amendment C11: a sense dot sat on the BRAIN 3 BRAIN label in the
 * 1440x900 renders. A brain's own name is part of the display, so its label
 * band is a keep-out like a rail column: the dot, its tick and its name all
 * stand down there rather than print over it. Nothing moves for this — not the
 * orb, not a brain — the ring's marks simply wait for the next sweep. */
test('§8 amendment C11 — a brain name label takes no sense label and no sense dot', () => {
  const heads = DATA.senses.map((s) => s.label.toUpperCase().slice(0, 4));
  for (const [w, h] of SIZES) {
    const where = `${w}x${h}`;
    const canvas = makeCanvas(w, h);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: w, height: h });
    scene.setData(DATA).setPresence(presence('listening'));
    const st = scene.state, boxes = st.geo.brainLabels;

    assert.strictEqual(boxes.length, DATA.brains.length,
      `${where}: one keep-out per brain name, and there are ${DATA.brains.length} brains`);
    // each box really does sit on its own brain, above the node
    const pos = [0, 0];
    for (let i = 0; i < DATA.brains.length; i += 1) {
      M.jarvisBrainPos(st, i, DATA.brains.length, pos);
      const b = boxes[i];
      assert.ok(b[0] < pos[0] && b[2] > pos[0], `${where}: label box ${i} is not centred on its brain`);
      assert.ok(b[3] < pos[1], `${where}: label box ${i} is not above its brain`);
      assert.ok(b[3] - b[1] >= 10, `${where}: label box ${i} is thinner than the type in it`);
    }
    // and the keep-out list the scene checks carries them
    for (const b of boxes) {
      assert.ok(st.geo.keepOut.some((r) => r[0] === b[0] && r[1] === b[1] && r[2] === b[2] && r[3] === b[3]),
        `${where}: a brain label is missing from the scene keep-out`);
    }

    const inLabel = (x, y) => boxes.some((r) => x > r[0] && x < r[2] && y > r[1] && y < r[3]);
    let dots = 0, names = 0;
    for (let sweep = 0; sweep < 40; sweep += 1) {
      for (let k = 0; k < 12; k += 1) M.jarvisSceneStep(st, 200, presence('listening'));
      canvas.__ctx.calls.length = 0;
      scene.render();
      for (const c of canvas.__ctx.calls) {
        if (c[0] === 'fillText' && heads.some((head) => String(c[1]).startsWith(head))) {
          names += 1;
          assert.ok(!inLabel(c[2], c[3]),
            `${where}: sense label ${c[1]} drew at ${Math.round(c[2])},${Math.round(c[3])} on a brain's name`);
        }
        if (c[0] === 'arc' && (c[3] === 5.2 || c[3] === 1.9)) {
          dots += 1;
          assert.ok(!inLabel(c[1], c[2]),
            `${where}: a sense dot drew at ${Math.round(c[1])},${Math.round(c[2])} on a brain's name`);
        }
        if (c[0] === 'fillRect' && c[3] === 2.6 && c[4] === 2.6) {
          dots += 1;
          assert.ok(!inLabel(c[1] + 1.3, c[2] + 1.3),
            `${where}: an unreachable sense mark drew on a brain's name`);
        }
      }
    }
    assert.ok(dots > 40, `${where}: only ${dots} sense marks were drawn in a whole orbit`);
    assert.ok(names > 20, `${where}: only ${names} sense names were drawn in a whole orbit`);
    scene.destroy();
  }
});

/* SPEC §0 law 2: the brains are a DISPLAY and never react to voice. Everything
 * Agent's voice or Owner's mic MOVES therefore has to stay inside his own
 * airspace — his constant chrome rings are not in this rule, they turn at the
 * same pace whatever anyone says. */
test('§0 — every voice-driven circle stays inside Agent\'s airspace', () => {
  for (const [w, h] of SIZES) {
    const where = `${w}x${h}`;
    const canvas = makeCanvas(w, h);
    const scene = M.createScene(canvas, { dpr: 1, warmupMs: 0, width: w, height: h });
    scene.setData(DATA);
    const st = scene.state, g = st.geo;
    assert.ok(g.nearEdge > 0 && g.airspace > 0, `${where}: the airspace is unsolved`);
    assert.ok(g.airspace < g.nearEdge, `${where}: the airspace reaches the brain rings`);
    assert.ok(g.airspace > g.rMax, `${where}: a shock ring has nowhere to fly`);
    assert.ok(g.rippleR1 > g.rippleR0, `${where}: the mic ripple has nowhere to travel`);

    // mic hot AND a voice peak: whatever those add must stay inside it
    let peaks = 0;
    for (let i = 0; i < 120; i++) {
      const v = (Math.floor(i / 3) % 2) ? 0.9 : 0.1;
      M.jarvisSceneStep(st, 33, presence('speaking', { voice: v, mic: 0.9 }));
      if (M.jarvisSceneSnapshot(st).agent.rings > 0) peaks++;
    }
    assert.ok(peaks > 0, `${where}: no shock ring was ever alive`);
    canvas.__ctx.calls.length = 0;
    scene.render();
    const outer = agentArcs(canvas, g).filter((r) => r > g.ringOut + 0.5);
    assert.ok(outer.length > 0, `${where}: nothing voice-driven was painted at all`);
    for (const r of outer) {
      assert.ok(r <= g.airspace + 0.5, `${where}: a voice circle flew to ${r.toFixed(1)} (airspace ${g.airspace.toFixed(1)})`);
      assert.ok(r < g.nearEdge, `${where}: a voice circle reached a brain ring`);
    }
    scene.destroy();
  }
});
