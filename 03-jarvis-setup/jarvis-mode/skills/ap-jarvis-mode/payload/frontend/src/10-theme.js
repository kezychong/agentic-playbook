// hermes-jarvis — file 10: THE LOOK (SPEC §3 + §3b "Look v1.1").
//
// PURE by contract: no HermesSDK, no React, no `document` touched at load time.
// This file is concatenated into BOTH the desktop plugin and the standalone
// mirror page, so it must evaluate anywhere a plain JS engine runs.
//
// Exposes exactly four module-level bindings:
//   JARVIS_TOKENS      — the BRAIN 2 dark-HUD palette, read by 40-scene.js (canvas
//                        colours) and mirrored into CSS custom properties below.
//                        Names are ADDITIVE ONLY: the scene binds this object.
//   JARVIS_MODE_COLORS — mode → Agent's colour.
//   JARVIS_POD_HUES    — pod id → its hue bar colour (SPEC §3b).
//   JARVIS_CSS         — every style the vanilla-DOM overlay and the statusbar
//                        chip need, all class names prefixed `.jv-`.
//                        MUST stay the last binding in this file: scripts/build.py
//                        lifts it for the mirror with a `$`-anchored regex.
//
// Look v1.1 (Owner, 2026-09-18 14:20 — "the JARVIS color is so off from the
// command center. I want the similar color and design. It has to pop"): the
// chrome moved from near-black to the Brain Command Center's deep glowing navy,
// borders went cobalt-bright, and every glow alpha roughly doubled. `glow` keeps
// its v1.0 value on purpose — 40-scene.js binds this same object and doubles its
// own alphas independently; the chrome reaches for `glowStrong` / `panelGlow`.
const JARVIS_TOKENS = {
  bg: '#07080C',
  ink: '#0B0C0F',
  cobalt: '#2850E8',
  cobaltBright: '#3A62FF',
  wash: '#E5EBFF',
  coral: '#E85D4F',
  coralDeep: '#D14A3D',
  silver: '#8A93A6',
  bodyDark: '#C8CDD8',
  line: '#1F2229',
  cyan: '#35E0FF',
  violet: '#8B6CFF',
  magenta: '#FF4FD8',
  teal: '#2DD4BF',
  amber: '#FFB454',
  glow: 'rgba(58,98,255,.55)',
  // ---- Look v1.1 additions (never rename, never remove) ----
  // `navy` is the hex answer to color-mix(in srgb, #0B0C0F 78%, #2850E8 22%)
  // = rgb(17,27,63). It is the overlay's floor: deep, lit, never near-black.
  navy: '#111B3F',
  navyDeep: '#080C22',
  silverBright: '#A9B3C8',
  lineBright: 'rgba(58,98,255,.62)',
  panelGlow: 'rgba(58,98,255,.34)',
  glowStrong: 'rgba(58,98,255,.95)',
  glowWide: 'rgba(58,98,255,.42)',
  // `cobaltText` is cobaltBright lifted for TEXT only: #3A62FF measures ~3.2-3.9:1
  // at 8.5-9.5px on the navy floor and the pod fill. This tint clears 4.5:1 on both.
  // Glows, dots, bars and borders keep `cobaltBright` — only small type moves.
  cobaltText: '#7C97FF',
  washDim: 'rgba(229,235,255,.60)',
  coralGlow: 'rgba(232,93,79,.55)'
}

// Mode → Agent colour (SPEC §3). Kept beside the tokens so the scene, the HUD
// word and the statusbar dot can never drift apart.
const JARVIS_MODE_COLORS = {
  idle: JARVIS_TOKENS.silver,
  listening: JARVIS_TOKENS.cyan,
  thinking: JARVIS_TOKENS.violet,
  speaking: JARVIS_TOKENS.cobaltBright,
  working: JARVIS_TOKENS.amber,
  muted: JARVIS_TOKENS.coral,
  sleeping: JARVIS_TOKENS.coral
}

// Per-pod hue (SPEC §3b: "per-pod hue bars like the reference's SYSTEM VITALS").
// The hue is decoration that names the pod — never a gauge, never a reading.
// BRAINS is three dots instead of a bar, one per brain, in brain order.
const JARVIS_POD_HUES = {
  connection: JARVIS_TOKENS.cobaltBright,
  voice: JARVIS_TOKENS.cyan,
  lever: JARVIS_TOKENS.amber,
  jobs: JARVIS_TOKENS.coral,
  fleet: JARVIS_TOKENS.violet,
  scan: JARVIS_TOKENS.cobaltBright,
  telemetry: JARVIS_TOKENS.teal,
  brains: [JARVIS_TOKENS.magenta, JARVIS_TOKENS.cyan, JARVIS_TOKENS.teal]
}

const JARVIS_CSS = `
.jv-overlay, .jv-chip {
  --jv-bg:${JARVIS_TOKENS.bg};
  --jv-ink:${JARVIS_TOKENS.ink};
  --jv-navy:${JARVIS_TOKENS.navy};
  --jv-navy-deep:${JARVIS_TOKENS.navyDeep};
  --jv-cobalt:${JARVIS_TOKENS.cobalt};
  --jv-cobalt-bright:${JARVIS_TOKENS.cobaltBright};
  --jv-cobalt-text:${JARVIS_TOKENS.cobaltText};
  --jv-wash:${JARVIS_TOKENS.wash};
  --jv-wash-dim:${JARVIS_TOKENS.washDim};
  --jv-coral:${JARVIS_TOKENS.coral};
  --jv-coral-deep:${JARVIS_TOKENS.coralDeep};
  --jv-coral-glow:${JARVIS_TOKENS.coralGlow};
  --jv-silver:${JARVIS_TOKENS.silver};
  --jv-silver-bright:${JARVIS_TOKENS.silverBright};
  --jv-body:${JARVIS_TOKENS.bodyDark};
  --jv-line:${JARVIS_TOKENS.line};
  --jv-line-bright:${JARVIS_TOKENS.lineBright};
  --jv-cyan:${JARVIS_TOKENS.cyan};
  --jv-violet:${JARVIS_TOKENS.violet};
  --jv-magenta:${JARVIS_TOKENS.magenta};
  --jv-teal:${JARVIS_TOKENS.teal};
  --jv-amber:${JARVIS_TOKENS.amber};
  --jv-glow:${JARVIS_TOKENS.glow};
  --jv-glow-strong:${JARVIS_TOKENS.glowStrong};
  --jv-glow-wide:${JARVIS_TOKENS.glowWide};
  --jv-panel-glow:${JARVIS_TOKENS.panelGlow};
  --jv-mono:'JetBrains Mono', ui-monospace, Menlo, monospace;
  --jv-sans:'DM Sans', system-ui, -apple-system, sans-serif;
  --jv-serif:'Instrument Serif', Georgia, 'Times New Roman', serif;
  /* SPEC §8 amendments C10 — how much bigger the two RAILS are on this
     display. One number, set on the overlay root by measure() in
     50-overlay.js (1 · 1.25 from 2200 px of viewport width · 1.4 from 3000),
     read by every rail width and every rail type size below. 1 is the value
     a shell that never calls measure() — the mirror page — gets. */
  --jv-rail-k:1;
  --jv-pod:rgba(255,255,255,.04);
  --jv-pod-fill :linear-gradient(180deg, rgba(58,98,255,.17) 0%, rgba(12,18,48,.62) 100%);
}

/* The floor of the whole look: ink 78% / cobalt 22%. The hex above is the
   fallback for engines without color-mix; this line is the real thing. */
@supports (background:color-mix(in srgb, #000 50%, #fff)) {
  .jv-overlay { --jv-navy:color-mix(in srgb, #0B0C0F 78%, #2850E8 22%); }
}

/* ---------- shell ---------- */
.jv-overlay {
  position:fixed; inset:0; z-index:2147483000;
  background:
    radial-gradient(64% 52% at 50% 60%, rgba(58,98,255,.26) 0%, rgba(58,98,255,.09) 46%, rgba(58,98,255,0) 72%),
    radial-gradient(128% 106% at 50% 46%, rgba(8,12,34,0) 34%, rgba(8,12,34,.55) 100%),
    var(--jv-navy);
  color:var(--jv-body); font-family:var(--jv-sans); font-size:12px; line-height:1.4;
  overflow:hidden; user-select:none; cursor:default;
  animation:jv-fade .18s ease both;
}
.jv-overlay:focus { outline:none; }
@keyframes jv-fade { from { opacity:0 } to { opacity:1 } }
/* the scene paints its own nebula — it sits ABOVE the navy floor, below the pods */
.jv-canvas { position:absolute; inset:0; width:100%; height:100%; display:block; z-index:1; }

/* corner brackets — cobalt-bright 2px with glow */
.jv-bracket {
  position:absolute; width:30px; height:30px; border:2px solid var(--jv-cobalt-bright);
  opacity:.95; pointer-events:none; z-index:3;
  box-shadow:0 0 14px var(--jv-glow-wide);
}
.jv-bracket.tl { top:12px; left:12px; border-right:0; border-bottom:0; }
.jv-bracket.tr { top:12px; right:12px; border-left:0; border-bottom:0; }
/* the bottom pair clears the ticker rail */
.jv-bracket.bl { bottom:34px; left:12px; border-right:0; border-top:0; }
.jv-bracket.br { bottom:34px; right:12px; border-left:0; border-top:0; }

.jv-layer { position:absolute; pointer-events:none; z-index:4; }
.jv-top-left  { top:26px; left:30px; display:flex; flex-direction:column; align-items:flex-start; gap:10px; width:auto;
  max-width:min(42vw, calc(430px * var(--jv-rail-k, 1))); }
/* the rail pods (TELEMETRY, then VOICE CONTROL) keep one width so a long chip
   row cannot stretch them across the scene's brain labels. 300 + 2x11 padding +
   2x1 border = 324 px of glass; with left:30px the rail is 354 px wide, which is
   the number jarvisGeometry() keeps the brain rings clear of. */
.jv-top-left .jv-pod { width:calc(300px * var(--jv-rail-k, 1)); }
/* ONE right column (fix 2026-09-19). CONNECTION and SCAN used to be a top-
   anchored stack and VOICE/LEVER/JOBS/BRAINS/FLEET a bottom-anchored one;
   in a short window the bottom stack grew up THROUGH the top one and Owner
   read the VOICE pod over ghosted CONNECTION text. Now it is a single flex
   column pinned top AND bottom, so the only thing a short window can do is
   shrink a pod — never move one on top of another. */
.jv-right {
  top:26px; bottom:56px; right:30px; width:calc(300px * var(--jv-rail-k, 1));
  display:flex; flex-direction:column; align-items:stretch; gap:4px;
  min-height:0; overflow:hidden;
}
/* §7 amendment 5 — the rail's boxes do NOT shrink. A shrunk box clips a row
   through the middle (at 1440x813 AGENT IN FLIGHT was crushed to 14 px: header
   gone, row gone, nothing said). Their height is decided in whole ROWS by
   jarvisRailCaps() in 50-overlay.js, which reads this window's height; what
   will not fit is counted out loud as "+n more". NOW is the one exception: it
   may give up its "recent" list (and only that) before anything else does. */
.jv-right > * { flex:0 0 auto; min-height:0; }
/* SCAN is the sacrifice: a shrink weight far above its siblings' means it eats
   almost all of the squeeze first. Its radar sits LAST inside the pod (see
   50-overlay.js) precisely so the clipping starts with the dial — chrome —
   and the header and the session reading above it survive. */
/* min-height:auto (not 0) is the honest floor: SCAN may lose its radar — that
   is chrome — but never the words under it. Only once the radar is gone does
   the squeeze move on to the other pods. */
/* min-height:0 on purpose. A floor here only moves the squeeze onto the pods
   below, and at 1280x720 that cost the VOICE message its last line — a reading
   Owner needs. SCAN gives way to nothing rather than take that. */
.jv-right .jv-scan { display:flex; flex-direction:column; flex-shrink:200; min-height:0; overflow:hidden; }
.jv-right .jv-scan > * { flex:0 0 auto; }
.jv-right .jv-scan .jv-radar { flex:0 1 auto; min-height:0; overflow:hidden; }
/* eight stacked pods in ~718 px (Owner's 1312x800 window) is genuinely tight,
   so the right column shaves its own chrome — padding and rules, never the
   readings — before SCAN is asked to give anything up. */
.jv-right .jv-pod { padding-top:6px; padding-bottom:6px; }
.jv-right .jv-pod-h { padding-bottom:3px; margin-bottom:3px; }
.jv-right .jv-pod-bar { display:none; }
/* the clock steps in from the corner bracket, and shares its row with the two
   window buttons — six boxes in 818 px means chrome pays its way.
   The step-in is the CLOCK's, not the row's: with it on the row, the three
   chrome buttons (284 px) no longer fitted the 300 px rail and WINDOW was
   clipped to "NDOW". wrap-reverse puts the buttons on the lower line, well
   clear of the corner bracket, so only the clock needs the margin. */
.jv-top-row { display:flex; align-items:center; justify-content:flex-end; flex-wrap:wrap-reverse;
  gap:5px 8px; flex-shrink:0; }
.jv-top-row .jv-clock { margin-right:22px; }
.jv-top-row .jv-chrome { flex-shrink:1; min-width:0; }
.jv-head { display:block; }
/* the captions column stops ABOVE the centred line under the orb (§7.3 ruling
   6) instead of sharing its band, so the two never print over each other */
.jv-bot-left  { bottom:74px; left:30px; max-width:min(42vw, 500px); }
/* long readings are clamped, not allowed to push the column past the ticker */
.jv-clamp2, .jv-clamp3 { display:-webkit-box; -webkit-box-orient:vertical; overflow:hidden; }
.jv-clamp2 { -webkit-line-clamp:2; line-clamp:2; }
.jv-clamp3 { -webkit-line-clamp:3; line-clamp:3; }

/* ---------- type ---------- */
.jv-title { font-size:12px; letter-spacing:.34em; text-transform:uppercase; color:var(--jv-wash); white-space:nowrap; text-shadow:0 0 18px var(--jv-glow-wide); }
.jv-sub { margin-top:4px; font-family:var(--jv-mono); font-size:9px; letter-spacing:.18em; color:var(--jv-silver-bright); text-transform:uppercase; }
.jv-clock { font-family:var(--jv-mono); font-size:12px; letter-spacing:.1em; color:var(--jv-wash); white-space:nowrap; font-variant-numeric:tabular-nums; text-shadow:0 0 14px var(--jv-glow-wide); }
.jv-eyebrow { font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.2em; text-transform:uppercase; color:var(--jv-silver-bright); }

/* ---------- status chips (top-left, real readings only) ---------- */
/* The four chips ride on ONE line and must end left of the first brain's ring.
   Measured at 1440x900: the ring is a circle at (446,141) r 62 and the chip row
   sits at y 69-92, so a row ending past ~392 px clips it. 8 px of side padding
   and a 5 px gap end it at 392. */
.jv-chips { display:flex; flex-wrap:nowrap; gap:5px; max-width:calc(362px * var(--jv-rail-k, 1)); }
.jv-chipx {
  display:inline-flex; align-items:center; gap:5px; padding:3.5px 8px; border-radius:999px;
  border:1px solid var(--jv-line-bright); background:rgba(40,80,232,.16);
  font-family:var(--jv-mono); font-size:9.5px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--jv-wash); box-shadow:0 0 14px rgba(58,98,255,.24); white-space:nowrap;
}
.jv-chipx i { flex:0 0 auto; width:5px; height:5px; border-radius:50%; background:var(--jv-cobalt-bright); box-shadow:0 0 9px var(--jv-cobalt-bright); }
.jv-chipx.jv-alarm { border-color:rgba(232,93,79,.6); background:rgba(232,93,79,.15); color:#FFDED8; box-shadow:0 0 14px var(--jv-coral-glow); }
.jv-chipx.jv-alarm i { background:var(--jv-coral); box-shadow:0 0 9px var(--jv-coral); }
.jv-chipx.jv-off { opacity:.6; }

/* ---------- pods ---------- */
.jv-pod {
  position:relative; background:var(--jv-pod-fill);
  border:1px solid var(--jv-line-bright); border-radius:12px;
  padding:9px 11px; overflow:hidden; backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  box-shadow:0 0 20px var(--jv-panel-glow), inset 0 1px 0 rgba(255,255,255,.07);
}
.jv-pod::before {
  content:""; position:absolute; left:0; right:0; top:0; height:2px;
  background:linear-gradient(90deg, transparent, var(--jv-ac, ${JARVIS_TOKENS.cobaltBright}), transparent);
  opacity:1; box-shadow:0 0 12px var(--jv-ac, ${JARVIS_TOKENS.cobaltBright});
}
.jv-pod-h { display:flex; align-items:center; gap:6px; padding-bottom:5px; margin-bottom:6px; border-bottom:1px solid rgba(58,98,255,.28); }
.jv-pod-h b { flex:0 0 auto; width:5px; height:5px; border-radius:50%; background:var(--jv-ac, ${JARVIS_TOKENS.cobaltBright}); box-shadow:0 0 10px var(--jv-ac, ${JARVIS_TOKENS.cobaltBright}); }
.jv-pod-h span { font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.2em; text-transform:uppercase; color:var(--jv-wash); white-space:nowrap; }
/* hue bar: names the pod, measures nothing (honesty rule) */
.jv-pod-bar { height:2.5px; border-radius:2px; margin:0 0 7px;
  background:linear-gradient(90deg, var(--jv-ac, ${JARVIS_TOKENS.cobaltBright}) 0%, rgba(58,98,255,.06) 100%);
  box-shadow:0 0 10px var(--jv-ac, ${JARVIS_TOKENS.cobaltBright}); }
.jv-pod-dots { display:flex; align-items:center; gap:6px; margin:0 0 7px; height:2.5px; }
.jv-pod-dots i { width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 10px currentColor; }
.jv-pod-v { font-family:var(--jv-mono); font-size:12px; color:var(--jv-wash); font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
.jv-pod-n { margin-top:3px; font-size:9.5px; color:var(--jv-silver-bright); overflow-wrap:anywhere; white-space:pre-line; }
/* dim, not illegible: the element opacity fades text AND fill onto the navy floor,
   so .62 dropped the unreachable value to ~3.5-4.0:1. .78 keeps it visibly dim
   while the value text measures >=4.6:1 anywhere on the pod fill. */
.jv-pod.jv-dead { opacity:.78; box-shadow:none; }
.jv-pod.jv-dead .jv-pod-v { color:var(--jv-silver-bright); }
.jv-chip-pod { display:flex; align-items:center; gap:7px; padding:7px 12px; border-radius:999px; }
.jv-chip-pod .jv-pod-n { margin-top:0; }

.jv-row { display:flex; align-items:center; gap:6px; margin-top:3px; font-size:10px; color:var(--jv-body); }
.jv-row:first-of-type { margin-top:0; }
.jv-row i { flex:0 0 auto; width:5px; height:5px; border-radius:50%; background:var(--jv-silver); }
.jv-row i.ok { background:var(--jv-teal); box-shadow:0 0 10px rgba(45,212,191,.9); }
.jv-row i.bad { background:var(--jv-coral); box-shadow:0 0 10px var(--jv-coral-glow); }
.jv-row i.idle { background:var(--jv-silver-bright); }
.jv-row em { font-style:normal; margin-left:auto; font-family:var(--jv-mono); font-size:9px; color:var(--jv-silver-bright); letter-spacing:.06em; }
.jv-row b { font-weight:400; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* ---------- mini radar (blips = live sessions, capped at 6) ---------- */
.jv-radar { position:relative; height:88px; margin:2px 0 4px; }
.jv-radar-dial {
  position:absolute; left:50%; top:0; transform:translateX(-50%);
  width:88px; height:88px; border-radius:50%; overflow:hidden;
  border:1px solid rgba(58,98,255,.5);
  background:
    radial-gradient(circle at 50% 50%, rgba(58,98,255,.16) 0 1px, rgba(58,98,255,0) 1px),
    repeating-radial-gradient(circle at 50% 50%, rgba(58,98,255,.22) 0 1px, rgba(58,98,255,0) 1px 16px),
    radial-gradient(circle at 50% 50%, rgba(58,98,255,.16) 0%, rgba(10,16,44,.5) 100%);
  box-shadow:0 0 18px rgba(58,98,255,.28), inset 0 0 18px rgba(58,98,255,.16);
}
.jv-radar-dial::before, .jv-radar-dial::after {
  content:""; position:absolute; left:50%; top:50%; background:rgba(58,98,255,.28);
}
.jv-radar-dial::before { width:100%; height:1px; transform:translate(-50%,-50%); }
.jv-radar-dial::after { width:1px; height:100%; transform:translate(-50%,-50%); }
.jv-radar-sweep {
  position:absolute; inset:0; border-radius:50%;
  background:conic-gradient(from 0deg, rgba(58,98,255,.55) 0deg, rgba(53,224,255,.18) 26deg, rgba(58,98,255,0) 62deg, rgba(58,98,255,0) 360deg);
  animation:jv-spin 4.2s linear infinite;
}
@keyframes jv-spin { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }
.jv-blip { position:absolute; width:5px; height:5px; border-radius:50%; background:var(--jv-cyan);
  box-shadow:0 0 10px var(--jv-cyan); transform:translate(-50%,-50%); }

/* ---------- ambient telemetry (a timer, never the voice) ---------- */
.jv-tele { display:flex; align-items:flex-end; gap:2px; height:34px; margin:1px 0 3px; }
.jv-tbar { flex:1 1 0; min-width:2px; height:30%; border-radius:1px;
  background:linear-gradient(180deg, currentColor 0%, rgba(58,98,255,.18) 100%);
  box-shadow:0 0 7px currentColor; transition:height .34s ease; }

/* ---------- Agent's word + live line + captions ---------- */
.jv-mode { font-family:var(--jv-serif); font-style:italic; font-size:56px; line-height:1;
  color:var(--jv-wash); text-shadow:0 0 30px var(--jv-mode-c, ${JARVIS_TOKENS.cobaltBright}), 0 0 70px var(--jv-mode-c, ${JARVIS_TOKENS.cobaltBright}); }
/* the live line under Agent's word. Scoped :not(.jv-vbtn) on purpose: the hot
   voice button wears .jv-live too (§4.6), and this rule's margin-top/min-height
   used to push it ~7 px below its siblings in the VOICE pod row. */
.jv-live:not(.jv-vbtn) { margin-top:7px; font-family:var(--jv-mono); font-size:10px; letter-spacing:.1em; color:var(--jv-silver-bright); min-height:13px; }
.jv-captions { margin-top:12px; display:grid; gap:4px; }
.jv-cap { font-size:12px; color:var(--jv-silver-bright); opacity:.8; overflow-wrap:anywhere; }
.jv-cap.jv-new { color:var(--jv-wash); opacity:1; }
.jv-cap span { font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--jv-cobalt-text); margin-right:7px; }

/* ---------- Agent-summoned panel ---------- */
.jv-panel {
  position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); z-index:6;
  width:min(520px, 62vw); max-height:52vh; overflow:auto; padding:16px 18px;
  background:linear-gradient(180deg, rgba(23,34,74,.94), rgba(10,14,36,.96));
  border:1px solid var(--jv-line-bright); border-radius:12px;
  box-shadow:0 24px 70px rgba(0,0,0,.6), 0 0 34px var(--jv-panel-glow); pointer-events:auto;
}
.jv-panel h2 { margin:0 0 8px; font-size:15px; letter-spacing:.04em; color:var(--jv-wash); font-weight:500; }
.jv-panel p { margin:0; font-size:12.5px; line-height:1.55; color:var(--jv-body); white-space:pre-wrap; overflow-wrap:anywhere; }

/* ---------- event ticker ---------- */
.jv-ticker {
  position:absolute; left:0; right:0; bottom:0; height:26px; display:flex; align-items:center; z-index:5;
  border-top:1px solid rgba(58,98,255,.42); background:rgba(9,13,36,.8); overflow:hidden;
  box-shadow:0 -6px 22px rgba(58,98,255,.16);
  -webkit-mask-image:linear-gradient(90deg, transparent 0, #000 60px, #000 calc(100% - 60px), transparent 100%);
  mask-image:linear-gradient(90deg, transparent 0, #000 60px, #000 calc(100% - 60px), transparent 100%);
}
.jv-ticker-track { display:flex; white-space:nowrap; will-change:transform; animation:jv-scroll 64s linear infinite; }
.jv-ticker-track > span { font-family:var(--jv-mono); font-size:9.5px; letter-spacing:.09em; color:var(--jv-silver-bright); padding:0 18px; }
.jv-ticker-track > span b { font-weight:400; color:var(--jv-cobalt-text); text-shadow:0 0 10px var(--jv-glow-wide); }
@keyframes jv-scroll { from { transform:translateX(0) } to { transform:translateX(-50%) } }

/* ---------- badges ----------
   SPEC §7 amendment 3: the DEMO badge is NOT centred at the top any more. The
   middle brain is drawn there (≈ y 12–160 at 1440×900 and the same band at
   2560×1440), so the badge sat on its face. It rides at the foot of the left
   column instead — a flex row of .jv-top-left, under VOICE CONTROL — inside
   the strip the scene already keeps its own labels out of (40-scene.js
   keepOut [0, 0, 366, 306]). Being a column child, not an absolute box, it
   cannot drift onto anything when a pod above it grows. */
.jv-demo {
  align-self:flex-start; margin-top:-2px;
  font-family:var(--jv-mono); font-size:9px; letter-spacing:.3em; color:${JARVIS_TOKENS.ink};
  background:var(--jv-amber); border-radius:999px; padding:4px 12px; box-shadow:0 0 18px rgba(255,180,84,.5);
}
/* the hint steps out of the centre: the band under Agent belongs to the scene's
   own readouts and to the one quiet line below them (§7.3 ruling 6) */
.jv-hint { position:absolute; bottom:32px; left:52px; z-index:5;
  font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.24em; color:var(--jv-wash); opacity:.6; }

/* ---------- the quiet line under the orb (SPEC §7.3 ruling 6) ----------
   Line 1 of the NOW box plus the elapsed time, centred under Agent so a long
   silent turn is readable without looking right. One line, ellipsised, never
   a second place where a state is invented.

   It gets its OWN BAND, not a seat in somebody else's: the strip between the
   scene's FLEET caption (its text ends ~61 px off the floor) and the ticker
   (26 px tall) is 35 px of clear air, and this pill is 21 px of it — 9 px
   under the caption, 5 px over the ticker. The pill is opaque on purpose:
   the orb is now min(w,h) x 0.235 and its halo reaches this far down, so a
   bare line would have to be read through Agent's own light. ESC TO CLOSE
   keeps the far left of the same strip and the pill is centred, so at 1440
   and at 2560 they never touch. */
.jv-underorb {
  position:absolute; bottom:31px; left:50%; transform:translateX(-50%); z-index:5;
  max-width:min(46vw, 520px); padding:3px 14px; border-radius:999px;
  border:1px solid rgba(58,98,255,.34); background:rgba(9,13,36,.82);
  font-family:var(--jv-mono); font-size:10px; line-height:13px; letter-spacing:.06em;
  color:var(--jv-wash); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  box-shadow:0 0 18px rgba(58,98,255,.14);
}

/* ---------- the notice line (SPEC §7.2) ----------
   What happened when a window or full screen was asked for. It follows the
   DEMO badge at the foot of the left column (amendment 3, same reason), so the
   two never fight for a seat and neither one is printed over a brain. 300 px
   is the left rail's own width, so the pill ends at x 358 (padding + border)
   while the first brain's dashed ring starts at x ≈ 384 at 1440×900 and at
   x ≈ 678 at 2560×1440. Measured, not guessed: ?notice=1&measure=rects. */
.jv-notice {
  /* absolute inside .jv-top-left (a positioned layer): a nine-second line may
     never push the rail up and cut a row off the bottom of SCOREBOARD */
  position:absolute; left:0; bottom:0; align-self:flex-start; max-width:calc(300px * var(--jv-rail-k, 1));
  padding:5px 13px; border-radius:12px; text-align:left;
  border:1px solid var(--jv-line-bright); background:rgba(9,13,36,.88);
  font-family:var(--jv-mono); font-size:9.5px; line-height:1.45; letter-spacing:.05em; color:var(--jv-wash);
  box-shadow:0 0 20px var(--jv-panel-glow);
}

/* ---------- top chrome buttons: own window, full screen (SPEC §7.2) ---------- */
.jv-chrome { display:flex; align-items:center; justify-content:flex-end; gap:5px;
  flex-shrink:0; flex-wrap:wrap; pointer-events:auto; }
.jv-cbtn {
  display:inline-flex; align-items:center; gap:5px; padding:4px 8px; border-radius:8px;
  border:1px solid var(--jv-line-bright); background:var(--jv-pod-fill);
  font-family:var(--jv-mono); font-size:8px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--jv-wash); cursor:pointer; white-space:nowrap;
  box-shadow:0 0 14px var(--jv-panel-glow);
  transition:border-color .16s ease, box-shadow .16s ease;
}
.jv-cbtn kbd { font-family:var(--jv-mono); font-size:7.5px; line-height:1.4; color:var(--jv-wash);
  border:1px solid rgba(58,98,255,.55); border-radius:3px; padding:0 3px; background:rgba(40,80,232,.28); }
.jv-cbtn:hover:not(:disabled) { border-color:var(--jv-cobalt-bright); box-shadow:0 0 22px var(--jv-glow-wide); }
.jv-cbtn:focus-visible { outline:2px solid var(--jv-cobalt-bright); outline-offset:2px; }
.jv-cbtn:disabled { cursor:not-allowed; opacity:.45; box-shadow:none; }

/* ---------- the right rail boxes (SPEC §7.4) ----------
   Same glass as every pod; only the bodies are new. NOW is the box that wins
   space when the column is tight, and every list ellipsises instead of
   scrolling — a rail that scrolls is a reading Owner cannot see. */
/* NOW wins the squeeze, but it does not eat the leftovers: on a quiet day its
   two lines would otherwise be framed by 250 px of empty box. It grows to its
   content and no further (it grows by zero), keeps the rail's largest floor,
   and still shrinks like everything else when six boxes will not fit. */
.jv-right .jv-now { flex:0 1 auto; min-height:120px; display:flex; flex-direction:column; }
.jv-right .jv-now .jv-now-body { flex:1 1 auto; }
/* Inside NOW the give-way order is a ruling, not an accident (§7 amendment 5):
   the history, the helper chips and the italic thought are what a short window
   takes, in that order. The three lines that say what Agent is doing and the
   one coral block that asks Owner for something never shrink, so they can
   never be the thing that is half-drawn. jarvisRailCaps() takes the history
   away in whole ROWS before any of this pixel-shrinking starts. */
.jv-now-body > * { flex:0 0 auto; }
.jv-now-body > .jv-now-recent { flex:0 1 auto; }
/* SPEC §8 amendments C5 — THE THOUGHT SHOWS WHOLE LINES ONLY. It used to be a
   pixel-shrinker like its neighbours, and at 1440x900 ?rows=max it was squeezed
   to 17 px with 27 px of two-line content in it: line two was sliced in half
   behind the coral block. It does not shrink any more. Its height is its
   content's — one or two whole lines of a line-height declared in WHOLE pixels
   below — so at every rung of the ladder it is an exact multiple of one line,
   and the rung (the @media below) is what takes a line away. */
.jv-now-body > .jv-now-thought { flex:0 0 auto; min-height:0; overflow:hidden; }
.jv-now-body > .jv-chipsrow { flex:0 1 auto; min-height:0; overflow:hidden; }
/* AGENT IN FLIGHT is still the rail's give-way, but it gives way in ROWS, not
   in pixels: jarvisRailCaps() hands it what is left of the shared budget after
   WAITING ON YOU has been served, and it says "+n more" for the rest. */
/* the header tag gives way before the box's own name does: a long reason
   (AGENT IN FLIGHT's reason for saying unreachable) ellipsises instead of
   folding the title onto a second line */
.jv-box-tag { margin-left:auto; min-width:0; overflow:hidden; text-overflow:ellipsis;
  font-family:var(--jv-mono); font-size:8px; letter-spacing:.12em;
  text-transform:uppercase; color:var(--jv-silver-bright); white-space:nowrap; }
.jv-now-body { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.jv-now-line { font-family:var(--jv-sans); font-weight:500; font-size:15.5px; line-height:1.2;
  color:var(--jv-wash); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-now-detail { margin-top:2px; font-family:var(--jv-mono); font-size:9.5px; color:var(--jv-cobalt-text);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-now-meta { margin-top:3px; font-family:var(--jv-mono); font-size:9px; letter-spacing:.04em;
  color:var(--jv-silver-bright); font-variant-numeric:tabular-nums; }
/* past 60 s of silence the line warms; past 180 s it goes coral. It never
   delivers a verdict: it prints how long the quiet has lasted and leaves the
   reading of it to Owner (SPEC 7.3 ruling 3). */
.jv-now-meta.jv-warm { color:var(--jv-amber); }
.jv-now-meta.jv-hot { color:#FFA79C; }
.jv-now-thought { margin-top:5px; font-size:10px; font-style:italic; line-height:1.34; color:var(--jv-body);
  display:-webkit-box; -webkit-line-clamp:2; line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
/* §7 amendment 5, re-cut by §8 amendments C5 — on a short window the thought
   gives its second line, then the line itself: a WHOLE line each time, never
   half of one, so the coral block below it always stays whole. These two rungs
   are the only thing that changes its height; it never pixel-shrinks. The 950
   is where the bigger glance type (C10) makes two lines stop paying for
   themselves; under 700 the box has four readings and no room for a fifth. */
@media (max-height: 950px) {
  .jv-now-thought { -webkit-line-clamp:1; line-clamp:1; }
}
@media (max-height: 700px) {
  .jv-now-body > .jv-now-thought { display:none; }
}
.jv-chipsrow { display:flex; flex-wrap:wrap; gap:4px; margin-top:6px; }
.jv-subchip { font-family:var(--jv-mono); font-size:8px; letter-spacing:.1em; text-transform:uppercase;
  padding:2px 6px; border-radius:999px; border:1px solid rgba(58,98,255,.5); color:var(--jv-wash);
  background:rgba(40,80,232,.18); white-space:nowrap; max-width:100%; overflow:hidden; text-overflow:ellipsis; }
.jv-subchip.jv-done { opacity:.58; }
.jv-subchip.jv-failed { border-color:rgba(232,93,79,.62); color:#FFD9D3; background:rgba(232,93,79,.14); }
.jv-now-recent { margin-top:6px; padding-top:5px; border-top:1px solid rgba(58,98,255,.24);
  min-height:0; overflow:hidden; }
.jv-rrow { display:flex; align-items:baseline; gap:6px; margin-top:2px;
  font-family:var(--jv-mono); font-size:9px; color:var(--jv-silver-bright); }
.jv-rrow:first-child { margin-top:0; }
.jv-rrow b { flex:1 1 auto; font-weight:400; color:var(--jv-body); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-rrow em { flex:0 0 auto; font-style:normal; font-variant-numeric:tabular-nums; }
.jv-rrow.jv-bad b { color:#FFD9D3; }
/* THE one coral block on the glass (§7.3 ruling 5) */
.jv-needs { margin-top:7px; padding:6px 9px; border-radius:9px; color:#FFE7E2;
  border:1px solid rgba(232,93,79,.72); font-size:10.5px; line-height:1.32;
  background:linear-gradient(180deg, rgba(232,93,79,.26) 0%, rgba(44,15,13,.6) 100%);
  box-shadow:0 0 18px var(--jv-coral-glow); }

/* ---------- Agent's STATE rows (WAITING ON YOU · AGENT IN FLIGHT) ----------
   Fixed row heights on purpose: the two lists are capped at the §7.4 maxima
   (4 and 5), so a full rail clips at a ROW boundary and never halfway down a
   sentence. WAITING ON YOU gets two lines of the ask — it is the box Owner
   has to act on; AGENT IN FLIGHT gets one and ellipsises. */
/* No max-height any more (SPEC §8.4 item 10): the ROW COUNT is the cap, and it
   is decided in whole rows by jarvisRailCaps() for this window's height. A
   pixel ceiling here cut the open row's brief in half at every size above
   1440x900, which is the one thing the rail law forbids. The two class names
   stay: they still say how many lines a row's text may run to. */
.jv-rows { min-height:0; overflow:hidden; }
.jv-srow { margin-top:6px; }
.jv-srow:first-child { margin-top:0; }
.jv-srow-t { font-size:10px; line-height:1.28; color:var(--jv-body);
  display:-webkit-box; -webkit-line-clamp:2; line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.jv-rows-1 .jv-srow-t { -webkit-line-clamp:1; line-clamp:1; }
.jv-srow-m { display:flex; align-items:baseline; gap:6px; margin-top:1px;
  font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.04em; color:var(--jv-silver-bright); }
.jv-srow-m i { font-style:normal; color:var(--jv-cobalt-text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-srow-m em { font-style:normal; margin-left:auto; white-space:nowrap; }
.jv-srow-m em.jv-over { color:#FFA79C; }
.jv-more { margin-top:5px; font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.06em; color:var(--jv-silver-bright); }
.jv-empty { font-size:10px; color:var(--jv-silver-bright); }

/* ---------- the v3 boxes (SPEC §8.4) ----------
   Two rails now. The LEFT one lives under VOICE CONTROL inside .jv-top-left
   and holds NEXT MEETING, TODAY, SPEND and SCOREBOARD; the RIGHT one gained
   AGENT'S HELPERS and OVERNIGHT JOBS. Both obey the v2 rail law: a box does
   NOT shrink, a row is never cut, and what will not fit is counted out loud
   (jarvisRailCaps() in 50-overlay.js decides that in whole rows).

   The left column is bounded so its boxes can never grow down into the mode
   word and the captions (.jv-bot-left sits at bottom:74px and is ~130px tall
   with two caption lines, so its top is ~204px off the floor at any height).
   The rail inside it is the only thing allowed to clip, which keeps the DEMO
   badge and the §7.2 notice — both flex children AFTER it — on screen. */
/* 206 px is measured, not chosen: .jv-bot-left sits at bottom:74px and is
   127 px tall with its two caption lines, so its top is 201 px off the floor at
   every height. Five pixels of air, and the left rail can never reach the mode
   word. */
.jv-top-left { bottom:206px; overflow:hidden; }
/* the name, the chips and VOICE CONTROL do not give way — at 1280x720 the
   voice buttons were being squeezed by the column. The rail below them is the
   one thing that yields, and it yields in whole rows (jarvisRailCaps). */
.jv-top-left > * { flex:0 0 auto; }
.jv-top-left > .jv-left-rail { flex:0 1 auto; }
.jv-left-rail { display:flex; flex-direction:column; align-items:stretch; gap:4px;
  width:calc(324px * var(--jv-rail-k, 1)); min-height:0; flex:0 1 auto; overflow:hidden; }
.jv-left-rail > * { flex:0 0 auto; min-height:0; }
.jv-left-rail .jv-pod { padding-top:5px; padding-bottom:5px; }
.jv-left-rail .jv-pod-h { padding-bottom:3px; margin-bottom:3px; }
.jv-left-rail .jv-pod-bar { display:none; }

/* the one number that matters in a box, in type you can read across a desk */
/* 1.25 on purpose: at 1.1 the box is 23 px and the glyphs need 25, which the
   rail's own ?measure=cut correctly reports as a cut line */
.jv-big { font-family:var(--jv-sans); font-weight:500; font-size:21px; line-height:1.25;
  color:var(--jv-wash); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  font-variant-numeric:tabular-nums; text-shadow:0 0 22px var(--jv-glow-wide); }
.jv-big.jv-warm { color:var(--jv-amber); text-shadow:0 0 22px rgba(255,180,84,.45); }
.jv-big.jv-hot { color:#FFA79C; text-shadow:0 0 22px var(--jv-coral-glow); }
.jv-subline { margin-top:2px; font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--jv-silver-bright); overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap; }
.jv-box-tag.jv-warm { color:var(--jv-amber); }

/* ---------- AGENT'S HELPERS ---------- */
.jv-hrows { min-height:0; overflow:hidden; }
.jv-hrow { margin-top:6px; }
.jv-hrow:first-child { margin-top:0; }
.jv-hrow-t { display:flex; align-items:baseline; gap:6px; font-size:10.5px; line-height:1.25; color:var(--jv-wash); }
.jv-hrow-t b { flex:1 1 auto; font-weight:400; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-hrow-t em { flex:0 0 auto; font-style:normal; font-family:var(--jv-mono); font-size:8px;
  letter-spacing:.1em; text-transform:uppercase; color:var(--jv-cobalt-text); }
.jv-hrow-m { margin-top:1px; font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.04em;
  color:var(--jv-silver-bright); font-variant-numeric:tabular-nums;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-hrow-s { margin-top:2px; font-size:9.5px; line-height:1.3; color:var(--jv-body);
  display:-webkit-box; -webkit-line-clamp:2; line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.jv-hrow.jv-live-row .jv-hrow-t b { color:var(--jv-wash); }
.jv-hrow.jv-live-row .jv-hrow-t::before { content:""; }
.jv-hrow.jv-bad .jv-hrow-t b { color:#FFD9D3; }

/* ---------- OVERNIGHT JOBS ---------- */
.jv-jobs { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.jv-jobline { display:flex; align-items:baseline; gap:7px; }
/* 1.25, the same number and the same reason as .jv-big: at 1.15 the line box is
   shorter than the glyphs it holds, and the rail's own ?measure=cut correctly
   reports the descenders being clipped — at 1x by a hair, and by 2 px once
   §8 amendments C10 scales the type on a 2560 or 3440 display. */
.jv-jobline b { font-family:var(--jv-sans); font-weight:500; font-size:17px; line-height:1.25;
  color:var(--jv-wash); font-variant-numeric:tabular-nums; }
.jv-jobline em { font-style:normal; font-family:var(--jv-sans); font-size:13px; color:#FFA79C; }
.jv-jobline span { margin-left:auto; font-family:var(--jv-mono); font-size:8.5px;
  letter-spacing:.06em; color:var(--jv-silver-bright); white-space:nowrap; }
.jv-jobs .jv-rows { margin-top:4px; }
/* SPEC §8 amendment B.5: the next run is the LAST line of the box, never the
   header tag, where it was cut to "NEXT 02:35 SAMPLE MORNING S…". */
.jv-jobnext { margin-top:4px; font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.06em;
  color:var(--jv-silver-bright); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* ---------- NEXT MEETING ---------- */
.jv-meet { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.jv-meet-t { margin-top:2px; font-size:11px; line-height:1.25; color:var(--jv-body);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-meet-m { margin-top:2px; font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.06em;
  color:var(--jv-silver-bright); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-meet .jv-rows { margin-top:5px; padding-top:4px; border-top:1px solid rgba(58,98,255,.24); }

/* ---------- TODAY (the ONE lever is line 1) ---------- */
.jv-today { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.jv-lever { display:flex; align-items:baseline; gap:7px; }
.jv-lever i { flex:0 0 auto; font-style:normal; font-family:var(--jv-mono); font-size:8px;
  letter-spacing:.14em; text-transform:uppercase; color:var(--jv-amber); }
.jv-lever span { flex:1 1 auto; font-size:12px; line-height:1.3; color:var(--jv-wash);
  display:-webkit-box; -webkit-line-clamp:2; line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.jv-today-h { margin-top:4px; font-size:10px; line-height:1.3; color:var(--jv-silver-bright);
  display:-webkit-box; -webkit-line-clamp:2; line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.jv-trows { margin-top:4px; min-height:0; overflow:hidden; }
/* SPEC §8 amendment B.4: the task text is ONE face — the same sans the ONE
   LEVER line above it uses — and the small kind tag is the only mono in the
   row. Both are said out loud here: an in-progress row used to carry a bare
   .jv-live, which is the voice line's own class (mono, .1em tracking), and the
   task inherited it, so BUILD and CONTENT read wide-spaced mono while MOMENTUM
   read sans. The row class is .jv-live-row now, and the face is declared. */
.jv-titem { display:flex; align-items:baseline; gap:6px; margin-top:3px;
  font-family:var(--jv-sans); font-size:10px; letter-spacing:normal; color:var(--jv-body); }
.jv-titem:first-child { margin-top:0; }
.jv-titem b { flex:0 0 auto; font-weight:400; color:var(--jv-silver-bright); }
.jv-titem i { flex:0 0 auto; font-style:normal; font-family:var(--jv-mono); font-size:8px;
  letter-spacing:.12em; text-transform:uppercase; color:var(--jv-cobalt-text); }
.jv-titem span { flex:1 1 auto; font-family:var(--jv-sans); letter-spacing:normal;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-titem.jv-done b { color:var(--jv-teal); }
.jv-titem.jv-done span { opacity:.72; }
.jv-titem.jv-live-row b { color:var(--jv-amber); }

/* ---------- SPEND ---------- */
.jv-spend { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.jv-spend .jv-rows { margin-top:5px; }
.jv-spend-t { margin-top:4px; font-family:var(--jv-mono); font-size:9px; letter-spacing:.04em;
  color:var(--jv-body); font-variant-numeric:tabular-nums;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-spend-c { margin-top:2px; font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.06em;
  color:var(--jv-silver-bright); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* ---------- SCOREBOARD (the streaks) ---------- */
.jv-score { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
/* the streak number and the week sit side by side: the one number that matters
   is big on the left, the seven day marks read across from it */
.jv-score-top { display:flex; align-items:flex-end; justify-content:space-between; gap:10px; }
.jv-score-l { min-width:0; }
.jv-days { display:flex; align-items:flex-end; gap:5px; }
.jv-day { display:flex; flex-direction:column; align-items:center; gap:2px; }
.jv-day i { width:9px; height:4px; border-radius:2px; background:var(--jv-silver); opacity:.35; }
.jv-day i.b-yes { background:var(--jv-teal); opacity:1; box-shadow:0 0 7px rgba(45,212,191,.8); }
.jv-day i.b-no { background:var(--jv-coral); opacity:.9; }
.jv-day i.c-yes { background:var(--jv-cyan); opacity:1; box-shadow:0 0 7px rgba(53,224,255,.8); }
.jv-day i.c-no { background:var(--jv-coral); opacity:.9; }
.jv-day em { font-style:normal; font-family:var(--jv-mono); font-size:7.5px; letter-spacing:.04em;
  color:var(--jv-silver-bright); }

/* ---------- §8 amendments C10 · THE GLANCE SIZES + THE RAIL SCALE ----------
   Owner reads these two rails across a room, on a second display. Two laws
   come out of that, and this one block is where both of them live:

   1. NO INFORMATION UNDER 11 px. Anything on a rail that carries a READING —
      a task, an ask, a helper's goal, a count, a clock, a model name, an error
      — is at least 11 px. Only TAGS and BOX TITLES (the small uppercase mono
      that NAMES a thing rather than saying it) may stay at 10 px. Nothing on a
      rail is 8 or 8.5 px any more.
   2. THE RAILS SCALE WITH THE DISPLAY. --jv-rail-k is one number, set on the
      overlay root by measure() in 50-overlay.js from the viewport WIDTH: 1
      below 2200 px, 1.25 from 2200, 1.4 from 3000. It multiplies rail WIDTH
      (above) and rail TYPE (here) and nothing else — Agent, the brains and the
      captions belong to the scene, which already grows with the stage.
      40-scene.js reads the same width through the same thresholds so its
      rail-column keep-out grows with the glass, and jarvisRailCaps() is asked
      about height ÷ k, so the ladders count in these same scaled pixels and
      the no-cut law holds at 1440, 1920, 2560 and 3440.

   Every size is calc(Npx * var(--jv-rail-k, 1)). The fallback is what the
   mirror page — which never calls measure() — reads. Padding and gaps are NOT
   scaled on purpose: leaving them fixed makes a box a little SHORTER than k
   times its 1x self, which keeps the ÷ k ladder on the safe side of the cut.
   Only the two rails are in scope here; the diagnostics drawer keeps its own
   sizes, because it is a thing you lean in and read, not a thing you glance at. */

/* the tags and the box titles — the 10 px floor */
.jv-right .jv-pod-h span, .jv-left-rail .jv-pod-h span,
.jv-right .jv-box-tag, .jv-left-rail .jv-box-tag,
.jv-right .jv-subchip, .jv-left-rail .jv-subchip,
.jv-right .jv-hrow-t em, .jv-left-rail .jv-hrow-t em,
.jv-right .jv-titem i, .jv-left-rail .jv-titem i,
.jv-right .jv-titem em, .jv-left-rail .jv-titem em,
.jv-right .jv-lever i, .jv-left-rail .jv-lever i,
.jv-right .jv-brief-l i, .jv-left-rail .jv-brief-l i,
.jv-right .jv-day em, .jv-left-rail .jv-day em,
.jv-right .jv-sysdot, .jv-left-rail .jv-sysdot {
  font-size:calc(10px * var(--jv-rail-k, 1));
}
/* everything that says something — the 11 px floor */
.jv-right .jv-now-detail, .jv-left-rail .jv-now-detail,
.jv-right .jv-now-meta, .jv-left-rail .jv-now-meta,
.jv-right .jv-rrow, .jv-left-rail .jv-rrow,
.jv-right .jv-srow-m, .jv-left-rail .jv-srow-m,
.jv-right .jv-more, .jv-left-rail .jv-more,
.jv-right .jv-empty, .jv-left-rail .jv-empty,
.jv-right .jv-subline, .jv-left-rail .jv-subline,
.jv-right .jv-hrow-m, .jv-left-rail .jv-hrow-m,
.jv-right .jv-hrow-s, .jv-left-rail .jv-hrow-s,
.jv-right .jv-jobline span, .jv-left-rail .jv-jobline span,
.jv-right .jv-jobnext, .jv-left-rail .jv-jobnext,
.jv-right .jv-meet-t, .jv-left-rail .jv-meet-t,
.jv-right .jv-meet-m, .jv-left-rail .jv-meet-m,
.jv-right .jv-today-h, .jv-left-rail .jv-today-h,
.jv-right .jv-titem, .jv-left-rail .jv-titem,
.jv-right .jv-spend-t, .jv-left-rail .jv-spend-t,
.jv-right .jv-spend-c, .jv-left-rail .jv-spend-c,
.jv-right .jv-brief-l, .jv-left-rail .jv-brief-l,
.jv-right .jv-pod-n, .jv-left-rail .jv-pod-n {
  font-size:calc(11px * var(--jv-rail-k, 1));
}
/* the three a glance lands on first, a half-step up from the floor */
.jv-right .jv-srow-t, .jv-left-rail .jv-srow-t,
.jv-right .jv-hrow-t, .jv-left-rail .jv-hrow-t,
.jv-right .jv-needs, .jv-left-rail .jv-needs {
  font-size:calc(11.5px * var(--jv-rail-k, 1));
}
/* the type that was already big enough: it only takes the scale */
.jv-right .jv-now-line, .jv-left-rail .jv-now-line { font-size:calc(15.5px * var(--jv-rail-k, 1)); }
.jv-right .jv-lever span, .jv-left-rail .jv-lever span { font-size:calc(12px * var(--jv-rail-k, 1)); }
.jv-right .jv-big, .jv-left-rail .jv-big { font-size:calc(21px * var(--jv-rail-k, 1)); }
.jv-right .jv-jobline b, .jv-left-rail .jv-jobline b { font-size:calc(17px * var(--jv-rail-k, 1)); }
.jv-right .jv-jobline em, .jv-left-rail .jv-jobline em { font-size:calc(13px * var(--jv-rail-k, 1)); }
/* SPEC §8 amendments D2 — the pod's own value slot. Every rail box is built on
   the same pod and carries it, hidden, under its own body; if one is ever shown
   it is a rail reading and it grows with the rail like the rest. */
.jv-right .jv-pod-v, .jv-left-rail .jv-pod-v { font-size:calc(12px * var(--jv-rail-k, 1)); }
/* the seven day marks are the SCOREBOARD's reading, so they grow with it */
.jv-right .jv-day i, .jv-left-rail .jv-day i {
  width:calc(9px * var(--jv-rail-k, 1)); height:calc(4px * var(--jv-rail-k, 1));
}
/* The two window buttons and the clock ride INSIDE the right rail (they are its
   first child), so they scale with it — otherwise at 3440 they read as a row of
   specks above type twice their size. They keep their 1x size: they are
   CONTROLS and a clock, not readings, so the 11 px floor above is not theirs,
   and leaving 1x alone keeps the ladder's measured rungs exactly where they
   were. The scale alone carries them past 10 px on the displays that asked for
   this rule (8 x 1.25 = 10, 8 x 1.4 = 11.2). */
.jv-right .jv-cbtn { font-size:calc(8px * var(--jv-rail-k, 1)); }
.jv-right .jv-cbtn kbd { font-size:calc(7.5px * var(--jv-rail-k, 1)); }
.jv-right .jv-clock { font-size:calc(12px * var(--jv-rail-k, 1)); }
/* §8 amendments C9 — the status word this plugin does not know, beside its task */
.jv-titem em { flex:0 0 auto; margin-left:auto; font-style:normal; font-family:var(--jv-mono);
  letter-spacing:.1em; text-transform:uppercase; color:var(--jv-amber); white-space:nowrap; }
/* §8 amendments C5 — the NOW thought's line box is declared in WHOLE pixels so
   its height is always an exact multiple of one line, at k = 1, 1.25 and 1.4
   alike. The rung below takes a whole LINE; nothing ever takes half of one. */
.jv-right .jv-now-thought, .jv-left-rail .jv-now-thought {
  font-size:calc(11px * var(--jv-rail-k, 1)); line-height:calc(14px * var(--jv-rail-k, 1));
}

/* ---------- the open WAITING ON YOU row (SPEC §8.4 item 3) ----------
   A row is a real button: keyboard-reachable, Enter or Space opens it, and it
   blurs itself after a click so the composer keeps the caret and the chord
   keys keep working. The open row carries Agent's plain words underneath. */
.jv-waiting .jv-rows { pointer-events:auto; }
button.jv-srow { display:block; width:100%; text-align:left; appearance:none; -webkit-appearance:none;
  border:1px solid transparent; border-radius:9px; background:transparent;
  padding:4px 6px; margin-top:4px; color:inherit; font:inherit; cursor:pointer;
  transition:border-color .16s ease, background .16s ease; }
button.jv-srow:first-child { margin-top:0; }
button.jv-srow:hover { border-color:rgba(58,98,255,.42); background:rgba(40,80,232,.1); }
button.jv-srow:focus-visible { outline:2px solid var(--jv-cobalt-bright); outline-offset:1px; }
button.jv-srow.jv-open { border-color:var(--jv-line-bright); background:rgba(40,80,232,.16);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06); }
/* SPEC §8 amendments D2 — NO SIZE HERE. This rule is more specific than the
   rail block above (two classes and a tag against two classes), so a plain
   11px here BEAT the rail scale, and at 2560 the ask's title was drawn smaller
   than the id line under it. The open row's title is a rail reading like any
   other: the rail block sizes it, 11.5px x --jv-rail-k, and this rule only
   brightens it. */
button.jv-srow .jv-srow-t { color:var(--jv-wash); }
.jv-brief { margin-top:4px; padding-top:4px; border-top:1px solid rgba(58,98,255,.24); }
.jv-brief-l { display:flex; align-items:baseline; gap:6px; margin-top:3px; font-size:10px;
  line-height:1.3; color:var(--jv-body); }
.jv-brief-l:first-child { margin-top:0; }
.jv-brief-l i { flex:0 0 42px; font-style:normal; font-family:var(--jv-mono); font-size:8px;
  letter-spacing:.12em; text-transform:uppercase; color:var(--jv-cobalt-text); }
.jv-brief-l span { flex:1 1 auto;
  display:-webkit-box; -webkit-line-clamp:2; line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.jv-brief-l.jv-brief-none { color:var(--jv-silver-bright); font-style:italic; }

/* ---------- FLEET (AGENTS AT WORK, now in the drawer) ---------- */
.jv-agents { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.jv-agents-busy { font-family:var(--jv-mono); font-size:11px; color:var(--jv-wash);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.jv-agents .jv-rows { margin-top:3px; max-height:30px; flex:0 1 auto; }
.jv-agents-idle { margin-top:3px; font-size:9.5px; color:var(--jv-silver-bright); }

/* ---------- SYSTEMS: one row of dots, the drawer's door ---------- */
.jv-sysrow { display:flex; flex-wrap:wrap; gap:5px 9px; pointer-events:auto; cursor:pointer; }
.jv-sysdot { display:inline-flex; align-items:center; gap:4px; font-family:var(--jv-mono);
  font-size:8px; letter-spacing:.1em; text-transform:uppercase; color:var(--jv-silver-bright); white-space:nowrap; }
.jv-sysdot i { flex:0 0 auto; width:5px; height:5px; border-radius:50%; background:var(--jv-silver); opacity:.7; }
.jv-sysdot.ok i { background:var(--jv-teal); box-shadow:0 0 8px rgba(45,212,191,.9); opacity:1; }
.jv-sysdot.warn i { background:var(--jv-amber); box-shadow:0 0 8px rgba(255,180,84,.9); opacity:1; }
.jv-sysdot.bad i { background:var(--jv-coral); box-shadow:0 0 8px var(--jv-coral-glow); opacity:1; }

/* ---------- the diagnostics drawer (⌃⌥D, or a click on SYSTEMS) ----------
   Today's CONNECTION, SCAN, VOICE, BRAINS and TELEMETRY pods, unchanged. It
   takes the rail's seat while it is open, so nothing is ever half-clipped. */
.jv-drawer {
  position:absolute; top:26px; bottom:56px; right:30px; width:calc(300px * var(--jv-rail-k, 1)); z-index:7;
  display:flex; flex-direction:column; align-items:stretch; gap:8px;
  min-height:0; overflow:hidden; pointer-events:auto;
}
.jv-drawer .jv-pod { padding-top:7px; padding-bottom:7px; }
.jv-drawer .jv-scan { display:flex; flex-direction:column; flex-shrink:200; min-height:0; overflow:hidden; }
.jv-drawer .jv-scan > * { flex:0 0 auto; }
.jv-drawer .jv-scan .jv-radar { flex:0 1 auto; min-height:0; overflow:hidden; }
.jv-drawer > * { flex:0 1 auto; min-height:0; }
.jv-drawer-h { display:flex; align-items:center; justify-content:space-between; gap:8px; flex-shrink:0;
  font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.2em; text-transform:uppercase; color:var(--jv-wash); }

/* ---------- voice controls (SPEC §4.6, amended 2026-09-18 18:14) ----------
   The VOICE CONTROL pod in the LEFT rail, directly under TELEMETRY — the centre
   band belongs to Agent. Glass buttons in the Look v1.1 family: cobalt-bright
   border, wash type, coral when the state is live/muted/asleep, dim with a title
   reason when the plugin knows the door is shut. */
.jv-voice {
  display:flex; flex-direction:column; align-items:stretch; gap:6px;
  /* the rail layer is pointer-events:none so the scene stays draggable; the one
     interactive island in it turns hit-testing back on for itself */
  pointer-events:auto;
}
.jv-voice-row { display:flex; flex-wrap:wrap; align-items:stretch; gap:6px; }
.jv-vbtn {
  flex:1 1 auto; display:inline-flex; align-items:center; justify-content:center;
  gap:6px; padding:7px 8px; border-radius:9px;
  border:1px solid var(--jv-line-bright); background:var(--jv-pod-fill);
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  font-family:var(--jv-mono); font-size:9px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--jv-wash); cursor:pointer; white-space:nowrap;
  box-shadow:0 0 20px var(--jv-panel-glow), inset 0 1px 0 rgba(255,255,255,.07);
  transition:border-color .16s ease, box-shadow .16s ease, background .16s ease;
}
.jv-vbtn kbd {
  flex:0 0 auto;
  font-family:var(--jv-mono); font-size:8px; letter-spacing:.04em; line-height:1.4;
  color:var(--jv-wash); border:1px solid rgba(58,98,255,.55); border-radius:4px;
  padding:1px 4px; background:rgba(40,80,232,.28);
}
.jv-vbtn:hover:not(:disabled) {
  border-color:var(--jv-cobalt-bright);
  box-shadow:0 0 30px var(--jv-glow-wide), inset 0 1px 0 rgba(255,255,255,.1);
}
.jv-vbtn:focus-visible { outline:2px solid var(--jv-cobalt-bright); outline-offset:2px; }
/* live call / muted mic / sleeping Agent — the one coral accent down here */
.jv-vbtn.jv-live {
  border-color:rgba(232,93,79,.7); color:#FFE7E2;
  background:linear-gradient(180deg, rgba(232,93,79,.24) 0%, rgba(44,15,13,.6) 100%);
  box-shadow:0 0 24px var(--jv-coral-glow), inset 0 1px 0 rgba(255,255,255,.08);
}
.jv-vbtn.jv-live kbd { color:#FFE7E2; border-color:rgba(232,93,79,.55); background:rgba(232,93,79,.2); }
/* waiting on the bus: it says "starting…" and breathes until the bus answers */
.jv-vbtn.jv-pending { border-color:rgba(58,98,255,.72); animation:jv-wait 1.1s ease-in-out infinite; }
@keyframes jv-wait { 0%,100% { opacity:.6 } 50% { opacity:1 } }
.jv-vbtn:disabled { cursor:not-allowed; opacity:.45; box-shadow:none; }
.jv-voice-tag { font-family:var(--jv-mono); font-size:8.5px; letter-spacing:.18em; text-transform:uppercase; color:var(--jv-cobalt-text); overflow-wrap:anywhere; }
.jv-voice.jv-demo-on .jv-voice-tag { color:var(--jv-amber); }
/* the honest line in the VOICE pod when a command went nowhere */
.jv-cmdmsg { margin-top:4px; font-family:var(--jv-mono); font-size:9px; letter-spacing:.05em; color:#FFD9D3; overflow-wrap:anywhere; }

/* ---------- statusbar chip (lives in the app chrome, not the overlay) ---------- */
.jv-chip {
  display:inline-flex; align-items:center; gap:6px; border:0; background:transparent;
  padding:0 6px; height:100%; cursor:pointer; font-family:var(--jv-mono);
  font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; color:inherit; opacity:.8;
}
.jv-chip:hover { opacity:1; }
.jv-chip i { width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 9px currentColor; }
.jv-chip.jv-on i { animation:jv-blink 2s ease-in-out infinite; }
@keyframes jv-blink { 0%,100% { opacity:.35 } 50% { opacity:1 } }

@media (prefers-reduced-motion: reduce) {
  .jv-overlay { animation:none; }
  .jv-ticker-track { animation:none; }
  .jv-chip.jv-on i { animation:none; }
  .jv-radar-sweep { animation:none; }
  .jv-tbar { transition:none; }
  .jv-vbtn { transition:none; }
  .jv-vbtn.jv-pending { animation:none; }
}
`
