#!/usr/bin/env python3
"""Offline tests for order_window (no network or credentials)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import order_window as ow  # noqa: E402

PII = ["Jana Novakova", "jana@example.com", "+420123456789", "Hlavni 1", "203.0.113.9",
       "Mozilla/5.0 SECRETUA", "SECRET-TXN-ID", "private customer note"]

RAW = {
    "id": 1234, "status": "processing", "currency": "CZK", "total": "799.00",
    "discount_total": "0.00", "shipping_total": "79.00", "total_tax": "0.00",
    "date_created_gmt": "2026-10-04T10:00:00", "date_paid_gmt": "2026-10-04T10:05:00",
    "date_completed_gmt": None, "payment_method": "stripe",
    "payment_method_title": "Card", "transaction_id": "SECRET-TXN-ID",
    "customer_id": 77, "customer_ip_address": "203.0.113.9",
    "customer_note": "private customer note",
    "billing": {"first_name": "Jana", "last_name": "Novakova", "email": "jana@example.com",
                "phone": "+420123456789", "address_1": "Hlavni 1"},
    "shipping": {"first_name": "Jana", "address_1": "Hlavni 1"},
    "line_items": [{"product_id": 5, "name": "Navlek", "quantity": 1, "total": "720.00",
                    "meta_data": [{"key": "x", "value": "Jana Novakova"}]}],
    "shipping_lines": [{"method_id": "flat_rate", "method_title": "Zasilkovna",
                        "total": "79.00"}],
    "coupon_lines": [{"code": "WELCOME10"}],
    "meta_data": [
        {"key": "_wc_order_attribution_source_type", "value": "utm"},
        {"key": "_wc_order_attribution_utm_source", "value": "fb"},
        {"key": "_wc_order_attribution_utm_medium", "value": "paid"},
        {"key": "_wc_order_attribution_referrer", "value": "https://m.facebook.com/l/?u=abc"},
        {"key": "_wc_order_attribution_session_entry",
         "value": "https://molosoc.com/cz/lp/?utm_source=fb&email=jana@example.com&fbclid=Z"},
        {"key": "_wc_order_attribution_user_agent", "value": "Mozilla/5.0 SECRETUA"},
        {"key": "_billing_email", "value": "jana@example.com"},
    ],
}


def test_window_bounds_inclusive_and_limits():
    assert ow.window_bounds("2026-10-03", "2026-10-05") == (
        "2026-10-03T00:00:00", "2026-10-06T00:00:00")
    with pytest.raises(ValueError):
        ow.window_bounds("2026-10-05", "2026-10-03")
    with pytest.raises(ValueError):
        ow.window_bounds("2026-10-01", "2026-10-15")
    ow.window_bounds("2026-10-01", "2026-10-14")


def test_sanitized_output_contains_no_pii():
    out = ow.sanitize_order(RAW)
    text = json.dumps(out, ensure_ascii=False)
    for secret in PII:
        assert secret not in text
    assert out["has_transaction_id"] is True
    assert out["coupons"] == ["WELCOME10"]
    assert out["shipping_lines"][0]["method_title"] == "Zasilkovna"
    assert out["line_items"][0] == {"product_id": 5, "name": "Navlek", "quantity": 1,
                                    "total": "720.00"}
    assert set(out) == {
        "id", "status", "created_gmt", "paid_gmt", "completed_gmt", "currency", "total",
        "discount_total", "shipping_total", "total_tax", "payment_method",
        "payment_method_title", "has_transaction_id", "line_items", "shipping_lines",
        "coupons", "attribution"}


def test_attribution_allowlist_and_url_reduction():
    attr = ow.sanitize_order(RAW)["attribution"]
    assert attr["source_type"] == "utm" and attr["utm_medium"] == "paid"
    assert "user_agent" not in attr
    assert attr["referrer"] == "m.facebook.com/l/"
    assert attr["session_entry"] == "molosoc.com/cz/lp/?utm_source=fb [fbclid present]"


def test_fetch_orders_paginates_and_only_gets():
    calls = []

    class Fake:
        def get(self, path, params):
            calls.append((path, params["page"]))
            return [{"id": i} for i in range(ow.PER_PAGE)] if params["page"] == 1 else [{"id": 999}]

    assert len(ow.fetch_orders(Fake(), "a", "b")) == ow.PER_PAGE + 1
    assert calls == [("/orders", 1), ("/orders", 2)]


def test_http_error_does_not_leak_body(monkeypatch):
    import io
    import urllib.error

    def boom(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 401, "x", {}, io.BytesIO(b"secret body"))

    monkeypatch.setattr(ow._OPENER, "open", boom)
    with pytest.raises(RuntimeError) as exc:
        ow.Client("https://x.test", "ck", "cs").get("/orders", {})
    assert "401" in str(exc.value) and "secret body" not in str(exc.value)
    assert "ck" not in str(exc.value)


def test_clean_url_strips_userinfo():
    out = ow.clean_url("https://name:tok3n@example.com:8443/p?utm_source=fb")
    assert out == "example.com:8443/p?utm_source=fb"
    assert "name" not in out and "tok3n" not in out and "@" not in out


def test_cross_origin_redirect_is_refused_without_sending_credentials():
    import http.server
    import threading

    seen = []

    class Target(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"[]")

        def log_message(self, *a):
            pass

    target = http.server.HTTPServer(("127.0.0.1", 0), Target)

    class Redirector(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.server_port}/x")
            self.end_headers()

        def log_message(self, *a):
            pass

    redirector = http.server.HTTPServer(("127.0.0.1", 0), Redirector)
    for srv in (target, redirector):
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        client = ow.Client(f"http://127.0.0.1:{redirector.server_port}", "ck", "cs")
        with pytest.raises(RuntimeError) as exc:
            client.get("/orders", {})
        assert "302" in str(exc.value)
        assert seen == []
    finally:
        for srv in (target, redirector):
            srv.shutdown()
