/* ==========================================================================
 * 40-scene.js — Jarvis mode scene renderer  (PURE MODULE: no import /
 * export / HermesSDK / React / DOM lookups beyond the canvas handed in)
 *
 * THE THREE LAWS (SPEC §0 — Owner, 2026-09-18). Break one and this file is
 * wrong, not "stylistically different":
 *   1. Agent is the centre and the ONLY voice-reactive element on screen.
 *   2. The brains are a display BEHIND him. They never read presence.
 *   3. Everything else moves constantly, like a program doing something —
 *      at a pace that does not care whether anyone is talking.
 *
 * Structurally that means: the "world" layer (brains, links, packets, senses,
 * fleet, starfield) advances from scene time only, and `presence` is read in
 * exactly one function — jarvisStepAgent(). tests/scene.test.mjs enforces it.
 *
 * Public surface (SPEC §4.3):
 *   createScene(canvas, opts) -> { setPresence, setData, setSize, start,
 *                                  stop, destroy, snapshotState }
 *   jarvisSceneStep(state, dtMs, presence, data) -> state   (canvas-free)
 *   jarvisSceneSnapshot(state) -> plain deterministic object
 *
 * opts = { dpr?, reducedMotion?, width?, height?, seed?, warmupMs? }
 *   dpr, reducedMotion  default to the environment (devicePixelRatio,
 *                       prefers-reduced-motion) when not given.
 *   width, height       seed the first layout before setSize() is called.
 *   seed                fixes the starfield, so runs are repeatable in tests.
 *   warmupMs            default 2600: advances the simulation before the first
 *                       paint, so the scene opens developed, not frozen at t=0.
 *
 * Beyond the §4.3 contract createScene also returns two escape hatches, used by
 * the overlay, the mirror and the tests:
 *   render()  paints exactly one frame without running the loop.
 *   state     the live scene state that jarvisSceneStep() mutates.
 * ========================================================================== */

/* ---------------------------------------------------------------- tokens -- */
/* NOTE (deviation, deliberate): the shared palette is read from the global
 * JARVIS_TOKENS (10-theme.js) with a SPEC §3 fallback, but bound to a
 * uniquely-prefixed name. src/*.js are concatenated into ONE module by
 * scripts/build.py, so a bare top-level `const tokens` here would collide
 * with 10-theme.js ("tokens + CSS strings") and break the whole build. */
const JARVIS_SCENE_TOKENS = (typeof JARVIS_TOKENS !== 'undefined' && JARVIS_TOKENS) ? JARVIS_TOKENS : {
  bg: '#07080C', ink: '#0B0C0F', cobalt: '#2850E8', cobaltBright: '#3A62FF',
  wash: '#E5EBFF', coral: '#E85D4F', coralDeep: '#D14A3D', silver: '#8A93A6',
  bodyDark: '#C8CDD8', line: '#1F2229', cyan: '#35E0FF', violet: '#8B6CFF',
  magenta: '#FF4FD8', teal: '#2DD4BF', amber: '#FFB454', glow: 'rgba(58,98,255,.55)'
};

/* ---------------------------------------------------- Look v1.1 constants --
 * SPEC §3b: "the JARVIS color is so off from the command center… it has to
 * pop". The palette NAMES stay in 10-theme.js (owned elsewhere); how much
 * light this canvas puts on screen lives here, so the scene can be re-tuned
 * without touching the theme. Glow alphas are ~2x v1.0 across the board.   */
const JARVIS_LOOK = {
  /* color-mix(in srgb, #0B0C0F 78%, #2850E8 22%) computed for canvas 2D:
   * 11*.78+40*.22 = 17 | 12*.78+80*.22 = 27 | 15*.78+232*.22 = 63          */
  navy: [17, 27, 63],
  nebulaAlpha: 0.48,       /* nebula image, screen-blended over the navy      */
  gridAlpha: 0.075,        /* SPEC §3b: 6–9%                                  */
  vignette: 0.60,          /* pulls the field back down so the centre pops    */
  bgGlow: 0.22,            /* big soft cobalt-bright radial behind Agent 18–25 */
  cornerGlow: 0.15,        /* top-left cobalt wash                            */
  starAlpha: 0.52,
  agentHalo: 0.52,          /* kept for reference; §7.1 drives the halo from
                            * agentHaloR / agentHaloA times the eased `halo`    */
  agentImage: 0.74,         /* base alpha of the orb-agent plate (screen)       */
  agentTint: 0.26,          /* mode-colour wash over the plate (lighter)       */
  /* SPEC §7.1 replaced §3b's split swell (plate 1.08 / shell 1.35) with one
   * radius law for the whole ball — see agentR / speakBase / speakGain below. */
  boltMax: 7,              /* lightning filaments at voice 1.0                */
  brainHalo: 0.26,         /* was .13                                         */
  brainImage: 0.86,
  brainSpin: 132,          /* seconds per turn — constant, never voice-driven  */
  linkLine: 0.46,
  linkDash: 0.52,
  packetGlow: 0.9,
  senseLabel: 0.72,        /* SPEC §3b: labels wash ≥70%                      */
  fleetLabel: 0.78,
  tickRing: 0.62,
  /* ---- sizes: Jarvis mode v2 (SPEC §7.1 — Owner, 2026-09-19: "I want Jarvis
   * ball to look bigger. And when it speaks and thinks, it's more obvious.") --
   * agentR is a RULING, not a wish: jarvisGeometry() shrinks it only on a stage
   * so short that the brains would have nowhere left to stand (none of the four
   * sizes SPEC §7.1.1 lists lands there). The brains give way instead — they
   * keep their v1.3 size wherever the stage allows and shrink from there. */
  agentR: 0.235,            /* Agent's IDLE radius / min(w,h)   — SPEC §7.1.1    */
  speakBase: 1.04,         /* speaking radius = idle x (1.04 + 0.24 x voice)   */
  speakGain: 0.24,
  thinkScale: 0.78,        /* thinking / working radius = idle x 0.78          */
  brainWish: 0.0936,       /* brain radius / min(w,h) — v1.3's 0.13x0.45x1.60  */
  brainFloor: 0.030,       /* ...and the size below which the display dies     */
  brainDxWish: 0.19,       /* how far out the brain row likes to sit (of w)    */
  bottomPad: 10,           /* px the largest core keeps clear of the 17% band  */
  rail: 0.23,              /* SPEC §7.1.1: the left/right 23% are the rails    */
  agentTick0: 1.300,        /* tick ring inner — clears the 1.28 r0 speaking rim */
  agentTick1: 1.345,        /* tick ring outer (hot ticks reach +5 px)          */
  agentRing: 1.400,         /* Agent's dashed ring = his outermost CONSTANT chrome */
  agentLink: 1.430,         /* where a brain link leaves Agent (outside it all)  */
  agentHaloR: 1.55,         /* halo radius / r0 at halo = 1 (idle)              */
  agentHaloA: 0.22,         /* halo centre alpha at halo = 1 (idle)             */
  agentArc: 1.18,           /* the thinking/working arc, as a multiple of r     */
  shockRoom: 0.22,         /* how far past the peak core a shock ring may fly  */
  brainSeg: 1.18,          /* brain segmented ring                             */
  brainRing: 1.30,         /* brain dashed ring                                */
  brainLabel: 1.34,        /* brain label sits just outside its dashed ring    */
  brainLink: 1.24,         /* where a link arrives at a brain                  */
  sceneTop: 12,            /* px above the topmost brain label                 */
  brainGap: 10,            /* px between the brain ring and Agent's ring        */
  /* the AGENT / mode / live readout, under Agent's own ring */
  readoutGap: 10,          /* px between the dashed ring and the AGENT word   */
  readout3: 40,            /* px the AGENT + mode + live stack needs          */
  readout2: 26,            /* px for AGENT + the mode word                    */
  readout1: 13,            /* px for AGENT alone                              */
  /* the HUD chrome the canvas must not paint under, measured from 10-theme.js:
   * left rail = 30 + 300 + 2x11 padding + 2x1 border = 354 px of glass; right
   * column = 30 + 268 + 8 = 306 px. SPEC §7.1.1 widens both to 23% of the
   * width on a wide stage; the bigger of the two always wins.               */
  railW: 360,
  railH: 306,
  podColW: 306,
  /* SPEC §8 amendment B.3: the rails are COLUMNS of separate boxes with 4 px of
   * air between them, so a keep-out shaped like the first box lets a sense label
   * or dot show through the gaps (Owner saw one between SPEND and SCOREBOARD at
   * 1440x900). These four numbers are the columns themselves, read off the CSS in
   * 10-theme.js: .jv-top-left (top 26, left 30, bottom 206, 324 px of rail) and
   * .jv-right (top 26, right 30, bottom 56, 300 px wide). Six pixels of air are
   * added on the inner edge so a glow never licks the glass. */
  railFoot: 200,           /* px of stage below the LEFT column (bottom 206)   */
  podW: 336,               /* the RIGHT column: 300 + 30 right + 6 of air      */
  podFoot: 50              /* px of stage below the RIGHT column (bottom 56)   */
};

/* SPEC §7.1.5: every mode change eases over 350 ms — radius, brightness, halo,
 * colour. An exponential approach with this tau is ~95% there at 350 ms and
 * never pops, at any frame rate. */
const JARVIS_EASE = 0.1167;

/* --------------------------------------------------------------- helpers -- */
const JVS = {
  TAU: Math.PI * 2,
  MONO: "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace",
  SANS: "'DM Sans', system-ui, -apple-system, sans-serif",
  /* mode -> token key. Off-call is always dim silver (SPEC §3). */
  MODE: {
    idle: 'silver', listening: 'cyan', thinking: 'violet',
    speaking: 'cobaltBright', working: 'amber', muted: 'coral', sleeping: 'coral'
  },
  LANE: ['violet', 'cyan', 'teal', 'magenta', 'amber'],
  hex: function (v) {
    const m = /^#?([0-9a-f]{6})$/i.exec(String(v || '').trim());
    if (!m) return [138, 147, 166];
    const n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  },
  toHex: function (c) {
    const h = function (x) { const s = (Math.max(0, Math.min(255, Math.round(x)))).toString(16); return s.length < 2 ? '0' + s : s; };
    return '#' + (h(c[0]) + h(c[1]) + h(c[2])).toUpperCase();
  },
  rgba: function (c, a) { return 'rgba(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ',' + (Math.round(a * 1000) / 1000) + ')'; },
  lighten: function (c, k) { return [c[0] + (255 - c[0]) * k, c[1] + (255 - c[1]) * k, c[2] + (255 - c[2]) * k]; },
  shade: function (c, k) { return [c[0] * k, c[1] * k, c[2] * k]; },
  clamp01: function (v) { v = +v; return v > 0 ? (v < 1 ? v : 1) : 0; },
  /* frame-rate independent exponential approach — never snaps */
  approach: function (cur, target, dt, tau) { return cur + (target - cur) * (1 - Math.exp(-dt / (tau || 0.1))); },
  r6: function (v) { return Math.round(v * 1e6) / 1e6; },
  /* Fibonacci sphere — the eco page's point cloud, same language */
  fib: function (n) {
    const p = new Float32Array(n * 3), ga = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < n; i++) {
      const y = 1 - (i / (n - 1)) * 2, rr = Math.sqrt(Math.max(0, 1 - y * y)), th = ga * i;
      p[i * 3] = Math.cos(th) * rr; p[i * 3 + 1] = y; p[i * 3 + 2] = Math.sin(th) * rr;
    }
    return p;
  },
  /* depth-graded palette + bloom pass, ported from the eco page */
  STEPS: 18,
  mkPal: function (far, near) {
    const S = JVS.STEPS, P = new Array(S), B = new Array(S);
    for (let i = 0; i < S; i++) {
      const t = i / (S - 1);
      const c = [far[0] + (near[0] - far[0]) * t, far[1] + (near[1] - far[1]) * t, far[2] + (near[2] - far[2]) * t];
      P[i] = JVS.rgba(c, 0.035 + 0.90 * Math.pow(t, 2.05));
      B[i] = JVS.rgba(c, 0.012 + 0.070 * Math.pow(t, 3.0));
    }
    return { p: P, b: B };
  },
  mkSphere: function (n, rev, dir, ph, s0, s1) {
    return {
      n: n, pts: JVS.fib(n), px: new Float32Array(n), py: new Float32Array(n),
      ps: new Float32Array(n), pb: new Uint8Array(n),
      rev: rev, dir: dir, ph: ph, s0: s0, s1: s1, pal: null, bloom: null, key: ''
    };
  },
  /* rebuild a sphere palette only when the colour actually moved (>2/255) */
  tintSphere: function (sp, col) {
    const key = ((col[0] >> 1) << 16) | ((col[1] >> 1) << 8) | (col[2] >> 1);
    if (sp.key === key && sp.pal) return;
    const pal = JVS.mkPal(JVS.shade(col, 0.42), JVS.lighten(col, 0.72));
    sp.pal = pal.p; sp.bloom = pal.b; sp.key = key;
  },
  /* Look v1.1: explicit far/near ends, so Agent's shell can run the SPEC §3b
   * "cobalt-bright -> wash" gradient while still carrying the mode hue. */
  tintSphere2: function (sp, far, near) {
    const key = ((far[0] >> 2) << 18) | ((far[1] >> 2) << 12) | ((far[2] >> 2) << 6) | (near[0] >> 2);
    if (sp.key === key && sp.pal) return;
    const pal = JVS.mkPal(far, near);
    sp.pal = pal.p; sp.bloom = pal.b; sp.key = key;
  },
  mix: function (a, b, k) { return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]; },
  /* integer hash -> [0,1). Lets the lightning be regenerated every frame from
   * nothing but (epoch, index) — deterministic, and zero allocation. */
  hash: function (a, b) {
    let x = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) | 0;
    x = Math.imul(x ^ (x >>> 13), 1274126177);
    return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
  },
  fitText: function (ctx, s, maxW) {
    if (!ctx.measureText) return s;
    if (ctx.measureText(s).width <= maxW) return s;
    let out = s;
    while (out.length > 1 && ctx.measureText(out + '…').width > maxW) out = out.slice(0, -1);
    return out + '…';
  }
};

/* ============================ IMAGE LAYER ================================
 * SPEC §3b: Agent and the three brains are the Brain Command Center's plasma
 * spheres, composited with `screen` so their black backgrounds vanish. The
 * bytes arrive as data URIs in JARVIS_ASSETS (src/35-assets.js, generated).
 *
 * Rules kept here: each JPEG is decoded ONCE per scene into an <img>, then
 * rasterised into an offscreen canvas at the layout size and reused every
 * frame; the caches are dropped on setSize() and released by destroy(). When
 * there is no DOM at all (node tests, the pure-module path) every helper
 * returns null and the scene paints exactly as it did without art.
 * ========================================================================= */
const JARVIS_ORB_KEYS = ['orbAgent', 'orbBrain1', 'orbBrain2', 'orbBrain3'];

function jarvisNewCanvas(w, h) {
  try {
    if (typeof document === 'undefined' || !document || typeof document.createElement !== 'function') return null;
    const cv = document.createElement('canvas');
    cv.width = Math.max(1, Math.round(w)); cv.height = Math.max(1, Math.round(h));
    return cv.getContext && cv.getContext('2d') ? cv : null;
  } catch (e) { return null; }
}

function jarvisImagesInit(st) {
  if (st.imgInit) return st.img;
  st.imgInit = true;
  st.img = null;
  const A = (typeof JARVIS_ASSETS !== 'undefined' && JARVIS_ASSETS) ? JARVIS_ASSETS : null;
  if (!A) return null;
  let Ctor = null;
  try { Ctor = (typeof Image === 'function') ? Image : null; } catch (e) { Ctor = null; }
  if (!Ctor || !jarvisNewCanvas(2, 2)) return null;
  const bag = {};
  const keys = ['bgNebula', 'orbAgent', 'orbBrain1', 'orbBrain2', 'orbBrain3'];
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i], src = A[k];
    if (!src) continue;
    const rec = { img: null, ready: false, cv: null, size: 0 };
    try {
      const im = new Ctor();
      im.onload = function () { rec.ready = true; rec.cv = null; rec.size = 0; st.bg = null; };
      im.onerror = function () { rec.ready = false; };
      im.src = src;
      if (im.complete && im.naturalWidth > 0) rec.ready = true;
      rec.img = im;
    } catch (e) { rec.img = null; }
    bag[k] = rec;
  }
  st.img = bag;
  return bag;
}

/* A square orb plate at `size` px, black background intact (the caller
 * composites with `screen`, which eats it). Rebuilt only when size changes. */
function jarvisOrb(st, key, size) {
  const bag = st.img;
  if (!bag) return null;
  const rec = bag[key];
  if (!rec || !rec.ready || !rec.img) return null;
  size = Math.max(24, Math.min(1024, Math.round(size)));
  if (rec.cv && rec.size === size) return rec.cv;
  const cv = jarvisNewCanvas(size, size);
  if (!cv) return null;
  try {
    const c2 = cv.getContext('2d');
    c2.clearRect(0, 0, size, size);
    c2.drawImage(rec.img, 0, 0, size, size);
  } catch (e) { return null; }
  rec.cv = cv; rec.size = size;
  return cv;
}

/* Everything static about the background, composed once per size into one
 * offscreen canvas: navy, the nebula, the corner washes, the big cobalt glow
 * behind Agent, the vignette. One drawImage per frame instead of six fills. */
function jarvisBackplate(st) {
  const bp = st.bg;
  if (bp && bp.w === st.w && bp.h === st.h) return bp.cv;
  const cv = jarvisNewCanvas(st.w, st.h);
  if (!cv) return null;
  let c2 = null;
  try { c2 = cv.getContext('2d'); } catch (e) { c2 = null; }
  if (!c2) return null;
  jarvisDrawBackplate(c2, st);
  st.bg = { cv: cv, w: st.w, h: st.h };
  return cv;
}

function jarvisReleaseImages(st) {
  const bag = st.img;
  if (bag) {
    for (const k in bag) {
      const rec = bag[k];
      if (!rec) continue;
      try { if (rec.img) { rec.img.onload = null; rec.img.onerror = null; rec.img.src = ''; } } catch (e) { /* noop */ }
      rec.img = null; rec.cv = null; rec.ready = false; rec.size = 0;
    }
  }
  st.img = null; st.bg = null; st.imgInit = false;
}

/* ------------------------------------------------------------ state init -- */
function jarvisInitState(o) {
  o = o || {};
  const st = {
    __jarvis: true,
    seed: o.seed == null ? 20260918 : o.seed,
    w: o.w || o.width || 1200, h: o.h || o.height || 760,
    dpr: o.dpr || 1,
    reducedMotion: !!o.reducedMotion,
    t: 0, raw: 0, frames: 0, waiting: true,
    agent: {
      r: 0, r0: 0, rTarget: 0, breathPh: 0, breath: 1,
      /* the four eased numbers of SPEC §7.1: 1 = his idle look, and the paint
       * scales strictly with them, so a test that pins the number pins the
       * picture. plasma is SIGNED — negative means the shell swirls INWARD. */
      bright: 1, halo: 1, plasma: 1, plasmaT: 0, boltT: 0, swirl: 0,
      fx: 0, clock: 0,                  /* fx = how much of SPEAKING is in force */
      arc: null, arcKind: 'thinking', arcOn: 0, arcPh: 0,
      shocks: [], shockAt: -9, vhT: null, vhV: null, vhI: 0,
      mode: 'idle', call: 'off', live: '', demo: false, voice: 0, mic: 0,
      col: JVS.hex(JARVIS_SCENE_TOKENS.silver), modeCol: JARVIS_SCENE_TOKENS.silver,
      micAcc: 0, ripples: [], sphere: null
    },
    brains: [], links: [], senses: [], fleet: [], stars: [],
    labels: { agent: 'Agent', owner: 'Owner' },
    sensesOrbit: 0, starDrift: 0, geo: null, cache: {},
    /* Look v1.1 image layer — filled lazily, only where a DOM exists */
    img: null, imgInit: false, bg: null,
    /* scratch vectors — reused every frame so the hot paths allocate nothing */
    vec: [0, 0], vecA: [0, 0], vecB: [0, 0], vecZ: [0, 0]
  };
  for (let i = 0; i < 6; i++) st.agent.ripples.push({ on: false, p: 0 });
  /* shock rings (SPEC §7.1.2) and the 120 ms voice window that spawns them —
   * fixed pools, so a peak never allocates mid-frame */
  for (let i = 0; i < 4; i++) st.agent.shocks.push({ on: false, p: 0, r: 0 });
  st.agent.vhT = new Float64Array(8); st.agent.vhV = new Float64Array(8);
  /* starfield — seeded, deterministic, allocated once */
  let s = st.seed >>> 0;
  const rnd = function () { s = (s + 0x6D2B79F5) >>> 0; let x = s; x = Math.imul(x ^ (x >>> 15), x | 1); x ^= x + Math.imul(x ^ (x >>> 7), x | 61); return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
  for (let i = 0; i < 96; i++) st.stars.push({ x: rnd(), y: rnd(), z: 0.25 + rnd() * 0.75, ph: rnd() * JVS.TAU, vx: (rnd() - 0.5) * 0.004 });
  st.agent.sphere = JVS.mkSphere(760, 26, 1, 0, 0.7, 2.5);
  jarvisGeometry(st);
  return st;
}

/* Layout, recomputed on resize only. All link endpoints use the IDLE radius
 * r0 — never the mode/voice radius — so nothing on a link can inherit presence.
 *
 * SPEC §7.1.1 turned this solve upside down. Agent's idle radius is now a
 * RULING (min(w,h) x 0.235) instead of the wish the old chain shrank; what
 * gives way is the brain row, which keeps its v1.3 size only where the stage
 * has room for it. Four clearances are law at 1440x900, 1920x1080, 2560x1440
 * and 3440x1440, measured against the LARGEST speaking core (idle x 1.28):
 *   - the brain nodes and their labels          (solved here: brainR, brainY)
 *   - the bottom 17% (captions ribbon, ticker)  (solved here: cy)
 *   - the left and right 23% rails              (checked: rMax < 0.27 w)
 * tests/scene.test.mjs pins all four.                                      */
function jarvisGeometry(st) {
  const w = st.w, h = st.h, m = Math.min(w, h), L = JARVIS_LOOK;
  const g = st.geo || (st.geo = {});
  const nb = st.brains.length, nbb = Math.max(2, nb);
  const head = L.sceneTop + 22;              /* top margin + the label band    */
  const den = L.brainLabel + L.brainRing;    /* the brain chain, per radius    */
  const swell = L.speakBase + L.speakGain;   /* 1.28 — the loudest core        */
  const floorR = m * L.brainFloor;

  /* --- 1. Agent. The centre rides at 57% of the height and comes up only as
   * far as it takes to keep the loudest core out of the bottom 17% band. --- */
  const cyOf = function (rr) { return Math.min(h * 0.57, h * 0.83 - rr * swell - L.bottomPad); };
  /* the rails are a share of the WIDTH, so on a narrow or portrait stage they
   * bind before the height does: the loudest core may never pass 0.27 w. At
   * the four sizes SPEC §7.1.1 lists this is slack and 0.235 rules. */
  let r0 = Math.min(m * L.agentR, w * (0.5 - L.rail) / swell);
  if (nb > 0) {
    /* a stage too short for both: he gives way rather than standing on them.
     * None of the four sizes in SPEC §7.1.1 reaches this branch.            */
    const need = head + den * floorR + L.brainGap;
    const capA = (h * 0.83 - L.bottomPad - need) / (swell + L.agentRing);
    const capB = (h * 0.57 - need) / L.agentRing;
    r0 = Math.min(r0, Math.max(m * 0.06, Math.min(capA, capB)));
  }
  g.r0 = r0;
  g.rMax = r0 * swell;                       /* the core at its very largest   */
  g.ringOut = r0 * L.agentRing;               /* his outermost CONSTANT chrome  */
  g.cx = w * 0.5;
  g.cy = cyOf(r0);
  /* SPEC §8 amendments C10: the two rails SCALE with the display, so the
   * columns this canvas keeps clear scale with them. Same two thresholds as
   * the overlay's own jarvisRailScale() (50-overlay.js), read off the same
   * viewport width, so the glass and the keep-out can never disagree. The
   * columns themselves are rebuilt from the scaled glass: left = 30 margin +
   * 324 of rail + 6 of air, right = 300 of rail + 30 margin + 6 of air. */
  const railK = w >= 3000 ? 1.4 : (w >= 2200 ? 1.25 : 1);
  g.railK = railK;
  const railColW = 30 + 324 * railK + 6;
  const podColW = 300 * railK + 30 + 6;
  g.railL = Math.max(w * L.rail, railColW);
  g.railR = Math.max(w * L.rail, podColW - 30);
  g.fleetY = h - 82; g.fleetX0 = w * 0.32; g.fleetX1 = w * 0.68;
  g.fleetRise = Math.min(h * 0.028, 26);

  /* --- 2. the brains: today's size wherever the room allows, never smaller
   * than the floor, and smaller again when the feed sends more than three. - */
  let brainR = Math.min(m * L.brainWish, (g.cy - g.ringOut - L.brainGap - head) / den);
  if (nb > 3) brainR = Math.min(brainR, m * L.brainWish * Math.sqrt(3 / nb));
  g.brainR = brainR = Math.max(floorR, brainR);
  const bring = L.brainRing * brainR;
  g.brainY = head + L.brainLabel * brainR;
  g.brainCurv = brainR * 0.9;

  /* --- 3. how wide the row sits: far enough out that the END brains clear
   * his ring too, not so far that they climb into a rail. --- */
  const dyEnd = g.cy - g.brainY - g.brainCurv;
  const needR = g.ringOut + bring + L.brainGap;
  const dxRing = dyEnd >= needR ? 0 : Math.sqrt(Math.max(0, needR * needR - dyEnd * dyEnd));
  const dxMin = Math.max(bring * 2 + 12, dxRing);
  const dxMax = Math.max(bring, Math.min(g.cx - g.railL, w - g.railR - g.cx) - bring - 6);
  let dx = Math.max(w * L.brainDxWish, dxMin, (nbb - 1) * (bring + 6) * 0.5);
  /* a stage narrow enough that the fixed rails leave no room at all: sitting
   * under a rail is a smaller lie than three brains stacked on one another,
   * so the row keeps its minimum and the clamp stands down. */
  if (dx > dxMax && dxMax >= dxMin) dx = dxMax;
  else if (dx > dxMax) dx = dxMin;
  g.brainDx = dx;

  g.senseCx = w * 0.5; g.senseCy = h * 0.5;
  g.senseRx = w * 0.47; g.senseRy = h * 0.46;
  /* AGENT / mode / live ride under Agent's own ring; how many of the three lines
   * fit is a reading of the room left above the fleet band, not a guess. */
  g.textY = g.cy + g.ringOut + L.readoutGap;
  if (g.textY + L.readout1 > g.fleetY - 9) {
    g.textY = Math.max(g.cy + g.rMax + 4, g.fleetY - 9 - L.readout1);
  }
  const tr = g.fleetY - 9 - g.textY, eps = 0.5;
  g.textLines = tr >= L.readout3 - eps ? 3 : (tr >= L.readout2 - eps ? 2 : (tr >= L.readout1 - eps ? 1 : 0));
  /* Transparent HUD text the overlay owns (10-theme.js): the title + chip row,
   * the bottom-left mode word and captions, the ESC hint and the ticker rail.
   * The glass pods are opaque and paint OVER the canvas, so they need no entry;
   * these do, because a sense label under them would read as a collision. */
  /* SPEC §8 amendment B.3: each rail is ONE column, from the top of its first
   * box to the bottom of the last one its container allows — the 4 px gaps
   * between the boxes are inside it, which is where the labels were showing
   * through. Everything else here is unchanged HUD text the canvas must not
   * paint under. */
  g.railCols = [
    [0, 0, railColW, Math.max(L.railH, h - L.railFoot)],
    [w - podColW, 0, w, Math.max(L.railH, h - L.podFoot)]
  ];
  g.keepOut = [
    g.railCols[0],
    g.railCols[1],
    [0, h - 192, 430, h - 50],
    [w * 0.5 - 60, h - 52, w * 0.5 + 60, h - 30],
    [0, h - 32, w, h]
  ];
  /* --- 4. Agent's AIRSPACE. SPEC §0 law 2: the brains are a display and never
   * react to voice, so a mic ripple or a shock ring that crossed a brain ring
   * would read as exactly the reaction the law forbids. Everything his voice
   * moves stays inside this radius. (His tick ring and dashed ring are NOT in
   * this rule — they are constant chrome and turn whatever anyone says.)    */
  let nearEdge = Infinity;
  const bp = [0, 0];                    /* resize-time only: one scratch pair */
  for (let i = 0; i < nb; i++) {
    jarvisBrainPos(st, i, nb, bp);
    const bx = bp[0] - g.cx, by = bp[1] - g.cy;
    const d = Math.sqrt(bx * bx + by * by) - bring;
    if (d < nearEdge) nearEdge = d;
  }
  g.nearEdge = nearEdge;
  g.airspace = Math.min(g.rMax + g.r0 * L.shockRoom, nearEdge === Infinity ? Infinity : nearEdge - 5);
  if (!(g.airspace > g.r0 * 1.06)) g.airspace = g.r0 * 1.06;
  g.rippleR0 = g.r0 * 1.02;
  g.rippleR1 = g.airspace;
  g.small = m < 560;
  g.labels = m >= 460 && w >= 720;
  /* SPEC §8 amendment C11: a brain's NAME is part of the display, and a sense
   * dot was sitting on BRAIN 3 BRAIN in the 1440x900 renders. Each label band is
   * a keep-out of its own now, exactly like a rail column — the whole reading
   * stands down there, mark and name together — so nothing of the senses ring
   * ever prints over a brain's name. The numbers are read straight off
   * jarvisPaintBrains(): centred on the node, baseline 11 px above the dashed
   * ring, its text capped at 0.19 w wide (JVS.fitText), mono at 10.5 px (9.5
   * on a small stage). Neither the orb nor a brain moves for this: it is a
   * region the ring's marks avoid, nothing more. */
  g.brainLabels = [];
  if (g.labels) {
    const halfL = w * 0.095, lineH = (g.small ? 9.5 : 10.5) * 1.3;
    for (let i = 0; i < nb; i++) {
      jarvisBrainPos(st, i, nb, bp);
      const by = bp[1] - L.brainLabel * g.brainR - 11;
      g.brainLabels.push([bp[0] - halfL, by - lineH, bp[0] + halfL, by + 3]);
    }
    g.keepOut = g.keepOut.concat(g.brainLabels);
  }
  /* the orb plate is rasterised just past its LOUDEST drawn diameter so a
   * voice swell never up-samples it; quantised so a 1 px resize is not a
   * re-raster. 2.63 is the sphere's share of the JPEG. */
  g.agentPlate = Math.round(g.rMax * 2.72 / 16) * 16;
  g.brainPlate = Math.round(g.brainR * 3.4 / 16) * 16;
  st.cache = {};                       /* cached gradients are size-bound */
  st.bg = null;                        /* and so is the composed backplate */
  const bag = st.img;                  /* SPEC §3b: caches rebuilt on setSize */
  if (bag) for (let i = 0; i < JARVIS_ORB_KEYS.length; i++) {
    const rec = bag[JARVIS_ORB_KEYS[i]];
    if (rec) { rec.cv = null; rec.size = 0; }
  }
  return g;
}

/* True when (x,y) falls inside one of the two RAIL COLUMNS (SPEC §8 amendment
 * B.3). A sense reading asks this BEFORE it draws: the dot, its tick and its
 * name are one thing, and none of the three may land in a column — not on a
 * box, and not in the air between two boxes. The reading is not moved and
 * nothing is invented; it simply waits for the ring to carry it clear.
 * `pad` is the room the mark itself needs (the glow is 5.2 px, the tick 5). */
function jarvisRailZone(st, x, y, pad) {
  const g = st.geo, cols = g && g.railCols;
  if (!cols) return false;
  const m = pad || 0;
  for (let i = 0; i < cols.length; i++) {
    const r = cols[i];
    if (x > r[0] - m && x < r[2] + m && y > r[1] - m && y < r[3] + m) return true;
  }
  return false;
}

/* True when (x,y) falls inside one of the BRAIN NAME LABELS (SPEC §8 amendment
 * C11). Same law as a rail column: a sense reading asks this before it draws,
 * and the dot, its tick and its name all stand down together rather than print
 * over a brain's name. The reading is not moved and nothing is invented — it
 * waits for the ring to carry it clear. */
function jarvisBrainLabelZone(st, x, y, pad) {
  const g = st.geo, boxes = g && g.brainLabels;
  if (!boxes) return false;
  const m = pad || 0;
  for (let i = 0; i < boxes.length; i++) {
    const r = boxes[i];
    if (x > r[0] - m && x < r[2] + m && y > r[1] - m && y < r[3] + m) return true;
  }
  return false;
}

/* True when (x,y) is already spoken for: a brain node (its rings, or the band
 * its label sits in), a fleet node, the fleet caption, or a rail column. The
 * senses ring orbits through the whole frame, so its labels ask this before
 * picking a side — the reading itself (dot + tick) is drawn either way,
 * unless a rail column already turned the whole reading away above. */
function jarvisNodeZone(st, x, y) {
  const g = st.geo, n = st.brains.length, pos = st.vecZ;
  if (!g) return false;
  const ring = JARVIS_LOOK.brainRing * g.brainR + 22;
  const lab = JARVIS_LOOK.brainLabel * g.brainR + 17, halfW = st.w * 0.11;
  for (let i = 0; i < n; i++) {
    jarvisBrainPos(st, i, n, pos);
    const dx = x - pos[0], dy = y - pos[1];
    if (dx * dx + dy * dy < ring * ring) return true;
    if (Math.abs(dx) < halfW && Math.abs(dy + lab) < 30) return true;
  }
  const nf = st.fleet.length;
  for (let i = 0; i < nf; i++) {
    const u = nf === 1 ? 0.5 : i / (nf - 1), uu = u * 2 - 1;
    const fx = g.fleetX0 + (g.fleetX1 - g.fleetX0) * u, fy = g.fleetY - g.fleetRise * uu * uu;
    const dx = x - fx, dy = y - fy;
    if (dx * dx + dy * dy < 576) return true;                 /* 24 px around a node */
  }
  if (nf && Math.abs(x - (g.fleetX0 + g.fleetX1) * 0.5) < st.w * 0.10 &&
      y > g.fleetY + 4 && y < g.fleetY + 30) return true;     /* the FLEET caption  */
  const ko = g.keepOut;
  if (ko) for (let i = 0; i < ko.length; i++) {
    const r = ko[i];
    if (x > r[0] && x < r[2] && y > r[1] && y < r[3]) return true;
  }
  return false;
}

/* brain node centre for index i of n, on the arc laid out by jarvisGeometry:
 * symmetric about Agent, highest in the middle, dipping by brainCurv at the ends */
function jarvisBrainPos(st, i, n, out) {
  const g = st.geo, u = n <= 1 ? 0.5 : i / (n - 1), v = u * 2 - 1;
  out[0] = g.cx + v * g.brainDx;
  out[1] = g.brainY + g.brainCurv * v * v;
  return out;
}

/* ------------------------------------------------------------ data apply -- */
/* Honesty rule: nothing is drawn that is not in `data`. Reconcile by id so a
 * 30 s poll never resets a ring's phase (no visible stutter). */
function jarvisApplyData(st, data) {
  if (!data) return st;
  let fleetVisible = true;
  if (data.settings && typeof data.settings === 'object') {
    st.labels = {
      agent: String(data.settings.agent_name || 'Agent'),
      owner: String(data.settings.owner_label || 'Owner')
    };
    if (Array.isArray(data.settings.enabled_boxes)) {
      fleetVisible = data.settings.enabled_boxes.indexOf('fleet') >= 0;
    }
  }
  if (Array.isArray(data.brains)) {
    const prev = st.brains, prevL = st.links, next = [], links = [];
    for (let i = 0; i < data.brains.length; i++) {
      const d = data.brains[i] || {}, id = String(d.id == null ? ('brain-' + i) : d.id);
      let b = null, k = 0;
      for (; k < prev.length; k++) if (prev[k].id === id) { b = prev[k]; break; }
      if (!b) {
        b = {
          id: id, ring: 0, scan: 0, ph: i * 1.7,
          ringSpd: 0.22 + i * 0.07, ringDir: i % 2 ? -1 : 1, scanSpd: 0.17 + i * 0.04,
          sphere: JVS.mkSphere(300, 26 + i * 4, i % 2 ? -1 : 1, i * 1.3, 0.7, 1.9)
        };
      }
      b.label = String(d.label || d.name || 'BRAIN');
      /* honesty: only an explicit 'ok' is an ok reading — a missing status is unknown */
      b.status = d.status === 'unreachable' ? 'unreachable' : (d.status === 'ok' ? 'ok' : 'unknown');
      b.dim = b.status === 'unreachable' ? 0.35 : (b.status === 'unknown' ? 0.62 : 1);
      /* SPEC §3b: each brain wears its own plasma sphere. Match on the id or
       * label the feed actually gave us; an unrecognised brain falls back to
       * a hue by index and keeps the plate rotation of that slot. */
      b.asset = JARVIS_ORB_KEYS[1 + (i % 3)];
      b.lane = ['magenta', 'cyan', 'teal'][i % 3];
      next.push(b);
      /* link + packets: reuse the old link when the brain is the same id */
      let L = null;
      for (let q = 0; q < prevL.length; q++) if (prevL[q].id === id) { L = prevL[q]; break; }
      if (!L) {
        const count = 2 + (i % 3), packets = [];
        for (let p = 0; p < count; p++) {
          packets.push({ p: (p + 1) / (count + 1), dir: p % 2 ? -1 : 1, spd: 0.14 + 0.025 * i + 0.02 * p, on: true });
        }
        L = { id: id, i: i, on: true, packets: packets };
      }
      L.i = i;
      L.on = b.status !== 'unreachable';
      for (let p = 0; p < L.packets.length; p++) L.packets[p].on = L.on;
      links.push(L);
    }
    const countChanged = prev.length !== next.length;
    st.brains = next; st.links = links;
    /* the brain count is part of the layout chain (radius, arc, Agent's centre),
     * so a feed that adds or drops a brain re-solves the whole geometry. A poll
     * that returns the same brains must NOT, or it would drop the backplate. */
    if (st.geo && countChanged) jarvisGeometry(st);
  }
  if (Array.isArray(data.senses)) {
    const prev = st.senses, next = [], lim = Math.min(12, data.senses.length);
    for (let i = 0; i < lim; i++) {
      const d = data.senses[i] || {}, id = String(d.id == null ? ('sense-' + i) : d.id);
      let s = null;
      for (let k = 0; k < prev.length; k++) if (prev[k].id === id) { s = prev[k]; break; }
      if (!s) s = { id: id, ph: i * 0.9 };
      s.label = String(d.label || d.name || id);
      s.status = d.status === 'unreachable' ? 'unreachable' : (d.status === 'ok' ? 'ok' : 'unknown');
      s.dim = s.status === 'unreachable' ? 0.3 : (s.status === 'unknown' ? 0.55 : 1);
      next.push(s);
    }
    st.senses = next;
  }
  if (Array.isArray(data.fleet) || !fleetVisible) {
    const fleetRows = fleetVisible && Array.isArray(data.fleet) ? data.fleet : [];
    const prev = st.fleet, next = [];
    for (let i = 0; i < fleetRows.length; i++) {
      const d = fleetRows[i] || {}, id = String(d.id == null ? ('agent-' + i) : d.id);
      let f = null;
      for (let k = 0; k < prev.length; k++) if (prev[k].id === id) { f = prev[k]; break; }
      if (!f) f = { id: id, ph: i * 0.61 };
      f.label = String(d.label || d.name || id);
      f.busy = !!d.busy;
      next.push(f);
    }
    st.fleet = next;
  }
  st.waiting = st.brains.length === 0 && st.senses.length === 0 && st.fleet.length === 0;
  return st;
}

/* ------------------------------------------------------- the step (pure) -- */
/* `state` may be a live state or a plain init descriptor ({w,h,seed,…}). */
function jarvisSceneStep(state, dtMs, presence, data) {
  const st = (state && state.__jarvis) ? state : jarvisInitState(state || {});
  if (data !== undefined && data !== null) jarvisApplyData(st, data);

  let dt = (+dtMs || 0) / 1000;
  if (!(dt > 0)) dt = 0;
  if (dt > 0.2) dt = 0.2;                                   /* tab-switch guard */
  const sdt = st.reducedMotion ? dt * 0.5 : dt;             /* halved, never frozen */
  st.raw += dt; st.t += sdt; st.frames++;

  /* ---- LAW 3: the world layer. Reads scene time. Never reads presence. ---- */
  st.sensesOrbit = (st.t * (JVS.TAU / 90)) % JVS.TAU;
  st.starDrift = (st.starDrift + sdt * 0.02) % 1;
  for (let i = 0; i < st.brains.length; i++) {
    const b = st.brains[i];
    b.ring = (b.ring + b.ringSpd * b.ringDir * sdt) % JVS.TAU;
    b.scan = (b.scan + b.scanSpd * sdt) % 1;
  }
  for (let i = 0; i < st.links.length; i++) {
    const L = st.links[i];
    if (!L.on) continue;
    for (let k = 0; k < L.packets.length; k++) {
      const pk = L.packets[k];
      pk.p += pk.spd * sdt;
      if (pk.p > 1) pk.p -= Math.floor(pk.p);
    }
  }
  for (let i = 0; i < st.stars.length; i++) {
    const s = st.stars[i];
    s.x += s.vx * sdt;
    if (s.x > 1.05) s.x -= 1.1; else if (s.x < -0.05) s.x += 1.1;
  }

  /* ---- LAW 1: Agent. The ONLY reader of `presence` in this file. ---- */
  jarvisStepAgent(st, sdt, presence);
  return st;
}

function jarvisStepAgent(st, dt, presence) {
  const a = st.agent, p = presence || null, L = JARVIS_LOOK, E = JARVIS_EASE;
  const call = (p && p.call) || 'off';
  const on = call === 'on';
  const lv = (p && p.levels) || null;
  const voice = on ? JVS.clamp01(lv ? lv.voice : 0) : 0;
  const mic = on ? JVS.clamp01(lv ? lv.mic : 0) : 0;

  a.call = call;
  a.mode = (p && p.mode) || 'idle';
  a.live = (p && p.live) || '';
  a.demo = !!(p && p.demo);
  a.clock += dt;
  /* a second smoothing stage: fast attack, slow release, so the orb never jitters */
  a.voice = JVS.approach(a.voice, voice, dt, voice > a.voice ? 0.05 : 0.20);
  a.mic = JVS.approach(a.mic, mic, dt, mic > a.mic ? 0.05 : 0.20);

  const speaking = on && a.mode === 'speaking';
  const busy = on && (a.mode === 'thinking' || a.mode === 'working');
  /* Lightning and shock rings belong to SPEAKING (SPEC §7.1.2). Easing this
   * gate is what keeps SPEC §7.1.3's "nothing else distinguishes thinking from
   * working" true even when a tool call arrives mid-sentence. */
  a.fx = JVS.approach(a.fx, speaking ? 1 : 0, dt, E);

  /* ---- the breath: 4 s and +/-2% while he thinks or works (SPEC §7.1.3);
   * today's slow breath everywhere else; none while he speaks or listens,
   * where §7.1.2 / §7.1.4 pin the radius to an exact number. ---- */
  const bPer = busy ? 4 : (on ? 3.5 : 6);
  const bAmp = busy ? 0.02 : ((speaking || (on && a.mode === 'listening')) ? 0 : (on ? 0.014 : 0.024));
  a.breathPh = (a.breathPh + dt * (JVS.TAU / bPer)) % JVS.TAU;
  a.breath = 1 + bAmp * Math.sin(a.breathPh);

  a.r0 = st.geo ? st.geo.r0 : Math.min(st.w, st.h) * L.agentR;

  /* ---- the four numbers every mode is made of. 1 = his idle look. ---- */
  let rk, bright, halo, plasma;
  if (speaking) {                       /* SPEC §7.1.2 — glows more, moves more */
    rk = L.speakBase + L.speakGain * a.voice;
    bright = 1.22 + 0.95 * a.voice;     /* at voice 0 already brighter than idle */
    halo = 1.12 + 1.30 * a.voice;       /* radius AND alpha scale with this: x2.16 */
    plasma = 1.15 + 2.20 * a.voice;     /* x2.91 from voice 0 to voice 1        */
  } else if (busy) {                    /* SPEC §7.1.3 — shrinks, darkens, swirls in */
    rk = L.thinkScale * a.breath;
    bright = 0.40; halo = 0.30; plasma = -0.45;      /* negative = inward       */
  } else if (on && a.mode === 'listening') {         /* SPEC §7.1.4 — idle x 1.0 */
    rk = 1; bright = 1.02; halo = 1.00; plasma = 1.10;
  } else if (on) {                                   /* idle / muted / sleeping  */
    rk = a.breath; bright = 1; halo = 1; plasma = 1;
  } else {                                           /* off call: dim, slow      */
    rk = a.breath; bright = 0.52; halo = 0.45; plasma = 0.60;
  }
  a.rTarget = a.r0 * rk;
  a.r = a.r > 0 ? JVS.approach(a.r, a.rTarget, dt, E) : a.rTarget;
  a.bright = JVS.approach(a.bright, bright, dt, E);
  a.halo = JVS.approach(a.halo, halo, dt, E);
  a.plasma = JVS.approach(a.plasma, plasma, dt, E);
  a.plasmaT += dt * a.plasma;               /* the shell's own clock, SIGNED    */
  a.boltT += dt * Math.min(3.6, Math.abs(a.plasma));
  a.swirl = a.plasma < 0 ? (a.swirl + dt * 0.30 * -a.plasma) % 1 : 0;

  /* ---- the one thin arc that keeps a small dark orb from reading as dead --- */
  a.arc = busy ? (a.mode === 'working' ? 'working' : 'thinking') : null;
  if (a.arc) a.arcKind = a.arc;
  a.arcOn = JVS.approach(a.arcOn, a.arc ? 1 : 0, dt, E);
  /* 0.5 rev/s — reduced motion leaves it a static mark (SPEC §7.1.5) */
  if (!st.reducedMotion) a.arcPh = (a.arcPh + dt * JVS.TAU * 0.5) % JVS.TAU;

  const key = on ? (JVS.MODE[a.mode] || 'silver') : 'silver';
  a.modeCol = JARVIS_SCENE_TOKENS[key] || JARVIS_SCENE_TOKENS.silver;
  const target = JVS.hex(a.modeCol);
  const k = 1 - Math.exp(-dt / E);
  a.col[0] += (target[0] - a.col[0]) * k;
  a.col[1] += (target[1] - a.col[1]) * k;
  a.col[2] += (target[2] - a.col[2]) * k;

  /* ---- shock rings on a voice PEAK (SPEC §7.1.2): a rise of more than 0.18
   * inside 120 ms, at most one every 260 ms, gone in ~900 ms. ---- */
  const HT = a.vhT, HV = a.vhV, hn = HT.length;
  let vMin = a.voice;
  for (let i = 0; i < hn; i++) if (HT[i] > a.clock - 0.12 && HV[i] < vMin) vMin = HV[i];
  HT[a.vhI] = a.clock; HV[a.vhI] = a.voice; a.vhI = (a.vhI + 1) % hn;
  if (a.fx > 0.5 && a.voice - vMin > 0.18 && a.clock - a.shockAt >= 0.26) {
    a.shockAt = a.clock;
    for (let i = 0; i < a.shocks.length; i++) {
      if (a.shocks[i].on) continue;
      a.shocks[i].on = true; a.shocks[i].p = 0; a.shocks[i].r = a.r || a.r0;
      break;
    }
  }
  for (let i = 0; i < a.shocks.length; i++) {
    const sh = a.shocks[i];
    if (!sh.on) continue;
    sh.p += dt / 0.9;
    if (sh.p >= 1) { sh.on = false; sh.p = 0; }
  }

  /* mic -> inward-travelling ripples (Owner speaking). Fixed pool, no allocs. */
  if (on && a.mic > 0.05) {
    a.micAcc += dt * (0.7 + 4.0 * a.mic);
    if (a.micAcc >= 1) {
      a.micAcc = 0;
      for (let i = 0; i < a.ripples.length; i++) if (!a.ripples[i].on) { a.ripples[i].on = true; a.ripples[i].p = 1; break; }
    }
  } else if (a.micAcc > 1) { a.micAcc = 1; }
  for (let i = 0; i < a.ripples.length; i++) {
    const r = a.ripples[i];
    if (!r.on) continue;
    r.p -= dt / 1.4;
    if (r.p <= 0) { r.on = false; r.p = 0; }
  }
}

/* -------------------------------------------------------------- snapshot -- */
function jarvisSceneSnapshot(st) {
  const a = st.agent, r6 = JVS.r6;
  let rip = 0; for (let i = 0; i < a.ripples.length; i++) if (a.ripples[i].on) rip++;
  let shk = 0; for (let i = 0; i < a.shocks.length; i++) if (a.shocks[i].on) shk++;
  const brains = [], links = [], fleet = [];
  for (let i = 0; i < st.brains.length; i++) {
    const b = st.brains[i];
    brains.push({ id: b.id, label: b.label, status: b.status, dim: r6(b.dim), ring: r6(b.ring), scan: r6(b.scan) });
  }
  for (let i = 0; i < st.links.length; i++) {
    const L = st.links[i], ps = [];
    let act = 0;
    for (let k = 0; k < L.packets.length; k++) { ps.push(r6(L.packets[k].p)); if (L.packets[k].on) act++; }
    links.push({ id: L.id, on: L.on, packets: ps, active: act });
  }
  let busy = 0;
  for (let i = 0; i < st.fleet.length; i++) {
    const f = st.fleet[i];
    if (f.busy) busy++;
    fleet.push({ id: f.id, busy: f.busy, phase: r6((st.t * 0.9 + f.ph) % JVS.TAU) });
  }
  let sdim = 0; for (let i = 0; i < st.senses.length; i++) if (st.senses[i].status === 'unreachable') sdim++;
  return {
    t: r6(st.t), raw: r6(st.raw), frames: st.frames, w: st.w, h: st.h,
    reducedMotion: st.reducedMotion, waiting: st.waiting, starDrift: r6(st.starDrift),
    /* SPEC §7.1.6 — everything the mode rulings are made of, so a test can
     * pin the ratios without reading pixels. plasmaSpeed is SIGNED: negative
     * is the inward swirl of thinking / working. */
    agent: {
      mode: a.mode, call: a.call, radius: r6(a.r), idleRadius: r6(a.r0),
      brightness: r6(a.bright), halo: r6(a.halo), plasmaSpeed: r6(a.plasma),
      arc: a.arc, rings: shk,
      colour: JVS.toHex(a.col), modeColour: a.modeCol, voice: r6(a.voice), mic: r6(a.mic),
      breath: r6(a.breath), ripples: rip
    },
    brains: brains, links: links, fleet: fleet, fleetBusy: busy,
    senses: { orbit: r6(st.sensesOrbit), count: st.senses.length, unreachable: sdim }
  };
}

/* ============================== PAINT ==================================== */
function jarvisPaintSphere(ctx, sp, cx, cy, r, t) {
  const a = (t / sp.rev) * JVS.TAU * sp.dir + sp.ph;
  const wob = Math.sin(t * 0.17 + sp.ph) * 0.14;
  const ca = Math.cos(a), sa = Math.sin(a), cw = Math.cos(wob), sw = Math.sin(wob);
  const P = sp.pts, n = sp.n, d = 4.0, px = sp.px, py = sp.py, ps = sp.ps, pb = sp.pb, S = JVS.STEPS;
  for (let i = 0; i < n; i++) {
    const x = P[i * 3], y = P[i * 3 + 1], z = P[i * 3 + 2];
    const x1 = x * ca + z * sa, z1 = -x * sa + z * ca;
    const y2 = y * cw - z1 * sw, z2 = y * sw + z1 * cw;
    const pp = d / (d - z2);
    px[i] = cx + x1 * r * pp; py[i] = cy + y2 * r * pp;
    const td = (z2 + 1) * 0.5;
    ps[i] = sp.s0 + (sp.s1 - sp.s0) * td;
    pb[i] = (td * (S - 1)) | 0;
  }
  for (let b = 0; b < S; b++) {
    if (b >= 12) {
      ctx.fillStyle = sp.bloom[b];
      for (let i = 0; i < n; i++) { if (pb[i] !== b) continue; const bz = ps[i] * 3.4; ctx.fillRect(px[i] - bz * 0.5, py[i] - bz * 0.5, bz, bz); }
    }
    ctx.fillStyle = sp.pal[b];
    for (let i = 0; i < n; i++) { if (pb[i] !== b) continue; const sz = ps[i]; ctx.fillRect(px[i] - sz * 0.5, py[i] - sz * 0.5, sz, sz); }
  }
}

/* Everything static about the background — navy, the nebula, the corner
 * washes, the big cobalt glow behind Agent, the vignette. Composed ONCE per
 * size into the backplate canvas when there is a DOM; painted straight onto
 * the frame when there is not (node tests, any DOM-less host). */
function jarvisDrawBackplate(ctx, st) {
  const w = st.w, h = st.h, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK, g = st.geo;
  /* 1. deep glowing navy — color-mix(in srgb, #0B0C0F 78%, #2850E8 22%).
   *    SPEC §3b: never near-black. */
  ctx.fillStyle = JVS.rgba(L.navy, 1);
  ctx.fillRect(0, 0, w, h);
  /* 2. the nebula, screen-blended so only its light survives */
  const rec = st.img ? st.img.bgNebula : null;
  if (rec && rec.ready && rec.img) {
    ctx.save();
    try {
      ctx.globalCompositeOperation = 'screen';
      ctx.globalAlpha = L.nebulaAlpha;
      const iw = rec.img.naturalWidth || rec.img.width || w;
      const ih = rec.img.naturalHeight || rec.img.height || h;
      const k = Math.max(w / iw, h / ih);                 /* cover, never squash */
      ctx.drawImage(rec.img, (w - iw * k) * 0.5, (h - ih * k) * 0.5, iw * k, ih * k);
    } catch (e) { /* a half-decoded image must not kill the plate */ }
    ctx.restore();
  }
  /* 3. corner washes + 4. one large soft cobalt-bright glow behind Agent */
  const cb = JVS.hex(T.cobaltBright), vi = JVS.hex(T.violet);
  let gr = ctx.createRadialGradient(0, 0, 0, 0, 0, Math.max(w, h) * 0.66);
  gr.addColorStop(0, JVS.rgba(cb, L.cornerGlow)); gr.addColorStop(1, JVS.rgba(cb, 0));
  ctx.fillStyle = gr; ctx.fillRect(0, 0, w, h);
  gr = ctx.createRadialGradient(w, h, 0, w, h, Math.max(w, h) * 0.58);
  gr.addColorStop(0, JVS.rgba(vi, 0.12)); gr.addColorStop(1, JVS.rgba(vi, 0));
  ctx.fillStyle = gr; ctx.fillRect(0, 0, w, h);
  const bx = g ? g.cx : w * 0.5, by = g ? g.cy : h * 0.58;
  const br = (g ? g.r0 : Math.min(w, h) * JARVIS_LOOK.agentR) * 3.4;
  gr = ctx.createRadialGradient(bx, by, 0, bx, by, br);
  gr.addColorStop(0, JVS.rgba(cb, L.bgGlow));
  gr.addColorStop(0.42, JVS.rgba(cb, L.bgGlow * 0.42));
  gr.addColorStop(1, JVS.rgba(cb, 0));
  ctx.fillStyle = gr; ctx.fillRect(bx - br, by - br, br * 2, br * 2);
  /* 5. a LIGHT vignette: alpha 0.60, and the inner radius starts wide (24% of the
     short side) so the field around Agent stays lit and only the far edges fall off */
  gr = ctx.createRadialGradient(w * 0.5, h * 0.52, Math.min(w, h) * 0.24, w * 0.5, h * 0.52, Math.max(w, h) * 0.72);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, JVS.rgba([0, 0, 0], L.vignette));
  ctx.fillStyle = gr; ctx.fillRect(0, 0, w, h);
}

function jarvisPaintBackground(ctx, st) {
  const w = st.w, h = st.h, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK;
  const plate = jarvisBackplate(st);
  let blitted = false;
  if (plate) { try { ctx.drawImage(plate, 0, 0, w, h); blitted = true; } catch (e) { blitted = false; } }
  if (!blitted) jarvisDrawBackplate(ctx, st);
  /* grid — painted live, so it stays 1 px crisp on a retina backing store */
  const step = st.geo.small ? 40 : 58;
  ctx.strokeStyle = JVS.rgba(JVS.hex(T.cobaltBright), L.gridAlpha);
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = step * 0.5; x < w; x += step) { ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, h); }
  for (let y = step * 0.5; y < h; y += step) { ctx.moveTo(0, y + 0.5); ctx.lineTo(w, y + 0.5); }
  ctx.stroke();
  /* starfield — constant drift, never voice-reactive */
  const t = st.t, wash = JVS.hex(T.wash);
  for (let i = 0; i < st.stars.length; i++) {
    const s = st.stars[i];
    const tw = 0.30 + 0.45 * (0.5 + 0.5 * Math.sin(t * 0.6 + s.ph));
    ctx.fillStyle = JVS.rgba(wash, tw * L.starAlpha * s.z);
    const sz = 1 + s.z;
    ctx.fillRect(s.x * w, s.y * h, sz, sz);
  }
  /* corner brackets — cobalt-bright, glowing (SPEC §3b). Inset past the
   * overlay's own DOM brackets at 12 px so the two read as a double rule. */
  const bl = Math.min(34, Math.min(w, h) * 0.05), pad = 22;
  ctx.beginPath();
  ctx.moveTo(pad, pad + bl); ctx.lineTo(pad, pad); ctx.lineTo(pad + bl, pad);
  ctx.moveTo(w - pad - bl, pad); ctx.lineTo(w - pad, pad); ctx.lineTo(w - pad, pad + bl);
  ctx.moveTo(pad, h - pad - bl); ctx.lineTo(pad, h - pad); ctx.lineTo(pad + bl, h - pad);
  ctx.moveTo(w - pad - bl, h - pad); ctx.lineTo(w - pad, h - pad); ctx.lineTo(w - pad, h - pad - bl);
  ctx.strokeStyle = JVS.rgba(JVS.hex(T.cobaltBright), 0.22); ctx.lineWidth = 5; ctx.stroke();
  ctx.strokeStyle = JVS.rgba(JVS.lighten(JVS.hex(T.cobaltBright), 0.35), 0.78); ctx.lineWidth = 2; ctx.stroke();
}

function jarvisPaintSenses(ctx, st) {
  if (!st.senses.length) return;
  const g = st.geo, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK, n = st.senses.length;
  const sil = JVS.hex(T.silver), cy = JVS.hex(T.cyan), wash = JVS.hex(T.wash), cb = JVS.hex(T.cobaltBright);
  ctx.save();
  ctx.lineWidth = 1;
  ctx.strokeStyle = JVS.rgba(cb, 0.24);
  ctx.beginPath(); ctx.ellipse(g.senseCx, g.senseCy, g.senseRx, g.senseRy, 0, 0, JVS.TAU); ctx.stroke();
  ctx.font = '9.5px ' + JVS.MONO;
  ctx.textBaseline = 'middle';
  for (let i = 0; i < n; i++) {
    const s = st.senses[i];
    const ang = st.sensesOrbit + (i / n) * JVS.TAU - Math.PI / 2;
    const ux = Math.cos(ang), uy = Math.sin(ang);
    const x = g.senseCx + ux * g.senseRx, y = g.senseCy + uy * g.senseRy;
    /* SPEC §8 amendment B.3 + C11: a rail column and a brain's name label are
     * the two places where the whole reading stands down — mark and name
     * together — so nothing of it can be seen through the gaps between the
     * boxes, or sitting on top of a brain's own name. */
    if (jarvisRailZone(st, x, y, 7) || jarvisBrainLabelZone(st, x, y, 7)) continue;
    /* radial tick, pointing outward from the ellipse centre */
    const nx = ux * g.senseRy, ny = uy * g.senseRx, nl = Math.hypot(nx, ny) || 1;
    const dx = nx / nl, dy = ny / nl;
    const live = s.status !== 'unreachable';
    ctx.strokeStyle = JVS.rgba(live ? cy : sil, live ? 0.85 * s.dim : 0.26);
    ctx.lineWidth = live ? 1.8 : 1;
    ctx.beginPath(); ctx.moveTo(x - dx * 4, y - dy * 4); ctx.lineTo(x + dx * 5, y + dy * 5); ctx.stroke();
    if (live) {                                     /* glowing dot (SPEC §3b) */
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = JVS.rgba(cy, 0.26 * s.dim);
      ctx.beginPath(); ctx.arc(x, y, 5.2, 0, JVS.TAU); ctx.fill();
      ctx.fillStyle = JVS.rgba(JVS.lighten(cy, 0.5), 0.95 * s.dim);
      ctx.beginPath(); ctx.arc(x, y, 1.9, 0, JVS.TAU); ctx.fill();
      ctx.restore();
    } else {
      ctx.fillStyle = JVS.rgba(sil, 0.34);
      ctx.fillRect(x - 1.3, y - 1.3, 2.6, 2.6);
    }
    if (!g.labels) continue;
    /* the label sits INSIDE the ring so it can never clip the viewport edge —
     * unless a brain node owns that spot, in which case it steps outside; if
     * both are taken the dot stays and the name waits for the next sweep. */
    let lx = x - dx * 13, ly = y - dy * 13, side = -1;
    if (jarvisNodeZone(st, lx, ly)) {
      /* outside, then a step along the ring either way; the dot never moves */
      const tx = -dy, ty = dx, got = [0, 0];
      const tries = [[x + dx * 15, y + dy * 15, 1], [lx + tx * 46, ly + ty * 46, -1], [lx - tx * 46, ly - ty * 46, -1]];
      let ok = false;
      for (let k = 0; k < tries.length && !ok; k++) {
        const c = tries[k];
        if (c[0] < 70 || c[0] > st.w - 70 || c[1] < 12 || c[1] > st.h - 12) continue;
        if (jarvisNodeZone(st, c[0], c[1])) continue;
        got[0] = c[0]; got[1] = c[1]; side = c[2]; ok = true;
      }
      if (!ok) continue;                 /* the reading stays; the name waits */
      lx = got[0]; ly = got[1];
    }
    ctx.textAlign = dx * side > 0.25 ? 'left' : (dx * side < -0.25 ? 'right' : 'center');
    ctx.fillStyle = JVS.rgba(live ? wash : sil, live ? L.senseLabel : 0.34);
    ctx.fillText(JVS.fitText(ctx, String(s.label).toUpperCase(), 96), lx, ly);
  }
  ctx.restore();
}

function jarvisPaintLinks(ctx, st) {
  if (!st.links.length) return;
  const g = st.geo, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK, pos = st.vec, n = st.brains.length;
  const cb = JVS.hex(T.cobaltBright), cor = JVS.hex(T.coral);
  const flow = -(st.t * 26) % 1000;                  /* the animated dash flow */
  ctx.save();
  /* faint brain <-> brain chatter across the arc */
  if (n > 1) {
    ctx.strokeStyle = JVS.rgba(cb, 0.26);
    ctx.lineWidth = 1; ctx.setLineDash([3, 6]);
    if ('lineDashOffset' in ctx) ctx.lineDashOffset = flow * 0.4;
    const a = st.vecA, b = st.vecB;
    for (let i = 0; i < n - 1; i++) {
      jarvisBrainPos(st, i, n, a); jarvisBrainPos(st, i + 1, n, b);
      ctx.beginPath(); ctx.moveTo(a[0], a[1]);
      ctx.quadraticCurveTo((a[0] + b[0]) / 2, Math.min(a[1], b[1]) - g.brainR * 0.9, b[0], b[1]);
      ctx.stroke();
    }
    ctx.setLineDash([]);
    if ('lineDashOffset' in ctx) ctx.lineDashOffset = 0;
  }
  for (let i = 0; i < st.links.length; i++) {
    const L2 = st.links[i], br = st.brains[i];
    if (!br) continue;
    jarvisBrainPos(st, i, n, pos);
    const col = JVS.hex(T[br.lane] || T.cyan);
    let vx = pos[0] - g.cx, vy = pos[1] - g.cy;
    const len = Math.hypot(vx, vy) || 1; vx /= len; vy /= len;
    /* REST radius on purpose — link geometry must not inherit voice */
    const x0 = g.cx + vx * (g.r0 * L.agentLink), y0 = g.cy + vy * (g.r0 * L.agentLink);
    const x1 = pos[0] - vx * (g.brainR * L.brainLink), y1 = pos[1] - vy * (g.brainR * L.brainLink);
    /* the rail */
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = JVS.rgba(col, L2.on ? L.linkLine : 0.09);
    if (!L2.on) ctx.setLineDash([2, 7]);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    ctx.setLineDash([]);
    if (!L2.on) continue;
    /* the dash flow riding on top of it */
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.setLineDash([5, 11]);
    if ('lineDashOffset' in ctx) ctx.lineDashOffset = flow;
    ctx.strokeStyle = JVS.rgba(JVS.lighten(col, 0.35), L.linkDash);
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
    ctx.setLineDash([]);
    if ('lineDashOffset' in ctx) ctx.lineDashOffset = 0;
    /* packets: cobalt IN toward Agent, coral OUT to the brain (SPEC §3b) */
    for (let k = 0; k < L2.packets.length; k++) {
      const pk = L2.packets[k];
      if (!pk.on) continue;
      const out = pk.dir > 0;                        /* dir>0 travels Agent -> brain */
      const pc = out ? cor : cb;
      const u = out ? pk.p : 1 - pk.p;
      const px = x0 + (x1 - x0) * u, py = y0 + (y1 - y0) * u;
      const tx = px - (x1 - x0) * 0.045 * pk.dir, ty = py - (y1 - y0) * 0.045 * pk.dir;
      ctx.strokeStyle = JVS.rgba(pc, 0.55); ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(px, py); ctx.stroke();
      ctx.fillStyle = JVS.rgba(pc, 0.20 * L.packetGlow);
      ctx.beginPath(); ctx.arc(px, py, 6.4, 0, JVS.TAU); ctx.fill();
      ctx.fillStyle = JVS.rgba(JVS.lighten(pc, 0.30), 0.45 * L.packetGlow);
      ctx.beginPath(); ctx.arc(px, py, 3.6, 0, JVS.TAU); ctx.fill();
      ctx.fillStyle = JVS.rgba(JVS.lighten(pc, 0.72), L.packetGlow);
      ctx.beginPath(); ctx.arc(px, py, 1.8, 0, JVS.TAU); ctx.fill();
    }
    ctx.restore();
  }
  ctx.restore();
}

function jarvisPaintBrains(ctx, st) {
  if (!st.brains.length) return;
  const g = st.geo, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK, n = st.brains.length, pos = st.vec;
  const R = g.brainR;
  for (let i = 0; i < n; i++) {
    const b = st.brains[i];
    jarvisBrainPos(st, i, n, pos);
    const cx = pos[0], cy = pos[1];
    const col = JVS.hex(T[b.lane] || T.cyan), dim = b.dim;
    /* soft halo — Look v1.1 doubles it. Cached per brain: neither the hue nor
     * the geometry changes between resizes, so this must not allocate a
     * gradient every frame. */
    /* the key carries cx/cy too: a canvas gradient is anchored in absolute
     * coordinates, so a resize or a new brain count must rebuild it. */
    const hk = (cx | 0) + ':' + (cy | 0) + ':' + Math.round(R) + ':' + dim + ':' + b.lane;
    if (b.haloKey !== hk) {
      const g2 = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 2.6);
      g2.addColorStop(0, JVS.rgba(col, L.brainHalo * dim));
      g2.addColorStop(0.35, JVS.rgba(col, L.brainHalo * 0.46 * dim));
      g2.addColorStop(1, JVS.rgba(col, 0));
      b.halo = g2; b.haloKey = hk;
    }
    ctx.fillStyle = b.halo; ctx.fillRect(cx - R * 2.6, cy - R * 2.6, R * 5.2, R * 5.2);
    /* the plasma sphere itself: its own art, turning slowly and shimmering.
     * LAW 2 — this is a display; every number below comes from scene time. */
    const plate = jarvisOrb(st, b.asset, g.brainPlate);
    if (plate) {
      const spin = (st.t / L.brainSpin) * JVS.TAU * b.ringDir + b.ph;
      const shimmer = 0.86 + 0.14 * Math.sin(st.t * 0.75 + b.ph);
      const s = R * 3.3;                       /* the globe fills ~60% of the JPEG */
      ctx.save();
      try {
        ctx.globalCompositeOperation = 'screen';
        ctx.globalAlpha = L.brainImage * dim * shimmer;
        ctx.translate(cx, cy); ctx.rotate(spin);
        ctx.drawImage(plate, -s * 0.5, -s * 0.5, s, s);
      } catch (e) { /* noop */ }
      ctx.restore();
    }
    /* particle core over the plate — keeps the node alive at any size */
    JVS.tintSphere(b.sphere, dim < 0.5 ? JVS.hex(T.silver) : col);
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = plate ? 0.55 * dim : dim;
    jarvisPaintSphere(ctx, b.sphere, cx, cy, R * 0.82, st.t);
    ctx.restore();
    /* segmented ring — its own constant speed */
    const segs = 20, gap = 0.055;
    ctx.lineWidth = 2.4;
    for (let s = 0; s < segs; s++) {
      const a0 = b.ring + (s / segs) * JVS.TAU, a1 = a0 + (JVS.TAU / segs) - gap;
      const hot = (s % 5 === 1);
      ctx.strokeStyle = JVS.rgba(hot ? JVS.lighten(col, 0.5) : col, (hot ? 0.95 : 0.46) * dim);
      ctx.beginPath(); ctx.arc(cx, cy, R * L.brainSeg, a0, a1); ctx.stroke();
    }
    /* glowing dashed ring in the brain's own hue (SPEC §3b) */
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.setLineDash([6, 9]);
    if ('lineDashOffset' in ctx) ctx.lineDashOffset = -b.ring * 26;
    ctx.strokeStyle = JVS.rgba(col, 0.16 * dim); ctx.lineWidth = 5;
    ctx.beginPath(); ctx.arc(cx, cy, R * L.brainRing, 0, JVS.TAU); ctx.stroke();
    ctx.strokeStyle = JVS.rgba(JVS.lighten(col, 0.4), 0.62 * dim); ctx.lineWidth = 1.3;
    ctx.beginPath(); ctx.arc(cx, cy, R * L.brainRing, 0, JVS.TAU); ctx.stroke();
    ctx.setLineDash([]);
    if ('lineDashOffset' in ctx) ctx.lineDashOffset = 0;
    ctx.restore();
    /* inner sweep line, clipped to the node */
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, cy, R * 1.02, 0, JVS.TAU); ctx.clip();
    const sy = cy + (b.scan * 2 - 1) * R;
    const lg = ctx.createLinearGradient(cx - R, sy, cx + R, sy);
    lg.addColorStop(0, JVS.rgba(col, 0)); lg.addColorStop(0.5, JVS.rgba(JVS.lighten(col, 0.55), 0.85 * dim)); lg.addColorStop(1, JVS.rgba(col, 0));
    ctx.strokeStyle = lg; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(cx - R, sy); ctx.lineTo(cx + R, sy); ctx.stroke();
    ctx.restore();
    /* label */
    if (!g.labels) continue;
    ctx.save();
    ctx.font = (g.small ? '9.5px ' : '10.5px ') + JVS.MONO;
    /* label sits ABOVE the node: the link from Agent always arrives from below,
       so a label underneath would be crossed by the line and its packets. */
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0.16em';
    let lab = String(b.label).toUpperCase();
    if (b.status === 'unreachable') lab += ' · UNREACHABLE';
    else if (b.status === 'unknown') lab += ' · UNKNOWN';
    ctx.fillStyle = JVS.rgba(b.status === 'ok' ? JVS.hex(T.wash) : JVS.hex(T.silver), b.status === 'ok' ? 0.92 : 0.55);
    ctx.fillText(JVS.fitText(ctx, lab, st.w * 0.19), cx, cy - R * L.brainLabel - 11);
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
    ctx.restore();
  }
}

function jarvisPaintFleet(ctx, st) {
  if (!st.fleet.length) return;
  const g = st.geo, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK, n = st.fleet.length;
  const cb = JVS.hex(T.cobaltBright), sil = JVS.hex(T.silver), wash = JVS.hex(T.wash), vio = JVS.hex(T.violet);
  const x0 = g.fleetX0, x1 = g.fleetX1;
  let busy = 0;
  ctx.save();
  /* the arc itself */
  ctx.strokeStyle = JVS.rgba(vio, 0.28); ctx.lineWidth = 1.2;
  ctx.beginPath();
  for (let i = 0; i <= 40; i++) {
    const u = i / 40, uu = u * 2 - 1;
    const x = x0 + (x1 - x0) * u, y = g.fleetY - g.fleetRise * uu * uu;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const f = st.fleet[i];
    const u = n === 1 ? 0.5 : i / (n - 1), uu = u * 2 - 1;
    const x = x0 + (x1 - x0) * u, y = g.fleetY - g.fleetRise * uu * uu;
    if (f.busy) {
      busy++;
      const br = 0.62 + 0.38 * (0.5 + 0.5 * Math.sin(st.t * 2.1 + f.ph));
      ctx.fillStyle = JVS.rgba(cb, 0.22 * br);
      ctx.beginPath(); ctx.arc(x, y, 11 + 4 * br, 0, JVS.TAU); ctx.fill();
      ctx.fillStyle = JVS.rgba(JVS.lighten(cb, 0.45), 0.75 + 0.25 * br);
      ctx.beginPath(); ctx.arc(x, y, 3.4 + 1.5 * br, 0, JVS.TAU); ctx.fill();
      ctx.strokeStyle = JVS.rgba(cb, 0.55 * br); ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(x, y, 7 + 3 * br, 0, JVS.TAU); ctx.stroke();
    } else {
      ctx.fillStyle = JVS.rgba(sil, 0.20);
      ctx.beginPath(); ctx.arc(x, y, 5.4, 0, JVS.TAU); ctx.fill();
      ctx.fillStyle = JVS.rgba(JVS.lighten(sil, 0.4), 0.72);
      ctx.beginPath(); ctx.arc(x, y, 2.5, 0, JVS.TAU); ctx.fill();
    }
  }
  ctx.globalCompositeOperation = 'source-over';
  if (g.labels) {
    ctx.font = '9.5px ' + JVS.MONO;
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0.2em';
    ctx.fillStyle = JVS.rgba(wash, L.fleetLabel);
    ctx.fillText('FLEET · ' + busy + ' BUSY / ' + n, (x0 + x1) / 2, g.fleetY + 14);
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  }
  ctx.restore();
}

/* Procedural lightning over Agent's shell (SPEC §3b). Count and intensity
 * follow AGENT's voice only; at rest there are none. Every vertex comes from
 * an integer hash of (epoch, index), so this allocates nothing and stays
 * reproducible — it never touches scene state, so snapshotState() is
 * unchanged and the "only Agent reacts to voice" law still holds. */
function jarvisPaintBolts(ctx, st, cx, cy, r, a, v) {
  if (!(v > 0.10)) return;
  const T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK;
  const cyn = JVS.hex(T.cyan), wash = JVS.hex(T.wash);
  const n = Math.max(1, Math.round(L.boltMax * v));
  /* SPEC §7.1.2: the strike rate rides the plasma clock, so it speeds up at
   * least 2.5x from voice 0 to voice 1 with everything else about him. */
  const ep = Math.floor(a.boltT * 13) | 0;
  const SEG = 9;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const life = JVS.hash(ep, i * 7 + 5);
    if (life < 0.20) continue;                        /* flicker: dark slots */
    const a0 = JVS.hash(ep, i * 7 + 1) * JVS.TAU;
    const spread = 0.5 + 0.8 * JVS.hash(ep, i * 7 + 2);
    const rIn = r * 0.14, rOut = r * (0.92 + 0.22 * JVS.hash(ep, i * 7 + 3));
    ctx.beginPath();
    for (let sg = 0; sg <= SEG; sg++) {
      const u = sg / SEG;
      const jit = (JVS.hash(ep, i * 97 + sg * 13) - 0.5) * spread * (0.22 + u);
      const ang = a0 + jit, rad = rIn + (rOut - rIn) * u;
      const x = cx + Math.cos(ang) * rad, y = cy + Math.sin(ang) * rad;
      if (sg === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    const al = (0.22 + 0.58 * v) * (0.45 + 0.55 * life);
    ctx.strokeStyle = JVS.rgba(cyn, al * 0.28); ctx.lineWidth = 3.6; ctx.stroke();
    ctx.strokeStyle = JVS.rgba(wash, al); ctx.lineWidth = 1.1; ctx.stroke();
  }
  ctx.restore();
}

function jarvisPaintAgent(ctx, st) {
  const g = st.geo, a = st.agent, T = JARVIS_SCENE_TOKENS, L = JARVIS_LOOK;
  const cx = g.cx, cy = g.cy, r = a.r || g.r0, col = a.col;
  const off = a.call !== 'on';
  const vfx = a.voice * a.fx;                 /* voice, but only while SPEAKING */
  const wash = JVS.hex(T.wash), cyn = JVS.hex(T.cyan), cor = JVS.hex(T.coral), cb = JVS.hex(T.cobaltBright);

  /* ---- the halo. SPEC §7.1.2 wants its radius AND its alpha to at least
   * double between voice 0 and voice 1; both are this one eased number times
   * a constant, so the snapshot's `halo` IS the picture. ---- */
  const hR = g.r0 * L.agentHaloR * a.halo, hA = L.agentHaloA * a.halo;
  if (hR > 1 && hA > 0.004) {
    const gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, hR);
    gr.addColorStop(0, JVS.rgba(col, hA));
    gr.addColorStop(0.30, JVS.rgba(col, hA * 0.44));
    gr.addColorStop(1, JVS.rgba(col, 0));
    ctx.fillStyle = gr; ctx.fillRect(cx - hR, cy - hR, hR * 2, hR * 2);
  }

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineWidth = 2;
  /* mic ripples travelling inward (Owner speaking) */
  const rip0 = g.rippleR0 || g.r0 * 1.02;
  const rip1 = g.rippleR1 || g.r0 * 1.40;      /* solved to clear the brain rings */
  for (let i = 0; i < a.ripples.length; i++) {
    const rp = a.ripples[i];
    if (!rp.on) continue;
    const rr = rip0 + (rip1 - rip0) * rp.p;
    ctx.strokeStyle = JVS.rgba(cyn, 0.80 * (1 - rp.p * rp.p));
    ctx.beginPath(); ctx.arc(cx, cy, rr, 0, JVS.TAU); ctx.stroke();
  }
  /* shock rings leaving his rim on a voice peak (SPEC §7.1.2). Reduced motion
   * keeps them as static marks: they fade where they were struck. */
  const shockEnd = g.airspace || g.r0 * 1.45;
  for (let i = 0; i < a.shocks.length; i++) {
    const sh = a.shocks[i];
    if (!sh.on) continue;
    const start = Math.min(sh.r, shockEnd);
    const travel = st.reducedMotion ? 0.25 : Math.pow(sh.p, 0.55);
    const rr = start + (shockEnd - start) * travel;
    const fade = (1 - sh.p) * (1 - sh.p);
    /* a wide soft pass under a crisp one, so the ring reads as a shock front
     * and not as one more chrome circle */
    ctx.strokeStyle = JVS.rgba(cyn, 0.26 * fade); ctx.lineWidth = 9 * fade + 2;
    ctx.beginPath(); ctx.arc(cx, cy, rr, 0, JVS.TAU); ctx.stroke();
    ctx.strokeStyle = JVS.rgba(JVS.lighten(cyn, 0.35), 0.90 * fade);
    ctx.lineWidth = 1 + 3.2 * fade;
    ctx.beginPath(); ctx.arc(cx, cy, rr, 0, JVS.TAU); ctx.stroke();
  }
  ctx.restore();

  /* the plasma plate: the Command Center's own orb, `screen`-composited so its
   * black background disappears. SPEC §7.1 replaced §3b's split swell — the
   * whole ball is the reading now, so the plate rides the solved radius. */
  const plate = jarvisOrb(st, 'orbAgent', g.agentPlate);
  if (plate) {
    const s2 = r * 2.63;                      /* the sphere fills ~76% of the JPEG */
    ctx.save();
    try {
      ctx.globalCompositeOperation = 'screen';
      ctx.globalAlpha = Math.max(0.06, Math.min(1, L.agentImage * a.bright));
      ctx.drawImage(plate, cx - s2 * 0.5, cy - s2 * 0.5, s2, s2);
      if (!off && a.bright > 1.02) {           /* "glows more" while he speaks */
        ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = Math.min(0.55, 0.42 * (a.bright - 1));
        ctx.drawImage(plate, cx - s2 * 0.5, cy - s2 * 0.5, s2, s2);
      }
    } catch (e) { /* noop */ }
    ctx.restore();
    if (!off) {                                /* mode tint, so amber/violet read */
      const tint = L.agentTint * Math.min(1.4, Math.max(0.5, a.bright));
      const tg = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 1.1);
      tg.addColorStop(0, JVS.rgba(JVS.lighten(col, 0.35), tint * 0.5));
      tg.addColorStop(0.62, JVS.rgba(col, tint));
      tg.addColorStop(1, JVS.rgba(col, 0));
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = tg; ctx.fillRect(cx - r * 1.1, cy - r * 1.1, r * 2.2, r * 2.2);
      ctx.restore();
    }
  }
  /* the live particle shell on top — denser, brighter, cobalt-bright -> wash.
   * Its clock is Agent's own SIGNED plasma time, so the whole shell speeds up
   * with his voice and turns INWARD while he thinks (SPEC §7.1.2 / §7.1.3). */
  JVS.tintSphere2(
    a.sphere,
    JVS.shade(JVS.mix(col, cb, 0.45), 0.8),
    JVS.mix(JVS.lighten(col, 0.5), wash, 0.62)
  );
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  /* the shell is drawn at 0.76r because jarvisPaintSphere's perspective
   * (d=4) throws the near points out by up to 1.33x: that lands the shell
   * ON the plate and keeps it there at every size. */
  let shellR = r * (plate ? 0.76 : 1);
  let shellA = plate ? (off ? 0.34 : 0.52 * Math.min(1.7, a.bright))
                     : (off ? 0.50 : Math.min(1, 0.80 * a.bright));
  if (a.plasma < 0) {                          /* thinking / working: it falls IN */
    shellR *= 1 - 0.18 * a.swirl;
    shellA *= 0.45 + 0.55 * Math.sin(Math.PI * a.swirl);
  }
  ctx.globalAlpha = Math.max(0.05, Math.min(1, shellA));
  jarvisPaintSphere(ctx, a.sphere, cx, cy, shellR, a.plasmaT);
  ctx.restore();
  /* lightning filaments — SPEAKING only, none at rest */
  if (!off) jarvisPaintBolts(ctx, st, cx, cy, r, a, vfx);
  /* rim light, top-left */
  const rim = ctx.createLinearGradient(cx - r, cy - r, cx + r * 0.6, cy + r);
  rim.addColorStop(0, JVS.rgba(JVS.lighten(col, 0.7), Math.min(1, (off ? 0.34 : 0.55) * a.bright + 0.26 * vfx)));
  rim.addColorStop(0.55, JVS.rgba(col, 0.20));
  rim.addColorStop(1, JVS.rgba(col, 0));
  ctx.strokeStyle = rim; ctx.lineWidth = 1.8;
  ctx.beginPath(); ctx.arc(cx, cy, r * 1.02, 0, JVS.TAU); ctx.stroke();
  /* SPEC §7.1.3: the one thin arc orbiting him while he thinks or works, so a
   * small dark orb never reads as a dead one. Violet thinking, amber working;
   * nothing else tells the two apart. Reduced motion parks it at the top. */
  if (a.arcOn > 0.012) {
    const ac = JVS.hex(a.arcKind === 'working' ? T.amber : T.violet);
    const ar = r * L.agentArc, sweep = 70 * Math.PI / 180;
    const a0 = st.reducedMotion ? -Math.PI * 0.5 : a.arcPh;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    ctx.strokeStyle = JVS.rgba(ac, 0.30 * a.arcOn); ctx.lineWidth = 8;
    ctx.beginPath(); ctx.arc(cx, cy, ar, a0, a0 + sweep); ctx.stroke();
    /* the hue itself carries the crisp pass: lightened any further, `lighter`
     * blending turns both violet and amber into the same white streak. */
    ctx.strokeStyle = JVS.rgba(JVS.lighten(ac, 0.12), 0.88 * a.arcOn); ctx.lineWidth = 2.4;
    ctx.beginPath(); ctx.arc(cx, cy, ar, a0, a0 + sweep); ctx.stroke();
    ctx.restore();
  }
  /* tick ring + dashed arc — constant rotation, never voice-driven */
  const rot = st.t * 0.10, r0t = g.r0 * L.agentTick0, r1t = g.r0 * L.agentTick1;
  const dimK = off ? 0.55 : 1;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.lineWidth = 1.8;
  for (let i = 0; i < 64; i++) {
    const th = rot + i * (JVS.TAU / 64);
    const hot = (i % 16 === 3);
    const c = hot ? cor : (i % 8 === 0 ? cyn : wash);
    ctx.strokeStyle = JVS.rgba(c, (hot ? 1 : (i % 3 === 0 ? L.tickRing : 0.34)) * dimK);
    const e = hot ? r1t + 5 : r1t;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(th) * r0t, cy + Math.sin(th) * r0t);
    ctx.lineTo(cx + Math.cos(th) * e, cy + Math.sin(th) * e);
    ctx.stroke();
  }
  ctx.setLineDash([9, 12]);
  ctx.strokeStyle = JVS.rgba(cyn, 0.16 * dimK); ctx.lineWidth = 5;
  ctx.beginPath(); ctx.arc(cx, cy, g.ringOut, -rot * 0.7, -rot * 0.7 + JVS.TAU); ctx.stroke();
  ctx.strokeStyle = JVS.rgba(cyn, 0.85 * dimK); ctx.lineWidth = 1.3;
  ctx.beginPath(); ctx.arc(cx, cy, g.ringOut, -rot * 0.7, -rot * 0.7 + JVS.TAU); ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
  /* name + mode readout — back under Agent's own ring (SPEC §4.6 amendment) */
  if (!g.labels || !g.textLines) return;
  ctx.save();
  ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  const base = g.textY;
  ctx.font = '11px ' + JVS.MONO;
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0.34em';
  ctx.fillStyle = JVS.rgba(wash, 0.95);
  ctx.fillText(String((st.labels && st.labels.agent) || 'Agent').toUpperCase(), cx, base);
  /* the mode word is bigger and glows in its own colour (SPEC §3b) */
  if (g.textLines < 2) { if ('letterSpacing' in ctx) ctx.letterSpacing = '0px'; ctx.restore(); return; }
  ctx.font = (g.small ? '11px ' : '13px ') + JVS.MONO;
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0.26em';
  const word = off ? 'OFF CALL' : String(a.mode).toUpperCase();
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = JVS.rgba(col, off ? 0.22 : 0.45);
  ctx.fillText(word, cx, base + 14);
  ctx.restore();
  ctx.fillStyle = JVS.rgba(JVS.lighten(col, off ? 0.2 : 0.45), off ? 0.7 : 1);
  ctx.fillText(word, cx, base + 14);
  if (a.live && g.textLines >= 3) {
    ctx.font = '9.5px ' + JVS.MONO;
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0.1em';
    ctx.fillStyle = JVS.rgba(JVS.hex(T.silver), 0.78);
    ctx.fillText(JVS.fitText(ctx, String(a.live), st.w * 0.34), cx, base + 30);
  }
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  ctx.restore();
}

function jarvisPaintWaiting(ctx, st) {
  const g = st.geo, T = JARVIS_SCENE_TOKENS;
  ctx.save();
  ctx.setLineDash([4, 10]); ctx.lineWidth = 1.2;
  ctx.strokeStyle = JVS.rgba(JVS.hex(T.cobaltBright), 0.55);
  ctx.beginPath(); ctx.arc(g.cx, g.cy, g.r0 * (JARVIS_LOOK.agentRing + 0.30), 0, JVS.TAU); ctx.stroke();
  ctx.setLineDash([]);
  if (g.labels) {
    ctx.font = '10px ' + JVS.MONO;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0.28em';
    ctx.fillStyle = JVS.rgba(JVS.hex(T.wash), 0.8);
    ctx.fillText('WAITING FOR DATA', g.cx, g.cy - g.r0 * (JARVIS_LOOK.agentRing + 0.30) - 12);
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  }
  ctx.restore();
}

function jarvisPaintScene(ctx, st) {
  jarvisImagesInit(st);
  jarvisPaintBackground(ctx, st);
  jarvisPaintSenses(ctx, st);
  jarvisPaintLinks(ctx, st);
  jarvisPaintBrains(ctx, st);
  jarvisPaintFleet(ctx, st);
  jarvisPaintAgent(ctx, st);
  if (st.waiting) jarvisPaintWaiting(ctx, st);
}

/* ============================= createScene =============================== */
function createScene(canvas, opts) {
  opts = opts || {};
  let ctx = null;
  try { if (canvas && typeof canvas.getContext === 'function') ctx = canvas.getContext('2d'); } catch (e) { ctx = null; }

  let dpr = opts.dpr;
  if (!dpr) { try { dpr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1; } catch (e) { dpr = 1; } }
  dpr = Math.max(1, Math.min(2, dpr || 1));

  let reduced = opts.reducedMotion;
  if (reduced === undefined) {
    reduced = false;
    try { if (typeof matchMedia === 'function') reduced = !!matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { reduced = false; }
  }

  const st = jarvisInitState({
    w: opts.width || (canvas && canvas.clientWidth) || 1200,
    h: opts.height || (canvas && canvas.clientHeight) || 760,
    dpr: dpr, reducedMotion: !!reduced, seed: opts.seed
  });

  let presence = null, raf = 0, keepAlive = 0, running = false, lastMs = -1, lastPaint = -1e9;
  const FRAME = 1000 / 30;                                  /* 30 fps cap */
  const warmup = opts.warmupMs === undefined ? 2600 : (+opts.warmupMs || 0);
  let warmed = warmup <= 0;

  const nowMs = function () { try { return (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now(); } catch (e) { return Date.now(); } };
  const hidden = function () { try { return typeof document !== 'undefined' && !!document.hidden; } catch (e) { return false; } };

  function applySize() {
    jarvisGeometry(st);
    st.agent.r0 = st.geo.r0;
    if (!st.agent.r) st.agent.r = st.geo.r0;
    /* particle budget follows the stage size — Look v1.1 runs a DENSER shell */
    const want = st.geo.small ? 560 : (Math.min(st.w, st.h) > 820 ? 1500 : 1100);
    if (st.agent.sphere.n !== want) st.agent.sphere = JVS.mkSphere(want, 26, 1, 0, 0.7, 2.6);
    jarvisImagesInit(st);
    if (!canvas) return;
    try {
      canvas.width = Math.max(1, Math.round(st.w * st.dpr));
      canvas.height = Math.max(1, Math.round(st.h * st.dpr));
      if (canvas.style) { canvas.style.width = st.w + 'px'; canvas.style.height = st.h + 'px'; }
    } catch (e) { /* fake canvas in tests */ }
  }

  function render() {
    if (!ctx) return;
    try {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, st.w * st.dpr, st.h * st.dpr);
      ctx.setTransform(st.dpr, 0, 0, st.dpr, 0, 0);
      jarvisPaintScene(ctx, st);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    } catch (e) { /* never let one bad frame kill the loop */ }
  }

  function tick(ms) {
    if (!running) return;
    if (hidden()) { lastMs = ms; return; }                  /* pause, no drift */
    if (!warmed) {
      warmed = true;
      let left = warmup;
      while (left > 0) { jarvisSceneStep(st, Math.min(33, left), presence); left -= 33; }
    }
    if (lastMs < 0) lastMs = ms - FRAME;
    if (ms - lastPaint < FRAME - 1.2) return;               /* 30 fps cap */
    const dt = ms - lastMs;
    lastMs = ms; lastPaint = ms;
    jarvisSceneStep(st, dt, presence);
    render();
  }

  function loop() {
    raf = 0;
    if (!running) return;
    tick(nowMs());
    try { if (typeof requestAnimationFrame === 'function') raf = requestAnimationFrame(loop); } catch (e) { raf = 0; }
  }

  const api = {
    setPresence: function (p) { presence = p || null; return api; },
    setData: function (d) { jarvisApplyData(st, d); return api; },
    setSize: function (w, h) {
      st.w = Math.max(1, Math.round(+w || st.w));
      st.h = Math.max(1, Math.round(+h || st.h));
      applySize();
      if (running) render();
      return api;
    },
    start: function () {
      if (running) return api;
      running = true; lastMs = -1; lastPaint = -1e9;
      try { if (typeof requestAnimationFrame === 'function') raf = requestAnimationFrame(loop); } catch (e) { raf = 0; }
      /* rAF can be starved (headless capture, throttled window) — keep painting */
      try {
        if (typeof setInterval === 'function') {
          keepAlive = setInterval(function () { if (running && nowMs() - lastPaint > 240) { tick(nowMs()); } }, 160);
        }
      } catch (e) { keepAlive = 0; }
      return api;
    },
    stop: function () {
      running = false;
      try { if (raf && typeof cancelAnimationFrame === 'function') cancelAnimationFrame(raf); } catch (e) { /* noop */ }
      try { if (keepAlive && typeof clearInterval === 'function') clearInterval(keepAlive); } catch (e) { /* noop */ }
      raf = 0; keepAlive = 0;
      return api;
    },
    destroy: function () {
      api.stop();
      jarvisReleaseImages(st);          /* Look v1.1: let the plates go */
      st.cache = {};
      presence = null; ctx = null;
      return api;
    },
    snapshotState: function () { return jarvisSceneSnapshot(st); },
    /* escape hatches for the overlay/mirror; not part of the §4.3 contract */
    render: function () { render(); return api; },
    state: st
  };

  applySize();
  return api;
}
