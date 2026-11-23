# Black Friday landing hero — uploaded ad image (Issue #380)

Follow-up to #378 / PR #379. Applies to both Black Friday pages
(`/cz/black-friday-molosoc/`, `/black-friday-offer-molosoc/`) only.

## What changed

- **Hero image:** the small product-on-white photo (`landing-b/lpb-product-shot-2`)
  is replaced by Žaneta's ad `assets/images/molosoc_black_friday_ad.webp`
  (1254 × 1254, left untouched). Resized only — no crop, no retouch — to square
  WebP 480 / 800 / 1200 px in `assets/images/black-friday/molosoc-black-friday-ad-*.webp`
  (32 / 71 / 121 KB), served with `srcset`, `sizes="(max-width: 560px) 264px,
  (max-width: 900px) 440px, 500px"`, `fetchpriority="high"` and the existing hero
  preload. CSS keeps `aspect-ratio: 1 / 1; object-fit: contain`, so the whole ad
  (lettering, pack, foot covers) is always visible and never distorted.
- **BLACK FRIDAY prominence:** the ad's own gold-brushed "BLACK FRIDAY" lettering is
  the campaign headline, at the top of the first screen (~22 px letters at 390 px,
  larger than the HTML headline). The old tiny letter-spaced eyebrow is hidden
  visually while the ad is shown (no duplicate headline); it stays in the markup for
  screen readers, and the hero `alt` names Black Friday. If the ad file were ever
  missing, the eyebrow returns as a large gold uppercase "BLACK FRIDAY" line.
- **Look:** dark ad on the charcoal band, gold hairline frame (no white card any more).
  Mobile hero: ad 264 px wide, headline 1.5 rem, top padding 0.6 rem.
- **Open Graph:** `og:image` follows the hero, so link previews now show the ad
  (1200 × 1200).

## CZ localization

The ad's small print is English ("Deep hydration", "Soft, smooth feet",
"SPECIAL OFFER", pack text). "Black Friday" itself is the term used in Czech too.
On the CZ page the Czech HTML stays the primary message — H1 "Více párů, nižší
cena za pár.", prices "209 Kč · Doprava od 79 Kč", the Czech picker — and the ad is
a supporting visual with a Czech `alt`. The page is therefore not presented as an
English-only hero. A Czech version of the artwork (same layout, CZ small print) can
replace the files without code changes: export it at 480 / 800 / 1200 px under the
same names in `assets/images/black-friday/`, or add a CZ base name per language in
`molosoc_bf_images()`.

Note for Žaneta: the pack printed in the ad says "Disposable Nitrile Foot Covers",
while the page copy says the covers are reusable (at least 10 uses). Not changed here.

## Unchanged

Bundle selector, 209 / 199 Kč prices (3 pairs 607 Kč), sizes, Woo checkout,
`molosoc_lp=bf` return, tracking/consent, the two lazy story photos, Christmas
pages, Landing B (its `lpb-product-shot-2` files are untouched) and every other page.

## Measurements (local mirror, iPhone 12 emulation 390 × 844)

Mirror = the real template, theme CSS and JS through `tests/fixtures/landing_bf_stub_378.php`,
a 64 px stand-in header and no web fonts. The #378 mirror put the hero image 35 px lower
(taller header), so the live page should add ~35 px to the vertical numbers below.

| | BF CZ | BF EN |
|---|---|---|
| hero ad | 264 × 264, whole (contain), file 800w at DPR 3 | same |
| headline top | 346 px | 346 px |
| set cards | 457–620 px | 484–647 px |
| CTA | 737–778 px "Do košíku" (≈ 772–813 live) | 763–804 px "Add to cart" (≈ 798–839 live) |
| horizontal scroll | none (scrollWidth 390) | none |
| desktop 1280 | ad 500 × 500 left, headline + lede + gold button right | same |

Screenshots: `docs/black-friday-380/` (`cz-390`, `en-390`, `cz-1280`, `en-1280`).
After deploy, `tests/e2e/black-friday-378.spec.mjs` on the live pages re-checks the
first screen with the real header, fonts and consent banner.

## Not done here (needs Žaneta's approval)

Merge, deploy, publishing the pages, Meta ads.
