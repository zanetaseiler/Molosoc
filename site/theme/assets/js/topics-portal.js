/*
  Molosoc — "Foot care, topic by topic": one pinned, single-screen sequence.

  Per explicit request, the whole beat happens in this exact order, inside
  one fixed 100vh stage (.molosoc-topics__stage), not down a tall page:
    1. Image 1 (person sleeping) shows first, static.
    2. A scroll later, a circular opening (mask-image, center-out) reveals
       Image 2 underneath — scale/position of both images untouched, no
       zoom/parallax/fade, just the mask's radius growing.
    3. Image 2 completely replaces Image 1 (removed outright, not just
       faded) once the opening is far enough along.
    4. Image 2 is cropped to the exact same box as Image 1 (see
       .molosoc-topics__bg in homepage.css: both are inset:0 inside the
       same 100vh stage) — never its own, taller, full height.
    5. Once the portal is roughly 35-45% open, cards start emerging —
       each begins very small, centered on the portal's own center, and
       travels smoothly out to its final position, arriving one at a time
       with a slight stagger, then holding still.

  GSAP ScrollTrigger pins the stage for two extra viewport-heights of
  scroll and scrubs a single progress value (0-1) across that whole
  range — this part is completely unchanged: the portal reveal's own
  pacing (PORTAL_END, HIDE_AT, MAX_RADIUS_VMAX, the pin distance itself)
  is identical to before. Only CARD_START/CARD_END moved earlier, so the
  cards' own entrances now begin overlapping the portal's still-open
  circle instead of waiting for it to finish.

  Each card's entrance is a real GSAP tween (eased, time-based — not a
  linear scroll-scrub), so it can travel smoothly from a computed
  "starting point" back to wherever it already sits in the layout
  (homepage.css positions every card at its actual final resting spot;
  this script measures that position once at start-up, before any
  transform is applied, then works out how far "the stage's center" is
  from it). ScrollTrigger's progress crossing each card's own threshold
  just plays/reverses that tween — the motion itself is GSAP's own easing,
  which is what makes it read as "smooth arrival" rather than tied 1:1 to
  scroll speed. Reversible on scroll-up, matching every other scroll-
  linked effect on this site; settles and stays once played forward.

  Progressive enhancement: CSS default for --portal-hole is already a
  fully-open radius, .molosoc-topics__bg--one is hidden outright and every
  card already sits at its final, untransformed position under
  prefers-reduced-motion (see homepage.css) — so no-JS/reduced-motion
  always renders the finished, static state, still confined to the one
  100vh stage. Below the site's 760px card-stacking breakpoint this script
  steps aside entirely and homepage.css's own mobile fallback (plain
  stacked cards under a static Image 2) takes over instead of pinning a
  cramped viewport.
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
  var imageOne = stage && stage.querySelector(".molosoc-topics__bg--one");
  var cards = stage
    ? Array.prototype.slice.call(
        stage.querySelectorAll(".molosoc-feature-card")
      )
    : [];
  if (!stage || !imageOne || !cards.length) return;

  gsap.registerPlugin(ScrollTrigger);

  // --- Portal reveal — unchanged from before ---------------------------
  // A circle only needs to reach roughly half the viewport's diagonal
  // (~50-58vmax for most real aspect ratios) to cover every corner from
  // dead center — 70vmax gives that a safe margin while still growing
  // visibly across the whole portal segment below.
  var MAX_RADIUS_VMAX = 70;

  // The pinned scroll range splits in half: first half is the portal
  // reveal (0 -> PORTAL_END). HIDE_AT is measured against the portal's
  // OWN local progress (0-1 within its half), matching the original
  // "~90% through the reveal" cutoff — by then --portal-hole already
  // exceeds any real viewport's diagonal, so removing Image 1 is
  // invisible in practice.
  var PORTAL_END = 0.5;
  var HIDE_AT = 0.9;
  var hidden = false;

  gsap.set(imageOne, { "--portal-hole": "0vmax" });

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

  // Cards start emerging once the portal is ~35-45% open (portalProgress
  // ~0.4), well before Image 1 finishes revealing Image 2 — then stagger
  // in one at a time, evenly, up to CARD_END.
  var CARD_START = PORTAL_END * 0.4; // portalProgress 0.4
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
    end: "+=" + window.innerHeight * 2,
    pin: true,
    scrub: true,
    onUpdate: function (self) {
      var portalProgress = Math.min(self.progress / PORTAL_END, 1);

      imageOne.style.setProperty(
        "--portal-hole",
        portalProgress * MAX_RADIUS_VMAX + "vmax"
      );

      if (portalProgress >= HIDE_AT && !hidden) {
        imageOne.style.display = "none";
        hidden = true;
      } else if (portalProgress < HIDE_AT && hidden) {
        imageOne.style.display = "";
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

/*
  ScrollTrigger position refresh — deliberately OUTSIDE the IIFE above and
  not gated by its early returns (reduced-motion / no-GSAP / mobile), since
  merge-transition.js and proof-scale.js also register ScrollTriggers that
  need this regardless of whether THIS section's own pin set up.

  window.load alone isn't enough: it only waits for eagerly-loading
  resources. Most images on this page use loading="lazy" (deliberate, for
  performance) — a lazy image that hasn't scrolled near the viewport yet is
  never part of window.load's pending set, so it finishes loading LATER,
  growing page height and leaving every pin's cached start/end stale
  relative to the real, final layout. That produced the "plays once
  correctly, then the same section appears to repeat/jump further down,
  flickers on scroll-up" symptom: pins were engaging against pre-lazy-load
  geometry.

  NOTE: this used to be injected via wp_add_inline_script() in functions.php
  instead of living here as real file content — moved after discovering the
  site's WPO Minify plugin combines/minifies enqueued script FILES into a
  bundle correctly, but silently drops inline scripts attached to a
  bundled handle. Real file content survives that pipeline; inline scripts
  don't.
*/
(function () {
  "use strict";

  function molosocRefreshScrollTrigger() {
    if (window.ScrollTrigger) ScrollTrigger.refresh();
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
