# Landing B — mobile purchase path (Issue #209)

CZ Landing B (`/cz/hydratacni-navleky-molosoc/`, WP page 1037) is where all three Meta
video ads land (mobile IG/FB). Clarity: 1 of 38 visitors reached the product page.

## What changed

| # | Scope item | Change |
|---|---|---|
| 1 | Direct buy CTA | `inc/landing-b-buy.php` resolves one WooCommerce add-to-cart link per size (M, L) for product 364 and prints them as an "Objednat M (36–39)" / "Objednat L (39.5–44)" pair in the hero and after every main section (11 groups). Each link is `<CZ cart>?add-to-cart=364&variation_id=…&attribute_…=…&quantity=1`: WooCommerce's own form handler adds the item and the visitor lands on the cart. No JS, no AJAX, no jQuery on B. An unresolvable size falls back to the CZ product-page URL (the old behaviour). |
| 2 | Price + COD line | The hero already showed `229 Kč` (Woo product 364, unchanged). New line under "Za 1 pár · Doprava od 79 Kč": **Dobírka:** Zaplatíte při převzetí zásilky. — gateway title + the approved Issue #198 string `molosoc_cod_cz_text()`. |
| 3 | WPConsent at 390px | The restyled card (components.css) covered the hero copy. `landing-b.css` (enqueued on B only) now compacts the card at ≤560px: 8px offset, 10×12px padding, 0.75rem text, buttons in one row. Consent buttons, preferences modal and the Clarity consent replay (PR #191, `molosoc_clarity_consent_replay()`) are untouched. |
| 4 | `jQuery is not defined` | See below. |

At ≤560px the hero is also compacted so product, price, COD line and both buttons fit the first
screen: the hero photo is a 170px crop; the thumbnails, bold sub-line and lede are not displayed
(the lede repeats the first "Pro koho" card verbatim); the H1 is 1.55rem.

## Placeholders / decisions for Žaneta

1. **COD line** is composed from two approved strings ("Dobírka" gateway title + the #198 description). No new sentence was written; please confirm the join reads right.
2. **Button labels** "Objednat" + size label: "Objednat" is the existing CTA verb; size labels are the existing Woo size labels ("M (36–39)", "L (39.5–44)"). No price is printed on the buttons (it sits directly above them).
3. **Landing A** and the global sticky "Koupit nyní" pill are unchanged (the pill still links to the product page).
4. The scarcity strip "Počet kusů je omezený" is still kept verbatim (flagged in `docs/landing-page-b-580.md`); on 390px it now sits just below the buy buttons.
5. WooCommerce's GET add-to-cart does not redirect, so reloading the cart URL with the query string would add a second pair. Changing that is cart logic and out of scope here; say if you want a redirect-after-add filter as a follow-up.

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
  new CTAs need no WooCommerce JS, so they cannot introduce the error.
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
* Screenshots `docs/screenshots/issue-209-landing-b-390-{before,after}.png` are 390×844 Chromium
  renders of the real template + CSS through a PHP stub harness (no WordPress runtime here): fake
  product variations, header and a placeholder WPConsent card (a shadow root with the plugin's `part`
  names, so the `::part()` rules in components.css/landing-b.css apply). They show layout, not live data.
  The real card's text length, live add-to-cart behaviour and live console need checking on staging/prod.
