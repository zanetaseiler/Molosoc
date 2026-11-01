# Christmas announcement bar (Issue #317)

Slim burgundy/cream/gold strip above the global navigation, CZ + EN. Theme only; nothing is deployed or published by this change.

- Code: `inc/xmas-bar.php` (data + markup + dismiss script + stylesheet enqueue), `assets/css/xmas-bar.css`, one call in `template-parts/site-header.php` (before `<header>`, so it also covers the homepage card variant), one `require_once` in `functions.php`. Theme version 0.2.115.
- Copy: CZ `🎄 Tip na vánoční dárek — Objevte vánoční nabídku MOLOSOC` → `/cz/vanocni-darek-molosoc/`; EN `🎄 Christmas Gift Idea — Discover the MOLOSOC Holiday Offer` → `/christmas-gift-molosoc/`. URLs come from `molosoc_xmas_slugs()` + `get_permalink()`; the bar is not shown while that page is not published.
- Not shown on the two Christmas pages, cart, checkout / order-received. Filter `molosoc_xmas_bar_enabled` (return false) removes it after the season.
- Dismiss: 44px "×" button, flag `molosocXmasBar317` in sessionStorage (session-only, Issue #324) (try/catch; without storage/JS the bar just shows). Bump the key to re-show it in a later campaign.
- In-flow, not fixed: menu/hamburger, sticky Buy-now pill and the on-page Christmas purchase flow are untouched. No plugin.
- Verified: PHP rendered via WP stubs (both languages, hidden cases), static tests, headless Chrome at 390 and 1280 px (no horizontal overflow, 44px close target, dismiss hides it; CZ text wraps to two lines at 390 px). Not verified: live WordPress/Polylang rendering, WP-Optimize cache (purge after deploy), real devices.
