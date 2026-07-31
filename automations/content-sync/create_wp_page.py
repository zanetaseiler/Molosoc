#!/usr/bin/env python3
"""
Molosoc content-sync: generic version of create_category_page.py /
create_cracked_heels_page.py — ensure a WordPress Page exists for a given
slug, as a draft.

WordPress applies site/theme/page-{slug}.php automatically to any Page
with that slug (the "page-{slug}.php" template convention), but the Page
itself has to exist first — deploying the theme template alone doesn't
create it. This creates it once, as a draft, so a human still has to hit
Publish in wp-admin (same safety gate as push_to_wp.py). Safe to re-run:
if a Page with this slug already exists (draft or published), it does
nothing.

Post content is intentionally empty — page-{slug}.php templates render
their own hardcoded markup and never call the_content().

Usage:
    python3 create_wp_page.py --slug cracked-heels --title "Cracked Heels: Why They Happen..."

Pass --parent-slug for a spoke article nested under a pillar (e.g.
--parent-slug ingrown-toenails for the "treatment" spoke), so the created
Page's post_parent is set and the permalink nests correctly
(/ingrown-toenails/treatment/ instead of /treatment/). Looks the parent
page up by slug via the REST API; if it isn't found, the Page is still
created flat and a warning is printed — re-run once the parent exists, or
set it manually in wp-admin.
"""

import argparse
import os
import sys

import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")


def wp_auth():
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        sys.exit(
            "Missing WP_URL / WP_USER / WP_APP_PASSWORD environment variables. "
            "Set these as GitHub secrets or export them locally before running."
        )
    return (WP_USER, WP_APP_PASSWORD)


def main():
    parser = argparse.ArgumentParser(
        description="Ensure a WordPress Page exists for a given slug, as a draft."
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="Page slug — must match the page-{slug}.php template filename",
    )
    parser.add_argument("--title", required=True, help="Page title shown in wp-admin")
    parser.add_argument(
        "--parent-slug",
        required=False,
        default=None,
        help="Parent page slug, for a spoke article nested under a pillar (sets post_parent so the permalink nests correctly)",
    )
    args = parser.parse_args()

    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/pages",
        params={"slug": args.slug, "status": "draft,publish,future"},
        auth=wp_auth(),
        timeout=30,
    )
    resp.raise_for_status()
    existing = resp.json()

    if existing:
        page = existing[0]
        print(
            f"Page already exists — id={page['id']}, status={page['status']}, "
            f"link={page.get('link', '(none)')}. Nothing to do."
        )
        return

    payload = {
        "title": args.title,
        "slug": args.slug,
        "status": "draft",
        "content": "",
    }

    if args.parent_slug:
        parent_resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/pages",
            params={"slug": args.parent_slug, "status": "draft,publish,future"},
            auth=wp_auth(),
            timeout=30,
        )
        parent_resp.raise_for_status()
        parent_results = parent_resp.json()
        if parent_results:
            payload["parent"] = parent_results[0]["id"]
        else:
            print(
                f"  WARNING: parent slug {args.parent_slug!r} not found — creating "
                f"{args.slug!r} without a parent. Permalink won't nest until this is "
                f"re-run (safe/idempotent) or the parent is set manually in wp-admin."
            )

    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/pages", json=payload, auth=wp_auth(), timeout=30
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"CREATED draft page — id={data['id']}, title={args.title!r}")
        print(f"Review at: {WP_URL}/wp-admin/post.php?post={data['id']}&action=edit")
    else:
        sys.exit(f"ERROR {resp.status_code}: {resp.text[:300]}")


if __name__ == "__main__":
    main()
