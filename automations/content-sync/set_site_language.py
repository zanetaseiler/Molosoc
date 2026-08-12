#!/usr/bin/env python3
"""
Molosoc content-sync: set the WordPress site's admin language via the REST
API — the same setting as Settings -> General -> Site Language in wp-admin,
without a human needing to click through it by hand.

WordPress's REST Settings endpoint (/wp/v2/settings) exposes "language",
which maps 1:1 to Settings -> General -> Site Language. English (United
States) is represented internally as an empty string, not "en_US" — this
script accepts "en", "en_US", or "" on the command line and normalizes all
three to "" (the same result clicking "English (United States)" in
wp-admin and hitting Save produces).

Usage:
    python3 set_site_language.py --language en
    python3 set_site_language.py --language cs_CZ
"""

import os
import sys
import argparse

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
        description="Set the WordPress site language (Settings -> General -> Site Language) via the REST API."
    )
    parser.add_argument(
        "--language",
        required=True,
        help='WP locale code (e.g. "cs_CZ"), or "en"/"en_US"/"" for English (United States)',
    )
    args = parser.parse_args()

    value = args.language
    if value.lower() in ("en", "en_us"):
        value = ""  # WordPress core's own value for English (United States)

    resp = requests.get(f"{WP_URL}/wp-json/wp/v2/settings", auth=wp_auth(), timeout=30)
    resp.raise_for_status()
    current = resp.json().get("language", "(unknown)")
    print(f"Current site language: {current!r}")

    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/settings",
        json={"language": value},
        auth=wp_auth(),
        timeout=30,
    )
    if resp.status_code == 200:
        new_value = resp.json().get("language", "(unknown)")
        print(f"UPDATED site language -> {new_value!r} (English (United States))" if new_value == "" else f"UPDATED site language -> {new_value!r}")
    else:
        sys.exit(f"ERROR {resp.status_code}: {resp.text[:300]}")


if __name__ == "__main__":
    main()
