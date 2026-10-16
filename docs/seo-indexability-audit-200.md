# SEO indexability audit — Issue #200 (from TrafficDom #296)

Repo-grounded only. Live checks were not possible from this session
(outbound request to molosoc.com returned no response), so every live item is
**PENDING**. No GSC requests were made and no indexing evidence is claimed.

## What the repo controls (and what it does not)

- Controlled here: child theme templates, `functions.php` (wp_robots,
  core `wp-sitemap.xml` filters), `mu-plugins/sitemap-404-status-fix.php`,
  hreflang x-default, JSON-LD, and the copy in `seo/cz-pages/`.
- NOT controlled here: live page content edited in WP admin/Thrive, Polylang
  translation links, Redirection rules, WP Rocket/WPO cache, robots.txt
  physical file, staging basic-auth, GSC.

## Repo findings per URL

| URL | Repo evidence | Status |
|---|---|---|
| /cracked-heels/fix-permanently/ | `page-fix-permanently.php`; not in sitemap exclusion list, no noindex rule. Only linked to its pillar → now also links to treatment + cream spokes | live index state PENDING |
| /cracked-heels/cracked-heels-treatment/ | `page-cracked-heels-treatment.php`; same as above, now cross-links | PENDING |
| /ingrown-toenails/treatment/ | `page-treatment.php`; linked from pillar; now links to prevent | PENDING |
| /ingrown-toenails/prevent/ | `page-prevent.php`; now links to treatment | PENDING |
| /foot-covers/ | `page-foot-covers.php`; no noindex rule in repo | PENDING |
| /product-category/foot-care/ | WooCommerce taxonomy archive, not repo-templated; no noindex rule in repo; not excluded from sitemap | PENDING — check in WP/GSC |
| /cz/magazin/ | `page-magazin.php` shim → `page-blog.php`; already links all 5 CZ pillars/spokes. Inbound links were the gap: CZ pillars now link to it | PENDING |
| /cz/kurici-oko/ subpages | `page-na-chodidle.php`, jak-odstranit has no dedicated repo template (WP content). Both previously linked only back to the pillar | PENDING |

The only `noindex` rules in the repo are: author archives, `uncategorized`
category, `tcb_symbols_tax`, and `thank-you` (`functions.php` wp_robots).
None of the URLs above is affected. Sitemap exclusions are listed in
`molosoc_sitemap_excluded_page_ids()`; none of the URLs above is excluded.

## Product title/meta

Reviewed `seo/cz-pages/product.md` / `i18n/cz/cz-product-copy.md`: no change
made — the live title/meta is not provably what the repo holds, and a rewrite
without GSC query data would be a guess. Recommend revisiting after the
GSC query export is available.

## Staging basic-auth (recommendation only, nothing changed)

Keep staging behind basic-auth plus `X-Robots-Tag: noindex` at the server
level rather than relying on credentials alone; exempt only
`/wp-json/` and `/wp-admin/admin-ajax.php` needed by deploy workflows via
an IP allow-list, never by weakening the password. Store the credential in
the existing secret store; rotate by an operator, not by an agent.

## Manual items for Žaneta (after merge/deploy)

1. In GSC URL Inspection (operator, not Claude), inspect the eight URLs
   above and record "Indexed / Crawled-not-indexed / Discovered".
2. Confirm /product-category/foot-care/ should be indexable; if thin,
   noindex via WP admin or a follow-up Block.
3. Confirm Polylang hreflang pairs for popraskane-paty, zarostly-nehet and
   kurici-oko, and /cz/magazin/.
4. Re-fetch wp-sitemap.xml after deploy and confirm all eight URLs listed.
5. Spot-check "Související čtení" renders on the CZ pillars after deploy.
