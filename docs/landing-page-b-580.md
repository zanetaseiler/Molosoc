# Landing Page B — rebuild of WP page 580 (Issue #122)

**Status:** repo files only. Nothing on WordPress was written. Page 580 and the live
CZ landing Page A (886, `/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/`) are
untouched. B exists in WordPress as page 1037, slug `hydratacni-navleky-molosoc` (see "Draft creation + review path").

## Source

| | |
|---|---|
| WP page | **580** `Hydratacni Navleky Landing Page Old` (owner confirmation 2026-10-13 supersedes the earlier #650 assumption) |
| Public URL | https://molosoc.com/hydratacni-navleky-na-nohy/ — status `publish` on 2026-10-13 (modified 09:10 that day); the earlier cloud sessions could not reach molosoc.com at all, this rebuild was done from a local session where the public page and REST record are reachable without credentials |
| REST record | `GET /wp-json/wp/v2/pages/580` (public, `context=view`) |
| Built with | Thrive Architect landing page: meta `tve_landing_page = tcb2-clickjournalist-sales-page`, `_tve_header = 0`, `_tve_footer = 103` (Thrive footer symbol "Disclaimer / Privacy policy / Terms of service / Contact / © 2026 MOLOSOC" + WPConsent cookie banner), `tcb_editor_enabled = 1` |
| Why the block editor cannot render it | `post_content` is Thrive markup (`#tve_editor` > 16 `.thrv-page-section` blocks with `data-css` ids). All layout/colour/typography lives in the page's `tve_custom_style` block (~88 KB) + Thrive's base stylesheet, which only Thrive prints. The REST `content.rendered` (15 KB) is just the flattened text/images with no structure. Revisions were not readable without authentication (not needed — the live render was the source). |
| Template of record | `site/theme/page-hydratacni-navleky-molosoc.php` + `assets/css/landing-b.css` + `assets/js/landing-b.js` |

## Section map (page 580 → B)

| # | Page 580 section (Thrive) | B |
|---|---|---|
| 0–1 | Thrive header: logo + pinned "Objednat nyní" button (sticky) | theme header (real nav + cart pill) + `.lpb-sticky` bottom bar that appears once the hero CTA scrolls out |
| 2 | Hero over `hero-bg-v2…webp` + 50 % white; 2 cols: main photo + 3 thumbs / eyebrow, H1 "Namazané nohy. Bez nepořádku.", bold sub, lede, price, "Objednat za …" | `.lpb-hero` — same |
| 3 | Black strip "Počet kusů je omezený" + "100% nitril · Bez latexu · Hypoalergenní" | `.lpb-strip` — same (**flagged**, see below) |
| 4 | "Pro koho MOLOSOC je" — 3 icon cards | `.lpb-cards--3` — same icons (sparkle, shield-check, clock) |
| 5 | "Nejsou to ponožky." — photo left, copy + 4 bullets right | `.lpb-split` |
| 6 | "Dvě velikosti. Jeden účel." — 3 photo cards M / L / Porovnání | `.lpb-cards--photo` |
| 7 | "Jednoduchý rituál" — photo + steps 01–05 | `.lpb-steps` |
| 8 | "Jak MOLOSOC vznikl" — Thrive tabs ×3 | `.lpb-tabs` (ARIA tabs; stacked without JS) |
| 9 | "MOLOSOC v reálu" — 2 captioned photos | `.lpb-gallery` |
| 10 | "Jak to vše začalo." — YouTube `dXVivzbZBfc` (vertical Short) | `.lpb-video` (youtube-nocookie embed) |
| 11 | "Funguje s vaším oblíbeným krémem." — copy + 4 chips, photo right | `.lpb-split--reverse` |
| 12 | Black band "Konec klouzání. Konec čekání." — 3 icon cards, price, CTA | `.lpb-section--dark` |
| 13 | "Máte otázky?" — 6 Thrive toggles | `.lpb-faq` native `<details>` |
| 14 | "Objednejte MOLOSOC" — product card, price, CTA, 3 mini badges | `.lpb-order` |
| 15 | "Zakladatelky" — quote + photo | `.lpb-founders` |
| footer | Thrive symbol 103 | theme footer (Comgate/Visa/MC/GPay/APay strip, legal links) |

Body and label faces are page 580's own (Nunito Sans / Nunito / Open Sans); headings
use the theme display face (Tenor Sans via `--font-display`) instead of 580's DM Serif
Display, so B's headings match the rest of the site (Žaneta, 2026-10-13). Surface
`#faf7f2`, black bands and black square buttons with 2 px tracking — read from the
page's rendered CSS and `getComputedStyle`, not from the theme tokens.

## Operational purchase details adapted (the only intentional copy changes)

| Page 580 | B | Source of truth |
|---|---|---|
| `199 Kč` (hero, dark band, order card, FAQ) | `229 Kč` | Woo product 364 via Store API: price 22900 CZK, both variations in stock |
| `Doprava od 69 Kč` (hero, order section) and `Doprava od 49 Kč` (FAQ) | `Doprava od 79 Kč` | `inc/woocommerce-lang.php` `molosoc_product_364_shipping_note()`, live CZ product page |
| Order card `L (40–44)` (page 580's own size card already said 39.5–44) | `L (39.5–44)` | Woo attribute labels (`woocommerce-lang.php`), live product page |
| CTA `https://molosoc.com/product/molosoc-hydratacni-ponozky/` (dead slug — the product was renamed to `moisture-lock-foot-cover` on 2026-08-16) | `molosoc_product_url( 'cz' )` = `/cz/produkt/hydratacni-navlek-na-nohy/` | `MOLOSOC_PRODUCT_URL_CZ` |
| "Odesíláme do 24 hodin", "Bezpečná platba přes Comgate", "1 balení = 1 pár", M 36–39 | unchanged — still true | trust bars + footer in the theme |

## Flagged outdated / presale-era messaging (kept verbatim, owner decides)

1. **"Počet kusů je omezený"** (black strip under the hero) — presale scarcity claim; not an operational detail, so it was *not* changed. Remove the `.lpb-strip__scarcity` paragraph if B should not make this claim.
2. **Empty crossed-out price span** before "199 Kč" in page 580's hero and dark band — leftover of a struck-through presale price. Reproduced as nothing; no "was" price invented.
3. **Story tab 3 title** on page 580 is broken by a stray line break ("A pak se stal nápad sku / tečností."); B renders the evident intended text "A pak se stal nápad skutečností." — the only non-operational copy fix.
4. Page 580 is **noindex-free and currently published** at `/hydratacni-navleky-na-nohy/` (it is listed as a normal page). That was outside Issue #122; B was noindexed + sitemap-excluded in `functions.php` at the time so a published B could not compete with A or with 580. Since Issue #159 B is indexable (see "Indexing" below); a 301 from 580 to B is still a separate owner decision.
5. Page 580 wore no site header/nav and its own Thrive footer; B uses the theme header/footer like every other `page-{slug}.php` template. The pinned "Objednat nyní" header button became the bottom sticky bar.

## Asset inventory (all verified HTTP 200 on 2026-10-13, hot-linked exactly as page 580 does)

| File (`https://molosoc.com/wp-content/uploads/…`) | WP media id | Used in |
|---|---|---|
| `2026/04/hero-bg-v2-nqbEYtifYWW4XirFSK5h8z.webp` | — (Thrive bg) | hero background (since Issue #157 served from the theme pair `lpb-hero-bg-960/1920.webp`, see below) |
| `2026/04/Molosoc-Photos-Product-Hero-New-Baige.jpg` (1152×860) | 638 | hero main |
| `2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg` (1152×860) | 639 | hero thumb, "Co to je" |
| `2026/04/Molosoc-Photos-Product-New-Sizes-WBG.jpg` (1152×860) | 444 | hero thumb |
| `2026/04/Molosoc-Photos-Product-New-Product.png` (1152×860) | 436 | hero thumb |
| `2026/04/Molosoc-Photos-Product-Hero-New-White.jpg` (1152×860) | 640 | size M |
| `2026/04/Molosoc-Photos-Product-New-Studio.jpg` (1920×1434) | 439 | size L |
| `2026/04/Molosoc-Photos-Product-New-Sizes-WBG-1.jpg` (1152×860) | 446 | Porovnání |
| `2026/04/Molosoc-Photos-Product-New-Apply-Cream-Ok.jpg` (1920×1288) | 611 | Jednoduchý rituál |
| `2026/04/Molosoc-Photos-Product-Mami-Sofa.jpg` (1920×1434) | 538 | Z reálu |
| `2026/04/Molosoc-Photos-Product-Holdind-It-First-Time-WBG.jpg` (1920×1434) | 537 | Z reálu |
| `2026/04/Molosoc-Photos-Product-New-VariationCream-Ok.jpg` (1152×860) | 612 | Kompatibilita |
| `2026/04/Molosoc-Product-Shot-2.jpg` (2048×2048) | 617 | Objednávka |
| `2026/01/Molosoc-Opening-Package-Mami.jpg` (1290×1434) | 3346 | Zakladatelky |
| `2026/04/MOLOSOC_logo_only-copy.png` / `…-White.png` | 441 / — | page 580 header/footer logos — not needed (theme header/footer) |
| `2026/03/paticka-web-svetle.png` | — | page 580 Thrive footer — not needed |
| YouTube `dXVivzbZBfc` ("Takhle nějak to vypadalo… když vznikal první MOLOSOC.") | — | Podívejte se |

Note: page 580's content also references `Molosoc-Photos-Product-New-Sofa.jpg` only via
`srcset`; B uses the `-2` variant the page actually displays.

### WebP derivatives (Issue #153, mobile PageSpeed — LCP 9.2 s / score 60 before)

Since Issue #153 the `<img>` tags no longer hot-link the uploads above: each photo is served
from a theme-hosted WebP derivative set in `site/theme/assets/images/landing-b/`, resized to
the width `landing-b.css` displays it at (`cwebp -q 78 -m 6 -sharp_yuv -resize <w> 0` from the
live uploads; the hero "jpg" on the server is itself already a 1152×860 WebP). The template
echoes `molosoc_landing_b_img_attrs( <base>, <widths>, <sizes> )` (functions.php) for
`src`/`srcset`/`sizes`; the lightbox-style `<a href>` wrappers still point at the original
full-size uploads. The hero is the LCP element: `fetchpriority="high"`, eager, and preloaded
from `wp_head` (`molosoc_landing_b_head()`) with the identical srcset via
`molosoc_landing_b_hero_image()`.

| Upload | Derivative set | Widths | `sizes` |
|---|---|---|---|
| Hero-New-Baige | `lpb-hero-baige` | 480 / 800 / 1152 | `(max-width: 900px) 100vw, 700px` |
| New-Sofa-2 (hero thumb) | `lpb-sofa-2` | 480 | `(max-width: 900px) 33vw, 230px` |
| New-Sizes-WBG (hero thumb) | `lpb-sizes-wbg` | 480 | same |
| New-Product.png (hero thumb) | `lpb-product-pack` | 480 | same |
| New-Sofa-2 ("Co to je") | `lpb-sofa-2` | 480 / 960 | `(max-width: 900px) 100vw, 50vw` |
| Hero-New-White / New-Studio / New-Sizes-WBG-1 (size cards) | `lpb-hero-white` / `lpb-studio` / `lpb-sizes-wbg-1` | 480 / 960 | `230px` (matches the `.lpb-card img` 230px cap at every viewport) |
| New-Apply-Cream-Ok | `lpb-apply-cream` | 480 / 960 | `(max-width: 900px) 100vw, 50vw` |
| Mami-Sofa / Holdind-It-First-Time-WBG (gallery) | `lpb-mami-sofa` / `lpb-holding-first-time` | 480 / 960 | `(max-width: 900px) 100vw, 430px` |
| New-VariationCream-Ok | `lpb-variation-cream` | 480 / 960 | `(max-width: 900px) 100vw, 50vw` |
| Product-Shot-2 | `lpb-product-shot-2` | 480 / 960 | `(max-width: 900px) 100vw, 400px` |
| Opening-Package-Mami | `lpb-opening-package-mami` | 400 / 800 | `(max-width: 400px) 100vw, 400px` |
| hero-bg-v2 (`.lpb-hero` CSS background, Issue #157) | `lpb-hero-bg` | 960 (`(max-width: 900px)`, 4.4 KB) / 1920 (`(min-width: 900.1px)`, 12.5 KB) | — (`cover`; `cwebp -q 70`, a soft watercolour wash under the 50 % white overlay) |

**Issue #157 — the real LCP element.** After #153 PageSpeed still reported the `.lpb-hero`
section's CSS background (`hero-bg-v2…webp`, 1920×1072, 15.5 KB hot-linked from the uploads)
as the LCP element, not the prioritised `<img>`: a CSS `url()` is only discovered once the
WPO Minify bundle has downloaded and been parsed. The background is now the theme-hosted pair
above; `molosoc_landing_b_hero_background()` (functions.php) is the single source of the two
URLs + media queries, the template writes them onto the section as
`--lpb-hero-bg-mobile` / `--lpb-hero-bg-desktop` custom properties
(`molosoc_landing_b_hero_background_style()`), `.lpb-hero` in `landing-b.css` paints
`var(--lpb-hero-bg)` (desktop by default, the mobile copy inside the existing 900px media
query) under the unchanged 50 % white overlay, and `molosoc_landing_b_head()` prints one
`<link rel="preload" as="image" fetchpriority="high" media="…">` per breakpoint right after the
hero `<img>` preload, so a phone fetches only the 4.4 KB copy and starts it from the HTML.
The visual is unchanged; the fallback option (drop the image for a plain colour) stays open if
the re-run still flags the background. `homepage.css` / `thank-you.css` still use the upload.
Theme Version 0.2.92.

Same Issue, same page only: the unused WooCommerce / select2 / photoswipe / Customer Reviews /
PPL CZ / Comgate CSS+JS is dequeued (`molosoc_dequeue_unused_homepage_assets()`, now gated on
`molosoc_page_without_plugin_markup()`, also run right before the footer assets print because
PPL enqueues its CSS late), both Google Fonts stylesheets are printed as non-blocking
`media="print"` + `onload` links from `wp_head` (page 580's Open Sans dropped — fallback-only
in `landing-b.css`), `landing-b.js` is `defer`red, and `document_title_parts` strips
"(varianta, koncept)" from the `<title>` (the WP post title is unchanged). Theme Version
0.2.91 (0.2.92 with Issue #157). After the deploy: `purge-home-cache.yml -f page_ids=1037`,
then re-run PageSpeed mobile.

## Draft creation + review path (after this PR is merged and the theme deployed)

1. Theme deploy (production.yml on merge) puts the template, CSS and JS on the server.
   The Version header was bumped to 0.2.79 so Cloudflare does not serve stale assets.
2. Actions → **Create WP Page (draft)** → slug `hydratacni-navleky-molosoc` (created as
   `hydratacni-navleky-landing-b`; Žaneta renamed page 1037 in WordPress on 2026-10-13 and the
   template + is_page() gates followed), title
   e.g. `Hydratační návleky – Landing Page B (varianta, koncept)`. The workflow is
   idempotent and only ever creates a **draft** (`create_wp_page.py`); run it only with
   Žaneta's go-ahead.
3. In wp-admin → Pages → the new draft: set **Language = Cz** (Polylang; a REST-created
   page lands in the default EN language) — do **not** link it as a translation of A.
   Then use **Preview** (`/?page_id=<id>&preview=true`) to review. The page renders
   this template regardless of its (empty) content.
4. Verification: B shows `status: draft` in Pages; `GET /wp-json/wp/v2/pages/886` and
   `/pages/580` still report `modified` 2026-09-29T16:41:52 / 2026-10-13T09:10:53
   respectively (A and 580 unchanged); `/wp-sitemap-pages-page-1.xml` did not list B at the
   time (it does since Issue #159, see "Indexing" below).
5. Publishing B, any redirect, ad, analytics or A/B split is out of scope and needs a
   separate explicit decision.

## JSON-LD (Issue #155)

`site/theme/inc/landing-b-schema.php` prints one `<script type="application/ld+json">`
in `wp_head` on `/cz/hydratacni-navleky-molosoc/` only (slug gate + Polylang `cz`).

**Audit (repo; molosoc.com was not fetched from this cloud session):** the page had no
JSON-LD; the site has no SEO plugin; every other schema block is slug-gated to other
pages; WooCommerce prints its own Product graph only on the product page. So the page
emits `WebPage` + `FAQPage` and **no Product/Offer** (links to the CZ product URL via
`significantLink`; price/stock/seller stay WooCommerce's on the product page). It reuses
`https://molosoc.com/#website` / `#organization` (defined by the homepage graph) instead of
redefining the organization. Not emitted: BreadcrumbList (no visible breadcrumb), logo,
sameAs, GTIN, ratings, images, shipping/returns, dates.

Sanitized example (`<title>` comes from `wp_get_document_title()`):

```json
{"@context":"https://schema.org","@graph":[
 {"@type":"WebPage","@id":"https://molosoc.com/cz/hydratacni-navleky-molosoc/#webpage",
  "url":"https://molosoc.com/cz/hydratacni-navleky-molosoc/","name":"<document title>",
  "description":"Hydratační návleky na nohy MOLOSOC: bez klouzání, …","inLanguage":"cs",
  "isPartOf":{"@id":"https://molosoc.com/#website"},"about":{"@id":"https://molosoc.com/#organization"},
  "publisher":{"@id":"https://molosoc.com/#organization"},
  "significantLink":"https://molosoc.com/cz/produkt/hydratacni-navlek-na-nohy/"},
 {"@type":"FAQPage","@id":"https://molosoc.com/cz/hydratacni-navleky-molosoc/#faq","url":"…","inLanguage":"cs",
  "isPartOf":{"@id":"…#webpage"},"mainEntity":[ /* 6 Question/Answer pairs = the visible <details> */ ]}]}
```

**Tests:** `python3 -m unittest tests.test_landing_b_schema` (needs `php-cli` for the render
tests; static tests always run). They cover syntax, canonical @ids, no duplicate ids / no
Product / Offer, `</script>` escaping, FAQ text identical to the template, and silence on
other pages and non-`cz` languages.

**On-site verification needed (not possible from the repo):**
1. View source of the live page: exactly one `ld+json` block; canonical `<link>` equals the `@id` base.
2. Google Rich Results Test / validator.schema.org on the URL: `WebPage` + `FAQPage` parse, no errors.
   (FAQ rich results are not promised; Google restricts them to a few site types.)
3. Product page `/cz/produkt/hydratacni-navlek-na-nohy/`: still exactly one Product (WooCommerce); EN page and
   an unrelated page: no new JSON-LD.
4. Price/stock: the FAQ answer repeats the template's hardcoded `229 Kč` / `Doprava od 79 Kč`
   (same constants as the template, guarded by a test). Making the template itself read WooCommerce is out of scope here.
5. Page B was `noindex` and sitemap-excluded when this markup was added (Issue #122) and has no
   EN/hreflang twin; it is indexable since Issue #159 (see "Indexing" below).

## Indexing (Issue #159, 2026-10-14)

Žaneta decided to index B. `functions.php` no longer lists `hydratacni-navleky-molosoc` in the
`wp_robots` noindex gate nor in `molosoc_sitemap_excluded_page_ids()`, so the page gets core's
default `max-image-preview:large` robots meta and is listed in `/wp-sitemap-posts-page-1.xml`.
Along with that, `inc/landing-b-schema.php`:

- prints a Czech `<meta name="description">` (~150 chars, hero + strip + FAQ wording only; the page
  had none) — the same string is the WebPage `description`;
- entity-decodes the WebPage `name` (`wp_get_document_title()` is HTML-escaped, so the title's
  en dash was serialised as the literal `&#8211;` inside the JSON);
- adds the `Organization` + `WebSite` nodes (same `@id`s, name, url, logo, sameAs as the homepage
  graph in `functions.php`, checked by `tests/test_landing_b_schema.py`) that the graph referenced
  but never defined on this page.

Post-merge checklist: purge the page cache for 1037 (`purge-home-cache.yml -f page_ids=1037`),
then on the live page confirm no `noindex` in the robots meta, the URL listed in
`/wp-sitemap-posts-page-1.xml`, the JSON-LD `name` showing `–`, the meta description present;
then request indexing in Google Search Console.

Still open (owner decision): 301 the old page 580 (`/hydratacni-navleky-na-nohy/`, 199 Kč) to
B via the Redirection plugin (`manage-redirects.yml`, action=add) and add its slug to
`molosoc_sitemap_excluded_page_ids()`.
