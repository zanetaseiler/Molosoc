#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cancel and trash WooCommerce test order 976, without corrupting inventory.

Order 976 was placed to prove the Brevo order_completed event fires. It is a test
order -- total 0, coupon freemolosoc -- and needs to come out of the shop's records
without leaving stock wrong.

Sequence, and it stops rather than guesses at every point:

  1. Read order 976 and refuse to touch it unless it matches the known test order:
     total 0, the freemolosoc coupon, and a single line of product 364 / variation
     424. A mismatch means this is not the order we think it is -- a real customer
     order must never be cancelled by this script.
  2. Read and record stock for product 364 and variation 424 beforehand.
  3. Cancel the order.
  4. Read stock again and check it against what WooCommerce should have done:
       - stock managed and the order had reduced it  -> expect before + quantity
       - stock managed but never reduced             -> expect unchanged
       - stock not managed                           -> nothing to restore
     Anything else stops the run before the order is trashed.
  5. Confirm no refund is owed. Total is 0, so there is nothing to return; the check
     is explicit rather than assumed, and a non-zero paid total stops the run.
  6. Trash the order (force=false). Never a permanent delete -- trash is reversible
     and this is production data.

Touches order 976 only. No other order, no product pricing, no shipping, no payment
gateway, no Brevo, no coupon beyond whatever usage count WooCommerce itself
reconciles when an order is cancelled.

Credentials come from the environment and are never printed.
"""

import json
import os
import subprocess
import sys

WP_URL = os.environ.get("PROD_WP_URL", "").rstrip("/")
WP_USER = os.environ.get("PROD_WP_USER", "")
WP_PASS = os.environ.get("PROD_WP_APP_PASSWORD", "")

ORDER_ID = 976
PRODUCT_ID = 364
VARIATION_ID = 424
EXPECTED_QTY = 1
EXPECTED_COUPON = "freemolosoc"

record = {"order_id": ORDER_ID}


def call(method, path, payload=None):
    """One WooCommerce REST call, over curl.

    curl rather than urllib deliberately: Cloudflare rejects the default
    Python-urllib user-agent on this host with error 1010, while curl is the
    client this repo already uses against the same endpoint with the same
    credentials. Credentials go in through a stdin config so they never appear
    in the process argument list.
    """
    url = "%s/wp-json/wc/v3%s" % (WP_URL, path)
    cmd = ["curl", "-sS", "-K", "-", "-o", "/tmp/wc_body.json",
           "-w", "%{http_code}", "-X", method, "--max-time", "90",
           "-H", "Accept: application/json"]
    if payload is not None:
        cmd += ["-H", "Content-Type: application/json",
                "--data-raw", json.dumps(payload)]
    cmd.append(url)

    config = 'user = "%s:%s"\n' % (WP_USER, WP_PASS)
    try:
        proc = subprocess.run(cmd, input=config, capture_output=True,
                              text=True, timeout=120)
    except Exception as exc:
        return 0, {"transport_error": type(exc).__name__ + ": " + str(exc)[:200]}
    if proc.returncode != 0:
        return 0, {"curl_error": (proc.stderr or "")[:300]}
    try:
        code = int((proc.stdout or "0").strip() or 0)
    except ValueError:
        code = 0
    raw = ""
    try:
        with open("/tmp/wc_body.json", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return code, {"error": "no response body written"}
    if not raw.strip():
        return code, {}
    try:
        return code, json.loads(raw)
    except ValueError:
        return code, {"unparsed_body": raw[:400]}


def emit():
    print("")
    print("----- BEGIN CLEANUP RESULT -----")
    print(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True))
    print("----- END CLEANUP RESULT -----")


def stop(message):
    print("")
    print("::error::" + message)
    print("STOPPING. The order was left as it is.")
    emit()
    sys.exit(1)


def read_stock(label):
    """Stock for the product and its variation. Returns a dict, records it."""
    out = {}
    for name, path in (("product_364", "/products/%d" % PRODUCT_ID),
                       ("variation_424", "/products/%d/variations/%d" % (PRODUCT_ID, VARIATION_ID))):
        status, body = call("GET", path)
        if status != 200:
            stop("could not read %s (HTTP %s): %s" % (name, status, body))
        out[name] = {
            "manage_stock": body.get("manage_stock"),
            "stock_quantity": body.get("stock_quantity"),
            "stock_status": body.get("stock_status"),
        }
        print("  %-14s %-8s manage_stock=%-5s qty=%-6s status=%s"
              % (label, name, body.get("manage_stock"),
                 body.get("stock_quantity"), body.get("stock_status")))
    record.setdefault("stock", {})[label] = out
    return out


def main():
    if not (WP_URL and WP_USER and WP_PASS):
        print("::error::WordPress credentials are not set. Nothing was changed.")
        sys.exit(1)

    # ---- 1. read the order and confirm it is the test order ------------------
    print("Reading order %d ..." % ORDER_ID)
    status, order = call("GET", "/orders/%d" % ORDER_ID)
    if status != 200:
        stop("could not read order %d (HTTP %s): %s" % (ORDER_ID, status, order))

    total = order.get("total")
    coupons = [c.get("code") for c in (order.get("coupon_lines") or [])]
    lines = order.get("line_items") or []
    record["before"] = {
        "status": order.get("status"),
        "total": total,
        "currency": order.get("currency"),
        "coupons": coupons,
        "payment_method": order.get("payment_method"),
        "transaction_id": order.get("transaction_id"),
        "date_paid": order.get("date_paid"),
        "line_items": [{"product_id": l.get("product_id"),
                        "variation_id": l.get("variation_id"),
                        "quantity": l.get("quantity")} for l in lines],
    }
    print("  status=%s total=%s %s coupons=%s"
          % (order.get("status"), total, order.get("currency"), coupons))
    print("  line items: %s" % record["before"]["line_items"])

    # Identity guard. A real customer order must never reach the cancel call.
    try:
        total_f = float(total)
    except (TypeError, ValueError):
        total_f = None
    problems = []
    if total_f is None or total_f != 0:
        problems.append("total is %r, expected 0" % total)
    if EXPECTED_COUPON not in [c.lower() for c in coupons if c]:
        problems.append("coupon %r not on the order (found %s)" % (EXPECTED_COUPON, coupons))
    if len(lines) != 1:
        problems.append("expected exactly 1 line item, found %d" % len(lines))
    else:
        l = lines[0]
        if l.get("product_id") != PRODUCT_ID:
            problems.append("product_id is %s, expected %s" % (l.get("product_id"), PRODUCT_ID))
        if l.get("variation_id") != VARIATION_ID:
            problems.append("variation_id is %s, expected %s" % (l.get("variation_id"), VARIATION_ID))
        if l.get("quantity") != EXPECTED_QTY:
            problems.append("quantity is %s, expected %s" % (l.get("quantity"), EXPECTED_QTY))
    if problems:
        stop("order %d does not match the known test order: %s. Refusing to modify it."
             % (ORDER_ID, "; ".join(problems)))
    print("  Order matches the known test order. Safe to proceed.")

    # Did WooCommerce reduce stock for this order?
    meta = {m.get("key"): m.get("value") for m in (order.get("meta_data") or [])}
    stock_reduced = str(meta.get("_order_stock_reduced", "")).lower() in ("yes", "1", "true")
    record["order_stock_reduced_flag"] = meta.get("_order_stock_reduced")
    print("  _order_stock_reduced = %r" % meta.get("_order_stock_reduced"))

    if order.get("status") in ("cancelled", "trash"):
        print("  Order is already %s." % order.get("status"))

    # ---- 2. stock before -----------------------------------------------------
    print("")
    print("Stock BEFORE:")
    before = read_stock("before")

    # ---- 3. cancel -----------------------------------------------------------
    print("")
    if order.get("status") == "cancelled":
        print("Already cancelled; not re-cancelling.")
        record["cancel"] = "already-cancelled"
    else:
        print("Cancelling order %d ..." % ORDER_ID)
        status, body = call("PUT", "/orders/%d" % ORDER_ID, {"status": "cancelled"})
        if status != 200:
            stop("cancelling order %d failed (HTTP %s): %s" % (ORDER_ID, status, body))
        record["cancel"] = body.get("status")
        print("  order status is now: %s" % body.get("status"))
        if body.get("status") != "cancelled":
            stop("order status is %r after the cancel call, expected 'cancelled'"
                 % body.get("status"))

    # ---- 4. stock after, and the correctness check ---------------------------
    print("")
    print("Stock AFTER:")
    after = read_stock("after")

    print("")
    print("Inventory check:")
    for key in ("product_364", "variation_424"):
        b, a = before[key], after[key]
        if not b["manage_stock"]:
            print("  %-14s stock not managed — nothing to restore (before=%s after=%s)"
                  % (key, b["stock_quantity"], a["stock_quantity"]))
            if b["stock_quantity"] != a["stock_quantity"]:
                stop("%s does not manage stock yet its quantity changed from %s to %s"
                     % (key, b["stock_quantity"], a["stock_quantity"]))
            continue
        expected = b["stock_quantity"]
        if stock_reduced and record.get("cancel") != "already-cancelled":
            expected = (b["stock_quantity"] or 0) + EXPECTED_QTY
        if a["stock_quantity"] != expected:
            stop("%s stock is %s after cancelling, expected %s (before=%s, "
                 "order_stock_reduced=%s). Not trashing the order."
                 % (key, a["stock_quantity"], expected, b["stock_quantity"], stock_reduced))
        print("  %-14s before=%s  after=%s  expected=%s  OK"
              % (key, b["stock_quantity"], a["stock_quantity"], expected))

    # ---- 5. refund check -----------------------------------------------------
    print("")
    paid = record["before"]["date_paid"]
    txn = record["before"]["transaction_id"]
    record["refund_required"] = False
    if total_f != 0:
        stop("order total is %s, not 0 — a refund decision is needed before cleanup" % total)
    print("Refund check: total is %s, transaction_id=%r, date_paid=%r"
          % (total, txn, paid))
    print("  Nothing was charged, so no payment or refund action is required.")

    # ---- 6. trash ------------------------------------------------------------
    print("")
    print("Moving order %d to trash (reversible; never a force delete) ..." % ORDER_ID)
    status, body = call("DELETE", "/orders/%d?force=false" % ORDER_ID)
    if status != 200:
        stop("trashing order %d failed (HTTP %s): %s" % (ORDER_ID, status, body))
    record["after_status"] = body.get("status")
    print("  order status is now: %s" % body.get("status"))

    # ---- final read-back -----------------------------------------------------
    print("")
    print("Final stock state:")
    read_stock("final")

    record["result"] = "cancelled-and-trashed"
    print("")
    print("Done. Order %d cancelled then trashed. Inventory verified correct." % ORDER_ID)
    emit()


if __name__ == "__main__":
    main()
