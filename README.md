# Molosoc

Foot care brand — reusable moisture-lock foot cover. This repo is the single source of truth: planning docs, site content drafts, and the automation that pushes content into WordPress.

## Start here
Read `docs/00-build-playbook.md` first — it's the ordered build sequence (Phase 0 → 5) with checkboxes. Everything else in this repo exists to serve one of those phases.

## First-time setup (do this once)
1. Create a new **private** repo on GitHub, e.g. `molosoc-site` — leave it empty, no README/gitignore.
2. Unzip this folder locally, `cd` into it.
3. Run:
   ```bash
   git init
   git add .
   git commit -m "Initial repo scaffold"
   git branch -M main
   git checkout -b staging
   git remote add origin https://github.com/YOUR-USERNAME/molosoc-site.git
   git push -u origin main
   git push -u origin staging
   ```
4. Set up WordPress Application Password + GitHub secrets — follow `automations/content-sync/wp-setup-instructions.md` exactly, in order.
5. For the theme deploy workflows (`site/deploy/staging.yml`, `production.yml`) you'll also need SFTP secrets: `STAGING_SFTP_HOST/USER/PASS` and `PROD_SFTP_HOST/USER/PASS`, plus a `production` GitHub Environment with required reviewers set (Settings → Environments) so live deploys need manual approval.

## Folder guide
- `docs/` — standing project knowledge: ICP, brand architecture, SEO/GEO plan, site structure, build playbook.
- `automations/content-sync/` — script + setup guide that pushes markdown drafts into WordPress as drafts via the REST API.
- `automations/analytics/` — read-only connection tests for GA4, Search Console (`GOOGLE_SERVICE_ACCOUNT_JSON`) and Microsoft Clarity (`CLARITY_API_TOKEN`). Clarity is capped at 10 API calls/project/day — read that README before touching it. Also the weekly analysis, the HTML dashboard, and the Email Marketing card that reads the email orchestrator's published evidence — see `docs/email-marketing-reporting.md`.
- `.github/workflows/content-sync.yml` — auto-runs content push on every commit to `staging` touching `seo/` or `content/`.
- `seo/pillars/`, `seo/spokes/` — TOFU content drafts. Copy `_template.md`, fill in frontmatter + body, commit.
- `content/` — homepage/category/product page drafts. Same template pattern.
- `tracking/ga4-events.md` — GA4/Pixel/Klaviyo shared event naming spec (Phase 2).
- `woocommerce/` — product/shipping/payment config notes (Phase 1c).
- `site/theme/` — WordPress child theme (only WP layer tracked in git).
- `site/deploy/` — GitHub Actions that push `site/theme/` to staging (auto) and production (manual approval).
- `i18n/` — CZ/EN content splits.

## How content actually gets published
1. Copy `seo/pillars/_template.md` (or spokes/content), fill in `title`, `slug`, `meta_description`, and the body.
2. Commit and push to the `staging` branch.
3. GitHub Action converts it and pushes it into WordPress as a **draft** automatically.
4. You review in wp-admin and click Publish yourself — nothing auto-publishes.
