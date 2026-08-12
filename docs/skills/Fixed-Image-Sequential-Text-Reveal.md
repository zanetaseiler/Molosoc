# Fixed Image, Sequential Text Reveal

A reusable scroll-driven pattern: a stack of supporting text blocks (with
or without a photo alongside — the photo is optional) enters one at a time
from a chosen direction (left, right, up, or down), each gated to its own
scroll-progress threshold inside a pinned single-screen stage. The first
scroll into the section reveals the first block; each further scroll
reveals the next one in turn. If a photo is part of the section, it stays
completely static/fixed, never part of the animated set.

This is the pattern built for three sections on the Category page
(`site/theme/preview/category-preview.html` /
`site/theme/assets/js/sequential-text-reveal.js` /
`site/theme/assets/css/category.css`):

| Section | Direction | Fixed photo? |
|---|---|---|
| "Disposable sock masks vs. reusable foot covers" | right | yes |
| "What 'moisture-lock' actually means" | left | yes |
| "Reusable vs. disposable: the real cost" | up | no — plain 3-column stat grid |

It's also registered as a global Claude Skill (`fixed-image-text-reveal`)
so it can be pulled into other projects — this file is the project-local
copy of that same skill, kept in sync by hand, per this repo's existing
convention (see `Luxury-Wellness-Editorial-System.md` in this same folder
for the earlier example of a skill documented both globally and here).

**Who this is for:** anyone (agent or engineer) adding a similar
one-by-one-entrance section elsewhere on this site, or starting the same
pattern on a different project with zero prior context.

**Where the canonical write-up lives:** `~/.claude/skills/fixed-image-text-reveal/SKILL.md`
(plus `reference/vanilla-html-css-js.md` alongside it) — that version is
the one to read for the full mechanics, the rejected variants that shaped
the final design, the accessibility/responsive/performance rules, and the
mistakes already made and corrected. This file exists so the pattern is
discoverable from inside this project too, without needing access to the
user's global `~/.claude/skills/` directory.

---

## Quick summary (see the global SKILL.md for the full version)

1. **A fixed photo, if the section has one, never animates.** No
   `gsap.set()`, no entrance timeline, no threshold — it renders at
   `opacity: 1; transform: none;` from CSS alone and JS never selects it.
   (Two earlier variants tried giving it a scale/fade entrance and a
   slide-in-from-the-left entrance; both were explicitly reverted — see
   the global SKILL.md intro for why.)
2. **Each text/stat block starts parked off in its direction** (a small
   offset, ~70px, along `x` for left/right or `y` for up/down) and fully
   transparent, via `gsap.set()`.
3. **Direction is one setting per stage** (`data-slide-direction` on the
   section — `left`/`right`/`up`/`down`), not a separate copy of the
   script per direction — the same JS file drives every instance on the
   page independently.
4. **One `ScrollTrigger` per stage, pinned**, drives every block's
   visibility by comparing live scroll progress against that block's own
   threshold — never an `IntersectionObserver` (it fires everything at
   once inside a pinned stage) and never a plain linear scroll-scrub
   (reads as mechanical instead of "smooth arrival").
5. **The first threshold sits low** (~0.12) so the first scroll into the
   section already reveals the first block, not after some empty "warm-up"
   scroll distance.
6. **A heading (eyebrow + H2) belongs in normal document flow ABOVE the
   pinned stage, not inside it.** Heading + several text/stat blocks + an
   image can easily add up to more than 100vh at real viewport heights;
   keeping the heading in its own un-pinned block is what actually fixed
   that overflow (see "Overflow lessons" below) rather than fiddling with
   `align-items` on the pinned box.
7. **Reduced motion / no-JS / CDN failure** all render the exact same
   finished state: every block already at its resting position/opacity —
   nothing is ever stuck half-animated.

## Overflow lessons learned building this (worth reading before reusing)

Getting the pinned stage to never clip its own content took three passes:

1. `align-items: center` on the stage centered overflowing content
   vertically, pushing the **heading** above the visible box, where
   `overflow: hidden` clipped it off entirely.
2. Switching to `align-items: flex-start` fixed the heading but, once
   content was still taller than 100vh, pushed the overflow to the
   **bottom** instead — the last text block ended up clipped/unreadable
   there.
3. The actual fix: pull the heading out of the pinned stage into its own
   normal-flow block above it (`.molosoc-sequential-heading`). That alone
   freed enough height. Where an image is also present and its own
   aspect-ratio math is the tall part (a wide grid column at 4:5 can
   easily exceed the remaining budget), cap it with `max-height: calc(100vh - <stage's own padding total>)` on the image wrapper — width
   follows automatically to preserve the ratio.

## This project's implementation

- Markup: `.molosoc-sequential-heading` (+ `__inner`) for each section's
  un-pinned heading block; `.molosoc-sequential-stage` for the pinned
  frame, with `data-slide-direction="left" | "right" | "up"`;
  `.molosoc-sequential-entrance--text` on every block that should animate
  in (a text/argument item, or a `.molosoc-pillar` stat card — the class
  doesn't care which).
- CSS: `.molosoc-sequential-heading`, `.molosoc-sequential-stage`,
  `.molosoc-sequential-entrance--text`, and the image `max-height` cap, all
  in `site/theme/assets/css/category.css`.
- JS: `site/theme/assets/js/sequential-text-reveal.js` — queries every
  `.molosoc-sequential-stage` on the page and sets each one up
  independently, reading its own direction from its `data-slide-direction`
  attribute. This is the project's concrete instance of the reference
  implementation in the global skill's `reference/vanilla-html-css-js.md`.
