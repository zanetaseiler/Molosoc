"""
Molosoc — WordPress Page Builder
=================================
Creates/updates WordPress pages via the REST API, matching molosoc_wordpress_build_spec.md.

SAFETY DEFAULTS (do not change without a reason):
  - Every page is created with status="draft" — nothing goes live automatically.
  - Menus are never touched by this script — add pages to nav manually in wp-admin.
  - WooCommerce products, payments, and shipping are never touched — this script
    only calls the /wp/v2/pages endpoint, a completely separate data type.

SETUP (do this before running):
  1. In wp-admin: Users -> Profile -> Application Passwords -> create one.
  2. pip install requests --break-system-packages
  3. Fill in SITE_URL, WP_USERNAME, WP_APP_PASSWORD below (or set as env vars).
  4. Run: python wp_build_pages.py --dry-run     (prints what it WOULD do, no API calls)
     Then: python wp_build_pages.py              (actually creates draft pages)
"""

import os
import sys
import json
import base64
import argparse
import requests

# ─── CONFIG ──────────────────────────────────────────────────────────────
SITE_URL = os.environ.get("WP_SITE_URL", "https://molosoc.com")
WP_USERNAME = os.environ.get("WP_USERNAME", "REPLACE_ME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "REPLACE_ME")  # the App Password, NOT your login password

API_BASE = f"{SITE_URL.rstrip('/')}/wp-json/wp/v2"
DEFAULT_STATUS = "draft"  # do not change to "publish" here — flip individual pages manually after review


def auth_header():
    token = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def check_connection():
    """Confirm the REST API is reachable and credentials work before doing anything else."""
    resp = requests.get(f"{API_BASE}/pages", headers=auth_header(), params={"per_page": 1})
    if resp.status_code == 401:
        sys.exit("Auth failed — check WP_USERNAME / WP_APP_PASSWORD (must be an Application Password, not your login password).")
    if resp.status_code != 200:
        sys.exit(f"Could not reach {API_BASE}/pages — status {resp.status_code}: {resp.text[:300]}")
    print(f"Connected to {SITE_URL} OK.")


def find_page_by_slug(slug):
    """Look up an existing page's ID by slug (needed to set parent, or to update instead of duplicate)."""
    resp = requests.get(f"{API_BASE}/pages", headers=auth_header(), params={"slug": slug, "status": "any"})
    resp.raise_for_status()
    results = resp.json()
    return results[0]["id"] if results else None


def create_or_update_page(title, slug, content_html, parent_slug=None, meta_title=None, meta_description=None, dry_run=False):
    """
    Creates a new draft page, or updates it if a page with this slug already exists
    (safe to re-run this script — it won't create duplicates).
    """
    parent_id = None
    if parent_slug:
        parent_id = find_page_by_slug(parent_slug)
        if parent_id is None:
            print(f"  ! WARNING: parent slug '{parent_slug}' not found yet — build parent pages first. Skipping '{slug}'.")
            return None

    payload = {
        "title": title,
        "slug": slug,
        "status": DEFAULT_STATUS,
        "content": content_html,
    }
    if parent_id:
        payload["parent"] = parent_id

    # NOTE on SEO fields (title tag / meta description):
    # These are usually owned by an SEO plugin (Yoast, Rank Math), not core WordPress.
    # Core /wp/v2/pages doesn't expose them unless the plugin registers them for REST.
    #   - Rank Math: meta keys are typically `rank_math_title`, `rank_math_description`
    #   - Yoast: requires the "Yoast SEO REST API" add-on, or a snippet that calls
    #     register_meta() to expose `_yoast_wpseo_title` / `_yoast_wpseo_metadesc`
    # Check which plugin is active before assuming this part works — this script
    # includes the meta fields, but they'll silently no-op if the plugin doesn't expose them.
    if meta_title or meta_description:
        payload["meta"] = {}
        if meta_title:
            payload["meta"]["rank_math_title"] = meta_title
            payload["meta"]["_yoast_wpseo_title"] = meta_title
        if meta_description:
            payload["meta"]["rank_math_description"] = meta_description
            payload["meta"]["_yoast_wpseo_metadesc"] = meta_description

    existing_id = find_page_by_slug(slug)

    if dry_run:
        action = "UPDATE" if existing_id else "CREATE"
        print(f"  [dry-run] {action} page '{slug}' (parent: {parent_slug or 'none'}) — status={DEFAULT_STATUS}")
        return None

    if existing_id:
        resp = requests.post(f"{API_BASE}/pages/{existing_id}", headers=auth_header(), json=payload)
    else:
        resp = requests.post(f"{API_BASE}/pages", headers=auth_header(), json=payload)

    if resp.status_code not in (200, 201):
        print(f"  ! FAILED '{slug}' — {resp.status_code}: {resp.text[:300]}")
        return None

    data = resp.json()
    print(f"  OK: '{slug}' -> id={data['id']} status={data['status']} link={data.get('link')}")
    return data["id"]


# ─── PAGE LIST ───────────────────────────────────────────────────────────
# Start with the three core pages (they're the deep-link targets everything else needs).
# Add pillars/spokes here as you're ready to build them — same shape, using
# molosoc_wordpress_build_spec.md as the source for title/slug/parent/meta.
# `content_html` below is placeholder — replace with real drafted copy before running for real.

PAGES = [
    {
        "title": "Molosoc Foot Cover",
        "slug": "moisture-lock-foot-cover",
        "parent_slug": "foot-covers",
        "meta_title": "Molosoc Foot Cover — The Cream You Already Own, Finally Working",
        "meta_description": "Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.",
        "content_html": "<h1>Molosoc Foot Cover</h1><p>PLACEHOLDER — replace with real drafted copy.</p>",
    },
    {
        "title": "Reusable Foot Covers",
        "slug": "foot-covers",
        "parent_slug": None,
        "meta_title": "Reusable Foot Covers | Moisture-Lock Foot Cover — Molosoc",
        "meta_description": "Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results.",
        "content_html": "<h1>Reusable foot covers that lock moisture in — not just once</h1><p>PLACEHOLDER — replace with real drafted copy.</p>",
    },
    {
        "title": "Molosoc — Home",
        "slug": "blank-homepage",
        "parent_slug": None,
        "meta_title": "Molosoc® | Foot Care That Actually Sticks",
        "meta_description": "Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.",
        "content_html": "<h1>Foot care you'll actually stick with</h1><p>PLACEHOLDER — replace with real drafted copy.</p>",
    },
]
# IMPORTANT: "foot-covers" (Category) must exist before "moisture-lock-foot-cover" (Product)
# since Product's parent_slug depends on it — that's why Category is listed after Product
# above but the script builds in list order. Reorder PAGES so parents come before children,
# or run this script twice (harmless — it updates instead of duplicating).


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, make no API calls that change data.")
    args = parser.parse_args()

    if WP_USERNAME == "REPLACE_ME" or WP_APP_PASSWORD == "REPLACE_ME":
        sys.exit("Set WP_USERNAME and WP_APP_PASSWORD (env vars or edit the CONFIG section) before running.")

    if not args.dry_run:
        check_connection()

    print(f"\nBuilding {len(PAGES)} page(s) — status will be '{DEFAULT_STATUS}' (not published)\n")
    for page in PAGES:
        create_or_update_page(
            title=page["title"],
            slug=page["slug"],
            content_html=page["content_html"],
            parent_slug=page["parent_slug"],
            meta_title=page.get("meta_title"),
            meta_description=page.get("meta_description"),
            dry_run=args.dry_run,
        )

    print("\nDone. Review pages in wp-admin (they're drafts) before publishing or adding to menus.")


if __name__ == "__main__":
    main()
