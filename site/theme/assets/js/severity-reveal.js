/*
  Molosoc — "When cracked heels go from dry to painful" editorial feature
  reveal (Pillar 1 — Cracked Heels).

  Image A (pillar1_03_sandals.jpg) sits static over Image B
  (pillar3_03_texture.jpg) in the exact same crop. GSAP ScrollTrigger pins
  the stage for extra scroll and grows a plain circular mask-image hole
  from the frame's own center — a camera-iris reveal, never a distorted/
  organic edge — showing Image B underneath. Once open, the three severity
  cards (painful deep cracks, severe cracks, why moisturizing more stops
  working) stagger in one at a time, each starting small and centered on
  the stage, then traveling out to its real, hand-placed resting position.

  Same mechanics as assets/js/who-reveal.js (category page) — see
  ~/.claude/skills/editorial-feature-reveal for the full pattern — kept as
  its own file/selector set since this is a different stage on a different
  page, not a reuse of that page's own class names.

  Progressive enhancement: no-JS/reduced-motion/CDN-failure all render the
  exact same finished state — Image A hidden, Image B as the plain
  background, every card already at its final position (see pillar1.css).
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

  var stage = document.querySelector(".molosoc-severity-section__stage");
  var imageA = stage && stage.querySelector(".molosoc-severity-section__bg--a");
  var cards = stage
    ? Array.prototype.slice.call(stage.querySelectorAll(".molosoc-severity-card"))
    : [];
  if (!stage || !imageA || !cards.length) return;

  gsap.registerPlugin(ScrollTrigger);

  // --- Mask reveal ---------------------------------------------------------
  var MAX_RADIUS_VMAX = 70;
  var REVEAL_START = 0.15;
  var REVEAL_END = 0.55;
  var HIDE_AT = 0.9;
  var hidden = false;

  gsap.set(imageA, { "--severity-hole": "0vmax" });

  // --- Card entrances: measure once, before any transform is applied -------
  var stageRect = stage.getBoundingClientRect();
  var centerX = stageRect.width / 2;
  var centerY = stageRect.height / 2;
  var START_SCALE = 0.15;
  var ENTRANCE_DURATION = 0.7;
  var ENTRANCE_EASE = "power2.out";
  var HOVER_LIFT_Y = -3;
  var HOVER_DURATION = 0.25;

  var triggered = cards.map(function () {
    return false;
  });

  var entrances = cards.map(function (card, i) {
    var r = card.getBoundingClientRect();
    var cardCenterX = r.left - stageRect.left + r.width / 2;
    var cardCenterY = r.top - stageRect.top + r.height / 2;
    var fromX = centerX - cardCenterX;
    var fromY = centerY - cardCenterY;

    gsap.set(card, { x: fromX, y: fromY, scale: START_SCALE, opacity: 0 });

    card.addEventListener("mouseenter", function () {
      if (!triggered[i]) return;
      gsap.to(card, { y: HOVER_LIFT_Y, duration: HOVER_DURATION, ease: "power2.out" });
    });
    card.addEventListener("mouseleave", function () {
      if (!triggered[i]) return;
      gsap.to(card, { y: 0, duration: HOVER_DURATION, ease: "power2.out" });
    });

    return gsap.timeline({ paused: true }).to(card, {
      x: 0,
      y: 0,
      scale: 1,
      opacity: 1,
      duration: ENTRANCE_DURATION,
      ease: ENTRANCE_EASE,
    });
  });

  var CARD_START = REVEAL_START + (REVEAL_END - REVEAL_START) * 0.4;
  var CARD_END = 0.85;
  var cardThresholds = cards.map(function (_, i) {
    return cards.length === 1
      ? CARD_START
      : CARD_START + (i * (CARD_END - CARD_START)) / (cards.length - 1);
  });

  // --- One ScrollTrigger drives the whole sequence --------------------------
  ScrollTrigger.create({
    trigger: stage,
    start: "top top",
    end: "+=" + window.innerHeight * 1.5,
    pin: true,
    scrub: true,
    onUpdate: function (self) {
      var revealProgress = Math.max(
        0,
        Math.min((self.progress - REVEAL_START) / (REVEAL_END - REVEAL_START), 1)
      );

      imageA.style.setProperty(
        "--severity-hole",
        revealProgress * MAX_RADIUS_VMAX + "vmax"
      );

      if (revealProgress >= HIDE_AT && !hidden) {
        imageA.style.display = "none";
        hidden = true;
      } else if (revealProgress < HIDE_AT && hidden) {
        imageA.style.display = "";
        hidden = false;
      }

      entrances.forEach(function (tl, i) {
        var shouldShow = self.progress >= cardThresholds[i];
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
})();
