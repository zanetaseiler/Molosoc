# MOLOSOC English Social Set — Batch 2 (Posts 011–020)

Template legend: **TEMPLATE_SIDE** = cream text panel left / photo right. **TEMPLATE_BOTTOM** = photo top / cream text panel bottom. No text is ever placed directly on a photograph.

## Masters pulled from Drive this round

013, 014, 015, 016, 017 were missing from the local `masters/` folder and have been downloaded from the approved Drive folder, verified (local file size matches Drive's reported size exactly), and added to `masters/MANIFEST.json` with their sha256 and Drive file ID. Masters are read-only; none were cropped, resized, or recompressed.

Two of these introduced a second and third native master size into the set — the renderer's template geometry (previously computed only for 1122×1402) now derives panel/band size as a **ratio** of each master's own dimensions, so this works for any master size without ever resizing a photo:

| Master family | Posts | Canvas |
|---|---|---|
| 1122×1402 (original) | 011, 012, 013, 014, 019 | — |
| 1126×1397 (near-4:5, 0.76% off) | 015 | — |
| 928×1152 (second native size) | 016, 017, 018, 020 | — |

## Template choices

| Post | Source master | Template | Headline |
|---|---|---|---|
| MOL_POST_011_EN | MOL_IMG_011_bathroom-cream-routine.png | TEMPLATE_BOTTOM | "Care that / works with / your routine." |
| MOL_POST_012_EN | MOL_IMG_012_kitchen-island-slicing.png | TEMPLATE_BOTTOM | "Simple care. / Nothing / complicated." |
| MOL_POST_013_EN | MOL_IMG_013_counter-cream-jar.png | TEMPLATE_SIDE | "Start with / the cream / you love." |
| MOL_POST_014_EN | MOL_IMG_014_bedside-morning-coffee.png | TEMPLATE_BOTTOM | "Good mornings / start with / small rituals." |
| MOL_POST_015_EN | MOL_IMG_015_bathroom-relaxing.png | TEMPLATE_SIDE | "Care should / feel this / easy." |
| MOL_POST_016_EN | MOL_IMG_016_daybed-window-view.png | TEMPLATE_BOTTOM | "Nothing to do / but let your / cream stay put." |
| MOL_POST_017_EN | MOL_IMG_017_feet-closeup-bench.png | TEMPLATE_BOTTOM | "Made for / the cream / you already use." |
| MOL_POST_018_EN | MOL_IMG_018_sofa-relaxing.png | TEMPLATE_SIDE | "Put your / feet up. / Literally." |
| MOL_POST_019_EN | MOL_IMG_019_watering-plants.png | TEMPLATE_BOTTOM | "Care that / moves with / you." |
| MOL_POST_020_EN | MOL_IMG_020_floor-reading-sheepskin.png | TEMPLATE_BOTTOM | "Care doesn't / have to feel / like work." |

**Batch 2 split:** 3 SIDE / 7 BOTTOM. **Full 20-post set:** 7 SIDE / 13 BOTTOM.

- **SIDE** (013, 015, 018) went to photos where the subject is a contained, fairly vertical pose that survives a narrower photo crop.
- **BOTTOM** was used everywhere the scene needs its full width (011's bathroom vanity+plant, 012's dining table+cabinets, 014's nightstand+bed, 016's window view, 019's flanking plants), or where the copy's longest line doesn't fit a narrow SIDE column at a large size (020: "have to feel" only fits SIDE below ~48px — rejected per the "never shrink to force a worse layout" rule — so it went to BOTTOM instead, same as batch 1's post 009).
- 017 is already a tight detail crop (legs/feet, no face) — BOTTOM keeps its full width intact.

## Disclosed crop trade-offs (BOTTOM only)

TEMPLATE_BOTTOM's photo band height is fixed by ratio (≈67% of canvas height) — for three posts, the subject's head and her socked feet are too far apart vertically to both fit with margin:

- **011**: head (y≈15) to sock (y≈900–1250) spans 1235px against a 939px band. Kept the head, robe, and the actual cream-application gesture in full; the sock is cropped down to its ankle.
- **014**: head (y≈100) to sock (y≈900–1270) spans 1170px against 939px. Kept her face, mug, and book in full; the sock is cropped to roughly its top third.
- **020**: head (y≈130) to sock (y≈830–950) spans ~820px against 772px (this master's smaller 928×1152 band). Kept her head with margin; only the sock's ankle is visible, the toe is cropped.

In every case this is a framing trade-off, not a rule violation — no text touches the photo, nothing is distorted, and the primary subject (face/action) is fully intact.

## Headline sizes

No face/hand/product-avoidance math anywhere in this batch — text lives entirely in its own cream panel/band. Sizes below are each post's real width- or height-bound ceiling for its own copy and its own master's panel geometry:

| Post | Template | Headline size | Ceiling reason |
|---|---|---|---|
| 011 | BOTTOM | 93px | standard 1122-family band |
| 012 | BOTTOM | 93px | standard 1122-family band |
| 013 | SIDE | 72px | 339px-wide panel |
| 014 | BOTTOM | 93px | widened text box to 700px so "Good mornings" still gets 93px |
| 015 | SIDE | 62px | 341px-wide panel (1126-family) |
| 016 | BOTTOM | 70px | 928-family band is shorter (380px vs. 463px) — scaled down proportionally |
| 017 | BOTTOM | 70px | same 928-family band |
| 018 | SIDE | 64px | 261px-wide panel — the 928-family's narrower SIDE column |
| 019 | BOTTOM | 93px | standard 1122-family band |
| 020 | BOTTOM | 70px | same 928-family band |

## Quality checks performed on every render

- Master sha256 verified before every render (all untouched, including the 5 newly-downloaded ones).
- Every photo region is a lossless in-memory crop — no resize/distort, no recompression.
- Boundary checks validate text against the cream panel/band's own edges (`textAreaBounds`) — text cannot geometrically reach the photo region. All 10 renders passed.
- Post-render ink-presence check confirms every text element actually rasterized.
- Rounded outer corners (32px radius) applied on the final composite only.
- Fonts, colors, and locked design-system values unchanged from batch 1 and from every prior approved post.

## Full-set manifest

`output/MANIFEST_EN.json` now covers all 20 posts (001–020) — source master, filename, template, and copy per post.
