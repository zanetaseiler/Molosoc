# Global sticky "Buy now" pill

The bottom-right pill (`assets/js/sticky-cta.js`, styled by `components.css`
`.molosoc-sticky-cta`, Issue #73) links to Landing Page B of the current language (Issue #311,
`molosoc_landing_url()`: CZ `/cz/hydratacni-navleky-molosoc/`; EN `/hydrating-foot-covers-molosoc/` once published, else Landing A
(the existing functional page)). Before #311 it linked straight to the WooCommerce product
page — `molosoc_product_url()`:
EN `/product/moisture-lock-foot-cover/`, CZ `/cz/produkt/hydratacni-navlek-na-nohy/` —
with the label "Buy now" / "Koupit nyní" from the current Polylang language.

`functions.php` `molosoc_sticky_cta_hidden()` is the single gate: it decides
both whether `sticky-cta.js` is enqueued and whether `window.molosocStickyCta`
is printed on `wp_head`.

## Coverage (Issue #177, 2026-10-14)

| Pages (CZ and EN) | Pill |
| --- | --- |
| Homepages, pillar + cluster pages, Journal / Magazín, Landing Page B, shop, my-account, thank-you, contact | shown |
| Landing Page A (`page-moisture-lock-foot-cover.php`: CZ 886, EN 869) | shown at > 760px; hidden at phone widths by `product.css`, where the page's own `.molosoc-sticky-buy` bar (price + button, same product URL) is the sticky CTA |
| Christmas gift landing (`page-vanocni-darek-molosoc.php` 1065 / `page-christmas-gift-molosoc.php` 1066) | shown, but as an **in-page link** to the bundle picker `#lpx-bundle` labelled "Vybrat dárkový set" / "Choose gift set" (Issue #299: order #1073 paid the regular 229 Kč after tapping the product-page pill). `inc/landing-xmas.php` returns url + label through the `molosoc_sticky_cta_data` filter that the `wp_head` print applies first; `landing-xmas.js` smooth-scrolls, keeps the URL and hides the pill while a buy box is on screen. |
| Product page (`is_product()`) | hidden — it is the destination |
| Cart / Checkout (`is_cart()` / `is_checkout()`, incl. CZ kosik / pokladna) | hidden |
| Privacy policy, terms of service, shipping policy — EN `privacy-policies`, `terms-of-services`, `shipping-policy`; CZ `zasady-ochrany-osobnich-udaju`, `obchodni-podminky`, `zasady-dopravy` | hidden (per Žaneta, Issue #177) |

Not excluded (not in the request): EN `refund-policy`, `legal-disclaimer`;
CZ `vraceni-a-refundace`. Adding a slug to the `is_page()` array in the gate
is the whole change if that should follow.

Tests: `tests/test_sticky_cta_gate.py`. Any CSS change here needs the
`style.css` Version bump so WP-Optimize rebuilds the bundle (see
`docs/` WPO notes); after a deploy purge the page cache for the six legal
pages and 886 / 869.
