# Christmas 2026 gift landing (Issue #251)

Draft-first CZ/EN gift landing based on Landing B. Nothing here creates or publishes a WP page.

- Pages (create as WP drafts after separate approval): CZ slug `vanocni-darek-molosoc` (`/cz/vanocni-darek-molosoc/`), EN slug `christmas-gift-molosoc` (`/christmas-gift-molosoc/`). Link them as a Polylang CZ↔EN pair so hreflang is emitted.
- Code: `inc/landing-xmas.php`, `template-parts/landing-xmas.php`, `page-vanocni-darek-molosoc.php`, `page-christmas-gift-molosoc.php`, `assets/css/landing-xmas.css`, `assets/js/landing-xmas.js`.
- Pricing (approved 2026-10-26): 209 / 408 / 607 CZK for 1 / 2 / 3 pairs (209 + 199 + 199). One cart line per pair, tagged `molosoc_xmas_slot`; the price is set server-side from that tag in `woocommerce_before_calculate_totals`. Other add-to-carts, A/B/product pages and the post-purchase gift add-on (`molosoc_gift_slot`) keep their own prices. Product 364 stays 229 CZK.
- Release gate: noindex + sitemap-excluded until `molosoc_xmas_published` returns true.

## Image ingestion (BLOCKER for publication)

The three owner-edited photos live in Google Drive, which the cloud session cannot reach, so no image is in the repo and none was substituted. The page renders without any image until they exist. To finish:

1. Commit the full-resolution originals under `site/theme/assets/images/landing-xmas/source/` (or upload to WP media).
2. Add web renditions (e.g. `cwebp -q 80`, ~1600 px wide) as `site/theme/assets/images/landing-xmas/MOLOSOC_Christmas_Gift_Scene_01.webp`, `_02.webp`, `_03.webp`.
3. Confirm the files are real full-resolution images (Drive metadata showed ~11 KB each).

Scene 01 is the hero slot, 02 sits under "why a thoughtful gift", 03 under the story; reassign in `template-parts/landing-xmas.php` once the strongest hero is chosen.
