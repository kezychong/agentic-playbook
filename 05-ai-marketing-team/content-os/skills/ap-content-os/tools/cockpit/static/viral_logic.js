(function(root, factory){
  "use strict";
  var api = factory();
  if(typeof module === "object" && module.exports) module.exports = api;
  else root.CockpitViralLogic = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function(){
  "use strict";

  // Splits the library into the two honest views the tab shows.
  //
  //   recent          posted inside the chosen window, nothing else
  //   resurgingOlder  older, but repeated view counts prove a new burst
  //   allTime         historical winners, with no claim about today
  //   unvalidated     never recorded the numbers, so reference only

  function inPostedWindow(entry, windowDays){
    return !!(
      entry
      && Array.isArray(entry.posted_windows)
      && entry.posted_windows.indexOf(windowDays) !== -1
    );
  }

  function byMultiple(a, b){
    return (Number(b && b.multiple) || 0) - (Number(a && a.multiple) || 0);
  }

  function buildViralView(entries, state){
    entries = Array.isArray(entries) ? entries : [];
    state = state || {};
    var windowDays = Number(state.window) || 7;
    var includeOwn = state.includeOwn !== false;
    var visible = entries.filter(function(entry){
      return includeOwn || entry.own !== true;
    });
    var validated = visible.filter(function(entry){
      return entry.admission_valid !== false;
    });
    var unvalidated = visible.filter(function(entry){
      return entry.admission_valid === false;
    }).sort(byMultiple);
    var recent = validated.filter(function(entry){
      return inPostedWindow(entry, windowDays);
    }).sort(byMultiple);
    var resurgingOlder = validated.filter(function(entry){
      return !inPostedWindow(entry, windowDays)
        && entry.velocity
        && entry.velocity.is_resurging === true;
    }).sort(byMultiple);
    var allTime = validated.slice().sort(byMultiple);

    return {
      recent: recent,
      resurgingOlder: resurgingOlder,
      currentEntries: recent.concat(resurgingOlder),
      allTime: allTime,
      unvalidated: unvalidated
    };
  }

  return {
    buildViralView: buildViralView,
    inPostedWindow: inPostedWindow
  };
});
