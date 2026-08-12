/*
  Molosoc — "Why moisturizer alone doesn't fix it" orbit scroll drawer
  (Pillar 1 — Cracked Heels).

  The molosoc-3d.glb model keeps rotating the entire time (model-viewer's
  own auto-rotate attribute — independent of scroll, never touched by this
  script). As the visitor scrolls through the pinned section, the model
  fades toward ~25% opacity and gently blurs while a glass drawer — heading,
  copy, and the three "routine breaks down" cards — slides up from below
  and settles over it. See .claude/skills/orbit-scroll-drawer/SKILL.md §3-5
  for the pattern this implements.

  Plain scroll listener (not GSAP) per the skill's own reference
  implementation — this section doesn't need scroll-scrubbed easing beyond
  a direct progress->custom-property mapping, so it doesn't pull GSAP's
  pinning machinery into a section that's already pinned via CSS
  `position: sticky` (see pillar1.css's .molosoc-mechanism-pin).

  Progressive enhancement: no-JS/reduced-motion/CDN-failure all render the
  drawer already settled (opacity 1, no offset) over a full-opacity,
  unblurred, still-rotating model — see pillar1.css's defaults.
*/
(function () {
  "use strict";

  var prefersReduced = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  if (prefersReduced) return;

  if (window.innerWidth <= 760) return;

  var section = document.querySelector(".molosoc-mechanism-section");
  var stage = section && section.querySelector(".molosoc-mechanism-stage");
  var drawer = section && section.querySelector(".molosoc-mechanism-drawer");
  if (!section || !stage || !drawer) return;

  function clamp01(n) {
    return Math.max(0, Math.min(1, n));
  }

  function getProgress() {
    var rect = section.getBoundingClientRect();
    var total = section.offsetHeight - window.innerHeight;
    if (total <= 0) return 1;
    return clamp01(-rect.top / total);
  }

  var ticking = false;
  function update() {
    ticking = false;
    var p = getProgress();

    // Never fully invisible/paused — the model keeps spinning faintly
    // through the glass the whole time (skill §3), floored at ~25% opacity.
    stage.style.setProperty("--mech-opacity", (1 - p * 0.75).toFixed(3));
    stage.style.setProperty("--mech-blur", (p * 10).toFixed(2) + "px");

    // Drawer physically travels up from off-screen (40px below its resting
    // spot, fully transparent) to settled — a genuine slide-in tied to the
    // same progress number that drives the stage, so they never drift out
    // of sync.
    drawer.style.setProperty("--drawer-opacity", p.toFixed(3));
    drawer.style.setProperty("--drawer-offset", ((1 - p) * 40).toFixed(2) + "px");
  }

  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(update);
      ticking = true;
    }
  }

  // Drawer starts parked off/below before the first scroll tick runs.
  drawer.style.setProperty("--drawer-opacity", "0");
  drawer.style.setProperty("--drawer-offset", "40px");

  window.addEventListener("scroll", onScroll, { passive: true });
  update();
})();
