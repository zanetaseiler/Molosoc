#!/usr/bin/env python3
"""Read-only, non-PII WooCommerce order extraction for a UTC window (Issue #100).

GET /wp-json/wc/v3/orders only, authenticated with the dedicated read-only REST
key (WOO_RO_CONSUMER_KEY / WOO_RO_CONSUMER_SECRET). Nothing is written anywhere.

Output is built from a strict allowlist: every printed field is named below, so
customer data (billing/shipping addresses, name, email, phone, IP, user agent,
customer id, transaction id, notes) cannot reach the log by omission.
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

MAX_DAYS = 14
PER_PAGE = 100
MAX_PAGES = 20
DEFAULT_SITE = "https://molosoc.com"

# `_wc_order_attribution_*` meta keys that are safe to print (suffix after the prefix).
ATTRIBUTION_PREFIX = "_wc_order_attribution_"
ATTRIBUTION_ALLOWED = (
    "source_type", "utm_source", "utm_medium", "utm_campaign", "utm_content",
    "utm_term", "utm_id", "device_type", "referrer", "session_entry",
    "session_pages", "session_count", "session_start_time",
)
URL_FIELDS = ("referrer", "session_entry")
KEPT_QUERY_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content",
                   "utm_term", "utm_id")
SAFE_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
SAFE_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+ -]{0,59}$")
REDACTED = "[redacted]"


def safe_value(value):
    """Keep a visitor-controlled value only if it looks like a plain campaign label."""
    text = str(value)
    if "@" in text or not SAFE_VALUE.match(text) or re.search(r"\d{6,}", text):
        return REDACTED
    return text


def safe_path(path):
    """Keep only short lowercase slug segments; anything else (emails, ids, tokens) is masked."""
    segs = []
    for seg in path.split("/"):
        if not seg or (SAFE_SEGMENT.match(seg) and not re.search(r"\d{6,}", seg)
                       and not (len(seg) > 24 and re.search(r"\d", seg))):
            segs.append(seg)
        else:
            segs.append("*")
    return "/".join(segs)


def window_bounds(start, end):
    """(after, before) ISO strings, UTC; end day is inclusive. Max MAX_DAYS days."""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    if e < s:
        raise ValueError("end is before start")
    if (e - s).days + 1 > MAX_DAYS:
        raise ValueError(f"window is longer than {MAX_DAYS} days")
    after = datetime(s.year, s.month, s.day).isoformat()
    nxt = datetime(e.year, e.month, e.day) + timedelta(days=1)
    return after, nxt.isoformat()


def clean_url(value):
    """Reduce a URL to host + path + allowlisted utm_* params; flag fbclid presence."""
    if not value or not isinstance(value, str):
        return value
    parsed = urllib.parse.urlsplit(value)
    if not parsed.scheme and not parsed.netloc:
        return safe_path(parsed.path)[:200]
    query = urllib.parse.parse_qs(parsed.query)
    kept = {k: safe_value(query[k][0]) for k in KEPT_QUERY_KEYS if k in query}
    # Rebuild the authority from hostname + port only: netloc may carry userinfo.
    try:
        port = parsed.port
    except ValueError:
        port = None
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    out = f"{host}{':' + str(port) if port else ''}{safe_path(parsed.path)}"
    if kept:
        out += "?" + urllib.parse.urlencode(kept)
    if "fbclid" in query:
        out += " [fbclid present]"
    return out[:300]


def attribution(meta_data):
    out = {}
    for item in meta_data or []:
        key = str(item.get("key", ""))
        if not key.startswith(ATTRIBUTION_PREFIX):
            continue
        name = key[len(ATTRIBUTION_PREFIX):]
        if name not in ATTRIBUTION_ALLOWED:
            continue
        value = item.get("value")
        if name in URL_FIELDS:
            value = clean_url(value)
        elif name.startswith("utm_") and value is not None:
            value = safe_value(value)
        out[name] = value
    return out


def sanitize_order(order):
    """Project one raw WooCommerce order onto the non-PII allowlist."""
    return {
        "id": order.get("id"),
        "status": order.get("status"),
        "created_gmt": order.get("date_created_gmt"),
        "paid_gmt": order.get("date_paid_gmt"),
        "completed_gmt": order.get("date_completed_gmt"),
        "currency": order.get("currency"),
        "total": order.get("total"),
        "discount_total": order.get("discount_total"),
        "shipping_total": order.get("shipping_total"),
        "total_tax": order.get("total_tax"),
        "payment_method": order.get("payment_method"),
        "payment_method_title": order.get("payment_method_title"),
        "has_transaction_id": bool(order.get("transaction_id")),
        "line_items": [
            {"product_id": li.get("product_id"), "name": li.get("name"),
             "quantity": li.get("quantity"), "total": li.get("total")}
            for li in order.get("line_items") or []],
        "shipping_lines": [
            {"method_id": sl.get("method_id"), "method_title": sl.get("method_title"),
             "total": sl.get("total")}
            for sl in order.get("shipping_lines") or []],
        "coupons": [c.get("code") for c in order.get("coupon_lines") or []],
        "attribution": attribution(order.get("meta_data")),
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow redirects: urllib would forward the Authorization header."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class Client:
    def __init__(self, site, key, secret):
        self.base = site.rstrip("/") + "/wp-json/wc/v3"
        token = base64.b64encode(f"{key}:{secret}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Accept": "application/json",
                        "User-Agent": "molosoc-order-window/1"}

    def get(self, path, params):
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with _OPENER.open(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            # Status only: never echo the response body or the credentials.
            raise RuntimeError(f"WooCommerce GET {path} failed: HTTP {exc.code}") from None
        except urllib.error.URLError as exc:
            raise RuntimeError(f"WooCommerce GET {path} failed: {exc.reason}") from None


def fetch_orders(client, after, before):
    orders = []
    # WooCommerce `after` is an exclusive bound: step back 1s so an order created
    # exactly at the window start is included.
    query_after = (datetime.fromisoformat(after) - timedelta(seconds=1)).isoformat()
    for page in range(1, MAX_PAGES + 1):
        batch = client.get("/orders", {
            "after": query_after, "before": before, "dates_are_gmt": "true",
            "status": "any", "per_page": PER_PAGE, "page": page,
            "orderby": "date", "order": "asc"})
        orders.extend(batch)
        if len(batch) < PER_PAGE:
            return orders
    raise RuntimeError(f"more than {MAX_PAGES * PER_PAGE} orders in window; narrow it")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", required=True, help="First UTC day (YYYY-MM-DD)")
    ap.add_argument("--end", required=True, help="Last UTC day, inclusive (max 14 days)")
    args = ap.parse_args(argv)
    key = os.environ.get("WOO_RO_CONSUMER_KEY", "")
    secret = os.environ.get("WOO_RO_CONSUMER_SECRET", "")
    if not key or not secret:
        print("ERROR: WOO_RO_CONSUMER_KEY / WOO_RO_CONSUMER_SECRET not set", file=sys.stderr)
        return 2
    try:
        after, before = window_bounds(args.start, args.end)
        client = Client(os.environ.get("WOO_SITE_URL") or DEFAULT_SITE, key, secret)
        orders = [sanitize_order(o) for o in fetch_orders(client, after, before)]
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"WooCommerce orders (UTC) {after} <= created < {before}: {len(orders)}")
    print(json.dumps(orders, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
