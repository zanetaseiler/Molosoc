#!/usr/bin/env python3
"""
Molosoc content-sync: translate the two empty-cart headings saved inside
the Czech cart page (page 1012, /cz/kosik/) — GitHub Issue #198.

The CZ cart page was created by copying the EN cart page's (359) block
markup (create_cart_checkout_cz_pages.py), so the WooCommerce Cart block's
`woocommerce/empty-cart-block` inner headings are still saved in English:

    "Your cart is currently empty!"  ->  "Váš košík je zatím prázdný."
    "New in store"                   ->  "Novinky v obchodě"

This script changes exactly those two heading TEXTS in page 1012's saved
content (content.raw) and nothing else — every block comment, attribute
and class stays byte-for-byte as WordPress saved it, so the page keeps
opening in the editor with no block-recovery prompt. It never touches the
EN page 359 (read-only sanity check), page 1013, or any other page.

Safety model:
  * Default run is a DRY RUN: it fetches, prints what would change, writes
    nothing. `--apply` performs the write.
  * verify_target_is_production() (shared with create_cart_checkout_cz_pages.py,
    Issue #65) proves from the target's own site identity that WP_URL is
    molosoc.com production before anything is read.
  * The page must be id 1012, slug "kosik", served at /cz/kosik/ on a
    production host, or the script refuses.
  * Each English heading must occur exactly once (a heading already in
    Czech is skipped, so re-running is idempotent); anything else aborts
    before the write.
  * After the write the page is re-read and must equal the content this
    script sent, byte for byte; if WordPress altered anything else on save
    (kses, balanceTags, a plugin filter) the run fails loudly and names the
    editor's Revisions screen for a one-click restore.

Run only via .github/workflows/translate-cz-cart-empty-state.yml
(workflow_dispatch, never on push) or locally with WP_URL / WP_USER /
WP_APP_PASSWORD exported. Not executed by the PR that added it — editing
published production content needs Zaneta's separate approval.

Usage:
    python3 translate_cz_cart_empty_state.py            # dry run
    python3 translate_cz_cart_empty_state.py --apply    # write page 1012
"""

import argparse
import sys

import requests

from create_cart_checkout_cz_pages import (
    PRODUCTION_HOSTS,
    WP_URL,
    _host,
    verify_target_is_production,
    wp_auth,
)

# The CZ cart page (Polylang twin of EN cart page 359) — Issue #198.
PAGE_ID = 1012
EXPECTED_SLUG = "kosik"
EXPECTED_PATH = "/cz/kosik/"
EN_TWIN_ID = 359

# (English saved text, Czech replacement). Matched together with the
# closing </h2> and the preceding '>' so only the heading's text node is
# ever touched — never a class name or block attribute that might contain
# a similar phrase.
REPLACEMENTS = (
    (">Your cart is currently empty!</h2>", ">Váš košík je zatím prázdný.</h2>"),
    (">New in store</h2>", ">Novinky v obchodě</h2>"),
)


class ContentMismatch(Exception):
    """Page content is not in the one shape this script knows how to edit."""


def translate_cart_content(raw):
    """Return (new_raw, changed) for the saved block markup `raw`.

    `changed` lists the (old, new) pairs actually replaced. A heading that
    already carries its Czech text (and no English one) is skipped, so the
    function is idempotent; any other count of the English text raises
    ContentMismatch rather than guessing.
    """
    out = raw
    changed = []
    for old, new in REPLACEMENTS:
        n_old = out.count(old)
        if n_old == 1:
            out = out.replace(old, new, 1)
            changed.append((old, new))
        elif n_old == 0 and new in out:
            continue  # Already translated on an earlier run.
        else:
            raise ContentMismatch(
                f"expected exactly one {old!r} in page {PAGE_ID}'s saved content, "
                f"found {n_old} (and Czech text present: {new in out}). Nothing "
                f"was written — inspect the page in wp-admin before re-running."
            )
    for _, new in REPLACEMENTS:
        if out.count(new) != 1:
            raise ContentMismatch(
                f"after replacement {new!r} occurs {out.count(new)} times, expected 1. "
                f"Nothing was written."
            )
    return out, changed


def fetch_page_raw(page_id):
    """(page json, content.raw) via an authenticated context=edit read."""
    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/pages/{page_id}",
        params={"context": "edit"},
        auth=wp_auth(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    raw = (data.get("content") or {}).get("raw")
    if raw is None:
        sys.exit(
            f"ERROR: page {page_id} response had no content.raw — was the request "
            f"authenticated with edit permission? Got keys: {list(data.keys())}"
        )
    return data, raw


def verify_is_cz_cart_page(page):
    """Refuse unless this really is the published CZ cart page on production."""
    link = page.get("link") or ""
    problems = []
    if page.get("id") != PAGE_ID:
        problems.append(f"id={page.get('id')!r} != {PAGE_ID}")
    if page.get("slug") != EXPECTED_SLUG:
        problems.append(f"slug={page.get('slug')!r} != {EXPECTED_SLUG!r}")
    if _host(link) not in PRODUCTION_HOSTS:
        problems.append(f"link host {_host(link)!r} is not production")
    if not link.endswith(EXPECTED_PATH):
        problems.append(f"link={link!r} does not end with {EXPECTED_PATH!r}")
    if problems:
        sys.exit(
            "REFUSING TO CONTINUE: page %d is not the CZ cart page this script "
            "expects (%s). Nothing was written." % (PAGE_ID, "; ".join(problems))
        )
    print(
        f"Target page: id={page.get('id')} slug={page.get('slug')!r} "
        f"status={page.get('status')!r} link={link!r}"
    )


def check_en_twin_untouched():
    """Read-only: the EN cart page must still carry both English headings."""
    _, raw = fetch_page_raw(EN_TWIN_ID)
    missing = [old for old, _ in REPLACEMENTS if old not in raw]
    if missing:
        print(
            f"WARNING: EN cart page {EN_TWIN_ID} does not contain {missing!r} — "
            f"this script never writes to it, so that is pre-existing; check it "
            f"in wp-admin."
        )
    else:
        print(f"EN cart page {EN_TWIN_ID}: both English headings present (unchanged).")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the translated content to page %d (default: dry run, no write)"
        % PAGE_ID,
    )
    args = parser.parse_args(argv)

    verify_target_is_production()

    page, raw = fetch_page_raw(PAGE_ID)
    verify_is_cz_cart_page(page)

    try:
        new_raw, changed = translate_cart_content(raw)
    except ContentMismatch as exc:
        sys.exit(f"REFUSING TO CONTINUE: {exc}")

    if not changed:
        print("Both headings are already Czech — nothing to do, nothing written.")
        check_en_twin_untouched()
        return 0

    for old, new in changed:
        print(f"  {old!r}\n    -> {new!r}")

    if not args.apply:
        print("DRY RUN — nothing written. Re-run with --apply (workflow input "
              "'apply') to save these two changes to page %d." % PAGE_ID)
        check_en_twin_untouched()
        return 0

    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/pages/{PAGE_ID}",
        json={"content": new_raw},
        auth=wp_auth(),
        timeout=30,
    )
    if resp.status_code != 200:
        sys.exit(f"ERROR updating page {PAGE_ID}: {resp.status_code} {resp.text[:300]}")
    print(f"UPDATED page {PAGE_ID} ({len(changed)} heading(s) translated).")

    _, reread = fetch_page_raw(PAGE_ID)
    if reread != new_raw:
        sys.exit(
            f"ERROR: page {PAGE_ID} was saved, but WordPress stored content that "
            f"differs from what this script sent (sent {len(new_raw)} chars, "
            f"stored {len(reread)} chars). Something on save (kses, balanceTags, "
            f"a plugin filter) changed more than the two headings. Restore the "
            f"previous revision at {WP_URL}/wp-admin/post.php?post={PAGE_ID}"
            f"&action=edit (Revisions) and investigate before re-running."
        )
    print(f"Verified: re-read content of page {PAGE_ID} matches byte for byte.")
    print(f"Check live: {WP_URL}/cz/kosik/ with an empty cart.")

    check_en_twin_untouched()
    return 0


if __name__ == "__main__":
    sys.exit(main())
