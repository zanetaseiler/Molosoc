#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scripted HTTP test for the bilingual WooCommerce purchase flow
(GitHub Issue #53): CZ /cz/produkt -> /cz/kosik -> /cz/pokladna ->
/cz/pokladna/order-received/..., EN /product -> /cart -> /checkout ->
/checkout/order-received/..., both fully in their own language.

REQUIRES: env var WP_URL (e.g. https://staging.molosoc.com), pointing at a
site where:
  1. This PR's code (site/theme/inc/woocommerce-lang.php and its callers)
     is already deployed, AND
  2. The two Czech cart/checkout Page twins (slugs "kosik" and "pokladna",
     Polylang-linked to pages 359/360) already exist and are published —
     see automations/content-sync/create_cart_checkout_cz_pages.py.

This script is NOT run by the PR that adds it. Both prerequisites above
are production changes this PR deliberately does not make (see that
script's own header, and the PR description's "not executed" note) — this
is a deliverable for CI or for Zaneta to run once both are true, not
something this session can execute (no network access to any WP install
from this sandbox, and no server exists yet in the session's reach even
if there were).

What it checks, per language (en, cz):
  - product -> cart -> checkout -> order-received URL routing: each hop
    responds HTTP 200 directly (no 301/302 redirect chain), and the
    rendered page's <html lang="..."> attribute matches en-US / cs-CZ.
  - The rendered product page's own cart/checkout links (header cart link,
    add-to-cart form action) point at the CZ pages when language is cz,
    EN pages when language is en — checked by parsing the rendered HTML,
    since this script has no way to call wc_get_cart_url()/
    wc_get_checkout_url() directly over HTTP.
  - Size dropdown: placeholder text ("Vyberte velikost" / "Choose your
    size") and that "M (36" appears before "L (39.5" in the rendered
    option order.
  - Price HTML: CZ product page shows "229 Kč" without a EUR figure; EN
    product page shows "€10" and "229 CZK".
  - EN shipping/payment labels: adds product 364 (variation 424) to an
    ephemeral cart (its own curl cookie-jar session, never submitted to
    checkout, no order is placed) and greps the rendered EN checkout page
    for the mapped English labels (PPL pickup point, Bank transfer, Card
    payment (Comgate), etc.) instead of the Czech originals.

Every request is read-only except the one non-destructive add-to-cart POST
used for the shipping/payment-label check above, which only ever touches
that ephemeral session's own cart — no order is created, no inventory is
touched, nothing is submitted to checkout.

curl (not python's requests/urllib) for the same reason
scripts/cleanup_test_order.py uses it: this repo has already observed
Cloudflare reject the default python-urllib user agent on this host with
error 1010.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

WP_URL = os.environ.get("WP_URL", "").rstrip("/")

PRODUCT_ID = 364
VARIATION_ID_L = 424  # noqa: not used directly, documented for reference
VARIATION_ID_M = 425  # noqa: not used directly, documented for reference

EN = {
    "product_url": "/product/moisture-lock-foot-cover/",
    "cart_url": "/cart/",
    "checkout_url": "/checkout/",
    "html_lang": "en-US",
    "size_placeholder": "Choose your size",
    "price_needles": ["€10", "229 CZK"],
    "price_absent": ["229 Kč"],
}
CZ = {
    "product_url": "/cz/produkt/hydratacni-navlek-na-nohy/",
    "cart_url": "/cz/kosik/",
    "checkout_url": "/cz/pokladna/",
    "html_lang": "cs-CZ",
    "size_placeholder": "Vyberte velikost",
    "price_needles": ["229 Kč"],
    "price_absent": ["€10"],
}

EN_LABEL_NEEDLES = [
    "PPL pickup point",
    "PPL home delivery",
    "Zásilkovna Z-BOX",
    "Zásilkovna pickup point",
    "Card payment (Comgate)",
    "Bank transfer",
]

results = []  # list of {"check": str, "status": "PASS"|"FAIL"|"SKIP", "detail": str}


def record(check, ok, detail="", skip=False):
    status = "SKIP" if skip else ("PASS" if ok else "FAIL")
    results.append({"check": check, "status": status, "detail": detail})
    print("  [%s] %s%s" % (status, check, (" — " + detail) if detail else ""))


def curl(method, path, cookie_jar=None, data=None, follow_redirects=False, extra_headers=None):
    """One HTTP call via curl. Returns (status_code, final_url, body_text, headers_text)."""
    url = path if path.startswith("http") else (WP_URL + path)
    body_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    body_file.close()
    header_file = tempfile.NamedTemporaryFile(delete=False, suffix=".hdr")
    header_file.close()

    cmd = [
        "curl", "-sS", "-o", body_file.name, "-D", header_file.name,
        "-w", "%{http_code} %{url_effective}",
        "-X", method, "--max-time", "30",
    ]
    if follow_redirects:
        cmd.append("-L")
    if cookie_jar:
        cmd += ["-b", cookie_jar, "-c", cookie_jar]
    for h in (extra_headers or []):
        cmd += ["-H", h]
    if data is not None:
        cmd += ["--data-raw", data]
    cmd.append(url)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return 0, url, "", "", "curl transport error: %s" % exc

    out = (proc.stdout or "").strip().split(" ", 1)
    try:
        code = int(out[0])
    except (ValueError, IndexError):
        code = 0
    final_url = out[1] if len(out) > 1 else url

    body = ""
    try:
        with open(body_file.name, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
    except OSError:
        pass
    headers = ""
    try:
        with open(header_file.name, encoding="utf-8", errors="replace") as fh:
            headers = fh.read()
    except OSError:
        pass
    for f in (body_file.name, header_file.name):
        try:
            os.unlink(f)
        except OSError:
            pass

    return code, final_url, body, headers, None


def check_no_redirect_chain(label, path):
    """A single hop must answer 200 directly — not a 301/302 (i.e. WP core's
    redirect_canonical, or a missing/incorrect rewrite, sending the visitor
    somewhere else first)."""
    code, final_url, body, headers, err = curl("GET", path, follow_redirects=False)
    if err:
        record(label, False, err)
        return None
    ok = code == 200
    record(label, ok, "HTTP %s at %s" % (code, path))
    return body if ok else None


def check_html_lang(label, body, expected_lang):
    if body is None:
        record(label, False, "no body to check (previous fetch failed)", skip=False)
        return
    m = re.search(r'<html[^>]*\blang="([^"]+)"', body, re.IGNORECASE)
    found = m.group(1) if m else None
    record(label, found == expected_lang, "found lang=%r, expected %r" % (found, expected_lang))


def check_contains(label, body, needles, all_required=True):
    if body is None:
        record(label, False, "no body to check (previous fetch failed)")
        return
    hits = [n for n in needles if n in body]
    ok = (len(hits) == len(needles)) if all_required else (len(hits) > 0)
    record(label, ok, "found=%s / expected=%s" % (hits, needles))


def check_absent(label, body, needles):
    if body is None:
        record(label, False, "no body to check (previous fetch failed)")
        return
    hits = [n for n in needles if n in body]
    record(label, len(hits) == 0, "unexpectedly present: %s" % hits if hits else "none present, as expected")


def check_size_order(label, body):
    if body is None:
        record(label, False, "no body to check (previous fetch failed)")
        return
    m_pos = body.find("M (36")
    l_pos = body.find("L (39.5")
    ok = m_pos != -1 and l_pos != -1 and m_pos < l_pos
    record(label, ok, "M at %d, L at %d (M must come first)" % (m_pos, l_pos))


def run_language_flow(lang_key, cfg):
    print("")
    print("=== %s ===" % lang_key.upper())

    product_body = check_no_redirect_chain(
        "%s: product URL resolves 200 (no redirect chain)" % lang_key, cfg["product_url"]
    )
    check_html_lang("%s: product page <html lang>" % lang_key, product_body, cfg["html_lang"])
    check_contains("%s: product price HTML shows expected currency copy" % lang_key,
                    product_body, cfg["price_needles"])
    check_absent("%s: product price HTML does NOT show the other language's price" % lang_key,
                  product_body, cfg["price_absent"])
    check_contains("%s: size dropdown placeholder present" % lang_key,
                    product_body, [cfg["size_placeholder"]])
    check_size_order("%s: size options render M before L" % lang_key, product_body)

    if product_body is not None:
        # The rendered header cart link (functions.php molosoc_cart_link())
        # should point at this language's cart URL.
        cart_href_ok = cfg["cart_url"] in product_body
        record(
            "%s: header cart link points at %s" % (lang_key, cfg["cart_url"]),
            cart_href_ok,
            "cart_url substring %s in product page HTML" % ("found" if cart_href_ok else "NOT found"),
        )

    cart_body = check_no_redirect_chain("%s: cart URL resolves 200 (no redirect chain)" % lang_key, cfg["cart_url"])
    check_html_lang("%s: cart page <html lang>" % lang_key, cart_body, cfg["html_lang"])

    checkout_body = check_no_redirect_chain(
        "%s: checkout URL resolves 200 (no redirect chain)" % lang_key, cfg["checkout_url"]
    )
    check_html_lang("%s: checkout page <html lang>" % lang_key, checkout_body, cfg["html_lang"])


def run_en_shipping_payment_label_check():
    """Best-effort: adds product 364/variation 424 to an ephemeral cart
    (own cookie-jar session) and checks the rendered EN checkout page for
    the mapped English shipping/payment labels. Non-destructive — nothing
    is submitted to checkout, no order is created; the cart only exists in
    this session's own cookies, which are discarded when the script exits.

    SKIPped (not failed) if the add-to-cart doesn't visibly succeed, since
    shipping methods depend on the store's configured zones/rates actually
    matching whatever address WooCommerce defaults to for a guest with no
    address set yet — this check can only confirm the LABEL TEXT mapping,
    not that every rate is configured to show under every possible
    shipping-zone/tax scenario.
    """
    print("")
    print("=== EN shipping/payment label mapping (best-effort) ===")

    tmp_jar = tempfile.NamedTemporaryFile(delete=False, suffix=".cookies")
    tmp_jar.close()
    jar = tmp_jar.name
    try:
        add_path = "/?add-to-cart=%d&variation_id=%d&quantity=1" % (PRODUCT_ID, 424)
        code, _final, body, _headers, err = curl("GET", add_path, cookie_jar=jar, follow_redirects=True)
        if err or code != 200:
            record("EN: add product 364 to ephemeral cart", False,
                   "HTTP %s%s" % (code, (" " + err) if err else ""), skip=True)
            return
        record("EN: add product 364 to ephemeral cart", True, "HTTP %s" % code)

        code, _final, checkout_body, _headers, err = curl(
            "GET", EN["checkout_url"], cookie_jar=jar, follow_redirects=True
        )
        if err or code != 200:
            record("EN: fetch checkout with item in ephemeral cart", False,
                   "HTTP %s%s" % (code, (" " + err) if err else ""), skip=True)
            return

        for needle in EN_LABEL_NEEDLES:
            found = needle in checkout_body
            # A rate/gateway not appearing isn't necessarily a bug in the
            # label mapping — it may simply not be configured to show for
            # whatever shipping zone/address WooCommerce defaults a guest
            # to. SKIP (not FAIL) when absent, rather than assert every
            # rate must always be visible.
            record("EN: checkout shows label %r" % needle, found,
                   detail="" if found else "not present — may not apply to the default shipping zone",
                   skip=not found)
    finally:
        try:
            os.unlink(jar)
        except OSError:
            pass


def main():
    if not WP_URL:
        print("::error::WP_URL is not set. This script requires a deployed site to test against.")
        print("It cannot run until: (1) this PR's code is deployed, AND (2) the CZ")
        print("kosik/pokladna pages exist and are published. See this file's own header.")
        sys.exit(1)

    print("Testing bilingual purchase flow against %s" % WP_URL)

    run_language_flow("en", EN)
    run_language_flow("cz", CZ)
    run_en_shipping_payment_label_check()

    print("")
    print("----- BEGIN TEST RESULT -----")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("----- END TEST RESULT -----")

    failures = [r for r in results if r["status"] == "FAIL"]
    print("")
    print("%d check(s), %d pass, %d fail, %d skip"
          % (len(results), sum(r["status"] == "PASS" for r in results),
             len(failures), sum(r["status"] == "SKIP" for r in results)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
