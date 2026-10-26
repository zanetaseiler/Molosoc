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
