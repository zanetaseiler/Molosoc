/*
  Molosoc — "Real results" proof image: scroll-linked scale only.

  Per explicit request: only the four-corner results photo under "Three
  months in, no filters" animates here — heading, spacing, image
  proportions, layout, and every other section are untouched. It starts
  very small and centered, scales smoothly up to its normal size/position
  as the section scrolls into view, then holds static once fully scaled.

  Scale only, transform-origin centered (see .molosoc-proof__media--scale
  in homepage.css) — the image never shifts off-center at any point.

  Genuinely scroll-LINKED, not a one-time reveal: GSAP + ScrollTrigger
  scrub ties --proof-scale directly to scroll position (reverses smoothly
  if the user scrolls back up), unlike the site's toggled .molosoc-reveal
  fade-ins elsewhere. That's why this image deliberately does NOT carry
  .molosoc-reveal in the markup — the two would otherwise animate
  opacity/transform against each other.

  Progressive enhancement: CSS default for --proof-scale is 1, so
  no-JS / reduced-motion always renders the image at final size, fully
  static. This script only pulls it down to a small starting scale once it
  has confirmed GSAP + ScrollTrigger are actually available to scrub it
  back up — same pattern as merge-transition.js.
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

  var media = document.querySelector(".molosoc-proof__media--scale");
  if (!media) return;

  gsap.registerPlugin(ScrollTrigger);

  gsap.fromTo(
    media,
    { "--proof-scale": 0.15 },
    {
      "--proof-scale": 1,
      ease: "none",
      scrollTrigger: {
        trigger: media,
        start: "top 90%",
        end: "top 40%",
        scrub: true,
      },
    }
  );
})();
