# CZ organic growth plan — Issue #207

Research and planning only. No page, template, SEO setting, permalink or
production change is made or implied by this document; every recommendation
needs its own approved Block. Do not start implementation from this plan
automatically.

## 1. Evidence status (read this first)

| Source | Accessible? | Used how |
|---|---|---|
| Google Search Console (CZ queries, impressions, CTR, positions) | **No.** Not reachable from this session; no export exists in either repo (`automations/analytics/` only describes the API pull; TrafficDom `clients/molosoc/evidence.toml` says Search Console evidence lives inside the weekly analysis document, which is not in the repo). | Data unavailable. |
| Semrush / any Czech keyword-volume tool | **No** (no mention of Semrush anywhere in either repo). | Data unavailable. |
| Competitor rankings (DM, Rossmann, Dr. Max, Notino, Czech blogs) | **No** live SERP access. | Data unavailable. |
| Keyword volumes in `docs/site-structure.md` / `docs/seo-geo-plan.md` | Yes, but they are **English-language** Keywords Everywhere figures (e.g. "cracked heels cream" 27,100). They say nothing about Czech demand. | Used only as a loose hint that a topic is generally searched; **no Czech volume is stated or implied anywhere below.** |
| Repo copy (`seo/cz-pages/`, `i18n/cz/`, theme templates, #200/#202/#203 docs) | Yes | Basis of the inventory and the on-page recommendations. |
| #202 live observations | Quoted second-hand via `docs/seo-followup-203.md`; not re-verified (molosoc.com unreachable from the sandbox). | Context only. |

Consequence: the ranking in §3 is a **provisional, judgement-based ranking**
(topic fit × intent × existing coverage), not a data-driven one. Every row has
a "confirm with" column naming the exact GSC/tool check that would validate or
overturn it. Indexing of six URLs was only requested on Oct 16 (re-inspect
Oct 23–30), so GSC may well show little or nothing for them yet; treat the
first usable query export as the trigger to revisit this plan, not this
document's order.

## 2. Existing CZ URL inventory and intent served

Paths are from the copy in `seo/cz-pages/` and the `https://molosoc.com/cz/…`
links in `i18n/cz/`. "Live state" is not verified here (see §1).

| CZ URL | Role | Intent it serves today | Current title (repo) |
|---|---|---|---|
| `/cz/` (homepage) | Brand hub | Navigational / brand; topic hub linking all three pillars | `i18n/cz/cz-homepage-copy.md` |
| `/cz/popraskane-paty/` | Pillar (EN: cracked-heels) | Informational: why heels crack, what helps; bridges to cream+cover | Popraskané paty: Proč vznikají a jak se jich skutečně zbavit |
| `/cz/zarostly-nehet/` | Pillar (EN: ingrown-toenails) | Informational, health-adjacent: causes, home care, when it is more than a nail problem | Zarostlý nehet: Proč vzniká a co skutečně pomáhá |
| `/cz/kurici-oko/` | Pillar (EN: hardened-skin-calluses) | Informational: corn vs. callus, why they form, what softens them | Kuří oko a mozoly: Proč vznikají a co je změkčí |
| `/cz/kurici-oko/jak-odstranit/` | Spoke (EN: callus-remover) | Informational / how-to: removal methods | Jak odstranit kuří oko: co skutečně funguje |
| `/cz/kurici-oko/na-chodidle/` | Spoke (CZ-only, no EN twin) | Informational: corn under the sole | Kuří oko na chodidle: proč je jiné a co s ním |
| `/cz/magazin/` | Hub | Navigation: "Kde začít podle toho, co vás trápí" (#203) | — (theme template) |
| `/cz/navleky-na-nohy/` | Category (EN: foot-covers) | Commercial investigation: reusable cover vs. disposable sock mask | Návleky na nohy \| Hydratační návlek na nohy — Molosoc |
| `/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/` | Product | Transactional + proof (before/after, cream-you-own) | Návlek na nohy Molosoc — Krém, který už doma máte, konečně funguje |

**Not published in Czech (EN exists or planned):** dry skin on feet
(`/dry-skin-feet/`), foot cream that works (`/foot-cream-that-works/`),
cracked-heels cream / treatment / fix-permanently spokes, ingrown
treatment / prevent spokes. So in Czech the whole "suchá kůže / hydratace /
krém" cluster has no dedicated page; the only Czech coverage of it is one H3
on the homepage ("Popraskané paty a suchá kůže") and sections inside the
pillars. Do not duplicate topics already published: the three pillars and two
spokes above already own *popraskané paty příčina*, *zarostlý nehet*,
*zarostlý nehet na palci*, *kuří oko*, *mozoly na nohou*, *jak odstranit kuří
oko* and *kuří oko na chodidle*.

## 3. Provisional ranking of CZ opportunities

Intent key: **I** = informational, **C** = commercial investigation, **T** =
transactional/product. "Fit" = how directly MOLOSOC's reusable cover + the
customer's own cream answers the searcher's need (the site must never claim a
medical cure). Volumes: **not available for CZ — none stated.**

| # | Opportunity (CZ query theme) | Intent | Fit with cream + reusable cover | Existing page that should carry it | Confirm with |
|---|---|---|---|---|---|
| 1 | **popraskané paty** — co pomáhá, mast/krém na popraskané paty, proč praskají (incl. winter angle) | I → C | **Highest.** Pillar already frames "mast se otře dřív, než se vstřebá", which is exactly the cover's job; matches the best-performing proof content (before/after heels). | `/cz/popraskane-paty/` | GSC: queries containing *popraskan\*/paty/mast/krém* → page, country CZ; positions 8–30 are the quick wins |
| 2 | **mast / krém na popraskané paty** (the product-shaped half of #1) | C → T | **Highest.** Searcher already plans to buy a cream; "works with your cream" is the angle. | Section of `/cz/popraskane-paty/` (already has H3 "Mast na popraskané paty — co v ní hledat") then link to product | GSC: does this query appear against the pillar or not at all? |
| 3 | **hydratace nohou / jak hydratovat nohy přes noc / krém na nohy přes noc / ponožky po krému** | I → C | **High.** Directly the "cream needs sealed contact time" story; closest match to the cover's use case. | **No CZ page.** Interim: strengthen the cracked-heels pillar and category; new CZ page is a later decision (see §4, R7) | GSC/Semrush CZ: any volume for *hydratace nohou*, *přes noc* variants |
| 4 | **suchá kůže na chodidlech / suché nohy** | I | **High**, but no CZ page. EN pillar 4 exists (`/dry-skin-feet/`) with no CZ twin. | Interim: section in `/cz/popraskane-paty/`; later: CZ translation of pillar 4 (needs approval, see R7) | Same as #3 |
| 5 | **kuří oko** (+ *jak odstranit kuří oko*, *kuří oko na chodidle*) | I | **Low–medium.** Cover/cream helps only with the "soften afterwards, keep it from returning" part; the main intent (removal) is not what the product does. | Already fully covered by 3 pages — **do not add more.** | GSC: impressions vs. clicks vs. product-page sessions from these URLs |
| 6 | **zarostlý nehet** (+ *na palci*) | I (health-adjacent) | **Low.** Only the "softer surrounding skin" angle; high medical sensitivity; many searchers need a doctor. | Already covered by the pillar — **do not add more; keep claims minimal.** | GSC as #5 |
| 7 | **maska na nohy / hydratační maska na nohy / ponožky na hydrataci** (the disposable-product search that the cover competes with) | C | **High for conversion**, but the category page is titled *návleky na nohy*, which in Czech may read as shoe covers/protective covers. This is a hypothesis taken from the EN "foot covers" PPE-overlap warning in `docs/seo-geo-plan.md` §3, **not** checked against Czech SERPs. | `/cz/navleky-na-nohy/` (category) | Live SERP check of *návleky na nohy* vs. *maska na nohy*; GSC: which queries the category/product pages receive |

Ranking logic: 1–2 first because the page exists, the intent is
cream-adjacent, and the proof content already lives on the product page.
3–4 and 7 carry the highest purchase fit but need either demand evidence or a
new page, so they are gated on data (§4 R7). 5–6 are where impressions are
most likely to come from while qualified traffic stays low — see §5.

## 4. Recommendations for existing pages (priority order)

All are **proposals for a later Block**, not changes made here. Where a title
or meta change is proposed, make it only after a GSC query export confirms the
page is indexed and shows which query it actually receives (same stance as
#200: "a rewrite without GSC query data would be a guess").

**R1 — `/cz/popraskane-paty/` (priority 1).**
- Intent/title/meta: keep the informational lead, add the product-shaped
  phrase the page already uses in its H3. Candidate (test only after GSC
  confirms): title *Popraskané paty: příčiny a mast, která se skutečně
  vstřebá*; keep the meta factual and non-curative.
- Add a short seasonal block ("Proč paty praskají hlavně v zimě" — heating,
  socks/tights; fits the Oct–Mar habit window in `docs/seo-geo-plan.md` §6)
  and a short "Suchá kůže na patách a chodidlech" block. This captures
  opportunity 4 without a new URL.
- Genuinely useful FAQ (3–4 items, plain answers): *Jak často natírat paty?*,
  *Pomáhá krém přes noc?*, *Kdy s popraskanými patami k lékaři?* (e.g. deep,
  bleeding or infected-looking cracks — send them to a doctor, do not treat;
  no medical-condition-specific framing, per the non-medical content
  rules in `docs/site-structure.md` and `docs/wp-build-spec.md`). Note that FAQ rich results are largely limited to authoritative
  government/health sites, so the value is user usefulness and GEO
  extractability, not a SERP feature.
- Internal links: one contextual link to the product page "Skutečné výsledky"
  section (already present at the bottom — move a second one next to the
  "Proč se to stejně vrací" H3, where the problem peaks); keep the existing
  Související čtení block.

**R2 — `/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/` (priority 2).**
- Highest-value *conversion* page; do not chase impressions here. Verify
  title/meta in GSC once indexed; keep the proof-led angle.
- The page already has "Jak to funguje" / "Jak ho použít" (30–60 min, rinse,
  dry, reuse) in `site/theme/page-moisture-lock-foot-cover.php`. Do not add a
  second instructions block; extend that section with only the missing
  "Pro koho je (a pro koho není)" eligibility and safety guidance, with honest
  limits (not a medical device, not for broken or infected skin) — qualified visitors need this before
  buying, and it supports #3/#4 wording ("hydratace", "přes noc") naturally.

**R3 — `/cz/navleky-na-nohy/` (priority 3).**
- Test whether Czech searchers use *maska na nohy* rather than *návleky na
  nohy* (opportunity 7). If yes, qualify the title/H1 so the page is not read
  as shoe covers (e.g. *Opakovaně použitelný hydratační návlek na nohy — na
  krém, který už máte*), mirroring the EN "qualify `foot covers` fast" rule.
  Do **not** change the slug or permalink.
- The "co skutečně znamená hydratační" section is the right home for the
  *přes noc / hydratace nohou* wording until a dedicated page is approved.

**R4 — `/cz/kurici-oko/` and its two spokes (priority 4, restraint).**
- Already comprehensive; extra content mostly adds impressions. Only add a
  clear next-step link: from "Co dělat po odstranění, aby se nevrátilo"
  (`/jak-odstranit/`) and "Změkčení kůže jako první krok" (`/na-chodidle/`)
  to the product page, phrased as supporting softening/aftercare, never as a
  corn remover. No title/meta change without GSC data.

**R5 — `/cz/zarostly-nehet/` (priority 5, restraint).**
- Keep as is. Do not push product calls harder here; this is the most
  medically sensitive intent and the product fit is weakest. Confirm the
  "kdy jde o víc než nehet" guidance stays prominent.

**R6 — `/cz/magazin/` (data task, not a content task).**
- #203 already added topic navigation. Add nothing until GSC shows whether it
  receives its own queries.

**R7 — Decisions for Žaneta (not to be started automatically).**
1. After the first usable CZ query export, is a CZ page for *suchá kůže na
   nohou / hydratace nohou* (translation of EN pillar 4, or a new CZ-first
   page) justified? It is the largest CZ topic with product fit and no page.
2. Same question for the CZ twins of the EN cream spokes
   (`cracked-heels-cream`) — only if #1 queries show demand.
3. Approve a CZ-language SERP check for *návleky na nohy* vs. *maska na nohy*.

## 5. What can generate qualified traffic vs. only impressions

**Likely qualified (searcher has a cream/dryness problem and a buying
path):** popraskané paty + mast/krém queries (#1–2); hydratace/přes noc
(#3–4, once a page exists); *maska na nohy*-type commercial queries (#7); any
query that lands on the product page directly.

**Likely impressions only:** *kuří oko* head terms and *jak odstranit kuří
oko*, *zarostlý nehet* and *zarostlý nehet na palci*. These are high-volume in
English and plausibly high in Czech, but the searcher wants removal or a
doctor, not a cream-plus-cover routine. Expect many impressions, low
product-page click-through, and a risk of medical-claim drift; the EN plan
already marks this class as health-adjacent (`docs/site-structure.md` §7
discard list).

How to tell once data exists (all in GSC/GA4, read-only): per URL,
impressions → clicks → sessions on the product/category page → add-to-cart.
A page earning clicks but no product-page sessions is an impressions page.
Judge success by product-page sessions and orders from organic CZ, not by
impressions or average position.

## 6. Data tasks that unblock this plan (for the operator, not Claude)

1. GSC Performance export, **Country = Czechia**, last 3 months (after Oct
   23–30 re-inspection), dimensions Query × Page; save as an operator
   artifact, not committed if it contains anything private.
2. For each §3 row, record: queries received, impressions, clicks, position.
   Fill the "confirm with" column and re-rank.
3. One manual SERP look (in Google.cz and Seznam.cz, signed-out) for
   *popraskané paty*, *mast na popraskané paty*, *hydratace nohou*, *maska na
   nohy*, *návleky na nohy*: who ranks (retail vs. blog vs. clinic), and
   whether any competitor targets "krém + návlek".
4. If a Semrush CZ database is available later, add volumes **with source and
   date** to the §3 table; until then none are stated.

## 7. Scope guard

This Block changes one file: `docs/cz-organic-growth-207.md`. No content was
published, no template, permalink, robots/sitemap or WP setting changed, no
tool or credential used, no live URL requested. Verification was
repo-only (file inventory and copy read-through; no automated tests apply to
a markdown document).
