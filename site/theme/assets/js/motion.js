/*
  Molosoc — restrained motion layer.
  Rules from docs/molosoc-animation-specification.md:
    - opacity / translate / scale / blur / depth only — no bounce/elastic/spin
    - one primary reveal per section, not per element
    - respects prefers-reduced-motion (no observer attached at all if set)
    - lightweight: no animation library, IntersectionObserver + CSS transitions
*/
(function () {
  "use strict";

  var prefersReduced = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  if (prefersReduced) {
    document.querySelectorAll(".molosoc-reveal").forEach(function (el) {
      el.classList.add("is-visible");
    });
    return;
  }

  var revealObserver = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2, rootMargin: "0px 0px -10% 0px" }
  );

  document.querySelectorAll(".molosoc-reveal").forEach(function (el) {
    revealObserver.observe(el);
  });

  // Hero: one subtle parallax/scale cue on load, not scroll-linked (per spec:
  // "very subtle image reveal", not continuous parallax scrubbing on mobile).
  var hero = document.querySelector(".molosoc-hero");
  if (hero) {
    requestAnimationFrame(function () {
      hero.classList.add("is-visible");
    });
  }

  // Header contrast: only toggles a class, no animation of its own — keeps
  // the fixed logo readable over both light and dark hero imagery.
  var header = document.querySelector(".molosoc-home-header");
  if (header && "IntersectionObserver" in window) {
    var heroSentinel = document.querySelector(".molosoc-hero");
    if (heroSentinel) {
      var headerObserver = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            header.classList.toggle("is-past-hero", !entry.isIntersecting);
          });
        },
        { threshold: 0 }
      );
      headerObserver.observe(heroSentinel);
    }
  }
})();
