// Jarvis mode dashboard tab. The web dashboard SDK is intentionally different
// from the Desktop SDK: authenticated HTTP/WS helpers are its auth boundary.
(function () {
  "use strict";

  var SDK = window.__HERMES_PLUGIN_SDK__;
  var host = window.__HERMES_PLUGINS__;
  if (!SDK || !host || !SDK.React || !SDK.hooks || typeof SDK.fetchJSON !== "function" ||
      typeof SDK.authedFetch !== "function" || typeof SDK.buildWsUrl !== "function") return;

  var React = SDK.React;
  var h = React.createElement;
  var useState = SDK.hooks.useState;
  var useEffect = SDK.hooks.useEffect;
  var useRef = SDK.hooks.useRef;
  var MIRROR_URL = "/api/plugins/hermes-jarvis/mirror";
  var STATE_URL = "/api/plugins/hermes-jarvis/state";
  var EVENTS_URL = "/api/plugins/hermes-jarvis/events";

  var wrapStyle = {
    position: "absolute", inset: 0, width: "100%", height: "100%", minHeight: "100%",
    background: "#07080C", overflow: "hidden"
  };
  var frameStyle = { display: "block", width: "100%", height: "100%", border: "0", background: "#07080C" };

  function profileFromState(body) {
    var settings = body && body.settings;
    if (!settings || typeof settings !== "object" || Array.isArray(settings) ||
        settings.schema_version !== 1 || typeof settings.profile_id !== "string") return "";
    return settings.profile_id.trim();
  }

  function JarvisPage() {
    var state = useState({ html: "", name: "", error: "Connecting to this chief profile dashboard…" });
    var view = state[0];
    var setView = state[1];
    var frameRef = useRef(null);

    useEffect(function () {
      var dead = false;
      var bridgeId = "jarvis-web-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);

      function onMessage(event) {
        var frame = frameRef.current && frameRef.current.contentWindow;
        var data = event && event.data;
        if (!frame || event.source !== frame || !data || data.type !== "hermes-jarvis:ws-url-request" ||
            data.bridgeId !== bridgeId || typeof data.requestId !== "string") return;
        var requestId = data.requestId;
        Promise.resolve(SDK.buildWsUrl(EVENTS_URL)).then(function (url) {
          if (dead || !frameRef.current || frameRef.current.contentWindow !== frame) return;
          frame.postMessage({ type: "hermes-jarvis:ws-url-response", bridgeId: bridgeId, requestId: requestId, url: String(url || "") }, "*");
        }, function () {
          if (dead || !frameRef.current || frameRef.current.contentWindow !== frame) return;
          frame.postMessage({ type: "hermes-jarvis:ws-url-response", bridgeId: bridgeId, requestId: requestId, error: "unreachable" }, "*");
        });
      }

      window.addEventListener("message", onMessage);
      setView({ html: "", name: "", error: "Connecting to this chief profile dashboard…" });
      Promise.resolve(SDK.fetchJSON(STATE_URL)).then(function (body) {
        var profileId = profileFromState(body);
        if (!profileId) throw new Error("dashboard backend did not identify its chief profile");
        return Promise.resolve(SDK.authedFetch(MIRROR_URL)).then(function (response) {
          if (!response || !response.ok || typeof response.text !== "function") throw new Error("mirror unavailable");
          return response.text();
        }).then(function (html) { return { profileId: profileId, html: String(html || "") }; });
      }).then(function (ready) {
        if (dead || !ready.html) return;
        setView({
          html: ready.html,
          name: JSON.stringify({ type: "hermes-jarvis-mirror", profileId: ready.profileId, bridgeId: bridgeId, parentWsBridge: true }),
          error: ""
        });
      }, function () {
        if (!dead) setView({ html: "", name: "", error: "Connect to this chief profile dashboard." });
      });

      return function () {
        dead = true;
        window.removeEventListener("message", onMessage);
      };
    }, []);

    return h("div", { style: wrapStyle, "data-jarvis-tab": "mirror" },
      view.html ? h("iframe", {
        ref: frameRef, srcDoc: view.html, name: view.name, title: "Jarvis mode mirror",
        style: frameStyle, allow: "autoplay; fullscreen", loading: "eager"
      }) : h("div", { style: { color: "#E85D4F", padding: "24px", fontFamily: "system-ui" } }, view.error)
    );
  }

  host.register("hermes-jarvis", JarvisPage);
})();
