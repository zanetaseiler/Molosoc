# Choosing and sizing TEMPLATE_SIDE vs TEMPLATE_BOTTOM

Two templates cover the vast majority of a real batch. Reach for a third
(TEMPLATE_FULL, text directly on the photo) only when a specific photo has
large, genuinely clean negative space nowhere near a face, hands, or the
product — never as the default, and never because "the batch needs
variety." The whole point of SIDE/BOTTOM is that they make the
face/hands/product-avoidance problem disappear by construction: text lives
in its own solid-color panel or band, physically separate from the photo,
so there is no obstacle to dodge and no boundary check that depends on
where a person happens to be standing in the frame.

## The decision heuristic

Ask one question: **does this photo's composition need its full width to
read?**

- **Full width needed → TEMPLATE_BOTTOM.** Props or context flank the
  subject on both sides (a kitchen scene with a table on the left and a
  window on the right, a wide activity shot), or the subject/action itself
  spans most of the frame's width. Cropping into a narrower side panel
  would cut into one side's story or force an awkward crop through the
  subject. The full-width photo stays on top; the text band below has the
  freedom to run wide, so it usually supports a larger headline than SIDE
  does for the same copy.

- **Contained/vertical subject → TEMPLATE_SIDE.** A single figure or
  object that reads fine cropped to roughly 55-65% of the frame's width —
  seated, standing centrally, a product on a surface — survives having one
  side trimmed for the panel. SIDE's panel is narrower than BOTTOM's band
  (a fraction of canvas *width* vs. a fraction of canvas *height* on a
  portrait-oriented canvas), so it caps headline size lower for the same
  copy. That's an honest consequence of the panel's geometry, not a defect
  — don't compensate by force-fitting SIDE onto a photo that wants BOTTOM.

When genuinely unsure, render both and compare — but decide, don't hedge:
ship one template per post, not two "just in case." If a specific post's
copy has an unusually long line and TEMPLATE_SIDE's width forces that line
below a comfortable size while TEMPLATE_BOTTOM handles it fine at a normal
size, that in itself is a legitimate reason to pick BOTTOM for that post —
see "the copy can change the answer" below.

## Why geometry is a ratio, not a fixed pixel size

A real photo set is very rarely one uniform size. Master images arrive at
whatever size the photographer/generator produced, and different batches
or reshoots often land on a different native size than the first batch
did. If `photoPanelWidthRatio` / `photoBandHeightRatio` were fixed pixel
values, every master that isn't exactly the size the constants were tuned
for would either need upscaling (never do this — it's the one thing that
must never happen to a master) or would composite with visible seams.

Storing the ratio and computing `photoPanelWidth = round(canvasWidth *
photoPanelWidthRatio)` (and the mirror for BOTTOM) fresh per master means
the SAME two templates work unmodified across every native size a photo
set contains, with the canvas always exactly equal to that master's own
width/height — never resized, never upscaled, never letterboxed.

## Picking a photoCrop within a template's fixed panel size

Once the template's ratio fixes exactly how wide the photo panel (SIDE) or
tall the photo band (BOTTOM) has to be for a given master, the only
remaining decision per photo is *which* region of the master to show in
that fixed-size window — you're panning a fixed-size crop window over the
master, not choosing its size.

- **SIDE**: pick `photoCrop.x` (height is always the full master height,
  never cropped vertically) so the fixed-width window contains the subject
  with the composition you want, trimming whichever side(s) matter least
  (usually background, secondary props).
- **BOTTOM**: pick `photoCrop.y` (width is always the full master width) —
  usually `0` (top-crop, trimming the bottom of the frame) works because
  the subject's head/face is near the top of most product photography, but
  check this per photo rather than assuming it. If a subject's key
  content (head, product) is unusually low in frame, computing the crop
  window that keeps a body's head-to-important-detail span decently
  centered can matter more than defaulting to y=0 — measure the two
  y-coordinates you actually need to keep in frame (real pixel numbers,
  not eyeballed from a thumbnail) before picking `photoCrop.y`.

## Disclose crop trade-offs, don't hide them

A fixed-size crop window sometimes can't include everything you'd like —
e.g. a subject's face AND a product visible near their feet, when the
vertical distance between them exceeds the band height. When that happens:

1. Work out which end is the photo's actual hero content (usually a face —
   check the brief) and keep that fully in frame.
2. Say so explicitly in the layout's `_notes` field and in whatever report
   you hand back for review — "kept her face in frame with margin; the
   product is visible but cropped to its upper half because the two are
   1170px apart in a 940px band" is a fine, honest trade-off. Silently
   shipping a crop that cuts off the product without saying so is not.

## Sizing the headline once the template is chosen

With SIDE/BOTTOM, there's no face/hands/product to dodge inside the text
area — the panel is empty brand color. That means headline size is purely
a text-fitting problem: the largest font size whose widest line still
clears the panel/band's own width (and whose block height clears its own
maxHeight), found by real glyph-width measurement (see
`scripts/textMetrics.mjs`'s `measureWidth`), never guessed. Search
candidate sizes and keep a real safety margin (a few pixels of slack, not
a razor-thin exact fit) rather than the absolute maximum that barely
passes — rendering environments and font hinting can shift a pixel or two,
and future copy edits shouldn't immediately break a layout that was tuned
to the exact boundary.
