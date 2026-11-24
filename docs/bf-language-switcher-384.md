# Black Friday CZ ↔ EN language switcher (Issue #384)

**Symptom:** on `/cz/black-friday-molosoc/`, clicking **EN** goes to the homepage
instead of `/black-friday-offer-molosoc/`.

**Cause (confirmed by the dry run below, not yet by a live read):** Polylang's switcher
links a page to its *translation*. When a page has none, Polylang falls back to the
other language's homepage (the same fallback that `molosoc_product_language_switcher_link()`
works around for the product). #378 step 2 said to link the two BF pages as a Polylang
pair. #382 records the IDs (CZ **1128**, EN **1129**) and that Žaneta published 1128 by
hand, but nothing records the link being made. Without the link there is also no
hreflang pair between the two pages.

**Fix:** use Polylang's own translation link, pairing 1128 (cz) with 1129 (en). No theme
code, routing, switcher settings, design, offer or checkout change.

## The repository side (this PR)

- `automations/content-sync/link_bf_pages.py` and `.github/workflows/link-bf-pages.yml`
  (manual dispatch only). Modelled on `publish-xmas-pages.yml` (#262).
  - **Dry run (default, read-only):** checks that 1128 is `black-friday-molosoc`/cz and
    1129 is `black-friday-offer-molosoc`/en. Prints each page's Polylang translations and
    both live switcher hrefs, marking each OK or WRONG.
  - **apply=true + confirm `LINK-1128-1129`:** refuses if either page is already paired
    with a *different* page, because that link would be removed. Otherwise it calls
    `pll_save_post_translations({cz:1128, en:1129})` through the molosoc-migrate helper,
    re-reads both sides and stops with an error unless the pair is confirmed.
  - It never creates, publishes or edits a page.
- `tests/test_link_bf_pages_384.py`.

## Production actions that need Žaneta's approval (ZANETA_DECISION on #384)

Option A is the manual route and needs no deploy. Option B uses the workflow (after merge).

**A. wp-admin (simplest):** Pages → edit **1128** „Black Friday“ (CZ) → *Languages* box
→ in the **EN** translation field type `black-friday-offer` and pick page **1129** →
*Update*. Then purge the page cache for 1128 and 1129 (`purge-home-cache.yml`, which
resaves pages; both are already published, so the resave changes nothing else).

**B. workflow:** merge this PR (no theme change, so `production.yml` is not needed), then:
1. If the helper is not deployed, run `migrate-to-production.yml` phase `deploy-helper`
   (the dry run says so if it is missing).
2. Run `link-bf-pages.yml` with apply=false and post the output on #384.
3. Run `link-bf-pages.yml` with apply=true and confirm `LINK-1128-1129`.
4. Run `migrate-to-production.yml` phase `remove-helper`, then purge the cache for 1128 and 1129.

## Live verification after the link

Run `link-bf-pages.yml` again with apply=false (or check by hand, logged out):

| page | switcher | expected href |
|---|---|---|
| `/cz/black-friday-molosoc/` | EN | `https://molosoc.com/black-friday-offer-molosoc/` |
| `/black-friday-offer-molosoc/` | CZ | `https://molosoc.com/cz/black-friday-molosoc/` |

Also check that both pages' `<head>` carries `hreflang="cs"` and `hreflang="en"` alternates
for the pair. After the #382 end date (1 Dec 00:00 Prague) both BF pages 302 to the
Christmas pages, so check before then.
