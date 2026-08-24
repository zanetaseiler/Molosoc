# MOLOSOC English Social Set — Batch 1 (Posts 001–010)

Template legend: **TEMPLATE_SIDE** = cream text panel left / photo right. **TEMPLATE_BOTTOM** = photo top / cream text panel bottom. No text is ever placed directly on a photograph in this set.

| Post | Source master | Template | Headline |
|---|---|---|---|
| MOL_POST_001_EN | MOL_IMG_001_floor-journaling.png | TEMPLATE_BOTTOM | "Care that / fits real / life." |
| MOL_POST_002_EN | MOL_IMG_002_yoga-mat-roll.png | TEMPLATE_BOTTOM | "Care that / keeps up / with you." |
| MOL_POST_003_EN | MOL_IMG_003_reading-chair.png | TEMPLATE_SIDE | "A little care. / A little / quiet." |
| MOL_POST_004_EN | MOL_IMG_004_vacuuming-living-room.png | TEMPLATE_BOTTOM | "Self-care / while life / happens." |
| MOL_POST_005_EN | MOL_IMG_005_kitchen-prep.png | TEMPLATE_BOTTOM | "Simple care / fits right / in." |
| MOL_POST_006_EN | MOL_IMG_006_home-office.png | TEMPLATE_SIDE | "Your feet / work all / day too." |
| MOL_POST_007_EN | MOL_IMG_007_armchair-coffee-book.png | TEMPLATE_SIDE | "Slow down. / Your feet / can too." |
| MOL_POST_008_EN | MOL_IMG_008_kitchen-flowers.png | TEMPLATE_BOTTOM | "Small rituals / matter / too." |
| MOL_POST_009_EN | MOL_IMG_009_armchair-cream.png | TEMPLATE_BOTTOM | "Take a moment. / Keep / going." |
| MOL_POST_010_EN | MOL_IMG_010_window-bench-journaling.png | TEMPLATE_SIDE | "A quiet / moment / counts." |

**Split:** 4 SIDE / 6 BOTTOM.

## Why each template was chosen

- **BOTTOM** was used where the composition depends on its full width — flanking furniture/props on both sides that are part of the scene's story (sideboard+table in 001, water bottle+sofa in 002, dining table+sofa with the vacuum wand crossing between them in 004, shelving+stove in 008) — or where the copy's own longest line doesn't fit a narrow column at a large size (009's "Take a moment.").
- **SIDE** was used where the subject reads as a single, fairly contained vertical figure that survives a narrower photo crop without losing the scene's key elements (003, 006, 007, 010).

## Headline sizes (no photo-avoidance math needed anymore)

Since text now lives entirely in its own cream panel/band and never touches the photo, the only ceiling on headline size is the panel's own width (SIDE, ~335px usable) or the band's shared width/height budget (BOTTOM, ~600–700px usable, height-shared with support/divider/wordmark below it). Sizes below are each image's real ceiling for its own copy — not a reduction made to dodge a face, hand, or product.

| Post | Template | Headline size |
|---|---|---|
| 001 | BOTTOM | 93px |
| 002 | BOTTOM | 93px |
| 003 | SIDE | 61px |
| 004 | BOTTOM | 93px |
| 005 | BOTTOM | 93px |
| 006 | SIDE | 82px |
| 007 | SIDE | 62px |
| 008 | BOTTOM | 93px |
| 009 | BOTTOM | 88px (widened text box to 700px so this copy's longer line still gets a large size) |
| 010 | SIDE | 86px |

SIDE's headline ceiling (61–86px) is consistently smaller than BOTTOM's (88–93px) — an honest consequence of the SIDE panel being ~40% of canvas width vs. BOTTOM's full width, not inconsistent treatment.

## Quality checks performed on every render

- Master sha256 verified against `masters/MANIFEST.json` before every render (all untouched).
- Every photo region is a lossless `sharp` in-memory crop of its master — no resize/distort, no recompression artifacts introduced.
- `buildOverlay.mjs`'s boundary checks validate text against the cream panel/band's own edges (`textAreaBounds`), not the full canvas — text cannot geometrically reach the photo region on any of these 10 renders (all passed).
- Post-render ink-presence check confirms every text element actually rasterized (no silent blank text from a font-load failure).
- Rounded outer corners (32px radius) applied via an alpha mask on the final composite only — nothing is drawn over the photo or text to achieve it.
- Fonts: DM Serif Display (headline), Mulish (support/wordmark) — same locked font files as every prior post, no substitution.
- Colors: charcoal `#171719` (headline/support/wordmark), warm beige `#E8D1A6` (accent line + divider), cream `#F8F7F4` (panel/band background, matches the site's own `--color-cream` token) — unchanged from the approved system.
