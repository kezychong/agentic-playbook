(function(root, factory){
  var api = factory();
  if(typeof module === "object" && module.exports) module.exports = api;
  if(root) root.CockpitPatternsLogic = api;
})(typeof self !== "undefined" ? self : this, function(){
  "use strict";

  // Reads the generated pattern file. It calculates nothing of its own: every
  // state, count, and comparison already exists in the file, and this module
  // only resolves the ids and formats what is there. When the file is stale,
  // recommendations are paused rather than shown with a warning attached.

  var HOUR_MS = 60 * 60 * 1000;
  // Ten days. The read behind this tab is rebuilt once a week, so anything
  // tighter than that would mark a perfectly current read as stale for most
  // of every week.
  var STALE_AFTER_HOURS = 240;

  function isRecord(value){
    return !!value && typeof value === "object" && !Array.isArray(value);
  }

  function timestampMs(value){
    if(typeof value !== "string" || !value.trim()) return null;
    var parsed = Date.parse(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  // Three states for one date field, because two of them mean opposite
  // things. "absent" is a field nothing has been written into yet, which is
  // what a brand-new file looks like. "unreadable" is a field with something
  // in it that is not a date, which is damage. Saying damage when a file was
  // built seconds ago is the mistake this tells apart.
  function fieldState(value){
    if(value == null) return "absent";
    if(typeof value !== "string" || !value.trim()) return "absent";
    return timestampMs(value) != null ? "readable" : "unreadable";
  }

  function scanState(freshness){
    if(freshness == null) return { state:"absent", ms:null };
    if(!isRecord(freshness)) return { state:"unreadable", ms:null };
    var candidates = [freshness.w2_last_success, freshness.last_scan_success, freshness.last_success];
    var damaged = false;
    for(var i = 0; i < candidates.length; i++){
      var state = fieldState(candidates[i]);
      if(state === "readable") return { state:"readable", ms:timestampMs(candidates[i]) };
      if(state === "unreadable") damaged = true;
    }
    return { state: damaged ? "unreadable" : "absent", ms:null };
  }

  function feedStatus(feed, nowValue){
    var nowMs = nowValue instanceof Date ? nowValue.getTime() : Number(nowValue);
    if(!Number.isFinite(nowMs)) nowMs = Date.now();
    if(!isRecord(feed)){
      return { available:false, stale:true, reason:"There is no pattern read to show yet." };
    }
    var generated = fieldState(feed.generated_at);
    var scan = scanState(feed.freshness);
    if(generated !== "readable" || scan.state !== "readable"){
      var damaged = generated === "unreadable" || scan.state === "unreadable";
      return {
        available:true,
        stale:true,
        first_run:!damaged,
        reason: damaged
          ? "The dates on this pattern read are missing or unreadable."
          : "No confirmed weekly read yet. Patterns firm up after the first weekly research runs."
      };
    }
    var generatedMs = timestampMs(feed.generated_at);
    var scanMs = scan.ms;
    var scanAgeHours = (nowMs - scanMs) / HOUR_MS;
    if(scanAgeHours > STALE_AFTER_HOURS){
      return { available:true, stale:true, reason:"The last successful look at your numbers is more than 10 days old." };
    }
    var feedLagHours = (scanMs - generatedMs) / HOUR_MS;
    if(feedLagHours > STALE_AFTER_HOURS){
      return { available:true, stale:true, reason:"This pattern read is more than 10 days behind the last look at your numbers." };
    }
    return {
      available:true,
      stale:false,
      reason:"",
      provisional:feed.provisional === true,
      generated_at:feed.generated_at,
      as_of_date:typeof feed.as_of_date === "string" ? feed.as_of_date : "",
      last_confirmed_snapshot:typeof feed.last_confirmed_snapshot === "string" ? feed.last_confirmed_snapshot : ""
    };
  }

  function recordIdentifier(record){
    if(!isRecord(record)) return "";
    if(typeof record.record_id === "string" && record.record_id) return record.record_id;
    return typeof record.id === "string" ? record.id : "";
  }

  function patternLabel(record){
    if(!isRecord(record)) return "";
    if(isRecord(record.pattern) && typeof record.pattern.label === "string" && record.pattern.label) return record.pattern.label;
    var fallbacks = [record.plain_english, record.pattern_name, record.label, record.name, record.pattern_id, record.id];
    for(var i = 0; i < fallbacks.length; i++){
      if(typeof fallbacks[i] === "string" && fallbacks[i]) return fallbacks[i];
    }
    return "";
  }

  function patternCounts(record){
    var windows = isRecord(record) && isRecord(record.windows) ? record.windows : {};
    var current = isRecord(windows.days_14) ? windows.days_14 : {};
    var metrics = isRecord(record) && isRecord(record.metrics) ? record.metrics : {};
    var legacy = isRecord(metrics.current_14d) ? metrics.current_14d : {};
    return {
      creators:current.distinct_creator_count != null ? current.distinct_creator_count : legacy.distinct_creators,
      reels:current.eligible_reel_count != null ? current.eligible_reel_count : legacy.eligible_reels,
      families:current.distinct_family_count != null ? current.distinct_family_count : legacy.distinct_families
    };
  }

  function patternComparison(record){
    var windows = isRecord(record) && isRecord(record.windows) ? record.windows : {};
    var current = isRecord(windows.days_14) ? windows.days_14 : {};
    var comparison = isRecord(record) && isRecord(record.comparison) ? record.comparison : {};
    var metrics = isRecord(record) && isRecord(record.metrics) ? record.metrics : {};
    var legacyCurrent = isRecord(metrics.current_14d) ? metrics.current_14d : {};
    var legacyReference = isRecord(metrics.reference_mean) ? metrics.reference_mean : {};
    return {
      current:current.creator_coverage != null ? current.creator_coverage : legacyCurrent.creator_coverage,
      reference:comparison.reference_creator_coverage != null ? comparison.reference_creator_coverage : legacyReference.creator_coverage,
      delta:comparison.creator_coverage_delta != null ? comparison.creator_coverage_delta : metrics.creator_coverage_delta,
      ratio:comparison.coverage_ratio != null ? comparison.coverage_ratio : metrics.coverage_ratio,
      ratioState:typeof comparison.coverage_ratio_state === "string" ? comparison.coverage_ratio_state : metrics.coverage_relation
    };
  }

  function patternQuality(record){
    var quality = isRecord(record) && isRecord(record.quality) ? record.quality : {};
    return {
      cleanSupportShare:quality.clean_support_share,
      visualEvidenceMode:quality.visual_evidence_mode,
      pendingMaturationExcluded:quality.pending_maturation_excluded
    };
  }

  function testNextState(card){
    if(!isRecord(card)) return {};
    var state = isRecord(card.state) ? card.state : {};
    return {
      momentum:typeof state.momentum === "string" ? state.momentum : (typeof card.state === "string" ? card.state : card.momentum_state),
      evidence:typeof state.evidence === "string" ? state.evidence : card.evidence_state,
      persistent:typeof state.persistent === "boolean" ? state.persistent : card.persistent,
      confidence:typeof state.confidence === "string" ? state.confidence : card.confidence,
      scope:typeof state.scope === "string" ? state.scope : card.scope
    };
  }

  function testNextCounts(card){
    var counts = isRecord(card) && isRecord(card.evidence_counts) ? card.evidence_counts : {};
    return { creators:counts.creators, reels:counts.reels, families:counts.families };
  }

  function patternIndex(feed){
    var index = Object.create(null);
    var records = feed && Array.isArray(feed.patterns) ? feed.patterns : [];
    records.forEach(function(record){
      var id = recordIdentifier(record);
      if(id && !index[id]) index[id] = record;
    });
    return index;
  }

  function resolveView(feed, viewName){
    var views = feed && isRecord(feed.views) ? feed.views : {};
    var ids = Array.isArray(views[viewName]) ? views[viewName] : [];
    var index = patternIndex(feed);
    return ids.map(function(id){ return typeof id === "string" ? index[id] : null; }).filter(Boolean);
  }

  function resolveCollecting(feed){
    var ids = feed && Array.isArray(feed.collecting_evidence) ? feed.collecting_evidence : [];
    var index = patternIndex(feed);
    return ids.map(function(id){ return typeof id === "string" ? index[id] : null; }).filter(Boolean);
  }

  function confirmedTestNext(feed, nowValue){
    var status = feedStatus(feed, nowValue);
    if(status.stale) return [];
    var confirmed = typeof feed.last_confirmed_snapshot === "string" ? feed.last_confirmed_snapshot : "";
    if(!confirmed) return [];
    var cards = Array.isArray(feed.test_next) ? feed.test_next : [];
    return cards.filter(function(card){
      return isRecord(card) && card.snapshot_date === confirmed;
    });
  }

  function safeHttp(value){
    if(typeof value !== "string") return null;
    try{
      var parsed = new URL(value);
      return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : null;
    }catch(_err){
      return null;
    }
  }

  // A reference to a library card is only ever a plain relative path inside
  // the workspace. Anything with a drive letter, a leading slash, a step up a
  // level, a control character, or a non-markdown ending is rejected outright.
  function safeCardPath(value){
    if(typeof value !== "string" || !value || value.length > 800) return null;
    if(value.indexOf("\\") !== -1 || /[\u0000-\u001f]/.test(value)) return null;
    var marker = "/library/";
    if(value.charAt(0) === "/" && value.indexOf(marker) !== -1){
      value = "library/" + value.slice(value.indexOf(marker) + marker.length);
    }
    if(value.charAt(0) === "/") return null;
    var parts = value.split("/");
    if(parts.some(function(part){ return !part || part === "." || part === ".."; })) return null;
    if(!/\.md$/i.test(value)) return null;
    return value;
  }

  function cardUrlForPath(value){
    var safe = safeCardPath(value);
    return safe ? "api/card?path=" + encodeURIComponent(safe) : null;
  }

  return {
    STALE_AFTER_HOURS:STALE_AFTER_HOURS,
    timestampMs:timestampMs,
    feedStatus:feedStatus,
    recordIdentifier:recordIdentifier,
    patternLabel:patternLabel,
    patternCounts:patternCounts,
    patternComparison:patternComparison,
    patternQuality:patternQuality,
    testNextState:testNextState,
    testNextCounts:testNextCounts,
    patternIndex:patternIndex,
    resolveView:resolveView,
    resolveCollecting:resolveCollecting,
    confirmedTestNext:confirmedTestNext,
    safeHttp:safeHttp,
    safeCardPath:safeCardPath,
    cardUrlForPath:cardUrlForPath
  };
});
