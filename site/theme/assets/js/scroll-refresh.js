/*
  Molosoc — ScrollTrigger position refresh, shared by homepage-preview.html
  and front-page.php (real file content, not wp_add_inline_script: the
  site's WPO Minify plugin combines/minifies enqueued script FILES into a
  bundle correctly, but silently drops inline scripts attached to a bundled
  handle — real file content survives that pipeline, inline scripts don't).

  window.load alone isn't enough: it only waits for eagerly-loading
  resources. Most images on this page use loading="lazy" (deliberate, for
  performance) — a lazy image that hasn't scrolled near the viewport yet is
  never part of window.load's pending set, so it finishes loading LATER,
  growing page height and leaving every pin's cached start/end (and, for a
  released pin, its unpin compensating transform) stale relative to the
  real, final layout — producing a visible jump/"repeat" right where a
  pinned section releases. Refreshing once on window.load, then again once
  every currently-pending image finishes (plus a standing listener for any
  future image load), keeps every ScrollTrigger's pin matched to the real,
  settled DOM regardless of script order or image load timing.

  The future-load listener is debounced (rAF-coalesced) AND waits for no
  pin to be actively engaged before it actually calls refresh(): confirmed
  directly that ScrollTrigger.refresh() firing while a pinned section is
  mid-scrub can knock that pin's own progress to 1 (fully released) as a
  side effect, even when nothing about the page's real height changed —
  refresh briefly reverts every pin to its unpinned state to remeasure true
  positions, and an in-progress pin doesn't always survive that round-trip
  cleanly. Once knocked to progress 1, the section renders via its
  "already unpinned" settled transform while still scrolled to a mid-pin
  position, which reads as the tile/background layer disappearing or
  landing in the wrong stacking position relative to whatever comes next.
  Deferring the refresh (retried every animation frame) until every pin
  reports !isActive avoids ever interrupting one mid-scrub.
*/
(function () {
  "use strict";

  var refreshQueued = false;
  // Height of the document as of the last completed refresh. Every image on
  // these pages carries width/height attributes, so most image loads don't
  // change layout at all — but the standing per-image listener below still
  // fired a full ScrollTrigger.refresh() for each one. On a COLD first visit
  // that meant one forced re-layout of the whole 13k-px page (pins reverted
  // and re-applied) per arriving image, repeatedly, exactly while a
  // first-time visitor is trying to scroll — warm repeat visits never fire
  // any of them, which is why the resulting jank was only ever reported by
  // first-time visitors and never reproducible afterwards. Skipping the
  // refresh whenever the document height is unchanged keeps the correctness
  // net (a load that DOES grow the page still refreshes) while making the
  // no-op case actually a no-op.
  var lastRefreshedHeight = null;
  function molosocRefreshScrollTrigger() {
    if (refreshQueued || !window.ScrollTrigger) return;
    refreshQueued = true;
    (function tryRefresh() {
      var anyPinActive = ScrollTrigger.getAll().some(function (st) {
        return st.pin && st.isActive;
      });
      if (anyPinActive) {
        requestAnimationFrame(tryRefresh);
        return;
      }
      refreshQueued = false;
      var height = document.documentElement.scrollHeight;
      if (height === lastRefreshedHeight) return;
      lastRefreshedHeight = height;
      ScrollTrigger.refresh();
    })();
  }

  window.addEventListener("load", function () {
    molosocRefreshScrollTrigger();

    var pending = [];
    document.querySelectorAll("img").forEach(function (img) {
      if (!img.complete) {
        pending.push(
          new Promise(function (resolve) {
            img.addEventListener("load", resolve, { once: true });
            img.addEventListener("error", resolve, { once: true });
          })
        );
      }
      // Safety net — fires on every future image load, including ones not
      // yet in the DOM/pending set at window.load time.
      img.addEventListener("load", molosocRefreshScrollTrigger);
    });

    if (pending.length) {
      Promise.all(pending).then(molosocRefreshScrollTrigger);
    }
  });
})();
