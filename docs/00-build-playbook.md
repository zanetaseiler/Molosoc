# Molosoc — Master Build Playbook
**Purpose:** a single, ordered instruction set for standing up the full stack. Hand this to Antigravity or Claude Code at the start of any session so it knows exactly what phase you're in and what depends on what. Update the checkboxes as you go — this file *is* the project status tracker.

**Read alongside:** `docs/icp.md`, `docs/brand-architecture.md`, `docs/seo-geo-plan.md`, `docs/site-structure.md` — those define *what* to say; this defines *what to build, in what order*.

---

## How to use this doc with Antigravity / Claude Code

- Paste the relevant **Phase** section into the session, not the whole file — keeps context tight.
- Each phase lists: **Depends on**, **Tools involved**, **Steps**, **Who does it** (You / Agent / Both — some steps need a human clicking inside a dashboard; agents can't do those).
- Don't let an agent skip ahead to a later phase "to save time" — the order exists because later phases assume earlier ones are live (e.g., GTM must exist before GA4/Clarity/Pixel are wired in, since they're deployed *through* GTM, not installed separately).

---

## Phase 0 — Environment & Repo (foundation)

**Depends on:** nothing
**Tools:** GitHub, VS Code, Claude Code, Antigravity
**Who:** You (accounts/access) + Agent (scaffolding)

- [ ] Create the GitHub repo (private) — `molosoc/molosoc-site` or similar
- [ ] Clone locally, open in VS Code
- [ ] Scaffold the folder structure:
  ```
  molosoc/
  ├── docs/            (the 4 existing planning docs)
  ├── site/theme/       (WP child theme — only git-tracked WP layer)
  ├── site/deploy/       (GitHub Actions YAML)
  ├── woocommerce/
  ├── tracking/          (GTM export, GA4/Pixel/Clarity event specs)
  ├── seo/pillars/ + seo/spokes/
  ├── i18n/cz/ + i18n/en/
  └── automations/klaviyo/ + automations/ai-agents/
  ```
- [ ] Commit the 4 planning docs into `docs/` as the standing project-knowledge base
- [ ] Set repo secrets placeholders (empty for now, filled in Phase 1): `STAGING_SFTP_HOST`, `STAGING_SFTP_USER`, `STAGING_SFTP_PASS`, `PROD_SFTP_HOST`, `PROD_SFTP_USER`, `PROD_SFTP_PASS`
- [ ] Decide split: **Claude Code** for terminal/repo-level work (theme code, GitHub Actions, refactors); **Antigravity** for longer autonomous multi-file builds where you want to walk away and come back. Both point at the same repo — no divergence risk as long as everything routes through git.

**Exit condition:** repo exists, structure is scaffolded, docs are committed, both agents can see the same repo.

---

## Phase 1 — Infrastructure (Cloudflare → WordPress → WooCommerce)

**Depends on:** Phase 0
**Tools:** Cloudflare, cPanel/SFTP, WordPress, WooCommerce
**Who:** Mostly You (dashboard clicks), Agent drafts config/theme code

### 1a. Cloudflare (do this before touching DNS elsewhere)
- [ ] Add `molosoc.com` to Cloudflare, point nameservers there
- [ ] Set up `staging.molosoc.com` subdomain (DNS only, or proxied — proxied gets you caching/WAF on staging too)
- [ ] Enable: Auto HTTPS rewrites, Always Use HTTPS, Brotli compression
- [ ] Set caching rule: bypass cache for `/wp-admin`, `/checkout`, `/cart`, `/my-account` (critical for WooCommerce — caching checkout breaks orders)
- [ ] Turn on Bot Fight Mode / basic WAF rules

### 1b. WordPress (staging + live)
- [ ] Confirm cPanel supports SSH/SFTP (not just plain FTP) — check "SSH Access" in cPanel
- [ ] Create two folders/subdomains: staging and live, each a full WP install
- [ ] Install WP on staging first, get it fully working before touching live
- [ ] Fill in the Phase 0 SFTP secrets in GitHub now that credentials exist
- [ ] Agent drafts `site/deploy/staging.yml` and `site/deploy/production.yml` (staging auto-deploys on push; production requires manual GitHub Environment approval)
- [ ] Test: push a trivial theme change to `staging` branch → confirm it lands on staging.molosoc.com
- [ ] Old URL redirect required per site-structure.md: `molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/` → 301 → `molosoc.com/foot-covers/moisture-lock-foot-cover/` (set this in theme's mu-plugin or Cloudflare redirect rule, not just WP — belt and suspenders)

### 1c. WooCommerce
- [ ] Install WooCommerce on staging
- [ ] Set up the one live SKU: Molosoc Foot Cover (`woocommerce/products/foot-cover.json` as source of truth, imported via CSV importer or WC REST API)
- [ ] Configure shipping (CZ-first, likely EU zones)
- [ ] Configure payment gateway (confirm which — Stripe/GoPay/Comgate are common CZ choices)
- [ ] Test a full dummy order end-to-end on staging before going live

**Exit condition:** staging site is live, deployable via git push, WooCommerce checkout works on staging with test order.

---

## Phase 2 — Tracking & Analytics (GTM first, everything else through it)

**Depends on:** Phase 1 (needs a live site to install tags on)
**Tools:** Google Tag Manager, GA4, Google Search Console, Microsoft Clarity, Meta Pixel
**Who:** You (account creation, container publish), Agent (event spec, dataLayer code)

**Order matters here — GTM is the container everything else loads through:**

- [ ] Create GTM account + container, install the GTM snippet in theme header/footer (once, hardcoded — not the mu-plugin)
- [ ] Create GA4 property, add as a tag *inside* GTM (not a separate hardcoded snippet)
- [ ] Define the event spec first in `tracking/ga4-events.md` (e.g. `add_to_cart`, `begin_checkout`, `purchase`, matching WooCommerce's own dataLayer events) — agent drafts this from WooCommerce's standard events, you approve naming
- [ ] Add Meta Pixel as a GTM tag, fire on the same events (`AddToCart`, `Purchase`) — reuse the GA4 event spec, don't invent a second naming scheme
- [ ] Add Microsoft Clarity as a GTM tag (simplest — just page view, no event mapping needed)
- [ ] Add/confirm Cookie Consent tool fires *before* GTM tags load (consent-mode compliant — GA4/Pixel/Clarity should respect denied consent, especially since EU/CZ traffic applies GDPR)
- [ ] Export the finished GTM container JSON, commit to `tracking/gtm-container-export.json` — this is your version-controlled backup/rollback point
- [ ] Verify Google Search Console: add property, verify via GTM or DNS TXT record (Cloudflare DNS), submit sitemap (`molosoc.com/sitemap.xml` — WordPress SEO plugin generates this)

**Exit condition:** one GTM container drives GA4 + Pixel + Clarity, consent-gated, container JSON is committed, GSC verified and indexing.

---

## Phase 3 — SEO / GEO content build

**Depends on:** Phase 1 (site to publish to), ideally Phase 2 (so you can measure what you publish)
**Tools:** WordPress, `seo-site-architect` skill, `kw-fetch` skill
**Who:** Agent drafts content from `seo/pillars/` and `seo/spokes/`, you review before publish

- [ ] Build Category page (`molosoc.com/foot-covers/`) per site-structure.md §3
- [ ] Build Product page (`molosoc.com/foot-covers/moisture-lock-foot-cover/`) per §4
- [ ] Build the 5 TOFU pillars (§7) — already keyword-verified and locked, ready to draft
- [ ] Build the 6 spoke articles (§8) — same status
- [ ] Add schema markup (Product, Article, FAQPage where relevant) — this is the concrete GEO lever, not just good writing
- [ ] Add an `llms.txt` at site root summarizing the brand/product for AI crawlers (emerging GEO practice)
- [ ] Confirm internal linking map matches §5 exactly (pillars skip Category, link straight to Product persona sections)

**Exit condition:** homepage, category, product, 5 pillars, 6 spokes are live; internal linking matches spec; schema validates (test in Google's Rich Results Test).

---

## Phase 4 — Klaviyo (email/CRM layer)

**Depends on:** Phase 1c (WooCommerce live), Phase 2 (event spec exists — reuse it)
**Tools:** Klaviyo, WooCommerce
**Who:** You (account, list setup, legal opt-in language), Agent (flow drafts)

- [ ] Install Klaviyo's WooCommerce integration (official plugin — syncs customers/orders/events automatically)
- [ ] Reuse the exact GA4 event names from Phase 2 for Klaviyo flow triggers where possible — one source of truth for what an "event" is site-wide
- [ ] Build first flow: abandoned checkout (highest ROI, standard starting point)
- [ ] Build welcome flow for new signups
- [ ] Confirm CZ/EN language split matches `i18n/` — Klaviyo flows need both versions or a language-based split

**Exit condition:** at least abandoned-checkout + welcome flow live and tested with a dummy signup/cart.

---

## Phase 5 — Future AI agents (not started — placeholder)

**Depends on:** everything above being stable
**Status:** intentionally undefined until Phases 0–4 are solid. Don't let an agent session jump ahead to "build an AI agent" while Phase 1–2 are still shaky — a chatbot or automation built on top of an unfinished tracking/checkout layer just inherits the same bugs.

When you're ready to start this phase, first decide: what's the job (support chatbot? content generation? inventory alerts?) — that decision alone determines the next actual step, so it's not worth pre-planning further here.

---

## Quick status snapshot (update this table as phases close)

| Phase | Status |
|---|---|
| 0 — Environment & Repo | Not started |
| 1 — Infrastructure (Cloudflare/WP/Woo) | Not started |
| 2 — Tracking (GTM/GA4/GSC/Clarity/Pixel) | Not started |
| 3 — SEO/GEO content | Content planned (see seo-geo-plan.md), not built |
| 4 — Klaviyo | Not started |
| 5 — AI agents | Deferred |
