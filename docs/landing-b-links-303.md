# Every landing link goes to Landing Page B (Issue #303, 2026-10-30)

Žaneta pointed the main-menu "foot cover" item at Landing Page B; every other button and link on the site still went to Landing Page A (homepage hero button, both category pages — 2 buttons + 3 "who is it for" cards — and the CTA of every pillar/spoke page, 21 hard-coded hrefs in 15 templates, incl. two in-text links).

- `inc/landing-links.php`: `molosoc_landing_url( $lang )` returns the Landing B permalink when that language's Landing B page is **published**, otherwise the Landing A URL. CZ → `/cz/hydratacni-navleky-molosoc/` (page 1037). EN Landing B (`/hydrating-foot-covers-molosoc/`, `molosoc_landing_b_en_slug()`) is not published on production, so EN links keep going to `/foot-covers/moisture-lock-foot-cover/` until it is — then they switch by themselves (no deploy needed). Filter `molosoc_landing_url`.
- All 21 template links use the helper. Menu items (`wp_nav_menu_objects`) and block/page/product content (`the_content`, priority 20) that still carry a Landing A href are rewritten on output, so nothing hand-edited in WP admin is left behind.
- Unchanged: Landing A itself (still reachable, still its own template/gates/JSON-LD), the product page and `molosoc_product_url()` (sticky pill, checkout), prices. No redirect from Landing A to B — that is a separate decision if Landing A is retired.
- Theme 0.2.110. Tests: `tests/test_landing_b_links_303.py`; `tests/test_landing_xmas_251.py` allow-list now includes `front-page.php` and `page-foot-covers.php` for this change.

After deploy: purge the page cache site-wide (every page carries the menu): `gh workflow run purge-home-cache.yml -f page_ids="$(seq -s ' ' 867 895) 924 1037 1065 1066"` and re-check the homepage hero button, a category page card, a pillar CTA and the menu in both languages.
