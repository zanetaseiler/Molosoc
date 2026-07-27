# Molosoc — Animation Specification

This document defines all motion language for the Molosoc website.
Animations exist to improve storytelling. Never animate for decoration.

---

## Overall Feeling
Motion should feel:
- elegant, premium, natural
- slow enough to notice, fast enough to never frustrate
- invisible when unnecessary

**Inspiration:** Apple product launches, luxury hotel websites, premium architecture
studios, high-end skincare brands, editorial experiences.
**Not:** gaming, flashy agency demos, overly playful effects.

---

## Scroll Behaviour
- Smooth scrolling, natural momentum, no abrupt jumps.
- Every transition should feel intentional.

---

## Section Transitions
Each major section should transition like **entering another room**. Use combinations of:
- Fade
- Scale
- Depth
- Parallax
- Opacity

Never dramatic. Never distracting.

---

## Hero Section
The hero is emotional. Allow subtle movement. Examples:
- soft floating background
- gentle light movement
- slow parallax
- very subtle image reveal

The product should remain the visual focus.

**Documented exception — hero-to-section circular transition:** the
scroll-pinned circle transition carrying the hero into the following story
section (`assets/js/arc-reveal.js`) scales a shape from ~2% to 100%, well
outside the 98–100% range in Image Motion below. This is intentional: the
circle isn't "an image revealing," it's a full scene transformation — one
section becoming the next, not a small element easing into place. It still
follows every other rule here (scroll-scrubbed not time-based, no bounce/
overshoot, `--ease-in-out: cubic-bezier(0.76, 0, 0.24, 1)` — a symmetric,
monotonic curve, slower and more restrained than the site's default
`--motion-ease`). Treat this as the one place scale range is allowed to
depart from the general Image Motion guidance; it should stay a rare
exception, not a precedent for other sections.

---

## Image Motion
Images should reveal naturally. Examples:
- fade in
- soft upward movement
- scale from 98% to 100%
- mask reveal

Never fly in. Never bounce. Never rotate.

---

## Text Animation
**Preferred:** fade, blur-to-sharp, opacity, small translateY.
**Avoid:** letters flying in, typing effects, crazy stagger timing.

---

## Product Animations
The product deserves premium attention. Use:
- soft zoom
- light reveal
- shadow refinement
- micro parallax

Never spin products. Never rotate continuously. Never exaggerate.

---

## Hover Effects
Hover effects should communicate quality. Examples:
- soft elevation
- shadow refinement
- image zoom 2–4%
- color transitions
- cursor feedback

Never dramatic.

---

## Buttons
- Fast response, subtle press, soft hover.
- No excessive glow.

---

## Cards
- May lift slightly, shadow changes, very small movement.
- No bouncing.

---

## Performance
- Motion must remain smooth.
- Prefer GPU-accelerated transforms (`transform`, `opacity`).
- Avoid layout shifts.
- Maintain high Lighthouse scores.
- Animations should degrade gracefully on slower devices.

---

## Accessibility
- Respect `prefers-reduced-motion`.
- Provide an alternative static experience.
- Never force animation.

---

## Mobile Motion
- Lighter animations than desktop.
- Avoid heavy parallax.
- Avoid scroll lag.
- Prioritize responsiveness.

**Documented exception — hero-to-section circular transition:** the
scroll-pinned circle transition (`assets/js/arc-reveal.js`, see the Hero
Section exception above) runs at all viewport widths, including mobile —
confirmed explicitly as an intentional override of "avoid scroll lag" here,
since this transition is the intended hero experience everywhere rather than
a desktop-only flourish. Its math is vmax/viewport-relative throughout, so
it doesn't need separate mobile tuning. Treat this alongside the Hero
Section exception as the one place mobile gets the same weight of motion as
desktop; it should stay a rare exception, not a precedent for other
sections.

---

## Motion Philosophy
Visitors should remember how the website made them feel — not the animations themselves.
Good motion is almost invisible.
