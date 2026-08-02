#!/usr/bin/env python3
"""
Molosoc content-sync: push markdown drafts to WordPress as drafts via the REST API.

Reads every .md file passed on the command line (or via --all on a folder),
expects YAML frontmatter at the top, converts the body to WP block-editor
HTML, and creates or updates the matching page/post as status=draft.

Never publishes directly — always lands as "draft" so a human hits Publish
in wp-admin. That's the safety gate.

Frontmatter format expected in each .md file:
---
title: "Cracked Heels: Why They Happen and How to Actually Fix Them"
slug: cracked-heels
type: page          # "page" or "post" — defaults to "page"
meta_description: "Cracked heels aren't just dry skin — here's what's really causing them..."
---
# H1 ...
## H2 ...
content...
"""

import os
import sys
import time
import argparse
import requests
import frontmatter
import markdown as md
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

# The host has been observed rate-limiting/blocking bursts of rapid REST calls
# (each page push makes several lookups in quick succession). Retry with
# backoff on connection failures and 429/5xx before giving up.
_session = requests.Session()
_retry = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)
_session.mount("https://", HTTPAdapter(max_retries=_retry))
_session.mount("http://", HTTPAdapter(max_retries=_retry))


def wp_auth():
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        sys.exit(
            "Missing WP_URL / WP_USER / WP_APP_PASSWORD environment variables. "
            "Set these as GitHub secrets or export them locally before running."
        )
    return (WP_USER, WP_APP_PASSWORD)


def find_existing(post_type: str, slug: str, lang: str = None):
    """Look up an existing page/post by slug, optionally filtered to a Polylang lang. Returns its ID or None."""
    endpoint = f"{WP_URL}/wp-json/wp/v2/{post_type}s"
    params = {"slug": slug, "status": "draft,publish,future"}
    if lang:
        params["lang"] = lang
    resp = _session.get(
        endpoint,
        params=params,
        auth=wp_auth(),
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json()
    return results[0]["id"] if results else None


def push_file(path: str, force_status: str = "draft"):
    post = frontmatter.load(path)
    meta = post.metadata

    title = meta.get("title")
    slug = meta.get("slug")
    post_type = meta.get("type", "page")
    meta_description = meta.get("meta_description", "")
    lang = meta.get("lang")
    parent_slug = meta.get("parent_slug")
    translation_of_en_slug = meta.get("translation_of_en_slug")

    if not title or not slug:
        print(f"  SKIP {path}: frontmatter must include 'title' and 'slug'")
        return

    html_body = md.markdown(post.content, extensions=["extra"])

    payload = {
        "title": title,
        "content": html_body,
        "slug": slug,
        "status": force_status,
    }

    # Yoast SEO exposes meta description via REST if the Yoast REST fields
    # are enabled; harmless to include even if the plugin isn't active —
    # WordPress just ignores unknown meta keys silently.
    if meta_description:
        payload["meta"] = {"_yoast_wpseo_metadesc": meta_description}

    if parent_slug:
        parent_id = find_existing(post_type, parent_slug, lang=lang)
        if parent_id:
            payload["parent"] = parent_id
        else:
            print(f"  WARN {path}: parent_slug '{parent_slug}' (lang={lang}) not found yet — push it first")

    if translation_of_en_slug:
        en_id = find_existing(post_type, translation_of_en_slug)
        if en_id:
            payload["translations"] = {"en": en_id}
        else:
            print(f"  WARN {path}: translation_of_en_slug '{translation_of_en_slug}' not found — translation link skipped")

    existing_id = find_existing(post_type, slug, lang=lang)
    endpoint = f"{WP_URL}/wp-json/wp/v2/{post_type}s"
    lang_params = {"lang": lang} if lang else {}

    if existing_id:
        resp = _session.post(f"{endpoint}/{existing_id}", json=payload, params=lang_params, auth=wp_auth(), timeout=30)
        action = "UPDATED"
    else:
        resp = _session.post(endpoint, json=payload, params=lang_params, auth=wp_auth(), timeout=30)
        action = "CREATED"

    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"  {action} draft: {title}  →  {data.get('link', '(no link — check wp-admin)')}")
    else:
        print(f"  ERROR {path}: {resp.status_code} {resp.text[:300]}")


def main():
    parser = argparse.ArgumentParser(description="Push markdown drafts to WordPress as drafts.")
    parser.add_argument("files", nargs="*", help="Markdown files to push")
    parser.add_argument("--folder", help="Push every .md file in this folder", default=None)
    parser.add_argument(
        "--status",
        default="draft",
        choices=["draft", "publish"],
        help="Status to set (default: draft — use 'publish' deliberately, never as a default)",
    )
    args = parser.parse_args()

    targets = list(args.files)
    if args.folder:
        for root, _, filenames in os.walk(args.folder):
            for fn in filenames:
                if fn.endswith(".md"):
                    targets.append(os.path.join(root, fn))

    if not targets:
        print("No files given. Pass file paths or --folder <dir>.")
        sys.exit(1)

    print(f"Pushing {len(targets)} file(s) to {WP_URL} as status={args.status} ...")
    for path in targets:
        push_file(path, force_status=args.status)


if __name__ == "__main__":
    main()
