#!/usr/bin/env python3
"""
Molosoc content-sync: one-off — ensure the WordPress Page for
/cracked-heels/ exists, as a draft.

WordPress applies site/theme/page-cracked-heels.php automatically to any
Page with the slug "cracked-heels" (the "page-{slug}.php" template
convention), but the Page itself has to exist first — deploying the theme
template alone doesn't create it. This script creates it once, as a
draft, so a human still has to hit Publish in wp-admin (same safety gate
as push_to_wp.py / create_category_page.py). Safe to re-run: if a Page
with this slug already exists (draft or published), it does nothing.

Post content is intentionally empty — page-cracked-heels.php renders its
own hardcoded markup and never calls the_content().
"""

import os
import sys

import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

SLUG = "cracked-heels"
TITLE = "Cracked Heels: Why They Happen and How to Actually Fix Them — Molosoc"


def wp_auth():
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        sys.exit(
            "Missing WP_URL / WP_USER / WP_APP_PASSWORD environment variables. "
            "Set these as GitHub secrets or export them locally before running."
        )
    return (WP_USER, WP_APP_PASSWORD)


def main():
    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/pages",
        params={"slug": SLUG, "status": "draft,publish,future"},
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
        "title": TITLE,
        "slug": SLUG,
        "status": "draft",
        "content": "",
    }
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/pages", json=payload, auth=wp_auth(), timeout=30
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"CREATED draft page — id={data['id']}, title={TITLE!r}")
        print(f"Review at: {WP_URL}/wp-admin/post.php?post={data['id']}&action=edit")
    else:
        sys.exit(f"ERROR {resp.status_code}: {resp.text[:300]}")


if __name__ == "__main__":
    main()
