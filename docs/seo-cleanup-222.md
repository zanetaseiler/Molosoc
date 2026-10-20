# Issue #222 — CZ product redirect + staging noindex

## A. Old Czech product slug (changed, repo-controlled)
- `/product/molosoc-hydratacni-navleky-na-nohy/` -> 301 -> `/cz/produkt/hydratacni-navlek-na-nohy/`
  (`molosoc_cz_product_redirect_target()` in `site/theme/functions.php`).
- Exact path match on that one source only (trailing slash / query tolerated); runs at
  `template_redirect` priority 1, ahead of WordPress' old-slug redirect (priority 10).
  Target is built from `home_url()`; it never equals the source, so no loop. EN URLs untouched.
- Why code and not the Redirection plugin: plugin rules are live DB state, only creatable by
  the production-mutating `manage-redirects.yml` dispatch (needs Žaneta). Code ships with the
  normal theme deploy on merge.
- Live check PENDING after deploy: `curl -sI https://molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/`
  -> `301`, `location: https://molosoc.com/cz/produkt/hydratacni-navlek-na-nohy/`, then one 200 hop.

## A2. CZ product SEO title/description and product sitemap omission (NOT changed)
Not provably repo-controlled: the CZ WooCommerce product (`/cz/produkt/...`) title/description is
WP/Woo product data (no SEO plugin; no theme filter targets it), and `wp-sitemap.xml` product
inclusion depends on live Polylang/WooCommerce state (repo only removes `tcb_*`, utility pages and
the foot-care term). Root cause unverified without live data -> separate follow-up. Nothing was
changed to the CZ mask landing page, CZ informational product page, canonicals or slugs.

## B. staging.molosoc.com noindex (changed, repo-controlled)
- `automations/staging/staging-noindex.php`: on host `staging.molosoc.com` only, sends
  `X-Robots-Tag: noindex, nofollow` and a robots meta noindex. No robots.txt disallow (Google must
  be able to crawl to see noindex). Inert on every other host; kept out of `site/mu-plugins/`
  so the production mu-plugin deploy never ships it.
- `deploy-mu-plugins-staging.yml` now ships it with the sitemap fix and ends with a regression
  check: staging returns noindex (or 401), live `https://molosoc.com/` has no noindex header.
- Cause of the setting change is unconfirmed; not attributed to any plugin.

## Not done / needs Žaneta
- Merge, then dispatch "Deploy MU-Plugins to Staging" (or push to `staging`) — a live staging write.
- Static files / non-WP paths on staging are not covered by a PHP plugin; host-level
  (`.htaccess` / basic-auth) protection is not repo-managed. GSC Removals for the indexed staging
  URLs are a separate manual action.
