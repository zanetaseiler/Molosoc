#!/usr/bin/env python3
"""
Molosoc content-sync: dump the full WordPress media library to a CSV.

Paginates the /wp-json/wp/v2/media endpoint (WP caps at 100 per page) and
writes one row per attachment: id, filename, source_url, media_type,
mime_type, alt_text, date.

Read-only — never modifies anything in WordPress.

alt_text is merged with whatever the output CSV already has, not
overwritten: this sheet is where descriptions actually get curated by hand
(WP's own alt_text field is usually left blank on upload), so if the API
returns an empty alt_text for an id already present in the existing CSV, the
existing description is kept. Only ids the API reports as genuinely
non-empty override what's on disk.
"""

import csv
import os
import sys

import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

PER_PAGE = 100


def wp_auth():
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        sys.exit(
            "Missing WP_URL / WP_USER / WP_APP_PASSWORD environment variables. "
            "Set these as GitHub secrets or export them locally before running."
        )
    return (WP_USER, WP_APP_PASSWORD)


def fetch_all_media():
    endpoint = f"{WP_URL}/wp-json/wp/v2/media"
    page = 1
    items = []
    while True:
        resp = requests.get(
            endpoint,
            params={"per_page": PER_PAGE, "page": page},
            auth=wp_auth(),
            timeout=30,
        )
        if resp.status_code == 400 and page > 1:
            # WP returns 400 "rest_post_invalid_page_number" past the last page
            break
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        items.extend(batch)
        total_pages = int(resp.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break
        page += 1
    return items


def load_existing_alt_text(path):
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {row["id"]: row["alt_text"] for row in csv.DictReader(f) if row.get("alt_text")}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "media-library.csv"

    existing_alt_text = load_existing_alt_text(out_path)
    items = fetch_all_media()
    print(f"Found {len(items)} media item(s) at {WP_URL}")

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "filename", "source_url", "media_type", "mime_type", "alt_text", "date"])
        for item in items:
            item_id = str(item.get("id"))
            alt_text = item.get("alt_text") or existing_alt_text.get(item_id, "")
            writer.writerow([
                item_id,
                os.path.basename(item.get("source_url", "")),
                item.get("source_url", ""),
                item.get("media_type", ""),
                item.get("mime_type", ""),
                alt_text,
                item.get("date", ""),
            ])

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
