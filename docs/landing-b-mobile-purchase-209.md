# Landing B — mobile purchase path (Issue #209)

CZ Landing B (`/cz/hydratacni-navleky-molosoc/`, WP page 1037) is where all three Meta
video ads land (mobile IG/FB). Clarity: 1 of 38 visitors reached the product page.

## What changed

Revised scope (ZANETA_DECISION 2026-10-19): direct size selection + direct checkout. This replaces the first
implementation (PR #210, per-size "Objednat" add-to-cart links to the cart); there is one implementation only.

| # | Scope item | Change |
|---|---|---|
| 1 | Size → checkout | `inc/landing-b-buy.php` prints one CTA group in the hero and after every main section (11 groups): an **M (36–39) / L (39.5–44)** radio pair (no default) and a **Pokračovat k pokladně** button. `landing-b.js` (vanilla) shares the choice across all groups, shows "Vyberte velikost." and stops if nothing is picked, otherwise opens `<CZ checkout>?add-to-cart=364&variation_id=…&attribute_…=…&quantity=1&molosoc_lpb=1`. WooCommerce's own form handler adds that variation (qty 1); one scoped `woocommerce_add_to_cart_redirect` filter (only for requests carrying `molosoc_lpb`) redirects to the clean checkout URL, so a reload/back can't re-add. The button locks after the first click (re-enabled on bfcache restore) to prevent a double add. Without JS or for an unresolvable size the button is the old product-page link. |
| 2 | Price + COD line | Hero shows `229 Kč` (Woo product 364, unchanged) and, under "Za 1 pár · Doprava od 79 Kč": **Dobírka:** Zaplatíte při převzetí zásilky. — gateway title + the approved Issue #198 string `molosoc_cod_cz_text()`. |
| 3 | WPConsent at 390px | `landing-b.css` (B only) compacts the card at ≤560px: 8px offset, 10×12px padding, 0.75rem text, buttons in one row. Consent buttons, preferences modal and the Clarity consent replay (PR #191, `molosoc_clarity_consent_replay()`) are untouched. |
| 4 | `jQuery is not defined` | See below. |

At ≤560px the hero is also compacted so product, price, COD line, size choice and button fit the first
screen: the hero photo is a 170px crop; the thumbnails, bold sub-line and lede are not displayed
(the lede repeats the first "Pro koho" card verbatim); the H1 is 1.55rem.

## Placeholders / decisions for Žaneta

1. **"Vyberte velikost."** (shown when the button is pressed with no size chosen) and the radio-group
   legend **"Velikost"** are the only new UI strings; the legend reuses the page's "Velikosti" heading
   wording. Please confirm or replace.
2. **COD line** is composed from two approved strings ("Dobírka" gateway title + the #198 description);
   no new sentence. Please confirm the join reads right.
3. Size labels are the existing Woo labels ("M (36–39)", "L (39.5–44)"); price is the unchanged `229 Kč`
   (hard-coded in the template since #122; **verify it equals the live checkout charge** — not checkable
   from this sandbox).
4. **Landing A** and the global sticky "Koupit nyní" pill are unchanged (the pill still links to the product page).
5. The scarcity strip "Počet kusů je omezený" is still kept verbatim (flagged in `docs/landing-page-b-580.md`).
6. The cart/checkout/payment/shipping logic is not touched; the only new server hook is the marker-scoped
   add-to-cart redirect above.

## `jQuery is not defined` investigation

No live-site/Clarity access from the cloud session (molosoc.com is blocked by the agent proxy), so this
is from the repo:

* jQuery is **intentionally absent** on the homepage, Landing A and Landing B
  (`molosoc_page_without_plugin_markup()` + `molosoc_dequeue_unused_homepage_assets()`, Issue #190).
  The two undeclared callers known then — WooCommerce's `woocommerce-analytics-client` and Thrive's inline
  footer toast script — are already dequeued / stripped on exactly those pages.
* Product, cart and checkout keep WooCommerce's jQuery; `molosoc_wpo_minify_skip_cart_checkout()`
  (PR #197) is untouched and its defer-JS behaviour is not restored or changed.
* Nothing added here loads or calls jQuery (`tests/test_landing_b_buy_209.py` pins that), and the
  size selector is vanilla JS, so it cannot introduce the error.
* #190 shipped 2026-10-15; the 14 Clarity hits were counted over the following four days. If any are
  post-deploy, the remaining source is a third-party handle-less inline script on a gated page that this
  repo cannot see. **Needed to finish this item:** the Clarity filter's page URLs / script URL for the
  error (or a headless render of the live HTML on A/B/home looking for `jQuery` outside tags with a
  `jquery` dependency). No speculative fix was added.

## Verification

* `python3 -m unittest discover -s tests` — all pass except `test_cz_cart_cod_copy_198` (needs the
  `requests` module, absent in this sandbox; unrelated and unchanged).
* The stale `test_landing_page_b_not_touched` guard (a PR-scoped `git diff origin/main` check from
  Issue #179) was removed: it fails on any change to Landing B.
* Screenshots `docs/screenshots/issue-209-landing-b-390-size-select-{initial,selected,error}.png` (and the
  earlier `-before` original) are 390×844 Chromium renders of the real template + CSS + JS through a PHP stub
  harness (no WordPress runtime here): stubbed product variations, no header and no WPConsent card. In that
  harness the real JS was driven: 11 groups, the choice syncs across all, no size → error and no navigation,
  two clicks on the button → exactly one navigation to the chosen variation's checkout URL. Live add-to-cart,
  the redirect to checkout, the real consent card height and the live console need checking on staging/prod.

## Issue #216 — fewer CTA groups, sticky halo

* The size + checkout group now appears in the hero, after "Co to je", "Jak to funguje", "MOLOSOC v reálu",
  "Kompatibilita" and in the final "Objednávka" section (6 groups, was 11). Removed from "Pro koho",
  "Velikosti", "Příběh", "Jak to vše začalo" and the dark "Proč MOLOSOC" section; section layout and copy
  untouched. No default size; the JS still shares the choice across groups; checkout/redirect logic unchanged.
* The sticky "Koupit nyní" halo (ivory ring + fine brown outline + soft ivory glow, static, no animation)
  was only in `product.css` (Landing A), so B showed the plain pill. The recipe is repeated in `landing-b.css`
  at all widths; Landing A styles are untouched. Position/z-index stay the global ones (below the consent card).
* Theme `Version` bumped to 0.2.99 so WP-Optimize rebuilds the bundle. Not verified in a browser here
  (no WordPress runtime / screenshot reference); check 390px and desktop on staging, incl. consent overlap.
