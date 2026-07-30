#!/usr/bin/env python3
"""
Molosoc content-sync: upload a local binary file to the WordPress media
library via the REST API.

Unlike push_to_wp.py (pages/posts, always status=draft), media uploads have
no draft state — the file lands in the library immediately. That's fine:
an unattached media item isn't visible anywhere on the site until something
(a template, a block) actually references its URL.

On success, prints the resulting id and source_url and appends a row to
media-library.csv (same schema as list_media.py) so the file is discoverable
without a separate sync run.
"""

import csv
import mimetypes
import os
import sys
from datetime import datetime, timezone

import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

# WordPress's mimetypes module doesn't know about .glb; register it so
# requests/WP both see the right Content-Type instead of falling back to
# application/octet-stream.
mimetypes.add_type("model/gltf-binary", ".glb")


def wp_auth():
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        sys.exit(
            "Missing WP_URL / WP_USER / WP_APP_PASSWORD environment variables. "
            "Set these as GitHub secrets or export them locally before running."
        )
    return (WP_USER, WP_APP_PASSWORD)


def upload_file(path: str, alt_text: str = ""):
    filename = os.path.basename(path)
    content_type, _ = mimetypes.guess_type(filename)
    content_type = content_type or "application/octet-stream"

    with open(path, "rb") as f:
        data = f.read()

    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type,
        },
        data=data,
        auth=wp_auth(),
        timeout=120,
    )

    if resp.status_code not in (200, 201):
        sys.exit(f"ERROR uploading {path}: {resp.status_code} {resp.text[:300]}")

    item = resp.json()
    media_id = item["id"]
    source_url = item.get("source_url", "")
    print(f"  UPLOADED: {filename}  ->  {source_url}  (id {media_id})")

    if alt_text:
        alt_resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media/{media_id}",
            json={"alt_text": alt_text},
            auth=wp_auth(),
            timeout=30,
        )
        if alt_resp.status_code not in (200, 201):
            print(f"  WARN: alt_text update failed: {alt_resp.status_code} {alt_resp.text[:200]}")

    return item


def append_to_csv(out_path: str, item: dict):
    file_exists = os.path.exists(out_path)
    with open(out_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["id", "filename", "source_url", "media_type", "mime_type", "alt_text", "date"])
        writer.writerow([
            item.get("id"),
            os.path.basename(item.get("source_url", "")),
            item.get("source_url", ""),
            item.get("media_type", ""),
            item.get("mime_type", ""),
            item.get("alt_text", ""),
            item.get("date", datetime.now(timezone.utc).isoformat()),
        ])


def main():
    if len(sys.argv) < 2:
        print("Usage: upload_media.py <file1> [file2 ...] [--alt-text 'description'] [--csv media-library.csv]")
        sys.exit(1)

    args = sys.argv[1:]
    alt_text = ""
    csv_path = "media-library.csv"
    files = []

    i = 0
    while i < len(args):
        if args[i] == "--alt-text":
            alt_text = args[i + 1]
            i += 2
        elif args[i] == "--csv":
            csv_path = args[i + 1]
            i += 2
        else:
            files.append(args[i])
            i += 1

    if not files:
        print("No files given.")
        sys.exit(1)

    print(f"Uploading {len(files)} file(s) to {WP_URL} ...")
    for path in files:
        item = upload_file(path, alt_text=alt_text)
        append_to_csv(csv_path, item)


if __name__ == "__main__":
    main()
