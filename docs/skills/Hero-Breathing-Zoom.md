# Hero Breathing Zoom

A photo inside a fixed, `overflow: hidden` frame continuously and slowly
scales between 100% and roughly 106%, easing in and back out forever. The
frame itself never moves or resizes — only the image inside it grows and
shrinks, staying centered, so the effect reads as the photo gently
breathing rather than zooming toward the viewer or panning.

Extracted from Molosoc's own homepage hero
(`site/theme/assets/css/homepage.css`, `.molosoc-hero-breathe`) — this is
the canonical source; treat other implementations as variations on it.
Also live on the Product page's "Real results, no filters" cards
(`site/theme/assets/css/product.css`, `.molosoc-product-proof__media`).

---

## 1. The animation itself

Pure CSS `@keyframes`, no JS required to run once started:

```css
@keyframes molosoc-hero-breathe {
  from { transform: scale(1); }
  to   { transform: scale(1.06); }
}

.hero-photo-frame img {
  animation: molosoc-hero-breathe 9s ease-in-out infinite alternate;
}
```

- **Duration matters**: 9s per leg (18s full up-and-back cycle) is the
  calibrated value. Faster reads as nervous/gimmicky; much slower stops
  registering as motion at all.
- **Plain `ease-in-out`, not the site's snappier reveal easing** (e.g. a
  front-loaded curve tuned for ~400-900ms reveals). A front-loaded curve
  visibly finishes early and then sits motionless for the rest of a long
  duration like this — confirmed by testing on the source homepage build.
  Use a symmetric ease-in-out so `alternate` reverses smoothly instead of
  snapping at each turnaround.
- **`alternate`, not `infinite` with a reset** — the point is a continuous
  in-and-out breathing motion, not a zoom-then-jump-back-to-start loop.
- **The frame must clip.** The image's parent needs `overflow: hidden`
  (and typically `border-radius` if the design calls for rounded photo
  corners) so the scaled-up image never spills past its box.

## 2. Progressive enhancement — start on load, not before paint

The source implementation gates the animation behind an `.is-visible`
class added on load (via `requestAnimationFrame`, not a hard requirement —
an `IntersectionObserver` firing when the frame scrolls into view works
just as well, and is usually the better choice when the photo sits below
the fold):

```css
.hero-photo-frame img {
  transform: scale(1); /* explicit resting state before JS runs */
}
.hero-photo-frame.is-visible img {
  animation: molosoc-hero-breathe 9s ease-in-out infinite alternate;
}
```

```js
requestAnimationFrame(function () {
  document.querySelector(".hero-photo-frame").classList.add("is-visible");
});
```

This JS gating is optional, not load-bearing — for photos that are
already below the fold when the page loads (so the animation start is
never actually visible to the user), a plain unconditional
`animation: ...` with no class-gating at all is simpler and behaves
identically in practice. Reach for the JS version specifically when the
photo is above the fold and you want to guarantee the animation begins
from a clean, deliberate first frame rather than mid-transition on a
slow-loading page.

## 3. Accessibility

Always pair with a `prefers-reduced-motion` override that freezes the
image at rest:

```css
@media (prefers-reduced-motion: reduce) {
  .hero-photo-frame img {
    animation: none;
    transform: none;
  }
}
```

## 4. Where this does and doesn't fit

- **Fits**: hero photos, feature/proof photos the design wants to feel
  "alive" without literal motion — anywhere a single photo is the visual
  anchor of a moment.
- **Doesn't fit**: images already carrying their own scroll-driven or
  hover-driven motion (don't stack this on top of a hover-zoom — pick
  one). Also not a substitute for entrance reveals (fade-in, slide-up) —
  this is ambient/idle motion for a photo that's already fully visible,
  not how it arrives on screen.
