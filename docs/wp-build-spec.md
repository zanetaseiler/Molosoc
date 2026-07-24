# Molosoc — WordPress Build Spec
**Purpose:** hand-off file for Claude Code. Each page below has the exact WordPress fields needed to create/update it via the REST API (`/wp-json/wp/v2/pages` or `/posts`), plus the content outline and internal linking. Source: `molosoc_site_structure_summary.md`.

**Auth reminder:** use a WordPress Application Password (Users → Profile → Application Passwords in wp-admin). Auth header pattern: `Authorization: Basic base64(username:app_password)`.

**Status legend:** ⬜ not built · 🟨 in progress · ✅ live

---

## 0. Site map (build order, top to bottom)

```
molosoc.com/                                          [Homepage]        ⬜
molosoc.com/foot-covers/                              [Category]        ⬜
molosoc.com/foot-covers/moisture-lock-foot-cover/     [Product]         ⬜  ← needs 301 from old slug
molosoc.com/cracked-heels/                            [Pillar 1]        ⬜
molosoc.com/cracked-heels/cracked-heels-cream/        [Spoke 4]         ⬜
molosoc.com/cracked-heels/cracked-heels-treatment/    [Spoke 5]         ⬜
molosoc.com/cracked-heels/fix-permanently/            [Spoke 6]         ⬜
molosoc.com/ingrown-toenails/                         [Pillar 2]        ⬜
molosoc.com/ingrown-toenails/treatment/               [Spoke 1]         ⬜
molosoc.com/ingrown-toenails/prevent/                 [Spoke 3]         ⬜
molosoc.com/hardened-skin-calluses/                   [Pillar 3]        ⬜
molosoc.com/hardened-skin-calluses/callus-remover/    [Spoke 2]         ⬜
molosoc.com/dry-skin-feet/                             [Pillar 4]       ⬜
molosoc.com/foot-cream-that-works/                     [Pillar 5]       ⬜
```

**Recommended build order:** Product page → Category page → Homepage → Pillar 1 + its 3 spokes → Pillar 2 + its 2 spokes → Pillar 3 + its 1 spoke → Pillar 4 → Pillar 5.
Reasoning: build the deep-link *targets* before the pages that link to them, so nothing launches with a dead/placeholder link.

---

## 1. Redirect required

| Old URL | New URL | Type |
|---|---|---|
| `molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/` | `molosoc.com/foot-covers/moisture-lock-foot-cover/` | 301 |

Implement via `Redirection` plugin, `.htaccess`, or host-level rule — Claude Code should check which is available before choosing a method.

---

## 2. HOMEPAGE

| Field | Value |
|---|---|
| WP type | `page` |
| Slug | `/` (front page — set under Settings → Reading, or via `page_on_front`) |
| Title tag | Molosoc® \| Foot Care That Actually Sticks |
| Meta description | Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones. |
| H1 | Foot care you'll actually stick with |

**Body outline:**
- H2: Why foot care never sticks
  - H3: Feet deserve real care, not just intent
  - H3: Care should be simple enough to actually stick
  - H3: You don't need new products — you need the right ritual
  - H3: Foot care is self-care, not vanity
- H2: Foot care, topic by topic *(TOFU hub)*
  - H3: Cracked heels & dry skin → link `/cracked-heels/`
  - H3: Ingrown toenails → link `/ingrown-toenails/`
  - H3: Hardened skin & calluses → link `/hardened-skin-calluses/`
  - H3: Dry skin on feet → link `/dry-skin-feet/`
  - H3: Making the cream you already own actually work → link `/foot-cream-that-works/`
- H2: How Molosoc helps right now
  - H3: Meet the Foot Cover → link `/foot-covers/moisture-lock-foot-cover/`
- H2: The reusable alternative
  - H3: What is a moisture-lock foot cover? → link `/foot-covers/`

**Status:** ⬜

---

## 3. CATEGORY PAGE

| Field | Value |
|---|---|
| WP type | `page` |
| Slug | `foot-covers` |
| Parent | none (top-level) |
| Title tag | Reusable Foot Covers \| Moisture-Lock Foot Cover — Molosoc |
| Meta description | Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results. |
| H1 | Reusable foot covers that lock moisture in — not just once |

**Body outline:**
- H2: Disposable sock masks vs. reusable foot covers
  - H3: What's actually inside a single-use sock mask
  - H3: Why reusable changes the math
  - H3: One cover, any cream — not locked to a pre-filled formula
- H2: What "moisture-lock" actually means
  - H3: How the seal traps moisture against skin
  - H3: Why mess and slipping usually kill the routine
  - H3: Cream-agnostic, by design
- H2: Reusable vs. disposable: the real cost
  - H3: Cost per use over a month
  - H3: Cost per use over a year
  - H3: What you're not paying for anymore (salon touch-ups)
- H2: Who this is for
  - H3: Already have a cream you love → link Product page
  - H3: Just had a pedicure and want it to last → link Product page
  - H3: Buying this for someone else → link Product page

**Status:** ⬜

---

## 4. PRODUCT PAGE

| Field | Value |
|---|---|
| WP type | `page` |
| Slug | `moisture-lock-foot-cover` |
| Parent | `foot-covers` |
| Title tag | Molosoc Foot Cover — The Cream You Already Own, Finally Working |
| Meta description | Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick. |
| H1 | Molosoc Foot Cover |

**Body outline:**
- H2: The cream you already own, finally working *(Persona 1 — deep-link target for Pillar 5)*
  - H3: Why creams get abandoned halfway through
  - H3: What changes when the mess disappears
  - H3: Works with the cream in your drawer right now
- H2: Real results, no filters *(Persona 2 — deep-link target for Pillar 1/2/3/4, most spokes)*
  - H3: 3-month before/after, time-stamped
  - H3: What actually happens to cracked heels over time
  - H3: Unfiltered reactions (mom-reaction style content)
- H2: Make the pedicure last *(Persona 3)*
  - H3: Why salon results fade in ~10 days
  - H3: Cost per use vs. another salon visit
  - H3: Home spa, without the salon price
- H2: Give it as a gift *(Persona 4)*
  - H3: For someone always on her feet
  - H3: One before/after photo says it all
  - H3: How to gift it (simple, low-effort framing)
- H2: How it works
  - H3: What's in the box
  - H3: How to use it with any cream
  - H3: Reusable — how many uses to expect

**Status:** ⬜ · **Redirect needed:** yes (see §1)

---

## 5. PILLAR 1 — Cracked Heels

| Field | Value |
|---|---|
| WP type | `page` (or `post` if pillars should live in a blog structure — confirm with user before building) |
| Slug | `cracked-heels` |
| Parent | none (top-level) |
| Title tag | Cracked Heels: Why They Happen and How to Actually Fix Them |
| Meta description | Cracked heels aren't just dry skin — here's what's really causing them, what makes them worse, and what actually helps (without the gimmicks). |
| H1 | Cracked heels: what's really going on, and what helps |

**Body outline:**
- H2: What causes cracked heels
  - H3: Dry skin losing its ability to stretch
  - H3: Pressure and weight-bearing on the heel edge
  - H3: Standing all day, especially in open-back shoes
- H2: When cracked heels go from dry to painful
  - H3: Painful deep cracked heels
  - H3: Severe cracked heels
  - H3: Why "just moisturizing more" stops working at this stage
- H2: Why moisturizer alone doesn't fix it
  - H3: The routine most people already try
  - H3: Where that routine breaks down
  - H3: What actually needs to happen for cream to work
- H2: Go deeper
  - H3: Cracked heels cream → link `/cracked-heels/cracked-heels-cream/`
  - H3: How to fix cracked heels permanently → link `/cracked-heels/fix-permanently/`
  - H3: Cracked heels treatment → link `/cracked-heels/cracked-heels-treatment/`

**Deep-links to:** Product page, "Real results, no filters" H2
**Status:** ⬜

### 5a. Spoke — Cracked Heels Cream
| Field | Value |
|---|---|
| Slug | `cracked-heels/cracked-heels-cream` (parent: `cracked-heels`) |
| Title tag | Cracked Heels Cream: What Actually Makes One Work |
| Meta description | Not all cracked-heel creams work the same way. Here's what actually matters — the ingredients, the timing, and why even a good cream can fail without the right routine. |
| H1 | Cracked heels cream: what actually makes one work |
- H2: What to actually look for in a cracked heels cream (Urea/humectants; balms vs. lotions; consistency > ingredients)
- H2: Best cream for cracked heels (severity not brand; cost ≠ effectiveness; the cream you already own is probably fine)
- H2: Why a good cream still doesn't fix cracked heels (routine breakdown, mirrors site-wide hierarchy)
- **Deep-links to:** Product page, "The cream you already own, finally working" H2 (Persona 1 — *exception to pillar default*)
- **Links back to:** Pillar 1
- **Status:** ⬜

### 5b. Spoke — Cracked Heels Treatment
| Field | Value |
|---|---|
| Slug | `cracked-heels/cracked-heels-treatment` (parent: `cracked-heels`) |
| Title tag | Cracked Heels Treatment: What Actually Works, Step by Step |
| Meta description | Cream alone rarely fixes cracked heels. Here's the full picture — exfoliation, moisture, and the one step most routines skip. |
| H1 | Cracked heels treatment: what actually works |
- H2: The three things actual treatment requires (remove dead skin; moisture in, not just on; sealing it in)
- H2: When to see a podiatrist instead of treating it yourself (signs it's past surface-level; painful deep cracked heels; bleeding/infection)
- H2: Building a treatment routine that actually finishes (why people stop early; locking moisture in overnight; five-minute nightly step)
- **Deep-links to:** Product page, "Real results, no filters" H2
- **Links back to:** Pillar 1
- **Status:** ⬜

### 5c. Spoke — How to Fix Cracked Heels Permanently
| Field | Value |
|---|---|
| Slug | `cracked-heels/fix-permanently` (parent: `cracked-heels`) |
| Title tag | How to Fix Cracked Heels Permanently (Not Just Temporarily) |
| Meta description | Cracked heels keep coming back for a reason — treatment fixes them once, but doesn't stop them from returning. Here's what actually makes it stick. |
| H1 | How to fix cracked heels permanently |
- H2: Why cracked heels come back after treatment (cause vs. crack; same pressure points; consistency not stronger product)
- H2: Severe cracked heels (repeating cycle; severity escalation; what changes once routine holds)
- H2: What makes a fix stick, not just work once (one good week ≠ fixed; nightly moisture lock; five-minute habit)
- **Deep-links to:** Product page, "Real results, no filters" H2
- **Links back to:** Pillar 1
- **Status:** ⬜

---

## 6. PILLAR 2 — Ingrown Toenails

| Field | Value |
|---|---|
| Slug | `ingrown-toenails` (top-level) |
| Title tag | Ingrown Toenails: Why They Happen and What Actually Helps |
| Meta description | An ingrown toenail can go from mildly annoying to genuinely painful fast. Here's what causes it, what actually helps at home, and when it's more than a nail problem. |
| H1 | Ingrown toenails: what's happening, and what actually helps |

**Body outline:**
- H2: What causes ingrown toenails (nail edge growing into skin; tight shoes/cutting too short; recurrence)
- H2: Do ingrown toenails go away (resolves without intervention; worsening signs; risk of waiting)
- H2: Why cutting it yourself often backfires (big toenail hurts; ingrown big toe; softening skin)
- H2: Go deeper
  - H3: How to treat ingrown toenails → link `/ingrown-toenails/treatment/`
  - H3: How to prevent ingrown toenails → link `/ingrown-toenails/prevent/`
  - H3: Ingrown toenails treatment → *(folded into Spoke 1, see below — not a separate page)*

**Deep-links to:** Product page, "Real results, no filters" H2
**Status:** ⬜

### 6a. Spoke — Ingrown Toenails Treatment
| Field | Value |
|---|---|
| Slug | `ingrown-toenails/treatment` (parent: `ingrown-toenails`) |
| Title tag | Ingrown Toenails Treatment: What Actually Works |
| Meta description | From home softening to when a doctor needs to get involved — here's what actually treats an ingrown toenail, and what makes it worse. |
| H1 | Ingrown toenails treatment: what actually works |
- H2: How to treat ingrown toenails (softening first; warm soaks; pressure relief)
- H2: How to get rid of ingrown toenails (at-home approach; recurrence vs. one-time fix; trimming technique)
- H2: When home treatment isn't enough (infection signs; when to see a podiatrist; risk of waiting)
- **Deep-links to:** Product page, "Real results, no filters" H2
- **Links back to:** Pillar 2
- **Status:** ⬜

### 6b. Spoke — How to Prevent Ingrown Toenails
| Field | Value |
|---|---|
| Slug | `ingrown-toenails/prevent` (parent: `ingrown-toenails`) |
| Title tag | How to Prevent Ingrown Toenails (For Good) |
| Meta description | If this isn't your first ingrown toenail, the fix isn't just treating this one — it's changing what keeps causing them. Here's what actually prevents it. |
| H1 | How to prevent ingrown toenails |
- H2: Why do I keep getting ingrown toenails? (cutting habit; footwear pressure; recurrence after treatment)
- H2: How to stop ingrown toenails (trim shape; shoe-fit changes; ongoing softening)
- H2: Building a prevention routine that actually sticks (prevention fails same as treatment — no structure; five-minute weekly check; folding into existing routine)
- **Deep-links to:** Product page, "Real results, no filters" H2
- **Links back to:** Pillar 2
- **Status:** ⬜

---

## 7. PILLAR 3 — Hardened Skin & Calluses

| Field | Value |
|---|---|
| Slug | `hardened-skin-calluses` (top-level) |
| Title tag | Hardened Skin & Calluses on Feet: Why They Form and What Softens Them |
| Meta description | Thick, hardened skin on your feet doesn't happen overnight — and it doesn't have to stay that way. Here's why calluses form and what actually softens them. |
| H1 | Hardened skin and calluses: why they form, and what softens them |

**Body outline:**
- H2: Calluses on feet (foot callus; corns and calluses; gradual buildup)
- H2: Foot corn cure (callus treatment; effect on walking; risk of self-removal)
- H2: Why soaking and filing alone don't keep it away (routine most people try; why it returns; what actually needs to change)
- H2: Go deeper
  - H3: Callus remover → link `/hardened-skin-calluses/callus-remover/`
  - H3: How to remove thick dead skin from feet home remedy → *(folded into Spoke 2)*
  - H3: How to get rid of hard skin on feet permanently → *(folded into Spoke 2)*

**Deep-links to:** Product page, "Real results, no filters" H2
**Status:** ⬜

### 7a. Spoke — Callus Remover
| Field | Value |
|---|---|
| Slug | `hardened-skin-calluses/callus-remover` (parent: `hardened-skin-calluses`) |
| Title tag | Callus Remover: What Actually Works (And Why It Doesn't Last) |
| Meta description | Files, creams, pumice stones — here's an honest look at what actually removes hard skin, and why it keeps coming back no matter which one you use. |
| H1 | Callus remover: what actually works |
- H2: What actually removes hard skin (filing/pumice; chemical/acid removers + overdo risk; removal alone doesn't prevent return) — **brand-safety note: frame honestly, don't imply Molosoc is a removal tool**
- H2: How to remove thick dead skin from feet home remedy (soak first; safe filing; what happens after removal)
- H2: How to get rid of hard skin on feet permanently (pressure point still there; one-time ≠ prevention; what slows regrowth)
- **Deep-links to:** Product page, "Real results, no filters" H2
- **Links back to:** Pillar 3
- **Status:** ⬜

---

## 8. PILLAR 4 — Dry Skin on Feet

| Field | Value |
|---|---|
| Slug | `dry-skin-feet` (top-level) |
| Title tag | Dry Skin on Feet: Why It Happens and What Actually Helps |
| Meta description | Still dry after moisturizing? Here's what actually causes dry skin on feet, why cream alone doesn't fix it, and what actually helps it stop. |
| H1 | Dry skin on feet: why it keeps coming back |

**Body outline:**
- H2: What causes dry skin on feet (soles dry differently; socks/shoes trap moisture loss; seasonal triggers)
- H2: Why are my feet so dry even when I moisturize? (routine most people try; cream not absorbing; what needs to change)
- H2: Socks, tights, and the dryness nobody talks about (enclosed feet dry differently; winter habit-building vs. summer exposure; private low-effort ritual)
- H2: Go deeper
  - H3: Dry foot skin treatment → future spoke (not yet kw-fetched at spoke level)
  - H3: Dry skin feet home remedies → future spoke (not yet kw-fetched at spoke level)
  - H3: Dry feet vs. cracked heels: what's the difference → future spoke (cross-links to Pillar 1)

**Deep-links to:** Product page, "Real results, no filters" H2 (primary), secondary tie to Persona 1
**Status:** ⬜ · **No spokes built yet** — run `kw-fetch` at spoke level before building these three

---

## 9. PILLAR 5 — Making the Cream You Already Own Actually Work

| Field | Value |
|---|---|
| Slug | `foot-cream-that-works` (top-level) |
| Title tag | Does Foot Cream Actually Work? Why It Fails, and What Fixes It |
| Meta description | Tried every foot cream with no results? The cream probably isn't the problem — here's why it fails and what actually makes it work. |
| H1 | Does foot cream actually work? |

**Body outline:**
- H2: Why creams get abandoned halfway through (real intent, no structure; the mess; it's not that the cream failed)
- H2: How long does foot cream take to absorb? (timing matters; socks after cream; soft feet overnight)
- H2: The cream graveyard problem (2-3 half-used bottles; pattern says routine not product; breaking the cycle without a new cream)
- H2: Go deeper
  - H3: Softening foot cream → future spoke (not yet kw-fetched at spoke level)
  - H3: How to moisturize feet overnight → future spoke (not yet kw-fetched at spoke level)
  - H3: Overnight foot cream → future spoke (not yet kw-fetched at spoke level)

**Deep-links to:** Product page, "The cream you already own, finally working" H2 (Persona 1)
**Status:** ⬜ · **No spokes built yet** — run `kw-fetch` at spoke level before building these three

---

## 10. Site-wide rules for whoever writes body copy (Claude Code or human)

- **Message hierarchy, always in this order:** locks in moisture → reduces mess/slipping → works with your favorite cream → easy ritual for soft feet.
- **Never** use medical/clinical framing anywhere: no "diabetic foot," no diagnosis language, no ICD terms, no implying Molosoc is a medical device.
- **Exact-match heading rule:** where an H2/H3 above is marked as answering a specific searched query, use that exact phrasing verbatim as the heading — don't paraphrase it into "cleaner" prose. Bridge/connective headings (no query behind them) can stay natural.
- **Seasonal content** (only relevant on Product-page/persona content, not pillars/category): pre-summer (Apr–Jun) = urgency; deep summer (Jul–Aug) = skip "start now" framing; late summer/fall (Aug–Sept) = "summer wrecked my feet" repair angle; winter (Oct–Mar) = private habit-building, best for Persona 1.
- **Internal links must resolve** — build deep-link targets (Product page persona H2 anchors) before the pillars/spokes that link to them.

---

## 11. What's NOT done yet (be explicit with the user before assuming otherwise)

- Spoke articles for Pillar 4 (Dry Skin on Feet) and Pillar 5 (Cream That Works) — pillar-level keyword data is verified, but no spoke-specific `kw-fetch` pull has happened yet.
- Actual body copy for every page above — this file is skeleton/spec only (title, meta, headings, links), matching how the `seo-site-architect` skill defines its own deliverable. Copy still needs to be drafted per page before it can be pushed live.
- WordPress-side decisions not yet confirmed: whether pillars/spokes should be WP `pages` (nested URL, matches the plan exactly) or `posts` with a custom permalink structure — confirm before Claude Code starts creating content, since it affects the API calls.
