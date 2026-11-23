# Black Friday CZ/EN Meta landing pages (Issue #378)

New campaign pages next to the Christmas pages (1065 `/cz/vanocni-darek-molosoc/`,
1066 `/christmas-gift-molosoc/`), which stay unchanged.

| | CZ | EN |
|---|---|---|
| URL | `/cz/black-friday-molosoc/` | `/black-friday-offer-molosoc/` |
| WP page slug | `black-friday-molosoc` (language cz) | `black-friday-offer-molosoc` (language en) |
| Template (auto by slug) | `page-black-friday-molosoc.php` | `page-black-friday-offer-molosoc.php` |

**Why two slugs:** the site runs Polylang Free, which cannot save two pages with
the same slug (the second becomes `black-friday-molosoc-2`). The CZ page — the main
Meta market — gets the suggested slug; the EN page gets `black-friday-offer-molosoc`.
No page, template, redirect or test in the repo uses either slug (checked 23 Nov 2026).
The live site was not reachable from the implementation session; WordPress refuses a
duplicate slug when the draft is created, so the create step below is the live check.

## What is shared with the Christmas pages (same code, not a copy)

Both page templates render `template-parts/landing-xmas.php` with `$lpx_campaign = 'bf'`:

- bundle picker 1 / 2 / 3 / 4+ pairs, M/L per pair, M/L counters for 4–10 pairs (`landing-xmas.js`);
- the URL contract `?molosoc_xmas=1&molosoc_xmas_sizes=M,M,M` and the server path
  `molosoc_xmas_add_to_cart()` (one cart line per pair, stock check, all-or-nothing);
- pricing `molosoc_xmas_unit_prices()`: 209 Kč first pair + 199 Kč each further pair
  (3 pairs = 607 Kč), set server-side from the slot tag;
- checkout, shipping, tax and payment methods are WooCommerce's, untouched;
- consent/tracking: WPConsent, Meta pixel (PageView/ViewContent by Facebook for
  WooCommerce), Clarity, order attribution, delayed gtag.js (#301) — all untouched.
  `molosoc_xmas_current_lang()` answers for the BF slugs too, so every gate keyed on
  `molosoc_is_xmas_landing()` (assets, plugin dequeue, delayed gtag, sticky pill, logo)
  applies; the Christmas announcement bar is off on these pages.

## What differs (inc/landing-bf.php, assets/css/landing-bf.css)

- copy `molosoc_bf_copy()`: native CZ/EN, no Christmas wording, no order-by date, no
  percentage, no stock pressure; prices read from the checkout price list;
- photos: real MOLOSOC photos already in the theme (Landing B uploads) — hero
  `lpb-product-shot-2` (foot covers in front of the MOLOSOC pack, shown whole:
  `object-fit: contain`, square box), `lpb-apply-cream`, `lpb-opening-package-mami`;
- head: title, description, Open Graph + Twitter card (og:url = permalink =
  WordPress canonical; og:locale + alternate), product-photo preload. hreflang cs/en
  comes from Polylang once the pages are linked as translations, x-default from functions.php;
- picker's checkout URL carries `molosoc_lp=bf`, so a stock refusal returns to the BF page;
- release flag `molosoc_bf_published` (default true; false = noindex + out of sitemap);
- colours: charcoal / cream / one gold, scoped to `.lpx--bf`.

**Hero photo replaced in #380** by the uploaded Black Friday ad — see `docs/black-friday-380.md`. Original note: **Swapping the hero photo:** the issue names Žaneta's file "Product Molosoc Foot Cover
With Pack PNG(4).png", which was not attached to the issue. The hero uses the theme's
existing product-with-pack photo. To use the newer file: export it as square WebP at 480
and 960 px and replace `assets/images/landing-b/lpb-product-shot-2-{480,960}.webp`
(Landing B uses the same files), or add new files and point `molosoc_bf_images()['hero']` at them.

## Measurements (local mirror, iPhone 12 emulation 390×844)

Mirror = the real template, theme CSS and JS rendered through PHP stubs, with a 168 px
stand-in for the WPConsent card (the size measured live in #374). The same mirror
gives the Christmas CZ page the numbers measured on the live page in #375
(cards 521 px, "Do košíku" 800–842 px).

| | BF CZ | BF EN | Christmas CZ (mirror) |
|---|---|---|---|
| hero photo | 184×184 px, contain, whole | same | 350×233 |
| headline top | 317 px | 317 px | 354 px |
| set cards | 464–627 px | 464–627 px | 521–684 px |
| CTA | 743–785 px "Do košíku" | 743–785 px "Add to cart" | 800–842 px |
| horizontal scroll | none (390) | none | none |
| 3 pairs + M → button URL | `/cz/pokladna/?molosoc_lp=bf&molosoc_xmas=1&molosoc_xmas_sizes=M,M,M` | `/checkout/?molosoc_lp=bf&…=M,M,M` | `/cz/pokladna/?molosoc_xmas=1&…=M,M,M` |

Lighthouse 12.8 mobile on the mirror, medians of 3 (no WordPress plugins and no third
parties, so it is only a comparison between the two designs, not a live score):
BF CZ/EN performance 99, LCP 1.96 s, TBT 0, CLS 0, 208 KiB; Christmas mirror 98,
LCP 2.18 s, 266 KiB. Accessibility 96 (BF) vs 92 (Christmas mirror, colour contrast).
The only failing audits on BF are the document title and meta description, which the
mirror does not render (they are covered by `tests/test_landing_bf_378.py`).

Screenshots: `docs/black-friday-378/`.

## Not done here (needs Žaneta's approval)

1. Merge + deploy (`production.yml`).
2. Create the two drafts (`create-wp-page.yml`, production): slug `black-friday-molosoc`,
   lang `cz`; slug `black-friday-offer-molosoc`, lang `en`. Link them as a translation
   pair (Polylang Languages box) and publish.
3. Then on the live pages: `tests/e2e/black-friday-378.spec.mjs` (first screen, photo,
   no Christmas copy, og:url = canonical) and with `MOLOSOC_E2E_CART=1` the live cart
   flow: 3 pairs + M → checkout subtotal 607 Kč, 3 lines, `#place_order` visible, cart
   emptied through the Store API, no order placed; it reports PageView / ViewContent /
   AddToCart.
4. Meta ads: not touched.

**AddToCart (#374 finding, unchanged here):** the bundle is added server-side in
`wp_loaded` and the request redirects straight to the checkout, so Facebook for
WooCommerce never prints a browser AddToCart on this flow (the Christmas pages behave
the same). Its server-side CAPI event cannot be seen from the browser. The BF pages
use the same path, so the browser-side AddToCart is expected to be missing until a
separate Issue decides how to send it.
