---
name: orbit-scroll-drawer
description: Reusable scroll-driven hero pattern where a glossy 3D-looking rotating object (rings, an orb, or similar) animates continuously in the background, then on scroll fades toward transparent and blurs while a glass-panel content block — headline, description, and a row of static feature cards — slides up over it like a drawer. The rotating object keeps spinning faintly behind the glass the whole time; it never stops or gets removed. Use when a request describes a rotating 3D/chrome/glass background object that "becomes transparent" or fades as a new content block scrolls in on top of it, on a static HTML/CSS/JS site, a WordPress theme, or a React/Next.js app.
---

# Orbit Scroll Drawer

A pinned hero sequence: a continuously-rotating glossy object (rings around
a glowing core is the reference look, but any 3D-looking CSS/SVG object
works) sits behind everything from the start. It never stops animating.
As the user scrolls, it shrinks, blurs, and fades toward transparent while
a glass-panel drawer — headline, supporting copy, a CTA, and a row of
**static** (non-animated, no stagger) feature cards — slides up and settles
over it. Further scroll can pin/collapse that drawer and hand off to the
next section.

This pattern was authored directly from a set of reference screenshots of
a real product marketing site, not extracted from a prior build with its
own corrected mistakes — so treat the mechanics below as a solid starting
point, not battle-tested folklore. Verify the specific gotchas called out
in §8 on whatever project this gets grafted onto.

---

## 1. Before touching anything

1. **Detect the project type** — plain HTML/CSS/JS, a WordPress theme
   (`style.css` theme header, `functions.php`, template files), or a
   React/Next.js app (`package.json`, `app/`/`pages/` directory, component
   files). This pattern almost always gets added to an existing hero
   section, not built on a blank page.
2. **Find existing design tokens** (CSS custom properties, a
   `tailwind.config`, a theme object) and reuse them — background, ink,
   accent, radii, shadow tokens especially. Don't invent a parallel color
   system for this one section.
3. **Identify what the rotating object should actually be.** Default to a
   pure CSS/SVG look-alike (concentric rings + a radial-gradient "glowing
   core," see §2) — no external video/GIF asset, no 3D library dependency.
   If the project already has a specific 3D asset (a real GLB model, a
   Lottie file, a video loop) the person wants reused, that changes §2
   entirely — confirm before building a CSS look-alike nobody asked for.
4. **Preserve existing layout and content.** This grafts onto an existing
   hero + next-section pair; don't restructure surrounding sections or
   rewrite unrelated copy while implementing this.
5. **Default to local preview.** Verify in the project's existing local
   dev server/build. Don't deploy, push, or publish unless explicitly
   asked.

---

## 2. The rotating object (background layer)

Build it as layered SVG/CSS, not an image or video — it needs to keep
rendering crisply at any size and rotate forever without a decoded asset:

```html
<div class="orbit-stage">
  <svg class="orbit-rings" viewBox="0 0 600 600" aria-hidden="true">
    <circle class="ring ring--1" cx="300" cy="300" r="220" />
    <circle class="ring ring--2" cx="300" cy="300" r="170" />
    <circle class="ring ring--3" cx="300" cy="300" r="120" />
    <circle class="orbit-core" cx="300" cy="300" r="42" />
  </svg>
</div>
```

```css
.orbit-stage {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  /* this is the layer §3 fades/blurs — keep it isolated so filters don't
     leak onto siblings */
  isolation: isolate;
}

.orbit-rings { width: min(70vw, 640px); height: auto; }

.ring {
  fill: none;
  stroke: color-mix(in srgb, var(--accent, #b98cff) 60%, white);
  stroke-width: 1.5;
  opacity: 0.55;
  transform-origin: 300px 300px;
}
.ring--1 { animation: orbit-spin 40s linear infinite; }
.ring--2 { animation: orbit-spin 26s linear infinite reverse; }
.ring--3 { animation: orbit-spin 60s linear infinite; }

.orbit-core {
  fill: url(#orbit-core-gradient);
  animation: orbit-pulse 5s ease-in-out infinite;
}

@keyframes orbit-spin {
  to { transform: rotate(360deg); }
}
@keyframes orbit-pulse {
  0%, 100% { filter: drop-shadow(0 0 18px var(--accent, #b98cff)); }
  50%      { filter: drop-shadow(0 0 34px var(--accent, #b98cff)); }
}
```

Add the radial gradient once, in an inline `<defs>` inside the SVG:

```html
<defs>
  <radialGradient id="orbit-core-gradient" cx="35%" cy="35%">
    <stop offset="0%" stop-color="#ffffff" />
    <stop offset="45%" stop-color="var(--accent, #b98cff)" />
    <stop offset="100%" stop-color="color-mix(in srgb, var(--accent, #b98cff) 40%, black)" />
  </radialGradient>
</defs>
```

**Give each ring a different period and at least one a reversed
direction** (§ reference above: 40s / 26s reverse / 60s) — matching speeds
or matching direction on every ring reads as one flat spinning disc rather
than several rings with real depth between them.

---

## 3. The scroll transition — fade + blur, never removed

The rotating object **keeps animating the entire time** — it is not paused,
removed from the DOM, or `display: none`'d at any scroll position. Only its
`opacity` and `filter: blur()` change, driven by scroll progress:

```css
.orbit-stage {
  opacity: var(--orbit-opacity, 1);
  filter: blur(var(--orbit-blur, 0px));
  transition: opacity 0.1s linear, filter 0.1s linear; /* smooths JS ticks, not the transition itself */
}
```

```js
function onScroll() {
  var progress = clamp01(getSectionScrollProgress()); // 0 at top of hero, 1 once fully scrolled past
  stage.style.setProperty("--orbit-opacity", 1 - progress * 0.75); // never fully invisible — stays ~25% visible through the glass
  stage.style.setProperty("--orbit-blur", (progress * 10) + "px");
}
```

**Never drive this to full `opacity: 0`.** The reference sequence shows the
object still faintly visible, blurred, *through* the glass drawer once it's
fully in place — that residual motion behind the glass is the point of the
pattern. Floor it around 0.2–0.3 opacity, not 0.

---

## 4. The drawer (glass content block)

The drawer is a separate element that starts below the viewport (or at
`opacity: 0` / a small `translateY`) and slides/fades up over the rotating
object as the same scroll progress advances:

```css
.orbit-drawer {
  position: absolute;
  inset: auto 0 0 0;
  margin-inline: auto;
  max-width: 960px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface, #1a1226) 55%, transparent);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid color-mix(in srgb, white 12%, transparent);
  padding: 40px;
  transform: translateY(var(--drawer-offset, 40px));
  opacity: var(--drawer-opacity, 0);
  transition: transform 0.1s linear, opacity 0.1s linear;
}
```

```js
drawer.style.setProperty("--drawer-opacity", progress);
drawer.style.setProperty("--drawer-offset", (40 - progress * 40) + "px");
```

`backdrop-filter: blur()` on the drawer is what makes the still-rotating
object behind it read as "seen through frosted glass" rather than just a
plain solid panel plopped on top.

### Cards inside the drawer are static

The feature-card row inside the drawer (see the reference screenshots'
"Smart development" / "Super-fast delivery" / "Global & synced" cards) is
**not** independently animated or staggered — it's ordinary content that
arrives already-in-place as part of the drawer itself. Don't add a
per-card entrance animation or stagger delay; that's a different pattern
(see `editorial-feature-reveal` if a request specifically wants cards
traveling in from center to their own positions).

```html
<div class="orbit-drawer">
  <h2>About our team</h2>
  <p>…supporting copy…</p>
  <a class="cta" href="#">Work with us →</a>
  <div class="drawer-cards">
    <article><h3>Smart development</h3><p>…</p></article>
    <article><h3>Super-fast delivery</h3><p>…</p></article>
    <article><h3>Global &amp; synced</h3><p>…</p></article>
  </div>
</div>
```

```css
.drawer-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 32px;
}
.drawer-cards article {
  background: color-mix(in srgb, white 6%, transparent);
  border: 1px solid color-mix(in srgb, white 10%, transparent);
  border-radius: 14px;
  padding: 20px;
}
@media (max-width: 760px) {
  .drawer-cards { grid-template-columns: 1fr; }
}
```

---

## 5. Driving scroll progress

Use a single scroll listener (or a `ScrollTrigger`/equivalent if the
project already has one loaded — don't add a new animation library just
for this) that measures the hero section's own scroll progress once and
updates both the stage and the drawer from the same number, so they always
stay in sync:

```js
function getSectionScrollProgress(section) {
  var rect = section.getBoundingClientRect();
  var total = section.offsetHeight - window.innerHeight;
  if (total <= 0) return 1;
  return clamp01(-rect.top / total);
}
function clamp01(n) { return Math.max(0, Math.min(1, n)); }
```

Pin the hero section (`position: sticky; top: 0; height: 100vh` on an inner
wrapper, with the outer section given extra scroll height, e.g. `height:
220vh`) so there's real scroll distance for the transition to play out
against, rather than it resolving within a single viewport-height of
scroll.

---

## 6. Responsive behavior

- **Desktop:** the full pinned sequence above.
- **Mobile / narrow viewports:** pinned scroll-hijacking and backdrop-blur
  glass panels are both expensive and fragile on small screens. Below a
  defined breakpoint (760px is a reasonable default), skip the JS
  entirely: no pin, no scroll-driven opacity/blur. Render the finished
  state as a normal static stack — rotating object as a smaller, still-
  animating (CSS `animation` alone is cheap) background behind a
  non-glass, non-blurred content block in normal document flow, cards
  stacked full-width below it.
- The JS should check the same breakpoint and return early
  (`if (window.innerWidth <= 760) return;`) rather than relying on CSS
  alone to hide the effect while JS still tries to drive it.

---

## 7. Accessibility

- **`prefers-reduced-motion: reduce`** must stop both the ring rotation and
  the pulse (`animation: none`) and render the drawer at its fully-settled
  state (`opacity: 1`, no offset) — check this before attaching any scroll
  listener, and skip attaching one entirely if it matches.
- The rotating SVG is purely decorative — mark it `aria-hidden="true"` (as
  in §2) so screen readers skip straight to the drawer's real heading/copy.
- The drawer's CTA stays a real, focusable `<a>`/`<button>` — never a
  `div` with a click handler.

---

## 8. Performance

- Animate the rings/core with plain CSS `@keyframes` (compositor-driven,
  no per-frame JS) — the scroll listener only ever touches `--orbit-opacity`,
  `--orbit-blur`, `--drawer-opacity`, and `--drawer-offset`, all consumed by
  `opacity`/`filter`/`transform`, never layout properties.
- `backdrop-filter: blur()` is expensive to repaint continuously — since
  the drawer's own blur amount is fixed (not scroll-scrubbed, only its
  opacity/offset are), this is a one-time cost per frame the drawer moves,
  not a continuously-recomputed filter.
- Throttle the scroll listener with `requestAnimationFrame` (read
  `scrollY`/`getBoundingClientRect()` once per rAF tick, not once per
  native `scroll` event) so fast scrolling doesn't queue redundant style
  writes.

---

## 9. Reference implementation

`assets/example.html` is a complete, self-contained worked example (dark
purple palette, three-ring orbit, "About our team" drawer with three
static cards) implementing every mechanic above — open it directly in a
browser and scroll to see the full sequence before adapting it into a
real project.

## Output

If this is being delivered as a standalone demo/prototype rather than
grafted into an existing project, save it as a single self-contained
`.html` file with `create_file` and share it with `present_files`. The
Visualizer tool's HTML mode also works well if the person wants to
iterate on it live in the conversation rather than as a downloadable file
— note that scroll-driven effects need real scroll distance to preview,
so keep the demo tall enough (`height: 220vh` or similar on the pinned
section) that the effect actually has room to play out.
