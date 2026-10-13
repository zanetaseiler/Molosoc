# Landing Page B — rebuild of WP page 580 (Issue #122)

**Status:** repo files only. Nothing on WordPress was written. Page 580 and the live
CZ landing Page A (886, `/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/`) are
untouched. B does not exist in WordPress yet (see "Draft creation + review path").

## Source

| | |
|---|---|
| WP page | **580** `Hydratacni Navleky Landing Page Old` (owner confirmation 2026-10-13 supersedes the earlier #650 assumption) |
| Public URL | https://molosoc.com/hydratacni-navleky-na-nohy/ — status `publish` on 2026-10-13 (modified 09:10 that day); the earlier cloud sessions could not reach molosoc.com at all, this rebuild was done from a local session where the public page and REST record are reachable without credentials |
| REST record | `GET /wp-json/wp/v2/pages/580` (public, `context=view`) |
| Built with | Thrive Architect landing page: meta `tve_landing_page = tcb2-clickjournalist-sales-page`, `_tve_header = 0`, `_tve_footer = 103` (Thrive footer symbol "Disclaimer / Privacy policy / Terms of service / Contact / © 2026 MOLOSOC" + WPConsent cookie banner), `tcb_editor_enabled = 1` |
| Why the block editor cannot render it | `post_content` is Thrive markup (`#tve_editor` > 16 `.thrv-page-section` blocks with `data-css` ids). All layout/colour/typography lives in the page's `tve_custom_style` block (~88 KB) + Thrive's base stylesheet, which only Thrive prints. The REST `content.rendered` (15 KB) is just the flattened text/images with no structure. Revisions were not readable without authentication (not needed — the live render was the source). |
| Template of record | `site/theme/page-hydratacni-navleky-landing-b.php` + `assets/css/landing-b.css` + `assets/js/landing-b.js` |

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

Type faces are page 580's own (DM Serif Display / Nunito Sans / Nunito / Open Sans),
surface `#faf7f2`, black bands and black square buttons with 2 px tracking — read from
the page's rendered CSS and `getComputedStyle`, not from the theme tokens.

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
4. Page 580 is **noindex-free and currently published** at `/hydratacni-navleky-na-nohy/` (it is listed as a normal page). That is outside this Issue; noted only because B is noindexed + sitemap-excluded in `functions.php` so a published B can never compete with A or with 580.
5. Page 580 wore no site header/nav and its own Thrive footer; B uses the theme header/footer like every other `page-{slug}.php` template. The pinned "Objednat nyní" header button became the bottom sticky bar.

## Asset inventory (all verified HTTP 200 on 2026-10-13, hot-linked exactly as page 580 does)

| File (`https://molosoc.com/wp-content/uploads/…`) | WP media id | Used in |
|---|---|---|
| `2026/04/hero-bg-v2-nqbEYtifYWW4XirFSK5h8z.webp` | — (Thrive bg) | hero background |
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

## Draft creation + review path (after this PR is merged and the theme deployed)

1. Theme deploy (production.yml on merge) puts the template, CSS and JS on the server.
   The Version header was bumped to 0.2.79 so Cloudflare does not serve stale assets.
2. Actions → **Create WP Page (draft)** → slug `hydratacni-navleky-landing-b`, title
   e.g. `Hydratační návleky – Landing Page B (varianta, koncept)`. The workflow is
   idempotent and only ever creates a **draft** (`create_wp_page.py`); run it only with
   Žaneta's go-ahead.
3. In wp-admin → Pages → the new draft: set **Language = Cz** (Polylang; a REST-created
   page lands in the default EN language) — do **not** link it as a translation of A.
   Then use **Preview** (`/?page_id=<id>&preview=true`) to review. The page renders
   this template regardless of its (empty) content.
4. Verification: B shows `status: draft` in Pages; `GET /wp-json/wp/v2/pages/886` and
   `/pages/580` still report `modified` 2026-09-29T16:41:52 / 2026-10-13T09:10:53
   respectively (A and 580 unchanged); `/wp-sitemap-pages-page-1.xml` does not list B.
5. Publishing B, any redirect, ad, analytics or A/B split is out of scope and needs a
   separate explicit decision.
