# Black Friday first screen continues the ad (Issue #388)

Both Black Friday pages only. The Christmas pages, prices, picker, checkout,
shipping, top bar, pixel/consent and the 30 Nov switch are unchanged.

- **Copy:** new headline, benefit line and one gold price line (CZ + EN, Žaneta's
  wording). Amounts come from `molosoc_xmas_unit_prices()` and
  `molosoc_xmas_bundle_total( 3 )`. Shipping, end date and COD keep their own lines.
- **Clip:** `assets/video/molosoc-we-tried-it-720.mp4` — 6.3 s, 720 × 720, H.264,
  no audio, 654 KB. Seconds 3.3–9.6 of Žaneta's public video „Šly jsme to prostě
  zkusit“ (EN „We Just Went and Tried It“), her choice. The square frame lies below
  the burned-in Czech captions, so one file serves both languages; the foot and the
  whole foot cover stay in frame.
- **Loading:** the ad image stays the LCP element, poster and fallback. `<video
  preload="none">` sits in an inert `<template>`; a small inline script inserts it
  after window load + idle and sets `src` and `poster` (the ad file already loaded).
  A `<video>` in the initial HTML, even without `src`, made the hero image finish
  about 350 ms later on a throttled phone. Skipped for reduced motion, data saver and 2G; paused off
  screen; pause/play button. The clip is 1 px inside the image box: edge to edge,
  Chrome counted it as a larger LCP element (46 656 vs 46 568 px²).
- **Phone (390 × 844):** headline 358–410, benefit line 414–475, price 480–522, gold
  button 530–573, shipping / end date / COD to 648 px: all above the cookie card
  (670 px). The set cards start at 706 (CZ) / 685 (EN); the picker's own
  „Do košíku“ is now below the first screen. The ad keeps its 264 px.
- The page has no video section, so there is no „▶ Podívejte se“ link.

## After merge

Deploy, purge 1128 + 1129, then: live 390 × 844 + desktop screenshots CZ/EN,
PageSpeed mobile LCP ≤ 2.5 s, 3 páry = 607 Kč in the cart, empty the cart.
