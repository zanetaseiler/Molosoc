# Christmas 2026 gift landing (Issue #251)

Draft-first CZ/EN gift landing based on Landing B. Nothing here creates or publishes a WP page.

- Pages (create as WP drafts after separate approval): CZ slug `vanocni-darek-molosoc` (`/cz/vanocni-darek-molosoc/`), EN slug `christmas-gift-molosoc` (`/christmas-gift-molosoc/`). Link them as a Polylang CZ↔EN pair so hreflang is emitted.
- Code: `inc/landing-xmas.php`, `template-parts/landing-xmas.php`, `page-vanocni-darek-molosoc.php`, `page-christmas-gift-molosoc.php`, `assets/css/landing-xmas.css`, `assets/js/landing-xmas.js`.
- Pricing (approved 2026-10-26): 209 / 408 / 607 CZK for 1 / 2 / 3 pairs (209 + 199 + 199). One cart line per pair, tagged `molosoc_xmas_slot`; the price is set server-side from that tag in `woocommerce_before_calculate_totals`. Other add-to-carts, A/B/product pages and the post-purchase gift add-on (`molosoc_gift_slot`) keep their own prices. Product 364 stays 229 CZK.
- Release gate: `molosoc_xmas_published` now defaults to true (Issue #260), so the two pages are indexable and in the sitemap once published. Returning false from the filter restores noindex + sitemap exclusion. Only these two slugs are affected.

## Images (Issue #255)

The three owner-edited photos are imported from `zanetaseiler-patch-1` @ `3cf7b19` (`landing-xmas-01/02/03.webp`, byte-identical) as `site/theme/assets/images/landing-xmas/MOLOSOC_Christmas_Gift_Scene_01/02/03.webp`: real lossy WebP, 1536x1024 each. Scene 01 is the hero, 02 sits under "why a thoughtful gift", 03 under the story; the same images serve CZ and EN (only alt text differs). Note: scene 01's gift tag reads "Po krásné chvíli" (Czech) on the EN page too — an owner call whether to swap it.

Not verified: rendering in a browser (mobile/desktop), no WP/staging. The WooCommerce staging bundle tests (1/2/3 pairs = 209/408/607 CZK, regular 229 CZK unchanged) remain BLOCKED pending staging access/owner approval; no real transactions were made. Pages stay draft/noindex/unpublished.

## Publication gate (Issue #260)

Production drafts exist: CZ id 1065, EN id 1066 (both still drafts, i.e. non-public). This change only flips the code gate; it publishes nothing.

Remaining manual production tasks / not verified:
- Polylang CZ↔EN translation link (1065 <-> 1066) is NOT set; hreflang will not be emitted until it is (WP admin: edit 1065 -> Languages -> translation = 1066).
- Not verified on production: 209/408/607 CZK, regular 229 CZK unchanged, M/L selectors, CZ/EN output, canonical/hreflang, images/mobile layout, checkout. No orders or payments were made. Owner accepted this risk (Option C).
- Scene 01 keeps the Czech gift tag on EN for now (owner decision).

## Pre-launch fixes (Issue #269, 2026-10-27)

- Removed the internal "Normální WooCommerce objednávka…" / "A normal WooCommerce order…" sentence. The order section now reads "Bezpečná platba přes Comgate. Doprava od 69 Kč. Objednejte do 18. prosince, doručíme před Vánoci." (EN equivalent).
- Order-by line, 18 December (Žaneta's decision): in the hero under the price, in the order section and in the shipping FAQ answer. This replaces the #251 rule of "no delivery-date promise".
- Removed the crossed-out "běžně 229 Kč" / "normally 229 CZK" (Žaneta's decision; EU Omnibus rule: a reference price must be the lowest of the previous 30 days, which could not be confirmed). Bundle prices 209 / 408 / 607 are unchanged.
- CZ block cart showed "MOLOSOC Moisture Lock Foot Cover": the Store API cart item name comes from `get_title()` (`woocommerce_product_title`), which the CZ name filters did not cover. `molosoc_cz_store_api_product_name()` now also runs on that hook (CZ + product 364 only).
- Not changed: checkout loaded halfway once in review; not reproducible, to monitor.

## Size feedback for 2–3 pairs (Issue #287, 2026-10-28)

Clarity, 27 Oct 2026 (~21:12, mobile, Facebook in-app browser, the only checkout attempt of the campaign so far): the visitor chose 2 páry, picked M for pair 1 only and tapped "Pokračovat k pokladně" four times. The handler blocked correctly but nothing visible happened: `landing-b.css` hides every `.lpb-buy__legend` (sr-only) at ≤560px, so the existing "Pár 1 · Velikost / Pár 2 · Velikost" legends were invisible on the phone; `.lpb-buy__error` inherited the muted body colour; the JS only focused an opacity-0 radio.

What changed (theme only, both pickers, CZ + EN):
- Every size row shows `1. pár · Velikost` / `Pair 1 · Size` on every width (`.lpx-pair__legend` undoes B's sr-only rule on the Christmas pages only). M/L cards stay compact at 390px.
- When the pair count increases, the new rows take pair 1's size (if any, and only when that size is purchasable); each row can still be changed. Nothing is pre-selected while pair 1 has no size. The Clarity order (count first, size for pair 1 second) also fills rows that are already on screen and still empty.
- Blocked click: every visible row without a size is outlined red (`.is-missing`), the first one is smooth-scrolled to the middle of the viewport (plain jump under `prefers-reduced-motion`), the error reads "Vyberte velikost pro 2. pár." / "Please choose a size for pair 2." in red (#b3261e, ≥6:1 on cream and white) and is re-announced through `role="alert" aria-live="assertive"`. The next size pick clears everything.
- Unchanged: the URL contract `molosoc_xmas=1&molosoc_xmas_sizes=…`, server validation and prices in `inc/landing-xmas.php` (209 / 408 / 607 Kč, regular 229 Kč), the no-JS product-page link, payment and shipping.
- Theme version 0.2.103 (`assets/js/landing-xmas.js` and `assets/css/landing-xmas.css` must be re-fetched; WP-Optimize rebuilds its bundle from the new version).

Cookie card (WPConsent): the theme already compacts the card at ≤560px for Landing B and the Christmas pages (`landing-b.css`, `::part()` surfaces only); `landing-xmas.css` now shaves it further on the Christmas pages (6px bottom offset, 8/10px padding, 0.7rem text, 32px one-row buttons). No consent logic, button or category is touched. The error row is scrolled to the middle of the screen, so it never sits under the card. If the card still covers the buy box on a given phone, the plugin-side option is WP admin → WPConsent → Settings → Banner: switch the banner position from bottom to top (or the layout from "long" to a smaller one); re-check the Clarity consent replay (Issue #190) after any plugin-side change.

After deploy: purge the WP-Optimize page cache for `/cz/vanocni-darek-molosoc/` and `/christmas-gift-molosoc/` (ad URLs carry utm/fbclid, so cached variants multiply). Verified locally in headless Chrome against a copy of the picker markup (390×844): inheritance in both orders, per-pair error, highlight cleared on fix, busy lock, URL built as before. Not verified: live pages, real WPConsent card size in the Facebook in-app browser, screen-reader announcement.
