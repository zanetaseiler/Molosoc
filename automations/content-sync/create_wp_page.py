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

--environment production|staging is required and WP_URL must match that
environment's exact host (checked before any request).

Pass --parent-slug for a spoke article nested under a pillar (e.g.
--parent-slug ingrown-toenails for the "treatment" spoke), so the created
Page's post_parent is set and the permalink nests correctly
(/ingrown-toenails/treatment/ instead of /treatment/). Looks the parent
page up by slug via the REST API; if it isn't found, the Page is still
created flat and a warning is printed — re-run once the parent exists, or
set it manually in wp-admin.

Pass --lang cz (Polylang language slug) for a Czech page. The script sends
it as the Polylang `lang` REST parameter, then checks the returned permalink
really sits under /cz/ and prints a loud ACTION REQUIRED notice if it does
not (Polylang free's REST support for this varies by version). Do not
publish a page, or deploy a link to it, until the check passes — set the
language in wp-admin's Languages box and re-check the permalink first.
"""

import argparse
import os
import sys

import requests
from urllib.parse import urlparse

# Exact hosts each --environment may talk to. WP_URL is validated against this
# before any request, so a staging secret can never create a production page
# (or vice versa) just because the wrong secret set was wired in.
EXPECTED_HOSTS = {
    "production": "molosoc.com",
    "staging": "staging.molosoc.com",
}

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


def validate_wp_url(url, environment):
    """Exit unless `url` is exactly https://<expected host> for the environment.

    Runs before any GET/POST. Never prints credentials.
    """
    expected = EXPECTED_HOSTS.get(environment)
    if expected is None:
        sys.exit(f"Unknown --environment {environment!r}; use one of {sorted(EXPECTED_HOSTS)}.")
    parsed = urlparse(url or "")
    if (
        parsed.scheme != "https"
        or parsed.hostname != expected
        or parsed.port is not None
        or parsed.username
        or parsed.password
        or parsed.path.strip("/")
        or parsed.params
        or parsed.query
        or parsed.fragment
        or "?" in url
        or "#" in url
    ):
        sys.exit(
            f"REFUSING to run: --environment {environment} requires WP_URL to be "
            f"https://{expected}, but it resolves to host {parsed.hostname!r}. "
            f"No request was made."
        )


def permalink_in_language(link, lang):
    """True if the permalink's first path segment is the language slug."""
    path = urlparse(link or "").path.strip("/")
    return path.split("/")[0] == lang


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
    parser.add_argument(
        "--lang",
        required=False,
        default=None,
        help="Polylang language slug (e.g. cz). Sent as `lang`; the permalink is then verified to sit under /<lang>/",
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=sorted(EXPECTED_HOSTS),
        help="Target site. WP_URL must be exactly https://<that environment's host> or nothing is requested",
    )
    args = parser.parse_args()

    validate_wp_url(WP_URL, args.environment)

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
        if args.lang and not permalink_in_language(page.get("link", ""), args.lang):
            print(
                f"  ACTION REQUIRED: existing page link {page.get('link')!r} is not "
                f"under /{args.lang}/ — set its language in wp-admin before publishing."
            )
            sys.exit(2)
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

    if args.lang:
        payload["lang"] = args.lang

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
        if args.lang:
            link = data.get("link", "")
            if not permalink_in_language(link, args.lang):
                print(
                    f"  ACTION REQUIRED: permalink {link!r} is not under /{args.lang}/ — "
                    f"Polylang did not apply language {args.lang!r}. In wp-admin set "
                    f"Languages = {args.lang} on this Page and confirm the permalink "
                    f"becomes {WP_URL}/{args.lang}/{args.slug}/ BEFORE publishing or "
                    f"linking to it."
                )
                sys.exit(2)
            print(f"Language check OK — permalink {link!r} is under /{args.lang}/")
    else:
        sys.exit(f"ERROR {resp.status_code}: {resp.text[:300]}")


if __name__ == "__main__":
    main()
