/*
  Molosoc — sequential, scroll-gated text entrance (category page).

  Applies independently to every ".molosoc-sequential-stage" on the page: a
  photo (if the instance has one) stays fixed/static in place — never
  selected or touched by this script — while its stack of
  ".molosoc-sequential-entrance--text" items slides in one at a time from
  the direction named in that stage's own [data-slide-direction] ("left",
  "right", "up", or "down"), each gated to its own scroll-progress
  threshold. The first scroll into a stage already reveals its first item;
  continuing to scroll reveals each subsequent one. A fixed image isn't
  required — the same pinned/threshold mechanic works for a plain stat
  grid with no photo at all (see the "real cost" section, direction "up").

  This is the reusable "fixed image, sequential text reveal" pattern — see
  docs/skills/Fixed-Image-Sequential-Text-Reveal.md (project copy) or
  ~/.claude/skills/fixed-image-text-reveal (canonical/global) for the full
  mechanics, the two earlier variants that were tried and reverted before
  landing here, and the mistakes to avoid (an IntersectionObserver inside a
  pinned stage fires every item at once; giving the photo its own entrance
  reintroduces an edge-clipping bug on a rounded/overflow-hidden wrapper).

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
  var DURATION = 0.6;
  var EASE = "power2.out";
  var STEP_START = 0.12;
  var STEP_END = 0.9;

  stages.forEach(function (stage) {
    var textItems = Array.prototype.slice.call(
      stage.querySelectorAll(".molosoc-sequential-entrance--text")
    );
    if (!textItems.length) return;

    // Direction names the side each item starts offset toward, then eases
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

    var entrances = textItems.map(function (item) {
      return gsap.timeline({ paused: true }).to(item, {
        x: 0,
        y: 0,
        opacity: 1,
        duration: DURATION,
        ease: EASE,
      });
    });

    var triggered = entrances.map(function () {
      return false;
    });
    var thresholds = entrances.map(function (_, i) {
      return entrances.length === 1
        ? STEP_START
        : STEP_START + (i * (STEP_END - STEP_START)) / (entrances.length - 1);
    });

    ScrollTrigger.create({
      trigger: stage,
      start: "top top",
      end: "+=" + window.innerHeight * 1.5,
      pin: true,
      scrub: true,
      onUpdate: function (self) {
        entrances.forEach(function (tl, i) {
          var shouldShow = self.progress >= thresholds[i];
          if (shouldShow && !triggered[i]) {
            triggered[i] = true;
            tl.play();
          } else if (!shouldShow && triggered[i]) {
            triggered[i] = false;
            tl.reverse();
          }
        });
      },
    });
  });
})();
