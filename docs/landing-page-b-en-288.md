# English Landing Page B + CZ/EN menu links (Issue #288)

**Status:** repo files only. Nothing on production was written by this PR, and nothing runs
until Žaneta dispatches the workflow with a separate `ZANETA_DECISION`.

## What ships in the repo

| | |
|---|---|
| EN template | `site/theme/page-hydrating-foot-covers-molosoc.php` — same sections, order, markup, classes, images and size → add-to-cart → checkout flow as CZ B (`page-hydratacni-navleky-molosoc.php`); localized copy only |
| EN include | `site/theme/inc/landing-b-en.php` — slug helper, `landing-b.css/js` enqueue, hero/font preloads, document title, meta description, JSON-LD (`inLanguage en`), the FAQ (one source for page + JSON-LD) |
| Buy helper | `site/theme/inc/landing-b-buy.php` gains an optional `$lang` (default `'cz'`, so the CZ page is byte-for-byte unchanged): EN labels, EN product fallback, EN checkout, marker `molosoc_lpb=en` |
| Provisioning | `automations/content-sync/landing_b_en.py` + `.github/workflows/provision-landing-b-en.yml` (dispatch-only; `list` by default) |
| Tests | `tests/test_landing_b_en_288.py` |

`functions.php` only gains one `require_once` line. The CZ Landing B gates, title, schema, noindex/sitemap lists,
canonical handling and the CZ template are untouched. No redirects, no canonical/robots changes, no page removal.

## Proposed EN URL (not live yet)

**`https://molosoc.com/hydrating-foot-covers-molosoc/`** — slug `hydrating-foot-covers-molosoc`.

Derived from the existing architecture, not claimed to exist: English pages sit at the site root and Czech ones under
`/cz/`; the Christmas pair already maps `vanocni-darek-molosoc` ↔ `christmas-gift-molosoc` as a literal translation of the
CZ slug, and CZ B is `hydratacni-navleky-molosoc` ("hydrating foot covers" + brand). The provisioning script refuses to
reuse a page with that slug if it is not an EN page. If another slug is preferred, change `molosoc_landing_b_en_slug()`
(inc/landing-b-en.php), the template file name and `EN_SLUG` in the script.

## EN copy decisions (please review)

* Price/shipping use the EN product page's own wording: **€10 · charged as 229 CZK**, **Shipping from 69 CZK**
  (`molosoc_cz_product_price_html()`, `molosoc_product_364_shipping_note()`).
* Translated hero nudge, FAQ, story, steps and sizes (EU sizing) are new English wording for review.
* **Not carried over** because no EN wording is approved: the presale "Počet kusů je omezený" strip line, the
  cash-on-delivery line (CZ gateway text), and the anonymous CZ customer-feedback block.
* The YouTube Short is the same Czech-language video (the page says "video in Czech").
* The "cracked heels" lede links to `/cracked-heels/` (EN pillar).
* The CZ-only "unused plugin CSS/JS" dequeue pass (`molosoc_page_without_plugin_markup()`) is not replicated, to keep
  `functions.php` additive; the EN page keeps WooCommerce's default assets. Extending that one gate later is a follow-up.

## Provisioning + menu workflow (production — needs a separate ZANETA_DECISION)

Order of operations after merge + theme deploy:

1. **Dispatch `Provision EN Landing B…` with `action=list`** (default, read-only; GET requests only). It prints CZ B (1037),
   whether the EN page exists, the Polylang state, and **both menus (CZ 68, EN 67) with their real item ids**, marking
   every item that currently points at Landing Page A (`/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/`, page 886; EN
   `/foot-covers/moisture-lock-foot-cover/`, page 869). Item ids are **not** assumed (905 is only a guess until listed).
2. Žaneta records a `ZANETA_DECISION` naming the two item ids.
3. **Dispatch with `action=apply`**, `cz_menu_item`, `en_menu_item`, `confirm=APPLY-LANDING-B-288`. Preflight first
   (nothing is written if any check fails); then: create EN draft → verify language `en` → Polylang-link to 1037 and
   re-read → publish → fetch the public URL and require the EN Landing B `<title>` (else back to draft, **no menu change**)
   → repoint only the two named items (page items: `object_id`; custom links: `url`) → re-read both menus and require that
   every other item, the language switcher, and every label/parent/order are unchanged. Idempotent.

### Blockers / conditions (stated, not worked around)

* **Polylang linking needs the `molosoc-migration-helper` mu-plugin** (the free Polylang REST API cannot set a
  translation link). It is normally removed after migration; if `list` reports it missing, `apply` stops before writing
  anything. Either deploy it (`migrate-to-production.yml` phase=deploy-helper — a production mutation needing its own
  approval) or create the EN page and link it in wp-admin (Languages box), then re-run `apply`, which skips the finished steps.
* `apply` must run **after** the theme containing the EN template is deployed; otherwise the public check fails and the
  page is reverted to draft.
* Manual alternative for the menus: Appearance → Menus, change the two links in wp-admin.
