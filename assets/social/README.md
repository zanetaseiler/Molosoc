# MOLOSOC social-post renderer

Deterministic, config-driven renderer that composites headline + supporting
copy onto the approved 4:5 lifestyle masters. No generative AI is involved in
producing type — every pixel of text comes from real font glyphs, laid out
and rasterized by code, so the same config always produces the same output
byte-for-byte.

**Everything is manually authored, nothing is auto-placed.** An earlier
version of this renderer computed a "safe zone" from fractions of the canvas
and shrank text to fit it — that produced inconsistent sizing and layouts
that didn't actually match each photo's negative space. This version has no
such logic anywhere: every position and size in `config/layouts.json` was
chosen by looking at that specific photo (see the `_rationale` field on each
entry) and typed in as an absolute pixel value. The renderer's only job is to
place things exactly where told and refuse to render if that violates a hard
boundary — never to calculate a layout or shrink one that doesn't fit.

## Why this exists

The 20 approved masters in Google Drive
(`https://drive.google.com/drive/folders/1FbiYmcjB7eGMxgZzanFGWZu66dHimCXD`)
are read-only source photography. This renderer never edits, crops, resizes,
recompresses, or overwrites them — it only reads them and paints a
transparent text overlay on top. See "Master handling" below for how that's
enforced, not just promised.

## How it works

1. `masters/` holds byte-identical copies of the approved Drive masters,
   fingerprinted in `masters/MANIFEST.json` (sha256 per file). `render.mjs`
   refuses to run if a master's hash doesn't match the manifest.
2. `config/design-system.json` is the **locked global system** — the same for
   every post, never varied: fonts (DM Serif Display / Mulish, same families
   as `site/theme/assets/css/tokens.css`), font weights, the four fixed
   colors, wordmark text/size/tracking, divider thickness/width, and the
   global `minEdgePadding` (55px) every element must clear on every canvas
   edge. No blur, gradient, background panel, or shadow is implemented
   anywhere in this system — there's no code path that could draw one.
3. `config/copy.json` holds **only** copy — headline lines, which line gets
   the accent color, and the supporting line — keyed by image id (`MOL_IMG_001`
   etc). A post's copy can only come from its own id; there's no shared
   "default copy" a post could accidentally inherit.
4. `config/layouts.json` holds **only** the manually-authored per-image
   layout: which master, the headline's text box (`x`, `y`, `width`,
   `maxHeight` — a hard cap, not a fitting target), `headlineFontSize` /
   `headlineLineHeight`, `supportFontSize` and its position, and the
   divider/wordmark positions. Only images with an entry here can be
   rendered — everything else fails with "no entry in layouts.json" rather
   than falling back to some computed guess.
5. `src/textMetrics.mjs` measures real glyph advances (via `fontkit`, reading
   the actual font files) so line widths used in validation are exact.
6. `src/buildOverlay.mjs` takes the copy + layout + design system and does
   two things, in order: **validate**, then **draw**. Validation checks (all
   hard failures, not warnings):
   - every headline line's measured width fits inside `textBox.width`;
   - the headline block's total height fits inside `textBox.maxHeight`;
   - the headline box, supporting text, divider, and wordmark each clear
     `minEdgePadding` (55px) on all four canvas edges.

   There is no shrink-to-fit anywhere — a violation throws immediately,
   naming the post and the exact overflow, instead of silently rendering a
   smaller or misplaced headline.
7. `src/render.mjs` also asserts the declared font files exist on disk before
   rendering (no system-font fallback is possible — `loadSystemFonts` is
   always `false`), and after rasterizing, reads back the overlay's alpha
   channel in each text region to confirm it actually contains ink — a guard
   against a font silently failing to match and rendering blank.
8. Compositing (`sharp`) only writes pixels where the overlay has alpha > 0 —
   everywhere else in the output is bit-identical to the master. This is
   re-verified for every render with an external pixel diff against the
   source master (not just trusted).

## Master handling

- `masters/*.png` are working copies of the Drive files, not edited copies —
  see `masters/MANIFEST.json` for the Drive file ID and sha256 of each.
- Adding a new master: download it from the Drive folder, drop it in
  `masters/` unmodified, add its filename + sha256 + dimensions to
  `MANIFEST.json`. Never re-save/re-export it through an image editor first.
- **Cross-check the live Drive folder, not just the inventory doc.**
  `MOLOSOC_Approved_Image_Masters_Inventory.md` was found to be stale for
  `MOL_IMG_019` (it describes a different, landscape file than what's
  actually in the folder) — always confirm the actual current filename/id
  in Drive before adding a manifest entry.
- `render.mjs` throws before rendering if a master's aspect ratio drifts more
  than `design-system.json`'s `canvas.aspectTolerance` from 4:5, or if its
  hash doesn't match the manifest.

## Fonts

`fonts/*.ttf` are the brand typefaces (DM Serif Display, Mulish), converted
from the `@fontsource` npm packages' WOFF2 files to plain TTF so
`@resvg/resvg-js`'s font loader (which needs SFNT/TTF, not compressed WOFF)
can load them directly, with no network fetch at render time. Same
OFL-licensed glyphs, just a different container format.

## Running it

```bash
cd assets/social
npm ci
node src/render.mjs MOL_IMG_001:MOL_POST_001_EN_TEST.png
# multiple in one call:
node src/render.mjs MOL_IMG_001:out1.png MOL_IMG_005:out2.png
```

Each argument is `<image id>:<output filename>`. Output PNGs land in
`output/`.

## Adding another post

1. Add the master to `masters/` + `MANIFEST.json` (see above) if it isn't
   there yet.
2. Add its copy to `config/copy.json` (headline lines, `accentLineIndex`,
   supporting line).
3. **Look at the actual photo** (crop it, grid it, whatever it takes) and
   hand-author its entry in `config/layouts.json` — text box, font sizes,
   divider/brand position — based on where *that photo's* negative space
   actually is. Do not copy another post's numbers and assume they'll fit.
4. `node src/render.mjs <id>:<output>.png`. If it throws, the error names
   exactly which boundary was violated and by how much — fix the layout
   entry, don't work around the check.

As of this writing, `config/layouts.json` has entries for `MOL_IMG_001`,
`MOL_IMG_005`, and `MOL_IMG_019` only (manually-configured prototypes).
`config/copy.json` has all 20 images' copy ready, but the other 17 need a
layout entry authored the same way before they can render.
