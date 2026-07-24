# Molosoc — Core Site Structure (Homepage / Category / Product)
**Consolidated reference — main structure for dev/build.**

This document ties together the three-layer architecture (Brand → Category → Product) with exact URLs, titles, headings, and internal linking, plus the TOFU pillar articles and their spoke articles that feed the Homepage and Product page. Use this as the single source of truth for building the whole site.

---

## 1. Site map at a glance

```
molosoc.com/
  ├─ molosoc.com/foot-covers/
  │     └─ molosoc.com/foot-covers/moisture-lock-foot-cover/
  │
  └─ TOFU pillars (linked from homepage, deep-link down to Product page — see §7; spoke articles nested under each pillar — see §8)
        ├─ molosoc.com/cracked-heels/
        ├─ molosoc.com/ingrown-toenails/
        ├─ molosoc.com/hardened-skin-calluses/
        ├─ molosoc.com/dry-skin-feet/
        └─ molosoc.com/foot-cream-that-works/
```

| Layer | URL | Old URL to redirect |
|---|---|---|
| Homepage (Brand) | `molosoc.com/` | — |
| Category | `molosoc.com/foot-covers/` | — |
| Product | `molosoc.com/foot-covers/moisture-lock-foot-cover/` | `molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/` → 301 redirect required |
| TOFU pillars (×5) | see §7 | — |

---

## 2. HOMEPAGE

**URL:** `molosoc.com/`
**Title tag:** Molosoc® | Foot Care That Actually Sticks
**Meta description:** Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.
**H1:** Foot care you'll actually stick with

**H2 — Why foot care never sticks**
- H3: Feet deserve real care, not just intent
- H3: Care should be simple enough to actually stick
- H3: You don't need new products — you need the right ritual
- H3: Foot care is self-care, not vanity

**H2 — Foot care, topic by topic** *(TOFU hub — each H3 links to a future standalone pillar article, see §7)*
- H3: Cracked heels & dry skin → Pillar 1
- H3: Ingrown toenails → Pillar 2
- H3: Hardened skin & calluses → Pillar 3
- H3: Dry skin on feet → Pillar 4
- H3: Making the cream you already own actually work → Pillar 5

**H2 — How Molosoc helps right now**
- H3: Meet the Foot Cover → **links to Product page**

**H2 — The reusable alternative**
- H3: What is a moisture-lock foot cover? → **links to Category page**

---

## 3. CATEGORY PAGE

**URL:** `molosoc.com/foot-covers/`
**Title tag:** Reusable Foot Covers | Moisture-Lock Foot Cover — Molosoc
**Meta description:** Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results.
**H1:** Reusable foot covers that lock moisture in — not just once

**H2 — Disposable sock masks vs. reusable foot covers**
- H3: What's actually inside a single-use sock mask
- H3: Why reusable changes the math
- H3: One cover, any cream — not locked to a pre-filled formula

**H2 — What "moisture-lock" actually means**
- H3: How the seal traps moisture against skin
- H3: Why mess and slipping usually kill the routine
- H3: Cream-agnostic, by design

**H2 — Reusable vs. disposable: the real cost**
- H3: Cost per use over a month
- H3: Cost per use over a year
- H3: What you're not paying for anymore (salon touch-ups)

**H2 — Who this is for**
- H3: Already have a cream you love → **links to Product page**
- H3: Just had a pedicure and want it to last → **links to Product page**
- H3: Buying this for someone else → **links to Product page**

---

## 4. PRODUCT PAGE

**URL:** `molosoc.com/foot-covers/moisture-lock-foot-cover/`
**Redirect:** old slug `molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/` → 301 to this URL
**Title tag:** Molosoc Foot Cover — The Cream You Already Own, Finally Working
**Meta description:** Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.
**H1:** Molosoc Foot Cover

**H2 — The cream you already own, finally working** *(Persona 1 — Cream Graveyard Owner)*
- H3: Why creams get abandoned halfway through
- H3: What changes when the mess disappears
- H3: Works with the cream in your drawer right now

**H2 — Real results, no filters** *(Persona 2 — Ingrown-Nail/Hardened-Skin Sufferer)*
- H3: 3-month before/after, time-stamped
- H3: What actually happens to cracked heels over time
- H3: Unfiltered reactions (mom-reaction style content)
- ⚠️ **This is the deep-link target for the future cracked-heels TOFU article** (skips the Category page per SEO/GEO plan §7b)

**H2 — Make the pedicure last** *(Persona 3 — After-Pedicure Maintainer)*
- H3: Why salon results fade in ~10 days
- H3: Cost per use vs. another salon visit
- H3: Home spa, without the salon price

**H2 — Give it as a gift** *(Persona 4 — Gift Buyer)*
- H3: For someone always on her feet
- H3: One before/after photo says it all
- H3: How to gift it (simple, low-effort framing)

**H2 — How it works**
- H3: What's in the box
- H3: How to use it with any cream
- H3: Reusable — how many uses to expect

---

## 5. Internal linking map

```
Homepage
  ├─ "Foot care, topic by topic" H3s → future TOFU articles (not yet built)
  ├─ "Meet the Foot Cover"        → Product page
  └─ "What is moisture-lock..."   → Category page

Category page
  └─ "Who this is for" H3s        → Product page

Future cracked-heels TOFU article
  └─ links straight down to       → Product page, "Real results, no filters" H2
     (skips Category page — someone with a real problem needs proof, not the format argument)
```

---

## 6. Keyword rationale by layer (for reference)

| Layer | Keyword role | Notes |
|---|---|---|
| Homepage | "foot care" — territory/voice, not a head-term ranking play | Local/branded competitor terms (foot care clinic, isdin foot care, etc.) discarded — irrelevant intent |
| Category | `foot covers` (3,600/mo) head term, `reusable foot covers` on-page target, `moisture-lock foot cover` (0 vol) owned descriptor being built | `moisture lock` (590/mo) used only as supporting phrase; `foot cover socks` (480/mo) and `lock cover`/`moisture proof` discarded as noise |
| Product | Long-tail, persona/proof-intent — not volume-driven | No head-term target; page converts on trust, not search traffic |

**Site-wide flag:** avoid "diabetic foot treatment" and similar medical-condition framing anywhere — Molosoc is explicitly not a medical device.

---

## 7. TOFU Pillar Articles (Awareness/Problem-Education layer — sits under Homepage)

Five pillars total. Each pillar is a hub article: title/H1/H2/H3 built from real keyword data where available, with a "Go deeper" H2 whose H3s become future spoke articles once a pillar's own traffic justifies it. Every pillar deep-links down to the Product page, to the H2 matching its persona — not to the Category page (per SEO/GEO plan §7b: someone with a real problem needs proof, not the reusable-vs-disposable argument).

**Keyword verification status:**
| Pillar | Keyword data | Status |
|---|---|---|
| 1. Cracked Heels | ✅ verified (Keywords Everywhere) | Locked |
| 2. Ingrown Toenails | ✅ verified (Keywords Everywhere) | Locked |
| 3. Hardened Skin & Calluses | ✅ verified (Keywords Everywhere) | Locked |
| 4. Dry Skin on Feet | ✅ verified (Keywords Everywhere) | Locked |
| 5. Cream That Works | ✅ verified (Keywords Everywhere) | Locked |

**Heading rule applied across all 5 pillars:** use the exact verbatim search term as the H2/H3 when that heading is directly answering a specific searched query (best for featured snippets and AI/GEO answer matching). Use natural language only for connective/bridge sections where no underlying query exists.

**Site-wide discard list for this content type:** medical/clinical-condition terms (paronychia, nail fungus, ICD codes, "diabetic foot," "postpartum," "hereditary," anything implying diagnosis or a surgical procedure) — these carry real volume but conflict with the "not a medical device" positioning and belong to podiatry/medical sites, not Molosoc.

---

### Pillar 1 — Cracked Heels ✅ *(verified + exact-match audited)*

**URL:** `molosoc.com/cracked-heels/`
**Title tag:** Cracked Heels: Why They Happen and How to Actually Fix Them
**Meta description:** Cracked heels aren't just dry skin — here's what's really causing them, what makes them worse, and what actually helps (without the gimmicks).
**H1:** Cracked heels: what's really going on, and what helps

**H2 — What causes cracked heels** *(exact match, 210/mo)*
- H3: Dry skin losing its ability to stretch
- H3: Pressure and weight-bearing on the heel edge
- H3: Standing all day, especially in open-back shoes

**H2 — When cracked heels go from dry to painful** *(natural — no direct query, connective)*
- H3: Painful deep cracked heels *(exact, 880/mo)*
- H3: Severe cracked heels *(exact, 390/mo)*
- H3: Why "just moisturizing more" stops working at this stage

**H2 — Why moisturizer alone doesn't fix it** *(natural bridge, no query behind it)*
- H3: The routine most people already try
- H3: Where that routine breaks down
- H3: What actually needs to happen for cream to work

**H2 — Go deeper**
- H3: Cracked heels cream *(exact, 27,100/mo)* → future spoke article
- H3: How to fix cracked heels permanently *(exact, 8,100/mo)* → future spoke article
- H3: Cracked heels treatment *(exact, 14,800/mo)* → future spoke article

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)

**Discarded from this cluster:** cracked heels diabetes (270), cracked heels pregnancy (260), cracked heels medicine (260), what deficiency causes cracked heels — all medical/diagnostic framing, off-brand for a non-medical-device product.

---

### Pillar 2 — Ingrown Toenails ✅ *(verified + exact-match audited)*

**URL:** `molosoc.com/ingrown-toenails/`
**Title tag:** Ingrown Toenails: Why They Happen and What Actually Helps
**Meta description:** An ingrown toenail can go from mildly annoying to genuinely painful fast. Here's what causes it, what actually helps at home, and when it's more than a nail problem.
**H1:** Ingrown toenails: what's happening, and what actually helps

**H2 — What causes ingrown toenails** *(exact match, 14,800/mo)*
- H3: How the nail edge starts growing into skin
- H3: Tight shoes and cutting nails too short
- H3: Why some people get them again and again

**H2 — Do ingrown toenails go away** *(exact match, 3,600/mo)*
- H3: When it resolves without intervention
- H3: When it doesn't — signs it's getting worse
- H3: Why waiting too long makes it harder to treat

**H2 — Why cutting it yourself often backfires** *(natural bridge, no direct query)*
- H3: Big toenail hurts *(exact, 5,400/mo)*
- H3: Ingrown big toe *(exact, 2,400/mo)*
- H3: What softening the surrounding skin actually changes

**H2 — Go deeper**
- H3: How to treat ingrown toenails *(exact, 22,200/mo)* → future spoke article
- H3: How to prevent ingrown toenails *(exact, 12,100/mo)* → future spoke article
- H3: Ingrown toenails treatment *(exact, 90,500/mo — biggest single keyword across all 5 pillars)* → future spoke article

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)

**Discarded from this cluster:** paronychia (301,000), nail fungus (90,500), onychocryptosis (12,100), ingrown toenails icd 10 (5,400), ingrown toenails postpartum (260), ingrown toenails hereditary (110), ingrown toenails tools (8,100 — implies cutting instruments), ingrown toenails removal (210 — implies surgical procedure), toenail hangnail (2,900 — different condition) — all medical/clinical or wrong-lane framing.

---

### Pillar 3 — Hardened Skin & Calluses ✅ *(verified + exact-match audited)*

**URL:** `molosoc.com/hardened-skin-calluses/`
**Title tag:** Hardened Skin & Calluses on Feet: Why They Form and What Softens Them
**Meta description:** Thick, hardened skin on your feet doesn't happen overnight — and it doesn't have to stay that way. Here's why calluses form and what actually softens them.
**H1:** Hardened skin and calluses: why they form, and what softens them

**H2 — Calluses on feet** *(exact match, 49,500/mo)*
- H3: Foot callus *(exact, 49,500/mo)*
- H3: Corns and calluses *(exact, 14,800/mo)*
- H3: Why it builds up gradually, not overnight

**H2 — Foot corn cure** *(exact match, 33,100/mo)*
- H3: Callus treatment *(exact, 12,100/mo)*
- H3: When thick skin starts affecting how you walk
- H3: Why picking or cutting it off yourself is risky

**H2 — Why soaking and filing alone don't keep it away** *(natural bridge, no query)*
- H3: The routine most people already try
- H3: Why hard skin comes back within weeks
- H3: What actually needs to change for softening to last

**H2 — Go deeper**
- H3: Callus remover *(exact, 90,500/mo — biggest spoke candidate in this pillar)* → future spoke article
- H3: How to remove thick dead skin from feet home remedy *(exact, 2,900/mo)* → future spoke article
- H3: How to get rid of hard skin on feet permanently *(exact, 2,400/mo)* → future spoke article

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)

---

### Pillar 4 — Dry Skin on Feet ✅ *(verified)*

**URL:** `molosoc.com/dry-skin-feet/`
**Title tag:** Dry Skin on Feet: Why It Happens and What Actually Helps
**Meta description:** Still dry after moisturizing? Here's what actually causes dry skin on feet, why cream alone doesn't fix it, and what actually helps it stop.
**H1:** Dry skin on feet: why it keeps coming back

**H2 — What causes dry skin on feet** *(exact match, 720/mo)*
- H3: Why soles dry out differently than the rest of the body
- H3: Socks, shoes, and trapped moisture loss
- H3: Seasonal triggers (heating, cold air, hot showers)

**H2 — Why are my feet so dry even when I moisturize?** *(exact match, 1,900/mo)*
- H3: The routine most people already try
- H3: Why cream doesn't stay on long enough to actually absorb
- H3: What actually needs to change for it to stick

**H2 — Socks, tights, and the dryness nobody talks about** *(natural — no direct query behind it)*
- H3: Why enclosed feet dry out differently
- H3: Winter habit-building vs. summer exposure
- H3: A private, low-effort ritual for this window

**H2 — Go deeper**
- H3: Dry foot skin treatment *(exact match, 1,300/mo)* → future spoke article
- H3: Dry skin feet home remedies *(exact match, 210/mo)* → future spoke article
- H3: Dry feet vs. cracked heels: what's the difference *(no direct query — comparison angle)* → future spoke article (cross-links back to Pillar 1)

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2), secondary tie to Persona 1

**Discarded from this cluster:** diabetes dry feet (6,600 — medical framing), extremely dry feet vitamin deficiency (590 — medical/nutritional diagnosis), "Is dry foot a vitamin deficiency?" and "What does dry skin on feet indicate?" (both invite diagnostic answers, off-brand)

---

### Pillar 5 — Making the Cream You Already Own Actually Work ✅ *(verified)*

**URL:** `molosoc.com/foot-cream-that-works/`
**Title tag:** Does Foot Cream Actually Work? Why It Fails, and What Fixes It
**Meta description:** Tried every foot cream with no results? The cream probably isn't the problem — here's why it fails and what actually makes it work.
**H1:** Does foot cream actually work? *(exact match — recurring "People Also Ask" question)*

**H2 — Why creams get abandoned halfway through** *(natural bridge — Persona 1's core situation, no query behind it)*
- H3: Real intent, no structure to keep going
- H3: The mess that makes people stop reaching for it
- H3: It's not that the cream failed

**H2 — How long does foot cream take to absorb?** *(exact match — recurring PAA)*
- H3: Why timing matters more than the cream itself
- H3: Should you put socks on after foot cream *(exact, 10/mo — small volume, but names the exact technique gap Molosoc solves)*
- H3: How to get soft feet overnight *(exact, 480/mo)*

**H2 — The cream graveyard problem** *(Persona 1 naming, no direct query)*
- H3: Why bathrooms end up with 2-3 half-used bottles
- H3: What that pattern actually says about the routine, not the product
- H3: Breaking the cycle without buying a new cream

**H2 — Go deeper**
- H3: Softening foot cream *(exact, 720/mo)* → future spoke article
- H3: How to moisturize feet overnight *(exact, 210/mo)* → future spoke article
- H3: Overnight foot cream *(exact, 140/mo)* → future spoke article

**Deep-links to:** Product page, "The cream you already own, finally working" H2 (Persona 1)

**Discarded from this cluster:** urea foot cream (33,100) and best urea cream for feet (2,400) — pushes a specific ingredient, contradicts cream-agnostic positioning; silicone socks (12,100), moisturizing socks (5,400), socks for moisturizing feet overnight (90) — competitor disposable-product terms, belong to Category page's format argument, not this pillar; athletes foot (90,500) — medical/fungal condition, discarded; foot file (33,100), foot peel (22,200) — unrelated product categories; best foot cream (9,900) and "How can I make my own foot cream?" — generic recommendation/DIY territory, off-brand since Molosoc doesn't formulate or recommend a specific cream; can i use foot cream on my hands (170) — wrong body part.

**Overlap note:** "Why are my feet still dry even when I moisturize?" also surfaced here but is already owned by Pillar 4 (verified, 1,900/mo) — not duplicated in this pillar to avoid cannibalization. Pillar 4 owns the *causation* angle; this pillar stays on the *routine/technique* angle.

---

## 8. Spoke Articles

Spoke articles sit one level under their parent pillar (nested URL), rank independently on their own exact-match head term, link back up to the pillar, and link down to the same Product page persona section as the pillar. Built using the `kw-fetch` skill against each pillar's already-captured Keywords Everywhere data.

### Spoke 1 — Ingrown Toenails Treatment
**Parent pillar:** Pillar 2 (Ingrown Toenails)
**URL:** `molosoc.com/ingrown-toenails/treatment/`
**Title tag:** Ingrown Toenails Treatment: What Actually Works
**Meta description:** From home softening to when a doctor needs to get involved — here's what actually treats an ingrown toenail, and what makes it worse.
**H1:** Ingrown toenails treatment: what actually works *(exact match, 90,500/mo)*

**H2 — How to treat ingrown toenails** *(exact match, 22,200/mo)*
- H3: Softening the skin before anything else
- H3: Why warm soaks are step one, not a cure
- H3: What changes once the pressure is relieved

**H2 — How to get rid of ingrown toenails** *(exact match, 22,200/mo — merged here rather than split, near-duplicate intent to "how to treat")*
- H3: The at-home approach that actually holds up over time
- H3: Why "getting rid of it" once isn't the same as it not coming back
- H3: Nail-trimming technique that prevents the repeat cycle

**H2 — When home treatment isn't enough** *(natural — no query, responsible-content section)*
- H3: Signs of infection to take seriously
- H3: When to see a podiatrist instead of continuing at home
- H3: Why waiting too long makes treatment harder later

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)
**Links back to:** Pillar 2

**KW-fetch flags:** ingrown toenails tools (8,100), ingrown toenails removal (210), ingrown toenails icd 10 (5,400) — all discarded, medical/surgical framing. "How to prevent ingrown toenails" (12,100) kept OFF this spoke — large enough and distinct enough in intent to become its own future spoke rather than being absorbed here.

---

### Spoke 2 — Callus Remover
**Parent pillar:** Pillar 3 (Hardened Skin & Calluses)
**URL:** `molosoc.com/hardened-skin-calluses/callus-remover/`
**Title tag:** Callus Remover: What Actually Works (And Why It Doesn't Last)
**Meta description:** Files, creams, pumice stones — here's an honest look at what actually removes hard skin, and why it keeps coming back no matter which one you use.
**H1:** Callus remover: what actually works *(exact match, 90,500/mo)*

**H2 — What actually removes hard skin** *(natural — frames the category honestly rather than pushing one method; important since Molosoc is not itself a removal tool)*
- H3: Filing and pumice stones — what they do and don't fix
- H3: Chemical/acid removers — how they work, and the risk of overdoing it
- H3: Why removal alone doesn't stop it from coming back

**H2 — How to remove thick dead skin from feet home remedy** *(exact match, 2,900/mo)*
- H3: Soaking first, always
- H3: Safe filing without over-thinning the skin
- H3: What actually needs to happen after removal for it to last

**H2 — How to get rid of hard skin on feet permanently** *(exact match, 2,400/mo — folded in here rather than built as a separate spoke; too much semantic overlap with this H2 to justify its own page)*
- H3: The pressure point that caused it is still there
- H3: Why one-time removal isn't the same as prevention
- H3: What actually slows the regrowth cycle

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)
**Links back to:** Pillar 3

**KW-fetch flags:** foot corn cure (33,100) and callus treatment (12,100) — both discarded here, already own their own H2 in parent Pillar 3, not duplicated. "How to get rid of hard skin on feet permanently" (2,400) folded into the H2 above rather than built standalone — its volume was too close to, and semantically overlapping with, content already planned for this spoke.

**Brand-safety note:** "callus remover" implies a physical tool or chemical product. Molosoc doesn't sell one — the H2 structure above is written to cover removal methods honestly, then bridge to moisture/consistency (Molosoc's actual lane), rather than implying Molosoc itself is a callus remover.

---

### Spoke 3 — How to Prevent Ingrown Toenails
**Parent pillar:** Pillar 2 (Ingrown Toenails)
**URL:** `molosoc.com/ingrown-toenails/prevent/`
**Title tag:** How to Prevent Ingrown Toenails (For Good)
**Meta description:** If this isn't your first ingrown toenail, the fix isn't just treating this one — it's changing what keeps causing them. Here's what actually prevents it.
**H1:** How to prevent ingrown toenails *(exact match, 12,100/mo)*

**H2 — Why do I keep getting ingrown toenails?** *(exact match, 1,600/mo — anchors the spoke on recurrence, not first-time causation, which stays with the parent pillar)*
- H3: The nail-cutting habit that causes repeat problems
- H3: Footwear that keeps recreating the same pressure point
- H3: Why one successful treatment doesn't mean it won't happen again

**H2 — How to stop ingrown toenails** *(exact match, 1,280/mo — near-synonym of "prevent," folded in rather than split into its own spoke)*
- H3: The trim shape that actually prevents regrowth into skin
- H3: Shoe-fit changes that remove the root pressure
- H3: Softening the surrounding skin as an ongoing habit, not a one-time fix

**H2 — Building a prevention routine that actually sticks** *(natural bridge — no direct query, ties to the site-wide "broken routine" reframe)*
- H3: Why prevention fails the same way treatment does — no structure
- H3: What a five-minute weekly check actually catches
- H3: Making it part of an existing routine instead of a new one

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)
**Links back to:** Pillar 2

**KW-fetch flags:** ingrown toenails hereditary (110), ingrown toenails postpartum (260), ingrown toenails tools (8,100) — discarded, medical/off-brand. "How do ingrown toenails happen" (2,900) and "how do you get ingrown toenails" (2,900) deliberately excluded — duplicate causation intent already owned by parent Pillar 2's H2, kept out to avoid the two pages competing for the same searcher.

---

### Spoke 4 — Cracked Heels Cream
**Parent pillar:** Pillar 1 (Cracked Heels)
**URL:** `molosoc.com/cracked-heels/cracked-heels-cream/`
**Title tag:** Cracked Heels Cream: What Actually Makes One Work
**Meta description:** Not all cracked-heel creams work the same way. Here's what actually matters — the ingredients, the timing, and why even a good cream can fail without the right routine.
**H1:** Cracked heels cream: what actually makes one work *(exact match, 27,100/mo)*

**H2 — What to actually look for in a cracked heels cream** *(natural — deliberately avoids a "best creams ranked" format, which would conflict with cream-agnostic positioning)*
- H3: Urea and other humectants — what they actually do
- H3: Thicker balms vs. lighter lotions — when each makes sense
- H3: Why ingredients matter less than how consistently it's used

**H2 — Best cream for cracked heels** *(exact match — surfaced in "también se buscó" data — answered honestly without turning into a product ranking)*
- H3: What "best" really depends on — severity, not brand
- H3: Why the most expensive option isn't always the most effective
- H3: The cream you already own is probably fine

**H2 — Why a good cream still doesn't fix cracked heels** *(natural bridge — mirrors the site-wide message hierarchy)*
- H3: The routine most people already try
- H3: Where that routine breaks down
- H3: What actually needs to happen for cream to work

**Deep-links to:** Product page, "The cream you already own, finally working" H2 (Persona 1) — *deliberate exception: this spoke is about cream effectiveness, matching the Cream Graveyard Owner's mindset, rather than Pillar 1's default Persona 2 (proof/pain) link*
**Links back to:** Pillar 1

**KW-fetch flags:** cracked heels diabetes (270), cracked heels pregnancy (260), cracked heels medicine (260), what deficiency causes cracked heels — all discarded, medical/diagnostic framing. "Cracked heels treatment" (14,800) and "how to fix cracked heels permanently" (8,100) deliberately kept off this spoke — both remain separate future spokes.

---

### Spoke 5 — Cracked Heels Treatment
**Parent pillar:** Pillar 1 (Cracked Heels)
**URL:** `molosoc.com/cracked-heels/cracked-heels-treatment/`
**Title tag:** Cracked Heels Treatment: What Actually Works, Step by Step
**Meta description:** Cream alone rarely fixes cracked heels. Here's the full picture — exfoliation, moisture, and the one step most routines skip.
**H1:** Cracked heels treatment: what actually works *(exact match, 14,800/mo)*

**H2 — The three things actual treatment requires** *(natural — broader "treatment" framing than the cream-only spoke, deliberately non-overlapping with Spoke 4)*
- H3: Removing the built-up dead skin first
- H3: Getting moisture in, not just on
- H3: The step most routines skip entirely — sealing it in

**H2 — When to see a podiatrist instead of treating it yourself** *(natural — responsible-content section, same pattern as Spoke 1)*
- H3: Signs a crack has gone past the surface layer
- H3: Painful deep cracked heels *(exact, 880/mo — cross-referenced from parent pillar as the "when it's serious" marker)*
- H3: Why bleeding or infection changes the plan

**H2 — Building a treatment routine that actually finishes** *(natural bridge — ties to site-wide broken-routine reframe; introduces Molosoc's mechanism as part of a broader answer, not the whole answer)*
- H3: Why most people stop after the first sign of improvement
- H3: What locking moisture in actually changes overnight
- H3: Making it a five-minute nightly step, not a project

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)
**Links back to:** Pillar 1

**KW-fetch flags:** cracked heels diabetes (270), cracked heels pregnancy (260), cracked heels medicine (260) — discarded, medical framing. "Cracked heels cream" (27,100, already Spoke 4) and "how to fix cracked heels permanently" (8,100) deliberately kept off this spoke to avoid the three pages competing for the same searcher.

---

### Spoke 6 — How to Fix Cracked Heels Permanently
**Parent pillar:** Pillar 1 (Cracked Heels)
**URL:** `molosoc.com/cracked-heels/fix-permanently/`
**Title tag:** How to Fix Cracked Heels Permanently (Not Just Temporarily)
**Meta description:** Cracked heels keep coming back for a reason — treatment fixes them once, but doesn't stop them from returning. Here's what actually makes it stick.
**H1:** How to fix cracked heels permanently *(exact match, 8,100/mo)*

**H2 — Why cracked heels come back after treatment** *(natural — recurrence framing, deliberately distinct from Spoke 5's one-time treatment focus)*
- H3: Treating the crack without treating the cause
- H3: Why the same pressure points keep failing the same way
- H3: What "permanently" actually requires — consistency, not a stronger product

**H2 — Severe cracked heels** *(exact match, 390/mo — the recurring/chronic end of the spectrum)*
- H3: When cracks have become a repeating cycle, not a one-off
- H3: Why severity increases if the same pattern isn't broken
- H3: What changes once the routine actually holds

**H2 — What makes a fix stick, not just work once** *(natural bridge — where the brand thesis lands most directly)*
- H3: Why one good week doesn't mean it's fixed
- H3: Locking in moisture nightly instead of only when it's bad
- H3: Turning it into a five-minute habit, not a project you restart

**Deep-links to:** Product page, "Real results, no filters" H2 (Persona 2)
**Links back to:** Pillar 1

**KW-fetch flags:** cracked heels diabetes (270), cracked heels pregnancy (260), cracked heels medicine (260) — discarded, medical framing. "Cracked heels treatment" (14,800, Spoke 5) and "cracked heels cream" (27,100, Spoke 4) deliberately kept off this spoke to avoid overlap.

---

## 9. Project status

**Core structure: complete.** Homepage, Category page, Product page, all 5 TOFU pillars, and 6 spoke articles (§8) are fully planned, keyword-verified, and ready to build: Ingrown Toenails Treatment, Callus Remover, How to Prevent Ingrown Toenails, Cracked Heels Cream, Cracked Heels Treatment, and How to Fix Cracked Heels Permanently.

**Nothing is outstanding right now.** There is no pending decision or unfinished task in this plan.

**If more spoke articles are wanted later** (optional, not required), two honest paths exist:
- Run `kw-fetch` on Pillar 4 (Dry Skin on Feet) or Pillar 5 (Cream That Works) at the spoke level specifically — their pillar-level data is verified, but no spoke-specific screenshot has been pulled for either yet, the way it was for Pillars 1–3.
- Once pages are live, use Search Console performance data (pages ranking or getting impressions on adjacent long-tail terms) as a signal for which spoke to build next.

Either path follows the same process as §8: `kw-fetch` first, apply the 5,000/mo threshold honestly (folding overlapping low-volume terms into an existing page rather than forcing a thin new one), exact-match headings where a query exists, link back to the parent pillar, and deep-link to whichever Product page persona fits the spoke's specific angle.
