# Molosoc Site Build — Master Status
**Last updated:** July 23, 2026
**Reference structure doc:** `molosoc_site_structure_summary.md` (updated version — 5 TOFU pillars + 6 spokes, in project files)

---

## ✅ DONE — Core 3 Pages (copy + schema both locked)

| Page | Copy file | Schema file | Status |
|---|---|---|---|
| Homepage (`molosoc.com/`) | `01-homepage/homepage-copy.md` | `01-homepage/homepage-schema.html` | ✅ Complete |
| Category (`molosoc.com/foot-covers/`) | `02-category/category-copy.md` | `02-category/category-schema.html` | ✅ Complete |
| Product (`molosoc.com/foot-covers/moisture-lock-foot-cover/`) | `03-product/product-copy.md` | `03-product/product-schema.html` | ✅ Complete |

## 🔄 IN PROGRESS — TOFU Pillars

| Page | Copy file | Schema file | Status |
|---|---|---|---|
| Pillar 1 — Cracked Heels (`molosoc.com/cracked-heels/`) | `04-pillar1-cracked-heels/pillar1-cracked-heels-copy.md` | `04-pillar1-cracked-heels/pillar1-cracked-heels-schema.html` | ✅ Complete (publish date placeholder pending) |
| Pillar 2 — Ingrown Toenails (`molosoc.com/ingrown-toenails/`) | `05-pillar2-ingrown-toenails/pillar2-ingrown-toenails-copy.md` | `05-pillar2-ingrown-toenails/pillar2-ingrown-toenails-schema.html` | ✅ Complete (publish date placeholder pending) |
| Pillar 3 — Hardened Skin & Calluses (`molosoc.com/hardened-skin-calluses/`) | `06-pillar3-hardened-skin-calluses/pillar3-hardened-skin-calluses-copy.md` | `06-pillar3-hardened-skin-calluses/pillar3-hardened-skin-calluses-schema.html` | ✅ Complete (publish date placeholder pending) |
| Pillar 4 — Dry Skin on Feet (`molosoc.com/dry-skin-feet/`) | `07-pillar4-dry-skin-feet/pillar4-dry-skin-feet-copy.md` | `07-pillar4-dry-skin-feet/pillar4-dry-skin-feet-schema.html` | ✅ Complete (publish date placeholder pending; 3 spoke links not yet built per doc §9) |
| Pillar 5 — Cream That Works (`molosoc.com/foot-cream-that-works/`) | `08-pillar5-cream-that-works/pillar5-cream-that-works-copy.md` | `08-pillar5-cream-that-works/pillar5-cream-that-works-schema.html` | ✅ Complete (publish date placeholder pending; 3 spoke links not yet built per doc §9) |

**🎉 All 5 TOFU pillars are now complete.**

## 🔄 IN PROGRESS — Spoke Articles

| Page | Copy file | Schema file | Status |
|---|---|---|---|
| Spoke 1 — Ingrown Toenails Treatment (`molosoc.com/ingrown-toenails/treatment/`) | `09-spoke1-ingrown-toenails-treatment/spoke1-ingrown-toenails-treatment-copy.md` | `09-spoke1-ingrown-toenails-treatment/spoke1-ingrown-toenails-treatment-schema.html` | ✅ Complete (publish date placeholder pending) |
| Spoke 2 — Callus Remover (`molosoc.com/hardened-skin-calluses/callus-remover/`) | `10-spoke2-callus-remover/spoke2-callus-remover-copy.md` | `10-spoke2-callus-remover/spoke2-callus-remover-schema.html` | ✅ Complete (publish date placeholder pending) |
| Spoke 3 — How to Prevent Ingrown Toenails (`molosoc.com/ingrown-toenails/prevent/`) | `11-spoke3-prevent-ingrown-toenails/spoke3-prevent-ingrown-toenails-copy.md` | `11-spoke3-prevent-ingrown-toenails/spoke3-prevent-ingrown-toenails-schema.html` | ✅ Complete (publish date placeholder pending) |
| Spoke 4 — Cracked Heels Cream (`molosoc.com/cracked-heels/cracked-heels-cream/`) | `12-spoke4-cracked-heels-cream/spoke4-cracked-heels-cream-copy.md` | `12-spoke4-cracked-heels-cream/spoke4-cracked-heels-cream-schema.html` | ✅ Complete (publish date placeholder pending) |
| Spoke 5 — Cracked Heels Treatment (`molosoc.com/cracked-heels/cracked-heels-treatment/`) | `13-spoke5-cracked-heels-treatment/spoke5-cracked-heels-treatment-copy.md` | `13-spoke5-cracked-heels-treatment/spoke5-cracked-heels-treatment-schema.html` | ✅ Complete (publish date placeholder pending) |
| Spoke 6 — How to Fix Cracked Heels Permanently (`molosoc.com/cracked-heels/fix-permanently/`) | `14-spoke6-fix-cracked-heels-permanently/spoke6-fix-cracked-heels-permanently-copy.md` | `14-spoke6-fix-cracked-heels-permanently/spoke6-fix-cracked-heels-permanently-schema.html` | ✅ Complete (publish date placeholder pending) |

**🎉🎉 ALL 15 PAGES IN THE SITE STRUCTURE DOC ARE NOW COMPLETE:**
Homepage, Category, Product, all 5 TOFU Pillars, and all 6 Spoke articles — copy + schema for every single one.

Each copy file matches the structure doc's title tag, meta description, H1/H2/H3s exactly — nothing renamed or reworded from the locked structure. Each schema file is a ready-to-paste `<script type="application/ld+json">` block for that page's `<head>`.

---

## ⚠️ OPEN ITEMS — needs your input before these are 100% final

| Item | Where it lives | What's needed |
|---|---|---|
| Product SKU | `03-product/product-schema.html` | Not yet assigned — placeholder left in schema, drop in when ready |
| Currency check | `03-product/product-schema.html` | Resolved 2026-08-16 — schema set to 229 CZK (matches WooCommerce checkout); €10 is the EN/EU display price only |
| Publish dates | All 11 Article schema files (5 pillars + 6 spokes) | `datePublished`/`dateModified` are placeholders — drop in real dates once each page goes live |

### ✅ Resolved (previously open, now filled in)
- Product image: `https://molosoc.com/wp-content/uploads/2026/04/Molosoc-Product-Shot-2.jpg`
- Social profiles (Facebook, Instagram, TikTok, YouTube, LinkedIn, X): all in homepage schema
- 3-month before/after photo: `https://molosoc.com/wp-content/uploads/2026/07/Molosoc-Real-3-months-results.jpg`
- Mom-reaction video: `https://www.youtube.com/shorts/GlJ06PdQxg4`
- Salon touch-up price: $15–30 per session depending on pedicure level (Product page, Persona 3)

---

## 🔜 NOT STARTED YET

Nothing remains from the locked site structure doc — all 15 pages are built (copy + schema).

The only future work not yet possible: fresh spoke-level keyword research for Pillars 4 (Dry Skin on Feet) and 5 (Cream That Works), per doc §9 — those pillars don't have spokes specified yet, so there's nothing to draft against until that research exists.

---

## Confirmed facts locked in across all copy (so nothing gets re-invented per page)
- Price: **€10** display price on EN pages (charged as 229 CZK at checkout); **229 Kč** on CZ pages
- Durability: **10+ uses** minimum before replacement (conservative — real range may be 15–30)
- Session length: **30–60 minutes** (not overnight)
- Disposable mask comparison price: **$6–10** per single-use mask
- Brand social profiles: Facebook, Instagram, TikTok, YouTube, LinkedIn, X — all live in homepage schema `sameAs`
