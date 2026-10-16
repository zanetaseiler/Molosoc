# SEO follow-up — Issue #203 (from #202 live observations)

Repo-grounded only. The sandbox cannot reach molosoc.com, so every live check
is **PENDING**; the live observations below are those recorded in #202.

## 1. /product-category/foot-care/ — noindex + sitemap exclusion (changed)

- Observed (#202): no canonical, ~55 words, one product.
- Repo: no SEO plugin; core emits `rel=canonical` only for singular posts, so
  a missing canonical on a taxonomy archive is expected, not a bug. The real
  "Category" page is the `/foot-covers/` Page (docs/site-structure.md §3); the
  Woo archive only repeats the single product shown on the product page.
- Decision: noindex,follow + drop from `wp-sitemap.xml`; **no canonical added**
  (it would contradict noindex). `molosoc_thin_product_cat_term_ids()` in
  `functions.php` resolves the `foot-care` term (+ Polylang translations);
  other `product_cat` archives and the rest of the taxonomy behaviour are
  untouched. The page stays reachable (WooCommerce links, 200).
- Reversal: if a real category landing is wanted later, remove the two
  filters and give the archive real copy first.
- Live check PENDING after deploy: robots meta on the archive, absence from
  `wp-sitemap-taxonomies-product_cat-*.xml`.

## 2. /cz/kurici-oko/na-chodidle/ hreflang — no change (justified)

`seo/cz-pages/spoke-na-chodidle.md` has `translation_of_en_slug: null` and the
template header says "Czech-only spoke". There is no EN equivalent, so no
alternate may be emitted (Polylang free correctly emits none). Its sibling
`jak-odstranit` maps to EN `callus-remover`; that is a separate mapping.
Adding an EN alternate pointing to callus-remover would be a fabricated pair.
Self-canonical/indexability stay as observed. Nothing to do in WP admin
unless a real EN article is later written and translation-linked.

## 3. /cz/magazin/ — useful CZ topic navigation added

`page-blog.php` (CZ branch only) now renders a "Kde začít podle toho, co vás
trápí" section: one short description per CZ pillar (paraphrased from the
pillars' own meta descriptions) plus links to the two existing kuří-oko
spokes. It lists only existing CZ pages; EN is unchanged. No noindex: the page
is the hub the CZ pillars link to (#200).

## Files changed

`site/theme/functions.php`, `site/theme/page-blog.php`,
`site/theme/assets/css/blog.css`, `tests/test_seo_followup_203.py`, this doc.

## Manual / open

- After deploy: confirm items 1 and 3 live. Do not re-request indexing for
  the six URLs already submitted; re-inspect 2026-10-23..30 per #202.
- Optional (Žaneta): decide whether /cz/magazin/ should be re-requested in GSC
  once the new content is live (not done here).
