#!/usr/bin/env python3
"""
Molosoc content-sync: create the Czech cart/checkout page twins (slugs
"kosik" and "pokladna") that GitHub Issue #53's bilingual purchase flow
needs — /cz/kosik/ and /cz/pokladna/ — as drafts, copying the live
block/shortcode content of the existing EN cart (page 359) and checkout
(page 360) pages so the Czech pages render the same cart/checkout blocks.

Same safety model as create_wp_page.py: creates as DRAFT only, so a human
still has to hit Publish in wp-admin. Safe to re-run — if a page with the
target slug already exists (draft or published), it is skipped rather
than duplicated or overwritten.

WHY content is fetched live via REST (content.raw on /wp/v2/pages/359 and
/wp/v2/pages/360) rather than hardcoded here: the cart page is WooCommerce
block markup and the checkout page is the [woocommerce_checkout] shortcode
— both are content a site editor can and does change from wp-admin, so a
hardcoded copy in this repo would silently drift out of sync. Fetching
live keeps this script correct regardless of future edits to 359/360,
at the cost of requiring EN pages 359/360 to exist and be readable at
the time this runs (they do, per the issue's own audit).

Polylang translation linking: Polylang free's REST API (as of the 3.8.x
line audited for this issue) does not reliably expose a documented,
stable endpoint for setting a page's language and translation-group
membership on plain wp/v2/pages create — this varies by exact Polylang
version/REST-API settings and could not be verified from this repo (no
server/plugin access). Rather than guess at an unstable filter/meta key
name and silently fail closed, this script:
  1. Creates each page as an ordinary draft Page via wp/v2/pages (slug +
     copied content), same as create_wp_page.py.
  2. Prints an explicit, unmissable manual follow-up step: open each new
     Page in wp-admin, use the Languages meta box to set its language to
     Czech (cs_CZ) and link it as the CZ translation of page 359 (cart) /
     360 (checkout) respectively.
This manual step is an acceptable trade-off here because page creation
itself already requires a human to hit Publish (this repo's standing
safety gate) — the same person doing that review sets the two dropdowns
in the same sitting. If a later Polylang version exposes a reliable REST
path for this, prefer switching to it over the manual step.

This script is NOT executed by the PR that added it — creating production
content and rewriting Polylang's translation table are both write actions
that need Zaneta's separate approval and, for the translation-link step,
a human in wp-admin regardless. Run manually or via
.github/workflows/create-cart-checkout-cz-pages.yml (workflow_dispatch
only, never on push).

Usage:
    python3 create_cart_checkout_cz_pages.py
"""

import os
import sys

import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

# The two EN pages this store already uses — see the issue's own audit:
# cart page 359 (block cart), checkout page 360 (classic [woocommerce_checkout]
# shortcode checkout).
SOURCE_PAGES = (
    {"source_id": 359, "slug": "kosik", "title": "Košík", "kind": "cart"},
    {"source_id": 360, "slug": "pokladna", "title": "Pokladna", "kind": "checkout"},
)


def wp_auth():
    if not (WP_URL and WP_USER and WP_APP_PASSWORD):
        sys.exit(
            "Missing WP_URL / WP_USER / WP_APP_PASSWORD environment variables. "
            "Set these as GitHub secrets or export them locally before running."
        )
    return (WP_USER, WP_APP_PASSWORD)


def fetch_source_content(source_id):
    """Live block/shortcode markup from the EN page, via content.raw.

    content.raw requires the request to be authenticated as a user who can
    edit pages (the same app-password auth used everywhere else in this
    file) — the public REST response only ever exposes content.rendered.
    """
    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/pages/{source_id}",
        params={"context": "edit"},
        auth=wp_auth(),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    raw = (data.get("content") or {}).get("raw")
    if raw is None:
        sys.exit(
            f"ERROR: page {source_id} response had no content.raw — was the "
            f"request authenticated with edit permission? Got keys: {list(data.keys())}"
        )
    return raw


def main():
    # Every target page this run either finds already existing or creates
    # — NOT just the ones created this run. A prior run can have created
    # page 1, then failed (network error, page 2's create call rejected,
    # etc.) before ever reaching the final follow-up print below; on a
    # rerun, page 1 is found via the "already exists" branch and must
    # still be carried into the follow-up list, or its still-pending
    # manual Polylang-linking step is silently lost for good (it will
    # never be selected by pll_get_post() until that step is done).
    needs_follow_up = []
    for target in SOURCE_PAGES:
        slug = target["slug"]

        existing_resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/pages",
            params={"slug": slug, "status": "draft,publish,future"},
            auth=wp_auth(),
            timeout=30,
        )
        existing_resp.raise_for_status()
        existing = existing_resp.json()
        if existing:
            page = existing[0]
            print(
                f"Page {slug!r} already exists — id={page['id']}, "
                f"status={page['status']}, link={page.get('link', '(none)')}. "
                f"Nothing to do."
            )
            needs_follow_up.append(
                {"id": page["id"], "slug": slug, "source_id": target["source_id"]}
            )
            continue

        print(f"Fetching live content from source page {target['source_id']} ({target['kind']}) ...")
        content_raw = fetch_source_content(target["source_id"])

        payload = {
            "title": target["title"],
            "slug": slug,
            "status": "draft",
            "content": content_raw,
        }
        resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/pages", json=payload, auth=wp_auth(), timeout=30
        )
        if resp.status_code not in (200, 201):
            sys.exit(f"ERROR creating {slug!r}: {resp.status_code} {resp.text[:300]}")

        data = resp.json()
        print(f"CREATED draft page — id={data['id']}, slug={slug!r}, title={target['title']!r}")
        print(f"Review/edit at: {WP_URL}/wp-admin/post.php?post={data['id']}&action=edit")
        needs_follow_up.append(
            {"id": data["id"], "slug": slug, "source_id": target["source_id"]}
        )

    if needs_follow_up:
        print("")
        print("MANUAL FOLLOW-UP REQUIRED (see this script's own header comment for why):")
        for c in needs_follow_up:
            print(
                f"  - Open {WP_URL}/wp-admin/post.php?post={c['id']}&action=edit, "
                f"set Language = Czech in the Languages meta box, and link it as "
                f"the translation of page {c['source_id']}."
            )
        print("  Then hit Publish on each once reviewed (same standing safety gate")
        print("  as every other page this repo's automations create as a draft).")
        print("  (Listed above regardless of whether it was just created or already")
        print("  existed — safe to skip if a given page's translation link is")
        print("  already set; re-run this script any time to see this list again.)")


if __name__ == "__main__":
    main()
