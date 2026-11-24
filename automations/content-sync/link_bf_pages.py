#!/usr/bin/env python3
"""
Link the two existing Black Friday pages (CZ id 1128, EN id 1129) as a
Polylang CZ<->EN translation pair, so the language switcher on each page
points at the other page instead of falling back to the other language's
homepage. Issue #384.

Scope: only these two fixed IDs. Never creates, publishes, unpublishes or edits
page content; never touches language routing, menus, the switcher settings,
the offer or checkout. Safe to re-run (a pair that is already linked is a no-op).

Order:
  1. read both pages (core REST, context=edit) and their Polylang state
     (molosoc-migration-helper /status), verify slug + language
  2. print the current translations and the live switcher hrefs (public HTML)
  3. dry-run (default) stops here
  4. --apply: refuse if either page is already paired with a *different* page
     (that would silently unlink another translation); otherwise link via the
     helper's /link-translations (Polylang's own pll_save_post_translations),
     re-read and verify the pair from both sides
Requires WP_URL to be exactly https://molosoc.com (checked before any request).
"""

import argparse
import html
import os
import re
import sys
from urllib.parse import urlparse

import requests

HOST = "molosoc.com"
PAGES = {
    "cz": {"id": 1128, "slug": "black-friday-molosoc", "path": "/cz/black-friday-molosoc/"},
    "en": {"id": 1129, "slug": "black-friday-offer-molosoc", "path": "/black-friday-offer-molosoc/"},
}
OTHER = {"cz": "en", "en": "cz"}


def validate_url(url):
    p = urlparse(url or "")
    if p.scheme != "https" or p.hostname != HOST or p.port or p.path.strip("/") or p.query:
        sys.exit(f"REFUSING: WP_URL must be exactly https://{HOST}. No request was made.")


def get_page(base, auth, pid):
    r = requests.get(f"{base}/wp-json/wp/v2/pages/{pid}", params={"context": "edit"}, auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()


def helper_missing_msg(pid):
    return (
        "ABORT: Polylang helper endpoint /wp-json/molosoc-migrate/v1/status is not registered on "
        f"{HOST} (REST code rest_no_route, page id {pid}). The molosoc-migration-helper mu-plugin is "
        "not deployed. Either run migrate-to-production.yml phase=deploy-helper (needs Zaneta's "
        "approval), re-run this dry run and remove-helper afterwards, or link the pages by hand in "
        "wp-admin (docs/bf-language-switcher-384.md). Nothing was changed."
    )


def get_pll(base, auth, pid):
    r = requests.get(f"{base}/wp-json/molosoc-migrate/v1/status/{pid}", auth=auth, timeout=30)
    if r.status_code == 404:
        try:
            code = r.json().get("code")
        except ValueError:
            code = None
        if code != "no_post":
            sys.exit(helper_missing_msg(pid))
    r.raise_for_status()
    return r.json()


def check(page, pll, lang):
    exp = PAGES[lang]
    if page.get("slug") != exp["slug"] or pll.get("language") != lang:
        sys.exit(
            f"REFUSING: page {exp['id']} is slug={page.get('slug')!r} lang={pll.get('language')!r}, "
            f"expected slug={exp['slug']!r} lang={lang!r}. Nothing changed."
        )


def translations(pll):
    t = pll.get("translations") or {}
    return {k: int(v) for k, v in t.items()} if isinstance(t, dict) else {}


def is_linked(t_cz, t_en):
    return t_cz.get("en") == PAGES["en"]["id"] and t_en.get("cz") == PAGES["cz"]["id"]


def conflicts(t_cz, t_en):
    """Pairings that linking 1128<->1129 would overwrite (another page in the other language)."""
    out = []
    other_en = t_cz.get("en")
    if other_en not in (None, PAGES["en"]["id"]):
        out.append(f"CZ {PAGES['cz']['id']} is already paired with EN page {other_en}")
    other_cz = t_en.get("cz")
    if other_cz not in (None, PAGES["cz"]["id"]):
        out.append(f"EN {PAGES['en']['id']} is already paired with CZ page {other_cz}")
    return out


LANG_ITEM_RE = re.compile(r'<li[^>]*class="[^"]*\blang-item-([a-z]{2})\b[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"', re.I)


def switcher_hrefs(page_html):
    """{lang slug: href} from Polylang's <li class="lang-item lang-item-xx"><a href=...> switcher."""
    out = {}
    for lang, href in LANG_ITEM_RE.findall(page_html or ""):
        out.setdefault(lang.lower(), html.unescape(href))
    return out


def report_switcher(base):
    for lang, spec in PAGES.items():
        url = base + spec["path"]
        try:
            r = requests.get(url, timeout=30, allow_redirects=False)
        except Exception as exc:  # report only; the dry run must not fail on this
            print(f"{lang}: GET {url} failed: {exc}")
            continue
        hrefs = switcher_hrefs(r.text) if r.status_code == 200 else {}
        target = hrefs.get(OTHER[lang])
        want = base + PAGES[OTHER[lang]]["path"]
        mark = "OK" if target == want else "WRONG"
        print(f"{lang}: {url} -> HTTP {r.status_code}; switcher {OTHER[lang]} href={target!r} "
              f"(expected {want}) {mark}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="link the pair (default: dry-run, read-only)")
    args = ap.parse_args()

    base = os.environ.get("WP_URL", "").rstrip("/")
    validate_url(base)
    user, pw = os.environ.get("WP_USER", ""), os.environ.get("WP_APP_PASSWORD", "")
    if not (user and pw):
        sys.exit("Missing WP_USER / WP_APP_PASSWORD.")
    auth = (user, pw)

    pll = {}
    for lang, spec in PAGES.items():
        page = get_page(base, auth, spec["id"])
        pll[lang] = get_pll(base, auth, spec["id"])
        check(page, pll[lang], lang)
        print(f"{lang}: id={spec['id']} status={page.get('status')} link={page.get('link')} "
              f"translations={translations(pll[lang])}")
    t_cz, t_en = translations(pll["cz"]), translations(pll["en"])
    ok = is_linked(t_cz, t_en)
    print(f"translation pair 1128<->1129 already linked: {ok}")
    report_switcher(base)

    bad = conflicts(t_cz, t_en)
    if bad and not ok:
        sys.exit("REFUSING: " + "; ".join(bad) + ". Linking would unlink that page. Nothing changed.")

    if not args.apply:
        print("DRY RUN: no changes made. Re-run with apply=true to link the pair.")
        return
    if ok:
        print("Nothing to do: already linked.")
        return

    r = requests.post(
        f"{base}/wp-json/molosoc-migrate/v1/link-translations",
        json={"translations": {"cz": PAGES["cz"]["id"], "en": PAGES["en"]["id"]}},
        auth=auth, timeout=30,
    )
    r.raise_for_status()
    if not is_linked(translations(get_pll(base, auth, PAGES["cz"]["id"])),
                     translations(get_pll(base, auth, PAGES["en"]["id"]))):
        sys.exit("ABORT: translation link not confirmed after write. Link by hand in wp-admin (Languages box).")
    print("VERIFIED: 1128 (cz) <-> 1129 (en) linked. Purge the page cache for 1128 and 1129, then re-run the dry run "
          "to confirm the live switcher hrefs.")


if __name__ == "__main__":
    main()
