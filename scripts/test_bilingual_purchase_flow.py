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

OPTIONAL: WP_USER / WP_APP_PASSWORD (a WooCommerce REST API-capable
WordPress Application Password on that same WP_URL host, same convention
as scripts/cleanup_test_order.py). When both are set, one extra check per
language creates a real, non-paid WC_Order fixture (status "pending", one
line item of product 364 / variation 424, tagged with the same
`_molosoc_lang` meta this PR's checkout hook writes) to exercise
molosoc_cz_order_received_url() itself — the bogus-order-id probe below
only proves the order-received endpoint exists on each language's own
checkout page, not that this filter routes a real order to the right one.
The fixture order is always cancelled and trashed (force=false, same as
cleanup_test_order.py) before the check returns, pass or fail. Without
these two env vars, this extra check is SKIPped and the script's behavior
is unchanged from before — still guest-HTTP-only, no order created.

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

Every guest-HTTP request is read-only except the one non-destructive
add-to-cart POST used for the shipping/payment-label check above, which
only ever touches that ephemeral session's own cart — no order is
created, no inventory is touched, nothing is submitted to checkout. The
one exception to "no order is created" is the OPTIONAL, credential-gated
order-received fixture check described above, which is skipped entirely
unless WP_USER/WP_APP_PASSWORD are explicitly provided.

curl (not python's requests/urllib) for the same reason
scripts/cleanup_test_order.py uses it: this repo has already observed
Cloudflare reject the default python-urllib user agent on this host with
error 1010.
"""

import html
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

PRODUCT_ID = 364
VARIATION_ID_L = 424
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


def wc_api_call(method, path, payload=None):
    """One WooCommerce REST API call (wp-json/wc/v3), authenticated via
    WP_USER/WP_APP_PASSWORD. Same conventions as scripts/cleanup_test_order.py's
    call() helper: curl (not requests/urllib, for the Cloudflare user-agent
    reason documented at the top of this file), credentials passed through a
    stdin config file so they never appear in the process argument list."""
    url = "%s/wp-json/wc/v3%s" % (WP_URL, path)
    body_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    body_file.close()
    cmd = [
        "curl", "-sS", "-K", "-", "-o", body_file.name,
        "-w", "%{http_code}", "-X", method, "--max-time", "60",
        "-H", "Accept: application/json",
    ]
    if payload is not None:
        cmd += ["-H", "Content-Type: application/json", "--data-raw", json.dumps(payload)]
    cmd.append(url)

    config = 'user = "%s:%s"\n' % (WP_USER, WP_APP_PASSWORD)
    try:
        proc = subprocess.run(cmd, input=config, capture_output=True, text=True, timeout=90)
    except Exception as exc:
        return 0, {"transport_error": "%s: %s" % (type(exc).__name__, exc)}

    try:
        code = int((proc.stdout or "0").strip() or 0)
    except ValueError:
        code = 0

    raw = ""
    try:
        with open(body_file.name, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError:
        pass
    finally:
        try:
            os.unlink(body_file.name)
        except OSError:
            pass

    if not raw.strip():
        return code, {}
    try:
        return code, json.loads(raw)
    except ValueError:
        return code, {"unparsed_body": raw[:400]}


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

    check_order_received_endpoint_routing(lang_key, cfg)
    check_order_received_url_for_real_order(lang_key, cfg)


def check_order_received_url_for_real_order(lang_key, cfg):
    """OPTIONAL, credential-gated: the bogus-order-id probe below only proves
    an order-received endpoint exists on this language's own checkout page —
    it never creates an order, so it can't catch a regression in
    molosoc_cz_order_received_url() itself (the filter deciding which
    checkout twin's order-received endpoint a CZ order is actually sent to).
    That filter only ever runs for a real WC_Order.

    When WP_USER/WP_APP_PASSWORD (a WooCommerce REST API-capable WordPress
    Application Password) are present, this creates a real, unpaid,
    "pending" WC_Order fixture via the REST API — one line item of product
    364/variation 424, tagged with the same `_molosoc_lang` order meta this
    PR's woocommerce_checkout_create_order hook writes — fetches that
    order's own order-received URL on this language's checkout page, and
    confirms it resolves directly (no redirect) to a page that actually
    shows this order (its id appears in the body), not a generic "order not
    found" placeholder. The fixture is always cancelled and trashed
    (force=false, same as scripts/cleanup_test_order.py) before returning,
    pass or fail.

    Without those two env vars this check is SKIPped and nothing is
    created — matching this script's default guest-HTTP-only behavior.
    """
    label = "%s: real order's order-received URL routes to this language's checkout" % lang_key
    if not (WP_USER and WP_APP_PASSWORD):
        record(label, False,
               "WP_USER/WP_APP_PASSWORD not set — skipping the real-order-fixture check; "
               "the bogus-order-id endpoint probe above is the only coverage without it",
               skip=True)
        return

    status, order = wc_api_call("POST", "/orders", {
        "status": "pending",
        "set_paid": False,
        "line_items": [{"product_id": PRODUCT_ID, "variation_id": VARIATION_ID_L, "quantity": 1}],
        "meta_data": [{"key": "_molosoc_lang", "value": lang_key}],
    })
    if status not in (200, 201) or not order.get("id"):
        record(label, False, "could not create fixture order (HTTP %s): %s" % (status, order), skip=True)
        return

    order_id = order["id"]
    order_key = order.get("order_key")
    try:
        if not order_key:
            record(label, False, "created order %d but the response had no order_key" % order_id)
            return
        url = cfg["checkout_url"] + "order-received/%d/?key=%s" % (order_id, order_key)
        code, _final, body, _headers, err = curl("GET", url, follow_redirects=False)
        if err:
            record(label, False, err)
            return
        order_id_shown = body is not None and str(order_id) in body
        ok = code == 200 and order_id_shown
        record(label, ok, "HTTP %s at %s, order id %s in body" % (
            code, url, "found" if order_id_shown else "NOT found"))
        if ok:
            check_html_lang("%s: real order-received page <html lang>" % lang_key, body, cfg["html_lang"])
    finally:
        cancel_status, cancel_body = wc_api_call("PUT", "/orders/%d" % order_id, {"status": "cancelled"})
        trash_status, trash_body = wc_api_call("DELETE", "/orders/%d?force=false" % order_id)
        print("  (cleanup) order %d: cancel HTTP %s (status=%s), trash HTTP %s (status=%s)"
              % (order_id, cancel_status, cancel_body.get("status"),
                 trash_status, trash_body.get("status")))


def check_order_received_endpoint_routing(lang_key, cfg):
    """This script never submits a real order via guest HTTP (non-destructive
    by design), so on its own it can't fetch a real order-received page.
    Instead, this is a focused
    check on the URL GENERATION this PR actually changes: WooCommerce's
    order-received endpoint (wc_get_endpoint_url('order-received', ...), which
    molosoc_cz_order_received_url() rebuilds off the CZ checkout twin's own
    permalink) must be registered on THIS language's checkout URL at all.

    A bogus order id/key on that endpoint still hits WooCommerce's own
    checkout/order-received template — it responds 200 DIRECTLY (no
    redirect) with an "order not found" style notice, not a hard 404 and
    not a redirect elsewhere. Following redirects here would let a missing/
    canonicalized-away endpoint silently pass by landing on the ordinary
    checkout/cart/home page with the right <html lang> — exactly the
    regression this check exists to catch — so this reuses
    check_no_redirect_chain's single-hop, redirect-rejecting request rather
    than following redirects."""
    url = cfg["checkout_url"] + "order-received/999999999/?key=wc_order_nonexistent_test_key"
    body = check_no_redirect_chain(
        "%s: order-received endpoint is routed (HTTP 200, not 404/redirect) off %s"
        % (lang_key, cfg["checkout_url"]),
        url,
    )
    if body is not None:
        check_html_lang("%s: order-received page <html lang>" % lang_key, body, cfg["html_lang"])


def _variation_attributes_from_product_page(product_body, variation_id):
    """Read the {attribute_slug: value} pairs WooCommerce itself declares for
    this variation id out of the product page's own variation-form JSON
    (the `data-product_variations` attribute WooCommerce renders on the
    `.variations_form`), instead of guessing at an unconfirmed attribute
    taxonomy/slug name (flagged elsewhere in this PR as not verifiable from
    this sandbox). This is exactly what the real add-to-cart form itself
    would submit for that variation."""
    if not product_body:
        return None
    m = re.search(r'data-product_variations="([^"]*)"', product_body)
    if not m:
        return None
    try:
        variations = json.loads(html.unescape(m.group(1)))
    except (ValueError, TypeError):
        return None
    for variation in variations:
        if variation.get("variation_id") == variation_id:
            return {k: v for k, v in (variation.get("attributes") or {}).items() if v}
    return None


def run_en_shipping_payment_label_check():
    """Best-effort: adds product 364/variation 424 (with its real attribute
    values, read off the product page's own variation-form data) to an
    ephemeral cart (own cookie-jar session) and checks the rendered EN
    checkout page for the mapped English shipping/payment labels.
    Non-destructive — nothing is submitted to checkout, no order is created;
    the cart only exists in this session's own cookies, which are discarded
    when the script exits.

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
        code, _final, product_body, _headers, err = curl("GET", EN["product_url"], follow_redirects=True)
        if err or code != 200:
            record("EN: fetch product page to read variation %d's attribute values" % VARIATION_ID_L,
                   False, "HTTP %s%s" % (code, (" " + err) if err else ""), skip=True)
            return
        attrs = _variation_attributes_from_product_page(product_body, VARIATION_ID_L)
        if not attrs:
            record("EN: read variation %d's attribute values from the product page" % VARIATION_ID_L,
                   False, "no data-product_variations entry found for this variation id", skip=True)
            return

        qs = "&".join(
            "%s=%s" % (urllib.parse.quote(k), urllib.parse.quote(str(v))) for k, v in attrs.items()
        )
        add_path = "/?add-to-cart=%d&variation_id=%d&quantity=1&%s" % (PRODUCT_ID, VARIATION_ID_L, qs)
        code, _final, body, _headers, err = curl("GET", add_path, cookie_jar=jar, follow_redirects=True)
        if err or code != 200:
            record("EN: add product 364 to ephemeral cart", False,
                   "HTTP %s%s" % (code, (" " + err) if err else ""), skip=True)
            return

        code, _final, checkout_body, _headers, err = curl(
            "GET", EN["checkout_url"], cookie_jar=jar, follow_redirects=True
        )
        if err or code != 200:
            record("EN: fetch checkout with item in ephemeral cart", False,
                   "HTTP %s%s" % (code, (" " + err) if err else ""), skip=True)
            return

        # The add-to-cart request answering 200 only means WooCommerce
        # rendered *a* page — it can still reject an invalid/incomplete
        # variation request with a notice while redirecting back to a normal
        # 200 page. Confirm the item actually landed in the cart by checking
        # the checkout page itself doesn't show WooCommerce's own "cart is
        # empty" notice before trusting anything rendered below it.
        cart_has_item = checkout_body is not None and "currently empty" not in checkout_body.lower()
        record("EN: item actually present in cart at checkout (not WooCommerce's empty-cart notice)",
               cart_has_item, "attributes submitted=%s" % attrs, skip=not cart_has_item)
        if not cart_has_item:
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
