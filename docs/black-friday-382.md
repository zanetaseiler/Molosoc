# Black Friday top bar, end date and switch-back (Issue #382)

## What changes
- **Top bar** (`inc/xmas-bar.php`): until Mon 30 Nov 2026 23:59 Prague it reads
  „✦ Black Friday — první pár 209 Kč, každý další 199 Kč. Platí do pondělí 30. 11. →“ (CZ, → `/cz/black-friday-molosoc/`)
  / „✦ Black Friday — first pair 209 CZK, each extra pair 199 CZK. Until Monday 30 Nov →“ (EN, → `/black-friday-offer-molosoc/`).
  Same look, × button and mobile behaviour, no 🎄, new dismiss key `molosocBfBar382`.
  Prices come from `molosoc_xmas_unit_prices()` (the checkout price list), not typed.
  Hidden on both Black Friday and both Christmas pages (the existing landing-family gate).
  If the Black Friday page of that language is **not published**, the bar stays Christmas (never a link that bounces).
- **Black Friday pages**: „Nabídka platí do pondělí 30. 11.“ / „Offer valid until Monday 30 Nov.“ under the price line in the hero
  and in the lede of „Objednejte svůj set“ (the template's existing `deadline` slot).
- CZ hero: „**Dobírka:** Zaplatíte při převzetí zásilky.“ — the label was there but charcoal on the charcoal hero
  (`landing-b.css` colours it `--lpb-ink`, which the BF page sets to charcoal). Now cream. (≤560 px the COD line stays hidden
  in the hero as on the Christmas page since #373; the facts line under the picker still says „můžete platit i dobírkou“.)
- **Reviews** (`inc/real-reviews.php`): Czech pages list only reviews with Czech letters (ě š č ř ž ů ť ď ň). This applies to
  every Czech landing that shows the block (Black Friday, Christmas, Landing B CZ), since they share the helper. EN pages unchanged.

## How the 1 Dec switch works
One helper, `molosoc_bf_active()` = `now < 2026-12-01 00:00 Europe/Prague` (= 2026-11-30 23:00 UTC; `DateTimeZone` applies CET),
`now` from the `molosoc_bf_now` filter (default `time()`), used three ways:

1. **Server render** — the bar picks Black Friday or Christmas; from 00:00 both Black Friday pages answer **302** to the
   Christmas page of the same language (query string kept, response `DONOTCACHEPAGE` + no-cache headers).
2. **Cached bar** — WP-Optimize serves cached HTML without PHP, so a page cached on 30 Nov would keep the BF bar.
   The Black Friday bar therefore ships the Christmas text/link/key too, and its inline script swaps to them when
   `Date.now() >= end`. No purge is needed at midnight.
3. **Cached Black Friday page** — the first `<head>` script does `location.replace(<Christmas page> + search + hash)`
   when `Date.now() >= end`.

Limits: the client-side swap follows the visitor's device clock (a phone set days ahead would switch early); the server-side
302 and bar follow the server clock.

## Proof with a faked date
`tests/test_bf_bar_382.py`:
- Node runs the real inline scripts with `Date.now` faked to 30 Nov 23:59:59.999 and 1 Dec 00:00:00 Prague:
  cached BF bar stays BF / becomes the Christmas bar (text, link, aria-label, Christmas dismiss key); cached BF page stays /
  redirects to the Christmas page with `?utm…#…` kept. These ran locally.
- PHP stub `tests/fixtures/bf_bar_stub_382.php` fakes `molosoc_bf_now` for the server path (bar text/link before/after,
  unpublished BF page → Christmas bar, 302 + query string, other pages never redirect). Needs the php CLI — **skipped on this
  machine** (no php), so not executed here.
- On staging the same can be shown with a one-line mu-plugin: `add_filter( 'molosoc_bf_now', fn() => 1796079600 );`.

## After merge (owed, Žaneta's approval)
1. Production deploy (theme 0.2.127).
2. Publish the CZ Black Friday page **1128** (draft today; `/cz/black-friday-molosoc/` 301s to the homepage) and link it with 1129 in Polylang.
3. Purge: `purge-home-cache.yml` page_ids `867 884 868 885 869 886 1065 1066 1129 1128` (other cached pages pick up the bar
   as their cache expires); the minify bundle refreshes via the Version bump.
4. Live check: bar on CZ/EN pages, BF page end date + „Dobírka:“, no Spanish reviews on CZ, 3 páry = 607 Kč then empty cart.

Screenshots in `docs/black-friday-382/` are **pre-deploy mocks**: live HTML + this branch's CSS and markup changes
(390 px in an iframe, 1280 px desktop). The live BF page served an older cached hero (product photo) at the time.
