# Czech visitors land on the Czech home (Issue #293)

Order #1070 (29 Oct 2026) showed a Czech desktop visitor typing
`molosoc.com`, landing on the English home and ordering only after switching
language by hand. This note records what was evaluated and what ships.

## Polylang's own "Detect browser language" — evaluated, not used

Languages → Settings → URL modifications → *Detect browser language*
(option `browser`). Verified against Polylang 3.9.1, the version on
production:

- `PLL_Choose_Lang::get_home_language()` picks the `pll_language` cookie
  first, then the browser preference; `home_requested()` sends a 302 with
  `Vary: Accept-Language` and keeps the query string. Functionally close to
  the requirement.
- It only works with a page cache because
  `PLL_Cache_Compat::do_not_cache_site_home()` defines `DONOTCACHEPAGE` on
  the default-language front page whenever the option is on. WP-Optimize's
  advanced-cache serves a cached `/` before Polylang (or any plugin) runs and
  never varies on `Accept-Language`, so an uncached `/` is the only way a
  PHP-side redirect can ever fire. That is why the option was switched off on
  2026-08-20 (the English home had become a 1–4 s PHP render for everyone)
  and replaced by the client-side script in `front-page.php`.
- It does not meet three requirements of Issue #293: Slovak browsers are not
  mapped to Czech (`sk` is not a site language), bots are not excluded, and a
  returning `pll_language=cz` visitor is redirected again instead of being
  left alone.

The option therefore stays **off**.

## What ships: `site/mu-plugins/molosoc-cz-home-redirect.php`

Hooked on `plugins_loaded` (priority 20, after Polylang's init at 1) so a
redirected visitor never pays for the theme or the main query. Acts only when
the request path is exactly the site home; everything else is untouched.

| Request on `/` (GET or HEAD)                              | Result |
| --------------------------------------------------------- | ------ |
| `Accept-Language` top entry `cs-*` or `sk-*`, no cookie, no same-site referer, human UA | 302 → `pll_home_url('cz')` + original query string |
| `Accept-Language` top entry anything else (`en-US`, `de`, `*`, missing) | 200 English |
| any `pll_language` cookie (`en` or `cz`)                   | 200 English (manual/previous choice respected; the front-page script still sends `cz` cookie holders to the Czech home on direct entries) |
| same-site referer (EN link in the language switcher, logo, menu) | 200 English |
| bot / crawler / link previewer UA (Googlebot, bingbot, facebookexternalhit, …) or empty UA | 200 English, hreflang/canonical unchanged |
| POST or any other method                                  | untouched |

On every bare `/` request the plugin also defines `DONOTCACHEPAGE` (so
WP-Optimize never writes a cache file for `/`, with or without a query
string) and adds `Vary: Accept-Language`. The redirect carries
`nocache_headers()` so neither browsers nor Cloudflare keep it.

The redirect target is read from Polylang at request time
(`pll_home_url('cz')`, currently `/cz/molosoc-home-cestina/`); nothing is
hard-coded, and the plugin does nothing if Polylang or the `cz` language is
missing.

Known limit, by design: Polylang's footer script sets `pll_language` on every
page view in either language, so a Czech visitor who has ever opened an
English page (for example from an English ad) is not redirected afterwards.

## Deploy and verify

`deploy-mu-plugins.yml` syncs `site/mu-plugins/` to production on merge to
`main` and asserts the file is present. The previously cached `/` must be
purged once after the deploy (WP-Optimize → Cache → Purge, or
`purge-home-cache.yml` with `page_ids=867`), otherwise the old cache file keeps
being served until it expires.

Then, from any machine (run each twice; `wpo-cache-status` must never say
`cached` for `/`):

```bash
curl -sI -A "Mozilla/5.0" -H "Accept-Language: cs-CZ,cs;q=0.9" https://molosoc.com/            # 302, location: /cz/molosoc-home-cestina/, vary: Accept-Language
curl -sI -A "Mozilla/5.0" -H "Accept-Language: sk-SK,sk;q=0.9" https://molosoc.com/            # 302
curl -sI -A "Mozilla/5.0" -H "Accept-Language: en-US,en;q=0.9" https://molosoc.com/            # 200
curl -sI -A "Mozilla/5.0" -H "Accept-Language: cs-CZ" -H "Cookie: pll_language=en" https://molosoc.com/   # 200
curl -sI -A "Mozilla/5.0" -H "Accept-Language: cs-CZ" -H "Referer: https://molosoc.com/cz/molosoc-home-cestina/" https://molosoc.com/   # 200 (EN switcher)
curl -sI -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" -H "Accept-Language: cs-CZ" https://molosoc.com/   # 200
curl -sI -A "Mozilla/5.0" -H "Accept-Language: cs-CZ" "https://molosoc.com/?utm_source=test"    # 302, location ends with ?utm_source=test
curl -sI -A "Mozilla/5.0" -H "Accept-Language: cs-CZ" https://molosoc.com/foot-covers/          # 200, untouched
curl -sI -A "Mozilla/5.0" -H "Accept-Language: cs-CZ" https://molosoc.com/christmas-gift-molosoc/   # 200, untouched
```

## Removal

Delete the file from `site/mu-plugins/` (the deploy workflow syncs
deletions) and drop its `need` line in `deploy-mu-plugins.yml`. `/` becomes
page-cacheable again on the next request.

Note: the comment above the `molosoc-home-lang-redirect` script in
`front-page.php` still describes the August 2026 state ("moved here so the EN
homepage can be page-cached"). The theme was left untouched on purpose (the
Christmas evergreen guard in `tests/test_landing_xmas_251.py` protects
`front-page.php`); this note and the mu-plugin header are the current
description.
