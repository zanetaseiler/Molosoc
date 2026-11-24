# Black Friday header globe → other language's Black Friday page (Issue #386)

**Symptom:** on `/cz/black-friday-molosoc/`, the header globe's **EN** goes to Home. The
Black Friday top bar already opens the right language.

**Why #384 / PR #385 changed nothing live:** #385 added only a manual workflow
(`link-bf-pages.yml`), its script, a doc and a test. Nothing under `site/theme/**` changed,
so `production.yml` did not run (hence no action runs for the merge SHA). The Polylang
pair write only happens when someone dispatches `link-bf-pages.yml` with apply=true, and
nothing records that dispatch. Pages 1128/1129 are therefore still not a Polylang pair.

**Code path:** `template-parts/site-header.php` → `wp_nav_menu('primary')`. The globe is
Polylang's language-switcher menu item. For a page with no translation, `PLL_Switcher`
uses the other language's homepage as the link and then passes it through the
`pll_the_language_link` filter. The top bar (`inc/xmas-bar.php`) builds its own link with
`get_page_by_path()` and never uses the switcher, which is why it was right.

**Fix (theme):** `molosoc_bf_language_switcher_link()` in `inc/landing-bf.php`, hooked on
`pll_the_language_link`. Only on the two Black Friday pages (`molosoc_is_bf_landing()`)
it returns `molosoc_bf_page_url('cz'|'en')`. This is the same approach as the product's
`molosoc_product_language_switcher_link()`. It does not depend on the Polylang pair.
Every other page, the top bar, and the product and Thank-You switcher filters are unchanged.

Tests: `tests/test_bf_switcher_386.py` (runs the real filter through
`tests/fixtures/bf_switcher_stub_386.php`, which reproduces Polylang's homepage fallback).

## After Žaneta approves the merge

1. Merging changes `site/theme/**`, so `production.yml` deploys the theme automatically.
   Confirm that run succeeded for the merge SHA.
2. Purge the page cache for 1128 and 1129 (`purge-home-cache.yml` or the host's purge).
   A cached page keeps the old Home href until it is purged.
3. Check live, logged out, the **header globe** (not the top bar), before 1 Dec 00:00 Prague:

| page | globe item | expected href |
|---|---|---|
| `https://molosoc.com/cz/black-friday-molosoc/` | EN | `https://molosoc.com/black-friday-offer-molosoc/` |
| `https://molosoc.com/black-friday-offer-molosoc/` | CZ | `https://molosoc.com/cz/black-friday-molosoc/` |

   Click each one and confirm it lands on the other page (the round trip works both ways).
   Spot-check one other page (e.g. home, `/cz/navleky-na-nohy/`) to confirm its globe is unchanged.

Linking 1128/1129 as a Polylang pair (#384) is still useful for hreflang, but the globe
no longer depends on it.
