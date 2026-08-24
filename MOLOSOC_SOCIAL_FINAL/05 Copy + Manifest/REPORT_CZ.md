# MOLOSOC Czech Social Set (CZ) — Full 20-Post Set

Translated from the approved 20-post English (EN) set. Same masters, same template per post (SIDE or BOTTOM), same crop/placement/safe-zone logic, same visual system — only the copy and, where the Czech text required it, headline size/line-breaks/support wrapping differ from EN.

## EN review (before starting CZ)

Reviewed all 20 approved EN posts together as a set (combined contact sheet). No problems found — consistent premium Scandinavian feel, correct template variety, no boundary issues. No changes made to any EN post, crop, copy, or layout value.

## Font coverage fix (infrastructure, not a design change)

The locked font files (`fonts/DMSerifDisplay-Regular.ttf`, `Mulish-Regular/Medium/SemiBold.ttf`) turned out to be Latin-only subsets — missing every Czech caron/háček character (č, ď, ě, ň, ř, š, ť, ů, ž and uppercase). Rendering Czech copy with them would have silently dropped those glyphs.

Fix: replaced each file with the full Google Fonts release of the exact same family/weight (verified: identical `unitsPerEm`/ascent/descent, and identical advance width for every Latin glyph tested — a metric-compatible superset, not a different font). Regression-checked 3 existing EN renders (posts 001, 013, 019) before and after the swap: **byte-for-byte identical output**. This is a coverage fix, not a font substitution — same typeface, now complete.

## Template choice — unchanged from EN

| Post | Template (EN = CZ) |
|---|---|
| 001, 002, 004, 005, 008, 009, 011, 012, 014, 016, 017, 019, 020 | TEMPLATE_BOTTOM |
| 003, 006, 007, 010, 013, 015, 018 | TEMPLATE_SIDE |

7 SIDE / 13 BOTTOM — identical split to the EN set, because every post reuses the exact same `template`, `photoCrop`/`crop`, and `textAreaBounds` values as its EN counterpart. No template was changed, no crop was changed, no master was touched.

## Where Czech copy needed adjustment

11 of 20 posts fit at the exact same headline size and line-break as EN (001, 002, 004, 008, 009, 011, 014, 016, 017, 019, 020) — Czech happened to measure close enough to English for these.

9 posts needed a smaller headline size, a different (but same-word) line-break, or both — because Czech is, word for word, usually longer than English, and the SIDE panel in particular is a narrow, fixed-width column:

| Post | Template | EN size | CZ size | Line-break changed? |
|---|---|---|---|---|
| 003 | SIDE | 61px | 57px | no |
| 005 | BOTTOM | 93px | 93px | yes (fits the same size once regrouped) |
| 006 | SIDE | 82px | 67px | no |
| 007 | SIDE | 62px | 55px | no |
| 010 | SIDE | 86px | 62px | yes |
| 012 | BOTTOM | 93px | 93px | yes (fits the same size once regrouped) |
| 013 | SIDE | 72px | 49px | no |
| 015 | SIDE | 62px | 58px | yes |
| 018 | SIDE | 64px | 54px | no |

Every size above is that post's real ceiling — the largest size (found by measuring every candidate line-break, not just the first one tried) that still clears its own textBox width with a safety margin of several pixels. None were reduced further than the text required. 013 and 018 land furthest from their EN size (72→49 and 64→54) simply because "krémem, který máte rádi" and "Dejte nohy nahoru. Doslova." are long relative to their narrow SIDE columns (335px and 261px) — confirmed visually afterward that both still read as large, confident headlines, not a cramped afterthought.

Two posts also needed their support line wrapped to a second/third line (same mechanism as several EN posts already used for long support sentences), because the Czech sentence didn't fit on one line at the same support size as EN:

- **013**: "MOLOSOC pomáhá, aby zůstal tam, kam patří." → wrapped 2 ways, same 16px support size as EN.
- **018**: "Krém naneste. MOLOSOC natáhněte. Čas na odpočinek." → wrapped 3 ways, same 13px support size as EN.

Text-block vertical position (textBox.y, support/divider/brand Y) was recentered within each post's cream panel/band wherever headline size or line-count changed, using the same centering method used to build the EN set originally — never eyeballed.

## Quality checks performed on every render

- Master sha256 verified before every render — same masters as EN, byte-for-byte, still untouched.
- Boundary checks (text within its own textBox, cream-panel/band edges never crossed) passed on all 20 CZ renders.
- Post-render ink-presence check confirms every text element rasterized (catches a silent glyph-drop, which is exactly the risk the font-coverage fix above addresses).
- Rounded outer corners (32px radius), colors, dividers, and wordmark sizing unchanged from EN.
- No text on any photograph in any of the 20 CZ posts.

## Output paths

- EN finals: `assets/social/output/EN/MOL_POST_001_EN.png` … `MOL_POST_020_EN.png`
- CZ finals: `assets/social/output/CZ/MOL_POST_001_CZ.png` … `MOL_POST_020_CZ.png`
- `output/MANIFEST_EN.json` — EN manifest (unchanged)
- `output/MANIFEST_CZ.json` — CZ manifest (source master, template, EN/CZ copy side-by-side per post)
- `output/REPORT_CZ.md` — this report
