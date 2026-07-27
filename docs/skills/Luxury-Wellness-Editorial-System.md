# Luxury Wellness Editorial System

A reusable design system for premium wellness, skincare, and self-care brand
websites — extracted from a real production build (a foot-care brand
homepage). This is not a case study. It is an implementation playbook: the
philosophy, the exact CSS/JS mechanics, the mistakes that were made and
fixed, and a checklist for applying all of it to a new brand from scratch.

**Who this is for:** an AI agent (or engineer) starting a new luxury
wellness / self-care / premium skincare website with zero prior context on
where these patterns came from. Everything you need to reproduce the system
is in this document — you should not need to see the original project.

**How to use it:** read Design Philosophy and Visual Language first to
internalize the taste bar, then treat the rest as a component/pattern
library. Copy formulas and code structures, rename the CSS namespace to the
new brand, and re-derive the actual pixel/rem values from that brand's own
type and spacing scale rather than hard-coding the numbers below verbatim —
the numbers are reference points, the *reasoning* is what transfers.

---

## 1. Design Philosophy

### The one-sentence test
Every screen should pass this test: **"Does this feel like a luxury
skincare brand, or does it feel like an ecommerce template?"** If a visitor
could mistake the site for a generic WooCommerce/Shopify store, the design
has failed regardless of how correct the code is.

### Reference points (use these, not "modern SaaS" or "startup landing page")
- Apple product pages — restraint, one idea per screen, huge whitespace
- Aesop — ingredient-led minimalism, editorial photography, quiet confidence
- Minimal Scandinavian design — function over ornament, generous negative space
- Editorial magazine layouts — asymmetric image/text composition, not grids of cards
- Spa / boutique-hotel websites — calm pacing, nothing competing for attention

### Explicitly reject
- Card-grid "features" sections (3 icons + heading + paragraph, repeated)
- Bright saturated CTAs, badges, countdown timers, urgency UI
- Stock "hero + button" templates with no narrative
- Dense, symmetric grids — luxury reads as asymmetric and unhurried
- Generic sans-serif-everywhere typography (this is the single fastest way
  to make a premium brand look like a template)
- Motion for decoration — every animation must serve the story, not prove
  the developer knows GSAP

### The core narrative principle
**A luxury wellness homepage is a guided story, not a product catalog.**
Structure content as a sequence of "beats," each one communicating exactly
one idea, in a fixed emotional order:

1. Emotional opening (hero) — how the visitor will *feel*, not what you sell
2. The problem — name the frustration the visitor already has
3. Why existing solutions fail — reframe the category, not just the product
4. How the brand's approach works
5. Benefits — tangible outcomes, still emotionally framed
6. Social proof — real, understated, never a "5 stars!!" badge wall
7. The product itself — arrives *late*, after trust is built
8. Educational content — positions the brand as a guide, not a seller
9. Final CTA — calm, single action, no urgency tactics

**Educate first. Sell second.** The product should feel like the natural
conclusion of a story the visitor already agreed with, not something being
pushed on them from the first screen.

### Restraint is the luxury signal
The finished site should feel expensive because of what's *absent* —
competing colors, dense grids, more than one CTA per screen, decorative
motion — not because of what's added. Every element must justify its own
existence. When in doubt, remove it.

---

## 2. Visual Language

### Color
- One warm neutral background (cream/off-white), one deep ink/near-black
  for text, one muted neutral for secondary text, at most one accent tone
  pulled from the product itself (not an arbitrary brand-kit color).
- Never highly saturated colors. Saturation reads as "discount," not "premium."
- Backgrounds alternate between the warm neutral and a slightly deeper
  variant of the same neutral (not white vs. gray) to create section rhythm
  without introducing a new hue.
- Photography carries color. The UI chrome should almost disappear into the
  photography rather than competing with it.

### Layout posture
- Full-viewport or near-full-viewport sections, not stacked content blocks
  of arbitrary height. Each section should feel like **entering another
  room**, not scrolling past a divider.
- Asymmetric compositions by default: image 60–75% width, offset left or
  right, alternating per section — never a repeated 50/50 grid.
- Sharp corners on editorial imagery (no `border-radius`) when the
  reference mood is "magazine," not "app UI." Reserve rounded corners for
  actual UI chrome (buttons, cards in more utilitarian sections).
- Whitespace is a design element, not empty space to be minimized. If a
  section feels "safe," it usually needs *more* space around it, not more
  content inside it.

### What "premium" looks like in code, concretely
- Large type steps (fewer sizes, bigger jumps between them) instead of a
  dense 10-step type scale.
- Generous, non-linear spacing scale (see §10) — luxury spacing is not a
  flat 8px grid, it's an accelerating scale for section-level rhythm.
- Photography given room to breathe: never crop tight around a subject to
  fit a fixed card size; pick the aspect ratio the photo wants.

---

## 3. Editorial Composition System

The "story beat" is the fundamental content unit for the narrative sections
(problem, benefits, proof) — one image + one short heading + one short
paragraph, treated as a single visual composition, not a card.

### Anatomy of one editorial composition
```html
<div class="story story--left" style="--story-w: 74%;">
  <div class="story__media">
    <img src="..." alt="..." loading="lazy" decoding="async">
  </div>
  <div class="story__text">
    <h3>Short, declarative headline</h3>
    <p>One or two sentences. Muted color, relaxed line-height.</p>
  </div>
</div>
```

```css
.story { display: flex; flex-direction: column; width: 100%; }
.story--left  { align-items: flex-start; }
.story--right { align-items: flex-end; }

.story__media {
  position: relative;
  width: var(--story-w, 60%);
  aspect-ratio: 4 / 3;
  overflow: hidden; /* sharp corners — no border-radius */
}
.story__media img { width: 100%; height: 100%; object-fit: cover; }

.story__text { margin-top: var(--space-xs); width: var(--story-w, 60%); max-width: 26rem; }
.story--right .story__text { text-align: right; margin-left: auto; }
```

### Rules that make this read as "editorial" instead of "cards"
1. **Text alignment always follows image alignment.** Left-aligned image →
   left-aligned text. Right-aligned image → right-aligned text, `margin-left:
   auto` so the text block visually anchors to the image, not floats
   independently in the middle of the row.
2. **Alternate left/right/left/right per composition** down the page. Never
   two of the same alignment in a row — the alternation *is* the rhythm.
3. **Vary width per item** (`--story-w`, set inline per instance: 52%, 68%,
   74%, etc.), not a fixed column width. Uniform widths read as a grid;
   varied widths read as curated.
4. **One heading + one short paragraph maximum per composition.** This is
   not the place for feature lists or bullet points.
5. **A tight gap between image and its own heading** (`margin-top:
   var(--space-xs)`, i.e. one of the *smallest* steps in the spacing scale)
   — the text should feel physically attached to its image. The *generous*
   spacing in this system lives *between* compositions (`gap:
   var(--space-l)` on the parent flex column), not within one.
6. **An "overlap" variant exists but should be rare**: heading positioned
   `position: absolute; inset: auto 0 0 0` over the image's own lower edge,
   behind a gradient scrim for contrast. Use it for exactly one composition
   per page at most — overusing it turns editorial into "poster carousel."

### Composition sequencing
Treat the parent container as one continuous flow, not separated cards:
```css
.story-rows {
  display: flex;
  flex-direction: column;
  gap: var(--space-l); /* tighter than a full section gap — one flow, not stacked cards */
  max-width: 90rem;
  margin: 0 auto;
}
```

---

## 4. Hero Architecture

### Structure
```html
<section class="hero">
  <div class="hero__media"><img ... loading="eager" fetchpriority="high"></div>
  <div class="hero__scrim"></div>
  <div class="hero__content">
    <p class="eyebrow">Brand name</p>
    <h1>The emotional promise, not the product name</h1>
    <p>One sentence of supporting context.</p>
  </div>
  <a class="hero__scroll-cue" href="#next-section">Scroll</a>
</section>
```

```css
.hero {
  position: relative;
  width: 100%;              /* explicit — see §5 for why this matters */
  min-height: 100svh;       /* svh, not vh — avoids mobile browser-chrome jump */
  display: flex;
  align-items: flex-end;    /* content sits low, photo dominates */
  overflow: hidden;
}
.hero__media { position: absolute; inset: 0; }
.hero__media img { width: 100%; height: 100%; object-fit: cover; }
```

### Rules
- **The photograph is the hero, not the headline.** Content is bottom-aligned,
  large, but occupies a minority of the frame.
- **A gradient scrim, not a flat overlay.** Near-transparent over the top
  ~40% of the image, deepening toward the text zone for contrast — the
  photo should read as *bright* everywhere the text isn't:
  ```css
  background: linear-gradient(180deg,
    rgba(0,0,0,0.02) 0%,
    rgba(0,0,0,0.06) 40%,
    rgba(0,0,0,0.32) 65%,
    rgba(0,0,0,0.5) 100%);
  ```
- **One subtle load-in cue, not continuous parallax.** A single slow
  `scale(1.06) → scale(1)` image settle on load (6s, eased) reads as
  "considered." Continuous scroll-linked parallax on the hero reads as
  "template with a parallax plugin." Keep motion here minimal and one-shot.
- **The headline is the emotional promise** ("Foot care you'll actually
  stick with"), not a product descriptor ("Premium Foot Cream 250ml"). Save
  literal product framing for later beats.
- **A scroll cue is not optional** on a full-viewport hero — visitors need
  a signal that content continues below the fold. A thin vertical line that
  draws in on load (`scaleY(0) → scaleY(1)`) is enough; no bouncing arrows.

---

## 5. Circular Transition Pattern

The signature "hero dissolves into the next section through an expanding
circle" moment. This is the highest-risk, highest-payoff piece of the whole
system — get it right and it feels cinematic; get it wrong and it produces
visible seams, jumps, or dead scroll space. This section is long because
every sentence in it was earned by a real bug.

### What it is
A perfect circle grows from the bottom-center of the viewport, overlaying
the hero photo, until it becomes a solid field of the *next section's own
background color* — at which point it silently **becomes** that section
instead of "revealing" it. A heading rises and fades in in step with the
circle's growth, inside it.

### Why a circle, and why bottom-center
A circle scaled from a single fixed point is the only shape that stays
geometrically correct (no distortion) using `transform: scale()` alone —
never animate `width`/`height` independently, or the shape stops being a
circle mid-growth. Bottom-center gives the growth a clear origin that reads
as "emerging" rather than an arbitrary wipe.

### HTML / CSS skeleton
```html
<section class="hero">
  ...
  <div class="circle-reveal"></div>
  <div class="circle-reveal__text"><h2 class="circle-reveal__heading">…</h2></div>
</section>
```

```css
.circle-reveal { display: none; } /* static by default — see §11 progressive enhancement */

.hero.is-circle-active .circle-reveal {
  display: block;
  position: absolute;
  left: 50%; bottom: 0;
  z-index: 3;
  /* 300vmax diameter (150vmax radius): comfortably covers the distance
     from bottom-center to the farthest viewport corner at ANY aspect
     ratio, with margin — guarantees full coverage, no gap at the corners
     once fully expanded, on any screen shape. */
  width: 300vmax; height: 300vmax;
  margin-left: -150vmax; margin-bottom: -150vmax;
  border-radius: 50%;
  background: var(--color-bg); /* MUST exactly match the next section's own background */
  transform: scale(var(--circle-scale));
  transform-origin: center center;
  will-change: transform;
  pointer-events: none;
}

.hero.is-circle-active .circle-reveal__text {
  display: block;
  position: absolute; left: 50%; bottom: 0; z-index: 4;
  text-align: center; pointer-events: none;
  /* Heading position AND opacity both read the SAME --circle-scale custom
     property the circle itself is scaled by — this is what keeps the
     heading physically "attached" to the circle instead of running on an
     independent timeline that can drift out of sync. */
  transform: translate(-50%, calc(-1 * min(150vmax * var(--circle-scale, 0.02) * 0.45, 58vh)));
  opacity: clamp(0, calc((var(--circle-scale, 0.02) - 0.15) / 0.3), 1);
}
```

The `min(…, 58vh)` cap on the heading's rise is important: without it, the
heading keeps climbing toward the (by-then off-screen) top of the fully
grown circle. Capping it means the heading settles into a comfortable
upper-middle resting position once the circle is already large.

The opacity formula (`0` below scale `0.15`, ramping to fully opaque by
scale `0.45`) front-loads the heading's legibility well before the circle
has finished growing — "the heading is already becoming visible within the
circle," not "wait for the circle to fill the screen, then reveal text."

### The color-match rule (non-negotiable)
The circle's `background` must be the **exact same token** as the next
section's own `background-color`. This single rule is what allows every
other trick in this section to work:
- It means the hand-off from "circle" to "next section" has no visible
  seam — the circle doesn't reveal the next section, it silently *becomes*
  its background.
- It means an instant positional "snap" at hand-off (see below) is
  invisible, because both states before and after the snap are the same
  flat color.

### The scroll mechanics (GSAP ScrollTrigger)
This is implemented as **two separate `ScrollTrigger` instances sharing one
trigger element**, not one. This split is the single most important
architectural decision in this pattern:

1. **The growth tween** — scrubs `--circle-scale` from `~0.02` to `1` across
   a scroll distance derived from the hero's own measured height (not a
   fixed `vh` guess, so it's correct at any hero height):
   ```js
   var heroHeight = hero.getBoundingClientRect().height;
   var growthDistance = heroHeight * 1.0; // tune this ONE number to change speed — see §6
   ```
2. **The pin** — a *separate* `ScrollTrigger.create({ pin: true, pinSpacing:
   false, ... })` on the same trigger element, whose own `end` can be a
   *different, shorter* distance than the growth tween's. This is what lets
   you release the pin (resume normal scrolling) at any point in the
   circle's growth — e.g. "the moment the heading is clearly visible" —
   completely independent of how long the circle itself takes to finish
   growing. Compute that release point from what's actually visible, not a
   guessed scroll fraction:
   ```js
   // Find the raw (pre-easing) scroll fraction at which the EASED
   // --circle-scale first reaches a target value, using the same easing
   // curve the growth tween uses (binary search / invert the curve).
   var pinEnd = growthDistance * scrollFractionForScale(0.45 /* heading fully opaque */);
   ```

Why two triggers instead of one: a single trigger can only have one `end`.
Coupling "how long the pin lasts" to "how long the circle takes to grow"
means you can never independently tune "the circle should feel slower" and
"scrolling should resume sooner" — which is exactly the pair of requests a
real client makes in sequence. Decouple them from day one.

### `pinSpacing: false` — what it actually buys you, and its real cost
- **The problem it solves:** a normal `pin: true` (default `pinSpacing:
  true`) inserts a spacer that reserves `element height + pin scroll
  distance` worth of document space. Once the pin's active phase ends, the
  visitor must *still* scroll through the element's own full natural
  height again before the next section arrives — a dead "coast" of nothing
  happening. **`position: sticky` has the exact same limitation** — a
  sticky element still has to scroll through its own full natural height
  once it un-sticks. (This is easy to misdiagnose as fixed if your test
  viewport happens to be unusually tall, because a tall viewport lets the
  next section's content peek in from the bottom before the coast is
  visually obvious — verify on a *realistic* 700–900px-tall viewport, not
  whatever your dev monitor happens to be.)
- **The fix:** `pinSpacing: false` reserves *no* extra document space at
  all — the next section scrolls into its true, normal document position
  underneath the still-pinned hero the entire time, so it's already
  exactly where it needs to be the moment the pin releases. Zero coast.
- **The real cost — read this before you use it:** `pinSpacing: false`
  does **not** produce a one-time "jump" at release, as GSAP's docs might
  imply. It leaves a **permanent compensating transform** on the pinned
  element after release, so it never *visibly* snaps — meaning the pinned
  element keeps rendering, opaque, at its old fixed screen position for
  another full pin-distance worth of scroll *after* the pin technically
  ends, silently overlapping into the next section's own space the whole
  time. Confirmed by inspecting the element's computed `transform` after
  release: it holds a constant `translateY` offset, it does not reset. If
  you don't correct for this, whatever is behind the pinned element (the
  next section's content) will either be invisibly hidden for far longer
  than intended, or — if stacking order favors the later element — will
  visibly collide with the still-lingering pinned content.
- **The corrective pattern**, in the pin trigger's `onLeave`:
  ```js
  onLeave: function () {
    gsap.set(pinnedElement, { clearProps: "all" }); // force a REAL snap to true static position
    // any element whose position depends on a "while pinned" formula
    // (like the heading above) needs its own one-time settle here too —
    // see the note on circleText below.
  },
  onEnterBack: function () {
    // scrolling back up into the active range — hand control back to
    // whatever live formula/ScrollTrigger normally drives this element
    gsap.set(settledElement, { clearProps: "transform" });
  },
  ```
  This forces an *actual* instant snap rather than a lingering fade — which
  is safe specifically *because* of the color-match rule above: at the
  release point the circle is already a large, solid field of the shared
  background color, so an instant positional snap of the whole hero is
  visually indistinguishable from no snap at all. **This pattern only
  works because of the color match — do not attempt `pinSpacing: false`
  hand-offs without it.**
- **z-index is not automatic.** A pinned (`position: fixed`) element has no
  z-index of its own by default, and the following section — later in DOM
  order — will paint *on top of* the pinned element the instant they
  visually overlap, unless the pinned element has an explicit z-index:
  ```css
  .hero.is-circle-active { z-index: 10; } /* higher than the next section's own content */
  ```
  Without this, the incoming section's content becomes visible (and can
  visually collide with foreground elements like a still-settling heading)
  *before* the pin releases, not after.
- **GSAP's pin-spacer wrapper is `display: flex`.** This silently turns
  the pinned element into a flex *item*, and flex items shrink to their
  content's width by default instead of filling the row — this only
  becomes visible once the pin's own inline width lock is cleared (via
  `clearProps` above), at which point a hero with no explicit width can
  collapse to a narrow, left-hugging column. Give the pinned element an
  explicit `width: 100%` in its base CSS, unconditionally, to make this
  robust regardless of what wrapper GSAP inserts:
  ```css
  .hero { width: 100%; /* explicit — see above */ }
  ```
- **Two `ScrollTrigger`s on the same trigger element will fight over "top
  top."** If one of them pins the element, GSAP re-derives the *second*
  trigger's `start` against the *already-pinned* state of the first,
  shifting its computed start forward by the first trigger's own pin
  distance — silently delaying the second trigger's animation until after
  the first one's pin has already released. **Fix: compute one absolute
  numeric scroll position up front and give both triggers that same
  number, instead of the `"top top"` keyword:**
  ```js
  var anchor = hero.getBoundingClientRect().top + window.scrollY; // usually 0
  // pin trigger:   start: anchor,           end: anchor + pinEnd
  // growth trigger: start: anchor,          end: anchor + growthDistance
  ```

### Mobile
Run this pattern at all viewport widths, including mobile, if it's meant
to be *the* hero-to-section experience rather than a desktop flourish —
its math is `vmax`/viewport-relative throughout and needs no separate
mobile tuning. This is a deliberate, documented exception to "avoid heavy
motion on mobile" — it should stay rare, not become precedent for adding
scroll-jacking elsewhere on mobile.

---

## 6. Scroll Behavior

### Two independently tunable levers, not one
Every scroll-driven sequence in this system separates **"how long/slow does
the effect take"** from **"when does control return to the visitor"** —
these must be two different numbers, even when implemented as two
ScrollTriggers on the same element (see §5). A single client request like
"make the circle slower, but let me scroll away sooner" is only answerable
if these were never coupled in the first place.

### Global rule: `scroll-behavior: smooth` and scrubbed animations
Keep `html { scroll-behavior: smooth; }` for anchor-link navigation (e.g. a
hero's "scroll cue" `<a href="#next">`), but be aware it can interact
unpredictably with any tooling that reads scroll position immediately after
a programmatic `scrollTo()` — always re-read the scroll position after a
short wait when verifying scroll-driven state, don't trust the value read
in the same tick as the scroll call.

### Full-viewport section rhythm
Treat each narrative beat (§1) as its own scroll "room": either a real
full-viewport (`min-height: 100svh`) section, or, if the content is short
(a 4-point list, say), one section with generous internal gaps rather than
four separate full-viewport sections — a genuine full-viewport-per-bullet
treatment can make a short list feel padded and overlong. Match the
section's height to how much visual weight the content actually earns, not
a rule of "every beat = one screen."

### Avoid dead scroll space above the fold of a section
A common failure mode: a section's heading is followed by large top
padding intended for "breathing room," but combined with a hero transition
above it, the *cumulative* gap between "previous section's content ends"
and "this section's first real content appears" balloons to several
screens of empty scroll. Audit the *actual end-to-end* gap a visitor
experiences, not each section's padding in isolation — min-height, pin
spacer distance, and top padding all stack.

---

## 7. Animation Principles

Ported near-verbatim from the animation spec this system was built under —
these are load-bearing rules, not suggestions.

### Overall feeling
Motion should be: **elegant, premium, natural — slow enough to notice, fast
enough to never frustrate, invisible when unnecessary.** Reference: Apple
product launches, luxury hotel sites, premium architecture studios. Not:
gaming, agency demo reels, playful bounce effects.

### Section transitions
Each major section transitions like entering another room. Use combinations
of fade / scale / depth / parallax / opacity. Never dramatic, never
distracting.

### Hero motion
Subtle only: soft floating background, gentle light movement, slow
parallax, a very restrained image reveal. One documented exception is
allowed per site: a hero-to-section transition (like the circular pattern
in §5) that departs from the usual small-scale-range image motion, because
it's a full scene transformation, not "an image revealing."

### Image motion (everywhere else)
Fade in, soft upward movement, scale from **98% to 100%** (not more). Never
fly in, never bounce, never rotate. This narrow scale range (98→100%,
not e.g. 90→100%) is what keeps image reveals reading as "settling into
place" rather than "sliding in."

### Text animation
Preferred: fade, blur-to-sharp, opacity, small `translateY`. Avoid: letters
flying in, typewriter effects, aggressive stagger timing.

### Hover effects
Soft elevation, shadow refinement, 2–4% image zoom, color transitions,
cursor feedback. Never dramatic.

### Buttons
Fast response, subtle press, soft hover, no glow effects.

### Motion philosophy
**Visitors should remember how the site made them feel, not the animations
themselves.** Good motion is nearly invisible. If a stakeholder's first
reaction to a section is "cool animation," reconsider whether it served the
story or just showed off the tooling.

---

## 8. Typography Hierarchy

### Three-family system (not one, not five)
- **Display serif** for headlines and the "moment" typography (hero H1,
  section H2s, the circular-transition heading) — this carries the luxury
  feeling. Pick something editorial, not a generic serif.
- **Body sans-serif** for paragraphs and UI text — legible at small sizes,
  quiet, doesn't compete with the display face.
- **Accent sans-serif** (can be the same as body, or a slightly more
  geometric companion) for labels, eyebrows, captions, small numerals.

Avoid defaulting to a single system-UI sans-serif (e.g. Inter) for
everything "unless there is a compelling reason" — a single generic sans
across headlines and body is the fastest way to make a premium brand read
as a template.

### Scale: fewer, larger steps
Luxury type scales are *shorter* than typical UI type scales — five or six
steps, not twelve — with **larger jumps between them**, all built on
`clamp()` so they're fluid without needing per-breakpoint overrides:

```css
--text-display-xl: clamp(2.75rem, 5vw + 1rem, 5.5rem);   /* hero H1 */
--text-display-l:  clamp(2.25rem, 3.5vw + 1rem, 3.75rem); /* section H2 */
--text-display-m:  clamp(1.75rem, 2.2vw + 1rem, 2.5rem);  /* sub-heads */
--text-body-l:     clamp(1.125rem, 0.6vw + 1rem, 1.375rem);
--text-body:       1.0625rem;
--text-small:      0.875rem;
--text-label:      0.8125rem;   /* eyebrows, buttons, uppercase labels */

--leading-tight:   1.15;  /* display type */
--leading-snug:    1.35;
--leading-relaxed: 1.7;   /* body paragraphs */
```

### The "moment" heading gets its own oversized step
A heading that IS the visual centerpiece of a scroll moment (like the
circular-transition heading) should be sized *larger* than the site's
normal `display-xl`, not reuse it — it's not a normal section heading, it's
the focal point of a specific scene:
```css
.moment-heading { font-size: clamp(2.5rem, 5vw + 1rem, 5rem); }
```

### Editorial composition headings (§3) run larger than utility headings
A `.story__text h3` should be sized closer to the site's `display-m`/`l`
range with the display serif — these headlines are primary editorial
elements, not card labels. Reserve smaller, sans-serif headings for
genuinely secondary UI (topic-grid cards, pillar lists).

---

## 9. Image Treatment

- **`object-fit: cover` everywhere**, paired with a deliberate `aspect-ratio`
  per context (don't let images dictate arbitrary box heights).
- **Sharp corners on editorial/story imagery** (no `border-radius`) —
  matches an editorial/magazine reference. Reserve soft rounding
  (`var(--radius-m)`) for more utilitarian media (proof screenshots, topic
  cards).
- **`object-position` tuned per photo**, not left at default `center` — a
  lifestyle photo's subject is rarely dead-center; adjust per image
  (`object-position: 75% 65%`, `center 30%`, etc.) rather than cropping the
  source file differently for each use.
- **Full-bleed treatment for wide architectural/environment shots.** If a
  source photo is meaningfully wider than the aspect ratio used elsewhere
  in a list, don't force it into that ratio and throw away most of the
  frame — give it its own near-native-width treatment so the space reads
  as a real place, not a cropped detail.
- **`loading="eager" fetchpriority="high"` on the hero image only**; every
  other image `loading="lazy" decoding="async"`.
- **Never crowd images with text.** Photography needs room to breathe —
  this is a philosophy point (§1) with a direct CSS consequence: generous
  `margin-top` between an image and its own caption/heading, and generous
  `gap` between compositions.
- **Product photography is the one place cutouts belong** — isolated
  product shots explain features/benefits; lifestyle photography (in
  context, in use) creates emotion. Use both, deliberately, not
  interchangeably.

---

## 10. Spacing System

### An accelerating scale, not a flat grid
Luxury spacing is not "everything is a multiple of 8px." Use a scale that
*accelerates* at the top end, so section-level rhythm (the big gaps) can be
dramatically larger than component-level rhythm (the small gaps) without
needing arbitrary one-off values:

```css
--space-3xs: 0.25rem;  /* 4px  — hairline gaps (icon+label) */
--space-2xs: 0.5rem;   /* 8px */
--space-xs:  0.75rem;  /* 12px — image-to-its-own-caption */
--space-s:   1.25rem;  /* 20px */
--space-m:   2rem;     /* 32px — standard component gap */
--space-l:   4.5rem;   /* 72px — between editorial compositions */
--space-xl:  7.5rem;   /* 120px */
--space-2xl: 11rem;    /* 176px */
--space-3xl: 15rem;    /* 240px — largest section-level rhythm */

/* Section-level padding — fluid, not fixed, so it scales with viewport
   rather than needing separate mobile overrides for every section */
--section-padding-y: clamp(5rem, 11vw, 10.5rem);
--section-padding-x: clamp(1.5rem, 6vw, 6rem);
```

### Rules
- **Small gaps (`3xs`–`xs`) are for things that belong to each other** —
  an image and its own directly-attached caption, an icon and its label.
- **Large gaps (`l`–`3xl`) are for things that are independent beats** —
  between editorial compositions, between major sections.
- **Never hand-roll a one-off pixel value mid-project.** If none of the
  scale steps feel right, that's a signal the scale itself needs a new
  step (rare), not a reason to write `padding-top: 87px` inline.
- **When a client asks to reduce space between two specific elements,
  identify EXACTLY which element is responsible before touching anything**
  (min-height? bottom padding? a scroll-trigger's own distance? a pin
  spacer?) — see §16 for the recurring failure mode here.

---

## 11. Sticky vs. Non-Sticky Decisions

### The core insight: `position: sticky` and `pin + spacer` have the SAME limitation
Both techniques reserve document space equal to `element's natural height +
however far it's meant to travel while stuck/pinned`. Once the
active/stuck phase ends, the visitor must **still scroll through the
element's own full natural height again** before the next section arrives.
This is not a bug in either technique — it's how both are defined. Treat
them as functionally equivalent for this purpose; switching from one to the
other to "fix" a coast problem will not fix it.

**Diagnosis trap:** this can look fixed on a tall test viewport, because
tall viewports let the next section's content visually peek in from the
bottom before the previous element has finished coasting away at the top —
disguising the real coast distance. Always verify against a realistic
700–900px-tall viewport, and trace the pinned/sticky element's actual
`getBoundingClientRect()` across the *entire* scroll range, not just its
resting state.

### When to use sticky
- Simple "stays in place while a sibling scrolls past" effects (a sticky
  sidebar nav, a sticky product image next to scrolling spec text) where
  the coast-after-release is either desired or irrelevant.
- You don't need JS, and you don't need the element to do anything other
  than stick and unstick.

### When to use `pin: true` (default spacing)
- You need scroll-scrubbed animation *during* the pinned phase (a GSAP
  timeline tied to scroll progress) and the "coast" after release is
  acceptable or even desired (e.g. a deliberate breathing pause before the
  next beat).

### When to use `pin: true` + `pinSpacing: false`
- You need scroll-scrubbed animation during the pinned phase **and** you
  need the next section to already be in position the instant the pin
  releases, with zero dead scroll after. This is the higher-complexity,
  higher-payoff option — see §5 for the full mechanics and the real cost
  (permanent compensating transform, z-index requirements, flex-item
  width collapse) that come with it. Don't reach for this by default;
  reach for it specifically when a coast is unacceptable.

### Never manually fight a pin's own position bookkeeping
Do not manually set `position`, `margin-top`, or `z-index` on a
pin-adjacent element *while* GSAP's `pin: true` is still the active
mechanism for that same element. This produces genuinely unstable,
reproducible bugs — erratic scroll-position jumps with no user input,
elements acquiring unexplained `transform: matrix(...)` values — because
it fights GSAP's own internal position-restoration bookkeeping. If an
element's position needs correcting post-pin, do it through GSAP's own
API (`clearProps`, or a `gsap.set` in `onLeave`/`onEnterBack`), never by
reaching into its inline styles directly alongside an active pin.

---

## 12. Motion Guidelines

### Two implementation tiers, used deliberately
- **Vanilla `IntersectionObserver` + CSS transitions** for simple one-shot
  reveals (fade/translate/scale on scroll-into-view). No animation library
  needed. This should be the *default* for the vast majority of the page.
- **GSAP + ScrollTrigger** reserved for genuinely scroll-*scrubbed*
  sequences (progress tied continuously to scroll position, not a single
  on/enter trigger) — pinned transitions, merge/split image sequences,
  anything where the animation must track scroll position frame-by-frame.
  Pulling in an animation library for simple fade-ins is over-engineering;
  reserve it for the 1–2 sections on the whole site that actually need it.

### The vanilla reveal pattern (default, use this first)
```js
var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (prefersReduced) {
  document.querySelectorAll(".reveal").forEach(el => el.classList.add("is-visible"));
} else {
  var observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target); // one-shot, never re-hide on scroll-away
      }
    });
  }, { threshold: 0.2, rootMargin: "0px 0px -10% 0px" });
  document.querySelectorAll(".reveal").forEach(el => observer.observe(el));
}
```
```css
.reveal {
  opacity: 0;
  transform: translateY(var(--motion-distance)) scale(0.98); /* 24px, 98% — see §7 */
  transition: opacity var(--motion-duration-l) var(--motion-ease),
              transform var(--motion-duration-l) var(--motion-ease);
}
.reveal.is-visible { opacity: 1; transform: translateY(0) scale(1); }
@media (prefers-reduced-motion: reduce) {
  .reveal { opacity: 1; transform: none; transition: none; }
}
```

### One trigger per section, not per element
Attach `.reveal` to the *outer* wrapper of a composition (image + heading +
paragraph together), not to each child independently. They should fade/rise
in as one unit. Per-element staggered reveals inside a single composition
read as "busy," not "premium."

### Deliberately un-animated content is a valid, common decision
Not everything needs scroll-reveal. Editorial story compositions (§3) that
already have generous natural spacing and appear in a slow, deliberate
scroll rhythm often read *better* fully static — simply present in normal
document flow — than with an added fade-in, especially directly after a
more elaborate hero transition where additional motion competes with what
just happened. If asked to "remove animation, let it move naturally with
the page," that means: no scroll trigger, no transform, no opacity
transition — just remove the reveal class entirely, don't replace it with
a faster/subtler version.

### Motion durations and easing tokens
```css
--motion-duration-s: 450ms;
--motion-duration-m: 650ms;
--motion-duration-l: 850ms;
--motion-ease: cubic-bezier(0.22, 1, 0.36, 1);   /* time-based reveals */
--motion-distance: 24px;
--ease-in-out: cubic-bezier(0.76, 0, 0.24, 1);   /* SYMMETRIC — for scroll-scrubbed properties */
```
Use a distinct easing token for scroll-scrubbed animation vs. time-based
reveal animation — a symmetric ease-in-out (equal acceleration and
deceleration) reads as "calm and architectural" for something tied to
scroll position, while `--motion-ease` (a gentler ease-out) suits
one-shot, time-based reveals better.

---

## 13. Performance Guidelines

- **Animate `transform` and `opacity` only.** Never animate `width`,
  `height`, `top`/`left`, or layout-triggering properties — this is why the
  circular transition (§5) uses `scale()` and CSS custom properties instead
  of resizing a box.
- **`will-change` only on elements actively mid-animation**, removed or
  scoped afterward — don't blanket-apply it, it costs memory.
- **`loading="eager" fetchpriority="high"` on the hero image only.**
  Everything else `loading="lazy"`.
- **Respect `prefers-reduced-motion` everywhere, with a real static
  fallback** — not just `transition: none` on top of a broken half-animated
  state. The reduced-motion path should render every element in its final,
  fully-visible position from the start (see §11's progressive-enhancement
  pattern for the canonical way to do this).
- **A JS/CDN failure must never leave the page half-animated.** If GSAP
  fails to load (`typeof gsap === "undefined"`), bail out of the whole
  enhancement script immediately — the page must already be correct
  without it (see §16, progressive enhancement).
- **One `IntersectionObserver`, reused, `unobserve()` after first
  trigger** — don't create a new observer per element.
- **Maintain high Lighthouse scores as a hard constraint**, not an
  afterthought — motion must remain smooth on mid-range devices, and
  should degrade gracefully (fewer/shorter animations, not broken ones) on
  slower ones.

---

## 14. GSAP Implementation Notes

Reference implementation: cubic-bezier easing without pulling in the
separate CustomEase plugin, using a standard Newton-Raphson solve (this is
the same technique browsers use internally for CSS bezier easing):

```js
function cubicBezier(x1, y1, x2, y2) {
  function a(p1, p2) { return 1 - 3 * p2 + 3 * p1; }
  function b(p1, p2) { return 3 * p2 - 6 * p1; }
  function c(p1) { return 3 * p1; }
  function calc(t, p1, p2) { return ((a(p1, p2) * t + b(p1, p2)) * t + c(p1)) * t; }
  function slope(t, p1, p2) { return 3 * a(p1, p2) * t * t + 2 * b(p1, p2) * t + c(p1); }
  function tForX(x) {
    var t = x;
    for (var i = 0; i < 8; i++) {
      var s = slope(t, x1, x2);
      if (s === 0) return t;
      t -= (calc(t, x1, x2) - x) / s;
    }
    return t;
  }
  return function (x) { return x1 === y1 && x2 === y2 ? x : calc(tForX(x), y1, y2); };
}
var easeInOut = cubicBezier(0.76, 0, 0.24, 1); // must match the CSS token exactly
```

### Load order matters when two GSAP sections share a page
If two independent GSAP scroll sections sit adjacent in the DOM and each
grows/measures its own trigger section's height dynamically, load and
initialize them in the same order they appear on the page. Initializing
the *later* section first can cause it to measure stale (pre-growth)
document heights from the earlier section, producing content
overlaps/gaps that only appear in that specific script-order combination.

### Registering and guarding
```js
(function () {
  "use strict";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") return;
  var el = document.querySelector(".target");
  if (!el) return;
  gsap.registerPlugin(ScrollTrigger);
  // ... only now touch the DOM / set starting states
})();
```
Every GSAP entry script should be wrapped exactly like this: guard clauses
first, DOM mutation only after every precondition is confirmed. This is
what makes the no-JS/reduced-motion/CDN-failure fallback actually work —
see §16.

### Debugging scroll-scrubbed state
- Read `ScrollTrigger.getAll()` to inspect every active trigger's computed
  `start`/`end`/`pin` — invaluable when two triggers unexpectedly
  interact (see §5's "top top" pitfall).
- Read a tween's live custom-property value via
  `getComputedStyle(el).getPropertyValue('--your-prop')`, not the GSAP
  tween object — you want what's actually painted.
- **Verify state at rest, not mid-momentum.** Programmatic `scrollTo()`
  followed immediately by a read can capture a scroll position that's
  still animating (native smooth-scroll easing, or scroll-linked
  momentum) — always `await` a short settle delay (300–600ms) before
  reading `window.scrollY` or any derived layout value when verifying
  behavior, and prefer `window.scrollTo({ top, behavior: 'instant' })`
  when you need a precise, non-animated jump for testing.
- **Browser HTTP caching can silently serve a stale script during
  iterative development**, making an edit appear to have "no effect" even
  though the file on disk is correct. If behavior doesn't change after an
  edit you're confident in, verify the actually-served bytes (fetch the
  script directly and diff, or check the live DOM's `<script src>` for
  unexpected staleness) before re-diagnosing the logic itself.

---

## 15. CSS Architecture

### File split
- `tokens.css` — every design token (color, type scale, spacing scale,
  motion durations/easing, radius, shadow). No selectors beyond `:root`.
  Single source of truth; every other file references tokens, never raw
  values.
- `base.css` — reset, root html/body rules, global `scroll-behavior`.
- `components.css` — reusable, page-agnostic components (buttons, the
  generic `.reveal` system, section wrapper, media/image components) —
  usable on any future page type, not homepage-specific.
- `homepage.css` (or `[page].css` per page type) — layout specific to one
  page's beat sequence. Comment each major block with which "beat" (§1) it
  implements.

### Token examples (color + motion; see §8/§10 for type/spacing)
```css
:root {
  --color-ink: #0c1115;
  --color-ink-muted: #6a6b6c;
  --color-white: #ffffff;
  --color-cream: #f8f7f4;
  --color-cream-deep: #efeee9;
  --color-accent: #e3c4a8; /* pull from product/packaging, not an arbitrary brand color */

  --color-bg: var(--color-cream);
  --color-bg-alt: var(--color-cream-deep);
  --color-text: var(--color-ink);
  --color-text-muted: var(--color-ink-muted);

  --radius-s: 4px;
  --radius-m: 10px;
  --shadow-soft: 0 12px 40px -16px rgba(12, 17, 21, 0.18);
  --shadow-lift: 0 20px 60px -20px rgba(12, 17, 21, 0.28);
}
```

### Comment discipline (this matters more than it sounds like)
Every non-obvious value gets a comment explaining **why**, not what — "96px
— within the requested 40-70px range once combined with the 16px settle
offset in arc-reveal.js" is useful; "padding-top: 2.5rem /* top padding */"
is not. This system accumulated many hard-won, non-obvious numbers (easing
curves, scroll-fraction formulas, z-index requirements); the reasoning is
what keeps a future editor from "simplifying" away a fix. When you resolve
a subtle bug, document the *failure mode*, not just the final value.

### Naming
Namespace every class to the brand (`.molosoc-story`, not `.story`, in
production) to avoid collisions with any CMS/theme framework classes. This
document uses unprefixed names for readability; rename on implementation.

---

## 16. Common Mistakes to Avoid

These are real mistakes made and corrected during this system's
development. Each one cost real iteration time — avoid repeating them.

1. **Misdiagnosing `position: sticky` as fixing a "coast" problem that
   `pin: true` also has.** They share the same root limitation (§11).
   Switching techniques without understanding *why* the coast happens will
   not fix it — always trace the element's actual on-screen position
   across the *entire* scroll range before concluding a fix worked.
2. **Verifying a fix only via static, at-rest geometry, never the full
   live scroll range.** A wrap/spacer's resting height can look correct
   while the element it wraps still visibly "coasts" for hundreds of
   pixels during actual scroll. Trace `getBoundingClientRect()` across
   multiple scroll positions, not just one.
3. **Testing on a tall viewport and calling it fixed.** A tall test
   viewport can visually disguise a coast bug by letting later content
   peek in before the coast finishes. Always additionally test at a
   realistic ~700–900px height.
4. **Manually setting `position`/`margin`/`z-index` on an element while a
   GSAP `pin: true` is still actively managing that same element.** This
   produces genuinely unstable, hard-to-reproduce scroll jitter by
   fighting GSAP's internal bookkeeping. Use GSAP's own APIs
   (`clearProps`, `onLeave`/`onEnterBack`) to correct pin-adjacent state.
5. **Assuming `pinSpacing: false` produces a one-time jump you can ignore.**
   It leaves a *permanent* compensating transform unless explicitly
   cleared — silently causing the pinned element to linger and overlap the
   next section for far longer than intended (§5).
6. **Giving two `ScrollTrigger`s on the same trigger element `"top top"`
   independently**, when one of them pins. The second trigger's computed
   start silently shifts by the first trigger's pin distance. Anchor both
   to one shared, precomputed absolute scroll number instead.
7. **Assuming a pinned element keeps its natural CSS width.** GSAP's pin
   wrapper is `display: flex`; an element with no explicit width can
   collapse to content-width once its own inline width lock is cleared.
   Give pinned elements an explicit `width: 100%` up front.
8. **Forgetting z-index on a pinned element sharing stacking with a
   following in-DOM section.** A fixed-position element does not
   automatically win a stacking fight against later siblings just because
   it's "on top of the page" visually — explicit z-index is required.
9. **Changing multiple things at once when asked to fix one specific
   symptom** (e.g. "the gap is too big" gets fixed by also re-timing the
   animation, which the client never asked to change). When a request is
   scoped to one visual symptom, first identify the *exact* CSS property or
   scroll-trigger value responsible before touching anything, and change
   only that. If the true root cause requires touching something adjacent
   to what was explicitly protected, say so and explain the trade-off
   rather than silently doing it.
10. **Retiming a shared timeline instead of decoupling.** If a heading and
    an image are visually tied to the same tween/property, and a request
    asks to change the timing of only one of them, the fix is almost
    always to decouple them into two independently-tunable levers (see
    §5's two-ScrollTrigger split), not to compromise on a single shared
    number that partially satisfies both requests.
11. **Reading scroll position or layout immediately after a programmatic
    `scrollTo()` without waiting for it to settle**, especially with
    `scroll-behavior: smooth` active — the read can capture a mid-flight,
    not-yet-final value, leading to false conclusions about a bug.
12. **Concluding an edit "had no effect" without verifying the served
    bytes match disk.** Browser HTTP caching can serve a stale script
    during iterative testing and produce misleading "nothing changed"
    results.
13. **Adding scroll-reveal animation to literally everything by default.**
    Some content (see §12) reads better fully static. Motion is a tool for
    specific narrative beats, not a blanket treatment.
14. **Using a repeated 50/50 grid for editorial compositions.** Uniform
    grids read as templates. Vary width and alternate alignment (§3)
    deliberately.

---

## 17. Best Practices

- **Build the static, fully-visible state first; JS only pulls elements
  INTO a "before" state, never the reverse.** Write the HTML/CSS so that
  with zero JavaScript, the page already renders correctly, fully visible,
  in its final layout. Enhancement scripts should begin by hiding/setting
  starting states for animation — meaning if the script never runs (blocked,
  failed CDN, reduced motion), nothing is ever left half-hidden or
  mid-transition. This single discipline eliminates an entire category of
  "broken without JS" bugs.
- **One idea per screen, always.** If a section needs a sub-heading to
  explain what its own heading means, it's trying to say two things —
  split it.
- **Prefer removing an element over adding a fallback for it.** If motion,
  a badge, or a UI affordance doesn't clearly serve the narrative, the
  premium choice is to cut it, not to make it "more subtle."
- **Every scroll-driven number should be derived, not guessed.** Growth
  distances from `getBoundingClientRect()`, release points from inverting
  the actual easing curve (§5) — not hand-tuned magic pixel values that
  silently break if a photo's aspect ratio or a viewport size changes.
- **Comment the *why*, especially for anything counter-intuitive** (a
  z-index that looks unnecessary, a `clearProps` call, an odd-looking
  formula). The next editor — human or AI — needs to know *not* to
  "simplify" it away.
- **When a stakeholder gives narrow, explicit scope ("only change X, do
  not touch Y")**, treat that as a hard constraint on the *solution*, not
  just the *goal*. If achieving X cleanly requires touching something
  adjacent to Y, surface that trade-off explicitly rather than either
  silently expanding scope or silently under-delivering.
- **Test the reverse direction, not just forward scroll.** Any
  scroll-driven sequence with state changes on enter (`onLeave`,
  `clearProps`, class toggles) needs an equivalent, tested path for
  scrolling back up (`onEnterBack`) — don't ship a sequence that only
  works scrolling one direction.
- **Verify visually, not just numerically.** A computed gap value being
  "correct" doesn't guarantee the visual composition reads correctly —
  take real screenshots (or equivalent) at the specific moments a
  stakeholder is describing, especially hand-off/transition instants.

---

## 18. Reusable Implementation Checklist

Use this when standing up a new luxury wellness site from this system.

### Foundation
- [ ] Define color tokens: one warm neutral bg, one deep ink text, one
      muted secondary, at most one accent pulled from product/packaging
- [ ] Define a 3-family type system (display serif / body sans / accent
      sans) and a short, `clamp()`-based type scale (§8)
- [ ] Define an accelerating spacing scale, `3xs` through `3xl` (§10)
- [ ] Define motion tokens: 2–3 durations, one time-based easing, one
      symmetric scroll-scrubbed easing (§12)
- [ ] Split CSS into `tokens.css` / `base.css` / `components.css` /
      `[page].css`, tokens-only source of truth (§15)

### Narrative structure
- [ ] Map the page as a 9-beat story (§1) before writing any layout code
- [ ] Confirm the product itself arrives *late* in the sequence, after
      problem/solution framing
- [ ] Confirm no section tries to communicate more than one idea

### Hero
- [ ] Full-viewport, bottom-aligned content, gradient scrim (§4)
- [ ] One-shot load-in image settle only — no continuous parallax
- [ ] Explicit `width: 100%` on the hero, even before adding any pin (§5,
      §16 mistake #7 — cheap insurance)
- [ ] Scroll cue present and animates in once on load

### Circular / signature transition (if used)
- [ ] Circle background color is the exact same token as the next
      section's background — verified, not assumed
- [ ] Circle scaled via `transform: scale()` only, fixed `vmax` diameter
- [ ] Heading position/opacity read the same custom property the circle
      itself uses — no separate parallel tween
- [ ] Growth tween and pin release are two separate `ScrollTrigger`s
- [ ] Pin release point is derived from a visible target (e.g. "heading
      fully opaque"), not a guessed scroll fraction
- [ ] Both triggers anchored to one precomputed absolute scroll number,
      not `"top top"` on both
- [ ] `onLeave` clears the pinned element's lingering transform
      (`clearProps`) and settles any dependent element's position
- [ ] `onEnterBack` hands control back to live formulas for reverse-scroll
- [ ] Explicit z-index on the pinned element while active
- [ ] Reduced-motion and no-JS fallback render a correct static state
- [ ] Tested scrolling both forward AND backward through the full sequence
- [ ] Verified at a realistic (~700–900px) viewport height, not just a
      tall dev monitor

### Editorial compositions
- [ ] Text alignment follows image alignment, every time (§3)
- [ ] Alternating left/right per composition down the page
- [ ] Varied width per composition (not a fixed column)
- [ ] Tight image→heading gap, generous gap between compositions
- [ ] Sharp corners on editorial media (no border-radius)
- [ ] Deliberate decision made (and stated) on whether these compositions
      animate on scroll-reveal or render fully static (§12)

### Motion
- [ ] Vanilla IntersectionObserver reveal system in place for standard
      sections; GSAP reserved only for genuinely scroll-scrubbed sequences
- [ ] `prefers-reduced-motion` respected everywhere, with a real static
      fallback, not just `transition: none`
- [ ] Every animated property is `transform`/`opacity` only
- [ ] No animation runs if its enhancement script's preconditions fail
      (missing element, no GSAP, reduced motion) — verified by testing
      with the CDN script blocked

### QA pass before calling it done
- [ ] Full scroll-through at realistic viewport height, forward and back
- [ ] Console clear of errors on load and through the full scroll range
- [ ] Confirm no dead "coast" scroll space between any two sections
- [ ] Confirm every scroll-driven gap a stakeholder asked about is
      measured directly (via computed geometry), not eyeballed
- [ ] Confirm reduced-motion path renders correctly end to end
- [ ] Confirm no-JS path (or GSAP CDN blocked) renders correctly end to end
