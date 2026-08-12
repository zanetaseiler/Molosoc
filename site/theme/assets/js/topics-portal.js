/*
  Molosoc — "Foot care, topic by topic": one pinned, single-screen sequence.

  A single static photo fills the 100vh stage (.molosoc-topics__stage) — no
  second image, no circle/portal reveal. GSAP ScrollTrigger pins the stage
  for extra scroll and scrubs a single progress value (0-1) across that
  range, staggering the five feature cards in one at a time (thresholded,
  not looping): each begins very small, centered on the stage's own center,
  and travels smoothly out to its final position (homepage.css positions
  every card at its actual final resting spot; this script measures that
  position once at start-up, before any transform is applied, then works
  out how far "the stage's center" is from it).

  Each card's entrance is a real GSAP tween (eased, time-based — not a
  linear scroll-scrub), so it can travel smoothly from a computed
  "starting point" back to wherever it already sits in the layout.
  ScrollTrigger's progress crossing each card's own threshold just
  plays/reverses that tween — the motion itself is GSAP's own easing,
  which is what makes it read as "smooth arrival" rather than tied 1:1 to
  scroll speed. Reversible on scroll-up, matching every other scroll-
  linked effect on this site; settles and stays once played forward.

  Progressive enhancement: every card already sits at its final,
  untransformed position under prefers-reduced-motion (see homepage.css) —
  so no-JS/reduced-motion always renders the finished, static state,
  confined to the one 100vh stage. Below the site's 760px card-stacking
  breakpoint this script steps aside entirely and homepage.css's own
  mobile fallback (plain stacked cards under the static photo) takes over
  instead of pinning a cramped viewport.
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

  var stage = document.querySelector(".molosoc-topics__stage");
  var cards = stage
    ? Array.prototype.slice.call(
        stage.querySelectorAll(".molosoc-feature-card")
      )
    : [];
  if (!stage || !cards.length) return;

  gsap.registerPlugin(ScrollTrigger);

  // --- Card entrances: measure once, before any transform is applied ---
  // Each card's CSS already places it at its real, final resting spot
  // (homepage.css) — read that now, work out the offset back to the
  // stage's own center, then park the card there (small, invisible)
  // until its threshold plays the tween that returns it home.
  var stageRect = stage.getBoundingClientRect();
  var centerX = stageRect.width / 2;
  var centerY = stageRect.height / 2;
  var START_SCALE = 0.15;
  var ENTRANCE_DURATION = 0.7;
  var ENTRANCE_EASE = "power2.out";

  // Hover lift (2-4px, on top of the settled resting state). This has to
  // be driven by GSAP too, not a plain CSS `:hover` rule: GSAP's CSSPlugin
  // writes `translate`/`scale`/`rotate` as inline styles on every element
  // it tweens (normalizing them into the single `transform` matrix it also
  // sets) — an inline style always outranks a class-based CSS rule for
  // that same property, so a CSS `:hover { translate: ... }` on a
  // GSAP-managed element is silently overridden and never actually
  // applies. Letting GSAP own the hover offset too avoids fighting its own
  // inline styles. The box-shadow "deeper on hover" part is NOT touched by
  // GSAP at all, so that stays a plain CSS `:hover` transition
  // (homepage.css) — only the lift itself needs to go through GSAP.
  var HOVER_LIFT_Y = -3; // px — within the requested 2-4px range
  var HOVER_DURATION = 0.25;

  var entrances = cards.map(function (card, i) {
    var r = card.getBoundingClientRect();
    var cardCenterX = r.left - stageRect.left + r.width / 2;
    var cardCenterY = r.top - stageRect.top + r.height / 2;
    var fromX = centerX - cardCenterX;
    var fromY = centerY - cardCenterY;

    gsap.set(card, { x: fromX, y: fromY, scale: START_SCALE, opacity: 0 });

    card.addEventListener("mouseenter", function () {
      if (!triggered[i]) return; // don't lift a card before it has arrived
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

  // Cards stagger in one at a time, evenly, across the pinned scroll range.
  var CARD_START = 0.1;
  var CARD_END = 0.85;
  var triggered = cards.map(function () {
    return false;
  });

  var cardThresholds = cards.map(function (_, i) {
    return cards.length === 1
      ? CARD_START
      : CARD_START + (i * (CARD_END - CARD_START)) / (cards.length - 1);
  });

  ScrollTrigger.create({
    trigger: stage,
    start: "top top",
    end: "+=" + window.innerHeight * 1.5,
    pin: true,
    scrub: true,
    onUpdate: function (self) {
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
