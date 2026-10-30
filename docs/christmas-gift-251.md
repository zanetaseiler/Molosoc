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

## Answers at the buy box + faster first screen (Issue #295, 2026-10-30)

Clarity, 28–30 Oct 2026 (mobile, Facebook/Instagram in-app browser): visitors scrolled past the picker, opened the size / shipping-and-payment / care FAQ items and left; LCP 3.2–3.6 s in the field.

Part 1, both pickers, CZ + EN (theme only):
- `molosoc_xmas_facts( $lang )` in `inc/landing-xmas.php` is the one source for the size ranges (M 36–39, L 39,5–44 / EU 39.5–44), the "from" shipping price (69 CZK) and the order-by date (18. prosince / 18 December). The hero line, the M/L buttons, both FAQ answers, the new info block and the size hint are composed from it in the template. Visible side effect: the CZ L button and FAQ now read "39,5–44" (Czech decimal comma, as in the Issue copy) instead of "39.5–44"; Landing B is untouched.
- Under the checkout button of each picker: three facts with 16 px line icons — `Velikost: M = 36–39 · L = 39,5–44 (podle velikosti bot)` / `Doprava od 69 Kč · můžete platit i dobírkou` / `Objednejte do 18. prosince, doručíme před Vánoci` (EN per the Issue). 0.9rem, 0.85rem at ≤560px, muted body colour (≈6.9:1 on cream), no card. The EN line is `Shipping from 69 CZK` only: cash on delivery is offered in the Czech Republic and Slovakia, nowhere else (Žaneta, 2026-10-30, Issue #297 — PR #296 had shipped it with "· cash on delivery available", removed in 0.2.109).
- Under the `1. pár · Velikost` / `Pair 1 · Size` label: `Nevíte? Zeptejte se na velikost bot.` / `Not sure? Ask for their shoe size.` (pair 1 only, both pickers).
- No price, shipping, gateway or checkout change; FAQ unchanged.

Part 2, Christmas templates only:
- Responsive scenes: 480/768/1080 px derivatives of the three photos (`MOLOSOC_Christmas_Gift_Scene_0N-<w>.webp`, `cwebp -m 6 -sharp_yuv`, q 75/70/60; the 1536 originals stay the largest candidate). `molosoc_xmas_image_set()` builds src/srcset/sizes once; the hero `<img>` (fetchpriority=high, eager, width/height) and a raw `<link rel="preload" as="image" imagesrcset imagesizes>` printed at `wp_head` priority 1 (`molosoc_xmas_head()`, outside WP-Optimize Minify) share it. Hero sizes `(max-width: 900px) calc(100vw - 40px), 524px`: a 390 px phone fetches 768w (53 KB) at 2x or 1080w (70 KB) at 3x instead of the 1536 px file (193 KB). Scenes 2–3 stay lazy. No AVIF: there is no encoder in the pipeline (cwebp/dwebp only); add `avifenc` derivatives and a `<picture>` later if wanted.
- Logo: `template-parts/site-header.php` now prints `molosoc_site_header_logo()` whose default output is byte-identical to the old `<img>`; `inc/landing-xmas.php` filters in `assets/images/molosoc-logo-tm-408/612.webp` (lossless, 4 + 6.5 KB, `sizes="(max-width: 380px) 164px, 205px"`) on the two Christmas pages only. The upload is already served as a 16 KB WebP by Cloudflare, so this is a small win (decode size 1567×230 → 612×90).
- Plugin assets: the Christmas pages join `molosoc_page_without_plugin_markup()` (one-line early return, additive edit — the #251 evergreen test allows no removed line in functions.php and the Landing B test reads the gate up to its first closing brace) and get the B/A extras plus WooCommerce's renamed PhotoSwipe handles (`wc-photoswipe`, `wc-photoswipe-ui-default`). Dropped on these pages: jQuery (+ migrate, blockUI, js-cookie), woocommerce.min.js, add-to-cart, cart-fragments, selectWoo, PhotoSwipe, Customer Reviews, WooCommerce analytics client, Thrive frontend + toast, PPL map/parcel-shop, and their CSS (woocommerce-general/layout/smallscreen, select2, photoswipe, CR, PPL, Comgate). Kept: Meta pixel + `wc-facebook-signals`, Clarity (+ consent replay), WPConsent, GA/GLA gtag, Brevo, order attribution/sourcebuster, nav toggle, cart badge sync, sticky CTA, back-to-top, landing-xmas.js (vanilla). The cart badge is server-rendered (`molosoc_cart_link()`); WP-Optimize bypasses the page cache for visitors with cart items, exactly as on Landing B.
- Google Fonts are already inlined into the WP-Optimize CSS bundle on these pages (`@font-face` in the bundle, no `<link>`), so no font change was made.
- Theme version 0.2.105.

Measured (Lighthouse 12.8 mobile, simulated slow 4G, logged out, `?utm_source=lh`): before, live CZ page — performance 57 / 69, LCP 7.4 s / 6.4 s, FCP 3.0 s / 1.6 s, 1,273 KiB, 72 requests, LCP element = hero `<img>`. The "after" numbers are in the PR (local mirror of the change) and are to be re-measured live after deploy + purge.

After deploy: purge the WP-Optimize page cache for `/cz/vanocni-darek-molosoc/` and `/christmas-gift-molosoc/` (ad URLs carry utm/fbclid, so cached variants multiply), then re-run the live checks: no `jquery`/`woocommerce.min.js`/`photoswipe` on either page, one CSS bundle, hero `srcset` + head preload present, cart badge and cookie card working, checkout URL `molosoc_xmas=1&molosoc_xmas_sizes=…` and 209 / 408 / 607 Kč unchanged. Not verified before deploy: the live WP-Optimize bundle, the real Facebook in-app browser, screen readers.

## Sticky pill stays on the page (Issue #299, 2026-10-30)

Order #1073 (30 Oct, 348 Kč) came from the Christmas ad, tapped the floating "Koupit nyní" pill, landed on the regular product page and paid 229 Kč instead of 209 Kč; the 27 Oct session did the same. The pill is the site-wide one (`sticky-cta.js`, data printed on `wp_head` in functions.php).

- functions.php now applies `molosoc_sticky_cta_data` (additive, inside the same gated closure) before the default product-URL print; `inc/landing-xmas.php` returns `{ url: '#lpx-bundle', label: 'Vybrat dárkový set' | 'Choose gift set' }` on the two Christmas pages only. Every other page prints exactly what it printed before.
- `landing-xmas.js`: the pill's click smooth-scrolls to the picker (plain jump under `prefers-reduced-motion`) with `preventDefault`, so the URL does not change; an IntersectionObserver on both `[data-lpx-buy]` boxes toggles `.lpx-pill-hidden` (opacity 0, visibility hidden, pointer-events none) while any buy box is on screen. `#lpx-bundle` gets `scroll-margin-top: 0.75rem` so the heading sits clear at the top (the header is not sticky).
- Other product-page links in the page body: only the no-JS fallback `href` of "Pokračovat k pokladně" (replaced by the checkout URL when JS runs) — kept, per the Issue. Header menu unchanged.
- Unchanged: `sticky-cta.js`, prices, the `molosoc_xmas=1&molosoc_xmas_sizes=…` contract, shipping, gateways. Theme 0.2.107. Tests: `tests/test_xmas_sticky_cta_299.py`, `tests/test_sticky_cta_gate.py` (print count pin).
- After deploy: purge pages 1065 and 1066, then check the pill label/href on both pages and "Koupit nyní" → product URL on `/cz/molosoc-home-cestina/` and Landing B.

## Speed step 2: gtag.js after the first screen (Issue #301, 2026-10-30)

PageSpeed Insights (mobile, slow 4G, 30 Oct 05:15 PDT) after #295: performance 89, FCP 0.9 s, **LCP 3.5 s**, TBT 40 ms; the hero (768w, 52 KB, preloaded) is the LCP element and gtag.js (~304 KB transfer, two ~150 KB files) is the biggest remaining weight competing with it.

- `inc/delayed-third-party.php` (required from functions.php): on the two Christmas pages only, the `script_loader_tag` of the WooCommerce Google Analytics Integration handle `google-tag-manager` (gtag.js) becomes an inert `type="text/plain"` placeholder with the URL in `data-molosoc-delayed-src`, plus a ~700-byte inline loader that injects the real `<script async src>` once, on the first of scroll / touchstart / pointerdown / keydown / mousemove or `load` + `requestIdleCallback` (2.5 s timeout; `setTimeout` 2 s fallback). The plugin's inline Consent Mode default, `gtag('js'|'config'|'set')`, `dataLayer` bootstrap, `window.ga4w` events data and the GA/GLA event bundles are untouched — they only queue into `dataLayer`, which gtag.js replays when it arrives, so page_view (now sent after the first interaction / idle), consent updates and the ecommerce events are complete. Cart, checkout and order-received pages are explicitly excluded in the gate, so the purchase event path is unchanged. Filters: `molosoc_delayed_third_party_enabled` (add Landing B with one `is_page()` if wanted), `molosoc_delayed_third_party_handles`.
- Brevo `sdk-loader.js`: printed raw in `<head>` by its plugin with `async` and an inline `window.Brevo.push(["init", …])`; already non-blocking and without a WordPress handle, so left alone. stats.wp.com (deferred), Clarity (async), Meta pixel (WPConsent-gated): untouched.
- Theme 0.2.108. Tests: `tests/test_delayed_third_party_301.py`.
- After deploy: purge 1065 / 1066, confirm `script[data-molosoc-delayed-src]` + the loader on both pages and the plain gtag tag on `/cz/kosik/`, `/cz/pokladna/`; re-run Lighthouse mobile. GA4 DebugView / Tag Assistant check of page_view-after-scroll and add_to_cart / begin_checkout needs GA4 access (not available from the agent session; the client-side `/g/collect?…en=page_view` request after a scroll was verified on a mirror in headless Chrome).

## Copy fixes (Issue #305, 2026-10-30)

- Size fact under the checkout button (CZ): briefly `(řiďte se podle velikosti bot)`; Issue #307 put that sentence where Žaneta meant it — the hint under `1. pár · Velikost` now reads `Řiďte se podle velikosti bot.` and the facts line is back to `(podle velikosti bot)`. Theme 0.2.112.
- "Co o nás říkají zákaznice": all three numbered items are shown, exactly as on Landing B (Žaneta confirmed the anonymous republication and wording of items 2 and 3 — ZANETA_DECISION 2026-10-27 on Landing B, re-confirmed 2026-10-30); the `molosoc_landing_b_feedback_extra_enabled` gate from #284 is removed. CZ page only; EN unchanged. Theme 0.2.111. After deploy purge page 1065.
