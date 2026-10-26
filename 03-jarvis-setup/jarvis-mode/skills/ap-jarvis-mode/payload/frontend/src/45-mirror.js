/* ==========================================================================
 * 45-mirror.js — Jarvis mirror runtime (PURE: no import/export, no SDK)
 *
 * scripts/build.py inlines 10-theme + 40-scene + THIS file into
 * dashboard/mirror.html, a standalone page served by the backend half at
 * GET /api/plugins/hermes-jarvis/mirror. It must work with no bundler, no
 * React and no desktop SDK — just document, WebSocket and location.
 *
 *   startJarvisMirror(rootEl, { url }) -> { stop(), destroy(), scene }
 *
 * It owns nothing but the page: the scene draws itself, and the only chrome
 * is one honest stamp bottom-right — how old the last presence frame is, or
 * OFFLINE / SIGNED OUT / UNREACHABLE when there is nothing live to show. It
 * never invents a reading.
 * ========================================================================== */
function startJarvisMirror(rootEl, opts) {
  opts = opts || {};
  const root = rootEl || document.body;
  const T = (typeof JARVIS_SCENE_TOKENS !== 'undefined' && JARVIS_SCENE_TOKENS) ? JARVIS_SCENE_TOKENS
    : { bg: '#07080C', silver: '#8A93A6', coral: '#E85D4F', line: '#1F2229', wash: '#E5EBFF', bodyDark: '#C8CDD8' };
  const MONO = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace";
  let expectedProfile = String(opts.profileId || '').trim();
  if (!expectedProfile) {
    try { expectedProfile = String(new URLSearchParams(location.search).get('expected_profile') || '').trim(); } catch (e) { expectedProfile = ''; }
  }
  const bridgeId = String(opts.bridgeId || '').trim();
  const parentWsBridge = opts.parentWsBridge === true && !!bridgeId && window.parent && window.parent !== window;

  /* ------------------------------------------------------------- the page -- */
  root.style.margin = '0';
  root.style.padding = '0';
  root.style.background = T.bg;
  root.style.overflow = 'hidden';
  if (root === document.body) { document.documentElement.style.background = T.bg; document.documentElement.style.height = '100%'; }
  if (getComputedStyle(root).position === 'static') root.style.position = 'relative';

  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;display:block';
  root.appendChild(canvas);

  const stamp = document.createElement('div');
  stamp.style.cssText = 'position:absolute;right:16px;bottom:14px;z-index:3;pointer-events:none;' +
    'font:10px/1.4 ' + MONO + ';letter-spacing:.2em;color:' + T.silver;
  root.appendChild(stamp);

  const card = document.createElement('div');
  /* top-LEFT, clear of the brain labels that live along the top-centre arc */
  card.style.cssText = 'position:absolute;left:24px;top:52px;z-index:4;' +
    'display:none;max-width:min(360px,30vw);padding:14px 18px;border-radius:12px;' +
    'background:rgba(255,255,255,.04);border:1px solid ' + T.line + ';backdrop-filter:blur(6px);' +
    'font:13px/1.55 system-ui,-apple-system,sans-serif;color:' + T.bodyDark;
  root.appendChild(card);

  /* -------------------------------------------------------------- the scene */
  const scene = createScene(canvas, { dpr: window.devicePixelRatio || 1 });
  function size() {
    const w = root === document.body ? window.innerWidth : (root.clientWidth || window.innerWidth);
    const h = root === document.body ? window.innerHeight : (root.clientHeight || window.innerHeight);
    scene.setSize(w, h);
  }
  size();
  window.addEventListener('resize', size);
  scene.start();

  /* ------------------------------------------------------------ the socket --
   * The host's WebSocket auth never reads cookies (docs/BACKEND.md, "WebSocket
   * auth"): a browser page cannot upgrade on its session cookie alone. So every
   * connect — the first and every reconnect — first POSTs /api/auth/ws-ticket on
   * the same origin, cookie-authenticated, and spends that single-use ticket in
   * the query string. The ticket is never stored beyond the connect it opens. */
  const wsUrl = opts.url || ((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host +
    '/api/plugins/hermes-jarvis/events');
  const ticketUrl = ticketEndpoint(wsUrl);
  let ws = null, backoff = 1000, retry = 0, open = false, dead = false;
  let lastPresenceAt = 0, panelUntil = 0, bound = false;
  let authState = '';      /* '' | 'signed-out' | 'unreachable' — never a fake reading */
  let attempt = 0;         /* drops a mint that lands after stop() or after a newer connect */
  let bridgeSeq = 0;
  const bridgePending = {};

  function ticketEndpoint(url) {
    const origin = /^wss?:\/\/[^/?#]+/.exec(String(url)) || /^https?:\/\/[^/?#]+/.exec(String(url));
    return origin ? origin[0].replace(/^ws/, 'http') + '/api/auth/ws-ticket' : '/api/auth/ws-ticket';
  }

  function applyFrame(f) {
    if (!f || typeof f !== 'object') return;
    const d = f.data;
    if (f.type === 'data' || f.type === 'state') {
      const checked = jarvisValidateSettings(d && d.settings, expectedProfile);
      if (!checked.ok) {
        bound = false;
        authState = expectedProfile ? 'profile-mismatch' : 'profile-required';
        clearPrivate();
        paintStamp();
        return;
      }
      bound = true;
      authState = '';
      scene.setData(Object.assign({}, d, { settings: checked.settings }));
      return;
    }
    if (!bound) return;
    if (f.type === 'presence') {
      if (d) { scene.setPresence(d); lastPresenceAt = Date.now(); }
      return;
    }
    if (f.type === 'panel') { showPanel(d); return; }
    if (f.type === 'hello') {
      /* The state frame binds identity. Priming payloads wait for it. */
    }
  }

  function clearPrivate() {
    lastPresenceAt = 0;
    panelUntil = 0;
    card.style.display = 'none';
    scene.setPresence({ mode: 'idle', call: 'off', live: '', source: { voice: 'none', mic: 'none' }, levels: { voice: 0, mic: 0 } });
    scene.setData({ settings: null, brains: [], senses: [], fleet: [], jobs: [], events: [], panel: null });
  }

  function showPanel(p) {
    if (!p || !p.title) { card.style.display = 'none'; panelUntil = 0; return; }
    card.innerHTML = '';
    const h = document.createElement('div');
    h.style.cssText = 'font:10px/1.4 ' + MONO + ';text-transform:uppercase;letter-spacing:.22em;color:' + T.silver + ';margin-bottom:6px';
    h.textContent = String(p.title);
    const b = document.createElement('div');
    b.textContent = String(p.body == null ? '' : p.body);
    card.appendChild(h); card.appendChild(b);
    card.style.display = 'block';
    panelUntil = Date.now() + (Math.max(3, +p.ttl_s || +p.ttl || 20) * 1000);
  }

  function mintTicket() {
    if (typeof fetch !== 'function') return Promise.reject({ kind: 'unreachable' });
    return fetch(ticketUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: '{}'
    }).then(function (res) {
      if (!res) throw { kind: 'unreachable' };
      if (res.status === 401 || res.status === 403) throw { kind: 'signed-out' };
      if (!res.ok) throw { kind: 'unreachable' };
      return res.json();
    }).then(function (body) {
      const ticket = body && body.ticket;
      if (!ticket) throw { kind: 'unreachable' };
      return String(ticket);
    });
  }

  function onParentMessage(event) {
    const body = event && event.data;
    if (!parentWsBridge || event.source !== window.parent || !body ||
        body.type !== 'hermes-jarvis:ws-url-response' || body.bridgeId !== bridgeId) return;
    const row = bridgePending[String(body.requestId || '')];
    if (!row) return;
    delete bridgePending[String(body.requestId || '')];
    clearTimeout(row.timer);
    if (body.url) row.resolve(String(body.url));
    else row.reject({ kind: 'unreachable' });
  }

  function parentSocketUrl() {
    return new Promise(function (resolve, reject) {
      const requestId = String(++bridgeSeq);
      const timer = setTimeout(function () {
        delete bridgePending[requestId];
        reject({ kind: 'unreachable' });
      }, 5000);
      bridgePending[requestId] = { resolve: resolve, reject: reject, timer: timer };
      window.parent.postMessage({
        type: 'hermes-jarvis:ws-url-request', bridgeId: bridgeId, requestId: requestId
      }, '*');
    });
  }

  function nextSocketUrl() {
    if (parentWsBridge) return parentSocketUrl();
    return mintTicket().then(function (ticket) {
      return wsUrl + (wsUrl.indexOf('?') === -1 ? '?' : '&') + 'ticket=' + encodeURIComponent(ticket);
    });
  }

  if (parentWsBridge) window.addEventListener('message', onParentMessage);

  function connect() {
    if (dead) return;
    if (!expectedProfile) { authState = 'profile-required'; clearPrivate(); paintStamp(); return; }
    const mine = ++attempt;
    nextSocketUrl().then(function (url) {
      if (dead || mine !== attempt) return;                /* a stale mint opens nothing */
      authState = '';
      try { ws = new WebSocket(url); } catch (e) { ws = null; schedule(); return; }
      ws.onopen = function () { open = true; backoff = 1000; };
      ws.onmessage = function (ev) {
        let f = null;
        try { f = JSON.parse(ev.data); } catch (e) { return; }
        if (Array.isArray(f)) { for (let i = 0; i < f.length; i++) applyFrame(f[i]); } else applyFrame(f);
      };
      ws.onerror = function () { /* onclose does the work */ };
      ws.onclose = function () { open = false; ws = null; schedule(); };
    }, function (err) {
      if (dead || mine !== attempt) return;
      /* no ticket, no socket, no reading — say which wall we hit and back off */
      authState = (err && err.kind === 'signed-out') ? 'signed-out' : 'unreachable';
      open = false; ws = null;
      paintStamp();
      schedule();
    });
  }

  function schedule() {
    if (dead || retry) return;
    retry = setTimeout(function () { retry = 0; connect(); }, backoff);
    backoff = Math.min(30000, Math.round(backoff * 1.8));   /* 1 s -> 30 s */
  }

  /* ------------------------------------------------------------- the stamp -- */
  function paintStamp() {
    if (dead) return;
    const now = Date.now();
    if (panelUntil && now > panelUntil) { card.style.display = 'none'; panelUntil = 0; }
    if (authState === 'signed-out') {
      stamp.textContent = 'SIGNED OUT · OPEN THE DASHBOARD AND SIGN IN, THEN RELOAD';
      stamp.style.color = T.coral;
      return;
    }
    if (authState === 'unreachable') {
      stamp.textContent = 'UNREACHABLE';
      stamp.style.color = T.coral;
      return;
    }
    if (authState === 'profile-required') {
      stamp.textContent = 'SELECT A CHIEF PROFILE, THEN OPEN ITS DASHBOARD';
      stamp.style.color = T.coral;
      return;
    }
    if (authState === 'profile-mismatch') {
      stamp.textContent = 'CONNECT TO THIS CHIEF PROFILE DASHBOARD';
      stamp.style.color = T.coral;
      return;
    }
    if (!open) {
      stamp.textContent = 'OFFLINE';
      stamp.style.color = T.coral;
      return;
    }
    if (!lastPresenceAt) {
      stamp.textContent = 'MIRROR · NO PRESENCE YET';
      stamp.style.color = T.silver;
      return;
    }
    const age = Math.floor((now - lastPresenceAt) / 1000);
    stamp.textContent = 'MIRROR · ' + age + 's ago';
    stamp.style.color = age > 10 ? T.coral : T.silver;     /* stale = coral */
  }
  paintStamp();
  const stampTimer = setInterval(paintStamp, 500);
  connect();

  const api = {
    scene: scene,
    stop: function () {
      dead = true;
      attempt++;                                 /* orphan any mint still in flight */
      clearInterval(stampTimer);
      if (retry) { clearTimeout(retry); retry = 0; }
      if (parentWsBridge) window.removeEventListener('message', onParentMessage);
      Object.keys(bridgePending).forEach(function (key) {
        clearTimeout(bridgePending[key].timer);
        delete bridgePending[key];
      });
      try { if (ws) { ws.onclose = null; ws.close(); } } catch (e) { /* noop */ }
      ws = null; open = false;
      scene.stop();
      return api;
    },
    destroy: function () {
      api.stop();
      window.removeEventListener('resize', size);
      scene.destroy();
      try { root.removeChild(canvas); root.removeChild(stamp); root.removeChild(card); } catch (e) { /* noop */ }
      return api;
    }
  };
  return api;
}
