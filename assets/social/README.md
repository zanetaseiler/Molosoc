# MOLOSOC social-post renderer

Deterministic, config-driven renderer that composites headline + supporting
copy onto the approved 4:5 lifestyle masters. No generative AI is involved in
producing type — every pixel of text comes from real font glyphs, laid out
and rasterized by code, so the same config always produces the same output
byte-for-byte.

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
   refuses to run if a master's hash doesn't match the manifest — that's the
   guard against a master ever being edited in place.
2. `config/template.json` defines the reusable part: canvas aspect
   (4:5, with a small drift tolerance rather than ever cropping to force it),
   the two brand typefaces (DM Serif Display for the headline, Mulish for
   the supporting line — same families as `site/theme/assets/css/tokens.css`),
   brand colors, and the default type scale/spacing as *fractions* of canvas
   width/height so it scales to any master at this aspect ratio.
3. `config/posts.json` defines the reusable-per-post part: which master to
   use, the headline lines, the supporting line, and the safe-zone box
   (as fractions of the canvas) where text is allowed to sit for that photo.
   Copy and layout never touch `src/*.mjs` — a new post is a new JSON entry.
4. `src/textMetrics.mjs` measures real glyph advances (via `fontkit`, reading
   the actual font files) so line widths are exact, not estimated.
5. `src/buildSvg.mjs` lays the headline + supporting line + wordmark out
   inside the post's safe-zone box at their **configured sizes — fixed, not
   auto-shrunk**. It only measures (via real glyph metrics) to validate: the
   headline block must clear `template.guards.minHeadlineBlockWidth/Height`,
   and the full lockup must not exceed the safe-zone box. Either failing
   throws instead of silently shrinking the type — a too-small safe zone or
   too-long copy is a config bug to fix, not something to paper over by
   quietly rendering a smaller headline than the brief calls for.
6. `src/render.mjs` rasterizes that SVG with `@resvg/resvg-js` (a
   deterministic Rust SVG renderer, not a browser) and composites it over the
   untouched master with `sharp`. Compositing only writes pixels where the
   overlay has alpha > 0 — everywhere else in the output is bit-identical to
   the master (verified for `MOL_POST_001_EN`: the only pixels that differ
   from the source master are inside the text block itself).

## Master handling

- `masters/*.png` are working copies of the Drive files, not edited copies —
  see `masters/MANIFEST.json` for the Drive file ID and sha256 of each.
- Adding a new master: download it from the Drive folder, drop it in
  `masters/` unmodified, add its filename + sha256 + dimensions to
  `MANIFEST.json`. Never re-save/re-export it through an image editor first.
- `render.mjs` throws before rendering if a master's aspect ratio drifts more
  than `template.canvas.aspectTolerance` from 4:5, or if its hash doesn't
  match the manifest. Both are fail-loud, not silent-crop, checks.

## Fonts

`fonts/*.ttf` are the brand typefaces (DM Serif Display, Mulish), converted
from the `@fontsource` npm packages' WOFF2 files to plain TTF so
`@resvg/resvg-js`'s font loader (which needs SFNT/TTF, not compressed WOFF)
can load them directly, with no network fetch at render time — this is what
makes the render reproducible in GitHub Actions. Same OFL-licensed glyphs,
just a different container format.

## Running it

```bash
cd assets/social
npm ci
npm run render                  # renders every post in config/posts.json
node src/render.mjs MOL_POST_001_EN   # renders just one post id
```

Output PNGs land in `output/<post-id>.png`. In CI
(`.github/workflows/social-render.yml`) they're uploaded as a build artifact
rather than committed on every run; `output/MOL_POST_001_EN.png` is committed
here as the first reviewable preview.

## Adding post 002 onward

1. Add the master to `masters/` + `MANIFEST.json` (see above).
2. Add an entry to `config/posts.json` with its headline/supporting copy and
   a safe-zone box chosen by eye for that photo's negative space (crop the
   master and look at it before picking numbers — don't guess blind).
3. `node src/render.mjs <new-id>` and look at the output.

Nothing in `src/` should need to change for a normal new post; if it does,
that's a sign the config schema needs to grow, not the renderer's logic.
