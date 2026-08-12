/*
  Molosoc — "Who this is for" editorial feature reveal (category page).

  Image A (hero_collection_03_relaxing-scaled.jpg) sits static over Image B
  (molosoc_pedicure_relaxing.jpg) in the exact same crop. GSAP ScrollTrigger
  pins the stage for extra scroll and grows a plain circular mask-image hole
  from the frame's own center — a camera-iris reveal, never a distorted/
  organic edge — showing Image B underneath. Once open, the three persona
  cards stagger in one at a time, each starting small and centered on the
  stage, then traveling out to its real, hand-placed resting position.

  Same mechanics as assets/js/topics-portal.js (that file's card-entrance
  approach is reused near-verbatim here) plus the image-reveal half of the
  pattern, which topics-portal.js's single-photo version doesn't need.

  Progressive enhancement: no-JS/reduced-motion/CDN-failure all render the
  exact same finished state — Image A hidden, Image B as the plain
  background, every card already at its final position (see category.css).
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

  var stage = document.querySelector(".molosoc-who-section__stage");
  var imageA = stage && stage.querySelector(".molosoc-who-section__bg--a");
  var cards = stage
    ? Array.prototype.slice.call(stage.querySelectorAll(".molosoc-who-card"))
    : [];
  if (!stage || !imageA || !cards.length) return;

  gsap.registerPlugin(ScrollTrigger);

  // --- Mask reveal ---------------------------------------------------------
  // ~70vmax comfortably covers any real viewport's diagonal from dead
  // center without overshooting (overshooting compresses the visually-
  // interesting growth into too little scroll distance).
  var MAX_RADIUS_VMAX = 70;
  // Image A holds flat/static for the first stretch of the pinned scroll
  // (no reveal motion at all) before the mask starts opening — a deliberate
  // pause so the "before" photo actually reads as a resting beat, not an
  // opening that begins the instant the pin engages.
  var REVEAL_START = 0.15;
  var REVEAL_END = 0.55;
  var HIDE_AT = 0.9; // measured against the reveal's own local progress
  var hidden = false;

  gsap.set(imageA, { "--who-hole": "0vmax" });

  // --- Card entrances: measure once, before any transform is applied -------
  // Each card's CSS already places it at its real, final resting spot
  // (category.css) — read that now, work out the offset back to the
  // stage's own center, then park the card there (small, invisible) until
  // its threshold plays the tween that returns it home.
  var stageRect = stage.getBoundingClientRect();
  var centerX = stageRect.width / 2;
  var centerY = stageRect.height / 2;
  var START_SCALE = 0.15;
  var ENTRANCE_DURATION = 0.7;
  var ENTRANCE_EASE = "power2.out";

  // Hover lift (2-4px) — has to go through GSAP too, not a CSS :hover, for
  // the same reason topics-portal.js does this (see that file's comment):
  // GSAP's CSSPlugin writes translate/scale as inline styles on any element
  // it tweens x/y/scale on, and an inline style always outranks a CSS class
  // rule for that property, hover or not.
  var HOVER_LIFT_Y = -3;
  var HOVER_DURATION = 0.25;

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

  // Cards start emerging once the mask is ~35-40% open (well before Image A
  // finishes revealing Image B), then stagger in evenly up to CARD_END.
  var CARD_START = REVEAL_START + (REVEAL_END - REVEAL_START) * 0.4;
  var CARD_END = 0.85;
  var triggered = cards.map(function () {
    return false;
  });
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
        "--who-hole",
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
