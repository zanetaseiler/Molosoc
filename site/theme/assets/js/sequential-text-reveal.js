/*
  Molosoc — scroll-triggered text-column entrance (shared).

  Applies independently to every ".molosoc-sequential-stage" on the page: a
  photo (if the instance has one) stays fixed/static in place — never
  selected or touched by this script — while its stack of
  ".molosoc-sequential-entrance--text" items slides in TOGETHER, as one
  unit, from the direction named in that stage's own [data-slide-direction]
  ("left", "right", "up", or "down") when the stage scrolls into view. One
  content section = one reveal event: reaching the section reveals the
  whole text column at once, and no paragraph ever needs its own extra
  scroll. A fixed image isn't required — the same entrance works for a
  plain stat grid with no photo at all (the "real cost" section, "up").

  This deliberately replaced the earlier pinned, scroll-gated variant
  (each item gated to its own scroll-progress threshold inside a pinned
  stage — see docs/skills/Fixed-Image-Sequential-Text-Reveal.md for that
  pattern's mechanics): revealing paragraphs one-per-scroll-step made
  visitors micro-scroll through every section and read as if the section
  had ended after its first item. No pin, no scrub — the stage scrolls
  normally and the column's entrance plays once on arrival.

  Progressive enhancement: no-JS/reduced-motion/CDN-failure all render the
  same finished state — every text item already at full opacity/no
  transform (see category.css). The photo needs no fallback since it never
  animates in the first place.
*/
(function () {
  "use strict";

  var prefersReduced = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  if (prefersReduced) return;

  if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
    return;
  }

  if (window.innerWidth <= 760) return;

  var stages = Array.prototype.slice.call(
    document.querySelectorAll(".molosoc-sequential-stage")
  );
  if (!stages.length) return;

  gsap.registerPlugin(ScrollTrigger);

  var SLIDE_DISTANCE = 70; // px
  var DURATION = 0.7;
  var EASE = "power2.out";

  stages.forEach(function (stage) {
    var textItems = Array.prototype.slice.call(
      stage.querySelectorAll(".molosoc-sequential-entrance--text")
    );
    if (!textItems.length) return;

    // Direction names the side the column starts offset toward, then eases
    // back to its resting position from: "left"/"right" move along x,
    // "up"/"down" move along y ("up" = starts lower, rises upward into
    // place — reads as "coming up from the bottom"). Defaults to "right".
    var direction = stage.getAttribute("data-slide-direction") || "right";
    var startProps =
      direction === "left"
        ? { x: -SLIDE_DISTANCE, opacity: 0 }
        : direction === "up"
        ? { y: SLIDE_DISTANCE, opacity: 0 }
        : direction === "down"
        ? { y: -SLIDE_DISTANCE, opacity: 0 }
        : { x: SLIDE_DISTANCE, opacity: 0 }; // "right" (default)

    gsap.set(textItems, startProps);

    // One tween, every item together, stagger 0 — no per-paragraph delay.
    // once:true (play on first arrival, never re-hide) also covers loading
    // mid-page past the stage: ScrollTrigger's initial refresh sees the
    // start already crossed and plays the entrance immediately.
    gsap.to(textItems, {
      x: 0,
      y: 0,
      opacity: 1,
      duration: DURATION,
      ease: EASE,
      scrollTrigger: {
        trigger: stage,
        start: "top 60%",
        once: true,
      },
    });
  });
})();
