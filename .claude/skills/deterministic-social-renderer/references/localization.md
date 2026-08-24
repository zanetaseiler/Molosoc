# Adding a second language to an existing render set

The template/crop/layout system was designed so translating a batch never
touches a master, a template choice, or a crop — only the copy and,
where the translated text genuinely doesn't fit, the text sizing. Follow
this order; skipping the first step is the single most common way a
localization pass goes wrong silently.

## 1. Check font glyph coverage BEFORE translating anything

A font file can "load" successfully in a renderer while still being
missing glyphs for characters outside whatever subset it was built with —
a missing glyph doesn't error, it just draws nothing. This is easy to miss
because it looks fine in every geometric/boundary check (those only care
about measured widths, and a missing glyph often measures as zero-width or
some fallback width) and only shows up as a blank gap in the actual
rendered pixels.

This bit hard in the project this skill was extracted from: the locked
brand fonts turned out to be a hand-trimmed Latin-only subset (241 glyphs)
missing every Czech caron/háček character. Before translating a single
line, run `missingGlyphs()` from `scripts/textMetrics.mjs` against a
sample string containing every special character the target language
uses:

```js
import { missingGlyphs } from './textMetrics.mjs';
const missing = missingGlyphs('fonts/HeadlineFont-Regular.ttf', 'áčďéěíňóřšťúůýž');
// non-empty => this font file cannot render this language safely
```

If glyphs are missing, the fix is usually **not** to substitute a
different font family (that changes the brand's look) — it's almost
always that the *same* font family has a full-coverage release somewhere
(most professionally-distributed type families, including the free ones
on Google Fonts, cover far more than a hand-picked subset would) and the
locked file in the project is just an incomplete cut of it. Before
swapping in a fuller version:

1. Confirm the replacement is metric-compatible with what's already
   rendered — same `unitsPerEm`, same ascent/descent, and identical
   advance width for every Latin glyph the existing renders actually use.
   fontkit exposes all of this (`font.unitsPerEm`, `font.ascent`,
   `font.descent`, `glyph.advanceWidth`).
2. If it matches, swap the file and re-render 2-3 already-approved posts
   from the existing (source) language. Diff the new output against the
   previously-approved PNG pixel-for-pixel. Byte-identical means the swap
   is safe — you've added coverage without changing anything anyone
   already signed off on. Any difference means stop and investigate before
   trusting it for the new language.

## 2. Translate for meaning and tone, not word-for-word

Preserve what the line is doing (a warm imperative, a short punchy accent
line, a question) rather than a literal translation. Keep the same
line-structure hierarchy the source language uses (how many headline
lines, which one is the accent color) unless the target language's
grammar makes that awkward.

## 3. Re-verify every post's text fit — don't assume the source layout still works

Different languages are rarely the same length for the same meaning.
Reusing the source layout's exact font size and line-breaks is the
default to *try*, but must be checked, not assumed:

1. Measure the translated headline's widest line at the source's exact
   font size against the source's exact `textBox.width` (same template,
   same crop — those never change for a translation).
2. If it fits with reasonable margin, done — nothing else about that
   post's layout needs to change.
3. If it doesn't fit, **try re-breaking the same translated words across
   the line count first**, before touching font size at all. Enumerate a
   few plausible line-break groupings (moving one word to the neighboring
   line, etc.) and measure each — often a different grouping alone fits at
   the exact same size the source language used.
4. Only if no re-break fits at the source size, reduce font size — by the
   smallest amount that clears the box with a real margin, found the same
   way the original size was (measure candidate sizes, don't guess). Note
   the reduction in whatever report goes back for review, with the actual
   before/after size, so a reviewer can judge whether it's still "large
   enough" rather than discovering a shrunk headline by surprise.
5. The supporting line can be wrapped across more lines than the source
   used (same mechanism as a same-language layout that needs it — see
   `supportLinesOverride` in SKILL.md) if it's long enough to need it. The
   renderer enforces that a wrapped support line reconstructs the exact
   translated sentence, just broken differently — never different words —
   so this is safe to lean on.

Never reduce a headline "aggressively" to force a stubborn line to fit
when a bit more room exists to try instead — e.g. widening the panel by a
few dozen pixels within the space actually available, or accepting the
one line that's slightly smaller than its neighbors because that's what
this specific phrase in this specific language needs. A visibly-cramped
headline reads as an afterthought; a small, disclosed, well-reasoned size
difference from the source language does not.

## 4. Recompute the whole text stack's vertical position, not just the headline

Headline block height changes when font size or line count changes, which
shifts where the support line, divider, and wordmark should sit beneath
it if the whole stack is meant to be vertically centered in its panel/band
(a common convention — see SKILL.md's stacking formula). Recompute the
stack's Y positions using the same centering method the source layout was
built with; don't reuse the source's exact Y pixel values if the block
above them changed height, and don't eyeball new ones either.

## 5. Keep locales in separate copy files, one shared layout file

One `copy.json` per locale (`copy.json`, `copy_fr.json`, `copy_de.json`,
...), each with the exact same set of image-id keys. Layouts live in the
single shared `layouts.json` — give a locale that needed different
sizing its own named variant per post (e.g. `final` for the source
language, `finalFr` for French) rather than a separate layouts file, so
the parts that stayed identical (template, crop, textAreaBounds,
divider/wordmark position) are visibly shared, not duplicated and left to
drift.

Keep locale outputs in clearly separate folders (`output/en/`,
`output/fr/`) so a batch delivery never mixes languages in one directory.
