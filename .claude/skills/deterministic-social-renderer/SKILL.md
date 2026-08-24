---
name: deterministic-social-renderer
description: Build a code-based (sharp + resvg-js + fontkit, Node.js), pixel-exact pipeline that composites branded headline/support text onto real product or lifestyle photography for a batch of social posts — never by asking an image-generation model to draw the text, and never by eyeballing pixel positions. Use this whenever someone wants to turn a folder of approved photos into a set of on-brand social graphics with a headline, a support line, and a small wordmark; wants that text to never cover a face, hands, or the product; wants the same exact layout system reused consistently across many images (and, if asked, translated into other languages without redoing the design); or describes a workflow with an "approved masters" folder, a design system / style guide to lock in, or a batch that needs a contact sheet and manifest handed back for review before continuing. Trigger even if the user doesn't say "renderer" or "pipeline" explicitly — phrases like "turn these product photos into Instagram posts," "add our branding text to this photo set," "make a batch of on-brand social graphics from these images," or "localize our social posts into French" all mean this. Do NOT use this for a single one-off graphic, a poster/flyer/carousel built as one HTML artifact, or a request where the text is meant to sit ON TOP of the photo in a freeform/artistic way — those want a design or artifact skill instead. This skill is specifically for a REPEATABLE, boundary-checked, multi-image batch system.
---

# Deterministic Social Renderer

Composite on-brand headline/support text onto real photography with code,
not with a model's guess at where text should go. The system in this
skill was extracted from a production pipeline that rendered 20 posts in
two languages against a locked design system, catching real mistakes
(text that would have overlapped a hand, a font silently missing glyphs
for a second language) before they shipped — because every placement is
checked against real numbers, not judged by eye.

## Why code, not an image model, and why fail-fast, not shrink-to-fit

Asking an image-generation model to "add this headline to this photo" is
fast but non-deterministic: the same prompt can place text differently
each time, drift off-brand, or quietly overlap a face. This skill instead
treats the composite as **arithmetic**: measure the actual glyph widths
of the actual copy at a candidate font size, using the actual font file
(`scripts/textMetrics.mjs`, backed by `fontkit`), and place text at exact
pixel coordinates read straight from a config file — nothing is drawn by
guesswork, so the same config always produces the same output, and a
different Claude session (or the same one, a week later) reruns it and
gets the identical file, not a fresh interpretation.

Because it's arithmetic, a layout either fits or it doesn't — there's no
"close enough" for a computer to shrink into. `scripts/buildOverlay.mjs`
throws a `LayoutViolation` the instant text would extend past its
allotted box, rather than silently reducing the font size or nudging the
position to make it pass. This is the single most important behavior to
preserve if you adapt this system: **a layout that doesn't fit is a bug to
fix by hand in config, not a render to quietly degrade.** An
auto-shrunk headline you never see happen is how a whole batch ends up
inconsistently sized without anyone deciding that on purpose.

## The two templates — and why only two

Real product/lifestyle photography has faces, hands, and products
scattered unpredictably across the frame. Trying to place text directly
on top of a photo while dodging all of that, image by image, is exactly
the kind of judgment call that degrades over a large batch. This system
sidesteps the problem by construction with two reusable templates that
put text in its own solid-color space, physically separate from the
photo:

- **TEMPLATE_SIDE** — a solid brand-color panel beside a cropped photo
  (photo fills the rest of the canvas). Good for a single, fairly
  vertical/contained subject that survives a narrower crop.
- **TEMPLATE_BOTTOM** — the photo on top (cropped to a fixed band height),
  a solid brand-color band below it holding the text. Good when the
  composition needs its full width to read.
- **TEMPLATE_FULL** (use sparingly) — text directly on the full photo,
  only when that specific photo has real, wide-open negative space nowhere
  near the subject. This is the one case closest to what most people
  picture by default; resist reaching for it as the default here — it
  reintroduces the exact per-photo obstacle-dodging problem the other two
  templates exist to eliminate.

Read `references/templates.md` before authoring the first layout — it
covers the SIDE-vs-BOTTOM decision heuristic, why panel/band geometry is
stored as a ratio of each master's own size (not a fixed pixel value —
this matters the moment your photo set has more than one native size),
and how to disclose an unavoidable crop trade-off instead of silently
picking one.

## Project layout

Set a new project up like this (copy the bundled scripts/assets as a
starting point, don't rewrite them from scratch):

```
your-project/
├── masters/                  # read-only source photos — never edited, ever
│   └── MANIFEST.json         # sha256 + dimensions per master, verified before every render
├── config/
│   ├── design-system.json    # LOCKED globals: colors, fonts, padding, template ratios
│   ├── layouts.json          # per-post: template choice, crop, text position/size
│   └── copy.json             # per-post: headline lines, accent line, support line
├── src/
│   ├── render.mjs            # CLI entry point
│   ├── buildOverlay.mjs      # boundary checks + SVG text generation
│   └── textMetrics.mjs       # real glyph-width measurement
├── fonts/                    # the exact font files locked in design-system.json
└── output/                   # rendered PNGs land here
```

Copy `scripts/render.mjs`, `buildOverlay.mjs`, `textMetrics.mjs`, and
`package.json` into `src/`, then `npm install`. Copy
`scripts/add_master.mjs` in too (it can live in `src/` alongside the
rest, but always run it from the project root — it looks for
`masters/MANIFEST.json` relative to the current directory). Copy
`assets/*.example.json` into `config/` and
`masters/MANIFEST.json`, strip the `_comment`/`_note` fields once you
understand them, and fill in real values.

## The locked design system vs. per-post layout — never mix these

This split is the backbone of the whole system:

- **`config/design-system.json`** — global constants. Colors, font
  files/families, edge padding, corner radius, and each template's
  geometry ratio. Every value here applies to every post identically and
  is never derived from an image or computed automatically. If a value
  would need to change to accommodate one specific photo, it doesn't
  belong here — that's a `layouts.json` decision.
- **`config/layouts.json`** — one manually-authored entry per post
  (keyed by image id, then by a variant name like `final`). Crop
  coordinates, text box position and size, font size, line breaks. Every
  value here was chosen by actually looking at that specific photo.

Keeping these separate is what makes the batch consistent: a brand color
or font change happens in exactly one place, while a crop or size tweak
for one stubborn photo never leaks into any other post's rendering.

## Sizing text: measure, don't guess

For any text element (headline, support line, wordmark), the workflow is
always the same, and it's the one piece of this system worth doing by
hand-computation rather than eyeballing:

1. Know the box: the panel/band's usable width (its full width minus
   `minEdgePadding` on both sides) and, for the headline block, its
   available height.
2. Call `measureWidth(fontPath, text, candidateSize, letterSpacing)` from
   `textMetrics.mjs` at a range of candidate sizes — it returns the real
   rendered width using the actual font file's glyph advances (kerning
   included), not an estimate from character count.
3. Pick the **largest** size whose widest line still clears the box with
   a real safety margin (a handful of pixels, not the exact boundary).
4. If nothing reasonable fits: try re-breaking the copy across a
   different line-break grouping *before* reducing size — often a
   different word grouping alone solves it at the original size. Only
   reduce size as a last resort, and only by as much as the text actually
   requires — never round down to some arbitrary smaller value "to be
   safe." A disclosed, minimal, well-reasoned size difference between two
   posts in a batch is normal (different copy, different available
   space); an unexplained one looks like an accident.

`buildOverlay.mjs`'s boundary checks are the safety net that catches a
mistake in this process — not a substitute for doing it. Getting a
`LayoutViolation` on first render of a new post is expected and fine;
getting one on a post you thought was already finished usually means a
config value drifted from what was actually measured.

## Master image integrity

Source photography is the one thing in this whole system that must never
change. Every master listed in `masters/MANIFEST.json` carries a sha256
hash; `render.mjs` recomputes it and refuses to render if it doesn't
match — this catches an accidental overwrite, a re-export at different
compression, or someone dragging a "similar but not the same" file into
the folder with the same name. Add a new master with
`scripts/add_master.mjs <path>`, never by hand-editing the manifest.

Every photo region that ends up in a rendered post is a **lossless
in-memory crop** — `sharp().extract()` piped straight to `.png()`, never
a resize. This is also why `.png()` is called explicitly even when the
source file is (confusingly) a `.jpg`-content file with a `.png`
extension: without it, `sharp` would re-encode the extracted buffer in
whatever format the source bytes actually are, silently reintroducing
lossy compression into a crop that's supposed to be pixel-identical to
the source.

## Verifying a render actually worked

Two checks worth doing on every render, not just trusting "it didn't
throw":

1. **Ink-presence check** (already built into `render.mjs`,
   `assertInkPresent`): reads back the rendered overlay's alpha channel in
   each text region and fails if any region drew zero visible pixels. This
   catches a font that "loaded" without erroring but had no matching
   glyphs for the text — which is exactly what happened with a missing
   diacritic in a second-language render (see
   `references/localization.md`). A geometric boundary check alone would
   never catch this; only actually looking at the rendered pixels does.
2. **Regression pixel-diff**, whenever you touch anything shared (a font
   file, `design-system.json`, the renderer code itself): re-render 2-3
   already-approved posts and diff them byte-for-byte against the
   previously-approved PNGs. Identical means the change was safe;
   anything else means stop and find out why before trusting it for new
   work.

## Deliverables for a batch

Hand back three things alongside the rendered PNGs, every batch:

1. **A contact sheet** — `scripts/contact_sheet.py out.png img1.png
   img2.png ... --cols 5` builds a labeled thumbnail grid. This is what
   a reviewer actually looks at first; don't make them open 20 individual
   files to get a sense of the whole batch.
2. **A manifest** — one JSON row per post: source master filename,
   template used, the actual copy rendered, output filename. This is the
   paper trail for "which photo/template/copy produced this file," useful
   the moment someone asks to tweak just one post later.
3. **A short report** — which template each post used and why (see
   `references/templates.md`'s heuristic), any disclosed crop trade-off,
   and any headline size that came out notably smaller than its
   neighbors and why.

## Batch discipline: render, verify, STOP

Don't render an entire large set speculatively and present it all at
once. Work in reviewable batches (10 is a reasonable default for a
20-40 image job; adjust to what's actually being asked): render a batch,
run the verification checks above, do a visual spot-check of a few
posts, hand back the batch's deliverables, and **stop for approval**
before starting the next batch. If a request explicitly says to continue
through the whole set without stopping, do that instead — but the default
is to pause, because a systemic mistake (a color, a template rule
misapplied, a copy error) is far cheaper to catch after 10 renders than
after 40.

## Adding a language

The template/crop/layout choices never change for a translation — only
the copy, and, where the translated text genuinely doesn't fit, the
sizing. This has one non-obvious first step (checking the locked font
files actually have glyphs for the new language, before translating
anything) and several judgment calls after that about when to re-break
lines vs. reduce size vs. widen a box. Read
`references/localization.md` in full before starting a second-language
pass — skipping the font-coverage check is the most common way this goes
wrong, and it fails silently (blank text, not an error) if you skip it.
