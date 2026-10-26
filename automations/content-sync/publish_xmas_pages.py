#!/usr/bin/env python3
"""
Publish the two existing Christmas gift drafts (CZ id 1065, EN id 1066) and
link them as a Polylang CZ<->EN translation pair. Issue #262.

Never creates a page: it only reads and updates the two fixed IDs, after
checking each is the expected slug/language. Safe to re-run.

Order (nothing is published unless the link is verified first):
  1. read both pages, verify slug + Polylang language
  2. dry-run (default) stops here and prints the plan
  3. --apply: link via the molosoc-migrate helper, re-read and verify the link
  4. only then set status=publish on any page still draft
Polylang state (language, translations) is read and written through the
molosoc-migration-helper mu-plugin (/molosoc-migrate/v1/status, /link-translations),
because the core pages endpoint does not expose it on Polylang Free.
Requires WP_URL to be exactly https://molosoc.com (checked before any request).
"""

import argparse
import os
import sys
from urllib.parse import urlparse

import requests

HOST = "molosoc.com"
PAGES = {
    "cz": {"id": 1065, "slug": "vanocni-darek-molosoc"},
    "en": {"id": 1066, "slug": "christmas-gift-molosoc"},
}


def validate_url(url):
    p = urlparse(url or "")
    if p.scheme != "https" or p.hostname != HOST or p.port or p.path.strip("/") or p.query:
        sys.exit(f"REFUSING: WP_URL must be exactly https://{HOST}. No request was made.")


def get_page(base, auth, pid):
    r = requests.get(f"{base}/wp-json/wp/v2/pages/{pid}", params={"context": "edit"}, auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()


def get_pll(base, auth, pid):
    r = requests.get(f"{base}/wp-json/molosoc-migrate/v1/status/{pid}", auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()


def check(page, pll, lang):
    exp = PAGES[lang]
    if page.get("slug") != exp["slug"] or pll.get("language") != lang:
        sys.exit(
            f"REFUSING: page {exp['id']} is slug={page.get('slug')!r} lang={pll.get('language')!r}, "
            f"expected slug={exp['slug']!r} lang={lang!r}. Nothing changed."
        )


def linked(base, auth):
    cz = get_pll(base, auth, PAGES["cz"]["id"])
    en = get_pll(base, auth, PAGES["en"]["id"])
    t_cz, t_en = cz.get("translations") or {}, en.get("translations") or {}
    return t_cz.get("en") == PAGES["en"]["id"] and t_en.get("cz") == PAGES["cz"]["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run, read-only)")
    args = ap.parse_args()

    base = os.environ.get("WP_URL", "").rstrip("/")
    validate_url(base)
    user, pw = os.environ.get("WP_USER", ""), os.environ.get("WP_APP_PASSWORD", "")
    if not (user and pw):
        sys.exit("Missing WP_USER / WP_APP_PASSWORD.")
    auth = (user, pw)

    pages = {lang: get_page(base, auth, spec["id"]) for lang, spec in PAGES.items()}
    for lang, page in pages.items():
        check(page, get_pll(base, auth, page["id"]), lang)
        print(f"{lang}: id={page['id']} status={page['status']} link={page.get('link')}")
    ok = linked(base, auth)
    print(f"translation link already set: {ok}")

    if not args.apply:
        print("DRY RUN: no changes made. Re-run with --apply to link and publish.")
        return

    if not ok:
        r = requests.post(
            f"{base}/wp-json/molosoc-migrate/v1/link-translations",
            json={"translations": {"cz": PAGES["cz"]["id"], "en": PAGES["en"]["id"]}},
            auth=auth, timeout=30,
        )
        r.raise_for_status()
        ok = linked(base, auth)
        if not ok:
            sys.exit("ABORT: translation link not confirmed after write. Nothing published. "
                     "Link manually in wp-admin (Languages box) then re-run.")
    print("translation link verified")

    for lang, spec in PAGES.items():
        if pages[lang]["status"] == "publish":
            print(f"{lang}: already published")
            continue
        r = requests.post(f"{base}/wp-json/wp/v2/pages/{spec['id']}", json={"status": "publish"}, auth=auth, timeout=30)
        r.raise_for_status()
        print(f"{lang}: published -> {r.json().get('link')}")

    for lang, spec in PAGES.items():
        st = get_page(base, auth, spec["id"])["status"]
        if st != "publish":
            sys.exit(f"VERIFY FAILED: {lang} id={spec['id']} status={st}")
    print("VERIFIED: both pages published and linked")


if __name__ == "__main__":
    main()
