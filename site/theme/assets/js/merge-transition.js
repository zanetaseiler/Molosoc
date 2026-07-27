/*
  Molosoc — "merge and emerge" scroll-pinned sequence for the
  ".molosoc-merge-section" ("The cream you own, finally finished").
  Reference: docs/references/reference-1.1/1.2/1.3.png.

  This is the one section on the site that uses an animation library (GSAP +
  ScrollTrigger, loaded via CDN in the page) rather than motion.js's vanilla
  IntersectionObserver approach — a proper pin+scrub sequence needs it. See
  docs/molosoc-animation-specification.md for the motion rules this follows
  (transform/opacity only, no bounce/spin, respects prefers-reduced-motion).

  Progressive enhancement: the section's HTML/CSS alone already renders the
  tiles flush (= one continuous photo) with all text visible — that is the
  reduced-motion AND the no-JS/CDN-failure fallback. This script only ever
  pulls the tiles apart into the "before merge" state and text into its
  hidden state once it has confirmed GSAP loaded and motion is allowed, so a
  failure anywhere above never leaves the section stuck half-animated.
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

  var section = document.querySelector(".molosoc-merge-section");
  if (!section) return;

  var tileLeft = section.querySelector(".molosoc-merge__tile--left");
  var tileRight = section.querySelector(".molosoc-merge__tile--right");
  var mergeGroup = section.querySelector(".molosoc-merge__group");
  var scrim = section.querySelector(".molosoc-section__scrim");
  var textEls = section.querySelectorAll(".molosoc-merge__text");

  if (!tileLeft || !tileRight || !mergeGroup || !scrim || !textEls.length) {
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  // "Before merge" starting state — matches docs/references/reference-1.1.png:
  // two tiles pulled apart with a gap, visibly smaller than full scale so the
  // merge phase reads as both closing the gap AND growing into place.
  gsap.set(tileLeft, { xPercent: -12, scale: 0.7, transformOrigin: "right center" });
  gsap.set(tileRight, { xPercent: 12, scale: 0.7, transformOrigin: "left center" });
  // Overlay stays fully transparent through merge + settle — it only appears
  // together with the text, not before it.
  gsap.set(scrim, { opacity: 0 });
  gsap.set(textEls, { opacity: 0, scale: 0.92, y: 24 });

  var tl = gsap.timeline({
    scrollTrigger: {
      trigger: section,
      start: "top top",
      end: "+=150%",
      pin: true,
      scrub: 1,
      anticipatePin: 1,
    },
  });

  // 0 -> 0.4: MERGE — tiles grow from 70% and close the gap, aligning into one image.
  tl.to(tileLeft, { xPercent: 0, scale: 1, duration: 0.4, ease: "power2.inOut" }, 0)
    .to(tileRight, { xPercent: 0, scale: 1, duration: 0.4, ease: "power2.inOut" }, 0)
    // 0.4 -> 0.6: SETTLE — merged image pulls back slightly. Overlay is NOT part
    // of this phase (see below) — it stays at 0 through settle too.
    .to(mergeGroup, { scale: 0.98, duration: 0.2, ease: "power1.out" }, 0.4)
    // 0.6 -> 1.0: TEXT EMERGENCE — overlay and text fade in together, headline +
    // pillars staggered. NOTE: a staggered tween's effective span is
    // duration + (targets-1)*stagger, not just `duration` — with 6 text targets
    // and stagger 0.06 that's +0.3, which would otherwise push this phase past
    // 1.0 and skew every percentage above. Shrinking textEls' duration to 0.1
    // keeps the whole staggered group landing exactly in the 0.6 -> 1.0 window.
    .to(scrim, { opacity: 1, duration: 0.4, ease: "power2.out" }, 0.6)
    .to(
      textEls,
      { opacity: 1, scale: 1, y: 0, duration: 0.1, stagger: 0.06, ease: "power2.out" },
      0.6
    );
})();
