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
import sys
import re
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
# Visitor-controlled text cannot be judged non-PII by its shape (a name looks like a
# campaign label), so only values from this fixed vocabulary are ever printed.
# Everything else is reported as present/redacted, never echoed.
SAFE_VALUES = frozenset((
    "fb", "facebook", "ig", "instagram", "meta", "google", "bing", "youtube", "tiktok",
    "pinterest", "linkedin", "twitter", "x", "email", "newsletter", "sms", "direct",
    "organic", "referral", "social", "paid", "paid_social", "cpc", "ppc", "display",
    "affiliate", "(direct)", "(none)", "utm", "typein", "admin"))
REDACTED = "[redacted]"
# Hostnames can be visitor-controlled too (personal domains, IP literals, fabricated
# subdomain labels), so only these exact hostnames are printed; any other host,
# including any other subdomain of these domains, is redacted.
SAFE_HOSTS = frozenset((
    "molosoc.com", "www.molosoc.com", "google.com", "www.google.com", "bing.com",
    "www.bing.com", "duckduckgo.com", "yahoo.com", "seznam.cz", "www.seznam.cz",
    "facebook.com", "www.facebook.com", "m.facebook.com", "l.facebook.com",
    "instagram.com", "www.instagram.com", "l.instagram.com", "youtube.com",
    "www.youtube.com", "tiktok.com", "www.tiktok.com", "pinterest.com",
    "www.pinterest.com", "linkedin.com", "www.linkedin.com", "twitter.com", "t.co",
    "x.com", "paypal.com", "www.paypal.com", "stripe.com", "checkout.stripe.com"))
# Landing-page paths are visitor-controlled too (/reset/jana@example.com), so each path
# segment is printed only if it is one of these fixed site slugs; others become REDACTED.
SAFE_PATH_SEGMENTS = frozenset((
    "cz", "cs", "en", "lp", "produkt", "product", "navleky-na-nohy",
    "hydratacni-navlek-na-nohy", "molosoc-hydratacni-navleky-na-nohy", "foot-covers",
    "moisture-lock-foot-cover", "cracked-heels", "ingrown-toenails",
    "hardened-skin-calluses", "dry-skin-feet", "foot-cream-that-works", "shop", "cart",
    "checkout", "order-received"))
MAX_PATH_SEGMENTS = 6
# Campaign/content labels are visitor-controlled free text, so besides the fixed
# vocabulary only purely numeric platform ids (e.g. Meta campaign/ad ids) are echoed.
ID_RE = re.compile(r"[0-9]{6,20}")
ID_FIELDS = ("utm_campaign", "utm_content")
# Non-text attribution fields are validated against their expected type/vocabulary.
SOURCE_TYPES = frozenset(("typein", "organic", "referral", "utm", "admin", "unknown"))
DEVICE_TYPES = frozenset(("desktop", "mobile", "tablet", "unknown"))
COUNT_RE = re.compile(r"[0-9]{1,6}")
START_TIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}")


def vocab_value(value, vocabulary):
    text = str(value).strip()
    return text if text.lower() in vocabulary else REDACTED


def pattern_value(value, pattern):
    text = str(value).strip()
    return text if pattern.fullmatch(text) else REDACTED


def safe_value(value):
    """Print a visitor-controlled value only if it is in the fixed SAFE_VALUES vocabulary."""
    text = str(value).strip()
    return text if text.lower() in SAFE_VALUES else REDACTED


def safe_host(host):
    host = (host or "").lower().rstrip(".")
    return host if host in SAFE_HOSTS else REDACTED


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
    """Reduce a URL to host only + vocabulary-checked utm_* params; flag fbclid presence."""
    if value is None or value == "":
        return value
    if not isinstance(value, str):
        return REDACTED  # dicts/lists/numbers must never reach the log
    try:
        parsed = urllib.parse.urlsplit(value)
        query = urllib.parse.parse_qs(parsed.query)
    except ValueError:
        return REDACTED  # malformed (e.g. "https://["): never abort the extraction
    if not parsed.scheme and not parsed.netloc:
        return REDACTED  # bare path: visitor-controlled, nothing safe to keep
    kept = {k: safe_value(query[k][0]) for k in KEPT_QUERY_KEYS if k in query}
    try:
        host = safe_host(parsed.hostname)
    except ValueError:
        return REDACTED
    # Host only: userinfo, port and the visitor-controlled path are all dropped.
    out = host
    if kept:
        out += "?" + urllib.parse.urlencode(kept)
    if "fbclid" in query:
        out += " [fbclid present]"
    return out[:300]


def clean_landing(value):
    """Reduce a URL to host + path only (query, fragment, userinfo, port dropped)."""
    if value is None or value == "":
        return value
    if not isinstance(value, str):
        return REDACTED
    try:
        parsed = urllib.parse.urlsplit(value)
        host = safe_host(parsed.hostname)
    except ValueError:
        return REDACTED
    if not parsed.netloc:
        return REDACTED  # bare path: no host to attribute it to
    segments = [s for s in parsed.path.split("/") if s]
    if len(segments) > MAX_PATH_SEGMENTS:
        segments = segments[:MAX_PATH_SEGMENTS] + [REDACTED]
    kept = [s if s.lower() in SAFE_PATH_SEGMENTS else REDACTED for s in segments]
    return (host + ("/" + "/".join(kept) + "/" if kept else "/"))[:300]


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
        elif value is None:
            pass
        elif name in ID_FIELDS and ID_RE.fullmatch(str(value).strip()):
            value = str(value).strip()
        elif name.startswith("utm_"):
            value = safe_value(value)
        elif name == "source_type":
            value = vocab_value(value, SOURCE_TYPES)
        elif name == "device_type":
            value = vocab_value(value, DEVICE_TYPES)
        elif name in ("session_pages", "session_count"):
            value = pattern_value(value, COUNT_RE)
        elif name == "session_start_time":
            value = pattern_value(value, START_TIME_RE)
        else:
            value = REDACTED  # allowlisted name without a validator: never echo
        out[name] = value
        if name == "session_entry":
            out["landing_page"] = clean_landing(item.get("value"))
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
    def __init__(self, site, key, secret, allow_loopback_http=False):
        parts = urllib.parse.urlsplit(site)
        loopback = parts.hostname in ("127.0.0.1", "localhost", "::1")
        if parts.scheme != "https" and not (allow_loopback_http and loopback and parts.scheme == "http"):
            # Basic auth over plaintext would expose the key and secret.
            raise ValueError("WOO_SITE_URL must be an https:// URL")
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
    for page in range(1, MAX_PAGES + 2):
        batch = client.get("/orders", {
            "after": query_after, "before": before, "dates_are_gmt": "true",
            "status": "any", "per_page": PER_PAGE, "page": page,
            "orderby": "date", "order": "asc"})
        if page > MAX_PAGES:
            # Probe page: a full final batch is fine; any extra record means overflow.
            if batch:
                raise RuntimeError(f"more than {MAX_PAGES * PER_PAGE} orders in window; narrow it")
            return orders
        orders.extend(batch)
        if len(batch) < PER_PAGE:
            return orders


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
